import os
import time
import random
import subprocess
import base64


# =========================
# CONFIG
# =========================

TEXT_FILE = "texts.txt"
LOG_FILE = "posted_log.txt"


# =========================
# BASIC ADB
# =========================

def adb(device, *args):
    return subprocess.run(["adb", "-s", device, *args], check=False)


def wait(a=1, b=2):
    time.sleep(random.uniform(a, b))


# =========================
# CAPTION SYSTEM
# =========================

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
        open(LOG_FILE, "w").close()
        available = captions

    caption = random.choice(available)

    save_posted(caption)

    return caption


# =========================
# SEND TEXT (THAI SAFE)
# =========================

def type_text(device, text):

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

    wait(1,2)


# =========================
# PREPARE TIKTOK
# =========================

def prepare_tiktok(device):

    print("🔄 Preparing TikTok")

    adb(device, "shell", "am", "force-stop", "com.ss.android.ugc.trill")
    wait(2,3)

    adb(
        device,
        "shell",
        "am",
        "start",
        "-n",
        "com.ss.android.ugc.trill/com.ss.android.ugc.aweme.splash.SplashActivity"
    )

    wait(5,7)


# =========================
# POST VIDEO
# =========================

def post_video(device, video_path, caption):

    try:

        print(f"\n📱 Device: {device}")

        if not os.path.exists(video_path):
            print("❌ Video not found:", video_path)
            return False

        adb(device, "shell", "rm", "/sdcard/Download/post.mp4")
        wait(3,4)

        print("📤 Uploading video to phone")

        adb(device, "push", video_path, "/sdcard/Download/post.mp4")

        wait(5,6)

        prepare_tiktok(device)

        print("STEP 1 : Tap +")

        adb(device, "shell", "input", "tap", "540", "2200")
        wait(4,5)

        print("STEP 2 : Upload")

        adb(device, "shell", "input", "tap", "900", "1806")
        wait(4,5)

        adb(device, "shell", "input", "tap", "340", "317")
        wait(4,5)

        adb(device, "shell", "input", "tap", "304", "440")
        wait(4,5)

        adb(device, "shell", "input", "tap", "821", "2197")
        wait(6,7)

        # ----------------------
        # CAPTION
        # ----------------------

        print("📝 Caption:", caption)

        adb(device, "shell", "input", "tap", "540", "600")

        wait(4,5)

        type_text(device, caption)

        adb(device, "shell", "input", "keyevent", "4")

        wait(4,5)

        # ----------------------
        # POST
        # ----------------------

        print("🚀 Posting")

        adb(device, "shell", "input", "tap", "821", "2197")

        wait(7,10)

        print("✅ Posted")

        return True

    except Exception as e:

        print("❌ Post Error:", e)

        return False


# =========================
# COMMENT SYSTEM
# =========================

def post_comment(device, text):

    try:

        print("💬 Posting comment")

        wait(5,6)

        adb(device, "shell", "input", "tap", "540", "2050")
        wait(3,4)

        adb(device, "shell", "input", "tap", "540", "2150")
        wait(3,4)

        type_text(device, text)

        adb(device, "shell", "input", "tap", "1000", "2150")

        wait(3,4)

        print("✅ Comment posted")

    except:

        print("⚠️ Comment failed")


# =========================
# MAIN ENTRY (Dashboard Use)
# =========================

def post(device, video, caption=None, cfg=None, comment_link=None):

    if not caption:
        caption = get_random_caption()

    success = post_video(device, video, caption)

    if success and comment_link:
        post_comment(device, comment_link)

    return success