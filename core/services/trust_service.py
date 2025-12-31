from core.storage.db import get_db
from core.models.trust_event import TrustEvent
from core.services.audit_service import log_event
from datetime import datetime
import json

class TrustService:
    """UCOS Trust Service - mathematical reputation calculation"""

    DECAY_RATE = 0.95  # Events lose 5% value per month
    MIN_TRUST = 0.05
    MAX_TRUST = 0.95

    def calculate(self, actor_id):
        """
        Calculate trust score for an actor using time-decayed events

        Returns 0.0-1.0 trust score
        """
        conn = get_db()
        cur = conn.cursor()

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
        now = datetime.now()

        for delta, reason, created_at_str, expires_at_str in events:
            # Skip expired events
            if expires_at_str and datetime.fromisoformat(expires_at_str) < now:
                continue

            event_time = datetime.fromisoformat(created_at_str)

            # Calculate months since event
            months_old = (now - event_time).days / 30.0

            # Apply exponential decay (newer events matter more)
            decay_factor = self.DECAY_RATE ** months_old
            effective_delta = delta * decay_factor

            score += effective_delta

        # Bound the score
        score = max(self.MIN_TRUST, min(self.MAX_TRUST, score))

        return round(score, 3)  # Round to 3 decimal places

    def apply_delta(self, actor_id, delta, reason, commitment_id=None):
        """
        Apply a trust delta and record the event

        Args:
            actor_id: Actor whose trust changes
            delta: Trust change (-0.3 to +0.3)
            reason: Reason for the change
            commitment_id: Related commitment (optional)
        """
        # Bound the delta
        delta = max(-0.3, min(0.3, delta))

        trust_event = TrustEvent(
            actor_id=actor_id,
            delta=delta,
            reason=reason,
            commitment_id=commitment_id
        )

        # Save to database
        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO trust_events
                (id, actor_id, delta, reason, commitment_id, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                trust_event.id,
                trust_event.actor_id,
                trust_event.delta,
                trust_event.reason,
                trust_event.commitment_id,
                trust_event.expires_at,
                trust_event.created_at
            ))

            conn.commit()

            # Recalculate and cache trust score
            new_trust = self.calculate(actor_id)

            # Emit event
            log_event(
                entity_type='trust',
                entity_id=trust_event.id,
                action='TRUST_DELTA_APPLIED',
                metadata={
                    'actor_id': actor_id,
                    'delta': delta,
                    'reason': reason,
                    'commitment_id': commitment_id,
                    'new_trust_score': new_trust,
                    'source': 'system'
                }
            )

            return new_trust

        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to apply trust delta: {str(e)}")

    def get_trust_history(self, actor_id, limit=20):
        """Get trust event history for an actor"""
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, actor_id, delta, reason, commitment_id, expires_at, created_at
            FROM trust_events
            WHERE actor_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (actor_id, limit))

        results = cur.fetchall()
        columns = ['id', 'actor_id', 'delta', 'reason', 'commitment_id', 'expires_at', 'created_at']

        return [TrustEvent.from_dict(dict(zip(columns, result))) for result in results]

    def get_trust_stats(self, actor_id):
        """Get trust statistics for an actor"""
        conn = get_db()
        cur = conn.cursor()

        # Get event counts by type
        cur.execute("""
            SELECT reason, COUNT(*), AVG(delta)
            FROM trust_events
            WHERE actor_id = ?
            GROUP BY reason
        """, (actor_id,))

        event_stats = cur.fetchall()

        current_trust = self.calculate(actor_id)
        history = self.get_trust_history(actor_id, limit=10)

        return {
            'current_trust': current_trust,
            'event_count': len(history),
            'event_stats': {
                reason: {'count': count, 'avg_delta': round(avg_delta, 3)}
                for reason, count, avg_delta in event_stats
            },
            'recent_events': [
                {
                    'reason': event.reason,
                    'delta': event.delta,
                    'created_at': event.created_at
                }
                for event in history[:5]  # Last 5 events
            ]
        }

# Global instance
trust_service = TrustService()
