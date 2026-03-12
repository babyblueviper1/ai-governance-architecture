import json
import hashlib
import hmac
import time
from datetime import datetime, timezone

def utcnow_iso() -> str:
    """Return current UTC time in ISO 8601 format with Z suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DRVL:
    """Demo Runtime Verification Layer – policy enforcement + tamper-evident signing."""

    def __init__(self):
        self.secret_key: bytes = b"drvl-demo-secret"  # In real use: load from secure store/env

        # Policy rules – deterministic order via sort_keys
        self.policy = {
            "READ":   "ALLOW",
            "UPDATE": "ALLOW",
            "DELETE": "ESCALATE",
            "DROP":   "DENY",
        }

        # Canonical policy hash (SHA-256 of sorted JSON)
        policy_json = json.dumps(self.policy, sort_keys=True, separators=(",", ":"))
        self.policy_hash: str = hashlib.sha256(policy_json.encode()).hexdigest()

    # ─────────────────────────────────────────────
    # Event Signing
    # ─────────────────────────────────────────────
    def sign_event(self, payload: dict) -> str:
        """Sign a deterministic canonical representation of the event (excludes signature)."""
        msg_dict = {k: v for k, v in payload.items() if k != "signature"}
        message = json.dumps(msg_dict, sort_keys=True, separators=(",", ":")).encode()
        return hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()

    # ─────────────────────────────────────────────
    # Signature Verification
    # ─────────────────────────────────────────────
    def verify_event_signature(self, event: dict) -> tuple[bool, str]:
        """Verify HMAC signature; constant-time comparison."""
        signature = event.get("signature")
        if not signature:
            return False, "Missing signature"

        payload = {k: v for k, v in event.items() if k != "signature"}
        message = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        expected = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()

        if hmac.compare_digest(signature, expected):
            return True, "Signature valid"
        return False, "Signature mismatch"

    # ─────────────────────────────────────────────
    # Execution Envelope
    # ─────────────────────────────────────────────
    class ExecutionEnvelope:
        """Immutable envelope for proposed actions – used for hashing & nonce."""

        def __init__(self, action: str, table: str):
            self.action: str = action
            self.table: str = table
            self.timestamp: str = utcnow_iso()
            self.nonce: int = time.time_ns()  # nanosecond monotonic

        def compute_hash(self) -> str:
            """Deterministic SHA-256 hash of envelope contents."""
            payload = {
                "action": self.action,
                "table": self.table,
                "timestamp": self.timestamp,
                "nonce": self.nonce,
            }
            return hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode()
            ).hexdigest()

    # ─────────────────────────────────────────────
    # Policy Decision
    # ─────────────────────────────────────────────
    def verify(self, action: str, table: str, environment: str = "demo") -> tuple[bool, bool, str, None, None]:
        """
        Decide whether action is allowed, needs escalation, or is denied.
        Returns: (allowed: bool, needs_escalation: bool, message: str, _, _)
        """
        rule = self.policy.get(action.upper())
        if rule == "ALLOW":
            return True, False, "Allowed by policy", None, None
        if rule == "ESCALATE":
            return False, True, "Escalation required", None, None
        if rule == "DENY":
            return False, False, "Denied by policy", None, None
        # Default-deny unknown actions (safer than "unknown")
        return False, False, f"Unknown action '{action}' – denied", None, None
