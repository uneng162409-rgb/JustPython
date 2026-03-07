import os
import json
from config import *

PRODUCT_JSON = "products.json"

def update_products_json(product_id, product_name):

    if os.path.exists(PRODUCT_JSON):
        with open(PRODUCT_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    # ตรวจว่ามีสินค้านี้แล้วหรือยัง
    for item in data:
        if item["id"] == product_id:
            return

    data.append({
        "id": product_id,
        "name": product_name
    })

    with open(PRODUCT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("✅ products.json updated")


def generate_page(product_id, product_name):

    os.makedirs("bio_pages", exist_ok=True)

    links_html = ""

    if ENABLE_SHOPEE:
        link = PLATFORM_LINKS["shopee"].format(product_id=product_id)
        links_html += f'<a href="{link}">🛒 ซื้อที่ Shopee</a><br><br>'

    if ENABLE_LAZADA:
        link = PLATFORM_LINKS["lazada"].format(product_id=product_id)
        links_html += f'<a href="{link}">🛒 ซื้อที่ Lazada</a><br><br>'

    if ENABLE_TIKTOK:
        link = PLATFORM_LINKS["tiktok"].format(product_id=product_id)
        links_html += f'<a href="{link}">📦 ซื้อที่ TikTok Shop</a><br><br>'

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{product_name}</title>
    </head>

    <body style="text-align:center;font-family:sans-serif;">
        <h1>{product_name}</h1>
        <p>เลือกช่องทางสั่งซื้อ</p>
        <br>
        {links_html}
    </body>
    </html>
    """

    with open(f"bio_pages/{product_id}.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ Bio Page Created")


if __name__ == "__main__":

    product_id = "88888888"
    product_name = "สินค้าใหม่ทดลอง"

    generate_page(product_id, product_name)
    update_products_json(product_id, product_name)

    from auto_push import push_to_github

    push_to_github()