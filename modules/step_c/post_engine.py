import os
import yaml
import random
import time
import json
import subprocess
from datetime import datetime, timedelta

from modules.step_c.platforms import tiktok, shopee, reels

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
STATE_FILE = os.path.join(BASE_DIR, "farm_state.json")
HISTORY_FILE = os.path.join(BASE_DIR, "post_history.json")


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
# SMART ROTATION
# =========================

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

def select_video_smart(videos):
    history = load_history()
    available = [v for v in videos if v not in history]

    if not available:
        print("♻ ใช้ครบแล้ว → Reset history")
        history = []
        available = videos

    if not available:
        return None, history

    return random.choice(available), history


# =========================
# AI CAPTION SYSTEM
# =========================

def generate_caption(video_path):

    filename = os.path.basename(video_path)
    product_name = os.path.basename(os.path.dirname(video_path))

    # สุ่มราคา
    fake_price = random.randint(199, 999)

    urgency_lines = [
        "รีบก่อนหมดล็อตนี้นะครับ",
        "ของมีจำนวนจำกัด!",
        "ราคานี้ไม่นานแน่นอน!",
        "หมดแล้วหมดเลย!",
        "โปรนี้เฉพาะช่วงนี้เท่านั้น!"
    ]

    hashtags_pool = [
        "#โปรวันนี้", "#ของดีบอกต่อ", "#ดีลเด็ด",
        "#สายช้อป", "#ลดแรง", "#ของมันต้องมี",
        "#รีวิวของดี", "#ถูกและดี"
    ]

    selected_hashtags = random.sample(hashtags_pool, random.randint(3, 5))

    caption = (
        f"🔥 {product_name} ลดเหลือ {fake_price} บาท!\n\n"
        f"{random.choice(urgency_lines)}\n"
        "กดลิงก์หน้าโปรไฟล์เลย 👆\n\n"
        + " ".join(selected_hashtags)
    )

    return caption


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
            if f == "tiktok.mp4":
                videos.append(os.path.join(root, f))
    return videos


# =========================
# ADB
# =========================

def adb_delete(device, remote_path):
    subprocess.run(["adb", "-s", device, "shell", "rm", remote_path])


# =========================
# MAIN LOOP
# =========================

def run_step_c():

    CHECK_INTERVAL = 5
    TOLERANCE_MINUTES = 10

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

        if state.get("current_date") != today_str:

            random_today_plan = random.randint(
                daily.get("min_post_per_day", 3),
                daily.get("max_post_per_day", 7)
            )

            state.update({
                "current_date": today_str,
                "today_plan": random_today_plan,
                "today_posts": 0,
                "success": 0,
                "failed": 0
            })
            save_state(state)

        if state.get("today_posts", 0) >= state.get("today_plan", 0):
            update_state(state="DONE", message="Daily quota reached")
            time.sleep(10)
            continue

        now = datetime.now()
        should_post = False

        for window in step.get("time_windows", []):
            start_time = datetime.strptime(window["start"], "%H:%M").time()
            start_dt = datetime.combine(now.date(), start_time)
            tolerance = timedelta(minutes=TOLERANCE_MINUTES)

            if start_dt <= now <= start_dt + tolerance:
                should_post = True
                break

        if not should_post:
            time.sleep(CHECK_INTERVAL)
            continue

        update_state(state="POSTING", message="Posting now...")

        output_path = cfg["paths"]["output"]
        videos = get_all_videos(output_path)

        if not videos:
            update_state(message="No videos found")
            time.sleep(10)
            continue

        video, history = select_video_smart(videos)

        if not video:
            update_state(message="No available videos")
            time.sleep(10)
            continue

        caption = generate_caption(video)

        for device in step["devices"]:
            for platform_name, platform_cfg in step["platforms"].items():

                if not platform_cfg.get("enabled", False):
                    continue

                success = False

                try:
                    if platform_name == "tiktok":
                        success = tiktok.post(device, video, caption, cfg, "")
                    elif platform_name == "shopee":
                        success = shopee.post(device, video, caption, cfg, "")
                    elif platform_name == "reels":
                        success = reels.post(device, video, caption, cfg, "")
                except:
                    success = False

                state = load_state()

                if success:
                    state["success"] += 1
                    state["today_posts"] += 1

                    if video not in history:
                        history.append(video)
                        save_history(history)

                    remote_path = "/sdcard/DCIM/Camera/" + os.path.basename(video)
                    adb_delete(device, remote_path)

                else:
                    state["failed"] += 1

                save_state(state)

        delay = random.randint(
            daily.get("min_wait", 3600),
            daily.get("max_wait", 7200)
        )

        update_state(state="WAITING", message="Waiting next round")
        time.sleep(delay)