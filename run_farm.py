import json
import traceback
import subprocess
from modules._bootstrap import load_config
from modules.step_a_fetch_and_filter import run as step_a
from modules.step_b_video_factory import run as step_b
from modules.step_c.post_engine import run_step_c

CFG = load_config()

STATE_FILE = "farm_state.json"


# =========================
# STATE FUNCTIONS
# =========================
def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


def update_status(state_value=None, step=None, message=None):
    state = load_state()

    if state_value:
        state["state"] = state_value

    if step:
        state["step"] = step

    if message:
        state["message"] = message

    save_state(state)


def should_stop():
    state = load_state()
    return state["state"] == "STOPPING"


# =========================
# MAIN FARM
# =========================
def main():

    try:

        print("🟢 RUN FARM START")
        update_status("RUNNING", "STARTING", "Farm Started")

        state = load_state()

        # =========================
        # STEP A
        # =========================
        if should_stop():
            return stop_farm()

        update_status(step="STEP A", message="Finding Products")

        if state.get("step_a", True):
            print("🚀 STEP A START")
            step_a()
            print("✅ STEP A DONE")

        # =========================
        # STEP B
        # =========================
        if should_stop():
            return stop_farm()

        update_status(step="STEP B", message="Generating Videos")

        if state.get("step_b", True):
            print("🎬 STEP B START")
            step_b()
            print("✅ STEP B DONE")

        # =========================
        # STEP C
        # =========================
        if should_stop():
            return stop_farm()

        update_status(step="STEP C", message="Posting to TikTok")

        if state.get("step_c", True):
            print("📤 STEP C START")
            run_step_c()
            print("✅ STEP C DONE")

        auto_git_push_farm_end()

        update_status("IDLE", "FINISHED", "Farm Completed")
        print("🟢 RUN FARM END")

    except Exception as e:

        print("❌ FARM ERROR:", e)
        traceback.print_exc()

        update_status("ERROR", "ERROR", str(e))


# =========================
# STOP FARM
# =========================
def stop_farm():
    print("🛑 FARM STOPPED BY DASHBOARD")
    update_status("IDLE", "STOPPED", "Stopped by user")


# =========================
# AUTO GIT PUSH
# =========================
def auto_git_push_farm_end():

    git_cfg = CFG.get("git", {})

    if not git_cfg.get("enabled", False):
        return

    if git_cfg.get("mode") != "farm_end":
        return

    message = git_cfg.get("commit_message", "AUTO FARM END UPDATE")

    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🚀 AUTO GIT PUSH SUCCESS")

    except subprocess.CalledProcessError:
        print("⚠️ AUTO GIT SKIPPED")


# =========================
if __name__ == "__main__":
    main()