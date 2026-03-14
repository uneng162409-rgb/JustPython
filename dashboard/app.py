import os
import json
import subprocess
import threading
from flask import Flask, render_template, request, redirect, url_for

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATE_FILE = os.path.join(BASE_DIR, "farm_state.json")

app = Flask(__name__)
farm_process = None


# =========================
# STATE FUNCTIONS
# =========================
def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


# =========================
# FARM RUNNER
# =========================
def run_farm_background():
    global farm_process

    python_path = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")
    run_farm_path = os.path.join(BASE_DIR, "run_farm.py")

    farm_process = subprocess.Popen(
        [python_path, run_farm_path],
        cwd=BASE_DIR
    )
# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    state = load_state()
    return render_template("index.html", state=state)


@app.route("/start")
def start():
    state = load_state()

    if state["state"] == "RUNNING":
        return redirect(url_for("index"))

    state["state"] = "RUNNING"
    state["step"] = "STARTING"
    state["message"] = "Starting Farm..."
    save_state(state)

    thread = threading.Thread(target=run_farm_background)
    thread.start()

    return redirect(url_for("index"))


@app.route("/stop")
def stop():
    state = load_state()
    state["state"] = "STOPPING"
    state["message"] = "Stopping by user..."
    save_state(state)
    return redirect(url_for("index"))


@app.route("/update", methods=["POST"])
def update_config():
    state = load_state()

    state["step_a"] = "step_a" in request.form
    state["step_b"] = "step_b" in request.form
    state["step_c"] = "step_c" in request.form

    state["products"] = int(request.form["products"])
    state["videos"] = int(request.form["videos"])
    state["posts"] = int(request.form["posts"])

    save_state(state)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)