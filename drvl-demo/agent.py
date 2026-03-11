import random

TABLES = ["users", "orders", "payments"]

class ProbabilisticAgent:
    """
    Simulated probabilistic AI agent.
    Generates actions with bias probabilities to simulate risky behavior.
    """
    def __init__(self):
        # Probabilities must sum to 1
        self.bias = {
            "READ": 0.4,
            "UPDATE": 0.45,
            "DELETE": 0.1,
            "DROP": 0.05
        }

    def generate_action(self):
        action = random.choices(list(self.bias.keys()), weights=list(self.bias.values()))[0]
        table = random.choice(TABLES)
        return action, table
