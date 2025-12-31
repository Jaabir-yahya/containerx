"""
Unit tests for payment service.

Tests payment service in isolation with real database.
"""

import pytest
from core.services.payment_service import record_payment, get_total_paid
from core.storage.db import get_db
from tests.helpers import get_event_log, assert_event_exists

class TestPaymentService:
    """Test payment service operations."""
    
    def test_record_payment_creates_record(self, clean_db):
        """Test that recording a payment creates a database record."""
        order_id = "TEST_ORDER_123"
        
        payment = record_payment(order_id, 1000.0, "manual", None)
        
        assert payment.order_id == order_id
        assert payment.amount == 1000.0
        assert payment.method == "manual"
        assert payment.status == "RECEIVED"
        
        # Verify in database
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM payments WHERE id = ?", (payment.id,))
        result = cur.fetchone()
        conn.close()
        
        assert result is not None
        assert result[1] == order_id  # order_id column
        assert result[2] == 1000.0   # amount column
    
    def test_record_payment_with_reference(self, clean_db):
        """Test recording payment with reference."""
        order_id = "TEST_ORDER_123"
        reference = "MPESA_ABC123"
        
        payment = record_payment(order_id, 500.0, "mpesa", reference)
        
        assert payment.reference == reference
        
        # Verify in database
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT reference FROM payments WHERE id = ?", (payment.id,))
        result = cur.fetchone()
        conn.close()
        
        assert result[0] == reference
    
    def test_record_payment_logs_event(self, clean_db):
        """Test that recording payment logs an event."""
        order_id = "TEST_ORDER_123"
        
        payment = record_payment(order_id, 1000.0, "manual", None)
        
        assert_event_exists("payment", payment.id, "recorded")
        
        events = get_event_log(entity_type="payment", entity_id=payment.id)
        assert len(events) == 1
        assert events[0]["action"] == "recorded"
    
    def test_get_total_paid_single_payment(self, clean_db):
        """Test getting total paid for order with single payment."""
        order_id = "TEST_ORDER_123"
        
        record_payment(order_id, 1000.0, "manual", None)
        
        total = get_total_paid(order_id)
        assert total == 1000.0
    
    def test_get_total_paid_multiple_payments(self, clean_db):
        """Test getting total paid for order with multiple payments."""
        order_id = "TEST_ORDER_123"
        
        record_payment(order_id, 500.0, "manual", None)
        record_payment(order_id, 300.0, "mpesa", "REF1")
        record_payment(order_id, 200.0, "cash", None)
        
        total = get_total_paid(order_id)
        assert total == 1000.0
    
    def test_get_total_paid_only_received(self, clean_db):
        """Test that only RECEIVED payments are counted."""
        from core.storage.db import get_db
        order_id = "TEST_ORDER_123"

        # Create order first
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO orders (id, customer_identifier, total_amount, status, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (order_id, "CUSTOMER1", 1000.0, "PENDING"))
        conn.commit()

        # Record payments with different statuses
        record_payment(order_id, 500.0, "manual", None)

        # Manually insert a FAILED payment (should not be counted)
        cur.execute("""
            INSERT INTO payments (id, order_id, amount, method, status, reference, created_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, ("FAILED_PAYMENT", order_id, 300.0, "manual", "FAILED", None))
        conn.commit()

        total = get_total_paid(order_id)
        assert total == 500.0  # Only the RECEIVED payment
    
    def test_get_total_paid_no_payments(self, clean_db):
        """Test getting total paid for order with no payments."""
        order_id = "NONEXISTENT_ORDER"
        
        total = get_total_paid(order_id)
        assert total == 0.0
    
    def test_record_payment_creates_timestamp(self, clean_db):
        """Test that payment record includes timestamp."""
        order_id = "TEST_ORDER_123"
        
        payment = record_payment(order_id, 1000.0, "manual", None)
        
        assert payment.created_at is not None
        
        # Verify in database
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT created_at FROM payments WHERE id = ?", (payment.id,))
        result = cur.fetchone()
        conn.close()
        
        assert result[0] is not None

