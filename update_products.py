import json
import os

def add_product(product_id, product_name):
    file = "products.json"

    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    # ป้องกันซ้ำ
    for p in data:
        if p["id"] == product_id:
            print("สินค้าอยู่แล้ว")
            return

    data.append({
        "id": product_id,
        "name": product_name
    })

    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print("เพิ่มสินค้าแล้ว")

if __name__ == "__main__":
    add_product("99999999999", "สินค้าทดสอบใหม่")