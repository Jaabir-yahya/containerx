"""
Scenario 2: Cash + M-Pesa Hybrid Payments

Nairobi Reality: Many customers pay part cash, part M-Pesa:
- "Pay 500 cash now, 300 M-Pesa later"
- Common in vegetable markets (Mama Mboga)
- Customer might pay cash deposit, then M-Pesa balance
- Need to track which payment covers which part

UCOS Requirement:
- Partial payment tracking (multiple payment methods)
- Payment allocation logic (which payment covers what)
- Mixed audit trail (cash + digital in same transaction)
- Completion workflows (know when fully paid)
"""

import pytest
import json
from datetime import datetime
from core.services.commitment_service import commitment_service
from core.services.payment_reference_service import payment_reference_service
from core.storage.db import get_db


@pytest.fixture(scope="function", autouse=True)
def cleanup_payments(test_setup):
    """Clean up payment-related data before each test."""
    conn = test_setup
    cur = conn.cursor()
    
    # Clean up
    cur.execute("DELETE FROM event_log WHERE action LIKE 'PAYMENT_%' OR action LIKE 'COMMITMENT_%'")
    cur.execute("DELETE FROM payments")
    cur.execute("DELETE FROM payment_references")
    conn.commit()
    
    yield conn


def test_cash_plus_mpesa_hybrid_payment(cleanup_payments):
    """
    Test that cash + M-Pesa hybrid payments are tracked correctly.
    
    Scenario: Customer orders vegetables worth 800 KES.
    Pays 500 KES cash, then 300 KES via M-Pesa.
    System should track both payments and know when fully paid.
    """
    conn = cleanup_payments
    cur = conn.cursor()
    
    # 1. Create commitment (vegetable order)
    commitment_id = commitment_service.emit_create_event(
        actor_id="mama_mboga_karen_001",
        promise="Deliver fresh vegetables",
        value=800.0
    )
    
    # 2. Customer pays 500 KES cash (partial payment)
    cash_payment = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=500.0,
        method="cash",
        reference=f"CASH_{commitment_id}_001",
        status="RECEIVED"
    )
    
    # 3. Verify cash payment recorded
    assert cash_payment['payment_id'] is not None
    assert cash_payment['status'] == 'RECEIVED'
    
    # Verify payment details in database
    cur.execute("""
        SELECT amount, method, status
        FROM payments
        WHERE id = ?
    """, (cash_payment['payment_id'],))
    
    payment_row = cur.fetchone()
    assert payment_row is not None
    assert payment_row[0] == 500.0, f"Payment amount should be 500, got {payment_row[0]}"
    assert payment_row[1] == 'cash', f"Payment method should be cash, got {payment_row[1]}"
    
    # 4. Check total paid so far
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE order_id = ? AND status = 'RECEIVED'
    """, (commitment_id,))
    
    total_paid = cur.fetchone()[0]
    assert total_paid == 500.0, f"Should have 500 paid, got {total_paid}"
    
    # 5. Customer pays remaining 300 KES via M-Pesa
    mpesa_reference = "MPESA_TXN_HYBRID_001"
    mpesa_payment = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=300.0,
        method="mpesa",
        reference=mpesa_reference,
        status="PENDING"
    )
    
    # 6. Simulate M-Pesa webhook arriving
    payment_reference_service.reconcile_webhook(
        reference=mpesa_reference,
        status="RECEIVED",
        webhook_data={
            'transaction_id': mpesa_reference,
            'amount': 300.0,
            'timestamp': datetime.utcnow().isoformat()
        }
    )
    
    # 7. Verify total paid is now 800 (fully paid)
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE order_id = ? AND status = 'RECEIVED'
    """, (commitment_id,))
    
    total_paid = cur.fetchone()[0]
    assert total_paid == 800.0, f"Should have 800 paid (fully paid), got {total_paid}"
    
    # 8. Verify both payment methods recorded
    cur.execute("""
        SELECT method, amount, status
        FROM payments
        WHERE order_id = ?
        ORDER BY created_at
    """, (commitment_id,))
    
    payments = cur.fetchall()
    assert len(payments) == 2, f"Should have 2 payments, got {len(payments)}"
    
    # Verify cash payment
    assert payments[0][0] == 'cash'
    assert payments[0][1] == 500.0
    
    # Verify M-Pesa payment
    assert payments[1][0] == 'mpesa'
    assert payments[1][1] == 300.0
    assert payments[1][2] == 'RECEIVED'
    
    # 9. Verify event log shows both payments
    cur.execute("""
        SELECT action, json_extract(metadata, '$.method') as method
        FROM event_log
        WHERE entity_type = 'payment'
          AND json_extract(metadata, '$.commitment_id') = ?
        ORDER BY created_at
    """, (commitment_id,))
    
    events = cur.fetchall()
    # Should have: PAYMENT_ATTEMPTED (cash), PAYMENT_ATTEMPTED (mpesa), PAYMENT_RECONCILED (mpesa)
    assert len(events) >= 3, f"Should have at least 3 payment events, got {len(events)}"
    
    print("✅ Cash + M-Pesa hybrid payment tracked correctly")


def test_partial_payment_allocation(cleanup_payments):
    """
    Test that partial payments are correctly allocated to commitments.
    
    Scenario: Customer has 2 commitments:
    - Commitment 1: 500 KES (pays 300 cash)
    - Commitment 2: 400 KES (pays 200 cash)
    System should track which payment goes to which commitment.
    """
    conn = cleanup_payments
    cur = conn.cursor()
    
    # 1. Create two commitments
    commitment1_id = commitment_service.emit_create_event(
        actor_id="customer_westlands_002",
        promise="Deliver groceries",
        value=500.0
    )
    
    commitment2_id = commitment_service.emit_create_event(
        actor_id="customer_westlands_002",
        promise="Deliver fruits",
        value=400.0
    )
    
    # 2. Pay partial for commitment 1
    payment1 = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment1_id,
        amount=300.0,
        method="cash",
        reference=f"CASH_{commitment1_id}_001",
        status="RECEIVED"
    )
    
    # 3. Pay partial for commitment 2
    payment2 = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment2_id,
        amount=200.0,
        method="cash",
        reference=f"CASH_{commitment2_id}_001",
        status="RECEIVED"
    )
    
    # 4. Verify payments allocated correctly
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE order_id = ? AND status = 'RECEIVED'
    """, (commitment1_id,))
    
    total1 = cur.fetchone()[0]
    assert total1 == 300.0, f"Commitment 1 should have 300 paid, got {total1}"
    
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE order_id = ? AND status = 'RECEIVED'
    """, (commitment2_id,))
    
    total2 = cur.fetchone()[0]
    assert total2 == 200.0, f"Commitment 2 should have 200 paid, got {total2}"
    
    # 5. Verify payment references link to correct commitments
    cur.execute("""
        SELECT commitment_id, amount
        FROM payment_references
        WHERE payment_id IN (?, ?)
        ORDER BY commitment_id
    """, (payment1['payment_id'], payment2['payment_id']))
    
    refs = cur.fetchall()
    assert len(refs) == 2, "Should have 2 payment references"
    assert refs[0][0] == commitment1_id
    assert refs[0][1] == 300.0
    assert refs[1][0] == commitment2_id
    assert refs[1][1] == 200.0
    
    print("✅ Partial payment allocation works correctly")


def test_mixed_payment_completion_workflow(cleanup_payments):
    """
    Test that system knows when mixed payment is complete.
    
    Scenario: 1000 KES commitment, customer pays:
    - 400 cash (immediate)
    - 300 M-Pesa (pending webhook)
    - 300 M-Pesa (pending webhook)
    System should track progress and know when fully paid.
    """
    conn = cleanup_payments
    cur = conn.cursor()
    
    commitment_id = commitment_service.emit_create_event(
        actor_id="electronics_cbd_003",
        promise="Repair phone",
        value=1000.0
    )
    
    # 1. Cash payment (immediate)
    cash_payment = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=400.0,
        method="cash",
        reference=f"CASH_{commitment_id}_001",
        status="RECEIVED"
    )
    
    # 2. First M-Pesa payment (pending)
    mpesa_ref1 = "MPESA_TXN_MIXED_001"
    mpesa1 = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=300.0,
        method="mpesa",
        reference=mpesa_ref1,
        status="PENDING"
    )
    
    # 3. Second M-Pesa payment (pending)
    mpesa_ref2 = "MPESA_TXN_MIXED_002"
    mpesa2 = payment_reference_service.record_payment_with_reference(
        commitment_id=commitment_id,
        amount=300.0,
        method="mpesa",
        reference=mpesa_ref2,
        status="PENDING"
    )
    
    # 4. Check current paid (only cash, M-Pesa still pending)
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE order_id = ? AND status = 'RECEIVED'
    """, (commitment_id,))
    
    paid_so_far = cur.fetchone()[0]
    assert paid_so_far == 400.0, f"Should have 400 paid (cash only), got {paid_so_far}"
    
    # 5. Reconcile first M-Pesa payment
    payment_reference_service.reconcile_webhook(
        reference=mpesa_ref1,
        status="RECEIVED",
        webhook_data={'transaction_id': mpesa_ref1, 'amount': 300.0}
    )
    
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE order_id = ? AND status = 'RECEIVED'
    """, (commitment_id,))
    
    paid_so_far = cur.fetchone()[0]
    assert paid_so_far == 700.0, f"Should have 700 paid after first M-Pesa, got {paid_so_far}"
    
    # 6. Reconcile second M-Pesa payment (now fully paid)
    payment_reference_service.reconcile_webhook(
        reference=mpesa_ref2,
        status="RECEIVED",
        webhook_data={'transaction_id': mpesa_ref2, 'amount': 300.0}
    )
    
    cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE order_id = ? AND status = 'RECEIVED'
    """, (commitment_id,))
    
    total_paid = cur.fetchone()[0]
    assert total_paid == 1000.0, f"Should be fully paid (1000), got {total_paid}"
    
    # 7. Verify all payment methods recorded
    cur.execute("""
        SELECT method, COUNT(*) as count
        FROM payments
        WHERE order_id = ?
        GROUP BY method
    """, (commitment_id,))
    
    methods = dict(cur.fetchall())
    assert methods.get('cash', 0) == 1, "Should have 1 cash payment"
    assert methods.get('mpesa', 0) == 2, "Should have 2 M-Pesa payments"
    
    print("✅ Mixed payment completion workflow works correctly")

