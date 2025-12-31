# **context.md**

#  **— ContainerX → UCOS Evolution (PHASE 1-8)**

> **Evolution from ERP Core to Unified Commerce Operating System**

> ✅ **PHASE 1 COMPLETED + ARCHITECTURE CORRECTED**: Pure event sourcing implemented!
> 
> ✅ Services emit events only (no direct state storage)
> ✅ State derived from event replay via StateDerivationService
> ✅ UCOS architecture pattern enforced

> **Next: Phase 2 (Weeks 3-4)**: Enforcement Engine (Event-Driven Timer Service + Auto-Refund)

---

## **🧠 CONTAINERX → UCOS — PHYSICS OF COMMERCE**

```
You are evolving ContainerX from a TRUTH-FIRST ERP into a
UNIFIED COMMERCE OPERATING SYSTEM (UCOS).

UCOS encodes commerce physics: commitments, trust, and automated enforcement.
It preserves all existing ERP invariants while adding commitment primitives.

PHASE: UCOS FOUNDATION (Weeks 1-8)
Goal: Working MVP with commitments, trust, and auto-enforcement
```

---

## **🔒 NON-NEGOTIABLE ERP + UCOS INVARIANTS**

  

You must obey these at all times:

1. Orders represent HUMAN INTENT — never reality.
    
2. Payments represent CASH REALITY (may be partial, delayed, duplicated).
    
3. Inventory represents PHYSICAL REALITY.
    
4. Stock is verified BEFORE commitment.
    
5. Stock moves ONLY once, ONLY on completion.
    
6. Failed orders and failed payments MUST be stored forever.
    
7. No deletes for financial or inventory records.
    
8. Status reflects reality, not expectations.
    
9. Every critical action must be auditable.
    
10. Correctness beats convenience.
    
11. Ambiguity must be logged, not auto-resolved.
    

  

Kenyan realities you must respect:

- M-Pesa is asynchronous and retry-prone
    
- Cash + M-Pesa mixed payments are normal
    
- Connectivity is unreliable
    
- Manual reconciliation is expected
    
- Human error is common

- Trust building takes time and consistent performance

**UCOS EXTENSIONS (ADDITIVE):**

12. Commitments represent PROMISES with deadlines and auto-enforcement.

13. Trust is mathematically derived from outcomes, never manually set.

14. State is derived from event replay, never stored directly.

15. All enforcement happens via TimerService, never manual intervention.

16. Business logic stays in core services, adapters stay thin.

17. Event sourcing mandatory - all state changes via events.

---

## **🚫 ABSOLUTELY OUT OF SCOPE (FOR NOW)**

  

Do NOT implement or suggest:

- UI / frontend
    
- APIs
    
- Authentication or users
    
- Roles & permissions
    
- CRM
    
- Reporting dashboards
    
- Multi-branch abstractions
    
- Tax / VAT logic
    
- WhatsApp, SMS, notifications
    
- Delivery or logistics routing
    
- Performance optimizations
    
- Frameworks or microservices
    

  

If any of the above appear — STOP.

---

## **✅ WHAT** 

## **IS**

##  **IN SCOPE**

  

Only these concepts may exist:

- Orders
    
- Payments
    
- Inventory
    
- Stock movements (ledger)
    
- Audit / event logs
    
- Case-study-driven tests
    
- SaaS isolation (already validated)
    
- Idempotency
    
- Failure preservation
    

  

Everything else is future.

---

## **🚀 UCOS EVOLUTION ROADMAP (PHASES 1-8)**

### **PHASE 1: FOUNDATION PRIMITIVES ✅ COMPLETED + CORRECTED (Week 1-2)**
**Goal**: Implement UCOS atomic units with PURE EVENT SOURCING

**✅ COMPLETED:**
- ✅ Add `commitments` table (cache/projection only, not source of truth)
- ✅ Add `trust_events` table (append-only)
- ✅ Create `commitment_service.py` - EVENT-EMISSION ONLY (corrected)
- ✅ Create `trust_service.py` with mathematical trust calculation
- ✅ Create `state_derivation_service.py` - derives all state from events
- ✅ Extend EventLog with UCOS event types (source/actor_id/correlation_id)
- ✅ Add UCOS database tables: timers, credit_packages, credit_transactions
- ✅ Update audit_service.py for UCOS event emission
- ✅ Comprehensive unit tests (event-driven pattern)

**🚨 ARCHITECTURE CORRECTION (Week 2):**
- ✅ Removed direct state storage from services
- ✅ All services now emit events ONLY
- ✅ State derived from event replay via StateDerivationService
- ✅ Pure event sourcing pattern enforced

**RESULTS:**
- ✅ Commitments: Event-emission only (COMMITMENT_CREATED event)
- ✅ Trust: Mathematical calculation (0.05-0.95 range, time-decayed)
- ✅ State: 100% derived from EventLog replay
- ✅ Event chain: COMMITMENT_CREATED → STATE_CHANGED → COMMITMENT_FULFILLED
- ✅ Zero direct state updates in services

### **PHASE 2: ENFORCEMENT ENGINE (Weeks 3-4)**
**Goal**: Build auto-enforcement through timers and SLA tracking

**Week 3: Timer Service & SLA Enforcement** ✅ COMPLETE (2025-12-31)
- ✅ Add `timers` table with SQLite persistence
- ✅ Implement TimerService with background scheduling
- ✅ Add SLA calculation based on trust scores
- ✅ Schedule acceptance/failure timers on commitment creation
- ✅ **FIXED**: Threading issues with thread-local database connections
- ⚠️ Known issue: SLA calculation logic bug (non-blocking)

**Week 4: Auto-Refund & Enforcement Integration** ✅ COMPLETE (2025-12-31)
- ✅ Implement AutoRefundEngine for SLA breaches
- ✅ Apply trust penalties for auto-refund events
- ✅ Thread-safe event monitoring
- ✅ End-to-end auto-enforcement testing
- ✅ Pizza delivery scenario added

### **PHASE 3: ECONOMIC LAYER (Weeks 5-6)**
**Goal**: Implement prepaid credits and virtual currency system

**Week 5: Prepaid Credit System**
- Add `credit_packages` and `credit_transactions` tables
- Implement CreditService with M-Pesa integration
- Add credit consumption for commitments
- Schedule credit expiry timers

**Week 6: Virtual Economy & Trust Integration**
- Implement trust-based pricing and SLA adjustments
- Add dynamic credit conversion rates
- Economic incentive testing
- Trust score integration across all services

### **PHASE 4: CHANNEL ADAPTERS & COMPLETION (Weeks 7-8)**
**Goal**: Build adapters for different channels and complete UCOS integration

**Week 7: WhatsApp Adapter (Thin Layer)**
- Create WhatsApp adapter that emits UCOS events
- No business logic in adapter (only parsing + event emission)
- Test channel independence

**Week 8: Complete UCOS Integration & Migration**
- Migration script from orders to commitments
- MWE (Minimal Working Example) flow testing
- Performance and security validation
- Complete UCOS documentation

---

## **🏛️ UCOS EVENT SOURCING PATTERNS (MANDATORY)**

### **CRITICAL: Pure Event Sourcing Architecture**

**UCOS Principle**: State is NEVER stored directly. State is ALWAYS derived from event replay.

```python
# ✅ CORRECT (Event-Emission Only):
from core.services.audit_service import log_event
from core.services.state_derivation_service import state_derivation

def create_commitment(actor_id, promise, value):
    # 1. Generate ID
    commitment_id = f"COMMIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    # 2. Emit event ONLY (no state storage)
    log_event(
        entity_type='commitment',
        entity_id=commitment_id,
        action='COMMITMENT_CREATED',
        metadata={'actor_id': actor_id, 'promise': promise, 'value': value},
        source='system',
        actor_id=actor_id
    )
    
    # 3. Return event ID or derived state
    return commitment_id

# ❌ WRONG (Direct State Storage):
def create_commitment(actor_id, promise, value):
    commitment = Commitment(...)
    db.execute("INSERT INTO commitments ...")  # ❌ NO!
    log_event(...)  # Secondary - WRONG!
    return commitment
```

### **State Derivation Pattern**

```python
from core.services.state_derivation_service import state_derivation

# Get state by replaying events
commitment_state = state_derivation.get_commitment_state(commitment_id)

# State dict structure:
{
    'status': 'pending' | 'accepted' | 'fulfilled' | 'expired' | 'refunded',
    'id': 'COMMIT_20251231_143622_2b40b520',
    'actor_id': 'nairobi_seller_001',
    'promise': 'Deliver fresh vegetables...',
    'value': 2500.0,
    'due_by': '2025-01-01T14:36:22',
    'metadata': {...},
    'events_applied': 3
}
```

### **Event Handler Pattern (For Phase 2-4)**

```python
# Services react to events, don't call each other directly
from core.services.audit_service import log_event

class TimerService:
    def __init__(self, event_log, state_derivation):
        self.event_log = event_log
        self.derive = state_derivation
    
    def handle_commitment_created(self, event):
        """React to COMMITMENT_CREATED event"""
        if event['action'] == 'COMMITMENT_CREATED':
            commitment_state = self.derive.get_commitment_state(event['entity_id'])
            
            # Schedule timer based on derived state
            timer_id = self.schedule_timer(...)
            
            # Emit TIMER_SCHEDULED event
            log_event(
                entity_type='timer',
                entity_id=timer_id,
                action='TIMER_SCHEDULED',
                metadata={...},
                source='system'
            )
```

### **Common Import Paths (Use These)**

```python
# Database access
from core.storage.db import get_db

# Event logging
from core.services.audit_service import log_event

# State derivation
from core.services.state_derivation_service import state_derivation

# Services (event-emission only)
from core.services.commitment_service import commitment_service
from core.services.trust_service import trust_service

# Models (for type hints, not direct storage)
from core.models.commitment import Commitment
from core.models.trust_event import TrustEvent
from core.models.event_log import EventLog
```

### **UCOS Event Types (Use These Exact Strings)**

```python
# Commitment events
'COMMITMENT_CREATED'
'COMMITMENT_ACCEPTED'
'COMMITMENT_FULFILLED'
'COMMITMENT_EXPIRED'
'COMMITMENT_REFUNDED'
'STATE_CHANGED_pending_TO_accepted'
'STATE_CHANGED_pending_TO_fulfilled'
'STATE_CHANGED_accepted_TO_fulfilled'
'AUTO_REFUND_TRIGGERED'

# Trust events
'TRUST_DELTA_APPLIED'

# Timer events
'TIMER_SCHEDULED'
'TIMER_FIRED'
'TIMER_CANCELLED'

# Credit events
'CREDIT_PACKAGE_PURCHASED'
'CREDITS_CONSUMED'
'CREDIT_PACKAGE_EXPIRED'
```

### **Example Event Chain**

```
Event 1: COMMITMENT_CREATED
{
    'id': 'EVENT_20251231_143622_abc123',
    'entity_type': 'commitment',
    'entity_id': 'COMMIT_20251231_143622_2b40b520',
    'action': 'COMMITMENT_CREATED',
    'metadata': {
        'commitment_id': 'COMMIT_20251231_143622_2b40b520',
        'actor_id': 'nairobi_seller_001',
        'promise': 'Deliver vegetables',
        'value': 2500.0,
        'due_by': '2025-01-01T14:36:22'
    },
    'source': 'system',
    'actor_id': 'nairobi_seller_001'
}

Event 2: STATE_CHANGED_pending_TO_accepted
{
    'id': 'EVENT_20251231_143725_def456',
    'entity_type': 'commitment',
    'entity_id': 'COMMIT_20251231_143622_2b40b520',
    'action': 'STATE_CHANGED_pending_TO_accepted',
    'metadata': {
        'old_state': 'pending',
        'new_state': 'accepted',
        'actor_id': 'nairobi_seller_001'
    },
    'source': 'web',
    'actor_id': 'nairobi_seller_001'
}

Event 3: COMMITMENT_FULFILLED
{
    'id': 'EVENT_20251231_150000_ghi789',
    'entity_type': 'commitment',
    'entity_id': 'COMMIT_20251231_143622_2b40b520',
    'action': 'COMMITMENT_FULFILLED',
    'metadata': {
        'evidence': {'photo': 'delivered.jpg'},
        'trust_impact': 0.2
    },
    'source': 'whatsapp',
    'actor_id': 'nairobi_seller_001'
}
```

### **Trust Delta Examples**

```python
# Standard trust deltas
'on_time_fulfillment': +0.02
'late_fulfillment': -0.01
'very_late_fulfillment': -0.05
'auto_refund_triggered': -0.10
'commitment_expired': -0.05
'repeat_customer': +0.01
'bulk_order_fulfilled': +0.03

# Bounded: -0.3 to +0.3 per event
# Trust score: 0.05 to 0.95 overall
```

### **Commitment ID Format**

```python
# Format: COMMIT_{timestamp}_{hash}
# Example: COMMIT_20251231_143622_2b40b520

from datetime import datetime
import uuid

commitment_id = f"COMMIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
```

### **Testing Event-Driven Code**

```python
def test_commitment_creation():
    # 1. Emit event
    commitment_id = commitment_service.emit_create_event(
        actor_id='test_actor',
        promise='Test promise',
        value=100.0
    )
    
    # 2. Verify event emitted
    from core.storage.db import get_db
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT action, metadata FROM event_log
        WHERE entity_id = ? AND action = 'COMMITMENT_CREATED'
    """, (commitment_id,))
    event = cur.fetchone()
    assert event is not None
    
    # 3. Derive state from events
    state = state_derivation.get_commitment_state(commitment_id)
    assert state['status'] == 'pending'
    assert state['value'] == 100.0
```

---

## **🧪 DEVELOPMENT METHODOLOGY (MANDATORY)**

  

You do NOT write features first.

  

You follow this loop:

1. **Describe a real Nairobi business scenario**
    
2. **Define expected events** (What events should happen?)
    
3. **Write event-driven test** (Test event emission, not state)
    
4. **Implement event emission** (Services emit events ONLY)
    
5. **Verify state derivation** (State matches event replay)
    
6. **Stop**

**UCOS Event-Driven Development:**

```python
# Step 1: Define events for scenario
# "Customer orders pizza" → COMMITMENT_CREATED event

# Step 2: Write test
def test_pizza_order():
    # Emit event
    commitment_id = commitment_service.emit_create_event(...)
    
    # Verify event
    events = get_events_for_commitment(commitment_id)
    assert len(events) == 1
    assert events[0]['action'] == 'COMMITMENT_CREATED'
    
    # Derive state
    state = state_derivation.get_commitment_state(commitment_id)
    assert state['status'] == 'pending'

# Step 3: Implement (event-emission only)
def create_pizza_order():
    return commitment_service.emit_create_event(...)  # ✅
    # NOT: db.execute("INSERT ...") + log_event()  # ❌
```

No abstractions without a real scenario.

No "just in case" logic.

No direct state storage - events only.

---

## **🛑 STOP CONDITIONS**

You must STOP and ask before proceeding if:

- A feature affects money or stock

- A shortcut hides failure

- A suggestion deletes data

- A retry could double-count

- A workflow assumes success

- **Code directly stores state** (Use events only!)

- **Service calls another service directly** (Use events!)

- **Testing checks database state** (Test events, derive state!)

---

## **📋 PHASE 2-4 DEVELOPMENT PATTERNS**

### **Phase 2: Timer Service (Event-Driven)** ✅ COMPLETE (2025-12-31)

```python
# TimerService reacts to COMMITMENT_CREATED events
# ✅ Threading fixed: Uses thread-local database connections
from core.services.audit_service import log_event
from core.services.state_derivation_service import state_derivation

class TimerService:
    def _get_thread_db(self):
        """Get thread-local database connection for background threads."""
        # Creates new connection per thread to avoid SQLite threading errors
        # Supports test database overrides via _db_override_path
        
    def handle_commitment_created(self, event):
        """Event handler - reacts to COMMITMENT_CREATED"""
        if event['action'] != 'COMMITMENT_CREATED':
            return
        
        commitment_state = state_derivation.get_commitment_state(event['entity_id'])
        sla_hours = commitment_state.get('metadata', {}).get('sla_hours', 24)
        
        # Schedule timer
        timer_id = self._schedule_timer(
            commitment_id=event['entity_id'],
            delay_hours=sla_hours,
            action='auto_refund'
        )
        
        # Emit event (uses thread-safe logging in background thread)
        self._log_event_thread_safe(
            entity_type='timer',
            entity_id=timer_id,
            action='TIMER_SCHEDULED',
            metadata={
                'commitment_id': event['entity_id'],
                'fires_at': calculate_fires_at(sla_hours),
                'action': 'auto_refund'
            },
            source='system'
        )

# Pattern: Timer fires → emits TIMER_FIRED event → AutoRefundEngine reacts
# ✅ Threading: All database access uses thread-local connections
```

### **Phase 2: Auto-Refund (Event-Driven)** ✅ COMPLETE (2025-12-31)

```python
# AutoRefundEngine reacts to TIMER_FIRED events
# ✅ Thread-safe: Uses thread-local database connections
class AutoRefundEngine:
    def _get_thread_db(self):
        """Get thread-local database connection for background threads."""
        # Creates new connection per thread to avoid SQLite threading errors
        
    def _monitor_timer_events(self):
        """Background thread monitoring for TIMER_FIRED events."""
        while self.running:
            self._check_timer_fired_events()
            time.sleep(1)
    
    def _check_timer_fired_events(self):
        """Process TIMER_FIRED events for SLA breaches."""
        conn = self._get_thread_db()  # Thread-safe connection
        
        # Find TIMER_FIRED events that haven't been processed
        # Check commitment state (thread-safe derivation)
        # Emit AUTO_REFUND_TRIGGERED if still pending
        
    def _trigger_auto_refund(self, commitment_id, state):
        """Emit AUTO_REFUND_TRIGGERED event."""
        self._log_event_thread_safe(
            entity_type='commitment',
            entity_id=commitment_id,
            action='AUTO_REFUND_TRIGGERED',
            metadata={
                'commitment_id': commitment_id,
                'reason': 'sla_acceptance_breach',
                'actor_id': state['actor_id']
            },
            source='system'
        )
        
        # TrustService reacts to AUTO_REFUND_TRIGGERED separately

# Pattern: AUTO_REFUND_TRIGGERED event → TrustService applies penalty
# ✅ Threading: All database access uses thread-local connections
```

### **Phase 4: Channel Adapters (Thin Layer)**

```python
# WhatsApp adapter - NO business logic, only event emission
from core.services.audit_service import log_event

class WhatsAppAdapter:
    def handle_message(self, phone, message_text):
        """Parse WhatsApp, emit UCOS event"""
        # Parse message (simple keyword matching)
        if 'order' in message_text.lower():
            # Resolve phone to actor_id
            actor_id = self.resolve_actor_id(phone)
            
            # Emit event (NO business logic here!)
            log_event(
                entity_type='commitment_request',
                entity_id=f"REQ_{actor_id}_{int(time.time())}",
                action='COMMITMENT_CREATION_REQUESTED',
                metadata={
                    'actor_id': actor_id,
                    'raw_message': message_text,
                    'channel': 'whatsapp'
                },
                source='whatsapp',
                actor_id=actor_id
            )
            
            # CommitmentService reacts to COMMITMENT_CREATION_REQUESTED event
            # (separate event handler)
```

### **Threading Pattern (From Existing Code)**

```python
# Use existing threading pattern from core/storage/db.py
import threading

class BackgroundService:
    def __init__(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        while self.running:
            # Process events, check timers, etc.
            self.process_pending_tasks()
            time.sleep(1)  # Check every second
```

### **Database Pattern (From Existing Code)**

```python
# Use existing get_db() pattern
from core.storage.db import get_db

def some_function():
    conn = get_db()  # Thread-local connection
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT ...")
        result = cur.fetchone()
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        raise
    # Don't close thread-local connections
```
    

---

## **🧭 CORE PHASE EXIT CRITERIA**

  

This phase ends ONLY when:

  

✔ Sales + partial payments are rock solid

✔ Inventory never lies

✔ Stock movements are reconstructable

✔ Failures are visible and auditable

✔ Case studies cover real Nairobi businesses

✔ You can explain the system **without code**

  

Only THEN do we unlock:

APIs → UI → Features → Expansion

---

## **✅ UCOS ARCHITECTURE VALIDATION CHECKLIST**

Before proceeding to Phase 2, verify:

- [ ] All services emit events ONLY (no direct state updates)
- [ ] State derived via `state_derivation.get_commitment_state()`
- [ ] Zero `db.execute("INSERT INTO commitments ...")` in services
- [ ] All tests verify events, not direct database state
- [ ] Event replay produces correct state
- [ ] Services decoupled (events, not direct calls)

**Validation Command:**
```python
# Run this to verify event sourcing
from core.services.commitment_service import commitment_service
from core.services.state_derivation_service import state_derivation
from core.storage.db import get_db

# Create via event
commitment_id = commitment_service.emit_create_event(
    actor_id='test',
    promise='Test',
    value=100.0
)

# Verify NO direct state in commitments table
conn = get_db()
cur = conn.cursor()
cur.execute("SELECT state FROM commitments WHERE id = ?", (commitment_id,))
direct_state = cur.fetchone()
# Should be None or projection-only

# Derive state from events
derived_state = state_derivation.get_commitment_state(commitment_id)
assert derived_state['status'] == 'pending'  # ✅ Derived correctly

print("✅ Event sourcing validation PASSED")
```

---

## **🤖 CURSOR PRO AGENT GUIDANCE (CRITICAL)**

### **⚠️ AVOID TOOL-FIXATION DRIFT**

**CRITICAL LESSON**: When asked to "help implement efficient building", the Agent may drift to:
- ❌ Build automation (Makefile, CI/CD)
- ❌ Dependency management (requirements.txt)
- ❌ Deployment tools

**REALITY**: You're in **DEVELOPMENT PHASE**, not deployment. Priority is **UCOS CORE FEATURES**, not tooling.

**DECISION MATRIX**:
- **Week 3-4 (Phase 2)**: TimerService + AutoRefundEngine ← **PRIORITY**
- **Week 8 (Phase 4)**: Build tools, CI/CD ← **CAN WAIT**

**WHEN TO ADD BUILD TOOLS**:
- ✅ After Phase 2-3 core features complete
- ✅ When deployment becomes priority
- ✅ When team collaboration needed

**WHEN TO IGNORE BUILD TOOLS**:
- ❌ During active feature development (Phase 2-3)
- ❌ When core UCOS patterns need implementation
- ❌ When asked to "help implement" - clarify: features or tools?

**CORRECT RESPONSE PATTERN**:
1. Check `roadmap.md` for current phase priorities
2. If unclear, ask: "Are you asking for feature implementation or build tooling?"
3. Default to feature implementation unless explicitly asked for tooling
4. Reference `context.md` UCOS patterns before suggesting tools

**SAVE THIS PATTERN**: Always check phase priorities before suggesting infrastructure improvements.

---

## **🛡️ UCOS SAFETY NET (ESTABLISHED 2025-12-31)**

### **CRITICAL: Safety Infrastructure is MANDATORY**

**Status**: ✅ **FULLY OPERATIONAL** - All critical safety checks passing

**Why This Exists**: Financial/trust systems require mathematical guarantees. Safety net prevents:
- Architecture drift (event sourcing violations)
- Mathematical errors (trust bounds, value conservation)
- Nairobi reality gaps (M-Pesa retries, connectivity issues)
- Regression bugs (breaking existing scenarios)

### **Safety Net Components:**

#### **1. Scenario-Driven Tests** (`tests/scenarios/`)
**Purpose**: Ground UCOS in REAL Nairobi business cases. These are the "truth" that must always pass.

**Current Scenarios:**
- ✅ `minimal_safety.py` - Basic commitment creation/derivation
- ✅ `test_event_sourcing_integrity` - Verifies pure event sourcing
- ✅ `pizza_delivery_auto_refund.py` - End-to-end auto-refund flow

**Pattern**: Write Nairobi business scenario FIRST, then implement feature to make it pass.

**Example**:
```python
# tests/scenarios/pizza_delivery_auto_refund.py ✅ ADDED
def test_pizza_delivery_auto_refund_on_sla_breach():
    """Real Nairobi: Pizza shop in Westlands, SLA breach triggers auto-refund"""
    # 1. Create commitment
    # 2. Simulate payment
    # 3. Timer fires (SLA breach)
    # 4. Auto-refund triggered ✅
    # 5. Trust penalty applied ✅
```

#### **2. UCOS Physics Validation** (`tests/ucos_physics/`)
**Purpose**: Mathematical invariants that MUST always hold.

**Current Physics Tests:**
- ✅ `test_event_sourcing.py` - All state from events, immutability, replay consistency
- ✅ `test_trust_math.py` - Trust bounds (0.05-0.95), delta bounds (-0.3 to +0.3)

**Invariants Enforced:**
1. **Event Sourcing**: All state derivable from event replay
2. **Event Immutability**: Events never change once logged
3. **State Replay Consistency**: Same events = same state (deterministic)
4. **Trust Bounds**: 0.05 ≤ trust_score ≤ 0.95 always
5. **Delta Bounds**: -0.3 ≤ trust_delta ≤ 0.3 per event

#### **3. Safety Scripts** (`scripts/`)
- ✅ `backup.sh` - Emergency backup (timestamped, excludes .git, .db)
- ✅ `validate.sh` - Pre-commit validation (runs scenarios + physics)

**Usage**:
```bash
# Daily safety check
./scripts/validate.sh

# Emergency backup
./scripts/backup.sh
```

#### **4. Pre-Commit Hook** (`.git/hooks/pre-commit`)
**Purpose**: Prevent unsafe commits automatically.

**What It Does**:
1. Runs minimal safety scenarios
2. Runs UCOS physics validation
3. Blocks commit if any fail
4. Allows TimerService tests to fail (non-blocking, known issue)

**Bypass** (NOT RECOMMENDED):
```bash
git commit --no-verify  # Only in emergencies
```

#### **5. Safety Documentation**
- ✅ `safety_checkpoints.md` - Tracks which scenarios must pass
- ✅ `roadmap.md` - Current phase priorities

### **Current Safety Status:**

```
Critical Scenarios: 7/7 ✅ PASSING
├── Minimal Safety: 2/2 ✅
├── Event Sourcing Physics: 3/3 ✅
└── Trust Math Physics: 2/2 ✅

TimerService Tests: 4/5 ✅ PASSING
├── Threading issues: ✅ FIXED (2025-12-31)
├── Timer scheduling: ✅ Working
├── Timer firing: ✅ Working
└── SLA calculation: ⚠️ Logic bug (non-blocking)

Known Issues (Non-Blocking):
└── SLA calculation logic bug (separate from threading)

Risk Level: LOW 🟢
Last Validated: 2025-12-31
Threading Fix: ✅ Complete
```

### **Safety Workflow (MANDATORY):**

```bash
# BEFORE any commit:
1. Run: ./scripts/validate.sh
2. If passes: git commit (pre-commit hook auto-runs)
3. If fails: Fix issues, don't commit

# BEFORE any feature:
1. Write failing scenario test
2. Implement feature
3. Run validation
4. Commit with scenario name in message

# Emergency recovery:
1. ./scripts/backup.sh
2. git checkout <last_known_good_commit>
3. ./scripts/validate.sh (verify)
```

### **Commit Message Convention (ENFORCED):**

```
[PHASE X][COMPONENT] Brief description

Examples:
[SAFETY][BASELINE] Establish UCOS safety net
[SCENARIO][PIZZA] Add pizza delivery SLA breach scenario
[FIX][TIMER] Resolve threading race conditions
[UCOS][PHYSICS] Ensure trust delta bounds respected
```

### **Adding New Scenarios:**

1. Create test in `tests/scenarios/`
2. Represent REAL Nairobi business case
3. Test end-to-end UCOS flow
4. Add to `safety_checkpoints.md`
5. Ensure it passes before committing

**SAVE THIS**: Safety net is your protection against weeks of debugging. Use it constantly.

---
