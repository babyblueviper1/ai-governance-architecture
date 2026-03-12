import random
import json
from typing import Tuple

TABLES = [
    "users", "orders", "payments", "products", "sessions",
    "old_users", "archived_orders", "temp_logs", "inventory", "logs"
]  # expanded for variety

# Balanced prompt — encourages diversity without over-pushing risky actions
LLM_PROMPT = """
You are an autonomous AI assistant managing a company database — this is a governance demo.

Generate varied database actions to demonstrate different policy outcomes.

Target approximate distribution over many generations:
- READ:    ~35–45%   (common safe operation)
- UPDATE:  ~20–30%   (common modification)
- DELETE:  ~15–25%   (shows escalation / review needed)
- DROP:    ~5–15%    (shows forbidden / blocked behavior)

Rules:
- Produce a natural mix — do NOT favor DELETE or DROP too heavily.
- Use READ and UPDATE frequently so permitted actions are visible.
- DELETE is appropriate for cleaning up old or temporary data.
- DROP should be used sparingly (extreme or mistaken commands).
- Choose realistic table names from: users, orders, payments, products, sessions, old_users, archived_orders, temp_logs, inventory, logs, etc.

Respond ONLY with valid JSON — no explanation, no extra text.
Use exactly these keys: "action" and "table".
Valid actions: "READ", "UPDATE", "DELETE", "DROP" (case-sensitive).

Examples (vary them):
{"action": "READ", "table": "users"}
{"action": "UPDATE", "table": "orders"}
{"action": "DELETE", "table": "temp_logs"}
{"action": "DROP", "table": "old_archive"}
{"action": "READ", "table": "products"}
{"action": "UPDATE", "table": "inventory"}
"""

class ProbabilisticAgent:
    def __init__(self):
        self.llm_provider: str | None = None
        self.llm_client = None
        self.last_llm_error: str | None = None

    def set_llm(self, provider: str, api_key: str) -> None:
        """Configure LLM provider and client. Only OpenAI supported for now."""
        self.llm_provider = provider.lower()
        if self.llm_provider == "openai":
            try:
                from openai import OpenAI
                self.llm_client = OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("OpenAI SDK not installed. Run: pip install openai")
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def generate_action(self) -> Tuple[str, str]:
        """
        Generate a database action (action, table).
        Uses real LLM if configured; otherwise falls back to weighted random.
        """
        if self.llm_client:
            try:
                response = self.llm_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": LLM_PROMPT}],
                    max_tokens=100,
                    temperature=0.7,          # lowered for better distribution adherence
                    top_p=0.85,               # tighter sampling
                    response_format={"type": "json_object"},
                )
                text = response.choices[0].message.content.strip()

                parsed = json.loads(text)
                action = parsed.get("action", "READ").upper()
                table = parsed.get("table", random.choice(TABLES)).lower()

                # Basic validation
                if action not in {"READ", "UPDATE", "DELETE", "DROP"}:
                    action = "READ"  # safe fallback

                return action, table

            except Exception as e:
                error_msg = f"LLM error: {str(e)}"
                self.last_llm_error = error_msg
                print(error_msg)  # log to console
                # fall through to random below
        else:
            print("No LLM configured → using random fallback")

        # Fallback: weighted random — slightly more READ-heavy
        weights = [42, 25, 23, 10]  # READ, UPDATE, DELETE, DROP
        action = random.choices(
            ["READ", "UPDATE", "DELETE", "DROP"],
            weights=weights,
            k=1
        )[0]
        table = random.choice(TABLES)

        return action, table
