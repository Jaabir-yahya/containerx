from datetime import datetime
import uuid

class TrustEvent:
    """UCOS Trust Event - mathematical reputation delta"""

    def __init__(self, actor_id, delta, reason, commitment_id=None, expires_at=None, created_at=None):
        self.id = f"TRUST_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        self.actor_id = actor_id
        self.delta = delta  # -0.3 to +0.3
        self.reason = reason
        self.commitment_id = commitment_id
        self.expires_at = expires_at  # For time-decay calculation
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            'id': self.id,
            'actor_id': self.actor_id,
            'delta': self.delta,
            'reason': self.reason,
            'commitment_id': self.commitment_id,
            'expires_at': self.expires_at,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        """Create TrustEvent from dict (for database loading)"""
        return cls(
            actor_id=data['actor_id'],
            delta=data['delta'],
            reason=data['reason'],
            commitment_id=data.get('commitment_id'),
            expires_at=data.get('expires_at'),
            created_at=data['created_at']
        )

    def is_expired(self):
        """Check if trust event should be excluded from calculations"""
        if not self.expires_at:
            return False
        return datetime.fromisoformat(self.expires_at) < datetime.utcnow()

    @staticmethod
    def get_delta_for_reason(reason):
        """Get standard delta values for common reasons"""
        deltas = {
            'on_time_fulfillment': 0.02,
            'late_fulfillment': -0.01,
            'very_late_fulfillment': -0.05,
            'auto_refund_triggered': -0.10,
            'customer_dispute_lost': -0.15,
            'customer_dispute_won': 0.05,
            'repeat_customer': 0.01,
            'bulk_order_fulfilled': 0.03,
            'subscription_renewal': 0.02,
            'positive_review': 0.01,
            'negative_review': -0.02,
        }
        return deltas.get(reason, 0)
