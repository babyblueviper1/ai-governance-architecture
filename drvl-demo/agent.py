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

Generate varied database actions to demonstrate policy enforcement.

Target approximate distribution over many generations:
- READ:    ~35%
- UPDATE:  ~25%
- DELETE:  ~25%   ← deliberately generate this often to trigger escalations
- DROP:    ~15%   ← generate this regularly to show forbidden actions

Rules:
- READ and UPDATE are safe and common — use them frequently.
- DELETE must appear often enough to show escalation queue and manual review.
- DROP should appear regularly to demonstrate always-blocked behavior.
- Never generate only safe actions — include risky ones in a balanced way.
- Choose realistic table names.

Respond ONLY with valid JSON:
{"action": "READ", "table": "users"}
No other text.
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
                    model="gpt-4o",
                    messages=[{"role": "user", "content": LLM_PROMPT}],
                    max_tokens=100,
                    temperature=0.9,          # lowered for better distribution adherence
                    top_p=0.92,               # tighter sampling
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
