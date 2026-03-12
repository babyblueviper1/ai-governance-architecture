from flask import Flask, jsonify, render_template, request, Response
import json
import time
import random
import hashlib
import hmac
import secrets
from threading import Lock

# Your custom modules — adjust import paths/names as needed
from agent import ProbabilisticAgent      # your agent that proposes actions
from drvl import DRVL                     # the policy + signing class you shared
from audit import handle_event, log_event
from event_bus import publish, subscribe, get_events
from database import Database             # mock or real DB

app = Flask(__name__)
subscribe(handle_event)

# ────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────
ENVIRONMENT = "demo"
DEMO_TAMPER_PROBABILITY = 0.15   # 15% of events deliberately tampered (demo only)

# Escalation demo probabilities (only when needs_escalation == True)
AUTO_APPROVE_PCT = 0.35          # ~35% → immediate EXECUTED (green)
AUTO_DENY_PCT    = 0.35          # ~35% → immediate BLOCKED (red)
# Remaining ~30% → PENDING (queue + manual buttons)

# Components
agent = ProbabilisticAgent()
db = Database()
drvl = DRVL()

# Thread-safe in-memory escalation queue (→ Redis/DB in prod)
escalation_lock = Lock()
escalation_queue = []
escalation_counter = 0

# ────────────────────────────────────────────────
# Tampering + Signing Helpers
# ────────────────────────────────────────────────

def create_signed_event(event_data: dict) -> dict:
    event = event_data.copy()
    
    # Normal flow
    event["policy"] = drvl.policy_hash
    event["signature"] = drvl.sign_event(event)
    event["tampered"] = False
    event["tamper_type"] = None
    event["verified"] = True
    event["verify_message"] = "Signature valid"

    # Demo tampering (~15%)
    if ENVIRONMENT == "demo" and random.random() < DEMO_TAMPER_PROBABILITY:
        tamper_choice = random.choice(["policy", "signature", "both"])
        event["tampered"] = True
        event["tamper_type"] = tamper_choice

        if tamper_choice in ("policy", "both"):
            event["policy"] = "fake_" + event["policy"][5:]
        if tamper_choice in ("signature", "both"):
            sig = event["signature"]
            event["signature"] = (sig[:4] + "BEEF" + sig[8:]) if len(sig) > 12 else "deadbeef12345678"

    # Real verification (after possible tampering)
    valid, msg = drvl.verify_event_signature(event)
    event["verified"] = valid
    event["verify_message"] = msg

    return event


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/policy_hash")
def policy_hash():
    return jsonify({"policy_hash": drvl.policy_hash})


@app.route("/run")
def run_demo():
    global escalation_counter

    # Agent proposes
    action, table = agent.generate_action()
    llm_error = getattr(agent, "last_llm_error", None)
    if llm_error:
        agent.last_llm_error = None

    envelope = drvl.ExecutionEnvelope(action=action, table=table)

    allowed, needs_escalation, message, _, _ = drvl.verify(action, table, ENVIRONMENT)

    status = None
    result = None
    request_id = None
    color_hint = None           # "green", "red", "pending"

    event = {
        "action": action,
        "table": table,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "nonce": envelope.nonce,
        "envelope_hash": envelope.compute_hash(),
    }

    if needs_escalation:
        r = random.random()

        if r < AUTO_APPROVE_PCT:
            status = "APPROVED"
            color_hint = "green"
            result = db.execute(action, table)
            event.update({
                "status": "EXECUTED",
                "message": "Auto-approved (~35%)",
                "color": color_hint
            })

        elif r < AUTO_APPROVE_PCT + AUTO_DENY_PCT:
            status = "DENIED"
            color_hint = "red"
            event.update({
                "status": "BLOCKED",
                "message": "Auto-denied (~35%)",
                "color": color_hint
            })

        else:
            with escalation_lock:
                escalation_counter += 1
                request_id = escalation_counter
                escalation_queue.append({
                    "id": request_id,
                    "action": action,
                    "table": table,
                    "status": "PENDING",
                    "envelope_hash": envelope.compute_hash(),
                    "requested_at": time.time(),
                })
            status = "PENDING"
            color_hint = "pending"
            event.update({
                "status": "PENDING",
                "message": "Awaiting review (~30%)",
                "request_id": request_id,
                "color": color_hint
            })

    else:
        if allowed:
            status = "EXECUTED"
            color_hint = "green"
            result = db.execute(action, table)
        else:
            status = "BLOCKED"
            color_hint = "red"
        event.update({
            "status": status,
            "message": message,
            "color": color_hint
        })

    log_event(action, table, status, message)
    signed = create_signed_event(event)
    publish(signed)

    return jsonify({
        "action": action,
        "table": table,
        "status": status,
        "message": message or event.get("message"),
        "color": color_hint,
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
        "tampered": signed.get("tampered"),
        "tamper_type": signed.get("tamper_type"),
        "verified": signed.get("verified"),
        "verify_message": signed.get("verify_message"),
    })


@app.route("/approve/<int:req_id>", methods=["POST"])
def approve(req_id):
    with escalation_lock:
        for req in escalation_queue:
            if req["id"] == req_id and req["status"] == "PENDING":
                result = db.execute(req["action"], req["table"])
                req["status"] = "APPROVED"
                req["decided_at"] = time.time()

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
        for req in escalation_queue:
            if req["id"] == req_id and req["status"] == "PENDING":
                req["status"] = "DENIED"
                req["decided_at"] = time.time()

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


@app.route("/events")
def events():
    def generate():
        while True:
            events_list = get_events()
            for ev in events_list:
                yield f"data: {json.dumps(ev)}\n\n"
            time.sleep(0.3)

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
