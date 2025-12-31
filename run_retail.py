from core.storage.db import init_db, get_db
from tools.manual_agent import collect_retail_input
from core.engine.retail import process_retail_sale

def seed_stock():
    conn = get_db()
    cur = conn.cursor()

    # Use inventory table (new schema)
    cur.execute(
        "INSERT OR IGNORE INTO inventory (sku, quantity) VALUES (?, ?)",
        ("MILK001", 100)
    )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_stock()

    customer, items, payment = collect_retail_input()
    order_id = process_retail_sale(customer, items, payment)

    print(f"✅ Retail sale completed. Order ID: {order_id}")