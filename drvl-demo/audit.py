# audit.py
from datetime import datetime
import json

LOG_FILE = "drvl_events.log"

def handle_event(event: dict):
    """
    Subscriber for published events.
    Logs both human-readable and JSON versions.
    """
    ts = event.get("timestamp", datetime.utcnow().isoformat())

    # Human-readable log
    log_line = (
        f"{ts} | "
        f"ACTION={event.get('action', '—')} | "
        f"TABLE={event.get('table', '—')} | "
        f"STATUS={event.get('status', '—')} | "
        f"MESSAGE={event.get('message', '—')} | "
        f"POLICY={event.get('policy', '—')} | "
        f"SIGNATURE={event.get('signature', '—')}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(log_line)

    # Full JSON log (good for parsing or auditing)
    with open(LOG_FILE, "a") as f_json:
        f_json.write(json.dumps(event) + "\n")


def log_event(action: str, table: str, status: str, message: str, timestamp: str = None, policy: str = None):
    """
    Local logging for internal use. Does NOT publish to bus.
    `timestamp` and `policy` are passed to match signed event exactly.
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    event = {
        "timestamp": timestamp,
        "action": action,
        "table": table,
        "status": status,
        "message": message,
        "policy": policy,
    }

    # Write structured JSON
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

    # Human-readable line
    log_line = (
        f"{timestamp} | "
        f"ACTION={action} | "
        f"TABLE={table} | "
        f"STATUS={status} | "
        f"MESSAGE={message} | "
        f"POLICY={policy}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(log_line)
