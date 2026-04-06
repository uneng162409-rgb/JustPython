import os
import shutil

BASE_DIR = "videos_pool"
READY_DIR = os.path.join(BASE_DIR, "ready")
POSTED_DIR = os.path.join(BASE_DIR, "posted_today")

BUFFER_SIZE = 3


def ensure_folders():
    os.makedirs(READY_DIR, exist_ok=True)
    os.makedirs(POSTED_DIR, exist_ok=True)


def get_ready_videos():
    return [f for f in os.listdir(READY_DIR) if f.endswith(".mp4")]


def move_to_posted(filename):
    shutil.move(
        os.path.join(READY_DIR, filename),
        os.path.join(POSTED_DIR, filename)
    )


def reset_posted_to_ready():
    for f in os.listdir(POSTED_DIR):
        shutil.move(
            os.path.join(POSTED_DIR, f),
            os.path.join(READY_DIR, f)
        )


def buffer_needed(state):
    needed_today = state["today_target"] - state["today_done"]
    ready_count = len(get_ready_videos())
    return ready_count < (needed_today + BUFFER_SIZE)