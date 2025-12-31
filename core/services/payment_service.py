import uuid
from core.storage.db import get_db
from core.models.payment import Payment
from core.services.audit_service import log_event

def record_payment(order_id, amount, method, reference=None):
    """
    Record a payment for an order.
    
    Args:
        order_id: ID of the order
        amount: Payment amount
        method: Payment method (e.g., 'mpesa', 'cash', 'manual')
        reference: Optional payment reference (e.g., M-Pesa transaction code)
    
    Returns:
        Payment instance
    
    Raises:
        Exception: If database operation fails
    """
    payment_id = str(uuid.uuid4())
    payment = Payment(
        id=payment_id,
        order_id=order_id,
        amount=amount,
        method=method,
        status="RECEIVED",
        reference=reference
    )
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO payments 
            (id, order_id, amount, method, status, reference, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            payment.id,
            payment.order_id,
            payment.amount,
            payment.method,
            payment.status,
            payment.reference,
            payment.created_at
        ))
        
        conn.commit()
        
        # Log event for audit trail
        log_event(
            entity_type='payment',
            entity_id=payment.id,
            action='recorded',
            metadata={
                'order_id': order_id,
                'amount': amount,
                'method': method,
                'reference': reference
            }
        )
        
        return payment
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to record payment: {str(e)}")
    # Don't close thread-local connections

def get_total_paid(order_id):
    """
    Calculate the total amount paid for an order.
    
    Args:
        order_id: ID of the order
    
    Returns:
        float: Total amount paid
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE order_id = ? AND status = 'RECEIVED'
    """, (order_id,))

    result = cur.fetchone()
    return float(result[0]) if result and result[0] is not None else 0.0

