from flask import Flask, jsonify, render_template, request, Response
import json
import time
import os
import random
from threading import Lock
from datetime import datetime
from queue import Queue, Empty

# Custom modules (assuming these exist)
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
AUTO_APPROVE_PCT = 0.25
AUTO_DENY_PCT = 0.25

last_run_time = 0

agent = ProbabilisticAgent()
db = Database()
drvl = DRVL()

print("DRVL policy hash:", drvl.policy_hash)

escalation_lock = Lock()
escalation_queue = []
escalation_counter = 0

# Simple in-memory event queue for SSE
event_queue = Queue()
MAX_QUEUED_EVENTS = 100

def broadcast_event(event):
    """Publish to callbacks + add to SSE queue"""
    publish(event)
    event_queue.put(event)
    while event_queue.qsize() > MAX_QUEUED_EVENTS:
        try:
            event_queue.get_nowait()
        except Empty:
            pass

# ──────────────────────────────
# Tampering + Signing
# ──────────────────────────────

def create_signed_event(event_data: dict) -> dict:
    event = event_data.copy()
    event["policy"] = drvl.policy_hash

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

    event["signature"] = drvl.sign_event(payload)
    event["tampered"] = False
    event["tamper_type"] = None
    event["verified"] = True
    event["verify_message"] = "Signature valid"

    if ENVIRONMENT == "demo" and random.random() < DEMO_TAMPER_PROBABILITY:
        tamper_choice = random.choice(["policy", "signature", "both"])
        event["tampered"] = True
        event["tamper_type"] = tamper_choice
        if tamper_choice in ("policy", "both"):
            event["policy"] = "fake_" + event["policy"][5:] if len(event["policy"]) > 5 else "fake_policy"
        if tamper_choice in ("signature", "both"):
            sig = event["signature"]
            event["signature"] = sig[:4] + "BEEF" + sig[8:] if len(sig) > 12 else "deadbeef12345678"

    valid, msg = drvl.verify_event_signature({
        **payload,
        "policy": event["policy"],
        "signature": event["signature"]
    })

    event["verified"] = valid
    event["verify_message"] = msg

    return event

# ──────────────────────────────
# SSE Endpoint
# ──────────────────────────────

@app.route("/events")
def events():
    def event_stream():
        while True:
            try:
                event = event_queue.get(timeout=15)
                yield f"data: {json.dumps(event)}\n\n"
            except Empty:
                yield ": ping\n\n"
            except GeneratorExit:
                break

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

# ──────────────────────────────
# Routes
# ──────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/policy_hash")
def policy_hash():
    return jsonify({"hash": drvl.policy_hash})

@app.route("/set_llm_key", methods=["POST"])
def set_llm_key():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        provider = data.get("provider")
        api_key = data.get("api_key")

        if not provider or not api_key:
            return jsonify({"error": "Provider and API key required"}), 400

        if provider.lower() != "openai":
            return jsonify({"error": "Only OpenAI supported"}), 400

        agent.set_llm(provider, api_key)

        try:
            agent.llm_client.models.list()
        except Exception as e:
            agent.llm_client = None
            return jsonify({"error": f"Invalid API key: {str(e)}"}), 401

        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"Set LLM key error: {e}")
        return jsonify({"error": "Activation failed"}), 500

@app.route("/run")
def run_demo():
    global escalation_counter, last_run_time

    now = time.time()
    if now - last_run_time < 0.8:
        return jsonify({"error": "Rate limit: wait 0.8s"}), 429
    last_run_time = now

    time.sleep(random.uniform(0.3, 0.8))

    action, table = agent.generate_action()
    llm_error = getattr(agent, "last_llm_error", None)
    if llm_error:
        agent.last_llm_error = None

    envelope = drvl.ExecutionEnvelope(action=action, table=table)
    event_timestamp = datetime.utcnow().isoformat()

    event = {
        "action": action,
        "table": table,
        "timestamp": event_timestamp,
        "nonce": envelope.nonce,
        "envelope_hash": envelope.compute_hash(),
    }

    # First, create signed event (with potential tamper)
    signed = create_signed_event(event.copy())

    status = None
    result = None
    request_id = None
    color_hint = None
    message = ""

    # CRITICAL: Check verification BEFORE any execution or escalation
    if not signed["verified"]:
        status = "TAMPERED"
        message = signed["verify_message"] or "Signature / policy mismatch - action rejected"
        color_hint = "red"
        result = {"blocked": True, "reason": "tampered"}
        print(f"Tampered event detected: {signed['verify_message']}")

    else:
        # Only proceed if verified
        allowed, needs_escalation, verify_message, _, _ = drvl.verify(action, table, ENVIRONMENT)
        message = verify_message or ""

        if needs_escalation:
            r = random.random()
            if r < AUTO_APPROVE_PCT:
                status = "APPROVED"
                color_hint = "green"
                try:
                    result = db.execute(action, table) or {"executed": True, "rows_affected": 1}
                    message += " (auto-approved)"
                except Exception as e:
                    result = {"error": str(e)}
                    status = "BLOCKED"
                    message = f"Execution failed: {e}"
            elif r < AUTO_APPROVE_PCT + AUTO_DENY_PCT:
                status = "DENIED"
                color_hint = "red"
                message += " (auto-denied)"
                result = {"blocked": True}
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
                message += " (awaiting review)"
                result = {"pending": True, "request_id": request_id}
        else:
            if allowed:
                status = "EXECUTED"
                color_hint = "green"
                try:
                    result = db.execute(action, table) or {"executed": True, "rows_affected": 1}
                except Exception as e:
                    result = {"error": str(e)}
                    status = "BLOCKED"
                    color_hint = "red"
                    message = f"Execution failed: {e}"
            else:
                status = "BLOCKED"
                color_hint = "red"
                result = {"blocked": True}

    log_event(action, table, status, message, timestamp=event_timestamp, policy=drvl.policy_hash)

    # Finalize signed event with correct status
    signed["status"] = status
    signed["message"] = message
    broadcast_event(signed)

    return jsonify({
        "action": action,
        "table": table,
        "status": status,
        "message": message,
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
                try:
                    result = db.execute(req["action"], req["table"]) or {"executed": True, "rows_affected": 1}
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
                        "result": result
                    }
                    signed = create_signed_event(event)
                    broadcast_event(signed)
                except Exception as e:
                    print(f"Approve execution failed for {req_id}: {e}")
                    return jsonify({"error": str(e)}), 500
                break
    return status()

@app.route("/deny/<int:req_id>", methods=["POST"])
def deny(req_id):
    with escalation_lock:
        for req in escalation_queue:
            if req["id"] == req_id and req["status"] == "PENDING":
                req["status"] = "DENIED"
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
                    "result": {"blocked": True}
                }
                signed = create_signed_event(event)
                broadcast_event(signed)
                break
    return status()

@app.route("/status")
def status():
    with escalation_lock:
        pending = sum(1 for q in escalation_queue if q["status"] == "PENDING")
        return jsonify({
            "total_escalations": len(escalation_queue),
            "pending": pending,
            "queue": [
                {"request_id": q["id"], "action": q["action"], "table": q["table"], "status": q["status"]}
                for q in escalation_queue
            ]
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
