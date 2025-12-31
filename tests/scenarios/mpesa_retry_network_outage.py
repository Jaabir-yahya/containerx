"""
Scenario 1: M-Pesa Retry & Reconciliation

Nairobi Reality: M-Pesa payments fail frequently due to:
- Network timeouts
- Insufficient funds (customer tries again after topping up)
- System overload during peak hours
- Webhook delays (payment succeeds but callback delayed)

UCOS Requirement: 
- Idempotent payments (same reference = same payment, no duplicates)
- Retry logic with exponential backoff
- Webhook reconciliation (match payments to commitments)
- Complete audit trail for all attempts
"""

import pytest
import time
import json
from datetime import datetime, timedelta
from core.services.commitment_service import commitment_service
from core.services.payment_reference_service import payment_reference_service
from core.storage.db import get_db


@pytest.fixture(scope="function", autouse=True)
def cleanup_payments(test_setup):
    """Clean up payment-related data before each test."""
    conn = test_setup
    cur = conn.cursor()
    
    # Ensure payment_references table exists (create if missing)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payment_references (
            reference TEXT PRIMARY KEY,
            payment_id TEXT NOT NULL,
            commitment_id TEXT,
            order_id TEXT,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            status TEXT NOT NULL,
            webhook_data TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Clean up
    cur.execute("DELETE FROM event_log WHERE action LIKE 'PAYMENT_%' OR action LIKE 'COMMITMENT_%'")
    cur.execute("DELETE FROM payments")
    cur.execute("DELETE FROM payment_references")
    conn.commit()
    
    yield conn


def test_mpesa_retry_same_reference_idempotent(cleanup_payments):
    """Test that retrying payment with same M-Pesa reference is idempotent."""
    conn = cleanup_payments
    cur = conn.cursor()
    
    commitment_id = commitment_service.emit_create_event(
        actor_id="pizza_westlands_001",
        promise="Deliver large pizza",
        value=500.0
    )
    
    mpesa_reference = "MPESA_TXN_ABC123"
    payment1 = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=500.0,
        method="mpesa",
        reference=mpesa_reference,
        status="PENDING"
    )
    
    payment2 = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=500.0,
        method="mpesa",
        reference=mpesa_reference,
        status="PENDING"
    )
    
    assert payment1['payment_id'] == payment2['payment_id']
    cur.execute("SELECT COUNT(*) FROM payments WHERE reference = ?", (mpesa_reference,))
    assert cur.fetchone()[0] == 1
    print("✅ M-Pesa retry idempotent")


def test_mpesa_webhook_reconciliation(cleanup_payments):
    """Test webhook reconciliation matches delayed callbacks to payments."""
    conn = cleanup_payments
    cur = conn.cursor()
    
    commitment_id = commitment_service.emit_create_event(
        actor_id="groceries_karen_002",
        promise="Deliver vegetables",
        value=1200.0
    )
    
    mpesa_reference = "MPESA_TXN_XYZ789"
    payment = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=1200.0,
        method="mpesa",
        reference=mpesa_reference,
        status="PENDING"
    )
    
    payment_id = payment['payment_id']
    time.sleep(1)
    payment_reference_service.reconcile_webhook(
        reference=mpesa_reference,
        status="RECEIVED",
        webhook_data={'transaction_id': mpesa_reference, 'amount': 1200.0}
    )
    
    cur.execute("SELECT status FROM payments WHERE id = ?", (payment_id,))
    assert cur.fetchone()[0] == "RECEIVED"
    print("✅ Webhook reconciliation works")


def test_mpesa_retry_different_reference_new_payment(cleanup_payments):
    """Test that different M-Pesa references create new payments."""
    conn = cleanup_payments
    cur = conn.cursor()
    
    commitment_id = commitment_service.emit_create_event(
        actor_id="electronics_cbd_003",
        promise="Repair phone screen",
        value=2500.0
    )
    
    reference1 = "MPESA_TXN_FAILED_001"
    payment1 = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=2500.0,
        method="mpesa",
        reference=reference1,
        status="FAILED"
    )
    
    reference2 = "MPESA_TXN_SUCCESS_002"
    payment2 = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=2500.0,
        method="mpesa",
        reference=reference2,
        status="PENDING"
    )
    
    assert payment1['payment_id'] != payment2['payment_id']
    cur.execute("SELECT COUNT(*) FROM payments WHERE reference IN (?, ?)", (reference1, reference2))
    assert cur.fetchone()[0] == 2
    print("✅ Different references create separate payments")


def test_mpesa_network_outage_queuing(cleanup_payments):
    """Test payment attempts during network outage are queued and processed later."""
    conn = cleanup_payments
    cur = conn.cursor()
    
    commitment_id = commitment_service.emit_create_event(
        actor_id="delivery_westlands_004",
        promise="Boda boda delivery",
        value=150.0
    )
    
    mpesa_reference = "MPESA_TXN_OFFLINE_001"
    payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=150.0,
        method="mpesa",
        reference=mpesa_reference,
        status="QUEUED"
    )
    
    cur.execute("SELECT COUNT(*) FROM payment_references WHERE reference = ? AND status = 'QUEUED'", (mpesa_reference,))
    assert cur.fetchone()[0] > 0
    
    processed = payment_reference_service.process_queued_payments()
    assert processed > 0
    print("✅ Network outage payments queued and processed")
