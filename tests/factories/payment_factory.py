"""
Factory for creating test payment data.
"""

import uuid
from datetime import datetime

def create_payment_data(
    order_id,
    amount=1000.0,
    method="manual",
    status="RECEIVED",
    reference=None,
    payment_id=None
):
    """
    Create payment data dictionary.
    
    Args:
        order_id: Order ID
        amount: Payment amount
        method: Payment method
        status: Payment status
        reference: Optional payment reference
        payment_id: Optional payment ID (generated if not provided)
    
    Returns:
        dict: Payment data
    """
    return {
        "id": payment_id or str(uuid.uuid4()),
        "order_id": order_id,
        "amount": amount,
        "method": method,
        "status": status,
        "reference": reference,
        "created_at": datetime.utcnow().isoformat()
    }

def create_mpesa_payment_data(order_id, amount, reference=None):
    """Create M-Pesa payment data with reference."""
    return create_payment_data(
        order_id=order_id,
        amount=amount,
        method="mpesa",
        status="RECEIVED",
        reference=reference or f"MPESA{uuid.uuid4().hex[:8].upper()}"
    )

