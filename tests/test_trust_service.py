"""
Unit tests for UCOS Trust Service
"""
import pytest
from datetime import datetime, timedelta
from core.services.trust_service import trust_service

class TestTrustService:
    """Test UCOS Trust Service"""

    def test_calculate_neutral_trust(self, test_setup):
        """Test trust calculation for actor with no events"""
        trust = trust_service.calculate("new_actor")

        assert trust == 0.5  # Default neutral trust

    def test_apply_positive_delta(self, test_setup):
        """Test applying positive trust delta"""
        actor_id = "test_positive"

        # Apply positive delta
        new_trust = trust_service.apply_delta(
            actor_id=actor_id,
            delta=0.1,
            reason="on_time_fulfillment"
        )

        assert new_trust == 0.6  # 0.5 + 0.1

        # Verify trust persists
        calculated_trust = trust_service.calculate(actor_id)
        assert calculated_trust == 0.6

    def test_apply_negative_delta(self, test_setup):
        """Test applying negative trust delta"""
        actor_id = "test_negative"

        # Apply negative delta
        new_trust = trust_service.apply_delta(
            actor_id=actor_id,
            delta=-0.05,
            reason="late_fulfillment"
        )

        assert new_trust == 0.45  # 0.5 - 0.05

    def test_trust_bounds(self, test_setup):
        """Test trust score bounds (0.05 to 0.95)"""
        actor_id = "test_bounds"

        # Try to go below minimum
        trust_service.apply_delta(actor_id, -2.0, "extreme_penalty")
        trust = trust_service.calculate(actor_id)
        assert trust >= 0.05

        # Try to go above maximum
        trust_service.apply_delta("test_bounds_max", 2.0, "extreme_bonus")
        trust = trust_service.calculate("test_bounds_max")
        assert trust <= 0.95

    def test_delta_bounds(self, test_setup):
        """Test that deltas are bounded (-0.3 to +0.3)"""
        actor_id = "test_delta_bounds"

        # Apply extreme delta (should be bounded)
        new_trust = trust_service.apply_delta(
            actor_id=actor_id,
            delta=1.0,  # Too high
            reason="test"
        )

        # Should only apply 0.3 max
        assert new_trust == 0.8  # 0.5 + 0.3

    def test_time_decay(self, test_setup):
        """Test that older events have less impact"""
        actor_id = "test_decay"

        # Add recent event
        trust_service.apply_delta(actor_id, 0.1, "recent_event")

        # Simulate old event by directly inserting (bypassing normal flow for test)
        from core.storage.db import get_db
        conn = get_db()
        cur = conn.cursor()

        old_time = (datetime.now() - timedelta(days=60)).isoformat()  # 2 months ago
        cur.execute("""
            INSERT INTO trust_events (id, actor_id, delta, reason, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (f"OLD_EVENT_{actor_id}", actor_id, 0.1, "old_event", old_time))

        conn.commit()

        # Calculate trust - old event should have less weight
        trust = trust_service.calculate(actor_id)

        # Should be less than 0.7 (0.5 + 0.1 + decayed 0.1)
        # Exact calculation depends on decay rate, but should be less than sum
        assert trust < 0.7

    def test_trust_history(self, test_setup):
        """Test retrieving trust event history"""
        actor_id = "test_history"

        # Add multiple events
        trust_service.apply_delta(actor_id, 0.05, "event1")
        trust_service.apply_delta(actor_id, -0.02, "event2")
        trust_service.apply_delta(actor_id, 0.08, "event3")

        # Get history
        history = trust_service.get_trust_history(actor_id)

        assert len(history) == 3
        assert history[0].reason == "event3"  # Most recent first
        assert history[1].reason == "event2"
        assert history[2].reason == "event1"

    def test_trust_stats(self, test_setup):
        """Test trust statistics"""
        actor_id = "test_stats"

        # Add events of different types
        trust_service.apply_delta(actor_id, 0.05, "on_time_fulfillment")
        trust_service.apply_delta(actor_id, 0.03, "on_time_fulfillment")
        trust_service.apply_delta(actor_id, -0.02, "late_fulfillment")

        # Get stats
        stats = trust_service.get_trust_stats(actor_id)

        assert 'current_trust' in stats
        assert 'event_count' in stats
        assert 'event_stats' in stats
        assert 'recent_events' in stats

        assert stats['event_count'] == 3
        assert 'on_time_fulfillment' in stats['event_stats']
        assert 'late_fulfillment' in stats['event_stats']

        # Check on_time_fulfillment stats
        otf_stats = stats['event_stats']['on_time_fulfillment']
        assert otf_stats['count'] == 2
        assert abs(otf_stats['avg_delta'] - 0.04) < 0.01  # (0.05 + 0.03) / 2

    def test_commitment_linking(self, test_setup):
        """Test trust events linked to commitments"""
        actor_id = "test_commitment_link"
        commitment_id = "COMMIT_test_123"

        # Apply delta with commitment link
        trust_service.apply_delta(
            actor_id=actor_id,
            delta=0.05,
            reason="on_time_fulfillment",
            commitment_id=commitment_id
        )

        # Get history and verify link
        history = trust_service.get_trust_history(actor_id)
        assert len(history) == 1
        assert history[0].commitment_id == commitment_id
