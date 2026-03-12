import json
import hashlib
import hmac
import time


class DRVL:
    """
    Distributed Runtime Verification Layer (DRVL)

    Provides:
    - deterministic policy enforcement
    - escalation signaling
    - policy attestation via policy hash
    - signed runtime events for auditability
    - lightweight execution envelope for boundary separation
    - event signature verification (added for tampering detection demo)
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

        # Deterministic policy hash (shortened for demo readability)
        self.policy_hash = hashlib.sha256(
            json.dumps(self.policy, sort_keys=True).encode()
        ).hexdigest()[:8]

        # Demo signing key — in production: securely stored, rotated, HSM/etc.
        self.signing_key = b"drvl-demo-secret-key-2026"

        # Event schema version
        self.version = "1.0"

    class ExecutionEnvelope:
        """Lightweight authorization boundary object between validation and execution."""
        def __init__(self, action: str, table: str, params: dict | None = None):
            self.action = action
            self.table = table
            self.params = params or {}
            self.timestamp = time.time()
            self.nonce = time.time_ns()  # simple replay protection (nanoseconds)

        def to_dict(self) -> dict:
            return {
                "action": self.action,
                "table": self.table,
                "params": self.params,
                "timestamp": self.timestamp,
                "nonce": self.nonce,
            }

        def compute_hash(self) -> str:
            """Deterministic SHA-256 hash of the envelope (truncated for demo readability)."""
            serialized = json.dumps(self.to_dict(), sort_keys=True)
            return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def verify(self, action: str, table: str, environment: str = "demo"):
        """
        Verify action against policy.

        Returns:
            allowed (bool)
            needs_escalation (bool)
            message (str)
            policy_hash (str)
            envelope (ExecutionEnvelope)
        """
        envelope = self.ExecutionEnvelope(action=action, table=table)

        if action in self.FORBIDDEN:
            return False, False, self.FORBIDDEN[action], self.policy_hash, envelope

        if action in self.ESCALATION_REQUIRED:
            return False, True, self.ESCALATION_REQUIRED[action], self.policy_hash, envelope

        # Default: allow anything not explicitly forbidden or escalated
        return True, False, "Allowed operation", self.policy_hash, envelope

    def sign_event(self, event_data: dict) -> str:
        """
        HMAC-SHA256 signature with version and nonce for replay protection and schema tracking.
        Note: nonce is re-generated here → verification needs to use the event's own nonce.
        """
        payload = {
            "version": self.version,
            # Use the nonce from the event if present, otherwise generate one
            "nonce": event_data.get("nonce", str(time.time_ns())),
            **{k: v for k, v in event_data.items() if k not in ["signature", "verified", "verify_message"]}
        }

        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')

        signature = hmac.new(
            self.signing_key,
            canonical,
            hashlib.sha256
        ).hexdigest()[:16]

        return signature

    def verify_event_signature(self, event: dict) -> tuple[bool, str]:
        """
        Verify the HMAC signature of an event.

        Returns:
            (valid: bool, message: str)
        """
        # Rebuild the exact payload that was signed
        payload = {
            "version": self.version,
            "nonce": event.get("nonce", ""),  # must match what was signed
            **{k: v for k, v in event.items()
               if k not in [
                   "signature", "verified", "verify_message",
                   "tampered", "tamper_type", "color", "envelope_hash"
               ]}
        }

        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')

        computed_signature = hmac.new(
            self.signing_key,
            canonical,
            hashlib.sha256
        ).hexdigest()[:16]

        received_signature = event.get("signature", "")

        valid = received_signature == computed_signature

        if valid:
            msg = "Signature valid"
        else:
            tamper_info = event.get("tamper_type", "unknown")
            msg = f"✗ Signature invalid (tampered: {tamper_info})"

        return valid, msg
