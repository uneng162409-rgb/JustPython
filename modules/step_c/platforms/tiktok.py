import os
import random
import time
import subprocess

TEXT_FILE = "texts.txt"
LOG_FILE = "posted_log.txt"


def load_captions():
    if not os.path.exists(TEXT_FILE):
        print("❌ texts.txt not found")
        return []

    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    return lines


def load_posted():
    if not os.path.exists(LOG_FILE):
        return set()

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_posted(caption):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(caption + "\n")


def get_random_caption():
    captions = load_captions()

    if not captions:
        print("⚠ texts.txt ว่าง ใช้ fallback")
        return "🔥"

    posted = load_posted()

    # กันซ้ำ
    available = [c for c in captions if c not in posted]

    # ถ้าใช้ครบแล้ว รีเซ็ต log
    if not available:
        print("♻ Caption ใช้ครบแล้ว รีเซ็ต log")
        open(LOG_FILE, "w", encoding="utf-8").close()
        available = captions

    caption = random.choice(available)

    save_posted(caption)

    return caption


def human_delay(min_sec=0.3, max_sec=1.2):
    time.sleep(random.uniform(min_sec, max_sec))


def adb(device, *args):
    return subprocess.run(["adb", "-s", device, *args], check=False)


def set_clipboard(device, text):
    safe_text = text.replace("\n", " ").replace('"', "").replace("'", "")

    adb(device,
        "shell",
        "cmd",
        "clipboard",
        "set",
        "text",
        safe_text
    )
    time.sleep(1)


def paste_clipboard(device):
    adb(device, "shell", "input", "keyevent", "279")  # KEYCODE_PASTE
    time.sleep(1)


def type_text(device, text):
    """
    พิมพ์ข้อความแบบปลอดภัย รองรับเว้นวรรค
    """
    safe = text.replace(" ", "%s").replace("\n", "%s")
    adb(device, "shell", "input", "text", safe)
    human_delay(1, 2)


def post(device, video, caption, cfg=None, comment_link=None):

    try:
        print(f"🎵 TikTok Posting: {video}")

        # -----------------------------
        # PUSH VIDEO
        # -----------------------------
        adb(device, "push", video, "/sdcard/Download/post.mp4")
        time.sleep(2)

        # -----------------------------
        # OPEN TIKTOK
        # -----------------------------
        adb(device, "shell", "monkey",
            "-p", "com.ss.android.ugc.trill",
            "-c", "android.intent.category.LAUNCHER",
            "1")

        time.sleep(6)

        # -----------------------------
        # UPLOAD FLOW
        # -----------------------------
        adb(device, "shell", "input", "tap", "540", "2200")  # +
        time.sleep(3)

        adb(device, "shell", "input", "tap", "900", "1806")  # Upload
        time.sleep(3)

        adb(device, "shell", "input", "tap", "340", "317")   # Video Tab
        time.sleep(2)

        adb(device, "shell", "input", "tap", "304", "440")   # First Video
        time.sleep(3)

        adb(device, "shell", "input", "tap", "821", "2197")  # Next
        time.sleep(8)  # รอเข้า caption page จริง

        # -----------------------------
        # INPUT CAPTION
        # -----------------------------
        caption = get_random_caption()
        print("📝 Caption:", caption)

        adb(device, "shell", "input", "tap", "540", "600")
        time.sleep(2)

        set_clipboard(device, caption)
        paste_clipboard(device)

        human_delay(2, 3)

        # ปิด keyboard
        adb(device, "shell", "input", "keyevent", "4")
        time.sleep(2)

        print("🚀 Posting...")

        # ใช้พิกัดเดิมล่างจอ
        adb(device, "shell", "input", "tap", "540", "2197")
        time.sleep(8)

        print("✅ Video Posted")

        return True

    except Exception as e:
        print("❌ TikTok Post Error:", e)
        return False
