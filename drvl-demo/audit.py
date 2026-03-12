from datetime import datetime
import json

LOG_FILE = "drvl_events.log"

def handle_event(event):
    # This is called when something is already published to the bus
    # (via subscribe(handle_event) in your main app)
    log_line = (
        f"{event.get('timestamp', datetime.utcnow().isoformat())} | "
        f"ACTION={event.get('action', '—')} | "
        f"TABLE={event.get('table', '—')} | "
        f"STATUS={event.get('status', '—')} | "
        f"MESSAGE={event.get('message', '—')}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(log_line)

    # Optional: also keep the full JSON version if you want both formats
    with open(LOG_FILE, "a") as f_json:
        f_json.write(json.dumps(event) + "\n")


def log_event(action, table, status, message):
    """
    Local logging only — writes to file.
    Does NOT publish to bus anymore (publication must happen via publish_signed_event).
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "table": table,
        "status": status,
        "message": message
    }

    # Write JSON line (good for structured parsing later)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

    # Optional: also write human-readable line
    log_line = (
        f"{event['timestamp']} | "
        f"ACTION={event['action']} | "
        f"TABLE={event['table']} | "
        f"STATUS={event['status']} | "
        f"MESSAGE={event['message']}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(log_line)
