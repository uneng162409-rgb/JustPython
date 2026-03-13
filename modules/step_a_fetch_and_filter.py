import os
import json
import requests
import pandas as pd
import urllib.parse
import subprocess
from datetime import datetime

from modules._bootstrap import BASE_DIR, load_config
from bio_engine import BioEngine


# =====================
# LOAD CONFIG
# =====================
CFG = load_config()
STEP = CFG["step_a"]
PATHS = CFG["paths"]

PRODUCTS_DIR = os.path.join(BASE_DIR, PATHS["products"])
os.makedirs(PRODUCTS_DIR, exist_ok=True)


# =====================
# HELPERS
# =====================
def is_real_affiliate(url: str) -> bool:
    return isinstance(url, str) and url.startswith("https://shope.ee")


def make_affiliate(product_url: str) -> str:

    if not product_url:
        return ""

    encoded = urllib.parse.quote(product_url, safe="")

    return f"{STEP['affiliate']['universal_link']}?redir={encoded}"


def download_image(url: str, path: str, timeout: int) -> bool:

    try:

        r = requests.get(url, timeout=timeout)

        if r.status_code == 200 and r.content:

            with open(path, "wb") as f:
                f.write(r.content)

            return True

    except Exception as e:
        print(f"⚠️ IMAGE FAIL {url} ({e})")

    return False


# =====================
# LOAD FEED
# =====================
def load_feed() -> pd.DataFrame:

    feed_file = os.path.join(BASE_DIR, STEP["feed"]["file"])

    if not os.path.exists(feed_file):
        raise FileNotFoundError(feed_file)

    df = pd.read_csv(feed_file, low_memory=False)

    print(f"📦 FEED LOADED : {len(df)} rows")

    for col in ["price", "discount_percentage", "item_sold", "shop_rating"]:

        if col not in df.columns:
            df[col] = 0

        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


# =====================
# SCORE ENGINE
# =====================
def score_products(df: pd.DataFrame) -> pd.DataFrame:

    sc = STEP["score"]
    w = sc["weights"]
    n = sc["normalize"]

    df["_price_score"] = 1 - (df["price"] / n["price_max"]).clip(0, 1)
    df["_discount_score"] = (df["discount_percentage"] / n["discount_max"]).clip(0, 1)
    df["_sold_score"] = (df["item_sold"] / n["sold_max"]).clip(0, 1)
    df["_rating_score"] = (df["shop_rating"] / 5).clip(0, 1)

    df["score"] = (
        df["_price_score"] * w["price"] +
        df["_discount_score"] * w["discount"] +
        df["_sold_score"] * w["sold"] +
        df["_rating_score"] * w["rating"]
    )

    return df


def auto_relax_if_needed(df: pd.DataFrame) -> pd.DataFrame:

    sc = STEP["score"]

    if not sc["auto_relax"]["enabled"]:
        return df

    if df["score"].sum() > 0:
        return df

    factor = sc["auto_relax"]["relax_factor"]

    print(f"🧠 AUTO RELAX ACTIVATED (x{factor})")

    df["score"] = (
        df["_price_score"] * factor +
        df["_discount_score"] * factor +
        df["_sold_score"] * factor +
        df["_rating_score"] * factor
    )

    return df


# =====================
# PREPARE PRODUCT
# =====================
def prepare_product(row) -> bool:

    itemid = str(row.get("itemid", "")).strip()

    if not itemid:
        return False

    product_dir = os.path.join(PRODUCTS_DIR, itemid)
    images_dir = os.path.join(product_dir, "images")

    if os.path.exists(product_dir):
        return False

    os.makedirs(images_dir, exist_ok=True)

    affiliate = row.get("affiliate_link", "")

    if STEP["affiliate"]["enabled"] and not is_real_affiliate(affiliate):
        affiliate = make_affiliate(row.get("product_link", ""))

    with open(os.path.join(product_dir, "affiliate_link.txt"), "w", encoding="utf-8") as f:
        f.write(affiliate or "")

    downloaded = 0

    urls = [
        v for k, v in row.items()
        if str(k).startswith("image_link") and isinstance(v, str)
    ][:STEP["images"]["per_product"]]

    first_image = ""

    for i, url in enumerate(urls, 1):

        path = os.path.join(images_dir, f"{i}.jpg")

        if download_image(url, path, STEP["images"]["timeout"]):

            downloaded += 1

            if i == 1:
                first_image = url

    if downloaded == 0:
        return False

    title = row.get("title", f"สินค้า {itemid}")

    meta = {
        "itemid": itemid,
        "score": row.get("score", 0),
        "price": row.get("price", 0),
        "sold": row.get("item_sold", 0),
        "rating": row.get("shop_rating", 0),
        "affiliate": affiliate,
        "images": downloaded,
        "created_at": datetime.now().isoformat()
    }

    with open(os.path.join(product_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # =====================
    # BIO ENGINE
    # =====================

    product_data = {
        "id": itemid,
        "name": title,
        "image": first_image,
        "affiliate_link": affiliate
    }

    BioEngine.build(product_data)

    print(f"📦 READY {itemid} | score={row.get('score'):.3f}")

    return True


# =====================
# ENTRY POINT
# =====================
def run():

    if not STEP["enabled"]:
        return

    print("🚀 STEP A : SCORE-BASED PRODUCT PIPELINE")

    df = load_feed()

    df = score_products(df)

    df = auto_relax_if_needed(df)

    df = df[df["score"] >= STEP["score"]["min_score"]]

    df = df.sort_values("score", ascending=False)

    if STEP["winners"]["enabled"]:
        df = df.head(STEP["winners"]["max_seed"])

    df = df.head(STEP["images"]["max_products"])

    created = 0

    for _, row in df.iterrows():

        if prepare_product(row):
            created += 1

    print(f"✅ STEP A DONE : {created}")
    import subprocess

    def git_push_once():

        try:

            subprocess.run(["git", "add", "."], check=True)

            subprocess.run(
                ["git", "commit", "-m", f"Auto update {datetime.now()}"],
                check=True
            )

            subprocess.run(["git", "push"], check=True)

            print("🚀 PUSHED TO GITHUB (ONCE)")

        except subprocess.CalledProcessError:

            print("⚠️ NOTHING TO COMMIT")

    if created > 0:
        git_push_once()