import os
import time
import random
import subprocess
import base64

# =========================
# CONFIG
# =========================
TEXT_FILE = "texts.txt"
POSTED_VIDEO_LOG = "posted_videos.txt"
MAX_RETRY = 3

DEVICES = [
    "192.168.1.103:5555",
    # เพิ่มเครื่องตรงนี้ได้เลย
]


# =========================
# BASIC
# =========================
def adb(device, *args):
    return subprocess.run(["adb", "-s", device, *args], check=False)


def wait(a=1, b=2):
    time.sleep(random.uniform(a, b))


# =========================
# POSTED VIDEO CHECK
# =========================
def load_posted_videos():
    if not os.path.exists(POSTED_VIDEO_LOG):
        return set()
    with open(POSTED_VIDEO_LOG, "r", encoding="utf-8") as f:
        return set(l.strip() for l in f if l.strip())


def save_posted_video(name):
    with open(POSTED_VIDEO_LOG, "a", encoding="utf-8") as f:
        f.write(name + "\n")


def already_posted(video_path):
    posted = load_posted_videos()
    return os.path.basename(video_path) in posted


# =========================
# CAPTION
# =========================
def get_random_caption():
    if not os.path.exists(TEXT_FILE):
        return "🔥"

    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        return "🔥"

    return random.choice(lines)


# =========================
# TYPE TEXT SAFE (THAI)
# =========================
def type_text(device, text):
    encoded = base64.b64encode(text.encode("utf-8")).decode()

    subprocess.run([
        "adb", "-s", device,
        "shell", "am", "broadcast",
        "-a", "ADB_INPUT_B64",
        "--es", "msg", encoded
    ])

    wait(1, 2)


# =========================
# PREPARE TIKTOK
# =========================
def prepare_tiktok(device):
    adb(device, "shell", "am", "force-stop", "com.ss.android.ugc.trill")
    wait(2, 3)

    adb(
        device,
        "shell", "am", "start",
        "-n",
        "com.ss.android.ugc.trill/com.ss.android.ugc.aweme.splash.SplashActivity"
    )
    wait(5, 7)


# =========================
# CHECK SUCCESS (basic verify)
# =========================
def verify_post_success(device):
    # เช็คว่ากลับมาหน้า feed หรือยัง
    result = subprocess.run(
        ["adb", "-s", device, "shell", "dumpsys", "window"],
        capture_output=True,
        text=True
    )

    return "SplashActivity" in result.stdout


# =========================
# POST CORE
# =========================
def post_video(device, video_path):

    if already_posted(video_path):
        print("⚠️ Already posted:", video_path)
        return True

    caption = get_random_caption()

    for attempt in range(1, MAX_RETRY + 1):

        print(f"\n📱 Device: {device} | Attempt {attempt}")

        try:
            adb(device, "shell", "rm", "/sdcard/Download/post.mp4")
            wait(2, 3)

            adb(device, "push", video_path, "/sdcard/Download/post.mp4")
            wait(4, 6)

            prepare_tiktok(device)

            # Tap +
            adb(device, "shell", "input", "tap", "540", "2200")
            wait(4, 5)

            # Upload
            adb(device, "shell", "input", "tap", "900", "1806")
            wait(4, 5)

            adb(device, "shell", "input", "tap", "340", "317")
            wait(4, 5)

            adb(device, "shell", "input", "tap", "304", "440")
            wait(4, 5)

            adb(device, "shell", "input", "tap", "821", "2197")
            wait(6, 7)

            # -------------------
            # CAPTION FIX
            # -------------------
            adb(device, "shell", "input", "tap", "540", "600")
            wait(3, 4)

            type_text(device, caption)

            # ปิดคีย์บอร์ด
            adb(device, "shell", "input", "keyevent", "4")
            wait(2, 3)

            # แตะพื้นที่ว่าง 1 ครั้งกันบัค
            adb(device, "shell", "input", "tap", "100", "100")
            wait(2, 3)

            # -------------------
            # POST BUTTON
            # -------------------
            adb(device, "shell", "input", "tap", "821", "2197")
            wait(8, 12)

            if verify_post_success(device):
                print("✅ POST SUCCESS")
                save_posted_video(os.path.basename(video_path))
                return True

            print("⚠️ Verify failed → retrying")

        except Exception as e:
            print("❌ Error:", e)

        wait(5, 8)

    print("❌ FAILED AFTER RETRY")
    return False


# =========================
# FARM LOOP
# =========================
def farm(video_path):

    for device in DEVICES:
        post_video(device, video_path)
        wait(5, 10)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    VIDEO = "video.mp4"
    farm(VIDEO)