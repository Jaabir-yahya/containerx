"""
Helper functions for testing and debugging.
"""

from core.storage.db import get_db
import json

def get_event_log(entity_type=None, entity_id=None, action=None):
    """
    Get event log entries with optional filters.
    
    Args:
        entity_type: Filter by entity type
        entity_id: Filter by entity ID
        action: Filter by action
    
    Returns:
        list: List of event log entries
    """
    conn = get_db()
    cur = conn.cursor()
    
    query = "SELECT * FROM event_log WHERE 1=1"
    params = []
    
    if entity_type:
        query += " AND entity_type = ?"
        params.append(entity_type)
    
    if entity_id:
        query += " AND entity_id = ?"
        params.append(entity_id)
    
    if action:
        query += " AND action = ?"
        params.append(action)
    
    query += " ORDER BY created_at"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    
    # Convert to list of dicts
    columns = [desc[0] for desc in cur.description] if cur.description else []
    events = []
    for row in rows:
        event = dict(zip(columns, row))
        # Parse metadata JSON
        if event.get('metadata'):
            try:
                event['metadata'] = json.loads(event['metadata'])
            except:
                pass
        events.append(event)
    
    return events

def get_stock_movements(sku=None, order_id=None):
    """
    Get stock movement entries with optional filters.
    
    Args:
        sku: Filter by SKU
        order_id: Filter by related order ID
    
    Returns:
        list: List of stock movement entries
    """
    conn = get_db()
    cur = conn.cursor()
    
    query = "SELECT * FROM stock_movements WHERE 1=1"
    params = []
    
    if sku:
        query += " AND sku = ?"
        params.append(sku)
    
    if order_id:
        query += " AND related_order_id = ?"
        params.append(order_id)
    
    query += " ORDER BY created_at"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    
    # Convert to list of dicts
    columns = [desc[0] for desc in cur.description] if cur.description else []
    movements = []
    for row in rows:
        movement = dict(zip(columns, row))
        movements.append(movement)
    
    return movements

def get_inventory_quantity(sku):
    """Get current inventory quantity for a SKU."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT quantity FROM inventory WHERE sku = ?", (sku,))
    result = cur.fetchone()
    # Don't close thread-local connections
    return result[0] if result else None

def print_event_log(entity_type=None, entity_id=None, action=None):
    """Print event log entries for debugging."""
    events = get_event_log(entity_type, entity_id, action)
    print(f"\n=== Event Log ({len(events)} entries) ===")
    for event in events:
        print(f"  {event['created_at']} | {event['entity_type']}:{event['entity_id']} | {event['action']}")
        if event.get('metadata'):
            print(f"    Metadata: {json.dumps(event['metadata'], indent=4)}")
    print()

def print_stock_movements(sku=None, order_id=None):
    """Print stock movements for debugging."""
    movements = get_stock_movements(sku, order_id)
    print(f"\n=== Stock Movements ({len(movements)} entries) ===")
    for movement in movements:
        print(f"  {movement['created_at']} | SKU: {movement['sku']} | Change: {movement['quantity_change']} | Reason: {movement['reason']}")
        if movement.get('related_order_id'):
            print(f"    Order: {movement['related_order_id']}")
    print()

def assert_stock_movement_count(sku, expected_count, msg=None):
    """
    Assert that the number of stock movements for a SKU matches expected count.
    
    Args:
        sku: SKU to check
        expected_count: Expected number of movements
        msg: Optional assertion message
    """
    movements = get_stock_movements(sku=sku)
    actual_count = len(movements)
    assert actual_count == expected_count, (
        msg or f"Expected {expected_count} stock movements for {sku}, got {actual_count}"
    )

def assert_event_exists(entity_type, entity_id, action, msg=None):
    """
    Assert that an event exists in the log.
    
    Args:
        entity_type: Entity type
        entity_id: Entity ID
        action: Action
        msg: Optional assertion message
    """
    events = get_event_log(entity_type=entity_type, entity_id=entity_id, action=action)
    assert len(events) > 0, (
        msg or f"Expected event {entity_type}:{entity_id} action={action} not found"
    )

def assert_no_negative_stock(msg=None):
    """
    Assert that no inventory items have negative quantity.
    
    Args:
        msg: Optional assertion message
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT sku, quantity FROM inventory WHERE quantity < 0")
    negative_items = cur.fetchall()
    conn.close()
    
    assert len(negative_items) == 0, (
        msg or f"Found {len(negative_items)} items with negative stock: {negative_items}"
    )

def get_order_status(order_id):
    """Get order status from database."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def get_total_paid(order_id):
    """Get total amount paid for an order."""
    from core.services.payment_service import get_total_paid as _get_total_paid
    return _get_total_paid(order_id)

