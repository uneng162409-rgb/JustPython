import os
import json

BIO_DIR = "bio_pages"
PRODUCT_JSON = "products.json"


def generate_bio_page(product_id, title, affiliate):

    os.makedirs(BIO_DIR, exist_ok=True)

    html = f"""
    <html>
    <head>
    <meta charset="UTF-8">
    <title>{title}</title>
    </head>

    <body style="text-align:center;font-family:sans-serif;">
        <h1>{title}</h1>

        <a href="{affiliate}">
        🛒 ซื้อสินค้าตอนนี้
        </a>

    </body>
    </html>
    """

    with open(f"{BIO_DIR}/{product_id}.html", "w", encoding="utf-8") as f:
        f.write(html)


def update_products_json(product_id, title):

    if os.path.exists(PRODUCT_JSON):

        try:
            with open(PRODUCT_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)

        except:
            data = []

    else:
        data = []

    for p in data:
        if p["id"] == product_id:
            return

    data.append({
        "id": product_id,
        "name": title
    })

    with open(PRODUCT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)