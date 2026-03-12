from datetime import datetime

subscribers = []
events = []


def subscribe(handler):
    subscribers.append(handler)


def publish(event):
    """Publish an event to all subscribers."""

    event.setdefault("timestamp", datetime.utcnow().isoformat())

    event["severity"] = "HIGH" if event.get("status") == "BLOCKED" else "LOW"

    # Enforce signing (do NOT allow unsigned events)
    if "policy" not in event or "signature" not in event:
        raise ValueError("Unsigned event rejected by event bus")

    events.append(event.copy())

    for handler in subscribers:
        try:
            handler(event)
        except Exception as e:
            print(f"Subscriber error: {e}")


def get_events():
    return events[:]


def clear_events():
    events.clear()
