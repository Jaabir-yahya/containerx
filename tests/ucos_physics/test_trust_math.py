"""
UCOS Physics: Trust Score Mathematical Invariants

Validates that trust calculations follow mathematical rules.
"""
import pytest
from core.services.trust_service import trust_service
from core.storage.db import get_db


def test_trust_bounds(test_setup):
    """
    UCOS Invariant: Trust scores must be bounded between 0.05 and 0.95.
    
    This ensures trust scores are always meaningful and never extreme.
    """
    actor_id = "trust_bounds_test"
    
    # Start with neutral trust
    initial_trust = trust_service.calculate(actor_id)
    assert 0.05 <= initial_trust <= 0.95, "Initial trust should be in bounds"
    
    # Apply many positive deltas (should cap at 0.95)
    for _ in range(20):
        trust_service.apply_delta(actor_id, 0.3, 'positive_test', None)
    
    high_trust = trust_service.calculate(actor_id)
    assert high_trust <= 0.95, "Trust should not exceed 0.95"
    assert high_trust >= 0.05, "Trust should not go below 0.05"
    
    # Apply many negative deltas (should floor at 0.05)
    actor_id2 = "trust_bounds_test_2"
    for _ in range(20):
        trust_service.apply_delta(actor_id2, -0.3, 'negative_test', None)
    
    low_trust = trust_service.calculate(actor_id2)
    assert low_trust >= 0.05, "Trust should not go below 0.05"
    assert low_trust <= 0.95, "Trust should not exceed 0.95"
    
    print("✅ Trust bounds invariant verified")


def test_trust_delta_bounds(test_setup):
    """
    UCOS Invariant: Individual trust deltas must be bounded (-0.3 to +0.3).
    
    This prevents single events from having extreme impact.
    """
    actor_id = "delta_bounds_test"
    
    # Try to apply extreme positive delta
    trust_service.apply_delta(actor_id, 1.0, 'extreme_positive', None)
    
    # Should be capped at 0.3
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT delta FROM trust_events 
        WHERE actor_id = ? AND reason = 'extreme_positive'
    """, (actor_id,))
    delta = cur.fetchone()[0]
    
    assert -0.3 <= delta <= 0.3, "Delta should be bounded"
    assert delta == 0.3, "Extreme positive should be capped at 0.3"
    
    # Try extreme negative
    trust_service.apply_delta(actor_id, -1.0, 'extreme_negative', None)
    cur.execute("""
        SELECT delta FROM trust_events 
        WHERE actor_id = ? AND reason = 'extreme_negative'
    """, (actor_id,))
    delta = cur.fetchone()[0]
    
    assert delta == -0.3, "Extreme negative should be floored at -0.3"
    
    print("✅ Trust delta bounds verified")

