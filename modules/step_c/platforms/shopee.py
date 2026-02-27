from modules.step_c.adb_core import tap, push_video, human_sleep


def post(device, video, caption, cfg, comment_link=None):

    step_cfg = cfg["step_c"]

    print(f"🛒 Shopee Posting {video_path}")

    push_video(device, video_path)
    human_sleep(step_cfg)

    tap(device, 540, 1800, step_cfg)
    tap(device, 300, 1600, step_cfg)
    tap(device, 950, 1750, step_cfg)

    return True
