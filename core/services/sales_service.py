import uuid
from core.storage.db import get_db
from core.models.order import Order
from core.models.payment import Payment
from core.services.inventory_service import verify_stock, adjust_inventory
from core.services.payment_service import record_payment, get_total_paid
from core.services.audit_service import log_event

def process_retail_sale(customer_identifier, items, payment_amount, payment_method="manual", payment_reference=None):
    """
    Process a retail sale with proper ERP invariants.

    Must:
    1. Calculate total
    2. Verify stock for all items
    3. On failure: Create FAILED order, record failed payment, log everything
    4. On success: Create order, record payment
       - If partial → PENDING
       - If full → deduct stock → COMPLETED
    5. Log every state change

    Args:
        customer_identifier: Customer identifier
        items: List of dicts with 'sku', 'qty', 'price'
        payment_amount: Amount paid
        payment_method: Payment method (default: 'manual')
        payment_reference: Optional payment reference

    Returns:
        str: Order ID

    Raises:
        ValueError: If stock verification fails
    """
    conn = get_db()
    cur = conn.cursor()

    try:
        # 1. Calculate total
        total_amount = sum(item["qty"] * item["price"] for item in items)

        # 2. Verify stock for all items
        stock_issues = []
        for item in items:
            try:
                verify_stock(item["sku"], item["qty"])
            except ValueError as e:
                stock_issues.append(str(e))

        # 3. Handle stock failure
        if stock_issues:
            order_id = str(uuid.uuid4())
            order = Order(
                id=order_id,
                customer_identifier=customer_identifier,
                total_amount=total_amount,
                status="FAILED"
            )

            cur.execute("""
                INSERT INTO orders (id, customer_identifier, total_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                order.id,
                order.customer_identifier,
                order.total_amount,
                order.status,
                order.created_at
            ))

            # Record failed payment attempt for audit trail
            payment_id = str(uuid.uuid4())
            payment = Payment(
                id=payment_id,
                order_id=order.id,
                amount=payment_amount,
                method=payment_method,
                status="FAILED",
                reference=payment_reference
            )

            cur.execute("""
                INSERT INTO payments
                (id, order_id, amount, method, status, reference, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                payment.id,
                payment.order_id,
                payment.amount,
                payment.method,
                payment.status,
                payment.reference,
                payment.created_at
            ))

            conn.commit()

            # Log events
            log_event(
                entity_type='order',
                entity_id=order.id,
                action='created',
                metadata={'status': 'FAILED', 'reason': 'stock_verification_failed'}
            )

            log_event(
                entity_type='payment',
                entity_id=payment.id,
                action='failed',
                metadata={
                    'order_id': order.id,
                    'reason': 'stock_verification_failed',
                    'stock_issues': stock_issues
                }
            )

            raise ValueError(f"Stock check failed: {', '.join(stock_issues)}")

        # 4. Create Order
        order_id = str(uuid.uuid4())
        order = Order(
            id=order_id,
            customer_identifier=customer_identifier,
            total_amount=total_amount,
            status="CREATED"
        )

        cur.execute("""
            INSERT INTO orders (id, customer_identifier, total_amount, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            order.id,
            order.customer_identifier,
            order.total_amount,
            order.status,
            order.created_at
        ))

        # Store order items for later stock deduction
        from datetime import datetime
        for item in items:
            item_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO order_items (id, order_id, sku, quantity, price, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                order.id,
                item["sku"],
                item["qty"],
                item["price"],
                datetime.utcnow().isoformat()
            ))

        log_event(
            entity_type='order',
            entity_id=order.id,
            action='created',
            metadata={'status': 'CREATED', 'total_amount': total_amount}
        )

        # 5. Record Payment and determine status
        payment = record_payment(order.id, payment_amount, payment_method, payment_reference)

        # Determine order status based on payment
        if payment_amount < total_amount:
            # Partial payment
            order.status = "PENDING"
            cur.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (order.status, order.id)
            )
            conn.commit()

            log_event(
                entity_type='order',
                entity_id=order.id,
                action='status_updated',
                metadata={'status': 'PENDING', 'reason': 'partial_payment'}
            )
        else:
            # Full payment or overpayment - deduct stock and complete
            order.status = "COMPLETED"
            cur.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (order.status, order.id)
            )

            # 6. Deduct Stock only if fully paid (ERP truth: stock moves only on completion)
            for item in items:
                adjust_inventory(
                    sku=item["sku"],
                    quantity_change=-item["qty"],
                    reason="sale",
                    order_id=order.id
                )

            conn.commit()

            log_event(
                entity_type='order',
                entity_id=order.id,
                action='completed',
                metadata={'status': 'COMPLETED', 'payment_amount': payment_amount}
            )

        return order.id

    except Exception as e:
        conn.rollback()
        raise

def apply_payment_to_order(order_id, payment_amount, method="manual", reference=None):
    """
    Apply an additional payment to an existing order.

    Must:
    - Validate order state (must be PENDING or CREATED, not FAILED or COMPLETED)
    - Record payment
    - Recalculate paid total
    - Deduct stock only once when fully paid
    - Prevent double deduction
    - Log everything
    - Be idempotent (handle retries safely)

    Args:
        order_id: ID of the order
        payment_amount: Amount to apply
        method: Payment method (default: 'manual')
        reference: Optional payment reference (for idempotency checks)

    Returns:
        dict: Status update with order_id, new_status, total_paid, order_total

    Raises:
        ValueError: If order state is invalid or order not found
    """
    conn = get_db()
    cur = conn.cursor()

    try:
        # Get order details
        cur.execute("""
            SELECT id, customer_identifier, total_amount, status
            FROM orders
            WHERE id = ?
        """, (order_id,))

        result = cur.fetchone()
        if not result:
            raise ValueError(f"Order {order_id} not found")

        order_id_db, customer_identifier, total_amount, current_status = result

        # Validate order state
        if current_status == "FAILED":
            raise ValueError(f"Cannot apply payment to FAILED order {order_id}")

        if current_status == "COMPLETED":
            # Check if this is a duplicate payment attempt (idempotency)
            if reference:
                cur.execute("""
                    SELECT id FROM payments
                    WHERE order_id = ? AND reference = ? AND status = 'RECEIVED'
                """, (order_id, reference))
                if cur.fetchone():
                    # Duplicate payment with same reference - return current state
                    total_paid = get_total_paid(order_id)
                    return {
                        'order_id': order_id,
                        'status': 'COMPLETED',
                        'total_paid': total_paid,
                        'order_total': total_amount,
                        'message': 'Payment already recorded (idempotent)'
                    }
            raise ValueError(f"Cannot apply payment to COMPLETED order {order_id}")

        # Check for duplicate payment by reference (idempotency)
        if reference:
            cur.execute("""
                SELECT id FROM payments
                WHERE order_id = ? AND reference = ? AND status = 'RECEIVED'
            """, (order_id, reference))
            if cur.fetchone():
                # Duplicate payment - return current state without error
                total_paid = get_total_paid(order_id)
                return {
                    'order_id': order_id,
                    'status': current_status,
                    'total_paid': total_paid,
                    'order_total': total_amount,
                    'message': 'Payment already recorded (idempotent)'
                }

        # Record payment
        payment = record_payment(order_id, payment_amount, method, reference)

        # Recalculate paid total
        total_paid = get_total_paid(order_id)

        # Determine if order should be completed
        if total_paid >= total_amount and current_status != "COMPLETED":
            # Order is now fully paid - deduct stock and complete
            # Get order items to deduct stock
            cur.execute("""
                SELECT sku, quantity FROM order_items WHERE order_id = ?
            """, (order_id,))

            order_items = cur.fetchall()

            if not order_items:
                raise ValueError(f"No items found for order {order_id}")

            # Deduct stock for all items (only once - check if already deducted)
            # Check if stock was already deducted by looking for stock movements
            cur.execute("""
                SELECT COUNT(*) FROM stock_movements
                WHERE related_order_id = ? AND reason = 'sale'
            """, (order_id,))

            stock_already_deducted = cur.fetchone()[0] > 0

            if not stock_already_deducted:
                # Deduct stock for each item
                for sku, quantity in order_items:
                    adjust_inventory(
                        sku=sku,
                        quantity_change=-quantity,
                        reason="sale",
                        order_id=order_id
                    )

            cur.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                ("COMPLETED", order_id)
            )

            conn.commit()

            log_event(
                entity_type='order',
                entity_id=order_id,
                action='completed',
                metadata={
                    'status': 'COMPLETED',
                    'total_paid': total_paid,
                    'order_total': total_amount,
                    'payment_id': payment.id,
                    'stock_deducted': not stock_already_deducted
                }
            )

            return {
                'order_id': order_id,
                'status': 'COMPLETED',
                'total_paid': total_paid,
                'order_total': total_amount,
                'payment_id': payment.id
            }
        else:
            # Still partial payment
            if current_status != "PENDING":
                cur.execute(
                    "UPDATE orders SET status = ? WHERE id = ?",
                    ("PENDING", order_id)
                )
                conn.commit()

                log_event(
                    entity_type='order',
                    entity_id=order_id,
                    action='status_updated',
                    metadata={
                        'status': 'PENDING',
                        'total_paid': total_paid,
                        'order_total': total_amount,
                        'payment_id': payment.id
                    }
                )

            return {
                'order_id': order_id,
                'status': 'PENDING',
                'total_paid': total_paid,
                'order_total': total_amount,
                'payment_id': payment.id
            }

    except Exception as e:
        conn.rollback()
        raise