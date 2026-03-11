from datetime import datetime

subscribers = []
events = []

def subscribe(handler):
    subscribers.append(handler)

def publish(event):

    event["timestamp"] = datetime.utcnow().isoformat()

    # Tag high-risk actions
    if event["status"] == "BLOCKED":
        event["severity"] = "HIGH"
    else:
        event["severity"] = "LOW"

    events.append(event)

    for handler in subscribers:
        handler(event)

def get_events():
    return events
