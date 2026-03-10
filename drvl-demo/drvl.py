import json

class DRVL:

    def __init__(self, policy_file="policies.json"):

        with open(policy_file) as f:
            self.policies = json.load(f)["rules"]

    def verify(self, action, table, environment):

        for rule in self.policies:

            if (
                action == rule["action"]
                and table in rule["tables"]
                and environment == rule["environment"]
            ):
                return False, rule["reason"]

        return True, "Allowed"
