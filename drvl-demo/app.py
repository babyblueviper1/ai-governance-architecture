from flask import Flask, jsonify, render_template, request, Response
import json
import time
import random
import hashlib
import hmac
import secrets
from threading import Lock

from agent import ProbabilisticAgent      # your LLM/random agent
from drvl import DRVL                     # your policy engine
from audit import handle_event, log_event
from event_bus import publish, subscribe, get_events  # your pub/sub
from database import Database             # your DB mock/real

app = Flask(__name__)
subscribe(handle_event)

# Config
ENVIRONMENT = "demo"
DEMO_TAMPER_PROBABILITY = 0.15

# Components
agent = ProbabilisticAgent()
db = Database()
drvl = DRVL()

# Thread-safe escalation queue (still in-memory → use Redis/DB in prod)
escalation_lock = Lock()
escalation_queue = []           # list of dicts
escalation_counter = 0

class ExecutionEnvelope:
    """Immutable action proposal with replay protection."""
    def __init__(self, action: str, table: str, params: dict | None = None):
        self.action = action
        self.table = table
        self.params = params or {}
        self.timestamp = time.time()
        self.nonce = secrets.token_hex(16)

    def to_dict(self):
        return {
            "action": self.action,
            "table": self.table,
            "params": self.params,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }

    def compute_hash(self) -> str:
        serialized = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode()).hexdigest()


def create_signed_event(event_data: dict) -> dict:
    event = event_data.copy()
    event["policy"] = drvl.policy_hash
    event["signature"] = drvl.sign_event(event)

    # Demo tampering (remove in production!)
    if random.random() < DEMO_TAMPER_PROBABILITY:
        tamper = random.choice(["policy", "signature", "both"])
        if tamper in ("policy", "both"):
            event["policy"] = "fake" + event["policy"][4:]
        if tamper in ("signature", "both"):
            sig = event["signature"]
            event["signature"] = sig[:8] + "DEAD" + sig[12:]

    return event


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/policy_hash")
def policy_hash():
    return jsonify({"policy_hash": drvl.policy_hash})


@app.route("/verification_key")
def verification_key():
    # WARNING: Exposes HMAC key — protect or remove in real systems!
    try:
        key = next(
            (v for k, v in vars(drvl).items()
             if k in ("secret_key", "hmac_key", "signing_key") and v is not None),
            None
        )
        if key is None:
            return jsonify({"error": "No signing key available"}), 500
        if isinstance(key, bytes):
            key = key.hex()
        return jsonify({"key": key})
    except Exception as e:
        print(f"Verification key error: {e}")
        return jsonify({"error": "Key retrieval failed"}), 500


@app.route("/run")
def run_demo():
    global escalation_counter

    # Agent proposes
    action, table = agent.generate_action()
    llm_error = getattr(agent, "last_llm_error", None)
    if llm_error:
        agent.last_llm_error = None

    envelope = ExecutionEnvelope(action=action, table=table)

    allowed, needs_escalation, message, _, _ = drvl.verify(action, table, ENVIRONMENT)

    status = None
    result = None
    request_id = None

    event = {
        "action": action,
        "table": table,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "nonce": envelope.nonce,
        "envelope_hash": envelope.compute_hash(),
    }

    if needs_escalation:
        with escalation_lock:
            escalation_counter += 1
            request_id = escalation_counter

            r = random.random()
            if r < 0.35:  # auto-approve
                status = "APPROVED"
                result = db.execute(action, table)
                event.update({"status": "EXECUTED", "message": "Auto-approved (demo)"})
            elif r < 0.70:  # auto-deny
                status = "DENIED"
                event.update({"status": "BLOCKED", "message": "Auto-denied (demo)"})
            else:  # pending
                status = "PENDING"
                escalation_queue.append({
                    "id": request_id,
                    "action": action,
                    "table": table,
                    "status": "PENDING",
                    "envelope_hash": envelope.compute_hash(),
                    "requested_at": time.time(),
                })
                event.update({"status": "PENDING", "message": "Escalation pending", "request_id": request_id})
    else:
        if allowed:
            status = "EXECUTED"
            result = db.execute(action, table)
        else:
            status = "BLOCKED"
        event.update({"status": status, "message": message})

    log_event(action, table, status, message)
    signed = create_signed_event(event)
    publish(signed)

    return jsonify({
        "action": action,
        "table": table,
        "status": status,
        "message": message,
        "result": result,
        "request_id": request_id,
        "escalation_queue": [
            {
                "request_id": q["id"],
                "action": q["action"],
                "table": q["table"],
                "status": q["status"],
                "envelope_hash": q["envelope_hash"],
            } for q in escalation_queue
        ],
        "llm_error": llm_error,
        "policy": drvl.policy_hash,
        "signature": signed.get("signature"),
        "envelope_hash": event["envelope_hash"],
    })


@app.route("/approve/<int:req_id>", methods=["POST"])
def approve(req_id):
    with escalation_lock:
        for i, req in enumerate(escalation_queue):
            if req["id"] == req_id and req["status"] == "PENDING":
                # Execute the action
                result = db.execute(req["action"], req["table"])
                req["status"] = "APPROVED"
                req["decided_at"] = time.time()
                # Optional: remove after decision
                # del escalation_queue[i]
                event = {
                    "type": "escalation_decision",
                    "request_id": req_id,
                    "status": "APPROVED",
                    "action": req["action"],
                    "table": req["table"],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "envelope_hash": req["envelope_hash"],
                }
                signed = create_signed_event(event)
                publish(signed)
                return jsonify({
                    "status": "approved",
                    "escalation_queue": [
                        {"request_id": q["id"], "action": q["action"], "table": q["table"], "status": q["status"]}
                        for q in escalation_queue
                    ]
                })
    return jsonify({"error": "Request not found or not pending"}), 404


@app.route("/deny/<int:req_id>", methods=["POST"])
def deny(req_id):
    with escalation_lock:
        for i, req in enumerate(escalation_queue):
            if req["id"] == req_id and req["status"] == "PENDING":
                req["status"] = "DENIED"
                req["decided_at"] = time.time()
                # Optional: del escalation_queue[i]
                event = {
                    "type": "escalation_decision",
                    "request_id": req_id,
                    "status": "DENIED",
                    "action": req["action"],
                    "table": req["table"],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "envelope_hash": req["envelope_hash"],
                }
                signed = create_signed_event(event)
                publish(signed)
                return jsonify({
                    "status": "denied",
                    "escalation_queue": [
                        {"request_id": q["id"], "action": q["action"], "table": q["table"], "status": q["status"]}
                        for q in escalation_queue
                    ]
                })
    return jsonify({"error": "Request not found or not pending"}), 404


@app.route("/status")
def status():
    with escalation_lock:
        return jsonify({
            "escalation_queue": [
                {
                    "request_id": q["id"],
                    "action": q["action"],
                    "table": q["table"],
                    "status": q["status"],
                    "envelope_hash": q.get("envelope_hash"),
                } for q in escalation_queue
            ]
        })


@app.route("/set_llm_key", methods=["POST"])
def set_llm_key():
    try:
        data = request.json
        provider = data.get("provider")
        api_key = data.get("api_key")

        if provider != "openai" or not api_key:
            return jsonify({"error": "Invalid provider or missing key"}), 400

        # In real code: store in session, env, or pass to agent
        # Here we just simulate success
        # agent.set_llm_credentials(provider, api_key)  # ← you'd implement this
        print(f"[DEMO] Received OpenAI key: {api_key[:10]}...")

        return jsonify({"status": "ok", "message": "LLM credentials accepted (session only)"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/events")
def events():
    def generate():
        while True:
            events = get_events()  # your event bus should yield new events
            for event in events:
                yield f"data: {json.dumps(event)}\n\n"
            time.sleep(0.3)  # tune as needed

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
