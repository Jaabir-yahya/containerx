from core.storage.db import get_db
from core.services.audit_service import log_event
from core.services.state_derivation_service import state_derivation
from datetime import datetime, timedelta
import uuid
import json

class CommitmentService:
    """
    UCOS Commitment Service - Event-Emission Only
    
    UCOS Principle: Services ONLY emit events. State is derived from event replay.
    NO direct database state storage. NO commitment objects stored directly.
    """

    def emit_create_event(self, actor_id, promise, value, due_by=None, metadata=None, source="system"):
        """
        Emit COMMITMENT_CREATED event (UCOS event-driven pattern).
        
        Returns event_id, not commitment object.
        State must be derived via state_derivation.get_commitment_state()
        """
        if due_by is None:
            # Default SLA is 24 hours
            due_by = (datetime.now() + timedelta(hours=24)).isoformat()

        # Generate commitment ID
        commitment_id = f"COMMIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Default metadata if not provided
        if metadata is None:
            metadata = {
                'type': 'order',
                'sla_hours': 24,
                'auto_refund': True,
                'trust_impact': 0.2
            }

        # Emit event (ONLY action - no state storage)
        event = log_event(
            entity_type='commitment',
            entity_id=commitment_id,
            action='COMMITMENT_CREATED',
            metadata={
                'commitment_id': commitment_id,
                'actor_id': actor_id,
                'promise': promise,
                'value': value,
                'due_by': due_by,
                'metadata': metadata,
                'created_at': datetime.utcnow().isoformat()
            },
            source=source,
            actor_id=actor_id
        )

        return commitment_id

    # Backward compatibility wrapper (deprecated - use emit_create_event)
    def create(self, actor_id, promise, value, due_by=None, metadata=None):
        """DEPRECATED: Use emit_create_event() instead"""
        commitment_id = self.emit_create_event(actor_id, promise, value, due_by, metadata)
        # Return derived state for compatibility
        return self.get(commitment_id)

    def get(self, commitment_id):
        """
        Get commitment state by deriving from events.
        
        Returns state dict (not Commitment object).
        """
        state = state_derivation.get_commitment_state(commitment_id)
        
        if state is None:
            return None
        
        # Return state dict with Commitment-like interface for compatibility
        return {
            'id': commitment_id,
            'actor_id': state.get('actor_id'),
            'promise': state.get('promise'),
            'value': state.get('value'),
            'due_by': state.get('due_by'),
            'state': state.get('status'),
            'metadata': state.get('metadata', {}),
            'created_at': state.get('created_at')
        }

    def emit_state_change_event(self, commitment_id, new_state, actor_id="system", source="system"):
        """
        Emit state change event (UCOS pattern).
        
        NO direct state update. State derived from events.
        """
        # Get current state from event replay
        current_state_dict = self.get(commitment_id)
        if not current_state_dict:
            raise ValueError(f"Commitment {commitment_id} not found")

        old_state = current_state_dict.get('state', 'non_existent')

        # Emit state change event (ONLY action)
        log_event(
            entity_type='commitment',
            entity_id=commitment_id,
            action=f'STATE_CHANGED_{old_state}_TO_{new_state}',
            metadata={
                'commitment_id': commitment_id,
                'old_state': old_state,
                'new_state': new_state,
                'actor_id': actor_id,
                'timestamp': datetime.utcnow().isoformat()
            },
            source=source,
            actor_id=actor_id
        )

        return True

    def update_state(self, commitment_id, new_state, actor_id="system"):
        """Backward compatibility wrapper"""
        return self.emit_state_change_event(commitment_id, new_state, actor_id)

    def emit_fulfill_event(self, commitment_id, evidence=None, actor_id="system", source="system"):
        """
        Emit commitment fulfillment event (UCOS pattern).
        
        Trust service will react to this event separately.
        """
        commitment_state = self.get(commitment_id)
        if not commitment_state:
            raise ValueError(f"Commitment {commitment_id} not found")

        # Emit state change to fulfilled
        self.emit_state_change_event(commitment_id, 'fulfilled', actor_id, source)

        # Emit fulfillment event (trust service reacts to this)
        trust_impact = commitment_state.get('metadata', {}).get('trust_impact', 0.2)
        
        log_event(
            entity_type='commitment',
            entity_id=commitment_id,
            action='COMMITMENT_FULFILLED',
            metadata={
                'commitment_id': commitment_id,
                'evidence': evidence,
                'trust_impact': trust_impact,
                'actor_id': commitment_state.get('actor_id'),
                'timestamp': datetime.utcnow().isoformat()
            },
            source=source,
            actor_id=actor_id
        )

        # Trust service will react to COMMITMENT_FULFILLED event
        # (separate event handler - not direct call)

        return True

    def fulfill(self, commitment_id, evidence=None, actor_id="system"):
        """Backward compatibility wrapper"""
        return self.emit_fulfill_event(commitment_id, evidence, actor_id)

    def emit_expire_event(self, commitment_id, actor_id="system", source="system"):
        """
        Emit commitment expiration event (UCOS pattern).
        
        Trust service will react to this event separately.
        """
        commitment_state = self.get(commitment_id)
        if not commitment_state:
            raise ValueError(f"Commitment {commitment_id} not found")

        # Emit state change to expired
        self.emit_state_change_event(commitment_id, 'expired', actor_id, source)

        # Emit expiration event (trust service reacts to this)
        trust_penalty = -0.05  # Standard penalty for expiration
        
        log_event(
            entity_type='commitment',
            entity_id=commitment_id,
            action='COMMITMENT_EXPIRED',
            metadata={
                'commitment_id': commitment_id,
                'trust_penalty': trust_penalty,
                'actor_id': commitment_state.get('actor_id'),
                'timestamp': datetime.utcnow().isoformat()
            },
            source=source,
            actor_id=actor_id
        )

        return True

    def expire(self, commitment_id, actor_id="system"):
        """Backward compatibility wrapper"""
        return self.emit_expire_event(commitment_id, actor_id)

    def list_by_actor(self, actor_id, state=None, limit=50):
        """List commitments for an actor (derived from events)"""
        return state_derivation.get_commitment_list(
            actor_id=actor_id,
            status_filter=state,
            limit=limit
        )

    def get_expired_commitments(self):
        """Get commitments that have passed their due date (derived from events)"""
        all_commitments = state_derivation.get_commitment_list(limit=1000)
        now = datetime.now()
        
        expired = []
        for commitment in all_commitments:
            if commitment.get('status') not in ('fulfilled', 'expired', 'refunded'):
                due_by = commitment.get('due_by')
                if due_by:
                    try:
                        due_date = datetime.fromisoformat(due_by.replace('Z', '+00:00') if 'Z' in due_by else due_by)
                        if due_date < now:
                            expired.append(commitment)
                    except:
                        pass
        
        return expired

# Global instance
commitment_service = CommitmentService()
