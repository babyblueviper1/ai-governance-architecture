from flask import Flask, jsonify
from agent import Agent
from database import Database
from drvl import DRVL

app = Flask(__name__)

environment = "production"

@app.route("/")
def home():
    return "DRVL Demo Running"

@app.route("/run")
def run_demo():

    agent = Agent()
    db = Database()
    drvl = DRVL()

    action, table = agent.generate_action()

    allowed, message = drvl.verify(action, table, environment)

    if not allowed:

        return jsonify({
            "action": action,
            "table": table,
            "status": "blocked",
            "reason": message
        })

    result = db.execute(action, table)

    return jsonify({
        "action": action,
        "table": table,
        "status": "executed",
        "result": result
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
