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

    class ExecutionEnvelope:
        """Lightweight authorization boundary object between validation and execution."""
        def __init__(self, action: str, table: str, params: dict | None = None):
            self.action = action
            self.table = table
            self.params = params or {}
            self.timestamp = time.time()
            self.nonce = time.time_ns()  # simple replay protection

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

    def verify(self, action, table, environment="demo"):
        """
        Verify action against policy and return decision + envelope.

        Returns:
            allowed (bool)
            needs_escalation (bool)
            message (str)
            policy_hash (str)
            envelope (ExecutionEnvelope)  # new: boundary object
        """
        envelope = self.ExecutionEnvelope(action=action, table=table)

        if action in self.FORBIDDEN:
            return False, False, self.FORBIDDEN[action], self.policy_hash, envelope

        if action in self.ESCALATION_REQUIRED:
            return False, True, self.ESCALATION_REQUIRED[action], self.policy_hash, envelope

        return True, False, "Allowed operation", self.policy_hash, envelope

    def sign_event(self, event_data):
        """HMAC-SHA256 signature with nonce and version for replay protection and schema tracking."""
        payload = {
            "version": self.version,
            "nonce": str(time.time_ns()),
            **event_data
        }
        
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        
        signature = hmac.new(
            self.signing_key,
            canonical,
            hashlib.sha256
        ).hexdigest()[:16]
        
        return signature
