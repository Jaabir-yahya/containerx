"""
Factory for creating test inventory data.
"""

def create_inventory_data(sku, quantity):
    """
    Create inventory item data.
    
    Args:
        sku: Stock keeping unit
        quantity: Available quantity
    
    Returns:
        dict: Inventory data
    """
    return {
        "sku": sku,
        "quantity": quantity
    }

def seed_inventory(conn, items):
    """
    Seed inventory table with items.
    
    Args:
        conn: Database connection
        items: List of (sku, quantity) tuples or dict with 'sku' and 'quantity'
    
    Returns:
        list: List of inserted SKUs
    """
    cur = conn.cursor()
    inserted = []
    
    for item in items:
        if isinstance(item, tuple):
            sku, quantity = item
        else:
            sku = item["sku"]
            quantity = item["quantity"]
        
        cur.execute(
            "INSERT OR REPLACE INTO inventory (sku, quantity) VALUES (?, ?)",
            (sku, quantity)
        )
        inserted.append(sku)
    
    conn.commit()
    return inserted

