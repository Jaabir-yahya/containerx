import sqlite3
import threading
from contextlib import contextmanager

DB_NAME = "containerx.db"

# Thread-local storage for database connections
_local = threading.local()

def get_db():
    """
    Get a database connection.

    Uses override if set (for testing), otherwise thread-local connection.
    """
    if _db_override is not None:
        return _db_override

    # Thread-local connection for production
    # Check if we need a new connection (database changed or doesn't exist)
    if (not hasattr(_local, 'connection') or
        not hasattr(_local, 'db_name') or
        _local.db_name != DB_NAME):

        # Close existing connection if it exists
        if hasattr(_local, 'connection'):
            try:
                _local.connection.close()
            except:
                pass  # Ignore errors when closing

        # Create new connection
        _local.connection = sqlite3.connect(DB_NAME, check_same_thread=False)
        _local.db_name = DB_NAME

        # Enable WAL mode for better concurrency
        _local.connection.execute("PRAGMA journal_mode=WAL")
        _local.connection.execute("PRAGMA synchronous=NORMAL")
        _local.connection.execute("PRAGMA cache_size=1000")
        _local.connection.commit()

    return _local.connection

# Global override for testing
_db_override = None

def set_db_override(conn):
    """Set database connection override (for testing)."""
    global _db_override
    _db_override = conn

def clear_db_override():
    """Clear database connection override."""
    global _db_override
    _db_override = None

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.

    Automatically handles connection lifecycle and cleanup.
    """
    conn = get_db()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        # Don't close thread-local connections - let them persist
        pass

def close_db():
    """
    Close the current thread's database connection.

    Should be called when a thread is shutting down.
    """
    if hasattr(_local, 'connection'):
        _local.connection.close()
        delattr(_local, 'connection')

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Orders table with created_at
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        customer_identifier TEXT,
        total_amount REAL,
        status TEXT,
        created_at TEXT
    )
    """)

    # Payments table with reference and created_at
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
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
    CREATE TABLE IF NOT EXISTS inventory (
        sku TEXT PRIMARY KEY,
        quantity INTEGER
    )
    """)

    # Stock movements table (append-only ledger)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_movements (
        id TEXT PRIMARY KEY,
        sku TEXT NOT NULL,
        quantity_change INTEGER NOT NULL,
        reason TEXT NOT NULL,
        related_order_id TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # Event log table (append-only audit trail)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS event_log (
        id TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        action TEXT NOT NULL,
        metadata TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # Order items table (tracks items in each order)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
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
    CREATE TABLE IF NOT EXISTS commitments (
        id TEXT PRIMARY KEY,
        actor_id TEXT NOT NULL,
        promise TEXT NOT NULL,
        value DECIMAL NOT NULL,
        due_by TEXT NOT NULL,
        state TEXT NOT NULL,
        metadata TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # UCOS: Trust events table (mathematical reputation)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS trust_events (
        id TEXT PRIMARY KEY,
        actor_id TEXT NOT NULL,
        delta DECIMAL NOT NULL,
        reason TEXT NOT NULL,
        commitment_id TEXT,
        expires_at TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # UCOS: Timers table (auto-enforcement)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS timers (
        id TEXT PRIMARY KEY,
        commitment_id TEXT NOT NULL,
        type TEXT NOT NULL,
        fires_at TEXT NOT NULL,
        action TEXT NOT NULL,
        status TEXT DEFAULT 'scheduled',
        created_at TEXT NOT NULL,
        FOREIGN KEY (commitment_id) REFERENCES commitments(id)
    )
    """)

    # UCOS: Credit packages table (prepaid system)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS credit_packages (
        id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        purchased_amount DECIMAL NOT NULL,
        issued_credits DECIMAL NOT NULL,
        remaining_credits DECIMAL NOT NULL,
        status TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # UCOS: Credit transactions table (credit ledger)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS credit_transactions (
        id TEXT PRIMARY KEY,
        package_id TEXT NOT NULL,
        commitment_id TEXT,
        amount DECIMAL NOT NULL,
        type TEXT NOT NULL,
        balance_after DECIMAL NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (package_id) REFERENCES credit_packages(id)
    )
    """)

    # Migration: If old 'stock' table exists, migrate data to 'inventory'
    cur.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='stock'
    """)
    if cur.fetchone():
        # Check if inventory table is empty
        cur.execute("SELECT COUNT(*) FROM inventory")
        if cur.fetchone()[0] == 0:
            # Migrate data from stock to inventory
            cur.execute("""
            INSERT INTO inventory (sku, quantity)
            SELECT sku, quantity FROM stock
            """)
        # Drop old stock table (commented out for safety - uncomment after verification)
        # cur.execute("DROP TABLE stock")

    # Migration: Add created_at to existing orders if missing
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN created_at TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Migration: Add customer_identifier and total_amount if old columns exist
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN customer_identifier TEXT")
        cur.execute("ALTER TABLE orders ADD COLUMN total_amount REAL")
        # Migrate data if old columns exist
        cur.execute("""
        UPDATE orders 
        SET customer_identifier = customer, total_amount = total
        WHERE customer_identifier IS NULL AND customer IS NOT NULL
        """)
    except sqlite3.OperationalError:
        pass  # Columns already exist

    # Migration: Add reference and created_at to payments if missing
    try:
        cur.execute("ALTER TABLE payments ADD COLUMN reference TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cur.execute("ALTER TABLE payments ADD COLUMN created_at TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # UCOS Migrations: Extend event_log with UCOS fields
    try:
        cur.execute("ALTER TABLE event_log ADD COLUMN source TEXT DEFAULT 'system'")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cur.execute("ALTER TABLE event_log ADD COLUMN actor_id TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cur.execute("ALTER TABLE event_log ADD COLUMN correlation_id TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # UCOS Migrations: Extend orders with commitment linkage
    try:
        cur.execute("ALTER TABLE orders ADD COLUMN commitment_id TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cur.execute("ALTER TABLE orders ADD COLUMN sla_hours REAL DEFAULT 24")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cur.execute("ALTER TABLE orders ADD COLUMN auto_refund BOOLEAN DEFAULT TRUE")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    # Don't close thread-local connections