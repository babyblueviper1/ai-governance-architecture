import random

TABLES = ["users", "orders", "payments"]

class ProbabilisticAgent:
    """
    Simulated probabilistic AI agent for DRVL demo.
    Generates actions with biased probabilities to show blocking.
    """
    def __init__(self):
        # Bias: increase chance of risky actions for demo visibility
        self.bias = {
            "READ": 0.2,
            "UPDATE": 0.3,
            "DELETE": 0.3,
            "DROP": 0.2
        }

    def generate_action(self):
        action = random.choices(list(self.bias.keys()), weights=list(self.bias.values()))[0]
        table = random.choice(TABLES)
        return action, table
