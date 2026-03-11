from datetime import datetime
import json
from event_bus import publish

LOG_FILE = "drvl_events.log"

def handle_event(event):
    log_line = (
        f"{event.get('timestamp', datetime.utcnow().isoformat())} | "
        f"ACTION={event['action']} | "
        f"TABLE={event['table']} | "
        f"STATUS={event['status']} | "
        f"MESSAGE={event['message']}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(log_line)

def log_event(action, table, status, message):
    """
    Logs an event to file and publishes to the event bus.
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "table": table,
        "status": status,
        "message": message
    }

    # publish to event bus
    publish(event)

    # append to log file
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
