import json
import os
from datetime import datetime

STATE_FILE = "state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return create_default_state()
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)


def create_default_state():
    state = {
        "farm_status": "STOPPED",
        "today_date": "",
        "today_target": 0,
        "today_done": 0,
        "today_schedule": [],
        "today_posted_videos": [],
        "next_post_time": ""
    }
    save_state(state)
    return state


def is_new_day(state):
    today = datetime.now().strftime("%Y-%m-%d")
    return state["today_date"] != today


def reset_day(state):
    today = datetime.now().strftime("%Y-%m-%d")
    state["today_date"] = today
    state["today_done"] = 0
    state["today_posted_videos"] = []
    state["today_schedule"] = []
    state["next_post_time"] = ""
    return state