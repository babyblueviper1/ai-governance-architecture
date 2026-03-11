from datetime import datetime

subscribers = []

def subscribe(handler):
    subscribers.append(handler)

def publish(event):

    event["timestamp"] = datetime.utcnow().isoformat()

    for handler in subscribers:
        handler(event)
