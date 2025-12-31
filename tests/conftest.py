"""
Shared pytest fixtures for ERP core testing.

Provides:
- Isolated test database for each test
- Service instances
- Helper functions for debugging
"""

import pytest
import tempfile
import os
import sqlite3

@pytest.fixture(scope="function")
def test_setup():
    """
    Complete test setup: isolated database with get_db override and seeded inventory.
    Returns the test database connection.
    """
    # Create test database
    test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db_path = test_db_file.name
    test_db_file.close()

    # Create and initialize the database
    conn = sqlite3.connect(test_db_path)

    # Initialize schema
    cur = conn.cursor()

    # Orders table with created_at
    cur.execute("""
    CREATE TABLE orders (
        id TEXT PRIMARY KEY,
        customer_identifier TEXT,
        total_amount REAL,
        status TEXT,
        created_at TEXT
    )
    """)

    # Payments table with reference and created_at
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

    # Inventory table (renamed from stock, removed name column)
    cur.execute("""
    CREATE TABLE inventory (
        sku TEXT PRIMARY KEY,
        quantity INTEGER
    )
    """)

    # Stock movements table (append-only ledger)
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

    # Event log table (append-only audit trail) - UCOS extended
    cur.execute("""
    CREATE TABLE event_log (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        action TEXT NOT NULL,
        metadata TEXT,
        created_at TEXT NOT NULL,
        source TEXT DEFAULT 'system',
        actor_id TEXT,
        correlation_id TEXT
    )
    """)

    # Order items table (tracks items in each order)
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

    # UCOS: Commitments table (core primitive)
    cur.execute("""
    CREATE TABLE commitments (
        id TEXT PRIMARY KEY,
        actor_id TEXT NOT NULL,
        promise TEXT NOT NULL,
        value DECIMAL NOT NULL,
        due_by TEXT NOT NULL,
        state TEXT NOT NULL,
        metadata TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # UCOS: Trust events table (mathematical reputation)
    cur.execute("""
    CREATE TABLE trust_events (
        id TEXT PRIMARY KEY,
        actor_id TEXT NOT NULL,
        delta DECIMAL NOT NULL,
        reason TEXT NOT NULL,
        commitment_id TEXT,
        expires_at TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # UCOS: Timers table (auto-enforcement)
    cur.execute("""
    CREATE TABLE timers (
        id TEXT PRIMARY KEY,
        commitment_id TEXT NOT NULL,
        type TEXT NOT NULL,
        fires_at TEXT NOT NULL,
        action TEXT NOT NULL,
        status TEXT DEFAULT 'scheduled',
        created_at TEXT NOT NULL
    );
    """)

    # UCOS: Credit packages table (prepaid system)
    cur.execute("""
    CREATE TABLE credit_packages (
        id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        purchased_amount DECIMAL NOT NULL,
        issued_credits DECIMAL NOT NULL,
        remaining_credits DECIMAL NOT NULL,
        status TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # UCOS: Credit transactions table (credit ledger)
    cur.execute("""
    CREATE TABLE credit_transactions (
        id TEXT PRIMARY KEY,
        package_id TEXT NOT NULL,
        commitment_id TEXT,
        amount DECIMAL NOT NULL,
        type TEXT NOT NULL,
        balance_after DECIMAL NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # UCOS: Payment references table (for M-Pesa idempotency)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payment_references (
            reference TEXT PRIMARY KEY,
            payment_id TEXT NOT NULL,
            commitment_id TEXT,
            order_id TEXT,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            status TEXT NOT NULL,
            webhook_data TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (payment_id) REFERENCES payments(id)
        )
    """)

    # UCOS: Offline queue for network outages
    cur.execute("""
        CREATE TABLE IF NOT EXISTS offline_queue (
            id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            data TEXT NOT NULL,
            status TEXT NOT NULL,
            retry_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            processed_at TEXT
        )
    """)

    # Seed inventory
    inventory = {
        "MILK001": 100,
        "BREAD001": 50,
        "EGGS001": 200,
        "TEST001": 100,
        "TEST002": 50,
    }

    for sku, quantity in inventory.items():
        cur.execute(
            "INSERT OR REPLACE INTO inventory (sku, quantity) VALUES (?, ?)",
            (sku, quantity)
        )

    conn.commit()

    # Set database override
    import core.storage.db
    core.storage.db.set_db_override(conn)

    yield conn

    # Cleanup
    core.storage.db.clear_db_override()
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)

@pytest.fixture(scope="function")
def clean_db(test_setup):
    """
    Combined fixture: clean database with seeded inventory.
    Most tests should use this.
    """
    return test_setup

@pytest.fixture(scope="function")
def seeded_inventory(clean_db):
    """
    Fixture that seeds the database with standard test inventory.
    Returns the database connection.
    """
    conn = clean_db
    cur = conn.cursor()

    # Seed inventory
    inventory = {
        "MILK001": 100,
        "BREAD001": 50,
        "EGGS001": 200,
        "TEST001": 100,
        "TEST002": 50,
    }

    for sku, quantity in inventory.items():
        cur.execute(
            "INSERT OR REPLACE INTO inventory (sku, quantity) VALUES (?, ?)",
            (sku, quantity)
        )

    conn.commit()
    return conn

