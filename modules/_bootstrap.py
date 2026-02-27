from pathlib import Path
import yaml

# =========================
# BASE DIR (Pathlib)
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================
# LOAD CONFIG
# =========================
def load_config():
    with open(BASE_DIR / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)