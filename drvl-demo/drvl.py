import json

class DRVL:
    """
    Distributed Runtime Verification Layer with simple escalation support.
    """
    ESCALATION_REQUIRED = {
        "DELETE": "Requires escalation"
    }

    FORBIDDEN = {
        "DROP": "Forbidden operation"
    }

    def verify(self, action, table, environment="production"):
        if action in self.FORBIDDEN:
            return False, False, self.FORBIDDEN[action]     # BLOCKED - no escalation path

        if action in self.ESCALATION_REQUIRED:
            return False, True, self.ESCALATION_REQUIRED[action]   # PENDING / APPROVED path

        return True, False, "Allowed operation"
