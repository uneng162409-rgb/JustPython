from modules.step_c.adb_core import tap, text, push_video, human_sleep


def post(device, video, caption, cfg, comment_link=None):

    step_cfg = cfg["step_c"]

    print(f"📘 Reels Posting {video_path}")

    push_video(device, video_path)
    human_sleep(step_cfg)

    tap(device, 540, 1800, step_cfg)
    tap(device, 300, 1600, step_cfg)

    text(device, caption, step_cfg)

    tap(device, 950, 1750, step_cfg)

    return True
