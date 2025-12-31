from datetime import datetime
import json

class EventLog:
    def __init__(self, id, entity_type, entity_id, action, metadata=None, created_at=None,
                 source="system", actor_id=None, correlation_id=None):
        self.id = id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.action = action
        self.metadata = metadata if metadata is not None else {}
        self.created_at = created_at or datetime.utcnow().isoformat()
        # UCOS extensions
        self.source = source          # system, whatsapp, web, api
        self.actor_id = actor_id      # who triggered the event
        self.correlation_id = correlation_id  # for tracing chains

    # UCOS event types (additive to existing)
    UCOS_EVENTS = [
        'COMMITMENT_CREATED',
        'COMMITMENT_ACCEPTED',
        'COMMITMENT_FULFILLED',
        'COMMITMENT_EXPIRED',
        'COMMITMENT_REFUNDED',
        'TRUST_DELTA_APPLIED',
        'TIMER_SCHEDULED',
        'TIMER_FIRED',
        'AUTO_REFUND_TRIGGERED',
        'CREDIT_PACKAGE_PURCHASED',
        'CREDITS_CONSUMED'
    ]
    
    def to_dict(self):
        return {
            'id': self.id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'action': self.action,
            'metadata': json.dumps(self.metadata) if isinstance(self.metadata, dict) else self.metadata,
            'created_at': self.created_at,
            'source': self.source,
            'actor_id': self.actor_id,
            'correlation_id': self.correlation_id
        }

