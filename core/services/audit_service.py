import uuid
import json
from datetime import datetime
from core.storage.db import get_db
from core.models.event_log import EventLog

def log_event(entity_type, entity_id, action, metadata=None, source="system", actor_id=None, correlation_id=None):
    """
    Log an event to the audit trail (UCOS-enhanced).

    Args:
        entity_type: Type of entity (e.g., 'order', 'payment', 'inventory', 'commitment')
        entity_id: ID of the entity
        action: Action performed (e.g., 'created', 'updated', 'failed', 'COMMITMENT_CREATED')
        metadata: Optional dictionary with additional context
        source: Event source ('system', 'whatsapp', 'web', 'api')
        actor_id: ID of actor who triggered event
        correlation_id: ID for tracing related events

    Returns:
        EventLog instance

    Raises:
        Exception: If logging fails (never fails silently per ERP invariants)
    """
    event_id = str(uuid.uuid4())
    event = EventLog(
        id=event_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        metadata=metadata or {},
        source=source,
        actor_id=actor_id,
        correlation_id=correlation_id
    )

    conn = get_db()
    cur = conn.cursor()

    try:
        # Serialize metadata to JSON string
        metadata_json = json.dumps(event.metadata) if isinstance(event.metadata, dict) else str(event.metadata)

        cur.execute("""
            INSERT INTO event_log (id, entity_type, entity_id, action, metadata, created_at, source, actor_id, correlation_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.id,
            event.entity_type,
            event.entity_id,
            event.action,
            metadata_json,
            event.created_at,
            event.source,
            event.actor_id,
            event.correlation_id
        ))

        conn.commit()
        return event
    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to log event: {str(e)}")
    # Don't close thread-local connections

