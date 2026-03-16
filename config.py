# ===== PLATFORM SWITCH =====
ENABLE_SHOPEE = True
ENABLE_LAZADA = True
ENABLE_TIKTOK = True
ENABLE_YOUPIK = False

# ===== PLATFORM LINKS TEMPLATE =====
PLATFORM_LINKS = {
    "shopee": "https://shopee.co.th/product/{product_id}",
    "lazada": "https://lazada.co.th/products/{product_id}",
    "tiktok": "https://tiktok.com/shop/{product_id}",
    "youpik": "https://youpik.com/item/{product_id}",
}

# ===== GOOGLE ANALYTICS =====
GA_TRACKING_ID = "G-G8Q9NCDTVL"
# =========================
# AUTO DEPLOY CONTROL
# =========================

AUTO_COMMIT = True
AUTO_PUSH = True

GIT_COMMIT_MESSAGE = "auto: update bio pages"
