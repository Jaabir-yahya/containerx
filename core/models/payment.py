from datetime import datetime

class Payment:
    def __init__(self, id, order_id, amount, method, status="RECEIVED", reference=None, created_at=None):
        self.id = id
        self.order_id = order_id
        self.amount = amount
        self.method = method
        self.status = status
        self.reference = reference
        self.created_at = created_at or datetime.utcnow().isoformat()