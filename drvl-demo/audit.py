from datetime import datetime

LOG_FILE = "drvl_events.log"

def log_event(action, table, status, message):

    timestamp = datetime.utcnow().isoformat()

    log_line = f"{timestamp} | ACTION={action} | TABLE={table} | STATUS={status} | MESSAGE={message}\n"

    with open(LOG_FILE, "a") as f:
        f.write(log_line)
