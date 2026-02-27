import subprocess
import time
import random


def run_adb(device, command):
    full_cmd = ["adb", "-s", device] + command.split()
    subprocess.run(full_cmd, check=False)


def human_sleep(cfg):
    if not cfg["human_delay"]["enabled"]:
        return
    t = random.uniform(
        cfg["human_delay"]["min_action_delay"],
        cfg["human_delay"]["max_action_delay"]
    )
    time.sleep(t)


def tap(device, x, y, cfg):
    run_adb(device, f"shell input tap {x} {y}")
    human_sleep(cfg)


def swipe(device, x1, y1, x2, y2, duration, cfg):
    run_adb(device, f"shell input swipe {x1} {y1} {x2} {y2} {duration}")
    human_sleep(cfg)


def text(device, message, cfg):
    message = message.replace(" ", "%s")
    run_adb(device, f"shell input text {message}")
    human_sleep(cfg)


def push_video(device, local_path):
    subprocess.run(
        ["adb", "-s", device, "push", local_path, "/sdcard/Download/"],
        check=False
    )

