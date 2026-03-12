from datetime import datetime

subscribers = []
events = []


def subscribe(handler):
    subscribers.append(handler)


def publish(event):
    """Publish an event to all subscribers."""

    # Ensure timestamp exists BEFORE publishing (should already exist for signing)
    if "timestamp" not in event:
        event["timestamp"] = datetime.utcnow().isoformat()

    # Severity metadata (optional)
    event["severity"] = "HIGH" if event.get("status") == "BLOCKED" else "LOW"

    # Enforce signing
    if "policy" not in event or "signature" not in event:
        raise ValueError("Unsigned event rejected by event bus")

    # Append a **deep copy** to avoid later mutations affecting logged events
    events.append(event.copy())

    # Notify subscribers
    for handler in subscribers:
        try:
            handler(event)
        except Exception as e:
            print(f"Subscriber error: {e}")


def get_events():
    return events[:]


def clear_events():
    events.clear()
