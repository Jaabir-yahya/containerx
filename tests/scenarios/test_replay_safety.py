"""
Scenario tests for replay safety.

Tests that system state is safe after simulated crashes and replays.
"""

import pytest
from core.services.sales_service import process_retail_sale, apply_payment_to_order
from core.storage.db import get_db
from tests.helpers import (
    get_order_status,
    get_total_paid,
    get_inventory_quantity,
    get_stock_movements,
    get_event_log,
    assert_no_negative_stock
)

class TestReplaySafety:
    """Test replay safety after simulated failures."""
    
    def test_replay_after_crash_before_completion(self, clean_db, seeded_inventory):
        """Test replaying payment after crash before order completion."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        initial_stock = get_inventory_quantity("MILK001")
        reference = "MPESA_CRASH"
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,
            payment_method="cash"
        )
        
        # Simulate crash: payment was sent but order not completed
        # Replay the payment
        result = apply_payment_to_order(order_id, 500.0, "mpesa", reference)
        
        # System should be in consistent state
        assert result["status"] == "COMPLETED"
        assert get_inventory_quantity("MILK001") == initial_stock - 10
        assert len(get_stock_movements(order_id=order_id)) == 1
        assert get_total_paid(order_id) == 1000.0
        
        assert_no_negative_stock()
    
    def test_replay_after_partial_crash(self, clean_db, seeded_inventory):
        """Test replay after partial operation crash."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        
        # Create order
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,
            payment_method="cash"
        )
        
        # Simulate: payment recorded but status update failed
        # Replay should complete safely
        result = apply_payment_to_order(order_id, 500.0, "mpesa", "MPESA_REPLAY")
        
        # State should be consistent
        assert result["status"] == "COMPLETED"
        assert get_total_paid(order_id) == 1000.0
    
    def test_replay_creates_audit_trail(self, clean_db, seeded_inventory):
        """Test that replays create proper audit trail."""
        items = [{"sku": "MILK001", "qty": 10, "price": 100}]
        reference = "MPESA_AUDIT"
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,
            payment_method="cash"
        )
        
        # Replay payment
        apply_payment_to_order(order_id, 500.0, "mpesa", reference)
        
        # Verify events logged
        events = get_event_log(entity_type="order", entity_id=order_id)
        assert len(events) >= 2  # created and completed
        
        # Verify payment events
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM payments WHERE order_id = ? AND reference = ?", (order_id, reference))
        payment_id = cur.fetchone()[0]
        conn.close()
        
        payment_events = get_event_log(entity_type="payment", entity_id=payment_id)
        assert len(payment_events) > 0
    
    def test_state_consistency_after_replay(self, clean_db, seeded_inventory):
        """Test that system state is consistent after replay."""
        items = [
            {"sku": "MILK001", "qty": 5, "price": 100},
            {"sku": "BREAD001", "qty": 2, "price": 50}
        ]
        initial_milk = get_inventory_quantity("MILK001")
        initial_bread = get_inventory_quantity("BREAD001")
        reference = "MPESA_CONSISTENCY"
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=300.0,
            payment_method="cash"
        )
        
        # Replay to complete
        apply_payment_to_order(order_id, 400.0, "mpesa", reference)
        
        # Verify all invariants hold
        assert get_order_status(order_id) == "COMPLETED"
        assert get_total_paid(order_id) == 700.0  # 300 + 400
        assert get_inventory_quantity("MILK001") == initial_milk - 5
        assert get_inventory_quantity("BREAD001") == initial_bread - 2
        
        # Verify stock movements
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 2  # One per SKU
        
        assert_no_negative_stock()

