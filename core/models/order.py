from datetime import datetime

class Order:
    def __init__(self, id, customer_identifier, total_amount, status="CREATED", created_at=None):
        self.id = id
        self.customer_identifier = customer_identifier
        self.total_amount = total_amount
        self.status = status
        self.created_at = created_at or datetime.utcnow().isoformat()