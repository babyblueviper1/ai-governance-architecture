# app.py
from flask import Flask, jsonify, render_template, request, Response
import json
import time
import os
import random
from threading import Lock
from datetime import datetime


# Custom modules (assuming these exist in your project)
from agent import ProbabilisticAgent
from drvl import DRVL
from audit import handle_event, log_event
from event_bus import publish, subscribe, get_events
from database import Database

app = Flask(__name__)
subscribe(handle_event)

# ──────────────────────────────
# Configuration
# ──────────────────────────────

ENVIRONMENT = "demo"
DEMO_TAMPER_PROBABILITY = 0.15
AUTO_APPROVE_PCT = 0.35
AUTO_DENY_PCT = 0.35

last_run_time = 0

agent = ProbabilisticAgent()
db = Database()
drvl = DRVL()

print("DRVL policy hash:", drvl.policy_hash)

escalation_lock = Lock()
escalation_queue = []
escalation_counter = 0

# ──────────────────────────────
# Tampering + Signing
# ──────────────────────────────

def create_signed_event(event_data: dict) -> dict:
    """Attach policy hash and signature deterministically, optionally tamper for demo"""
    event = event_data.copy()
    event["policy"] = drvl.policy_hash

    # Freeze payload deterministically for signing
    payload = {
        "action": event.get("action"),
        "table": event.get("table"),
        "timestamp": event.get("timestamp"),
        "nonce": event.get("envelope_hash"),
        "status": event.get("status"),
        "message": event.get("message"),
        "policy": event.get("policy"),
        "envelope_hash": event.get("envelope_hash"),
    }

    # Sign deterministically
    event["signature"] = drvl.sign_event(payload)
    event["tampered"] = False
    event["tamper_type"] = None
    event["verified"] = True
    event["verify_message"] = "Signature valid"

    # Optional demo tampering (~15% of events)
    if ENVIRONMENT == "demo" and random.random() < DEMO_TAMPER_PROBABILITY:
        tamper_choice = random.choice(["policy", "signature", "both"])
        event["tampered"] = True
        event["tamper_type"] = tamper_choice

        if tamper_choice in ("policy", "both"):
            event["policy"] = "fake_" + event["policy"][5:] if len(event["policy"]) > 5 else "fake_policy"

        if tamper_choice in ("signature", "both"):
            sig = event["signature"]
            event["signature"] = sig[:4] + "BEEF" + sig[8:] if len(sig) > 12 else "deadbeef12345678"

    # Re-verify using same deterministic payload (good practice)
    valid, msg = drvl.verify_event_signature({
        **payload,
        "policy": event["policy"],
        "signature": event["signature"]
    })

    event["verified"] = valid
    event["verify_message"] = msg

    return event

# ──────────────────────────────
# Routes
# ──────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/policy_hash")
def policy_hash():
    try:
        return jsonify({"hash": drvl.policy_hash})  # ← FIXED: frontend expects "hash"
    except Exception as e:
        print(f"Error serving policy_hash: {e}")
        return jsonify({"error": "Could not retrieve policy hash"}), 500

@app.route("/verification_key")
def verification_key():
    try:
        key = getattr(drvl, "secret_key", None)
        if key is None:
            return jsonify({"error": "No verification key available"}), 500
        if isinstance(key, bytes):
            key = key.hex()
        return jsonify({"key": key})
    except Exception as e:
        print("Verification key error:", e)
        return jsonify({"error": "verification key failure"}), 500

@app.route("/run")
def run_demo():
    global escalation_counter, last_run_time

    now = time.time()
    if now - last_run_time < 0.8:
        return jsonify({"error": "Rate limit: wait 0.8s between /run calls"}), 429
    last_run_time = now

    time.sleep(random.uniform(1.2, 2.5))  # simulate agent "thinking"

    action, table = agent.generate_action()
    llm_error = getattr(agent, "last_llm_error", None)
    if llm_error:
        agent.last_llm_error = None

    envelope = drvl.ExecutionEnvelope(action=action, table=table)
    allowed, needs_escalation, message, _, _ = drvl.verify(action, table, ENVIRONMENT)

    # Use deterministic timestamp for signing
    event_timestamp = datetime.utcnow().isoformat()
    event = {
        "action": action,
        "table": table,
        "timestamp": event_timestamp,
        "nonce": envelope.nonce,
        "envelope_hash": envelope.compute_hash(),
    }

    # Escalation / decision logic
    result = None
    request_id = None
    color_hint = None
    status = None

    if needs_escalation:
        r = random.random()
        if r < AUTO_APPROVE_PCT:
            status = "EXECUTED"
            color_hint = "green"
            result = db.execute(action, table)
            event.update({"status": status, "message": "Auto-approved (~35%)", "color": color_hint})
        elif r < AUTO_APPROVE_PCT + AUTO_DENY_PCT:
            status = "BLOCKED"
            color_hint = "red"
            event.update({"status": status, "message": "Auto-denied (~35%)", "color": color_hint})
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
                    "requested_at": time.time()
                })
            status = "PENDING"
            color_hint = "pending"
            event.update({"status": status, "message": "Awaiting review (~30%)", "request_id": request_id, "color": color_hint})
    else:
        if allowed:
            status = "EXECUTED"
            color_hint = "green"
            result = db.execute(action, table)
        else:
            status = "BLOCKED"
            color_hint = "red"
        event.update({"status": status, "message": message, "color": color_hint})

    log_event(action, table, status, message, timestamp=event_timestamp, policy=drvl.policy_hash)

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
            {"request_id": q["id"], "action": q["action"], "table": q["table"], "status": q["status"], "envelope_hash": q["envelope_hash"]}
            for q in escalation_queue
        ],
        "llm_error": llm_error,
        "policy": signed.get("policy"),
        "signature": signed.get("signature"),
        "envelope_hash": event["envelope_hash"],
        "tampered": signed.get("tampered"),
        "tamper_type": signed.get("tamper_type"),
        "verified": signed.get("verified"),
        "verify_message": signed.get("verify_message"),
    })

# ──────────────────────────────
# Escalation endpoints
# ──────────────────────────────

@app.route("/approve/<int:req_id>", methods=["POST"])
def approve(req_id):
    with escalation_lock:
        for req in escalation_queue:
            if req["id"] == req_id and req["status"] == "PENDING":
                db.execute(req["action"], req["table"])
                req["status"] = "APPROVED"
                req["decided_at"] = time.time()
                event_timestamp = datetime.utcnow().isoformat()
                event = {
                    "type": "escalation_decision",
                    "request_id": req_id,
                    "status": "APPROVED",
                    "action": req["action"],
                    "table": req["table"],
                    "timestamp": event_timestamp,
                    "envelope_hash": req["envelope_hash"],
                }
                publish(create_signed_event(event))
                break
    return status()

@app.route("/deny/<int:req_id>", methods=["POST"])
def deny(req_id):
    with escalation_lock:
        for req in escalation_queue:
            if req["id"] == req_id and req["status"] == "PENDING":
                req["status"] = "DENIED"                    # ← fix here
                req["decided_at"] = time.time()
                event_timestamp = datetime.utcnow().isoformat()
                event = {
                    "type": "escalation_decision",
                    "request_id": req_id,
                    "status": "DENIED",
                    "action": req["action"],
                    "table": req["table"],
                    "timestamp": event_timestamp,
                    "envelope_hash": req["envelope_hash"],
                }
                publish(create_signed_event(event))
                break
    return status()

if __name__ == "__main__":
    # For local development/testing
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
