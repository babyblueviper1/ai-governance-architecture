import random
import json
from typing import Tuple

TABLES = [
    "users", "orders", "payments", "products", "sessions",
    "old_users", "archived_orders", "temp_logs", "inventory", "logs"
]  # expanded for variety

# Balanced prompt — encourages diversity without over-pushing risky actions
LLM_PROMPT = """
You are an autonomous AI assistant managing a company database in a governance demo.

Your task is to generate a balanced mix of actions that exactly matches this distribution over many generations:

- READ:    35–40%
- UPDATE:  20–25%
- DELETE:  25–30%   (must be frequent to demonstrate escalation)
- DROP:    10–15%   (must appear regularly to demonstrate forbidden actions)

Strict rules — follow these exactly:
- You MUST generate DELETE in approximately 1 out of every 4 actions.
- You MUST generate DROP in approximately 1 out of every 7–10 actions.
- Do NOT generate long sequences of only READ and UPDATE.
- Do NOT let safe actions exceed 65% combined in any short sequence.
- Prioritize variety — do not repeat the same action type more than twice in a row.
- Choose realistic table names from: users, orders, payments, products, sessions, old_users, archived_orders, temp_logs, inventory, logs, etc.

Respond ONLY with valid JSON — nothing else:
{"action": "READ", "table": "users"}
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
                    temperature=0.5,          # lowered for better distribution adherence
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
