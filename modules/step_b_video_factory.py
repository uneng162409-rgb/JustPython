import random
import json
import numpy as np
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
    VideoFileClip
)

# Pillow fix
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from modules._bootstrap import BASE_DIR, load_config
from status_manager import update_status

CFG = load_config()
STEP = CFG["step_b"]
PATHS = CFG["paths"]

PRODUCTS_DIR = Path(BASE_DIR) / PATHS["products"]
OUTPUT_DIR   = Path(BASE_DIR) / PATHS["output"]
FONT_DIR     = Path(BASE_DIR) / PATHS["fonts"]
MUSIC_DIR    = Path(BASE_DIR) / PATHS["music"]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

USED_MUSIC = set()


# =========================
# UTIL
# =========================

def already_exists(product_id):
    return (OUTPUT_DIR / product_id / "video" / "base.mp4").exists()


def load_products():
    products = []
    for p in PRODUCTS_DIR.iterdir():
        if not p.is_dir():
            continue
        imgs = list((p / "images").glob("*.jpg"))
        if imgs:
            products.append({"id": p.name, "images": imgs})
    return products


def select_music():
    if not STEP["music"]["enabled"]:
        return None

    files = list(MUSIC_DIR.glob("*.mp3"))
    if not files:
        return None

    if STEP["music"]["avoid_repeat"]:
        files = [f for f in files if f not in USED_MUSIC] or files

    m = random.choice(files)
    USED_MUSIC.add(m)
    return m


# =========================
# CINEMATIC ENGINE
# =========================

def cinematic_clip(img_path, duration):

    clip = ImageClip(str(img_path)).set_duration(duration)

    if not STEP["cinematic"]["enabled"]:
        return clip

    zoom_min = STEP["cinematic"]["zoom_min"]
    zoom_max = STEP["cinematic"]["zoom_max"]

    pan_x_min = STEP["cinematic"]["pan_x_min"]
    pan_x_max = STEP["cinematic"]["pan_x_max"]
    pan_y_min = STEP["cinematic"]["pan_y_min"]
    pan_y_max = STEP["cinematic"]["pan_y_max"]

    blur_radius = STEP["cinematic"]["blur_radius"]

    z1 = random.uniform(zoom_min, zoom_max)
    z2 = random.uniform(zoom_min, zoom_max)

    pan_x = random.choice([-1, 1]) * random.uniform(pan_x_min, pan_x_max)
    pan_y = random.choice([-1, 1]) * random.uniform(pan_y_min, pan_y_max)

    def zoom(t):
        half = duration / 2
        if t < half:
            return z1 + (z2 - z1) * (t / half)
        return z2 + (z1 - z1) * ((t - half) / half)

    animated = clip.resize(zoom)

    animated = animated.set_position(
        lambda t: (pan_x * (t / duration), pan_y * (t / duration))
    )

    def blur(get_frame, t):
        frame = get_frame(t)
        img = Image.fromarray(frame)
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        return np.array(img)

    animated = animated.fl(blur)

    return animated


# =========================
# TEXT
# =========================

def load_font(size):
    try:
        font_path = FONT_DIR / STEP["lower_third"]["font"]
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)
    except:
        pass
    return ImageFont.load_default()


def text_clip(text, duration, font_size):
    W = STEP["video"]["width"]
    H = STEP["video"]["height"]

    font = load_font(font_size)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = (W - tw) // 2
    y = H - th - STEP["lower_third"]["margin_bottom"]

    draw.rectangle(
        [x-40, y-40, x+tw+40, y+th+40],
        fill=(0, 0, 0, int(255 * STEP["lower_third"]["bg_opacity"]))
    )

    draw.text((x, y), text, font=font,
              fill=tuple(STEP["lower_third"]["text_color"]))

    return ImageClip(np.array(img)).set_duration(duration)


# =========================
# BUILD VIDEO
# =========================

def build_video(images, duration):

    per_img = duration / len(images)

    clips = [cinematic_clip(img, per_img) for img in images]

    transition = STEP["cinematic"]["transition_duration"]

    clips = [clips[0]] + [
        clips[i].crossfadein(transition)
        for i in range(1, len(clips))
    ]

    final = concatenate_videoclips(clips, method="compose", padding=-transition)

    final = final.resize((STEP["video"]["width"], STEP["video"]["height"]))

    if STEP["text"]["promo"]["enabled"]:
        overlay = text_clip(
            random.choice(STEP["text"]["promo"]["texts"]),
            duration,
            STEP["text"]["promo"]["font_size"]
        )
        final = CompositeVideoClip([final, overlay])

    music = select_music()
    if music:
        audio = AudioFileClip(str(music)).volumex(STEP["music"]["volume"])
        final = final.set_audio(audio.set_duration(final.duration))

    return final


# =========================
# EXPORT
# =========================

def export_platforms(base_path, video_dir):

    clip = VideoFileClip(str(base_path))

    for name, cfg in STEP["export"].items():
        clip.resize((cfg["width"], cfg["height"])).write_videofile(
            str(video_dir / f"{name}.mp4"),
            codec="libx264",
            audio_codec="aac",
            fps=STEP["video"]["fps"],
            verbose=False,
            logger=None
        )

    clip.close()


# =========================
# MAIN
# =========================

def run():

    if not STEP["enabled"]:
        print("⏭ STEP B DISABLED")
        return

    print("🎬 STEP B V4 : CONFIG DRIVEN ENGINE")

    products = load_products()

    if not products:
        update_status(step="STEP B", message="No products found")
        print("⚠️ NO PRODUCTS FOUND")
        return

    if STEP["factory"]["shuffle_products"]:
        random.shuffle(products)

    max_run = STEP["factory"]["max_videos_per_run"]
    products = products[:max_run]

    total = len(products)
    made = 0

    for index, product in enumerate(products, start=1):

        update_status(
            step="STEP B",
            product=product["id"],
            progress=index,
            total=total,
            message=f"Generating video {index}/{total}"
        )

        if STEP["factory"]["skip_if_exists"] and already_exists(product["id"]):
            print(f"⏩ SKIP {product['id']} (exists)")
            continue

        images = product["images"]

        if STEP["factory"]["shuffle_images"]:
            random.shuffle(images)

        images = images[:STEP["images"]["max_images"]]

        duration = random.uniform(
            STEP["video"]["min_duration"],
            STEP["video"]["max_duration"]
        )

        video = build_video(images, duration)

        product_dir = OUTPUT_DIR / product["id"]
        video_dir = product_dir / "video"
        video_dir.mkdir(parents=True, exist_ok=True)

        base_path = video_dir / "base.mp4"

        video.write_videofile(
            str(base_path),
            fps=STEP["video"]["fps"],
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None
        )

        video.close()

        export_platforms(base_path, video_dir)

        with open(product_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump({
                "product_id": product["id"],
                "created_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

        made += 1
        print(f"✅ DONE {product['id']} ({made})")

    update_status(
        step="STEP B",
        progress=total,
        total=total,
        message="STEP B COMPLETE"
    )

    print("🎉 STEP B V4 COMPLETE")