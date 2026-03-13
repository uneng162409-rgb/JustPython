import urllib.parse
import os
import yaml
import hashlib
import random
import time
import json
from datetime import datetime
from pathlib import Path

from modules.step_c.platforms import tiktok, shopee, reels


# ==========================================
# LOAD CONFIG
# ==========================================

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ==========================================
# UTILS
# ==========================================

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def get_all_videos(output_path):
    videos = []
    for root, _, files in os.walk(output_path):
        for f in files:
            if f.endswith(".mp4") and "base.mp4" not in f:
                videos.append(os.path.join(root, f))
    return videos


def extract_product_id(video_path):
    path = Path(video_path)

    # กรณีโครงสร้างแบบ output/<product_id>/video.mp4
    parts = path.parts
    if "output" in parts:
        idx = parts.index("output")
        if len(parts) > idx + 1:
            candidate = parts[idx + 1]
            if candidate.isdigit():
                return candidate

    # กรณีไฟล์อยู่ตรง ๆ เช่น output/14100938177.mp4
    filename = path.stem
    if filename.isdigit():
        return filename

    return None


# ==========================================
# AFFILIATE LINK RESOLVER (SAFE + MULTI SOURCE)
# ==========================================

def read_affiliate_link(products_path, product_id):

    product_dir = Path(products_path) / product_id

    # 1️⃣ meta.json (priority สูงสุด)
    meta_path = product_dir / "meta.json"
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            # รองรับหลายรูปแบบ
            if isinstance(meta, dict):
                if "affiliate_link" in meta:
                    return meta["affiliate_link"]

                if product_id in meta and isinstance(meta[product_id], dict):
                    if "affiliate_link" in meta[product_id]:
                        return meta[product_id]["affiliate_link"]
        except:
            pass

    # 2️⃣ affiliate_link.txt
    txt_path = product_dir / "affiliate_link.txt"
    if txt_path.exists():
        link = txt_path.read_text(encoding="utf-8").strip()
        if link.startswith("http"):
            return link

    # 3️⃣ global fallback
    global_path = Path(products_path) / "affiliate_links.json"
    if global_path.exists():
        try:
            with open(global_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if product_id in data:
                    return data[product_id]
        except:
            pass

    return None


def read_product_meta(products_path, product_id):
    meta_path = Path(products_path) / product_id / "meta.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def already_posted(history_file, vhash):
    if not os.path.exists(history_file):
        return False
    with open(history_file, "r", encoding="utf-8") as f:
        return vhash in f.read()


def save_history(history_file, vhash):
    ensure_dir(os.path.dirname(history_file))
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(vhash + "\n")


# ==========================================
# SAFE DELAY ENGINE (ANTI-BAN READY)
# ==========================================

def smart_delay(step_cfg):
    if step_cfg.get("random_delay", False):
        min_d = step_cfg.get("min_delay", 40)
        max_d = step_cfg.get("max_delay", 120)
        delay = random.randint(min_d, max_d)
    else:
        delay = step_cfg.get("delay_between_platforms", 10)

    print(f"⏳ Delay {delay} sec")
    time.sleep(delay)


# ==========================================
# CAPTION ENGINE (SMART VARIATION)
# ==========================================

def generate_caption(cfg, product_meta, affiliate_link):

    caption_cfg = cfg["step_c"]["caption"]

    title = product_meta.get("title", "สินค้าขายดี")
    price = product_meta.get("price", 0)
    sold = product_meta.get("sold", 0)
    rating = product_meta.get("rating", 0)

    # 🔥 Dynamic Hook ตามข้อมูลจริง
    if sold > 1000:
        opener = f"🔥 ขายแล้ว {sold:,} ชิ้น! {title}"
    elif rating >= 4.8:
        opener = f"⭐ รีวิว {rating} ดาว! {title}"
    elif price and price < 100:
        opener = f"💸 ถูกมาก! {title} แค่ {price} บาท"
    else:
        opener = f"🎯 โปรแรง! {title}"

    cta_lines = [
        "👉 รีบกดก่อนหมด!",
        "👉 เช็คราคาล่าสุดที่ลิงก์",
        "👉 โปรจำกัดเวลา",
        "👉 กดดูรายละเอียดเลย"
    ]

    cta = random.choice(cta_lines)

    include_link_in_caption = random.choice([True, False])

    hashtags = ""
    if caption_cfg.get("add_hashtags"):
        tags = caption_cfg.get("default_hashtags", [])
        if tags:
            tags = random.sample(tags, min(len(tags), caption_cfg.get("hashtag_limit", 5)))
            hashtags = "\n\n" + " ".join(tags)

    body = f"{opener}\n\n💰 ราคา: {price}\n⭐ คะแนน: {rating}\n📦 ขายแล้ว: {sold:,} ชิ้น\n\n{cta}"
    # 🔥 Clean affiliate link (decode)
    clean_link = urllib.parse.unquote(affiliate_link)

    if include_link_in_caption:
        return f"{body}\n{clean_link}{hashtags}", None
    else:
        return f"{body}{hashtags}", clean_link


# ==========================================
# MAIN ENGINE
# ==========================================

def run_step_c():

    cfg = load_config()
    step = cfg["step_c"]

    license_cfg = cfg.get("license", {})

    if not step.get("enabled", False):
        print("❌ STEP C Disabled")
        return

    print("💰 STEP C MONETIZATION ENGINE V2")

    output_path = cfg["paths"]["output"]
    products_path = cfg["paths"]["products"]

    videos = get_all_videos(output_path)

    if not videos:
        print("❌ No videos found")
        return

    for device in step["devices"]:
        print(f"\n📱 Device: {device}")

        for platform_name, platform_cfg in step["platforms"].items():
            # 🔐 LICENSE PLATFORM CHECK
            if license_cfg.get("enabled", False):
                allowed = license_cfg.get("allowed_platforms", [])

                if allowed and platform_name not in allowed:
                    print(f"🔒 License block: {platform_name}")
                    continue

            if not platform_cfg.get("enabled", False):
                continue

            video = random.choice(videos)
            vhash = file_hash(video)

            history_file = f'post_history/{platform_name}.txt'

            if step.get("skip_if_posted", True):
                if already_posted(history_file, vhash):
                    print(f"⏩ SKIP {platform_name} (duplicate)")
                    continue

            product_id = extract_product_id(video)

            if not product_id:
                print("⚠️ Cannot detect product_id")
                continue

            affiliate_link = read_affiliate_link(products_path, product_id)

            if not affiliate_link:
                print(f"⚠️ No affiliate link for {product_id} → SKIP")
                continue

            product_meta = read_product_meta(products_path, product_id)

            caption, comment_link = generate_caption(cfg, product_meta, affiliate_link)

            print(f"📝 Caption Ready for {product_id}")

            if platform_name == "tiktok":
                success = tiktok.post(device, video, caption, cfg, comment_link)
            elif platform_name == "shopee":
                success = shopee.post(device, video, caption, cfg, comment_link)
            elif platform_name == "reels":
                success = reels.post(device, video, caption, cfg, comment_link)
            else:
                continue

            if success:
                save_history(history_file, vhash)
                print(f"✅ Posted to {platform_name}")
            else:
                print(f"❌ Failed posting {platform_name}")

            smart_delay(step)



    print("🎉 STEP C MONETIZATION COMPLETE")
