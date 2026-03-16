import os
import json
import subprocess
from datetime import datetime
from config import AUTO_COMMIT, AUTO_PUSH, GIT_COMMIT_MESSAGE


class BioEngine:

    BASE_DIR = os.getcwd()
    BIO_DIR = os.path.join(BASE_DIR, "bio_pages")
    REDIRECT_DIR = os.path.join(BASE_DIR, "redirect")
    PRODUCTS_JSON = os.path.join(BASE_DIR, "products.json")

    # ==========================================
    # MAIN BUILD ENTRY (เรียกจาก STEP A)
    # ==========================================
    @classmethod
    def build(cls, product_data):
        cls._ensure_folders()
        cls.create_product_page(product_data)
        cls.update_products_json(product_data)
        cls.create_redirect(product_data)
        cls.auto_push()
        print("✅ BIO ENGINE BUILD COMPLETE")

    # ==========================================
    # CREATE BIO PAGE
    # ==========================================
    @classmethod
    def create_product_page(cls, product_data):

        product_id = str(product_data["id"])
        name = product_data.get("name", "สินค้าแนะนำ")
        image = product_data.get("image", "")
        affiliate = product_data.get("affiliate_link", "#")

        html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{name}</title>
            <style>
                body {{
                    font-family: Arial;
                    text-align: center;
                    background: #f5f5f5;
                }}
                .card {{
                    background: white;
                    padding: 20px;
                    margin: 40px auto;
                    width: 350px;
                    border-radius: 12px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                img {{
                    width: 100%;
                    border-radius: 8px;
                }}
                a {{
                    display: block;
                    margin-top: 15px;
                    padding: 12px;
                    background: orange;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>{name}</h2>
                <img src="{image}">
                <a href="../redirect/{product_id}.html">🛒 ซื้อผ่าน Shopee</a>
            </div>
        </body>
        </html>
        """

        file_path = os.path.join(cls.BIO_DIR, f"{product_id}.html")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✅ Created Bio Page: {product_id}.html")

    # ==========================================
    # UPDATE PRODUCTS.JSON (กันซ้ำ + update ได้)
    # ==========================================
    @classmethod
    def update_products_json(cls, product_data):

        product_id = str(product_data["id"])
        name = product_data.get("name", "สินค้าแนะนำ")

        data = []

        if os.path.exists(cls.PRODUCTS_JSON):
            try:
                with open(cls.PRODUCTS_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                data = []

        # เช็คว่ามีอยู่แล้วไหม
        existing = next((p for p in data if p["id"] == product_id), None)

        if existing:
            existing["name"] = name
        else:
            data.append({
                "id": product_id,
                "name": name
            })

        with open(cls.PRODUCTS_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("✅ Updated products.json")

    # ==========================================
    # CREATE REDIRECT PAGE
    # ==========================================
    @classmethod
    def create_redirect(cls, product_data):

        product_id = str(product_data["id"])
        link = product_data.get("affiliate_link", "#")

        html = f"""
        <html>
        <head>
            <meta http-equiv="refresh" content="0; url={link}">
        </head>
        <body>
            Redirecting...
        </body>
        </html>
        """

        file_path = os.path.join(cls.REDIRECT_DIR, f"{product_id}.html")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✅ Created Redirect: {product_id}.html")

    # ==========================================
    # AUTO GIT PUSH (ใช้ config คุม)
    # ==========================================
    @classmethod
    def auto_push(cls):

        try:
            if AUTO_COMMIT:
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(
                    ["git", "commit", "-m",
                     f"{GIT_COMMIT_MESSAGE} {datetime.now()}"],
                    check=False
                )

            if AUTO_PUSH:
                subprocess.run(["git", "push"], check=True)

            print("🚀 Git Push Complete")

        except Exception as e:
            print("⚠ Git Error:", e)

    # ==========================================
    # ENSURE FOLDERS
    # ==========================================
    @classmethod
    def _ensure_folders(cls):
        os.makedirs(cls.BIO_DIR, exist_ok=True)
        os.makedirs(cls.REDIRECT_DIR, exist_ok=True)