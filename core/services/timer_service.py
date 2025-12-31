"""
TimerService - UCOS Phase 2
Event-driven timer scheduling for auto-enforcement.

UCOS Principle: Reacts to COMMITMENT_CREATED events, schedules SLA timers,
emits TIMER_SCHEDULED and TIMER_FIRED events. No direct state storage.
"""
import threading
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from core.services.audit_service import log_event
from core.services.state_derivation_service import state_derivation
from core.services.trust_service import trust_service
import uuid


class TimerService:
    """
    Event-driven timer service for UCOS auto-enforcement.
    
    Pattern:
    1. Reacts to COMMITMENT_CREATED events
    2. Schedules timers based on SLA (from trust scores)
    3. Emits TIMER_SCHEDULED events
    4. Fires timers and emits TIMER_FIRED events
    5. AutoRefundEngine reacts to TIMER_FIRED events
    
    UCOS: No direct state storage - all state derived from events.
    """
    
    def __init__(self):
        self.timers: Dict[str, threading.Timer] = {}
        self.running = True
        self.thread = threading.Thread(target=self._monitor_events, daemon=True)
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
        # This allows background threads to connect to the test database
        if _db_override_path and _db_override_path != "":
            db_path = _db_override_path
        else:
            db_path = DB_NAME
        
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=1000")
        return conn
    
    def _log_event_thread_safe(self, entity_type, entity_id, action, metadata=None, source="system", actor_id=None):
        """
        Thread-safe event logging for background threads.
        
        This is a version of log_event() that uses a thread-local
        database connection, safe for use from background threads.
        """
        from datetime import datetime
        
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
    
    def _monitor_events(self):
        """
        Background thread to monitor for COMMITMENT_CREATED events
        and check for expired timers.
        """
        while self.running:
            try:
                self._check_new_commitments()
                self._check_expired_timers()
                time.sleep(1)  # Check every second
            except Exception as e:
                print(f"TimerService error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _check_new_commitments(self):
        """
        Check for new COMMITMENT_CREATED events to schedule timers.
        
        UCOS Pattern: Query event_log for COMMITMENT_CREATED events,
        check if timer already scheduled, schedule if not.
        """
        conn = self._get_thread_db()
        cur = conn.cursor()
        
        try:
            # Find recent COMMITMENT_CREATED events without timers
            # Check if timer exists by looking for TIMER_SCHEDULED events
            cur.execute("""
                SELECT e1.entity_id, e1.metadata, e1.created_at, e1.actor_id
                FROM event_log e1
                WHERE e1.action = 'COMMITMENT_CREATED'
                  AND e1.entity_id NOT IN (
                      SELECT json_extract(e2.metadata, '$.commitment_id')
                      FROM event_log e2
                      WHERE e2.action = 'TIMER_SCHEDULED'
                        AND json_extract(e2.metadata, '$.commitment_id') IS NOT NULL
                  )
                ORDER BY e1.created_at DESC
                LIMIT 10
            """)
            
            for row in cur.fetchall():
                commitment_id = row[0]
                metadata_str = row[1]
                created_at_str = row[2]
                actor_id = row[3]
                
                try:
                    metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                    
                    # Schedule SLA timer
                    self._schedule_sla_timer(commitment_id, metadata, actor_id, created_at_str)
                except Exception as e:
                    print(f"Error scheduling timer for {commitment_id}: {e}")
        finally:
            conn.close()
    
    def _schedule_sla_timer(self, commitment_id: str, metadata: dict, actor_id: Optional[str], created_at_str: str):
        """
        Schedule SLA timer based on commitment metadata and trust score.
        
        UCOS Pattern: Calculate SLA from trust score, schedule timer,
        emit TIMER_SCHEDULED event, save to database.
        """
        # Get trust score for SLA calculation
        # Note: We calculate trust in this thread to avoid threading issues
        if actor_id:
            # Calculate trust using thread-local connection
            trust_score = self._calculate_trust_score(actor_id)
        else:
            trust_score = 0.5  # Default neutral trust
        
        # Calculate SLA hours based on trust score
        sla_hours = self._calculate_sla_hours(trust_score)
        
        # Get SLA from metadata if provided, otherwise use calculated
        metadata_sla = metadata.get('metadata', {}).get('sla_hours') if isinstance(metadata.get('metadata'), dict) else None
        if metadata_sla:
            sla_hours = metadata_sla
        
        # Calculate fire time
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00') if 'Z' in created_at_str else created_at_str)
        except:
            created_at = datetime.utcnow()
        
        fire_time = created_at + timedelta(hours=sla_hours)
        
        # Only schedule if fire time is in the future
        now = datetime.utcnow()
        if fire_time <= now:
            # Timer should have already fired - emit TIMER_FIRED immediately
            self._on_timer_fired(commitment_id, 'sla_acceptance', fire_time.isoformat())
            return
        
        # Calculate delay in seconds
        delay_seconds = (fire_time - now).total_seconds()
        
        # Generate timer ID
        timer_id = f"TIMER_{commitment_id}_{int(time.time())}"
        
        # Schedule timer using threading.Timer
        timer = threading.Timer(
            delay_seconds,
            self._on_timer_fired,
            args=[commitment_id, 'sla_acceptance', fire_time.isoformat()]
        )
        timer.daemon = True
        timer.start()
        
        # Store timer reference
        self.timers[timer_id] = timer
        
        # Save to database (for persistence across restarts)
        self._save_timer_to_db(timer_id, commitment_id, fire_time, 'sla_acceptance')
        
        # Emit TIMER_SCHEDULED event (UCOS pattern)
        # Use thread-safe logging since we're in a background thread
        self._log_event_thread_safe(
            entity_type='timer',
            entity_id=timer_id,
            action='TIMER_SCHEDULED',
            metadata={
                'commitment_id': commitment_id,
                'fires_at': fire_time.isoformat(),
                'sla_hours': sla_hours,
                'timer_type': 'sla_acceptance',
                'trust_score': trust_score,
                'actor_id': actor_id
            },
            source='system',
            actor_id=actor_id
        )
    
    def _on_timer_fired(self, commitment_id: str, timer_type: str, fires_at: str):
        """
        Called when timer fires. Emits TIMER_FIRED event.
        
        UCOS Pattern: Emit event only. AutoRefundEngine will react to this event.
        """
        # Generate fired event ID
        fired_event_id = f"FIRED_{commitment_id}_{int(time.time())}"
        
        # Emit TIMER_FIRED event (UCOS pattern)
        # Use thread-safe logging since we're in a background/timer thread
        self._log_event_thread_safe(
            entity_type='timer',
            entity_id=fired_event_id,
            action='TIMER_FIRED',
            metadata={
                'commitment_id': commitment_id,
                'timer_type': timer_type,
                'fires_at': fires_at,
                'fired_at': datetime.utcnow().isoformat()
            },
            source='system'
        )
        
        # Update timer status in database
        # Note: This is called from timer thread, so needs thread-local connection
        conn = self._get_thread_db()
        cur = conn.cursor()
        
        try:
            # Find the timer for this commitment
            cur.execute("""
                SELECT id FROM timers 
                WHERE commitment_id = ? AND status = 'scheduled'
                ORDER BY created_at DESC
                LIMIT 1
            """, (commitment_id,))
            
            timer_row = cur.fetchone()
            if timer_row:
                timer_id = timer_row[0]
                cur.execute("""
                    UPDATE timers SET status = 'fired' WHERE id = ?
                """, (timer_id,))
                conn.commit()
        finally:
            conn.close()
        
        # Remove from active timers dict
        timer_to_remove = None
        for tid, timer in self.timers.items():
            if commitment_id in tid:
                timer_to_remove = tid
                break
        if timer_to_remove:
            del self.timers[timer_to_remove]
        
        # AutoRefundEngine will react to TIMER_FIRED event separately
    
    def _calculate_trust_score(self, actor_id: str) -> float:
        """
        Calculate trust score for an actor using thread-local database connection.
        
        This is a thread-safe version of trust_service.calculate() that can be
        called from background threads.
        """
        from datetime import datetime
        import json
        
        conn = self._get_thread_db()
        cur = conn.cursor()
        
        try:
            # Get all trust events for actor, ordered by creation time
            cur.execute("""
                SELECT delta, reason, created_at, expires_at
                FROM trust_events
                WHERE actor_id = ?
                ORDER BY created_at ASC
            """, (actor_id,))
            
            events = cur.fetchall()
            if not events:
                return 0.5  # Neutral starting trust
            
            score = 0.5  # Start at neutral
            now = datetime.utcnow()
            DECAY_RATE = 0.95  # Events lose 5% value per month
            MIN_TRUST = 0.05
            MAX_TRUST = 0.95
            
            for delta, reason, created_at_str, expires_at_str in events:
                # Skip expired events
                if expires_at_str:
                    try:
                        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00') if 'Z' in expires_at_str else expires_at_str)
                        if expires_at < now:
                            continue
                    except:
                        pass
                
                try:
                    event_time = datetime.fromisoformat(created_at_str.replace('Z', '+00:00') if 'Z' in created_at_str else created_at_str)
                except:
                    continue
                
                # Calculate months since event
                months_old = (now - event_time).days / 30.0
                
                # Apply exponential decay (newer events matter more)
                decay_factor = DECAY_RATE ** months_old
                effective_delta = delta * decay_factor
                
                score += effective_delta
            
            # Bound the score
            score = max(MIN_TRUST, min(MAX_TRUST, score))
            
            return round(score, 3)  # Round to 3 decimal places
        finally:
            conn.close()
    
    def _calculate_sla_hours(self, trust_score: float) -> int:
        """
        Calculate SLA hours based on trust score.
        
        Higher trust = shorter SLA (faster expected delivery).
        Lower trust = longer SLA (more time allowed).
        
        Formula: base_sla - (trust_score - 0.5) * reduction_factor
        """
        base_sla = 24  # Default 24 hours
        max_reduction = 12  # Maximum reduction for high trust
        reduction = max_reduction * (trust_score - 0.5) * 2
        
        # Bound between 1 and 48 hours
        sla_hours = max(1, min(48, base_sla - reduction))
        return int(sla_hours)
    
    def _save_timer_to_db(self, timer_id: str, commitment_id: str, 
                         fires_at: datetime, timer_type: str):
        """
        Save timer to database for persistence.
        
        UCOS Note: This is for persistence only, not source of truth.
        Source of truth is TIMER_SCHEDULED event in event_log.
        """
        conn = self._get_thread_db()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO timers (id, commitment_id, type, fires_at, action, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                timer_id,
                commitment_id,
                timer_type,
                fires_at.isoformat(),
                'auto_refund',  # Action to take when timer fires
                'scheduled',
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error saving timer to database: {e}")
        finally:
            conn.close()
    
    def _check_expired_timers(self):
        """
        Check and fire timers that should have fired while offline.
        
        UCOS Pattern: Query database for scheduled timers past fire time,
        emit TIMER_FIRED events for them.
        """
        conn = self._get_thread_db()
        cur = conn.cursor()
        
        try:
            now = datetime.utcnow()
            
            cur.execute("""
                SELECT id, commitment_id, type, fires_at 
                FROM timers 
                WHERE status = 'scheduled' 
                  AND fires_at < ?
            """, (now.isoformat(),))
            
            for row in cur.fetchall():
                timer_id, commitment_id, timer_type, fires_at_str = row
                
                try:
                    # Fire the timer (emits TIMER_FIRED event)
                    self._on_timer_fired(commitment_id, timer_type, fires_at_str)
                except Exception as e:
                    print(f"Error firing expired timer {timer_id}: {e}")
        finally:
            conn.close()
    
    def stop(self):
        """Stop the timer service and cancel all active timers."""
        self.running = False
        for timer in self.timers.values():
            timer.cancel()
        self.timers.clear()


# Global instance
timer_service = TimerService()

