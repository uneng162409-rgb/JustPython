import json
import os
from datetime import datetime

STATE_FILE = "farm_state.json"


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def update_status(account="tiktok", **kwargs):
    """
    รองรับทุก parameter:
    message=
    step=
    progress=
    product=
    error=
    ฯลฯ
    """

    state = load_state()

    if "accounts" not in state:
        state["accounts"] = {}

    if account not in state["accounts"]:
        state["accounts"][account] = {}

    account_state = state["accounts"][account]

    # บันทึก timestamp ทุกครั้ง
    account_state["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # เก็บทุก field ที่ส่งเข้ามา
    for key, value in kwargs.items():
        account_state[key] = value

    save_state(state)