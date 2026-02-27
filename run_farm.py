import traceback
from modules._bootstrap import load_config
from modules.step_a_fetch_and_filter import run as step_a
from modules.step_b_video_factory import run as step_b
from modules.step_c.post_engine import run_step_c


CFG = load_config()


def main():
    try:
        print("🟢 RUN FARM START")

        # =========================
        # STEP A
        # =========================
        if CFG.get("step_a", {}).get("enabled", False):
            print("🚀 STEP A START")
            step_a()
            print("✅ STEP A DONE")

        # =========================
        # STEP B
        # =========================
        if CFG.get("step_b", {}).get("enabled", False):
            print("🎬 STEP B START")
            step_b()
            print("✅ STEP B DONE")

        # =========================
        # STEP C
        # =========================
        if CFG.get("step_c", {}).get("enabled", False):
            print("📤 STEP C START")
            run_step_c()
            print("✅ STEP C DONE")

        print("🟢 RUN FARM END")

    except Exception as e:
        print("❌ FARM ERROR:", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
