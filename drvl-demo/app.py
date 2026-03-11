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


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/run")
def run_demo():
    global escalation_counter

    llm_error = None
    action, table = agent.generate_action()

    # Capture LLM fallback error if it occurred
    if hasattr(agent, "last_llm_error") and agent.last_llm_error:
        llm_error = agent.last_llm_error
        agent.last_llm_error = None  # clear after use

    allowed, needs_escalation, message, policy_hash = drvl.verify(action, table, environment)

    status = ""
    result = None
    req_id = None

    if needs_escalation:
        escalation_counter += 1
        req_id = escalation_counter

        # Demo: probabilistic auto-decision for escalations (DELETE)
        # ~35% auto-approve, ~35% auto-deny, ~30% pending/manual
        rand = random.random()
        if rand < 0.35:
            status = "APPROVED"
            result = db.execute(action, table)
            publish_event = {
                "action": action,
                "table": table,
                "status": "EXECUTED",
                "message": "Auto-approved (demo)",
                "request_id": req_id,
                "timestamp": time.strftime("%H:%M:%S"),
                "policy": policy_hash
            }
            publish_event["signature"] = drvl.sign_event(publish_event)
            publish(publish_event)
        elif rand < 0.70:
            status = "DENIED"
            publish_event = {
                "action": action,
                "table": table,
                "status": "BLOCKED",
                "message": "Auto-denied (demo)",
                "request_id": req_id,
                "timestamp": time.strftime("%H:%M:%S"),
                "policy": policy_hash
            }
            publish_event["signature"] = drvl.sign_event(publish_event)
            publish(publish_event)
            result = None
        else:
            status = "PENDING"
            escalation_queue.append({
                "id": req_id,
                "action": action,
                "table": table,
                "status": status
            })
    else:
        # Non-escalation path: allowed or forbidden (e.g. DROP)
        if allowed:
            status = "EXECUTED"
            result = db.execute(action, table)
        else:
            status = "BLOCKED"
            result = None

    # Final log & publish (only once!)
    log_event(action, table, status, message)

    publish_event = {
        "action": action,
        "table": table,
        "status": status,
        "message": message,
        "request_id": req_id,
        "timestamp": time.strftime("%H:%M:%S"),
        "policy": policy_hash
    }
    publish_event["signature"] = drvl.sign_event(publish_event)
    publish(publish_event)

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
                "status": req["status"]
            } for req in escalation_queue
        ],
        "llm_error": llm_error,
        "policy": policy_hash,
        "signature": publish_event["signature"]
    })


@app.route("/approve/<int:req_id>", methods=["POST"])
def approve_request(req_id):
    for req in escalation_queue[:]:
        if req["id"] == req_id and req["status"] == "PENDING":
            req["status"] = "APPROVED"
            result = db.execute(req["action"], req["table"])

            publish_event = {
                "action": req["action"],
                "table": req["table"],
                "status": "EXECUTED",
                "message": "Escalation manually approved",
                "request_id": req_id,
                "timestamp": time.strftime("%H:%M:%S"),
                "policy": drvl.policy_hash
            }
            publish_event["signature"] = drvl.sign_event(publish_event)
            publish(publish_event)

            escalation_queue.remove(req)

            return jsonify({
                "status": "approved",
                "id": req_id,
                "escalation_queue": [
                    {
                        "request_id": r["id"],
                        "action": r["action"],
                        "table": r["table"],
                        "status": r["status"]
                    } for r in escalation_queue
                ]
            })

    return jsonify({"status": "not_found", "id": req_id}), 404


@app.route("/deny/<int:req_id>", methods=["POST"])
def deny_request(req_id):
    for req in escalation_queue[:]:
        if req["id"] == req_id and req["status"] == "PENDING":
            req["status"] = "DENIED"

            publish_event = {
                "action": req["action"],
                "table": req["table"],
                "status": "BLOCKED",
                "message": "Escalation denied by operator",
                "request_id": req_id,
                "timestamp": time.strftime("%H:%M:%S"),
                "policy": drvl.policy_hash
            }
            publish_event["signature"] = drvl.sign_event(publish_event)
            publish(publish_event)

            escalation_queue.remove(req)

            return jsonify({
                "status": "denied",
                "id": req_id,
                "escalation_queue": [
                    {
                        "request_id": r["id"],
                        "action": r["action"],
                        "table": r["table"],
                        "status": r["status"]
                    } for r in escalation_queue
                ]
            })

    return jsonify({"status": "not_found", "id": req_id}), 404


@app.route("/status")
def get_status():
    return jsonify({
        "escalation_queue": [
            {
                "request_id": req["id"],
                "action": req["action"],
                "table": req["table"],
                "status": req["status"]
            } for req in escalation_queue
        ]
    })


@app.route("/logs")
def view_logs():
    try:
        with open("drvl_events.log", "r") as f:
            logs = f.read()
    except Exception:
        logs = "No events yet."
    return f"<pre>{logs}</pre>"


@app.route("/set_llm_key", methods=["POST"])
def set_llm_key():
    if not request.is_json:
        return jsonify({"status": "error", "error": "Request must be JSON"}), 400

    data = request.get_json()
    provider = data.get("provider")
    api_key = data.get("api_key")

    if not provider or not api_key:
        return jsonify({"status": "error", "error": "Missing provider or api_key"}), 400

    try:
        global agent
        agent.set_llm(provider, api_key)
        return jsonify({"status": "ok"})
    except ValueError as e:
        return jsonify({"status": "error", "error": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "error": f"Server error: {str(e)}"}), 500


@app.route("/events")
def stream_events():
    def event_stream():
        last_index = 0
        while True:
            events = get_events()
            if len(events) > last_index:
                event = events[last_index]
                last_index += 1
                yield f"data: {json.dumps(event)}\n\n"
            time.sleep(0.5)  # faster polling for responsive demo feel
    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
