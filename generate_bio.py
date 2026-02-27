import os
import json
from config import *

PRODUCT_FILE = "products.json"

def update_products_json(product_id, product_name):
    if os.path.exists(PRODUCT_FILE):
        with open(PRODUCT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    if not any(p["id"] == product_id for p in data):
        data.append({
            "id": product_id,
            "name": product_name
        })

    with open(PRODUCT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def generate_redirect_page(product_id):
    os.makedirs("bio_pages", exist_ok=True)

    redirect_html = f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=landing_{product_id}.html" />
    </head>
    <body>
        Redirecting...
    </body>
    </html>
    """

    with open(f"bio_pages/{product_id}.html", "w", encoding="utf-8") as f:
        f.write(redirect_html)


def generate_landing_page(product_id, product_name):

    analytics_script = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_TRACKING_ID}');
    </script>
    """

    links_html = ""

    if ENABLE_SHOPEE:
        shopee_link = PLATFORM_LINKS["shopee"].format(product_id=product_id)
        links_html += f'<a href="{shopee_link}" target="_blank" onclick="gtag(\'event\', \'click\', {{\'event_category\': \'Shopee\', \'event_label\': \'{product_id}\'}});">🛒 Shopee</a><br><br>'

    if ENABLE_LAZADA:
        lazada_link = PLATFORM_LINKS["lazada"].format(product_id=product_id)
        links_html += f'<a href="{lazada_link}" target="_blank" onclick="gtag(\'event\', \'click\', {{\'event_category\': \'Lazada\', \'event_label\': \'{product_id}\'}});">🛒 Lazada</a><br><br>'

    if ENABLE_TIKTOK:
        tiktok_link = PLATFORM_LINKS["tiktok"].format(product_id=product_id)
        links_html += f'<a href="{tiktok_link}" target="_blank" onclick="gtag(\'event\', \'click\', {{\'event_category\': \'TikTok\', \'event_label\': \'{product_id}\'}});">📦 TikTok Shop</a><br><br>'

    html_content = f"""
    <html>
    <head>
        <title>{product_name}</title>
        {analytics_script}
    </head>
    <body style="text-align:center;font-family:sans-serif;">
        <h2>{product_name}</h2>
        <p>เลือกช่องทางสั่งซื้อ</p>
        <br>
        {links_html}
    </body>
    </html>
    """

    with open(f"bio_pages/landing_{product_id}.html", "w", encoding="utf-8") as f:
        f.write(html_content)


def generate_full_bio(product_id, product_name):
    update_products_json(product_id, product_name)
    generate_redirect_page(product_id)
    generate_landing_page(product_id, product_name)
    print(f"✅ FARM BIO CREATED: {product_id}")


if __name__ == "__main__":
    generate_full_bio("111222333", "สินค้า Farm Mode ทดสอบ")