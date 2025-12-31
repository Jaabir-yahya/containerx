"""
UCOS State Derivation Service
Derives all state from event replay - NO direct state storage
"""
import json
from datetime import datetime
from core.storage.db import get_db

class StateDerivationService:
    """
    Derives entity state from event replay.
    
    UCOS Principle: State is NEVER stored directly.
    State is ALWAYS derived by replaying events in chronological order.
    """

    def get_commitment_state(self, commitment_id):
        """
        Derive commitment state from events.
        
        Returns state dict or None if commitment doesn't exist.
        """
        events = self._get_events_for_entity('commitment', commitment_id)
        
        if not events:
            return None
        
        # Replay events in chronological order
        state = {'status': 'non_existent', 'events_applied': 0}
        
        for event in sorted(events, key=lambda e: e['created_at']):
            state = self._apply_event(state, event)
            state['events_applied'] += 1
        
        return state

    def _apply_event(self, current_state, event):
        """Pure function: event + state → new state"""
        event_type = event['action']
        event_data = json.loads(event['metadata']) if isinstance(event.get('metadata'), str) else event.get('metadata', {})
        
        handlers = {
            'COMMITMENT_CREATED': self._handle_created,
            'STATE_CHANGED_pending_TO_accepted': self._handle_accepted,
            'STATE_CHANGED_pending_TO_fulfilled': self._handle_fulfilled,
            'STATE_CHANGED_accepted_TO_fulfilled': self._handle_fulfilled,
            'STATE_CHANGED_pending_TO_expired': self._handle_expired,
            'STATE_CHANGED_accepted_TO_expired': self._handle_expired,
            'STATE_CHANGED_pending_TO_refunded': self._handle_refunded,
            'STATE_CHANGED_accepted_TO_refunded': self._handle_refunded,
            'COMMITMENT_FULFILLED': self._handle_fulfilled,
            'COMMITMENT_EXPIRED': self._handle_expired,
            'COMMITMENT_REFUNDED': self._handle_refunded,
            'AUTO_REFUND_TRIGGERED': self._handle_refunded,
        }
        
        handler = handlers.get(event_type)
        if handler:
            return handler(current_state, event_data)
        
        # Unknown event type - return state unchanged
        return current_state

    def _handle_created(self, state, data):
        """Handle COMMITMENT_CREATED event"""
        return {
            'status': 'pending',
            'id': data.get('commitment_id') or data.get('id'),
            'actor_id': data.get('actor_id'),
            'promise': data.get('promise'),
            'value': data.get('value'),
            'due_by': data.get('due_by'),
            'created_at': data.get('created_at'),
            'metadata': data.get('metadata', {}),
            'events_applied': state.get('events_applied', 0)
        }

    def _handle_accepted(self, state, data):
        """Handle state transition to accepted"""
        return {
            **state,
            'status': 'accepted',
            'accepted_at': data.get('created_at') or data.get('timestamp'),
            'accepted_by': data.get('actor_id')
        }

    def _handle_fulfilled(self, state, data):
        """Handle state transition to fulfilled"""
        return {
            **state,
            'status': 'fulfilled',
            'fulfilled_at': data.get('created_at') or data.get('timestamp'),
            'evidence': data.get('evidence')
        }

    def _handle_expired(self, state, data):
        """Handle state transition to expired"""
        return {
            **state,
            'status': 'expired',
            'expired_at': data.get('created_at') or data.get('timestamp')
        }

    def _handle_refunded(self, state, data):
        """Handle state transition to refunded"""
        return {
            **state,
            'status': 'refunded',
            'refunded_at': data.get('created_at') or data.get('timestamp'),
            'refund_reason': data.get('reason') or data.get('refund_reason')
        }

    def _get_events_for_entity(self, entity_type, entity_id):
        """Get all events for an entity"""
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, entity_type, entity_id, action, metadata, created_at, source, actor_id, correlation_id
            FROM event_log
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY created_at ASC
        """, (entity_type, entity_id))
        
        results = cur.fetchall()
        columns = ['id', 'entity_type', 'entity_id', 'action', 'metadata', 'created_at', 'source', 'actor_id', 'correlation_id']
        
        return [dict(zip(columns, row)) for row in results]

    def get_commitment_list(self, actor_id=None, status_filter=None, limit=50):
        """
        Get list of commitments by replaying events.
        
        Note: This is expensive for large datasets. In production,
        use projections/cache updated asynchronously.
        """
        conn = get_db()
        cur = conn.cursor()
        
        # Get all commitment creation events
        query = """
            SELECT DISTINCT entity_id
            FROM event_log
            WHERE entity_type = 'commitment' AND action = 'COMMITMENT_CREATED'
        """
        params = []
        
        if actor_id:
            query += " AND actor_id = ?"
            params.append(actor_id)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cur.execute(query, params)
        commitment_ids = [row[0] for row in cur.fetchall()]
        
        # Derive state for each
        commitments = []
        for commitment_id in commitment_ids:
            state = self.get_commitment_state(commitment_id)
            if state:
                if not status_filter or state.get('status') == status_filter:
                    commitments.append(state)
        
        return commitments

# Global instance
state_derivation = StateDerivationService()

