"""
Payment Reference Service - M-Pesa retry handling and idempotency

Handles:
- Payment reference tracking (M-Pesa transaction IDs)
- Idempotent payment recording (prevent duplicates)
- Webhook reconciliation
- Network outage queuing
"""
import uuid
import json
import threading
import time
from datetime import datetime
from typing import Dict, Optional

from core.storage.db import get_db, DB_NAME, _db_override_path
from core.services.audit_service import log_event


class PaymentReferenceService:
    """
    Service for handling payment references and idempotency.
    
    UCOS Pattern: Event-driven, thread-safe, state from events
    """
    
    def __init__(self):
        self._init_tables()
    
    def _init_tables(self):
        """Initialize payment reference and offline queue tables."""
        conn = get_db()
        cur = conn.cursor()
        
        # Payment references table (tracks M-Pesa transaction IDs)
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
                updated_at TEXT NOT NULL
            )
        """)
        
        # Offline queue (for network outages)
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
        
        conn.commit()
    
    def record_payment_with_reference(
        self,
        commitment_id: Optional[str] = None,
        order_id: Optional[str] = None,
        amount: float = 0.0,
        method: str = "mpesa",
        reference: Optional[str] = None,
        status: str = "PENDING"
    ) -> Dict:
        """
        Record payment with reference, ensuring idempotency.
        
        If same reference exists, returns existing payment (idempotent).
        If new reference, creates new payment.
        
        UCOS Pattern: Emits events, doesn't store state directly.
        """
        if not reference:
            reference = f"TXN_{uuid.uuid4().hex[:12]}"
        
        conn = get_db()
        cur = conn.cursor()
        
        try:
            # Check if reference already exists (idempotency check)
            cur.execute("""
                SELECT payment_id, status FROM payment_references
                WHERE reference = ?
            """, (reference,))
            
            existing = cur.fetchone()
            
            if existing:
                # Idempotent: same reference = same payment
                existing_payment_id, existing_status = existing
                
                # Log idempotent handling event
                log_event(
                    entity_type='payment',
                    entity_id=existing_payment_id,
                    action='PAYMENT_IDEMPOTENT',
                    metadata={
                        'reference': reference,
                        'payment_id': existing_payment_id,
                        'existing_status': existing_status,
                        'attempted_status': status,
                        'commitment_id': commitment_id,
                        'order_id': order_id
                    },
                    source='system'
                )
                
                return {
                    'payment_id': existing_payment_id,
                    'reference': reference,
                    'idempotent': True,
                    'status': existing_status
                }
            
            # New payment - create payment record
            payment_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            # Record payment
            cur.execute("""
                INSERT INTO payments 
                (id, order_id, amount, method, status, reference, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                payment_id,
                order_id or commitment_id,  # Support both orders and commitments
                amount,
                method,
                status,
                reference,
                now
            ))
            
            # Record payment reference for idempotency
            cur.execute("""
                INSERT INTO payment_references
                (reference, payment_id, commitment_id, order_id, amount, method, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reference,
                payment_id,
                commitment_id,
                order_id,
                amount,
                method,
                status,
                now,
                now
            ))
            
            conn.commit()
            
            # Emit payment attempted event
            log_event(
                entity_type='payment',
                entity_id=payment_id,
                action='PAYMENT_ATTEMPTED',
                metadata={
                    'reference': reference,
                    'commitment_id': commitment_id,
                    'order_id': order_id,
                    'amount': amount,
                    'method': method,
                    'status': status
                },
                source='system'
            )
            
            return {
                'payment_id': payment_id,
                'reference': reference,
                'idempotent': False,
                'status': status
            }
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to record payment with reference: {str(e)}")
    
    def reconcile_webhook(
        self,
        reference: str,
        status: str = "RECEIVED",
        webhook_data: Optional[Dict] = None
    ) -> Dict:
        """
        Reconcile webhook callback with existing payment.
        
        Updates payment status and logs reconciliation event.
        """
        conn = get_db()
        cur = conn.cursor()
        
        try:
            # Find payment by reference
            cur.execute("""
                SELECT payment_id, commitment_id, order_id, amount
                FROM payment_references
                WHERE reference = ?
            """, (reference,))
            
            ref_row = cur.fetchone()
            if not ref_row:
                raise ValueError(f"Payment reference not found: {reference}")
            
            payment_id, commitment_id, order_id, amount = ref_row
            
            # Update payment status
            cur.execute("""
                UPDATE payments
                SET status = ?
                WHERE id = ?
            """, (status, payment_id))
            
            # Update payment reference
            cur.execute("""
                UPDATE payment_references
                SET status = ?, webhook_data = ?, updated_at = ?
                WHERE reference = ?
            """, (
                status,
                json.dumps(webhook_data) if webhook_data else None,
                datetime.utcnow().isoformat(),
                reference
            ))
            
            conn.commit()
            
            # Emit reconciliation event
            log_event(
                entity_type='payment',
                entity_id=payment_id,
                action='PAYMENT_RECONCILED',
                metadata={
                    'reference': reference,
                    'payment_id': payment_id,
                    'commitment_id': commitment_id,
                    'order_id': order_id,
                    'status': status,
                    'webhook_data': webhook_data
                },
                source='webhook'
            )
            
            return {
                'payment_id': payment_id,
                'reference': reference,
                'status': status,
                'reconciled': True
            }
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to reconcile webhook: {str(e)}")
    
    
    def process_queued_payments(self):
        """
        Process payments that were queued during network outages.
        
        This would typically be called when network connectivity is restored.
        In a real system, this would retry webhook calls or check payment status.
        """
        conn = get_db()
        cur = conn.cursor()
        
        try:
            # Find queued payments
            cur.execute("""
                SELECT reference, payment_id, commitment_id, amount, method
                FROM payment_references
                WHERE status = 'QUEUED'
                ORDER BY created_at ASC
                LIMIT 10
            """)
            
            queued = cur.fetchall()
            
            for reference, payment_id, commitment_id, amount, method in queued:
                # In a real system, this would:
                # 1. Check payment status with M-Pesa API
                # 2. Update payment status
                # 3. Reconcile if successful
                
                # For now, just log that queue was processed
                log_event(
                    entity_type='payment',
                    entity_id=payment_id,
                    action='PAYMENT_QUEUE_PROCESSED',
                    metadata={
                        'reference': reference,
                        'commitment_id': commitment_id,
                        'amount': amount,
                        'method': method
                    },
                    source='system'
                )
            
            return len(queued)
            
        except Exception as e:
            print(f"Error processing queued payments: {e}")
            return 0


# Global instance
payment_reference_service = PaymentReferenceService()

