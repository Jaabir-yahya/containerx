"""
Factory for creating test order data.
"""

import uuid
from datetime import datetime

def create_order_data(
    customer_identifier="TEST_CUSTOMER",
    total_amount=1000.0,
    status="CREATED",
    order_id=None
):
    """
    Create order data dictionary.
    
    Args:
        customer_identifier: Customer identifier
        total_amount: Total order amount
        status: Order status
        order_id: Optional order ID (generated if not provided)
    
    Returns:
        dict: Order data
    """
    return {
        "id": order_id or str(uuid.uuid4()),
        "customer_identifier": customer_identifier,
        "total_amount": total_amount,
        "status": status,
        "created_at": datetime.utcnow().isoformat()
    }

def create_order_items_data(skus_and_quantities, base_price=100.0):
    """
    Create order items data from SKU/quantity pairs.
    
    Args:
        skus_and_quantities: List of (sku, quantity) tuples or dict with 'sku' and 'qty'
        base_price: Base price per item (or dict mapping SKU to price)
    
    Returns:
        list: List of item dicts with 'sku', 'qty', 'price'
    
    Example:
        create_order_items_data([("MILK001", 2), ("BREAD001", 1)])
        create_order_items_data([{"sku": "MILK001", "qty": 2}])
    """
    items = []
    
    for item_data in skus_and_quantities:
        if isinstance(item_data, tuple):
            sku, qty = item_data
            price = base_price if isinstance(base_price, (int, float)) else base_price.get(sku, 100.0)
        else:
            sku = item_data["sku"]
            qty = item_data["qty"]
            price = item_data.get("price", base_price if isinstance(base_price, (int, float)) else base_price.get(sku, 100.0))
        
        items.append({
            "sku": sku,
            "qty": qty,
            "price": price
        })
    
    return items

