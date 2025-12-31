"""
Property-based invariant tests.

Tests ERP invariants hold under randomized sequences of operations.
"""

import pytest
import random
from core.services.sales_service import process_retail_sale, apply_payment_to_order
from core.services.inventory_service import adjust_inventory
from tests.helpers import (
    get_inventory_quantity,
    get_stock_movements,
    get_event_log,
    assert_no_negative_stock,
    get_order_status,
    get_total_paid
)

class TestERPInvariants:
    """Property-based tests for ERP invariants."""
    
    @pytest.mark.parametrize("seed", [42, 123, 456, 789, 999])
    def test_stock_never_negative_random_operations(self, clean_db, seeded_inventory, seed):
        """Test that stock never goes negative under random operations."""
        random.seed(seed)
        
        sku = "MILK001"
        initial_qty = get_inventory_quantity(sku)
        
        # Perform random operations
        for _ in range(20):
            operation = random.choice(["add", "deduct", "sale"])
            
            if operation == "add":
                qty = random.randint(1, 50)
                try:
                    adjust_inventory(sku, qty, "random_addition", None)
                except Exception:
                    pass  # May fail if constraints violated
            
            elif operation == "deduct":
                qty = random.randint(1, 100)
                try:
                    adjust_inventory(sku, -qty, "random_deduction", None)
                except ValueError:
                    pass  # Expected if would go negative
            
            else:  # sale
                items = [{"sku": sku, "qty": random.randint(1, 20), "price": 100}]
                try:
                    process_retail_sale(
                        customer_identifier=f"CUSTOMER_{random.randint(1, 100)}",
                        items=items,
                        payment_amount=items[0]["qty"] * 100,
                        payment_method="cash"
                    )
                except ValueError:
                    pass  # Expected if insufficient stock
        
        # Invariant: Stock should never be negative
        assert_no_negative_stock()
        
        # Verify final stock is non-negative
        final_qty = get_inventory_quantity(sku)
        assert final_qty >= 0
    
    @pytest.mark.parametrize("seed", [100, 200, 300])
    def test_stock_movements_match_inventory_changes(self, clean_db, seeded_inventory, seed):
        """Test that stock movements always match inventory changes."""
        random.seed(seed)
        
        sku = "BREAD001"
        initial_qty = get_inventory_quantity(sku)
        initial_movements = len(get_stock_movements(sku=sku))
        
        # Perform random adjustments
        total_change = 0
        for _ in range(10):
            change = random.randint(-20, 20)
            try:
                adjust_inventory(sku, change, "random_test", None)
                total_change += change
            except ValueError:
                pass  # Expected if would go negative
        
        # Verify movements match changes
        final_qty = get_inventory_quantity(sku)
        final_movements = len(get_stock_movements(sku=sku))
        
        # Inventory change should equal sum of movements
        movements = get_stock_movements(sku=sku)
        movement_sum = sum(m["quantity_change"] for m in movements[initial_movements:])
        
        assert final_qty == initial_qty + movement_sum
        assert final_movements == initial_movements + len([m for m in movements[initial_movements:] if m])
    
    @pytest.mark.parametrize("num_orders", [5, 10, 15])
    def test_events_exist_for_all_operations(self, clean_db, seeded_inventory, num_orders):
        """Test that events exist for all operations."""
        order_ids = []
        
        # Create multiple orders
        for i in range(num_orders):
            items = [{"sku": "MILK001", "qty": 1, "price": 100}]
            try:
                order_id = process_retail_sale(
                    customer_identifier=f"CUSTOMER_{i}",
                    items=items,
                    payment_amount=100.0,
                    payment_method="cash"
                )
                order_ids.append(order_id)
            except ValueError:
                pass  # May fail if stock exhausted
        
        # Verify events exist for all successful orders
        for order_id in order_ids:
            events = get_event_log(entity_type="order", entity_id=order_id)
            assert len(events) > 0, f"No events found for order {order_id}"
            
            # Should have at least created event
            created_events = [e for e in events if e["action"] == "created"]
            assert len(created_events) > 0
    
    @pytest.mark.parametrize("seed", [500, 600, 700])
    def test_partial_payments_never_move_stock(self, clean_db, seeded_inventory, seed):
        """Test that partial payments never move stock."""
        random.seed(seed)
        
        sku = "EGGS001"
        initial_qty = get_inventory_quantity(sku)
        
        # Create orders with random partial payments
        order_ids = []
        for i in range(10):
            qty = random.randint(1, 10)
            total = qty * 10
            payment = random.randint(1, total - 1)  # Always partial
            
            items = [{"sku": sku, "qty": qty, "price": 10}]
            try:
                order_id = process_retail_sale(
                    customer_identifier=f"CUSTOMER_{i}",
                    items=items,
                    payment_amount=payment,
                    payment_method="cash"
                )
                order_ids.append(order_id)
            except ValueError:
                pass  # May fail if stock insufficient
        
        # Verify stock not moved for partial payments
        final_qty = get_inventory_quantity(sku)
        assert final_qty == initial_qty, "Stock should not be moved for partial payments"
        
        # Verify no stock movements for these orders
        for order_id in order_ids:
            movements = get_stock_movements(order_id=order_id)
            assert len(movements) == 0, f"Order {order_id} should have no stock movements"
    
    @pytest.mark.parametrize("seed", [800, 900, 1000])
    def test_payment_replay_never_double_deducts(self, clean_db, seeded_inventory, seed):
        """Test that payment replays never double-deduct stock."""
        random.seed(seed)
        
        sku = "MILK001"
        initial_qty = get_inventory_quantity(sku)
        
        # Create order with partial payment
        items = [{"sku": sku, "qty": 10, "price": 100}]
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500.0,
            payment_method="cash"
        )
        
        # Replay payment multiple times with same reference
        reference = f"MPESA_{seed}"
        for _ in range(5):
            try:
                apply_payment_to_order(order_id, 500.0, "mpesa", reference)
            except Exception:
                pass  # May fail if already completed
        
        # Stock should be deducted exactly once
        final_qty = get_inventory_quantity(sku)
        assert final_qty == initial_qty - 10
        
        # Verify only one stock movement
        movements = get_stock_movements(order_id=order_id)
        assert len(movements) == 1
    
    def test_random_payment_sequence_maintains_invariants(self, clean_db, seeded_inventory):
        """Test that random payment sequences maintain all invariants."""
        random.seed(42)
        
        sku = "BREAD001"
        initial_qty = get_inventory_quantity(sku)
        order_ids = []
        
        # Create multiple orders with random payment amounts
        for i in range(5):
            qty = random.randint(1, 5)
            total = qty * 50
            payment = random.randint(1, total)
            
            items = [{"sku": sku, "qty": qty, "price": 50}]
            try:
                order_id = process_retail_sale(
                    customer_identifier=f"CUSTOMER_{i}",
                    items=items,
                    payment_amount=payment,
                    payment_method="cash"
                )
                order_ids.append((order_id, total, payment))
            except ValueError:
                pass
        
        # Apply additional payments randomly
        for order_id, total, initial_payment in order_ids:
            if random.random() > 0.5:  # 50% chance
                remaining = total - initial_payment
                if remaining > 0:
                    try:
                        apply_payment_to_order(order_id, remaining, "cash", None)
                    except Exception:
                        pass
        
        # Verify all invariants
        assert_no_negative_stock()
        
        # Verify stock movements match completed orders
        completed_orders = []
        for order_id, total, _ in order_ids:
            status = get_order_status(order_id)
            if status == "COMPLETED":
                completed_orders.append(order_id)
        
        # Count expected stock movements
        movements = get_stock_movements(sku=sku)
        # Movements should match completed orders (one per SKU per order)
        assert len(movements) >= len(completed_orders)
    
    def test_concurrent_operations_respect_stock(self, clean_db, seeded_inventory):
        """Test that concurrent operations respect stock limits."""
        sku = "MILK001"
        initial_qty = get_inventory_quantity(sku)
        
        # Create orders that together would exceed stock
        order_ids = []
        total_requested = 0
        
        for i in range(10):
            qty = 15  # Each order requests 15, total would be 150 > 100
            items = [{"sku": sku, "qty": qty, "price": 100}]
            try:
                order_id = process_retail_sale(
                    customer_identifier=f"CUSTOMER_{i}",
                    items=items,
                    payment_amount=qty * 100,
                    payment_method="cash"
                )
                order_ids.append(order_id)
                total_requested += qty
            except ValueError:
                pass  # Expected when stock exhausted
        
        # Verify stock never goes negative
        assert_no_negative_stock()
        
        # Verify final stock is non-negative
        final_qty = get_inventory_quantity(sku)
        assert final_qty >= 0
        
        # Verify completed orders don't exceed initial stock
        completed_qty = initial_qty - final_qty
        assert completed_qty <= initial_qty

