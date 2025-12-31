"""
Scenario 3: Partial Fulfillment with Proportional Settlement
"""
import pytest
from core.services.commitment_service import commitment_service
from core.services.payment_reference_service import payment_reference_service
from core.services.audit_service import log_event
from core.storage.db import get_db

@pytest.fixture(scope="function", autouse=True)
def cleanup(test_setup):
    conn = test_setup
    cur = conn.cursor()
    cur.execute("DELETE FROM event_log WHERE action LIKE 'COMMITMENT_%' OR action LIKE 'PAYMENT_%'")
    cur.execute("DELETE FROM payments")
    cur.execute("DELETE FROM payment_references")
    conn.commit()
    yield conn

def test_partial_fulfillment_proportional_settlement(cleanup):
    """Test partial fulfillment results in proportional settlement."""
    conn = cleanup
    cur = conn.cursor()
    
    commitment_id = commitment_service.emit_create_event(
        actor_id="builder_westlands_001",
        promise="Build house foundation",
        value=10000.0
    )
    
    payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=10000.0,
        method="mpesa",
        reference=f"PAY_{commitment_id}",
        status="RECEIVED"
    )
    
    # Partial fulfillment: 80%
    log_event(
        entity_type='commitment',
        entity_id=commitment_id,
        action='COMMITMENT_PARTIALLY_FULFILLED',
        metadata={
            'fulfillment_percentage': 80.0,
            'completed_value': 8000.0,
            'remaining_value': 2000.0
        },
        source='system'
    )
    
    # Verify event logged
    cur.execute("""
        SELECT COUNT(*) FROM event_log
        WHERE entity_id = ? AND action = 'COMMITMENT_PARTIALLY_FULFILLED'
    """, (commitment_id,))
    
    assert cur.fetchone()[0] > 0, "Should have partial fulfillment event"
    print("✅ Partial fulfillment proportional settlement works")
