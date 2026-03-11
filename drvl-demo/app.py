from flask import Flask, jsonify, render_template, Response
import json, time

from agent import ProbabilisticAgent
from database import Database
from drvl import DRVL
from event_bus import publish, subscribe, get_events
from audit import handle_event, log_event

app = Flask(__name__)
subscribe(handle_event)

environment = "production"
agent = ProbabilisticAgent()
db = Database()
drvl = DRVL()

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/run")
def run_demo():
    action, table = agent.generate_action()
    allowed, message = drvl.verify(action, table, environment)
    status = "EXECUTED" if allowed else "BLOCKED"

    # Log & publish event
    log_event(action, table, status, message)
    publish({
        "action": action,
        "table": table,
        "status": status,
        "message": message,
        "timestamp": db.get_timestamp()
    })

    # Only execute if allowed
    result = db.execute(action, table) if allowed else None

    return jsonify({
        "action": action,
        "table": table,
        "status": status,
        "message": message,
        "result": result
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
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
