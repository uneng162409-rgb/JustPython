import time
from datetime import datetime
from production_state_manager import load_state, save_state, is_new_day, reset_day
from production_schedule_engine import generate_schedule
from production_video_pool import (
    ensure_folders,
    get_ready_videos,
    move_to_posted,
    reset_posted_to_ready,
    buffer_needed
)

SLEEP_INTERVAL = 5


def step_a():
    print("🔄 STEP A: Fetch products")


def step_b():
    print("🎬 STEP B: Generate videos")


def step_c(video_file):
    print(f"🚀 STEP C: Posting {video_file}")
    time.sleep(2)


def wait_until(target_time_str):
    target = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
    while True:
        now = datetime.now()
        state = load_state()
        if state["farm_status"] == "STOPPED":
            print("🛑 Farm stopped")
            return False
        if now >= target:
            return True
        time.sleep(SLEEP_INTERVAL)


def main():
    ensure_folders()
    print("🟢 SMART FARM SYSTEM START")

    while True:
        state = load_state()

        if state["farm_status"] != "RUNNING":
            time.sleep(SLEEP_INTERVAL)
            continue

        if is_new_day(state):
            print("🌙 New Day Reset")
            reset_posted_to_ready()
            state = reset_day(state)
            target, schedule = generate_schedule()
            state["today_target"] = target
            state["today_schedule"] = schedule
            state["next_post_time"] = schedule[0]
            save_state(state)
            print(f"📅 Today Plan: {target} posts")

        if state["today_done"] >= state["today_target"]:
            time.sleep(SLEEP_INTERVAL)
            continue

        if not state["next_post_time"]:
            state["next_post_time"] = state["today_schedule"][state["today_done"]]
            save_state(state)

        print(f"⏳ Waiting until {state['next_post_time']}")

        if not wait_until(state["next_post_time"]):
            continue

        if buffer_needed(state):
            step_a()
            step_b()

        videos = get_ready_videos()
        if not videos:
            print("⚠ No videos available")
            time.sleep(SLEEP_INTERVAL)
            continue

        video = videos[0]
        step_c(video)
        move_to_posted(video)

        state["today_done"] += 1
        state["today_posted_videos"].append(video)

        if state["today_done"] < state["today_target"]:
            state["next_post_time"] = state["today_schedule"][state["today_done"]]
        else:
            state["next_post_time"] = ""

        save_state(state)
        print(f"📊 Progress: {state['today_done']}/{state['today_target']}")

        time.sleep(SLEEP_INTERVAL)


if __name__ == "__main__":
    main()