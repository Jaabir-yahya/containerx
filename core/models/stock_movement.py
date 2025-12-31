from datetime import datetime

class StockMovement:
    def __init__(self, id, sku, quantity_change, reason, related_order_id=None, created_at=None):
        self.id = id
        self.sku = sku
        self.quantity_change = quantity_change
        self.reason = reason
        self.related_order_id = related_order_id
        self.created_at = created_at or datetime.utcnow().isoformat()

