"""
Integration tests for partial payment flows.

Tests partial payment scenarios and completion.
"""

import pytest
from core.services.sales_service import process_retail_sale, apply_payment_to_order
from tests.helpers import (
    get_order_status,
    get_total_paid,
    get_inventory_quantity,
    get_stock_movements,
    assert_no_negative_stock
)

class TestPartialPayments:
    """Test partial payment scenarios."""
    
    def test_partial_payment_flow(self, clean_db, seeded_inventory):
        """Test complete partial payment flow."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,  # 50% payment
            payment_method="cash"
        )
        
        # Verify order is PENDING
        assert get_order_status(order_id) == "PENDING"
        assert get_total_paid(order_id) == 500.0
        
        # Verify stock NOT deducted
        assert get_inventory_quantity("MILK001") == initial_stock
        
        # Complete payment
        result = apply_payment_to_order(order_id, 500.0, "mpesa", "MPESA123")
        
        # Verify order completed
        assert result["status"] == "COMPLETED"
        assert get_order_status(order_id) == "COMPLETED"
        assert get_total_paid(order_id) == 1000.0
        
        # Verify stock now deducted
        assert get_inventory_quantity("MILK001") == initial_stock - 10
        
        # Verify stock movement created
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 1
        
        assert_no_negative_stock()
    
    def test_multiple_partial_payments(self, clean_db, seeded_inventory):
        """Test order with multiple partial payments."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        
        # Create order with first partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=300.0,
            payment_method="cash"
        )
        
        assert get_order_status(order_id) == "PENDING"
        assert get_total_paid(order_id) == 300.0
        
        # Second partial payment
        apply_payment_to_order(order_id, 400.0, "mpesa", "MPESA1")
        assert get_order_status(order_id) == "PENDING"
        assert get_total_paid(order_id) == 700.0
        
        # Final payment completes order
        result = apply_payment_to_order(order_id, 300.0, "cash", None)
        assert result["status"] == "COMPLETED"
        assert get_total_paid(order_id) == 1000.0
        
        # Stock should be deducted only once
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 1
    
    def test_partial_payment_stock_not_deducted(self, clean_db, seeded_inventory):
        """Test that partial payments do not deduct stock."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=999.0,  # Almost full, but still partial
            payment_method="cash"
        )
        
        # Verify stock NOT deducted
        assert get_inventory_quantity("MILK001") == initial_stock
        
        # Verify no stock movements
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 0
    
    def test_partial_payment_then_cancel(self, clean_db, seeded_inventory):
        """Test that partial payment order can remain pending."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,
            payment_method="cash"
        )
        
        # Order remains pending, stock not deducted
        assert get_order_status(order_id) == "PENDING"
        assert get_inventory_quantity("MILK001") == initial_stock
        
        # Even after time passes, stock should not be deducted
        # (In real system, might have timeout/cancellation logic)
        assert get_inventory_quantity("MILK001") == initial_stock

