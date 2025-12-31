"""
UCOS Physics: Event Sourcing Invariants

Validates that UCOS follows pure event sourcing patterns.
"""
import pytest
from core.services.commitment_service import commitment_service
from core.services.state_derivation_service import state_derivation
from core.services.audit_service import log_event
from core.storage.db import get_db


def test_all_state_from_events(test_setup):
    """
    UCOS Invariant: All state must be derivable from event replay.
    
    This is the CORE invariant of UCOS. If this fails, the architecture is broken.
    """
    # Create commitment via event
    commitment_id = commitment_service.emit_create_event(
        actor_id="physics_test_actor",
        promise="Event sourcing physics test",
        value=500.0
    )
    
    # Derive state from events
    state = state_derivation.get_commitment_state(commitment_id)
    
    assert state is not None, "State must be derivable from events"
    assert state['status'] == 'pending', "Initial state should be pending"
    
    # Change state via event
    commitment_service.emit_state_change_event(commitment_id, 'accepted', 'test_actor')
    
    # Derive again - should reflect new state
    state_after = state_derivation.get_commitment_state(commitment_id)
    assert state_after['status'] == 'accepted', "State should update from events"
    
    print("✅ Event sourcing invariant verified")


def test_event_immutability(test_setup):
    """
    UCOS Invariant: Events are immutable - once logged, never changed.
    
    This ensures audit trail integrity.
    """
    commitment_id = commitment_service.emit_create_event(
        actor_id="immutability_test",
        promise="Event immutability test",
        value=300.0
    )
    
    # Get the original event
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, action, metadata, created_at 
        FROM event_log 
        WHERE entity_id = ? AND action = 'COMMITMENT_CREATED'
    """, (commitment_id,))
    
    original_event = cur.fetchone()
    original_id = original_event[0]
    original_metadata = original_event[2]
    
    # Try to "update" by creating another event (not modifying)
    commitment_service.emit_state_change_event(commitment_id, 'accepted', 'test')
    
    # Original event should be unchanged
    cur.execute("""
        SELECT id, action, metadata, created_at 
        FROM event_log 
        WHERE id = ?
    """, (original_id,))
    
    unchanged_event = cur.fetchone()
    assert unchanged_event[1] == 'COMMITMENT_CREATED', "Original event should be unchanged"
    assert unchanged_event[2] == original_metadata, "Original metadata should be unchanged"
    
    # Should now have 2 events (created + state change)
    cur.execute("""
        SELECT COUNT(*) FROM event_log WHERE entity_id = ?
    """, (commitment_id,))
    event_count = cur.fetchone()[0]
    assert event_count == 2, "Should have 2 events, not modified original"
    
    print("✅ Event immutability verified")


def test_state_replay_consistency(test_setup):
    """
    UCOS Invariant: Replaying events in order always produces same state.
    
    This ensures determinism - same events = same state.
    """
    commitment_id = commitment_service.emit_create_event(
        actor_id="replay_test",
        promise="Replay consistency test",
        value=400.0
    )
    
    # Derive state first time
    state1 = state_derivation.get_commitment_state(commitment_id)
    
    # Apply state change
    commitment_service.emit_state_change_event(commitment_id, 'accepted', 'test')
    
    # Derive state second time
    state2 = state_derivation.get_commitment_state(commitment_id)
    
    # Should be different (state changed)
    assert state1['status'] != state2['status'], "State should change after event"
    
    # Derive again - should be same as state2 (deterministic)
    state3 = state_derivation.get_commitment_state(commitment_id)
    assert state2['status'] == state3['status'], "Replay should be deterministic"
    assert state2['value'] == state3['value'], "All fields should be same"
    
    print("✅ State replay consistency verified")

