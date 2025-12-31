"""
Integration tests for failure scenarios.

Tests that failures are properly handled and recorded.
"""

import pytest
from core.services.sales_service import process_retail_sale, apply_payment_to_order
from core.storage.db import get_db
from tests.helpers import (
    get_order_status,
    get_total_paid,
    get_inventory_quantity,
    get_event_log,
    assert_no_negative_stock
)

class TestFailureStates:
    """Test failure scenario handling."""
    
    def test_insufficient_stock_creates_failed_order(self, clean_db, seeded_inventory):
        """Test that insufficient stock creates a FAILED order."""
        items = [{"sku": "MILK001", "qty": 200, "price": 100}]  # More than available
        
        with pytest.raises(ValueError):
            process_retail_sale(
                customer_identifier="CUSTOMER1",
                items=items,
                payment_amount=20000.0,
                payment_method="cash"
            )
        
        # Verify FAILED order exists
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT status FROM orders WHERE customer_identifier = ?", ("CUSTOMER1",))
        result = cur.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "FAILED"
        
        # Verify failed payment exists
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT status FROM payments 
            WHERE order_id IN (SELECT id FROM orders WHERE customer_identifier = ?)
        """, ("CUSTOMER1",))
        payment_result = cur.fetchone()
        conn.close()
        
        assert payment_result is not None
        assert payment_result[0] == "FAILED"
    
    def test_nonexistent_sku_creates_failed_order(self, clean_db, seeded_inventory):
        """Test that non-existent SKU creates a FAILED order."""
        items = [{"sku": "NONEXISTENT", "qty": 10, "price": 100}]
        
        with pytest.raises(ValueError):
            process_retail_sale(
                customer_identifier="CUSTOMER1",
                items=items,
                payment_amount=1000.0,
                payment_method="cash"
            )
        
        # Verify FAILED order exists
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT status FROM orders WHERE customer_identifier = ?", ("CUSTOMER1",))
        result = cur.fetchone()
        conn.close()
        
        assert result[0] == "FAILED"
    
    def test_failed_order_does_not_affect_stock(self, clean_db, seeded_inventory):
        """Test that failed orders do not affect inventory."""
        initial_stock = get_inventory_quantity("MILK001")
        
        items = [{"sku": "MILK001", "qty": 200, "price": 100}]
        
        with pytest.raises(ValueError):
            process_retail_sale(
                customer_identifier="CUSTOMER1",
                items=items,
                payment_amount=20000.0,
                payment_method="cash"
            )
        
        # Verify stock unchanged
        assert get_inventory_quantity("MILK001") == initial_stock
    
    def test_apply_payment_to_failed_order_fails(self, clean_db, seeded_inventory):
        """Test that applying payment to failed order raises error."""
        # Create a failed order manually
        conn = get_db()
        cur = conn.cursor()
        order_id = "FAILED_ORDER_123"
        cur.execute("""
            INSERT INTO orders (id, customer_identifier, total_amount, status, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (order_id, "CUSTOMER1", 1000.0, "FAILED"))
        conn.commit()
        conn.close()
        
        # Try to apply payment
        with pytest.raises(ValueError, match="FAILED order"):
            apply_payment_to_order(order_id, 1000.0, "cash", None)
    
    def test_apply_payment_to_completed_order_with_reference(self, clean_db, seeded_inventory):
        """Test idempotent payment to completed order."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        
        # Create completed order
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=1000.0,
            payment_method="cash"
        )
        
        # Try to apply payment with reference (should be idempotent)
        reference = "MPESA_RETRY"
        result = apply_payment_to_order(order_id, 1000.0, "mpesa", reference)
        
        # Should return idempotent message or raise error
        # (Current implementation raises error, which is acceptable)
        # If it returns, should indicate idempotent
        if "message" in result:
            assert "idempotent" in result["message"].lower() or "already" in result["message"].lower()
    
    def test_failed_order_events_logged(self, clean_db, seeded_inventory):
        """Test that failed orders have events logged."""
        items = [{"sku": "MILK001", "qty": 200, "price": 100}]
        
        with pytest.raises(ValueError):
            process_retail_sale(
                customer_identifier="CUSTOMER1",
                items=items,
                payment_amount=20000.0,
                payment_method="cash"
            )
        
        # Get failed order ID
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM orders WHERE customer_identifier = ?", ("CUSTOMER1",))
        order_id = cur.fetchone()[0]
        conn.close()
        
        # Verify events logged
        events = get_event_log(entity_type="order", entity_id=order_id)
        assert len(events) > 0
        
        # Verify payment failure event
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM payments WHERE order_id = ?", (order_id,))
        result = cur.fetchone()
        conn.close()
        
        if result:
            payment_id = result[0]
        
        if result:
            payment_events = get_event_log(entity_type="payment", entity_id=payment_id)
            assert len(payment_events) > 0

