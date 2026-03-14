import json
import os
from datetime import datetime

STATUS_FILE = "farm_status.json"


def default_status():
    return {
        "state": "IDLE",
        "step": "-",
        "message": "",
        "updated_at": str(datetime.now())
    }


def update_status(state=None, step=None, message=None):
    status = get_status()

    if state:
        status["state"] = state
    if step:
        status["step"] = step
    if message:
        status["message"] = message

    status["updated_at"] = str(datetime.now())

    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=4)


def get_status():
    if not os.path.exists(STATUS_FILE):
        return default_status()

    with open(STATUS_FILE, "r") as f:
        return json.load(f)