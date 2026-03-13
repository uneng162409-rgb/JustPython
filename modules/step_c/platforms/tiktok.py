import os
import random
import time
import subprocess
import base64

# ==============================
# CONFIG
# ==============================
TEXT_FILE = "texts.txt"
LOG_FILE = "posted_log.txt"


# ==============================
# BASIC ADB
# ==============================
def adb(device, *args):
    return subprocess.run(["adb", "-s", device, *args], check=False)


def human_delay(a=0.8, b=1.8):
    time.sleep(random.uniform(a, b))


# ==============================
# CAPTION SYSTEM
# ==============================
def load_captions():
    if not os.path.exists(TEXT_FILE):
        return ["🔥"]

    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    return lines if lines else ["🔥"]


def load_posted():
    if not os.path.exists(LOG_FILE):
        return set()

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return set(l.strip() for l in f if l.strip())


def save_posted(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")


def get_random_caption():
    captions = load_captions()
    posted = load_posted()

    available = [c for c in captions if c not in posted]

    if not available:
        open(LOG_FILE, "w", encoding="utf-8").close()
        available = captions

    caption = random.choice(available)
    save_posted(caption)
    return caption


# ==============================
# THAI INPUT (ADB KEYBOARD)
# ==============================
def type_text_thai(device, text):
    # เข้ารหัส base64 ป้องกัน shell แตกคำสั่ง
    encoded = base64.b64encode(text.encode("utf-8")).decode()

    subprocess.run([
        "adb",
        "-s",
        device,
        "shell",
        "am",
        "broadcast",
        "-a",
        "ADB_INPUT_B64",
        "--es",
        "msg",
        encoded
    ])

    time.sleep(1)


# ==============================
# MAIN POST FUNCTION
# ==============================
def post(device, video_path, caption=None, cfg=None, comment_link=None):

    try:
        print("🎵 TikTok Posting:", video_path)

        # ------------------------
        # PUSH VIDEO
        # ------------------------
        adb(device, "push", video_path, "/sdcard/Download/post.mp4")
        time.sleep(4)

        # ------------------------
        # OPEN TIKTOK
        # ------------------------
        adb(
            device,
            "shell",
            "am",
            "start",
            "-n",
            "com.ss.android.ugc.trill/com.ss.android.ugc.aweme.splash.SplashActivity"
        )
        time.sleep(6)

        # ------------------------
        # TAP +
        # ------------------------
        print("STEP 1: Tap +")
        adb(device, "shell", "input", "tap", "540", "2200")
        time.sleep(3)

        # ------------------------
        # TAP Upload
        # ------------------------
        print("STEP 2: Tap Upload")
        adb(device, "shell", "input", "tap", "900", "1806")
        time.sleep(3)

        # ------------------------
        # Video Tab
        # ------------------------
        adb(device, "shell", "input", "tap", "340", "317")
        time.sleep(2)

        # First Video
        adb(device, "shell", "input", "tap", "304", "440")
        time.sleep(3)

        # NEXT 1
        adb(device, "shell", "input", "tap", "821", "2197")
        time.sleep(5)



        # ------------------------
        # INPUT CAPTION
        # ------------------------
        if not caption:
            caption = get_random_caption()

        print("📝 Caption:", caption)

        adb(device, "shell", "input", "tap", "540", "600")
        time.sleep(2)

        type_text_thai(device, caption)
        human_delay(2, 3)

        # กด ENTER เพื่อปิด hashtag suggestion
        adb(device, "shell", "input", "keyevent", "66")
        time.sleep(2)

        # ปิด keyboard
        adb(device, "shell", "input", "keyevent", "4")
        time.sleep(2)

        # ------------------------
        # TAP POST
        # ------------------------
        print("STEP 3: Tap Post")

        time.sleep(3)

        adb(device, "shell", "input", "tap", "821", "2197")
        time.sleep(8)

        print("✅ Video Posted")
        return True

    except Exception as e:
        print("❌ TikTok Post Error:", e)
        return False