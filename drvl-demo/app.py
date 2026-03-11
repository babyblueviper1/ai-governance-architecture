from flask import Flask, jsonify, render_template, Response, request
import json
import time
import random  # ← Added this!

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
    action, table = agent.generate_action()
    allowed, needs_escalation, message = drvl.verify(action, table, environment)

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
            publish({
                "action": action,
                "table": table,
                "status": "EXECUTED",
                "message": "Auto-approved (demo)",
                "request_id": req_id,
                "timestamp": time.strftime("%H:%M:%S")
            })
        elif rand < 0.70:
            status = "DENIED"
            publish({
                "action": action,
                "table": table,
                "status": "BLOCKED",
                "message": "Auto-denied (demo)",
                "request_id": req_id,
                "timestamp": time.strftime("%H:%M:%S")
            })
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

@app.route("/deny/<int:req_id>", methods=["POST"])
def deny_request(req_id):
    for req in escalation_queue[:]:
        if req["id"] == req_id and req["status"] == "PENDING":
            req["status"] = "DENIED"

            publish({
                "action": req["action"],
                "table": req["table"],
                "status": "BLOCKED",
                "message": "Escalation denied by operator",
                "request_id": req_id,
                "timestamp": time.strftime("%H:%M:%S")
            })

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
                "action": req
