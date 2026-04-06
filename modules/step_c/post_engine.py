import os
import yaml
import random
import time
import json
import subprocess
import hashlib
from datetime import datetime, timedelta

from modules.step_c.platforms import tiktok, shopee, reels

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
STATE_FILE = os.path.join(BASE_DIR, "farm_state.json")


# =========================
# STATE SYSTEM
# =========================

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    state["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

def update_state(**kwargs):
    state = load_state()
    state.update(kwargs)
    save_state(state)


# =========================
# CONFIG
# =========================

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# =========================
# VIDEO UTIL
# =========================

def get_all_videos(output_path):
    videos = []
    for root, _, files in os.walk(output_path):
        for f in files:
            if f.endswith(".mp4") and "base.mp4" not in f:
                videos.append(os.path.join(root, f))
    return videos

def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


# =========================
# ADB UTILS
# =========================

def adb_push(device, local_path):
    remote_path = "/sdcard/Download/" + os.path.basename(local_path)

    cmd = ["adb", "-s", device, "push", local_path, remote_path]
    result = subprocess.run(cmd, capture_output=True)

    return result.returncode == 0, remote_path

def adb_delete(device, remote_path):
    cmd = ["adb", "-s", device, "shell", "rm", remote_path]
    subprocess.run(cmd)


# =========================
# TIME WINDOW
# =========================

def get_next_window(step):
    now = datetime.now()
    future_windows = []

    for window in step.get("time_windows", []):
        start_time = datetime.strptime(window["start"], "%H:%M").time()
        start_datetime = datetime.combine(now.date(), start_time)

        if start_datetime > now:
            future_windows.append(start_datetime)

    if not future_windows:
        first = step["time_windows"][0]
        start_time = datetime.strptime(first["start"], "%H:%M").time()
        return datetime.combine(now.date() + timedelta(days=1), start_time)

    return min(future_windows)


# =========================
# MAIN LOOP v2.5
# =========================

def run_step_c():

    CHECK_INTERVAL = 5  # เช็คทุก 5 วินาที
    TOLERANCE_MINUTES = 10  # เลทได้ 10 นาที

    while True:

        cfg = load_config()
        step = cfg["step_c"]
        daily = step["daily_control"]

        if not step.get("enabled", False):
            update_state(state="STOPPED", message="STEP C Disabled")
            time.sleep(5)
            continue

        state = load_state()
        today_str = datetime.now().strftime("%Y-%m-%d")

        # =============================
        # RESET DAILY PLAN
        # =============================
        if state.get("current_date") != today_str:

            min_post = daily.get("min_post_per_day", 3)
            max_post = daily.get("max_post_per_day", 7)
            random_today_plan = random.randint(min_post, max_post)

            state.update({
                "current_date": today_str,
                "today_plan": random_today_plan,
                "today_posts": 0,
                "success": 0,
                "failed": 0
            })
            save_state(state)

        # =============================
        # QUOTA CHECK
        # =============================
        if state.get("today_posts", 0) >= state.get("today_plan", 0):
            update_state(state="DONE", message="Daily quota reached")
            time.sleep(10)
            continue

        # =============================
        # CHECK TIME WINDOW
        # =============================
        now = datetime.now()
        should_post = False
        next_window_time = None

        for window in step.get("time_windows", []):
            start_time = datetime.strptime(window["start"], "%H:%M").time()
            start_dt = datetime.combine(now.date(), start_time)
            tolerance = timedelta(minutes=TOLERANCE_MINUTES)

            if start_dt <= now <= start_dt + tolerance:
                should_post = True
                break

            if now < start_dt:
                next_window_time = start_dt
                break

        if not should_post:
            if not next_window_time:
                # หมด window วันนี้ → ไปพรุ่งนี้
                first = step["time_windows"][0]
                start_time = datetime.strptime(first["start"], "%H:%M").time()
                next_window_time = datetime.combine(
                    now.date() + timedelta(days=1),
                    start_time
                )

            update_state(
                state="WAITING",
                message=f"Waiting until {next_window_time.strftime('%H:%M:%S')}",
                next_post_time=next_window_time.strftime("%H:%M:%S"),
                next_post_timestamp=next_window_time.timestamp()
            )

            time.sleep(CHECK_INTERVAL)
            continue

        # =============================
        # POSTING BLOCK (FIXED)
        # =============================
        update_state(state="POSTING", message="Posting now...")

        output_path = cfg["paths"]["output"]
        videos = get_all_videos(output_path)

        if not videos:
            update_state(message="No videos found")
            time.sleep(10)
            continue

        for device in step["devices"]:
            for platform_name, platform_cfg in step["platforms"].items():

                if not platform_cfg.get("enabled", False):
                    continue

                video = random.choice(videos)
                caption = "🔥 โปรแรงวันนี้!"

                print(f"DEBUG: Posting {platform_name} → {video}")

                success = False

                try:
                    if platform_name == "tiktok":
                        success = tiktok.post(device, video, caption, cfg, "")
                    elif platform_name == "shopee":
                        success = shopee.post(device, video, caption, cfg, "")
                    elif platform_name == "reels":
                        success = reels.post(device, video, caption, cfg, "")
                except Exception as e:
                    print("POST ERROR:", e)
                    success = False

                state = load_state()

                if success:
                    state["success"] = state.get("success", 0) + 1
                    state["today_posts"] = state.get("today_posts", 0) + 1
                else:
                    state["failed"] = state.get("failed", 0) + 1

                save_state(state)

        # =============================
        # CALCULATE NEXT ROUND
        # =============================
        min_wait = daily.get("min_wait", 3600)
        max_wait = daily.get("max_wait", 7200)

        delay = random.randint(min_wait, max_wait)
        next_time = datetime.now() + timedelta(seconds=delay)

        update_state(
            state="WAITING",
            message="Waiting next round",
            next_post_time=next_time.strftime("%H:%M:%S"),
            next_post_timestamp=next_time.timestamp()
        )

        # แทน sleep ยาว → loop check
        end_wait = datetime.now() + timedelta(seconds=delay)

        while datetime.now() < end_wait:

            # ถ้ากด STOP → ออกทันที
            cfg = load_config()
            if not cfg["step_c"].get("enabled", False):
                update_state(state="STOPPED", message="Stopped manually")
                break

            time.sleep(CHECK_INTERVAL)