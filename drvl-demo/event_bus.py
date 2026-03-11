from datetime import datetime

subscribers = []
events = []  # In-memory event log (demo only — use DB in real system)


def subscribe(handler):
    """Register a handler to receive published events."""
    subscribers.append(handler)


def publish(event):
    """
    Publish an event to all subscribers.
    Automatically adds timestamp, severity, policy, and signature.
    """
    # Ensure required fields (defensive)
    event.setdefault("timestamp", datetime.utcnow().isoformat())
    
    # Tag severity (demo-specific)
    event["severity"] = "HIGH" if event.get("status") == "BLOCKED" else "LOW"

    # Add policy hash and signature if not already present
    # (These should come from drvl.py, but fallback here if missing)
    if "policy" not in event:
        event["policy"] = "— (missing)"
    if "signature" not in event:
        event["signature"] = "— (missing)"

    # Append to log
    events.append(event.copy())  # copy to avoid mutation issues

    # Notify subscribers (with basic error tolerance)
    for handler in subscribers:
        try:
            handler(event)
        except Exception as e:
            print(f"Subscriber error: {e}")


def get_events():
    """Return all stored events (for SSE streaming)."""
    return events[:]  # shallow copy to avoid external mutation


def clear_events():
    """Clear event log (useful for demo reset, optional)."""
    events.clear()
