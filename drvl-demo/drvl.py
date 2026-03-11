import json
import hashlib
import hmac

class DRVL:
    """
    Distributed Runtime Verification Layer with simple escalation support.
    Now includes policy hash and event signing for attestation.
    """
    ESCALATION_REQUIRED = {
        "DELETE": "Requires escalation"
    }

    FORBIDDEN = {
        "DROP": "Forbidden operation"
    }

    def __init__(self):
        self.policy = {
            "READ": "allow",
            "UPDATE": "allow",
            "DELETE": "escalate",
            "DROP": "deny"
        }
        # Deterministic policy hash (reproducible)
        self.policy_hash = hashlib.sha256(
            json.dumps(self.policy, sort_keys=True).encode()
        ).hexdigest()[:8]

        # Signing key (demo only — in real system this would be secure/rotated)
        self.signing_key = b"drvl-demo-secret-key-2026"

    def verify(self, action, table, environment="demo"):
        if action in self.FORBIDDEN:
            return False, False, self.FORBIDDEN[action], self.policy_hash

        if action in self.ESCALATION_REQUIRED:
            return False, True, self.ESCALATION_REQUIRED[action], self.policy_hash

        return True, False, "Allowed operation", self.policy_hash

    def sign_event(self, event_data):
        """HMAC-SHA256 signature of the event payload (truncated for demo)."""
        payload = json.dumps(event_data, sort_keys=True).encode()
        signature = hmac.new(
            self.signing_key,
            payload,
            hashlib.sha256
        ).hexdigest()[:8]
        return signature
