"""
Unit tests for sales service.

Tests sales service operations in isolation.
"""

import pytest
from core.services.sales_service import process_retail_sale, apply_payment_to_order
from tests.helpers import (
    get_order_status,
    get_total_paid,
    get_inventory_quantity,
    get_stock_movements
)
from core.storage.db import get_db
from tests.helpers import (
    get_order_status,
    get_total_paid,
    get_inventory_quantity,
    get_stock_movements,
    assert_event_exists,
    assert_no_negative_stock
)

class TestSalesService:
    """Test sales service operations."""
    
    def test_process_retail_sale_full_payment(self, clean_db):
        """Test processing retail sale with full payment."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=1000.0,
            payment_method="manual"
        )
        
        # Verify order was created
        status = get_order_status(order_id)
        assert status == "COMPLETED"
        
        # Verify stock was deducted
        final_stock = get_inventory_quantity("MILK001")
        assert final_stock == initial_stock - 10
        
        # Verify stock movement was created
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 1
        assert movements[0]["quantity_change"] == -10
        
        # Verify events were logged
        assert_event_exists("order", order_id, "created")
        assert_event_exists("order", order_id, "completed")
    
    def test_process_retail_sale_partial_payment(self, clean_db):
        """Test processing retail sale with partial payment."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,  # Partial payment
            payment_method="manual"
        )
        
        # Verify order is PENDING
        status = get_order_status(order_id)
        assert status == "PENDING"
        assert get_total_paid(order_id) == 500.0

        # Verify stock was NOT deducted
        final_stock = get_inventory_quantity("MILK001")
        assert final_stock == initial_stock
        
        # Verify no stock movements for this order
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 0
    
    def test_process_retail_sale_insufficient_stock(self, clean_db):
        """Test processing retail sale with insufficient stock."""
        items = [{"sku": "MILK001", "qty": 200, "price": 100}]  # More than available
        
        with pytest.raises(ValueError, match="Stock check failed"):
            process_retail_sale(
                customer_identifier="CUSTOMER1",
                items=items,
                payment_amount=20000.0,
                payment_method="manual"
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
        result = cur.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == "FAILED"
    
    def test_apply_payment_to_order_completes_order(self, clean_db):
        """Test applying payment to complete a partial order."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,
            payment_method="manual"
        )
        
        # Apply remaining payment
        result = apply_payment_to_order(order_id, 500.0, "manual", None)
        
        # Verify order is completed
        assert result["status"] == "COMPLETED"
        assert get_order_status(order_id) == "COMPLETED"
        
        # Verify stock was deducted
        final_stock = get_inventory_quantity("MILK001")
        assert final_stock == initial_stock - 10
        
        # Verify stock movement was created
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 1
    
    def test_apply_payment_to_order_idempotent(self, clean_db):
        """Test that applying payment with same reference is idempotent."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        reference = "MPESA_ABC123"
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,
            payment_method="manual"
        )
        
        # Apply payment with reference
        result1 = apply_payment_to_order(order_id, 500.0, "mpesa", reference)
        stock_after_first = get_inventory_quantity("MILK001")
        
        # Apply same payment again (simulate retry)
        result2 = apply_payment_to_order(order_id, 500.0, "mpesa", reference)
        stock_after_second = get_inventory_quantity("MILK001")
        
        # Verify stock was not double-deducted
        assert stock_after_first == stock_after_second
        assert stock_after_first == initial_stock - 10
        
        # Verify idempotent message
        assert "idempotent" in result2.get("message", "").lower()
        
        # Verify only one stock movement
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 1

