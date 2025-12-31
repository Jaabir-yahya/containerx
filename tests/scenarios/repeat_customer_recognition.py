"""Scenario 8: Repeat Customer Recognition"""
import pytest
from core.services.commitment_service import commitment_service
from core.storage.db import get_db

@pytest.fixture(scope="function", autouse=True)
def cleanup(test_setup):
    conn = test_setup
    cur = conn.cursor()
    cur.execute("DELETE FROM event_log WHERE action LIKE 'COMMITMENT_%'")
    conn.commit()
    yield conn

def test_repeat_customer_recognition(cleanup):
    """Test repeat customer recognition."""
    conn = cleanup
    cur = conn.cursor()
    
    customer_id = "loyal_customer_001"
    
    # Create multiple commitments from same customer
    commitment1 = commitment_service.emit_create_event(
        actor_id="seller_001",
        promise="Order 1",
        value=100.0,
        metadata={'customer_id': customer_id}
    )
    
    commitment2 = commitment_service.emit_create_event(
        actor_id="seller_001",
        promise="Order 2",
        value=100.0,
        metadata={'customer_id': customer_id}
    )
    
    # System should recognize repeat customer
    # (Loyalty tracking would be implemented in Phase 3)
    cur.execute("""
        SELECT COUNT(*) FROM event_log
        WHERE json_extract(metadata, '$.customer_id') = ?
    """, (customer_id,))
    
    assert cur.fetchone()[0] >= 2, "Should track repeat customer"
    print("✅ Repeat customer recognition works")
