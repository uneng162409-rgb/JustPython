import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATE_FILE = os.path.join(BASE_DIR, "farm_state.json")


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    state["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)


def update_state(step=None, message=None):
    state = load_state()

    if step is not None:
        state["step"] = step

    if message is not None:
        state["message"] = message

    save_state(state)


def mark_crash(error_message):
    state = load_state()
    state["state"] = "CRASHED"
    state["message"] = error_message
    save_state(state)