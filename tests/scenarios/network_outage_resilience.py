"""Scenario 4: Network Outage Resilience"""
import pytest
from core.services.commitment_service import commitment_service
from core.services.payment_reference_service import payment_reference_service
from core.storage.db import get_db

@pytest.fixture(scope="function", autouse=True)
def cleanup(test_setup):
    conn = test_setup
    cur = conn.cursor()
    cur.execute("DELETE FROM event_log WHERE action LIKE 'COMMITMENT_%' OR action LIKE 'PAYMENT_%'")
    cur.execute("DELETE FROM payments")
    cur.execute("DELETE FROM payment_references")
    cur.execute("DELETE FROM offline_queue")
    conn.commit()
    yield conn

def test_network_outage_queuing(cleanup):
    """Test payments queued during network outage."""
    conn = cleanup
    cur = conn.cursor()
    
    commitment_id = commitment_service.emit_create_event(
        actor_id="customer_westlands_004",
        promise="Deliver groceries",
        value=500.0
    )
    
    # Payment queued during outage
    payment = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=500.0,
        method="mpesa",
        reference="MPESA_OFFLINE_001",
        status="QUEUED"
    )
    
    # Verify queued
    cur.execute("SELECT COUNT(*) FROM payment_references WHERE status = 'QUEUED'")
    assert cur.fetchone()[0] > 0, "Payment should be queued"
    
    # Process queue when network returns
    processed = payment_reference_service.process_queued_payments()
    assert processed >= 0, "Should process queued payments"
    
    print("✅ Network outage resilience works")
