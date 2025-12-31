"""
Unit tests for UCOS Commitment Service
"""
import pytest
from datetime import datetime, timedelta
from core.services.commitment_service import commitment_service
from core.models.commitment import Commitment

class TestCommitmentService:
    """Test UCOS Commitment Service"""

    def test_create_commitment(self, test_setup):
        """Test basic commitment creation"""
        actor_id = "test_customer_123"
        promise = "Deliver pizza within 30 minutes"
        value = 1500.0

        commitment = commitment_service.create(
            actor_id=actor_id,
            promise=promise,
            value=value
        )

        assert commitment.id.startswith("COMMIT_")
        assert commitment.actor_id == actor_id
        assert commitment.promise == promise
        assert commitment.value == value
        assert commitment.state == "pending"
        assert commitment.metadata['type'] == 'order'
        assert commitment.metadata['sla_hours'] == 24

    def test_get_commitment(self, test_setup):
        """Test retrieving a commitment"""
        # Create a commitment
        commitment = commitment_service.create(
            actor_id="test_actor",
            promise="Test promise",
            value=100.0
        )

        # Retrieve it
        retrieved = commitment_service.get(commitment.id)

        assert retrieved is not None
        assert retrieved.id == commitment.id
        assert retrieved.actor_id == commitment.actor_id
        assert retrieved.promise == commitment.promise

    def test_update_state(self, test_setup):
        """Test state updates"""
        # Create commitment
        commitment = commitment_service.create(
            actor_id="test_actor",
            promise="Test promise",
            value=100.0
        )

        # Update state
        success = commitment_service.update_state(commitment.id, "accepted")

        assert success is True

        # Verify state changed
        updated = commitment_service.get(commitment.id)
        assert updated.state == "accepted"

    def test_fulfill_commitment(self, test_setup):
        """Test commitment fulfillment with trust impact"""
        from core.services.trust_service import trust_service

        # Create commitment
        commitment = commitment_service.create(
            actor_id="test_seller",
            promise="Deliver goods",
            value=500.0
        )

        # Get initial trust
        initial_trust = trust_service.calculate("test_seller")
        assert initial_trust == 0.5  # Default neutral

        # Fulfill commitment
        success = commitment_service.fulfill(commitment.id)

        assert success is True

        # Verify state changed
        fulfilled = commitment_service.get(commitment.id)
        assert fulfilled.state == "fulfilled"

        # Verify trust increased
        final_trust = trust_service.calculate("test_seller")
        assert final_trust > initial_trust

    def test_commitment_expiration(self, test_setup):
        """Test commitment expiration"""
        from core.services.trust_service import trust_service

        # Create commitment with past due date
        past_due = (datetime.now() - timedelta(hours=1)).isoformat()

        commitment = commitment_service.create(
            actor_id="test_seller",
            promise="Expired promise",
            value=200.0,
            due_by=past_due
        )

        # Get initial trust
        initial_trust = trust_service.calculate("test_seller")

        # Expire commitment
        success = commitment_service.expire(commitment.id)

        assert success is True

        # Verify state changed
        expired = commitment_service.get(commitment.id)
        assert expired.state == "expired"

        # Verify trust decreased
        final_trust = trust_service.calculate("test_seller")
        assert final_trust < initial_trust

    def test_list_commitments_by_actor(self, test_setup):
        """Test listing commitments for an actor"""
        actor_id = "test_actor_list"

        # Create multiple commitments
        commitment1 = commitment_service.create(
            actor_id=actor_id,
            promise="Promise 1",
            value=100.0
        )

        commitment2 = commitment_service.create(
            actor_id=actor_id,
            promise="Promise 2",
            value=200.0
        )

        # List commitments
        commitments = commitment_service.list_by_actor(actor_id)

        assert len(commitments) == 2
        assert commitments[0].actor_id == actor_id
        assert commitments[1].actor_id == actor_id

        # Verify they're ordered by creation time (newest first)
        assert commitments[0].created_at >= commitments[1].created_at

    def test_get_expired_commitments(self, test_setup):
        """Test finding expired commitments"""
        # Create expired commitment
        past_due = (datetime.now() - timedelta(hours=1)).isoformat()

        expired_commitment = commitment_service.create(
            actor_id="test_expired",
            promise="Expired promise",
            value=100.0,
            due_by=past_due
        )

        # Create active commitment
        future_due = (datetime.now() + timedelta(hours=1)).isoformat()

        active_commitment = commitment_service.create(
            actor_id="test_active",
            promise="Active promise",
            value=100.0,
            due_by=future_due
        )

        # Get expired commitments
        expired_list = commitment_service.get_expired_commitments()

        # Should find the expired one
        expired_ids = [c.id for c in expired_list]
        assert expired_commitment.id in expired_ids
        assert active_commitment.id not in expired_ids
