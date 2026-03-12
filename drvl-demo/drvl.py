import json
import hashlib
import hmac


class DRVL:
    """
    Distributed Runtime Verification Layer (DRVL)

    Provides:
    - deterministic policy enforcement
    - escalation signaling
    - policy attestation via policy hash
    - signed runtime events for auditability
    """

    ESCALATION_REQUIRED = {
        "DELETE": "Requires escalation"
    }

    FORBIDDEN = {
        "DROP": "Forbidden operation"
    }

    def __init__(self):
        # Policy definition
        self.policy = {
            "READ": "allow",
            "UPDATE": "allow",
            "DELETE": "escalate",
            "DROP": "deny"
        }

        # Deterministic policy hash
        self.policy_hash = hashlib.sha256(
            json.dumps(self.policy, sort_keys=True).encode()
        ).hexdigest()[:8]

        # Demo signing key
        # In production this should be stored securely and rotated
        self.signing_key = b"drvl-demo-secret-key-2026"

        # Event schema version
        self.version = "1.0"

    def verify(self, action, table, environment="demo"):
        """
        Verify action against policy.

        Returns:
        allowed (bool)
        needs_escalation (bool)
        message (str)
        policy_hash (str)
        """

        if action in self.FORBIDDEN:
            return False, False, self.FORBIDDEN[action], self.policy_hash

        if action in self.ESCALATION_REQUIRED:
            return False, True, self.ESCALATION_REQUIRED[action], self.policy_hash

        return True, False, "Allowed operation", self.policy_hash

   def sign_event(self, event_data):

    event_data["version"] = self.version

    canonical = json.dumps(
        event_data,
        sort_keys=True,
        separators=(",", ":")
    ).encode("utf-8")

    signature = hmac.new(
        self.signing_key,
        canonical,
        hashlib.sha256
    ).hexdigest()[:16]

    return signature
