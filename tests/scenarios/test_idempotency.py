"""
Scenario tests for idempotency.

Tests that operations can be safely retried without side effects.
"""

import pytest
from core.services.sales_service import process_retail_sale, apply_payment_to_order
from tests.helpers import (
    get_order_status,
    get_total_paid,
    get_inventory_quantity,
    get_stock_movements,
    get_event_log,
    assert_no_negative_stock
)

class TestIdempotency:
    """Test idempotency of operations."""
    
    def test_payment_replay_same_reference(self, clean_db, seeded_inventory):
        """Test replaying payment with same reference is idempotent."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        reference = "MPESA_ABC123"
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,
            payment_method="cash"
        )
        
        # Apply payment with reference
        result1 = apply_payment_to_order(order_id, 500.0, "mpesa", reference)
        stock_after_first = get_inventory_quantity("MILK001")
        movements_after_first = len(get_stock_movements(order_id=order_id))
        
        # Replay same payment (simulate M-Pesa callback retry)
        result2 = apply_payment_to_order(order_id, 500.0, "mpesa", reference)
        stock_after_second = get_inventory_quantity("MILK001")
        movements_after_second = len(get_stock_movements(order_id=order_id))
        
        # Verify no double deduction
        assert stock_after_first == stock_after_second
        assert stock_after_first == initial_stock - 10
        assert movements_after_first == movements_after_second == 1
        
        # Verify idempotent response
        assert "idempotent" in result2.get("message", "").lower()
        
        # Verify total paid is correct (not doubled)
        assert get_total_paid(order_id) == 1000.0
        
        assert_no_negative_stock()
    
    def test_payment_replay_different_reference(self, clean_db, seeded_inventory):
        """Test that different references create separate payments."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,
            payment_method="cash"
        )
        
        # Apply payment with first reference
        apply_payment_to_order(order_id, 300.0, "mpesa", "MPESA_REF1")
        assert get_total_paid(order_id) == 800.0
        
        # Apply payment with different reference (should be accepted)
        apply_payment_to_order(order_id, 200.0, "mpesa", "MPESA_REF2")
        assert get_total_paid(order_id) == 1000.0
        assert get_order_status(order_id) == "COMPLETED"
    
    def test_multiple_retries_same_reference(self, clean_db, seeded_inventory):
        """Test multiple retries with same reference."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        reference = "MPESA_RETRY"
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,
            payment_method="cash"
        )
        
        # Retry payment multiple times
        for i in range(5):
            result = apply_payment_to_order(order_id, 500.0, "mpesa", reference)
            stock = get_inventory_quantity("MILK001")
            movements = len(get_stock_movements(order_id=order_id))
            
            # Stock should be deducted only once
            assert stock == initial_stock - 10
            assert movements == 1
            assert get_total_paid(order_id) == 1000.0
    
    def test_concurrent_payment_attempts(self, clean_db, seeded_inventory):
        """Test handling of concurrent payment attempts with same reference."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        reference = "MPESA_CONCURRENT"
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,
            payment_method="cash"
        )
        
        # Simulate concurrent attempts (sequential in test, but same scenario)
        results = []
        for _ in range(3):
            try:
                result = apply_payment_to_order(order_id, 500.0, "mpesa", reference)
                results.append(result)
            except Exception as e:
                results.append(str(e))
        
        # At least one should succeed, others should be idempotent
        successful = [r for r in results if isinstance(r, dict) and r.get("status") == "COMPLETED"]
        assert len(successful) >= 1
        
        # Verify stock deducted only once
        assert get_inventory_quantity("MILK001") == initial_stock - 10
        assert len(get_stock_movements(order_id=order_id)) == 1

