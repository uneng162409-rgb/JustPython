import traceback
import time
from modules._bootstrap import load_config
from modules.step_a_fetch_and_filter import run as step_a
from modules.step_b_video_factory import run as step_b
from modules.step_c.post_engine import run_step_c
from modules.system_state import update_state, mark_crash


def run_step(label, func):
    update_state(step=label, message=f"กำลังทำงาน {label}")

    print(f"\n==============================")
    print(f"🚀 {label} START")
    print(f"==============================")

    func()

    update_state(message=f"{label} เสร็จแล้ว")

    print(f"==============================")
    print(f"✅ {label} DONE")
    print(f"==============================\n")


def main():

    cfg = load_config()

    print("\n🟢 SMART FARM SYSTEM v2 START\n")

    update_state(step="INIT", message="Smart Farm กำลังเริ่มทำงาน...")

    try:

        # STEP A
        if cfg.get("step_a", {}).get("enabled", False):
            run_step("STEP A - PRODUCT PIPELINE", step_a)

        # STEP B
        if cfg.get("step_b", {}).get("enabled", False):
            run_step("STEP B - VIDEO FACTORY", step_b)

        # STEP C
        if cfg.get("step_c", {}).get("enabled", False):
            run_step("STEP C - POST ENGINE", run_step_c)

        update_state(step="-", message="รอรอบถัดไป")

        print("\n🎉 FARM RUN COMPLETE\n")

    except Exception as e:
        print("\n❌ FARM CRASHED")
        print(e)
        traceback.print_exc()

        mark_crash(str(e))


if __name__ == "__main__":
    main()