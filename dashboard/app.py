import os
import json
import subprocess
import threading
import sys
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, jsonify, request

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATE_FILE = os.path.join(BASE_DIR, "farm_state.json")
RUN_FARM_PATH = os.path.join(BASE_DIR, "run_farm.py")

app = Flask(__name__)

farm_process = None
lock = threading.Lock()

# =========================
# DEFAULT STATE
# =========================

def default_state():
    return {
        "state": "STOPPED",
        "step": "-",
        "message": "ยังไม่เริ่ม",

        "step_a": True,
        "step_b": True,
        "step_c": True,

        "today_products": 0,
        "today_videos": 0,
        "today_posts": 0,
        "success": 0,
        "failed": 0,

        # 👇 Dashboard Sync fields
        "today_plan": 0,
        "next_post_time": "-",
        "next_post_timestamp": 0,

        "last_update": "-"
    }

def load_state():
    if not os.path.exists(STATE_FILE):
        return default_state()

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default_state()

def save_state(state):
    state["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

# =========================
# RUN FARM BACKGROUND
# =========================

def run_farm_background():
    global farm_process

    with lock:
        state = load_state()
        state["state"] = "RUNNING"
        state["message"] = "🚜 Smart Farm กำลังทำงาน..."
        save_state(state)

        farm_process = subprocess.Popen(
            [sys.executable, RUN_FARM_PATH],
            cwd=BASE_DIR
        )

    farm_process.wait()

    with lock:
        state = load_state()
        state["state"] = "STOPPED"
        state["message"] = "⏹ Smart Farm หยุดแล้ว"
        save_state(state)

        farm_process = None

# =========================
# ROUTES
# =========================

@app.route("/")
def index():
    return render_template("index.html", state=load_state())

# 🔥 FIX สำคัญ — คืนค่า state จริง 100%
@app.route("/api/state")
def api_state():
    return jsonify(load_state())

@app.route("/update", methods=["POST"])
def update():
    state = load_state()

    state["step_a"] = "step_a" in request.form
    state["step_b"] = "step_b" in request.form
    state["step_c"] = "step_c" in request.form

    save_state(state)

    return redirect(url_for("index"))

@app.route("/start")
def start():
    global farm_process

    if farm_process and farm_process.poll() is None:
        return redirect(url_for("index"))

    thread = threading.Thread(target=run_farm_background, daemon=True)
    thread.start()

    return redirect(url_for("index"))

@app.route("/stop")
def stop():
    global farm_process

    if farm_process and farm_process.poll() is None:
        farm_process.terminate()
        farm_process.wait()
        farm_process = None

    state = load_state()
    state["state"] = "STOPPED"
    state["message"] = "หยุดโดยผู้ใช้"
    save_state(state)

    return redirect(url_for("index"))

# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)