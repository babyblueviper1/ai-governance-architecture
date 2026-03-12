import json
import hashlib
import hmac
import time
from datetime import datetime


class DRVL:
    """
    Distributed Runtime Verification Layer (DRVL)
    """

    def __init__(self):
        # single deterministic key
        self.secret_key = b"drvl-demo-secret"

        # policy definition
        self.policy = {
            "READ":   "ALLOW",
            "UPDATE": "ALLOW",
            "DELETE": "ESCALATE",
            "DROP":   "DENY"
        }

        # policy hash
        self.policy_hash = hashlib.sha256(
            json.dumps(self.policy, sort_keys=True).encode()
        ).hexdigest()

    # ─────────────────────────────────────────────
    # Signing
    # ─────────────────────────────────────────────

    def sign_event(self, event: dict) -> str:
        payload = event.copy()

        # NEVER sign the signature field
        payload.pop("signature", None)

        message = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":")
        ).encode()

        return hmac.new(
            self.secret_key,
            message,
            hashlib.sha256
        ).hexdigest()

    # ─────────────────────────────────────────────
    # Verification
    # ─────────────────────────────────────────────

    def verify_event_signature(self, event: dict):
        payload = event.copy()

        signature = payload.pop("signature", None)

        if not signature:
            return False, "Missing signature"

        message = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":")
        ).encode()

        expected = hmac.new(
            self.secret_key,
            message,
            hashlib.sha256
        ).hexdigest()

        if hmac.compare_digest(signature, expected):
            return True, "Signature valid"

        return False, "Signature mismatch"

    # ─────────────────────────────────────────────
    # Policy Enforcement
    # ─────────────────────────────────────────────

    def verify(self, action, table, environment):
        rule = self.policy.get(action.upper())

        if rule == "ALLOW":
            return True, False, "Allowed by policy", self.policy_hash, None

        if rule == "ESCALATE":
            return False, True, "Escalation required", self.policy_hash, None

        if rule == "DENY":
            return False, False, "Denied by policy", self.policy_hash, None

        return False, False, "Unknown action", self.policy_hash, None


class ExecutionEnvelope:
    def __init__(self, action, table):
        self.action = action
        self.table = table
        self.timestamp = datetime.utcnow().isoformat()  # instead of float
        self.nonce = time.time_ns()

    def compute_hash(self):
        payload = {
            "action": self.action,
            "table": self.table,
            "timestamp": self.timestamp,
            "nonce": self.nonce
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
