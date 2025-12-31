"""
AutoRefundEngine - UCOS Phase 2
Event-driven auto-refund system for SLA breaches.

UCOS Principle: Reacts to TIMER_FIRED events, checks commitment state,
emits AUTO_REFUND_TRIGGERED events. TrustService reacts separately to apply penalties.
No direct state storage - all state derived from events.
"""
import threading
import time
import json
import uuid
from datetime import datetime
from typing import Optional

from core.services.state_derivation_service import state_derivation


class AutoRefundEngine:
    """
    Event-driven auto-refund engine for UCOS auto-enforcement.
    
    Pattern:
    1. Reacts to TIMER_FIRED events (from TimerService)
    2. Checks commitment state (via StateDerivationService)
    3. If commitment is still pending, emits AUTO_REFUND_TRIGGERED event
    4. TrustService reacts to AUTO_REFUND_TRIGGERED separately to apply penalty
    
    UCOS: No direct state storage - all state derived from events.
    """
    
    def __init__(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_timer_events, daemon=True)
        self.thread.start()
    
    def _get_thread_db(self):
        """
        Get database connection for background thread.
        
        SQLite connections are thread-local, so background thread
        needs its own connection. This method creates a new connection
        that can be used safely in the background thread.
        
        If a database override is set (e.g., in tests), uses the stored
        database path to create a new connection to the same file.
        """
        import sqlite3
        from core.storage.db import DB_NAME, _db_override_path
        
        # If there's a database override path (for tests), use it
        if _db_override_path and _db_override_path != "":
            db_path = _db_override_path
        else:
            db_path = DB_NAME
        
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=1000")
        return conn
    
    def _monitor_timer_events(self):
        """
        Background thread to monitor for TIMER_FIRED events
        and trigger auto-refunds for SLA breaches.
        """
        while self.running:
            try:
                self._check_timer_fired_events()
                time.sleep(1)  # Check every second
            except Exception as e:
                print(f"AutoRefundEngine error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _check_timer_fired_events(self):
        """
        Check for TIMER_FIRED events that haven't been processed yet.
        
        UCOS Pattern: Query event_log for TIMER_FIRED events,
        check if auto-refund already triggered, process if not.
        """
        conn = self._get_thread_db()
        cur = conn.cursor()
        
        try:
            # Find TIMER_FIRED events for SLA acceptance breaches
            # that haven't been processed (no AUTO_REFUND_TRIGGERED event exists)
            cur.execute("""
                SELECT e1.entity_id, e1.metadata, e1.created_at
                FROM event_log e1
                WHERE e1.action = 'TIMER_FIRED'
                  AND e1.entity_type = 'timer'
                  AND json_extract(e1.metadata, '$.timer_type') = 'sla_acceptance'
                  AND e1.entity_id NOT IN (
                      SELECT json_extract(e2.metadata, '$.timer_event_id')
                      FROM event_log e2
                      WHERE e2.action = 'AUTO_REFUND_TRIGGERED'
                        AND json_extract(e2.metadata, '$.timer_event_id') IS NOT NULL
                  )
                ORDER BY e1.created_at DESC
                LIMIT 10
            """)
            
            for row in cur.fetchall():
                timer_event_id = row[0]
                metadata_str = row[1]
                created_at_str = row[2]
                
                try:
                    metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                    commitment_id = metadata.get('commitment_id')
                    
                    if commitment_id:
                        # Process this timer event
                        self._process_timer_fired(commitment_id, timer_event_id, metadata)
                except Exception as e:
                    print(f"Error processing timer event {timer_event_id}: {e}")
        finally:
            conn.close()
    
    def _process_timer_fired(self, commitment_id: str, timer_event_id: str, timer_metadata: dict):
        """
        Process a TIMER_FIRED event and trigger auto-refund if needed.
        
        UCOS Pattern: Check commitment state, emit AUTO_REFUND_TRIGGERED if pending.
        """
        # Derive current commitment state from events using thread-safe method
        state = self._get_commitment_state_thread_safe(commitment_id)
        
        if not state:
            # Commitment doesn't exist - skip
            return
        
        # Only trigger auto-refund if commitment is still pending
        # If already fulfilled, accepted, or refunded, skip
        if state['status'] not in ('pending', 'accepted'):
            # Commitment already resolved - no auto-refund needed
            return
        
        # Trigger auto-refund
        self._trigger_auto_refund(commitment_id, timer_event_id, state, timer_metadata)
    
    def _get_commitment_state_thread_safe(self, commitment_id: str):
        """
        Get commitment state using thread-local database connection.
        
        This is a thread-safe version of state_derivation.get_commitment_state()
        that can be called from background threads.
        """
        conn = self._get_thread_db()
        cur = conn.cursor()
        
        try:
            # Get all events for this commitment
            cur.execute("""
                SELECT id, entity_type, entity_id, action, metadata, created_at, source, actor_id, correlation_id
                FROM event_log
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY created_at ASC
            """, ('commitment', commitment_id))
            
            results = cur.fetchall()
            if not results:
                return None
            
            columns = ['id', 'entity_type', 'entity_id', 'action', 'metadata', 'created_at', 'source', 'actor_id', 'correlation_id']
            events = [dict(zip(columns, row)) for row in results]
            
            # Replay events in chronological order
            state = {'status': 'non_existent', 'events_applied': 0}
            
            for event in sorted(events, key=lambda e: e['created_at']):
                state = self._apply_event(state, event)
                state['events_applied'] += 1
            
            return state
        finally:
            conn.close()
    
    def _apply_event(self, current_state, event):
        """Pure function: event + state → new state (thread-safe version)"""
        import json
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
        
        return current_state
    
    def _handle_created(self, state, data):
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
        return {
            **state,
            'status': 'accepted',
            'accepted_at': data.get('created_at') or data.get('timestamp'),
            'accepted_by': data.get('actor_id')
        }
    
    def _handle_fulfilled(self, state, data):
        return {
            **state,
            'status': 'fulfilled',
            'fulfilled_at': data.get('created_at') or data.get('timestamp'),
            'evidence': data.get('evidence')
        }
    
    def _handle_expired(self, state, data):
        return {
            **state,
            'status': 'expired',
            'expired_at': data.get('created_at') or data.get('timestamp')
        }
    
    def _handle_refunded(self, state, data):
        return {
            **state,
            'status': 'refunded',
            'refunded_at': data.get('created_at') or data.get('timestamp'),
            'refund_reason': data.get('reason') or data.get('refund_reason')
        }
    
    def _trigger_auto_refund(self, commitment_id: str, timer_event_id: str, 
                            state: dict, timer_metadata: dict):
        """
        Trigger auto-refund for SLA breach.
        
        UCOS Pattern: Emit AUTO_REFUND_TRIGGERED event only.
        TrustService will react to this event separately.
        """
        actor_id = state.get('actor_id')
        value = state.get('value', 0.0)
        timer_type = timer_metadata.get('timer_type', 'sla_acceptance')
        fires_at = timer_metadata.get('fires_at')
        
        # Determine refund reason based on timer type
        reason_map = {
            'sla_acceptance': 'sla_acceptance_breach',
            'sla_fulfillment': 'sla_fulfillment_breach'
        }
        reason = reason_map.get(timer_type, 'sla_breach')
        
        # Emit AUTO_REFUND_TRIGGERED event (UCOS pattern)
        self._log_event_thread_safe(
            entity_type='commitment',
            entity_id=commitment_id,
            action='AUTO_REFUND_TRIGGERED',
            metadata={
                'commitment_id': commitment_id,
                'reason': reason,
                'actor_id': actor_id,
                'amount': value,
                'timer_event_id': timer_event_id,
                'timer_type': timer_type,
                'fires_at': fires_at,
                'triggered_at': datetime.utcnow().isoformat()
            },
            source='system',
            actor_id=actor_id
        )
        
        # Also emit state change to 'refunded'
        # (StateDerivationService will handle this)
        self._log_event_thread_safe(
            entity_type='commitment',
            entity_id=commitment_id,
            action='STATE_CHANGED_pending_TO_refunded',
            metadata={
                'commitment_id': commitment_id,
                'old_state': state.get('status', 'pending'),
                'new_state': 'refunded',
                'reason': reason,
                'actor_id': actor_id,
                'timestamp': datetime.utcnow().isoformat()
            },
            source='system',
            actor_id=actor_id
        )
        
        # TrustService will react to AUTO_REFUND_TRIGGERED event separately
        # (via event handler pattern)
    
    def _log_event_thread_safe(self, entity_type, entity_id, action, metadata=None, source="system", actor_id=None):
        """
        Thread-safe event logging for background threads.
        
        This is a version of log_event() that uses a thread-local
        database connection, safe for use from background threads.
        """
        event_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata) if isinstance(metadata, dict) else str(metadata) if metadata else "{}"
        created_at = datetime.utcnow().isoformat()
        
        conn = self._get_thread_db()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO event_log (id, entity_type, entity_id, action, metadata, created_at, source, actor_id, correlation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                entity_type,
                entity_id,
                action,
                metadata_json,
                created_at,
                source,
                actor_id,
                None  # correlation_id
            ))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to log event: {str(e)}")
        finally:
            conn.close()
    
    def stop(self):
        """Stop the auto-refund engine."""
        self.running = False


# Global instance
auto_refund_engine = AutoRefundEngine()

