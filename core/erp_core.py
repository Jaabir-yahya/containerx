"""
ERP Core Orchestrator

High-level orchestration functions that coordinate services.
No SQL, no business logic - just orchestration.
"""

from core.services.sales_service import process_retail_sale, apply_payment_to_order
from core.services.inventory_service import verify_stock, adjust_inventory
from core.services.payment_service import record_payment, get_total_paid
from core.services.audit_service import log_event

def create_retail_sale(customer_identifier, items, payment_amount, payment_method="manual", payment_reference=None):
    """
    Create a retail sale.
    
    Orchestrates the retail sale process through the sales service.
    
    Args:
        customer_identifier: Customer identifier
        items: List of dicts with 'sku', 'qty', 'price'
        payment_amount: Amount paid
        payment_method: Payment method (default: 'manual')
        payment_reference: Optional payment reference
    
    Returns:
        str: Order ID
    """
    return process_retail_sale(
        customer_identifier=customer_identifier,
        items=items,
        payment_amount=payment_amount,
        payment_method=payment_method,
        payment_reference=payment_reference
    )

def complete_partial_payment(order_id, payment_amount, method="manual", reference=None):
    """
    Apply additional payment to a partially paid order.
    
    Orchestrates payment application through the sales service.
    
    Args:
        order_id: ID of the order
        payment_amount: Amount to apply
        method: Payment method (default: 'manual')
        reference: Optional payment reference
    
    Returns:
        dict: Status update with order_id, status, total_paid, order_total
    """
    return apply_payment_to_order(
        order_id=order_id,
        payment_amount=payment_amount,
        method=method,
        reference=reference
    )

def check_inventory(sku, required_quantity):
    """
    Check if sufficient inventory is available.
    
    Args:
        sku: Stock keeping unit
        required_quantity: Quantity required
    
    Returns:
        bool: True if sufficient stock available
    
    Raises:
        ValueError: If SKU not found or insufficient stock
    """
    return verify_stock(sku, required_quantity)

def get_order_payment_status(order_id):
    """
    Get payment status for an order.
    
    Args:
        order_id: ID of the order
    
    Returns:
        dict: Payment status information
    """
    from core.storage.db import get_db
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT total_amount, status FROM orders WHERE id = ?
        """, (order_id,))
        
        result = cur.fetchone()
        if not result:
            return None
        
        total_amount, status = result
        total_paid = get_total_paid(order_id)
        
        return {
            'order_id': order_id,
            'order_total': total_amount,
            'total_paid': total_paid,
            'remaining': total_amount - total_paid,
            'status': status,
            'is_fully_paid': total_paid >= total_amount
        }
    finally:
        conn.close()

