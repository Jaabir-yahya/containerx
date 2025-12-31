"""
Invariant Tests for ERP Core

Tests that prove ERP invariants are maintained:
- Stock never goes negative
- Partial payments do not move stock
- Failed orders still exist in database
- Events exist for every action
- Replaying payments does not double-deduct stock
- Stock movements are created for every inventory change
"""

import unittest
import os
import tempfile
import shutil
from core.storage.db import init_db, get_db, DB_NAME
from core.services.sales_service import process_retail_sale, apply_payment_to_order
from core.services.inventory_service import verify_stock, adjust_inventory
from core.services.audit_service import log_event

class TestERPInvariants(unittest.TestCase):
    
    def setUp(self):
        """Set up test database before each test."""
        # Backup original DB name
        self.original_db_name = DB_NAME
        # Create temporary database
        self.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.test_db.close()
        
        # Temporarily replace DB_NAME
        import core.storage.db
        core.storage.db.DB_NAME = self.test_db.name
        
        # Initialize test database
        init_db()
        
        # Seed test inventory
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO inventory (sku, quantity) VALUES (?, ?)", ("TEST001", 100))
        cur.execute("INSERT INTO inventory (sku, quantity) VALUES (?, ?)", ("TEST002", 50))
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up test database after each test."""
        import core.storage.db
        core.storage.db.DB_NAME = self.original_db_name
        
        # Remove test database
        if os.path.exists(self.test_db.name):
            os.unlink(self.test_db.name)
    
    def test_stock_never_goes_negative(self):
        """Test that stock never goes negative."""
        # Try to deduct more than available
        with self.assertRaises(ValueError) as context:
            adjust_inventory("TEST001", -150, "test", None)
        
        self.assertIn("negative", str(context.exception).lower())
        
        # Verify stock is unchanged
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM inventory WHERE sku = ?", ("TEST001",))
        result = cur.fetchone()
        conn.close()
        self.assertEqual(result[0], 100)
    
    def test_partial_payments_do_not_move_stock(self):
        """Test that partial payments do not move stock."""
        items = [{"sku": "TEST001", "qty": 10, "price": 100}]
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500,  # Partial payment (total is 1000)
            payment_method="manual"
        )
        
        # Verify stock was NOT deducted
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM inventory WHERE sku = ?", ("TEST001",))
        result = cur.fetchone()
        conn.close()
        self.assertEqual(result[0], 100, "Stock should not be deducted for partial payment")
        
        # Verify order is PENDING
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
        result = cur.fetchone()
        conn.close()
        self.assertEqual(result[0], "PENDING")
    
    def test_failed_orders_still_exist(self):
        """Test that failed orders are still stored in database."""
        items = [{"sku": "NONEXISTENT", "qty": 10, "price": 100}]
        
        # Try to create order with non-existent SKU
        with self.assertRaises(ValueError):
            process_retail_sale(
                customer_identifier="CUSTOMER1",
                items=items,
                payment_amount=1000,
                payment_method="manual"
            )
        
        # Verify FAILED order exists in database
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT status FROM orders WHERE customer_identifier = ?", ("CUSTOMER1",))
        result = cur.fetchone()
        conn.close()
        
        self.assertIsNotNone(result, "Failed order should exist in database")
        self.assertEqual(result[0], "FAILED")
        
        # Verify failed payment exists
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT status FROM payments WHERE order_id IN (SELECT id FROM orders WHERE customer_identifier = ?)", ("CUSTOMER1",))
        payment_result = cur.fetchone()
        conn.close()
        self.assertIsNotNone(payment_result)
        self.assertEqual(payment_result[0], "FAILED")
    
    def test_events_exist_for_every_action(self):
        """Test that events are logged for every critical action."""
        items = [{"sku": "TEST001", "qty": 5, "price": 100}]
        
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500,  # Full payment
            payment_method="manual"
        )
        
        # Check for events
        conn = get_db()
        cur = conn.cursor()
        
        # Should have order created event
        cur.execute("""
            SELECT COUNT(*) FROM event_log 
            WHERE entity_type = 'order' AND entity_id = ? AND action = 'created'
        """, (order_id,))
        order_created = cur.fetchone()[0]
        self.assertGreater(order_created, 0, "Order created event should exist")
        
        # Should have payment recorded event
        cur.execute("""
            SELECT COUNT(*) FROM event_log 
            WHERE entity_type = 'payment' AND entity_id IN (
                SELECT id FROM payments WHERE order_id = ?
            )
        """, (order_id,))
        payment_recorded = cur.fetchone()[0]
        self.assertGreater(payment_recorded, 0, "Payment recorded event should exist")
        
        # Should have inventory adjusted events
        cur.execute("""
            SELECT COUNT(*) FROM event_log 
            WHERE entity_type = 'inventory' AND action = 'adjusted'
        """)
        inventory_adjusted = cur.fetchone()[0]
        self.assertGreater(inventory_adjusted, 0, "Inventory adjusted events should exist")
        
        conn.close()
    
    def test_replaying_payments_does_not_double_deduct(self):
        """Test that replaying the same payment does not double-deduct stock."""
        items = [{"sku": "TEST001", "qty": 10, "price": 100}]
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500,  # Partial payment
            payment_method="manual"
        )
        
        # Get initial stock
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM inventory WHERE sku = ?", ("TEST001",))
        initial_stock = cur.fetchone()[0]
        conn.close()
        
        # Complete payment with reference (simulate M-Pesa callback)
        reference = "MPESA123"
        apply_payment_to_order(order_id, 500, "mpesa", reference)
        
        # Get stock after first completion
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM inventory WHERE sku = ?", ("TEST001",))
        stock_after_first = cur.fetchone()[0]
        conn.close()
        
        # Replay the same payment (idempotency test)
        result = apply_payment_to_order(order_id, 500, "mpesa", reference)
        
        # Get stock after replay
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM inventory WHERE sku = ?", ("TEST001",))
        stock_after_replay = cur.fetchone()[0]
        conn.close()
        
        # Stock should be the same (not double-deducted)
        self.assertEqual(stock_after_first, stock_after_replay, "Stock should not be double-deducted")
        self.assertEqual(stock_after_first, initial_stock - 10, "Stock should be deducted exactly once")
        
        # Verify idempotent message
        self.assertIn("idempotent", result.get("message", "").lower())
    
    def test_stock_movements_created_for_every_inventory_change(self):
        """Test that stock movements are created for every inventory change."""
        initial_count = 0
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stock_movements")
        initial_count = cur.fetchone()[0]
        conn.close()
        
        # Make inventory adjustment
        adjust_inventory("TEST001", -5, "test_adjustment", None)
        
        # Verify stock movement was created
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stock_movements")
        new_count = cur.fetchone()[0]
        conn.close()
        
        self.assertEqual(new_count, initial_count + 1, "Stock movement should be created")
        
        # Verify movement details
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT sku, quantity_change, reason FROM stock_movements 
            ORDER BY created_at DESC LIMIT 1
        """)
        movement = cur.fetchone()
        conn.close()
        
        self.assertIsNotNone(movement)
        self.assertEqual(movement[0], "TEST001")
        self.assertEqual(movement[1], -5)
        self.assertEqual(movement[2], "test_adjustment")
    
    def test_full_payment_deducts_stock(self):
        """Test that full payment deducts stock correctly."""
        items = [{"sku": "TEST001", "qty": 10, "price": 100}]
        
        # Get initial stock
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM inventory WHERE sku = ?", ("TEST001",))
        initial_stock = cur.fetchone()[0]
        conn.close()
        
        # Create order with full payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=1000,  # Full payment
            payment_method="manual"
        )
        
        # Verify stock was deducted
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM inventory WHERE sku = ?", ("TEST001",))
        final_stock = cur.fetchone()[0]
        conn.close()
        
        self.assertEqual(final_stock, initial_stock - 10, "Stock should be deducted for full payment")
        
        # Verify order is COMPLETED
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
        status = cur.fetchone()[0]
        conn.close()
        self.assertEqual(status, "COMPLETED")
    
    def test_completing_partial_payment_deducts_stock(self):
        """Test that completing a partial payment deducts stock."""
        items = [{"sku": "TEST001", "qty": 10, "price": 100}]
        
        # Get initial stock
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM inventory WHERE sku = ?", ("TEST001",))
        initial_stock = cur.fetchone()[0]
        conn.close()
        
        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER1",
            items=items,
            payment_amount=500,  # Partial payment
            payment_method="manual"
        )
        
        # Verify stock was NOT deducted yet
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM inventory WHERE sku = ?", ("TEST001",))
        stock_after_partial = cur.fetchone()[0]
        conn.close()
        self.assertEqual(stock_after_partial, initial_stock, "Stock should not be deducted for partial payment")
        
        # Complete the payment
        apply_payment_to_order(order_id, 500, "manual", None)
        
        # Verify stock was deducted
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT quantity FROM inventory WHERE sku = ?", ("TEST001",))
        final_stock = cur.fetchone()[0]
        conn.close()
        self.assertEqual(final_stock, initial_stock - 10, "Stock should be deducted when payment is completed")

if __name__ == '__main__':
    unittest.main()

