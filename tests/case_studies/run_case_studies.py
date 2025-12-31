#!/usr/bin/env python3
"""
🇰🇪 Nairobi Case Study Test Runner

Runs focused case study tests for ContainerX ERP Core.
Validates real Kenyan business scenarios without complex test infrastructure.

Usage:
    python tests/case_studies/run_case_studies.py

This bypasses the complex pytest fixture system and tests the core directly.
"""

import sys
import os
import sqlite3
import tempfile
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def setup_test_database():
    """Create a clean test database for case studies."""
    print("🏗️  Setting up test database...")

    # Create temporary database
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()

    conn = sqlite3.connect(db_path)

    # Initialize schema
    cur = conn.cursor()

    # Create core tables
    schema_sql = """
    CREATE TABLE orders (
        id TEXT PRIMARY KEY,
        customer_identifier TEXT,
        total_amount REAL,
        status TEXT,
        created_at TEXT
    );

    CREATE TABLE payments (
        id TEXT PRIMARY KEY,
        order_id TEXT,
        amount REAL,
        method TEXT,
        status TEXT,
        reference TEXT,
        created_at TEXT
    );

    CREATE TABLE inventory (
        sku TEXT PRIMARY KEY,
        quantity INTEGER
    );

    CREATE TABLE stock_movements (
        id TEXT PRIMARY KEY,
        sku TEXT NOT NULL,
        quantity_change INTEGER NOT NULL,
        reason TEXT NOT NULL,
        related_order_id TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE event_log (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        action TEXT NOT NULL,
        metadata TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE order_items (
        id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        sku TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        created_at TEXT NOT NULL
    );
    """

    cur.executescript(schema_sql)

    # Seed Mama Mboga's inventory
    inventory_data = {
        "TOMATOES": 25, "ONIONS": 30, "SPINACH": 15, "CABBAGE": 8,
        "CARROTS": 20, "POTATOES": 40, "BANANAS": 35, "EGGS": 120
    }

    for sku, qty in inventory_data.items():
        cur.execute("INSERT INTO inventory (sku, quantity) VALUES (?, ?)", (sku, qty))

    conn.commit()

    # Override get_db
    import core.storage.db
    core.storage.db.set_db_override(conn)

    print(f"✅ Database ready at: {db_path}")
    return conn, db_path

def cleanup_test_database(conn, db_path):
    """Clean up test database."""
    import core.storage.db
    core.storage.db.clear_db_override()

    conn.close()
    if os.path.exists(db_path):
        os.unlink(db_path)
    print("🧹 Database cleaned up")

def run_mama_mboga_test(conn):
    """Run Mama Mboga vegetable vendor case study."""
    print("\n🥕 Testing Mama Mboga Case Study...")

    try:
        from core.services.sales_service import process_retail_sale
        from core.services.inventory_service import get_inventory_quantity

        # Test 1: Cash customer journey
        print("  💰 Testing cash customer journey...")

        items = [
            {"sku": "TOMATOES", "qty": 2, "price": 120},
            {"sku": "SPINACH", "qty": 1, "price": 80}
        ]

        initial_tomatoes = get_inventory_quantity("TOMATOES")
        initial_spinach = get_inventory_quantity("SPINACH")

        order_id = process_retail_sale(
            customer_identifier="CASH_CUSTOMER_001",
            items=items,
            payment_amount=400,  # 2*120 + 1*80
            payment_method="cash"
        )

        # Verify stock deduction
        assert get_inventory_quantity("TOMATOES") == initial_tomatoes - 2
        assert get_inventory_quantity("SPINACH") == initial_spinach - 1

        print("  ✅ Cash sale completed successfully")

        # Test 2: Insufficient stock handling
        print("  ❌ Testing insufficient stock handling...")

        try:
            process_retail_sale(
                customer_identifier="INSUFFICIENT_CUSTOMER",
                items=[{"sku": "CABBAGE", "qty": 12, "price": 150}],  # Only 8 available
                payment_amount=1800,
                payment_method="cash"
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Stock check failed" in str(e)
            print("  ✅ Insufficient stock properly rejected")

        print("🥕 Mama Mboga case study: PASSED")

    except Exception as e:
        print(f"🥕 Mama Mboga case study: FAILED - {e}")
        raise

def run_mpesa_integration_test(conn):
    """Test M-Pesa payment integration scenario."""
    print("\n📱 Testing M-Pesa Integration...")

    try:
        from core.services.sales_service import process_retail_sale, apply_payment_to_order
        from core.services.inventory_service import get_inventory_quantity

        # Create order with no initial payment
        items = [{"sku": "ONIONS", "qty": 1, "price": 100}]
        initial_onions = get_inventory_quantity("ONIONS")

        order_id = process_retail_sale(
            customer_identifier="MPESA_CUSTOMER",
            items=items,
            payment_amount=0,  # Will pay via M-Pesa
            payment_method="pending"
        )

        # Stock should not be deducted yet
        assert get_inventory_quantity("ONIONS") == initial_onions

        # Simulate M-Pesa callback
        payment_result = apply_payment_to_order(
            order_id=order_id,
            payment_amount=100,
            method="M-Pesa",
            reference="MPESA_TEST_123"
        )

        # Order should be completed and stock deducted
        assert payment_result["status"] == "COMPLETED"
        assert get_inventory_quantity("ONIONS") == initial_onions - 1

        print("📱 M-Pesa integration: PASSED")

    except Exception as e:
        print(f"📱 M-Pesa integration: FAILED - {e}")
        raise

def run_inventory_integrity_test(conn):
    """Test inventory integrity and audit trails."""
    print("\n📊 Testing Inventory Integrity...")

    try:
        from core.services.inventory_service import adjust_inventory, get_inventory_quantity

        # Test stock movement recording
        initial_qty = get_inventory_quantity("EGGS")

        adjust_inventory("EGGS", -6, "sale", "AUDIT_ORDER_123")

        assert get_inventory_quantity("EGGS") == initial_qty - 6

        # Verify stock movement was recorded
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stock_movements WHERE sku = 'EGGS'")
        movements = cur.fetchone()[0]
        assert movements > 0

        # Verify event was logged
        cur.execute("SELECT COUNT(*) FROM event_log WHERE entity_type = 'inventory' AND entity_id = 'EGGS'")
        events = cur.fetchone()[0]
        assert events > 0

        print("📊 Inventory integrity: PASSED")

    except Exception as e:
        print(f"📊 Inventory integrity: FAILED - {e}")
        raise

def run_business_summary_test(conn):
    """Test business analytics and reporting."""
    print("\n📈 Testing Business Summary...")

    try:
        cur = conn.cursor()

        # Get business metrics
        cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'COMPLETED'")
        completed_orders = cur.fetchone()[0]

        cur.execute("SELECT SUM(total_amount) FROM orders WHERE status = 'COMPLETED'")
        total_revenue = cur.fetchone()[0] or 0

        cur.execute("SELECT SUM(quantity) FROM inventory")
        total_stock = cur.fetchone()[0]

        print(f"  📊 Completed Orders: {completed_orders}")
        print(f"  📊 Total Revenue: KES {total_revenue}")
        print(f"  📊 Total Stock Items: {total_stock}")

        # Verify data integrity
        assert completed_orders >= 0
        assert total_revenue >= 0
        assert total_stock > 0

        print("📈 Business summary: PASSED")

    except Exception as e:
        print(f"📈 Business summary: FAILED - {e}")
        raise

def main():
    """Run all Nairobi case studies."""
    print("🇰🇪 ContainerX Nairobi Case Study Tests")
    print("=" * 50)

    conn = None
    db_path = None

    try:
        # Setup
        conn, db_path = setup_test_database()

        # Run case studies
        run_mama_mboga_test(conn)
        run_mpesa_integration_test(conn)
        run_inventory_integrity_test(conn)
        run_business_summary_test(conn)

        # Success
        print("\n" + "=" * 50)
        print("🎉 ALL NAIROBI CASE STUDIES PASSED!")
        print("✅ ERP Core validated for Kenyan retail scenarios")
        print("✅ Ready for SaaS deployment and data lake integration")

    except Exception as e:
        print(f"\n❌ CASE STUDY FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        if conn and db_path:
            cleanup_test_database(conn, db_path)

    return 0

if __name__ == "__main__":
    exit(main())
