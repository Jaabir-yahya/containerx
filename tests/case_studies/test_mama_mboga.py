"""
🇰🇪 Case Study: Mama Mboga Vegetable Vendor

**Business Profile:**
- Location: Westlands Market, Nairobi
- Business: Fresh produce retail (vegetables, fruits)
- Daily turnover: KES 15,000-25,000
- Peak hours: 6AM-2PM market time
- Challenges: Perishable stock, cash flow, M-Pesa reconciliation

**Customer Journey:**
1. Customer selects fresh produce
2. Mama Mboga weighs and calculates price
3. Customer pays via M-Pesa or cash
4. Receipt generated for customer
5. Stock levels updated automatically

**Test Scenarios:**
- Cash payment flow
- M-Pesa payment flow
- Mixed payment (cash + M-Pesa)
- Insufficient stock handling
- Spoilage write-offs
- End-of-day reconciliation
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime

class TestMamaMbogaWorkflow:
    """
    Test complete workflow for Mama Mboga vegetable vendor.
    Validates ERP core handles typical Nairobi retail scenarios.
    """

    @pytest.fixture(scope="class")
    def mama_mboga_business(self):
        """
        Setup Mama Mboga's business data and initial inventory.
        Represents a real Nairobi vegetable vendor.
        """
        # Create business database
        db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        db_path = db_file.name
        db_file.close()

        conn = sqlite3.connect(db_path)

        # Initialize schema
        self._init_business_schema(conn)

        # Seed Mama Mboga's inventory (typical Nairobi vegetable vendor)
        self._seed_mama_mboga_inventory(conn)

        # Override get_db for this test class
        import core.storage.db
        core.storage.db.set_db_override(conn)

        yield conn

        # Cleanup
        core.storage.db.clear_db_override()
        if os.path.exists(db_path):
            os.unlink(db_path)

    def _init_business_schema(self, conn):
        """Initialize ERP schema for business testing."""
        cur = conn.cursor()

        # Create all necessary tables
        cur.execute("""
        CREATE TABLE orders (
            id TEXT PRIMARY KEY,
            customer_identifier TEXT,
            total_amount REAL,
            status TEXT,
            created_at TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE payments (
            id TEXT PRIMARY KEY,
            order_id TEXT,
            amount REAL,
            method TEXT,
            status TEXT,
            reference TEXT,
            created_at TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE inventory (
            sku TEXT PRIMARY KEY,
            quantity INTEGER
        )
        """)

        cur.execute("""
        CREATE TABLE stock_movements (
            id TEXT PRIMARY KEY,
            sku TEXT NOT NULL,
            quantity_change INTEGER NOT NULL,
            reason TEXT NOT NULL,
            related_order_id TEXT,
            created_at TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE event_log (
            id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE order_items (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            sku TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """)

        conn.commit()

    def _seed_mama_mboga_inventory(self, conn):
        """
        Seed inventory for Mama Mboga's vegetable stall.
        Based on typical Nairobi market vendor inventory.
        """
        cur = conn.cursor()

        # Fresh produce inventory (typical for Nairobi vegetable vendor)
        inventory = {
            # Vegetables (in kg)
            "TOMATOES": 25,    # Fresh tomatoes
            "ONIONS": 30,      # Red onions
            "SPINACH": 15,     # Sukuma wiki
            "CABBAGE": 8,      # Whole cabbages
            "CARROTS": 20,     # Carrots
            "GREEN_PEPPER": 12, # Hoho (capsicum)
            "POTATOES": 40,    # Irish potatoes

            # Fruits (in kg)
            "BANANAS": 35,     # Cooking bananas
            "ORANGES": 18,     # Local oranges
            "PINEAPPLES": 6,   # Whole pineapples

            # Other items
            "EGGS": 120,       # Tray of eggs (30 eggs/tray)
            "MILK": 24,        # Liters of milk
        }

        for sku, quantity in inventory.items():
            cur.execute(
                "INSERT INTO inventory (sku, quantity) VALUES (?, ?)",
                (sku, quantity)
            )

        conn.commit()

    def test_morning_setup_verification(self, mama_mboga_business):
        """
        Test morning inventory setup and verification.
        Mama Mboga checks stock levels before opening.
        """
        from core.services.inventory_service import verify_stock

        # Test stock verification for popular items
        assert verify_stock("TOMATOES", 5) == True  # Can sell 5kg tomatoes
        assert verify_stock("SPINACH", 2) == True   # Can sell 2kg sukuma wiki
        assert verify_stock("BANANAS", 10) == True  # Can sell 10 bunches

        # Test insufficient stock
        assert verify_stock("CABBAGE", 10) == False  # Only has 8 cabbages

    def test_cash_customer_journey(self, mama_mboga_business):
        """
        Test complete customer journey with cash payment.
        Represents typical Nairobi market customer.
        """
        from core.services.sales_service import process_retail_sale
        from core.services.inventory_service import get_inventory_quantity

        # Customer buys: 2kg tomatoes, 1kg spinach, 3kg bananas
        items = [
            {"sku": "TOMATOES", "qty": 2, "price": 120},  # KES 120/kg
            {"sku": "SPINACH", "qty": 1, "price": 80},    # KES 80/kg
            {"sku": "BANANAS", "qty": 3, "price": 60},    # KES 60/kg
        ]

        # Calculate expected total: (2*120) + (1*80) + (3*60) = 240 + 80 + 180 = KES 500
        expected_total = 500

        # Record initial stock levels
        initial_tomatoes = get_inventory_quantity("TOMATOES")
        initial_spinach = get_inventory_quantity("SPINACH")
        initial_bananas = get_inventory_quantity("BANANAS")

        # Process sale with cash payment
        order_id = process_retail_sale(
            customer_identifier="CUSTOMER_001",
            items=items,
            payment_amount=expected_total,
            payment_method="cash"
        )

        # Verify order was created and completed
        assert order_id is not None

        # Verify stock was deducted
        assert get_inventory_quantity("TOMATOES") == initial_tomatoes - 2
        assert get_inventory_quantity("SPINACH") == initial_spinach - 1
        assert get_inventory_quantity("BANANAS") == initial_bananas - 3

        # Verify order status (would need helper function)
        # assert get_order_status(order_id) == "COMPLETED"

    def test_mpesa_customer_journey(self, mama_mboga_business):
        """
        Test customer journey with M-Pesa payment.
        Critical for Nairobi retail - most customers use mobile money.
        """
        from core.services.sales_service import process_retail_sale, apply_payment_to_order
        from core.services.inventory_service import get_inventory_quantity

        # Customer buys: 1kg onions, 2kg carrots, 1 dozen eggs
        items = [
            {"sku": "ONIONS", "qty": 1, "price": 100},    # KES 100/kg
            {"sku": "CARROTS", "qty": 2, "price": 90},    # KES 90/kg
            {"sku": "EGGS", "qty": 12, "price": 15},      # KES 15/egg
        ]

        # Calculate expected total: (1*100) + (2*90) + (12*15) = 100 + 180 + 180 = KES 460
        expected_total = 460

        # Record initial stock
        initial_onions = get_inventory_quantity("ONIONS")
        initial_carrots = get_inventory_quantity("CARROTS")
        initial_eggs = get_inventory_quantity("EGGS")

        # Step 1: Create order (customer selects items)
        order_id = process_retail_sale(
            customer_identifier="MPESA_CUSTOMER_001",
            items=items,
            payment_amount=0,  # No payment yet - waiting for M-Pesa
            payment_method="pending"
        )

        # Order should be PENDING (not enough payment)
        # Stock should NOT be deducted yet
        assert get_inventory_quantity("ONIONS") == initial_onions
        assert get_inventory_quantity("CARROTS") == initial_carrots
        assert get_inventory_quantity("EGGS") == initial_eggs

        # Step 2: M-Pesa payment arrives (simulated callback)
        mpesa_reference = "MPESA_TXN_123456"
        payment_result = apply_payment_to_order(
            order_id=order_id,
            payment_amount=expected_total,
            method="M-Pesa",
            reference=mpesa_reference
        )

        # Order should now be COMPLETED
        assert payment_result["status"] == "COMPLETED"
        assert payment_result["total_paid"] == expected_total

        # Stock should now be deducted
        assert get_inventory_quantity("ONIONS") == initial_onions - 1
        assert get_inventory_quantity("CARROTS") == initial_carrots - 2
        assert get_inventory_quantity("EGGS") == initial_eggs - 12

    def test_partial_mpesa_payment(self, mama_mboga_business):
        """
        Test partial M-Pesa payment scenario.
        Common in Nairobi - customer pays what they can afford.
        """
        from core.services.sales_service import process_retail_sale, apply_payment_to_order
        from core.services.inventory_service import get_inventory_quantity

        # Customer wants: 3kg potatoes, 2kg tomatoes
        items = [
            {"sku": "POTATOES", "qty": 3, "price": 80},   # KES 80/kg
            {"sku": "TOMATOES", "qty": 2, "price": 120},  # KES 120/kg
        ]

        # Total: (3*80) + (2*120) = 240 + 240 = KES 480
        expected_total = 480

        # Customer can only afford KES 300 now
        initial_payment = 300

        # Record initial stock
        initial_potatoes = get_inventory_quantity("POTATOES")
        initial_tomatoes = get_inventory_quantity("TOMATOES")

        # Create order with partial payment
        order_id = process_retail_sale(
            customer_identifier="PARTIAL_CUSTOMER_001",
            items=items,
            payment_amount=initial_payment,
            payment_method="M-Pesa",
            payment_reference="MPESA_PARTIAL_001"
        )

        # Order should be PENDING
        # Stock should NOT be deducted
        assert get_inventory_quantity("POTATOES") == initial_potatoes
        assert get_inventory_quantity("TOMATOES") == initial_tomatoes

        # Customer pays remaining KES 180 later
        final_payment_result = apply_payment_to_order(
            order_id=order_id,
            payment_amount=180,
            method="M-Pesa",
            reference="MPESA_FINAL_001"
        )

        # Order should now be COMPLETED
        assert final_payment_result["status"] == "COMPLETED"
        assert final_payment_result["total_paid"] == expected_total

        # Stock should now be deducted
        assert get_inventory_quantity("POTATOES") == initial_potatoes - 3
        assert get_inventory_quantity("TOMATOES") == initial_tomatoes - 2

    def test_insufficient_stock_scenario(self, mama_mboga_business):
        """
        Test insufficient stock handling.
        Critical for perishable goods - Mama Mboga can't sell what she doesn't have.
        """
        from core.services.sales_service import process_retail_sale
        from core.services.inventory_service import get_inventory_quantity

        # Customer wants more cabbages than Mama Mboga has
        # She only has 8 cabbages but customer wants 12
        items = [
            {"sku": "CABBAGE", "qty": 12, "price": 150},  # KES 150 each
        ]

        # Record initial stock
        initial_cabbages = get_inventory_quantity("CABBAGE")

        # Attempt sale - should fail
        with pytest.raises(ValueError, match="Stock check failed"):
            process_retail_sale(
                customer_identifier="INSUFFICIENT_CUSTOMER_001",
                items=items,
                payment_amount=1800,  # 12 * 150
                payment_method="cash"
            )

        # Stock should remain unchanged
        assert get_inventory_quantity("CABBAGE") == initial_cabbages

        # A FAILED order and payment should be recorded for audit trail
        # (This would be verified by checking the database directly)

    def test_end_of_day_reconciliation(self, mama_mboga_business):
        """
        Test end-of-day reconciliation.
        Mama Mboga needs to know daily sales and remaining stock.
        """
        # This would test:
        # - Total sales for the day
        # - Remaining inventory levels
        # - Payment method breakdown
        # - Any outstanding orders

        # Implementation would query:
        # - Sum of completed orders
        # - Current inventory levels
        # - Payment records by method
        pass

    def test_spoilage_write_off(self, mama_mboga_business):
        """
        Test spoilage write-off.
        Perishable goods can spoil - Mama Mboga needs to record losses.
        """
        from core.services.inventory_service import adjust_inventory, get_inventory_quantity

        # Record initial stock
        initial_spinach = get_inventory_quantity("SPINACH")

        # 2kg of spinach spoiled
        adjust_inventory(
            sku="SPINACH",
            quantity_change=-2,
            reason="spoilage",
            order_id=None
        )

        # Stock should be reduced
        assert get_inventory_quantity("SPINACH") == initial_spinach - 2

        # Stock movement should be recorded for audit trail
        # (Would verify by checking stock_movements table)
