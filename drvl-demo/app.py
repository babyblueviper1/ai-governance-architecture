from flask import Flask, jsonify, render_template, request, Response
import json
import time
import random
from threading import Lock

# Your custom modules
from agent import ProbabilisticAgent
from drvl import DRVL
from audit import handle_event, log_event
from event_bus import publish, subscribe, get_events
from database import Database

app = Flask(__name__)
subscribe(handle_event)

# ────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────

ENVIRONMENT = "demo"

DEMO_TAMPER_PROBABILITY = 0.15

AUTO_APPROVE_PCT = 0.35
AUTO_DENY_PCT = 0.35

# Rate limit protection
last_run_time = 0

# Components
agent = ProbabilisticAgent()
db = Database()
drvl = DRVL()

print("DRVL policy hash:", drvl.policy_hash)

# Escalation queue
escalation_lock = Lock()
escalation_queue = []
escalation_counter = 0

# ────────────────────────────────────────────────
# Tampering + Signing
# ────────────────────────────────────────────────
def create_signed_event(event_data: dict) -> dict:
    """Attach policy hash and signature deterministically, optionally tamper for demo"""

    event = event_data.copy()
    event["policy"] = drvl.policy_hash

    # Build a deterministic payload for signing (freeze only the fields that matter)
    payload = {
        "action": event.get("action"),
        "table": event.get("table"),
        "timestamp": event.get("timestamp"),
        "nonce": event.get("envelope_hash"),  # or event.get("nonce") if preferred
        "status": event.get("status"),
        "message": event.get("message"),
        "policy": event.get("policy"),
        "envelope_hash": event.get("envelope_hash"),
    }

    # Generate signature
    event["signature"] = drvl.sign_event(payload)
    event["tampered"] = False
    event["tamper_type"] = None
    event["verified"] = True
    event["verify_message"] = "Signature valid"

    # Optional demo tampering
    if ENVIRONMENT == "demo" and random.random() < DEMO_TAMPER_PROBABILITY:
        tamper_choice = random.choice(["policy", "signature", "both"])
        event["tampered"] = True
        event["tamper_type"] = tamper_choice

        if tamper_choice in ("policy", "both"):
            event["policy"] = "fake_" + event["policy"][5:]

        if tamper_choice in ("signature", "both"):
            sig = event["signature"]
            event["signature"] = sig[:4] + "BEEF" + sig[8:] if len(sig) > 12 else "deadbeef12345678"

    # Verification uses the **same deterministic payload** for consistency
    valid, msg = drvl.verify_event_signature({
        **payload,
        "policy": event["policy"],
        "signature": event["signature"]
    })

    event["verified"] = valid
    event["verify_message"] = msg

    return event


# ────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/policy_hash")
def policy_hash():
    return jsonify({"policy_hash": drvl.policy_hash})


@app.route("/verification_key")
def verification_key():

    try:

        key = None

        if hasattr(drvl, "secret_key"):
            key = drvl.secret_key
        elif hasattr(drvl, "hmac_key"):
            key = drvl.hmac_key
        elif hasattr(drvl, "signing_key"):
            key = drvl.signing_key

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
        return jsonify({"error": "Too many requests"}), 429

    last_run_time = now

    # Simulate agent / LLM thinking
    time.sleep(random.uniform(1.2, 2.5))

    action, table = agent.generate_action()

    llm_error = getattr(agent, "last_llm_error", None)
    if llm_error:
        agent.last_llm_error = None

    envelope = drvl.ExecutionEnvelope(action=action, table=table)

    allowed, needs_escalation, message, _, _ = drvl.verify(
        action, table, ENVIRONMENT
    )

    result = None
    request_id = None
    color_hint = None
    status = None

    event = {
        "action": action,
        "table": table,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "nonce": envelope.nonce,
        "envelope_hash": envelope.compute_hash(),
    }

    # Escalation logic
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
                    "requested_at": time.time()
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
                "envelope_hash": q["envelope_hash"]
            }
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


# ────────────────────────────────────────────────
# Escalation Decisions
# ────────────────────────────────────────────────

@app.route("/approve/<int:req_id>", methods=["POST"])
def approve(req_id):

    with escalation_lock:

        for req in escalation_queue:

            if req["id"] == req_id and req["status"] == "PENDING":

                db.execute(req["action"], req["table"])

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

                publish(create_signed_event(event))

                break

    return status()


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

                publish(create_signed_event(event))

                break

    return status()


# ────────────────────────────────────────────────
# Status
# ────────────────────────────────────────────────

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
                    "envelope_hash": q["envelope_hash"]
                }
                for q in escalation_queue
            ]
        })


# ────────────────────────────────────────────────
# Live Events (SSE)
# ────────────────────────────────────────────────

@app.route("/events")
def events():

    def generate():

        last_index = 0

        while True:

            events_list = get_events()

            if last_index < len(events_list):

                new_events = events_list[last_index:]

                for ev in new_events:
                    yield f"data: {json.dumps(ev)}\n\n"

                last_index = len(events_list)

            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")


# ────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
