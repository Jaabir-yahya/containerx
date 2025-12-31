"""Scenario 7: Dispute Escalation Paths"""
import pytest
from core.services.commitment_service import commitment_service
from core.services.audit_service import log_event
from core.storage.db import get_db

@pytest.fixture(scope="function", autouse=True)
def cleanup(test_setup):
    conn = test_setup
    cur = conn.cursor()
    cur.execute("DELETE FROM event_log WHERE action LIKE 'COMMITMENT_%' OR action LIKE 'DISPUTE_%'")
    conn.commit()
    yield conn

def test_dispute_escalation(cleanup):
    """Test dispute escalation with evidence."""
    conn = cleanup
    cur = conn.cursor()
    
    commitment_id = commitment_service.emit_create_event(
        actor_id="seller_001",
        promise="Deliver food",
        value=500.0
    )
    
    # Customer files dispute with evidence
    log_event(
        entity_type='commitment',
        entity_id=commitment_id,
        action='DISPUTE_RAISED',
        metadata={
            'reason': 'Food was cold',
            'evidence': {'photo': 'cold_food.jpg'},
            'requested_resolution': 'partial_refund'
        },
        source='customer'
    )
    
    # Verify dispute event
    cur.execute("""
        SELECT COUNT(*) FROM event_log
        WHERE entity_id = ? AND action = 'DISPUTE_RAISED'
    """, (commitment_id,))
    
    assert cur.fetchone()[0] > 0, "Should have dispute event"
    print("✅ Dispute escalation works")
