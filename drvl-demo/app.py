from flask import Flask, jsonify, render_template, Response, request
import json
import time

from agent import ProbabilisticAgent
from drvl import DRVL
from audit import handle_event, log_event
from event_bus import publish, subscribe, get_events
from database import Database

app = Flask(__name__)
subscribe(handle_event)

environment = "demo"  # changed for clarity
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
    action, table = agent.generate_action()
    allowed, needs_escalation, message = drvl.verify(action, table, environment)

    status = ""
    result = None
    req_id = None

    if needs_escalation:
        escalation_counter += 1
        req_id = escalation_counter
        # Auto-approve every 3rd escalation request for demo
        status = "APPROVED" if escalation_counter % 3 == 0 else "PENDING"

        escalation_queue.append({
            "id": req_id,
            "action": action,
            "table": table,
            "status": status
        })

        if status == "APPROVED":
            result = db.execute(action, table)
            publish({
                "action": action,
                "table": table,
                "status": "EXECUTED",
                "message": "Auto-approved escalation",
                "request_id": req_id
            })
    else:
        status = "EXECUTED" if allowed else "BLOCKED"
        if allowed:
            result = db.execute(action, table)

    # Log and publish event
    log_event(action, table, status, message)
    publish({
        "action": action,
        "table": table,
        "status": status,
        "message": message,
        "request_id": req_id,
        "timestamp": time.strftime("%H:%M:%S")
    })

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
        ]
    })

@app.route("/approve/<int:req_id>", methods=["POST"])
def approve_request(req_id):
    for req in escalation_queue[:]:
        if req["id"] == req_id and req["status"] == "PENDING":
            req["status"] = "APPROVED"
            result = db.execute(req["action"], req["table"])

            publish({
                "action": req["action"],
                "table": req["table"],
                "status": "EXECUTED",
                "message": "Escalation manually approved",
                "request_id": req_id,
                "timestamp": time.strftime("%H:%M:%S")
            })

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
    except:
        logs = "No events yet."
    return f"<pre>{logs}</pre>"

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
            time.sleep(0.5)  # faster polling for demo feel
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
