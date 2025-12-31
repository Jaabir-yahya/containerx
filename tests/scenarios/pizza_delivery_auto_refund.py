"""
Pizza Delivery Auto-Refund Scenario
Real Nairobi business case: Pizza shop in Westlands, SLA breach triggers auto-refund.

UCOS Pattern: End-to-end flow testing
1. Create commitment (pizza order)
2. Payment via M-Pesa (simulated)
3. TimerService schedules SLA timer
4. SLA breach occurs (timer fires)
5. AutoRefundEngine triggers auto-refund
6. Trust penalty applied
"""
import pytest
import time
import json
from datetime import datetime, timedelta
from core.services.commitment_service import commitment_service
from core.services.state_derivation_service import state_derivation
from core.services.timer_service import TimerService
from core.services.auto_refund_engine import auto_refund_engine
from core.services.payment_service import record_payment
from core.storage.db import get_db


def test_pizza_delivery_auto_refund_on_sla_breach(test_setup):
    """
    Real Nairobi: Pizza shop in Westlands, SLA breach triggers auto-refund.
    
    Scenario:
    - Customer orders pizza via WhatsApp
    - Payment made via M-Pesa
    - Seller commits to 2-hour delivery
    - 2.5 hours pass (SLA breach)
    - Auto-refund triggered automatically
    - Trust penalty applied to seller
    """
    conn = test_setup
    cur = conn.cursor()
    
    # Clean up
    cur.execute("DELETE FROM event_log WHERE action LIKE 'TIMER_%' OR action LIKE 'AUTO_REFUND%'")
    cur.execute("DELETE FROM timers")
    cur.execute("DELETE FROM payments")
    conn.commit()
    
    # Real Nairobi context
    customer_phone = "+254712345678"
    seller_id = "pizza_westlands_001"
    pizza_amount = 850.0  # KES for large pizza
    sla_hours = 0.01  # Very short SLA for fast test (~36 seconds)
    
    # Step 1: Create commitment (pizza order)
    commitment_id = commitment_service.emit_create_event(
        actor_id=seller_id,
        promise=f"Deliver large pizza to {customer_phone} within {sla_hours} hours",
        value=pizza_amount,
        metadata={
            'type': 'pizza_delivery',
            'sla_hours': sla_hours,
            'customer_phone': customer_phone,
            'auto_refund': True
        }
    )
    
    # Step 2: Payment via M-Pesa (simulated)
    payment_id = record_payment(
        order_id=commitment_id,
        amount=pizza_amount,
        method="mpesa",
        reference=f"MPESA_{int(time.time())}"
    )
    
    # Step 3: TimerService schedules SLA timer (should happen automatically)
    timer_service = TimerService()
    time.sleep(2)  # Wait for timer to be scheduled
    
    # Verify timer was scheduled
    cur.execute("""
        SELECT COUNT(*) FROM event_log 
        WHERE action = 'TIMER_SCHEDULED' 
          AND entity_type = 'timer'
    """)
    timer_scheduled_count = cur.fetchone()[0]
    assert timer_scheduled_count > 0, "Timer should be scheduled for commitment"
    
    # Step 4: Wait for SLA breach (timer fires)
    # With 0.01 hours SLA (~36 seconds), wait 40 seconds
    time.sleep(40)
    
    # Step 5: Verify TIMER_FIRED event was emitted
    cur.execute("""
        SELECT COUNT(*) FROM event_log 
        WHERE action = 'TIMER_FIRED' 
          AND entity_type = 'timer'
    """)
    timer_fired_count = cur.fetchone()[0]
    assert timer_fired_count > 0, "Timer should fire when SLA breached"
    
    # Step 6: Verify AUTO_REFUND_TRIGGERED event was emitted
    # (This will FAIL until AutoRefundEngine is implemented)
    cur.execute("""
        SELECT COUNT(*) FROM event_log 
        WHERE action = 'AUTO_REFUND_TRIGGERED' 
          AND entity_type = 'commitment'
          AND entity_id = ?
    """, (commitment_id,))
    auto_refund_count = cur.fetchone()[0]
    assert auto_refund_count > 0, "Auto-refund should be triggered on SLA breach"
    
    # Step 7: Verify commitment state changed to 'refunded'
    state = state_derivation.get_commitment_state(commitment_id)
    assert state['status'] == 'refunded', "Commitment should be marked as refunded"
    
    # Step 8: Verify trust penalty was applied
    from core.services.trust_service import trust_service
    trust_score = trust_service.calculate(seller_id)
    
    # Trust should be lower due to SLA breach penalty
    # (Exact value depends on initial trust, but should be < 0.5 if starting neutral)
    cur.execute("""
        SELECT COUNT(*) FROM trust_events 
        WHERE actor_id = ? 
          AND (reason LIKE '%sla%' OR reason LIKE '%auto_refund%')
    """, (seller_id,))
    trust_penalty_count = cur.fetchone()[0]
    assert trust_penalty_count > 0, "Trust penalty should be applied for SLA breach"
    
    # Clean up
    timer_service.stop()
    
    print("✅ Pizza delivery auto-refund scenario passed")


def test_auto_refund_only_for_pending_commitments(test_setup):
    """
    Verify that auto-refund only triggers for pending commitments.
    
    If commitment is already fulfilled or accepted, no auto-refund.
    """
    conn = test_setup
    cur = conn.cursor()
    
    # Clean up
    cur.execute("DELETE FROM event_log WHERE action LIKE 'TIMER_%' OR action LIKE 'AUTO_REFUND%'")
    cur.execute("DELETE FROM timers")
    conn.commit()
    
    seller_id = "test_seller"
    commitment_id = commitment_service.emit_create_event(
        actor_id=seller_id,
        promise="Test commitment",
        value=100.0,
        metadata={'sla_hours': 0.01}
    )
    
    # Fulfill the commitment before SLA breach
    commitment_service.emit_fulfill_event(commitment_id, evidence={'photo': 'delivered.jpg'})
    
    # Start timer service
    timer_service = TimerService()
    time.sleep(2)
    
    # Wait for timer to fire
    time.sleep(40)
    
    # Verify timer fired
    cur.execute("""
        SELECT COUNT(*) FROM event_log 
        WHERE action = 'TIMER_FIRED'
    """)
    timer_fired = cur.fetchone()[0]
    assert timer_fired > 0, "Timer should fire"
    
    # Verify NO auto-refund was triggered (commitment already fulfilled)
    cur.execute("""
        SELECT COUNT(*) FROM event_log 
        WHERE action = 'AUTO_REFUND_TRIGGERED' 
          AND entity_id = ?
    """, (commitment_id,))
    auto_refund_count = cur.fetchone()[0]
    assert auto_refund_count == 0, "Auto-refund should NOT trigger for fulfilled commitments"
    
    # Verify commitment state is still 'fulfilled'
    state = state_derivation.get_commitment_state(commitment_id)
    assert state['status'] == 'fulfilled', "Commitment should remain fulfilled"
    
    timer_service.stop()
    
    print("✅ Auto-refund correctly skipped for fulfilled commitments")

