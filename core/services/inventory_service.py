import uuid
from core.storage.db import get_db
from core.models.stock_movement import StockMovement
from core.services.audit_service import log_event

def verify_stock(sku, required_qty, db_conn=None):
    """
    Verify that sufficient stock is available for a SKU.

    Args:
        sku: Stock keeping unit identifier
        required_qty: Quantity required
        db_conn: Optional database connection (for testing)

    Returns:
        bool: True if sufficient stock is available

    Raises:
        ValueError: If SKU not found or insufficient stock
    """
    conn = db_conn or get_db()
    cur = conn.cursor()

    cur.execute("SELECT quantity FROM inventory WHERE sku = ?", (sku,))
    result = cur.fetchone()

    if not result:
        raise ValueError(f"SKU {sku} not found in inventory")

    available_qty = result[0]
    if available_qty < required_qty:
        raise ValueError(
            f"Insufficient stock for SKU {sku}: need {required_qty}, have {available_qty}"
        )

    return True

def adjust_inventory(sku, quantity_change, reason, order_id=None, db_conn=None):
    """
    Adjust inventory by creating a stock movement record.
    This is the ONLY way inventory should change (ERP invariant).

    Args:
        sku: Stock keeping unit identifier
        quantity_change: Change in quantity (negative for deduction, positive for addition)
        reason: Reason for the movement (e.g., 'sale', 'restock', 'adjustment')
        order_id: Optional order ID if related to an order
        db_conn: Optional database connection (for testing)

    Returns:
        StockMovement instance

    Raises:
        ValueError: If adjustment would result in negative stock
        Exception: If database operation fails
    """
    conn = db_conn or get_db()
    cur = conn.cursor()

    try:
        # Get current stock
        cur.execute("SELECT quantity FROM inventory WHERE sku = ?", (sku,))
        result = cur.fetchone()

        if not result:
            # Create inventory item if it doesn't exist (for positive adjustments)
            if quantity_change > 0:
                cur.execute(
                    "INSERT INTO inventory (sku, quantity) VALUES (?, ?)",
                    (sku, quantity_change)
                )
                new_quantity = quantity_change
            else:
                raise ValueError(f"Cannot adjust inventory for non-existent SKU {sku}")
        else:
            current_qty = result[0]
            new_quantity = current_qty + quantity_change

            # ERP invariant: Stock never goes negative
            if new_quantity < 0:
                raise ValueError(
                    f"Stock adjustment would result in negative inventory for SKU {sku}: "
                    f"current {current_qty}, change {quantity_change}, result {new_quantity}"
                )

            # Update inventory
            cur.execute(
                "UPDATE inventory SET quantity = ? WHERE sku = ?",
                (new_quantity, sku)
            )

        # Create stock movement record (mandatory for all inventory changes)
        movement_id = str(uuid.uuid4())
        movement = StockMovement(
            id=movement_id,
            sku=sku,
            quantity_change=quantity_change,
            reason=reason,
            related_order_id=order_id
        )

        cur.execute("""
            INSERT INTO stock_movements
            (id, sku, quantity_change, reason, related_order_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            movement.id,
            movement.sku,
            movement.quantity_change,
            movement.reason,
            movement.related_order_id,
            movement.created_at
        ))

        conn.commit()

        # Log event for audit trail (skip for testing if db_conn provided)
        if db_conn is None:
            log_event(
                entity_type='inventory',
                entity_id=sku,
                action='adjusted',
                metadata={
                    'quantity_change': quantity_change,
                    'new_quantity': new_quantity,
                    'reason': reason,
                    'order_id': order_id,
                    'movement_id': movement_id
                }
            )

        return movement
    except Exception as e:
        conn.rollback()
        raise

def get_inventory_quantity(sku):
    """
    Get current inventory quantity for a SKU.

    Args:
        sku: Stock keeping unit identifier

    Returns:
        int: Current quantity (0 if SKU not found)
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT quantity FROM inventory WHERE sku = ?", (sku,))
    result = cur.fetchone()

    return result[0] if result else 0

