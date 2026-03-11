from flask import Flask, jsonify, render_template
from agent import Agent
from database import Database
from drvl import DRVL
from audit import log_event
from event_bus import publish, subscribe
from flask import Flask, jsonify, render_template

from agent import Agent
from database import Database
from drvl import DRVL

from event_bus import publish, subscribe
from audit import handle_event

app = Flask(__name__)

# register event subscriber
subscribe(handle_event)

environment = "production"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/run")
def run_demo():

    agent = Agent()
    db = Database()
    drvl = DRVL()

    action, table = agent.generate_action()

    allowed, message = drvl.verify(action, table, environment)

    if not allowed:

        publish({
            "action": action,
            "table": table,
            "status": "BLOCKED",
            "message": message
        })

        return jsonify({
            "action": action,
            "table": table,
            "status": "blocked",
            "reason": message
        })

    result = db.execute(action, table)

    publish({
        "action": action,
        "table": table,
        "status": "EXECUTED",
        "message": "Policy allowed"
    })

    return jsonify({
        "action": action,
        "table": table,
        "status": "executed",
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
