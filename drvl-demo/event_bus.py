from datetime import datetime, timezone
from threading import Lock
from typing import Callable, Any, Dict

subscribers: list[Callable[[Dict[str, Any]], None]] = []
events: list[Dict[str, Any]] = []
lock = Lock()  # Protects subscribers and events lists


def utcnow_iso() -> str:
    """Return current UTC time in ISO 8601 format with 'Z' suffix (correctly timezone-aware)."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def subscribe(handler: Callable[[Dict[str, Any]], None]) -> None:
    """Register a handler to receive published events."""
    with lock:
        subscribers.append(handler)


def publish(event: Dict[str, Any]) -> None:
    """
    Publish an event to all subscribers.
    Enforces: timestamp, basic signature presence, severity hint.
    """
    if "policy" not in event or "signature" not in event:
        raise ValueError("Unsigned event rejected by event bus")

    # Add timestamp if missing (most events already have one, but defensive)
    event.setdefault("timestamp", utcnow_iso())

    # Simple severity tagging for UI/demo purposes
    status = event.get("status", "").upper()
    event["severity"] = "HIGH" if status in ("BLOCKED", "DENIED") else "LOW"

    event_copy = event.copy()

    with lock:
        events.append(event_copy)

        # Notify subscribers safely
        for handler in subscribers[:]:  # copy to avoid modification-during-iteration issues
            try:
                handler(event_copy)
            except Exception as e:
                print(f"Subscriber error in {handler.__name__ if hasattr(handler, '__name__') else 'anonymous'}: {e}")


def get_events() -> list[Dict[str, Any]]:
    """Return a copy of all published events (thread-safe)."""
    with lock:
        return events[:]


def clear_events() -> None:
    """Clear the event history (useful for testing/restarting demo)."""
    with lock:
        events.clear()
