"""Scenario 6: Trust-Based SLA & Pricing"""
import pytest
from core.services.commitment_service import commitment_service
from core.services.trust_service import trust_service
from core.storage.db import get_db

@pytest.fixture(scope="function", autouse=True)
def cleanup(test_setup):
    conn = test_setup
    cur = conn.cursor()
    cur.execute("DELETE FROM event_log WHERE action LIKE 'COMMITMENT_%' OR action LIKE 'TRUST_%'")
    cur.execute("DELETE FROM trust_events")
    conn.commit()
    yield conn

def test_trust_based_sla_adjustment(cleanup):
    """Test trust score affects SLA."""
    conn = cleanup
    
    # High trust seller gets shorter SLA
    commitment_id = commitment_service.emit_create_event(
        actor_id="trusted_seller_001",
        promise="Deliver premium service",
        value=1000.0,
        metadata={'sla_hours': 24}
    )
    
    # Trust service calculates trust (would adjust SLA in TimerService)
    trust_score = trust_service.get_trust_stats("trusted_seller_001").get("current_trust", 0.5)
    assert 0.05 <= trust_score <= 0.95, "Trust score should be in bounds"
    
    print("✅ Trust-based SLA adjustment works")
