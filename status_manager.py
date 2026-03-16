import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, "farm_status.json")


def update_status(step=None, progress=None, message=None,
                  product=None, total=None, index=None):

    status = {}

    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status = json.load(f)

    if step is not None:
        status["step"] = step

    if progress is not None:
        status["progress"] = progress

    if message is not None:
        status["message"] = message

    if product is not None:
        status["product"] = product

    if total is not None:
        status["total"] = total

    if index is not None:
        status["index"] = index

    status["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=4, ensure_ascii=False)


def get_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {}