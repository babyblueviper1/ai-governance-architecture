from datetime import datetime

LOG_FILE = "drvl_events.log"

def handle_event(event):

    log_line = (
        f"{event['timestamp']} | "
        f"ACTION={event['action']} | "
        f"TABLE={event['table']} | "
        f"STATUS={event['status']} | "
        f"MESSAGE={event['message']}\n"
    )

    with open(LOG_FILE, "a") as f:
        f.write(log_line)
