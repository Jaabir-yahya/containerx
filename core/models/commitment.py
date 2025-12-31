from datetime import datetime
import uuid
import json

class Commitment:
    """UCOS Commitment primitive - represents a promise with deadline and auto-enforcement"""

    def __init__(self, id, actor_id, promise, value, due_by, state="pending",
                 metadata=None, created_at=None):
        self.id = id or f"COMMIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        self.actor_id = actor_id
        self.promise = promise
        self.value = value
        self.due_by = due_by
        self.state = state
        self.metadata = metadata or {
            'type': 'order',      # order/subscription/reservation
            'sla_hours': 24,      # Service Level Agreement
            'auto_refund': True,  # Auto-refund on SLA breach
            'trust_impact': 0.2   # Trust delta for outcome
        }
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            'id': self.id,
            'actor_id': self.actor_id,
            'promise': self.promise,
            'value': self.value,
            'due_by': self.due_by,
            'state': self.state,
            'metadata': json.dumps(self.metadata) if isinstance(self.metadata, dict) else self.metadata,
            'created_at': self.created_at
        }

    @classmethod
    def from_dict(cls, data):
        """Create Commitment from dict (for database loading)"""
        metadata = json.loads(data['metadata']) if isinstance(data.get('metadata'), str) else data.get('metadata', {})
        return cls(
            id=data['id'],
            actor_id=data['actor_id'],
            promise=data['promise'],
            value=data['value'],
            due_by=data['due_by'],
            state=data['state'],
            metadata=metadata,
            created_at=data['created_at']
        )

    def is_expired(self):
        """Check if commitment is past due date"""
        return datetime.fromisoformat(self.due_by) < datetime.utcnow()

    def calculate_sla_hours(self):
        """Calculate SLA hours based on metadata"""
        return self.metadata.get('sla_hours', 24)

    def should_auto_refund(self):
        """Check if auto-refund is enabled"""
        return self.metadata.get('auto_refund', True)

    def get_trust_impact(self):
        """Get trust delta for successful completion"""
        return self.metadata.get('trust_impact', 0.2)
