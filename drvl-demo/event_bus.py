from datetime import datetime

subscribers = []
events = []

def subscribe(handler):
    subscribers.append(handler)

def publish(event):

    event["timestamp"] = datetime.utcnow().isoformat()

    events.append(event)

    for handler in subscribers:
        handler(event)

def get_events():
    return events
