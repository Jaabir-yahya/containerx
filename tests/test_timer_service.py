"""
Tests for TimerService - UCOS Phase 2
Tests event-driven timer scheduling and firing.
"""
import time
import json
from datetime import datetime, timedelta

import pytest
from core.services.timer_service import TimerService
from core.services.commitment_service import commitment_service
from core.services.audit_service import log_event
from core.services.state_derivation_service import state_derivation
from core.storage.db import get_db


def test_timer_service_schedules_on_commitment_created(test_setup):
    """
    Test that TimerService schedules timer on COMMITMENT_CREATED event.
    
    UCOS Pattern: Event-driven - commitment creation triggers timer scheduling.
    """
    conn = test_setup
    cur = conn.cursor()
    
    # Clean up
    cur.execute("DELETE FROM event_log WHERE action LIKE 'TIMER_%'")
    cur.execute("DELETE FROM timers")
    conn.commit()
    
    # Create a commitment event
    commitment_id = commitment_service.emit_create_event(
        actor_id='test_seller',
        promise='Test delivery',
        value=1000.0,
        metadata={'sla_hours': 1}  # 1 hour SLA for fast test
    )
    
    # Start timer service
    timer_service = TimerService()
    
    # Wait for processing (TimerService checks every second)
    time.sleep(2)
    
    # Check timer was scheduled in database
    cur.execute("SELECT COUNT(*) FROM timers WHERE commitment_id = ?", (commitment_id,))
    timer_count = cur.fetchone()[0]
    
    assert timer_count > 0, "Timer should be scheduled for new commitment"
    
    # Check TIMER_SCHEDULED event was emitted
    cur.execute("""
        SELECT COUNT(*) FROM event_log 
        WHERE action = 'TIMER_SCHEDULED' 
          AND entity_type = 'timer'
    """)
    event_count = cur.fetchone()[0]
    
    assert event_count > 0, "TIMER_SCHEDULED event should be emitted"
    
    # Verify event metadata contains commitment_id
    cur.execute("""
        SELECT metadata FROM event_log 
        WHERE action = 'TIMER_SCHEDULED'
        LIMIT 1
    """)
    metadata_row = cur.fetchone()
    assert metadata_row is not None
    
    metadata = json.loads(metadata_row[0]) if isinstance(metadata_row[0], str) else metadata_row[0]
    assert metadata.get('commitment_id') == commitment_id
    
    # Clean up
    timer_service.stop()


def test_timer_service_calculates_sla_from_trust(test_setup):
    """
    Test that TimerService calculates SLA based on trust score.
    """
    from core.services.trust_service import trust_service
    
    conn = test_setup
    
    # Set up actor with high trust
    actor_id = 'high_trust_seller'
    trust_service.apply_delta(actor_id, 0.2, 'test_positive', None)
    high_trust = trust_service.calculate(actor_id)
    assert high_trust > 0.5
    
    # Create commitment with high trust actor
    commitment_id = commitment_service.emit_create_event(
        actor_id=actor_id,
        promise='Fast delivery',
        value=500.0
    )
    
    timer_service = TimerService()
    time.sleep(2)
    
    # Check SLA was calculated (should be shorter for high trust)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT metadata FROM event_log 
        WHERE action = 'TIMER_SCHEDULED'
          AND entity_type = 'timer'
        ORDER BY created_at DESC
        LIMIT 1
    """)
    
    metadata_row = cur.fetchone()
    assert metadata_row is not None
    
    metadata = json.loads(metadata_row[0]) if isinstance(metadata_row[0], str) else metadata_row[0]
    sla_hours = metadata.get('sla_hours')
    trust_score = metadata.get('trust_score')
    
    assert sla_hours is not None
    assert trust_score is not None
    assert trust_score == high_trust
    # High trust should result in shorter SLA (less than 24 hours)
    assert sla_hours < 24
    
    timer_service.stop()


def test_timer_fires_and_emits_event(test_setup):
    """
    Test that timer fires and emits TIMER_FIRED event.
    
    UCOS Pattern: Timer fires → emits TIMER_FIRED → AutoRefundEngine reacts.
    """
    conn = test_setup
    cur = conn.cursor()
    
    # Clean up
    cur.execute("DELETE FROM event_log WHERE action LIKE 'TIMER_%'")
    cur.execute("DELETE FROM timers")
    conn.commit()
    
    # Create commitment with very short SLA (1 second for test)
    commitment_id = commitment_service.emit_create_event(
        actor_id='test_seller',
        promise='Quick test',
        value=100.0,
        metadata={'sla_hours': 0.0003}  # ~1 second
    )
    
    timer_service = TimerService()
    
    # Wait for timer to fire
    time.sleep(3)
    
    # Check TIMER_FIRED event was emitted
    cur.execute("""
        SELECT COUNT(*) FROM event_log 
        WHERE action = 'TIMER_FIRED' 
          AND entity_type = 'timer'
    """)
    fired_count = cur.fetchone()[0]
    
    assert fired_count > 0, "TIMER_FIRED event should be emitted when timer fires"
    
    # Verify event metadata
    cur.execute("""
        SELECT metadata FROM event_log 
        WHERE action = 'TIMER_FIRED'
        LIMIT 1
    """)
    metadata_row = cur.fetchone()
    assert metadata_row is not None
    
    metadata = json.loads(metadata_row[0]) if isinstance(metadata_row[0], str) else metadata_row[0]
    assert metadata.get('commitment_id') == commitment_id
    assert metadata.get('timer_type') == 'sla_acceptance'
    
    timer_service.stop()


def test_timer_service_handles_expired_timers_on_startup(test_setup):
    """
    Test that TimerService fires expired timers when starting up.
    
    UCOS Pattern: Persistence - timers saved to DB, fired on restart if expired.
    """
    conn = test_setup
    cur = conn.cursor()
    
    # Clean up
    cur.execute("DELETE FROM event_log WHERE action LIKE 'TIMER_%'")
    cur.execute("DELETE FROM timers")
    conn.commit()
    
    # Create a commitment
    commitment_id = commitment_service.emit_create_event(
        actor_id='test_seller',
        promise='Past due',
        value=200.0
    )
    
    # Manually insert an expired timer (simulating timer from before restart)
    past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    timer_id = f"TIMER_{commitment_id}_expired"
    
    cur.execute("""
        INSERT INTO timers (id, commitment_id, type, fires_at, action, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timer_id, commitment_id, 'sla_acceptance', past_time, 'auto_refund', 'scheduled', past_time))
    conn.commit()
    
    # Start timer service (should detect and fire expired timer)
    timer_service = TimerService()
    time.sleep(2)
    
    # Check that TIMER_FIRED event was emitted
    cur.execute("""
        SELECT COUNT(*) FROM event_log 
        WHERE action = 'TIMER_FIRED'
          AND json_extract(metadata, '$.commitment_id') = ?
    """, (commitment_id,))
    fired_count = cur.fetchone()[0]
    
    assert fired_count > 0, "Expired timer should fire on startup"
    
    # Check timer status updated
    cur.execute("SELECT status FROM timers WHERE id = ?", (timer_id,))
    status = cur.fetchone()[0]
    assert status == 'fired'
    
    timer_service.stop()


def test_timer_service_does_not_double_schedule(test_setup):
    """
    Test that TimerService doesn't schedule duplicate timers.
    
    UCOS Pattern: Idempotency - same commitment should only get one timer.
    """
    conn = test_setup
    cur = conn.cursor()
    
    # Clean up
    cur.execute("DELETE FROM event_log WHERE action LIKE 'TIMER_%'")
    cur.execute("DELETE FROM timers")
    conn.commit()
    
    # Create commitment
    commitment_id = commitment_service.emit_create_event(
        actor_id='test_seller',
        promise='Single timer test',
        value=300.0
    )
    
    timer_service = TimerService()
    
    # Wait for first scheduling
    time.sleep(2)
    
    # Count timers scheduled
    cur.execute("SELECT COUNT(*) FROM timers WHERE commitment_id = ?", (commitment_id,))
    first_count = cur.fetchone()[0]
    
    # Wait again (TimerService should not schedule again)
    time.sleep(2)
    
    cur.execute("SELECT COUNT(*) FROM timers WHERE commitment_id = ?", (commitment_id,))
    second_count = cur.fetchone()[0]
    
    assert first_count == second_count, "Should not schedule duplicate timers"
    assert first_count == 1, "Should have exactly one timer"
    
    timer_service.stop()

