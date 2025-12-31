"""
Scenario tests for double execution safety.

Tests that operations are safe when executed multiple times.
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

class TestDoubleExecution:
    """Test safety of double execution scenarios."""
    
    def test_double_payment_same_amount(self, clean_db, seeded_inventory):
        """Test applying same payment amount twice."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,
            payment_method="cash"
        )
        
        # Apply payment twice (no reference)
        apply_payment_to_order(order_id, 500.0, "cash", None)
        stock_after_first = get_inventory_quantity("MILK001")
        
        # Try to apply again (should complete or be idempotent)
        try:
            result = apply_payment_to_order(order_id, 500.0, "cash", None)
            # If it succeeds, should be idempotent or complete
            stock_after_second = get_inventory_quantity("MILK001")
            assert stock_after_first == stock_after_second
        except ValueError as e:
            # If it fails, should be because order is already completed
            assert "COMPLETED" in str(e) or "already" in str(e).lower()
            stock_after_second = get_inventory_quantity("MILK001")
            assert stock_after_first == stock_after_second
        
        # Stock should be deducted only once
        assert stock_after_first == initial_stock - 10
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 1
    
    def test_double_completion_attempt(self, clean_db, seeded_inventory):
        """Test attempting to complete order twice."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        
        # Create and complete order
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=1000.0,
            payment_method="cash"
        )
        
        stock_after_completion = get_inventory_quantity("MILK001")
        movements_after_completion = len(get_stock_movements(order_id=order_id))
        
        # Try to complete again (should fail or be no-op)
        try:
            result = apply_payment_to_order(order_id, 0.0, "cash", None)
            # Should indicate already completed
            assert result.get("status") == "COMPLETED"
        except ValueError as e:
            # Should fail with appropriate message
            assert "COMPLETED" in str(e) or "already" in str(e).lower()
        
        # Stock should not change
        assert get_inventory_quantity("MILK001") == stock_after_completion
        assert len(get_stock_movements(order_id=order_id)) == movements_after_completion
    
    def test_out_of_order_payments(self, clean_db, seeded_inventory):
        """Test payments applied out of order."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=200.0,
            payment_method="cash"
        )
        
        # Apply payments out of order
        apply_payment_to_order(order_id, 500.0, "mpesa", "MPESA1")
        apply_payment_to_order(order_id, 300.0, "cash", None)
        
        # Order should be completed
        assert get_order_status(order_id) == "COMPLETED"
        assert get_total_paid(order_id) == 1000.0
        
        # Stock should be deducted only once
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 1
    
    def test_concurrent_orders_same_sku(self, clean_db, seeded_inventory):
        """Test concurrent orders for same SKU respect stock limits."""
        items1 = [{"sku": "MILK001", "qty": 60, "price": 100}]
        items2 = [{"sku": "MILK001", "qty": 50, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")  # Should be 100
        
        # Create first order (should succeed)
        order_id1 = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items1,
            payment_amount=6000.0,
            payment_method="cash"
        )
        
        stock_after_first = get_inventory_quantity("MILK001")
        assert stock_after_first == initial_stock - 60
        
        # Create second order (should succeed, 50 <= 40 remaining)
        order_id2 = process_retail_sale(
            customer_identifier="CUSTOMER2",
            items=items2,
            payment_amount=5000.0,
            payment_method="cash"
        )
        
        stock_after_second = get_inventory_quantity("MILK001")
        assert stock_after_second == initial_stock - 60 - 50
        
        # Try to create third order that would exceed stock
        items3 = [{"sku": "MILK001", "qty": 1, "price": 100}]
        with pytest.raises(ValueError, match="Stock check failed"):
            process_retail_sale(
                customer_identifier="CUSTOMER3",
                items=items3,
                payment_amount=100.0,
                payment_method="cash"
            )
        
        assert_no_negative_stock()

