"""
Integration tests for complete retail sale flow.

Tests end-to-end retail sale processing with real database and services.
"""

import pytest
from core.services.sales_service import process_retail_sale
from tests.helpers import (
    get_order_status,
    get_total_paid,
    get_inventory_quantity,
    get_stock_movements,
    get_event_log,
    assert_no_negative_stock
)

class TestRetailFlow:
    """Test complete retail sale flows."""
    
    def test_complete_retail_sale_flow(self, clean_db, seeded_inventory):
        """Test complete retail sale from start to finish."""
        items = [
            {"sku": "MILK001", "qty": 5, "price": 100},
            {"sku": "BREAD001", "qty": 2, "price": 50}
        ]
        initial_milk = get_inventory_quantity("MILK001")
        initial_bread = get_inventory_quantity("BREAD001")
        
        # Process sale
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=600.0,  # Full payment (5*100 + 2*50 = 600)
            payment_method="cash"
        )
        
        # Verify order
        status = get_order_status(order_id)
        assert status == "COMPLETED"
        
        # Verify payment
        total_paid = get_total_paid(order_id)
        assert total_paid == 600.0
        
        # Verify stock deducted
        assert get_inventory_quantity("MILK001") == initial_milk - 5
        assert get_inventory_quantity("BREAD001") == initial_bread - 2
        
        # Verify stock movements
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 2  # One for each SKU
        
        # Verify events logged
        events = get_event_log(entity_type="order", entity_id=order_id)
        assert len(events) >= 2  # created and completed
        
        # Verify no negative stock
        assert_no_negative_stock()
    
    def test_retail_sale_with_multiple_items(self, clean_db, seeded_inventory):
        """Test retail sale with multiple different items."""
        items = [
            {"sku": "MILK001", "qty": 10, "price": 100},
            {"sku": "BREAD001", "qty": 5, "price": 50},
            {"sku": "EGGS001", "qty": 20, "price": 10}
        ]
        
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=2500.0,  # Full payment
            payment_method="mpesa",
            payment_reference="MPESA123"
        )
        
        # Verify all items deducted
        assert get_inventory_quantity("MILK001") == 90
        assert get_inventory_quantity("BREAD001") == 45
        assert get_inventory_quantity("EGGS001") == 180
        
        # Verify stock movements for all items
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 3
    
    def test_retail_sale_overpayment(self, clean_db, seeded_inventory):
        """Test retail sale with overpayment."""
        items = [{"sku": "MILK001", "qty": 5, "price": 100}]
        
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=600.0,  # Overpayment (total is 500)
            payment_method="cash"
        )
        
        # Order should still be completed
        assert get_order_status(order_id) == "COMPLETED"
        
        # Stock should be deducted
        assert get_inventory_quantity("MILK001") == 95
        
        # Total paid should be recorded
        assert get_total_paid(order_id) == 600.0

