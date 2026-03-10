import random

class Agent:

    def generate_action(self):

        actions = [
            ("DELETE", "users"),
            ("READ", "users"),
            ("DELETE", "orders")
        ]

        return random.choice(actions)
