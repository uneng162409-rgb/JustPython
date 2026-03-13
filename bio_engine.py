import os
import json
import subprocess
from datetime import datetime


class BioEngine:

    BASE_DIR = os.getcwd()
    BIO_DIR = os.path.join(BASE_DIR, "bio_pages")
    REDIRECT_DIR = os.path.join(BASE_DIR, "redirect")
    PRODUCTS_JSON = os.path.join(BASE_DIR, "products.json")

    # ===============================
    # MAIN BUILD FUNCTION
    # ===============================
    @classmethod
    def build(cls, product_data):
        cls._ensure_folders()
        cls.create_product_page(product_data)
        cls.update_products_json(product_data)
        cls.create_redirect(product_data)

        print("✅ BIO ENGINE BUILD COMPLETE")

    # ===============================
    # CREATE BIO PAGE
    # ===============================
    @classmethod
    def create_product_page(cls, product_data):

        product_id = str(product_data["id"])
        name = product_data.get("name", "สินค้าแนะนำ")
        image = product_data.get("image", "")
        shopee = product_data.get("affiliate_link", "#")

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
                    margin: 30px auto;
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
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>{name}</h2>
                <img src="{image}">
                <a href="../redirect/{product_id}.html">ซื้อผ่าน Shopee</a>
            </div>
        </body>
        </html>
        """

        file_path = os.path.join(cls.BIO_DIR, f"{product_id}.html")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✅ Created Bio Page: {product_id}.html")

    # ===============================
    # UPDATE PRODUCTS.JSON
    # ===============================
    @classmethod
    def update_products_json(cls, product_data):

        product_id = str(product_data["id"])
        name = product_data.get("name", "สินค้าแนะนำ")

        data = []

        if os.path.exists(cls.PRODUCTS_JSON):
            with open(cls.PRODUCTS_JSON, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except:
                    data = []

        # เช็คซ้ำ
        if not any(p["id"] == product_id for p in data):
            data.append({
                "id": product_id,
                "name": name
            })

        with open(cls.PRODUCTS_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("✅ Updated products.json")

    # ===============================
    # CREATE REDIRECT PAGE
    # ===============================
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

    # ===============================
    # GIT PUSH
    # ===============================
    @classmethod
    def auto_push(cls):

        try:
            subprocess.run("git add .", shell=True, check=True)
            subprocess.run(f'git commit -m "Auto update {datetime.now()}"', shell=True, check=True)
            subprocess.run("git push", shell=True, check=True)
            print("🚀 Pushed to GitHub")
        except subprocess.CalledProcessError:
            print("⚠ Nothing to commit or git error")

    # ===============================
    # CREATE FOLDERS IF NOT EXISTS
    # ===============================
    @classmethod
    def _ensure_folders(cls):
        os.makedirs(cls.BIO_DIR, exist_ok=True)
        os.makedirs(cls.REDIRECT_DIR, exist_ok=True)