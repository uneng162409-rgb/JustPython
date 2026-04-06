import os
import time
import random
import subprocess
import base64
from datetime import datetime

# =========================
# CONFIG
# =========================
TEXT_FILE = "texts.txt"
LOG_FILE = "posted_log.txt"

PACKAGE_NAME = "com.ss.android.ugc.trill"
ACTIVITY_NAME = "com.ss.android.ugc.aweme.splash.SplashActivity"

# =========================
# BASIC ADB
# =========================
def adb(device, *args):
    return subprocess.run(["adb", "-s", device, *args], check=False)


def wait(a=1.5, b=2.5):
    time.sleep(random.uniform(a, b))


# =========================
# CAPTION SYSTEM
# =========================
def load_captions():
    if not os.path.exists(TEXT_FILE):
        return ["🔥 โปรแรงวันนี้"]

    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    return lines if lines else ["🔥 โปรแรงวันนี้"]


def load_posted():
    if not os.path.exists(LOG_FILE):
        return set()

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return set(l.strip() for l in f if l.strip())


def save_posted(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")


def get_smart_caption():
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
# SEND TEXT (THAI SAFE BASE64)
# =========================
def type_text(device, text):
    encoded = base64.b64encode(text.encode("utf-8")).decode()

    subprocess.run([
        "adb", "-s", device,
        "shell", "am", "broadcast",
        "-a", "ADB_INPUT_B64",
        "--es", "msg", encoded
    ])

    wait(1.5, 2.5)


# =========================
# PREPARE TIKTOK
# =========================
def prepare_tiktok(device):
    print("🔄 Preparing TikTok")

    adb(device, "shell", "am", "force-stop", PACKAGE_NAME)
    wait(2, 3)

    adb(
        device,
        "shell", "am", "start",
        "-n",
        f"{PACKAGE_NAME}/{ACTIVITY_NAME}"
    )

    wait(10, 14)


# =========================
# PUSH VIDEO (SAFE UNIQUE NAME)
# =========================
def push_video(device, video_path):

    print("📤 Uploading video to phone")

    if not os.path.exists(video_path):
        print("❌ File not found:", video_path)
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"farm_{timestamp}.mp4"
    remote_path = f"/sdcard/Movies/{filename}"

    result = adb(device, "push", video_path, remote_path)

    if result.returncode != 0:
        print("❌ ADB push failed")
        return None

    adb(device,
        "shell", "am", "broadcast",
        "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
        "-d", f"file://{remote_path}"
    )

    print("📡 Media scan triggered")
    time.sleep(3)

    return remote_path


# =========================
# CLEANUP
# =========================
def cleanup_after_post(device, remote_path):

    print("🧹 Cleaning phone storage")

    if remote_path:
        adb(device, "shell", "rm", remote_path)
        wait(1, 2)

    adb(device, "shell", "am", "force-stop", PACKAGE_NAME)
    wait(2, 3)

    adb(device, "shell", "input", "keyevent", "3")
    wait(2, 3)

    print("🗑 Cleanup complete")


# =========================
# POST VIDEO
# =========================
def post_video(device, video_path, caption):
    try:
        print(f"\n📱 Device: {device}")

        remote = push_video(device, video_path)
        if not remote:
            return False

        print("🎬 Remote file:", remote)

        prepare_tiktok(device)

        print("STEP 1 : Tap +")
        adb(device, "shell", "input", "tap", "540", "2200")
        wait(4, 5)

        print("STEP 2 : Upload")
        adb(device, "shell", "input", "tap", "900", "1806")
        wait(4, 5)

        adb(device, "shell", "input", "tap", "540", "317")
        wait(4, 5)

        adb(device, "shell", "input", "tap", "304", "440")
        wait(4, 5)

        adb(device, "shell", "input", "tap", "821", "2197")
        wait(6, 7)

        # Caption
        print("📝 Caption:", caption)

        adb(device, "shell", "input", "tap", "540", "600")
        wait(3, 4)

        type_text(device, caption)

        adb(device, "shell", "input", "keyevent", "4")
        wait(4, 5)

        # Accept popup (if any)
        adb(device, "shell", "input", "tap", "60", "2000")
        wait(2, 3)

        # POST
        print("🚀 Posting")
        adb(device, "shell", "input", "tap", "821", "2197")
        wait(8, 12)

        print("✅ Posted Successfully")

        cleanup_after_post(device, remote)

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

        wait(5, 6)

        adb(device, "shell", "input", "tap", "540", "2050")
        wait(3, 4)

        adb(device, "shell", "input", "tap", "540", "2150")
        wait(3, 4)

        type_text(device, text)

        adb(device, "shell", "input", "tap", "1000", "2150")
        wait(3, 4)

        print("✅ Comment posted")

    except:
        print("⚠️ Comment failed")


# =========================
# MAIN ENTRY (STEP C COMPATIBLE)
# =========================
def post(device, video, caption=None, cfg=None, comment_link=None):

    if not caption:
        caption = get_smart_caption()

    success = post_video(device, video, caption)

    if success and comment_link:
        post_comment(device, comment_link)

    return success


if __name__ == "__main__":
    DEVICE_ID = "192.168.1.103:5555"
    VIDEO_PATH = "video.mp4"

    post(DEVICE_ID, VIDEO_PATH)