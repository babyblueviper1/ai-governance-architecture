from flask import Flask, jsonify, render_template, Response, request
import json
import time
import random
import hashlib
import hmac

from agent import ProbabilisticAgent
from drvl import DRVL
from audit import handle_event, log_event
from event_bus import publish, subscribe, get_events
from database import Database

app = Flask(__name__)
subscribe(handle_event)

environment = "demo"
agent = ProbabilisticAgent()
db = Database()
drvl = DRVL()

# Escalation tracking
escalation_queue = []
escalation_counter = 0


# Lightweight execution envelope — formal boundary between validation and execution
class ExecutionEnvelope:
    """Authorization boundary object — separates proposal from execution."""
    def __init__(self, action: str, table: str, params: dict | None = None):
        self.action = action
        self.table = table
        self.params = params or {}
        self.timestamp = time.time()
        self.nonce = time.time_ns()  # replay protection

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "table": self.table,
            "params": self.params,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }

    def compute_hash(self) -> str:
        """Deterministic short hash for demo visibility."""
        serialized = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]


def publish_signed_event(event_data):
    """Add policy hash and HMAC signature before publishing — sometimes tamper for demo"""
    
    # Normal path
    event_data["policy"] = drvl.policy_hash
    event_data["signature"] = drvl.sign_event(event_data)
    
    # ~15% tampered events for demo
    if random.random() < 0.15:
        tamper_type = random.choice(["policy", "signature", "both"])
        
        if tamper_type in ("policy", "both"):
            event_data["policy"] = "fake" + drvl.policy_hash[4:]
            
        if tamper_type in ("signature", "both"):
            real_sig = event_data["signature"]
            event_data["signature"] = real_sig[:8] + "DEAD" + real_sig[12:]
    
    publish(event_data)


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/policy_hash")
def policy_hash():
    return jsonify({
        "policy_hash": drvl.policy_hash
    })


@app.route("/run")
def run_demo():
    global escalation_counter

    llm_error = None
    action, table = agent.generate_action()

    if hasattr(agent, "last_llm_error") and agent.last_llm_error:
        llm_error = agent.last_llm_error
        agent.last_llm_error = None

    # Create envelope BEFORE verification — this is the proposal boundary
    envelope = ExecutionEnvelope(action=action, table=table)

    # Verify — note: drvl.verify now returns envelope too (update drvl.py accordingly)
    allowed, needs_escalation, message, policy_hash, envelope = drvl.verify(action, table, environment)

    status = ""
    result = None
    req_id = None

    # Base event
    event = {
        "action": action,
        "table": table,
        "timestamp": time.strftime("%H:%M:%S"),
        "nonce": time.time_ns(),
        "envelope_hash": envelope.compute_hash(),  # ← core new field
    }

    if needs_escalation:
        escalation_counter += 1
        req_id = escalation_counter
        event["request_id"] = req_id

        rand = random.random()
        if rand < 0.35:
            status = "APPROVED"
            result = db.execute(action, table)
            event.update({
                "status": "EXECUTED",
                "message": "Auto-approved (demo)"
            })
        elif rand < 0.70:
            status = "DENIED"
            event.update({
                "status": "BLOCKED",
                "message": "Auto-denied (demo)"
            })
            result = None
        else:
            status = "PENDING"
            escalation_queue.append({
                "id": req_id,
                "action": action,
                "table": table,
                "status": status,
                "envelope_hash": envelope.compute_hash()  # traceable in queue
            })
            event.update({
                "status": "PENDING",
                "message": "Escalation pending"
            })
    else:
        if allowed:
            status = "EXECUTED"
            result = db.execute(action, table)
        else:
            status = "BLOCKED"
            result = None

        event.update({
            "status": status,
            "message": message
        })

    # Final log & publish
    log_event(action, table, status, message)
    publish_signed_event(event)

    # Response — include envelope hash for UI display
    return jsonify({
        "action": action,
        "table": table,
        "status": status,
        "message": message,
        "result": result,
        "request_id": req_id,
        "escalation_queue": [
            {
                "request_id": req["id"],
                "action": req["action"],
                "table": req["table"],
                "status": req["status"],
                "envelope_hash": req.get("envelope_hash")  # optional
            } for req in escalation_queue
        ],
        "llm_error": llm_error,
        "policy": drvl.policy_hash,
        "signature": event.get("signature"),
        "envelope_hash": event["envelope_hash"]  # new
    })


# ... rest of your routes unchanged (approve, deny, status, policy_hash, logs, set_llm_key, events) ...

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
