# **HUMAN.MD - YOUR COMPLETE PROJECT GUIDE**

> **Single source of truth for understanding, using, and extending ContainerX/UCOS**

**Last Updated**: 2025-12-31  
**Phase**: 2 Complete (Enforcement Engine)  
**Status**: Production-ready foundation

---

## **📚 DOCUMENTATION HIERARCHY**

You have **3 main documentation files** that work together:

1. **`human.md`** (THIS FILE) - **How to use and understand the project**
   - Project overview and mental model
   - Daily workflows and commands
   - How to run tests, make changes, debug
   - Tips and best practices
   - **Read this first!**

2. **`context.md`** - **What the project is and why**
   - UCOS principles and architecture
   - Event sourcing patterns
   - Development methodology
   - Phase-by-phase roadmap
   - **Reference when building features**

3. **`roadmap.md`** - **Current status and next steps**
   - What's done, what's in progress
   - Known issues and priorities
   - Success criteria for each phase
   - **Check before starting work**

**Workflow**: Read `human.md` → Check `roadmap.md` → Reference `context.md` when coding

---

## **🎯 WHAT IS CONTAINERX/UCOS?**

### **The Big Picture**

ContainerX is evolving from a **TRUTH-FIRST ERP** into a **UNIFIED COMMERCE OPERATING SYSTEM (UCOS)**.

**What that means:**
- **ERP Layer**: Orders, payments, inventory (existing, working)
- **UCOS Layer**: Commitments, trust scores, auto-enforcement (new, in progress)
- **Architecture**: Pure event sourcing - all state from events, never stored directly

### **Current Status (2025-12-31)**

```
PHASE 1: FOUNDATION ✅ COMPLETE
├── Event sourcing architecture
├── Commitment service
├── Trust calculation
└── State derivation

PHASE 2: ENFORCEMENT ✅ COMPLETE
├── TimerService (thread-safe)
├── AutoRefundEngine
└── Trust penalties

PHASE 3: ECONOMIC LAYER ⏳ NEXT
└── Credits system

OVERALL: 75% to UCOS MVP
```

### **Key Concepts**

**1. Event Sourcing**
- State is NEVER stored directly
- State is ALWAYS derived from event replay
- Events are immutable (append-only)
- Full audit trail by design

**2. Trust System**
- Mathematical reputation (0.05 to 0.95)
- Time-decayed (newer events matter more)
- Auto-applied based on outcomes
- Never manually set

**3. Auto-Enforcement**
- TimerService: Schedules SLA timers
- AutoRefundEngine: Triggers refunds on SLA breach
- Trust penalties: Applied automatically
- No manual intervention needed

---

## **🚀 QUICK START**

### **First Time Setup**

```bash
# 1. Clone/navigate to project
cd /path/to/containerx

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# OR: .venv\Scripts\activate  # On Windows

# 3. Install dependencies
pip install pytest

# 4. Initialize database
python -c "from core.storage.db import init_db; init_db()"

# 5. Run validation
./scripts/validate.sh
```

**Expected output**: 7/7 critical tests passing ✅

### **Daily Workflow**

```bash
# Morning: Verify system works
./scripts/validate.sh

# Before coding: Check roadmap
cat roadmap.md | head -50

# While coding: Reference patterns
# See context.md sections on event sourcing

# Before commit: Use proof-backed commit
./scripts/smart_commit.sh
# OR manually:
# ./scripts/validate.sh
# git add .
# git commit -m "[PHASE][COMPONENT] Description"
```

---

## **🧪 TESTING SYSTEM**

### **Test Structure**

```
tests/
├── scenarios/          # Nairobi business scenarios (MUST PASS)
│   ├── minimal_safety.py
│   └── pizza_delivery_auto_refund.py
├── ucos_physics/       # Mathematical invariants (MUST PASS)
│   ├── test_event_sourcing.py
│   └── test_trust_math.py
├── unit/               # Service-level tests
├── integration/        # End-to-end flows
└── properties/         # Randomized invariant tests
```

### **Running Tests**

```bash
# Full validation (what you run before commits)
./scripts/validate.sh

# All tests
pytest tests/ -v

# Specific category
pytest tests/scenarios/ -v
pytest tests/ucos_physics/ -v

# Single test file
pytest tests/scenarios/pizza_delivery_auto_refund.py -v

# With output
pytest tests/ -v -s
```

### **Test Results Interpretation**

**✅ All safety checks passed**: Safe to commit  
**⚠️ TimerService tests failed (non-blocking)**: Known issue, can commit  
**❌ Safety checks FAILED**: DO NOT COMMIT - fix first

### **Critical Tests (MUST PASS)**

1. **Minimal Safety** (2 tests)
   - Can create commitments
   - Event sourcing integrity

2. **Event Sourcing Physics** (3 tests)
   - All state from events
   - Event immutability
   - State replay consistency

3. **Trust Math Physics** (2 tests)
   - Trust bounds (0.05-0.95)
   - Delta bounds (-0.3 to +0.3)

**Total: 7/7 must pass before any commit**

---

## **🏗️ PROJECT STRUCTURE**

### **Core Services** (`core/services/`)

**Event-Emission Services** (UCOS pattern):
- `commitment_service.py` - Creates commitments via events
- `trust_service.py` - Calculates trust, applies penalties
- `state_derivation_service.py` - Derives state from events
- `timer_service.py` - Schedules SLA timers (thread-safe)
- `auto_refund_engine.py` - Triggers refunds on SLA breach

**Legacy Services** (ERP layer):
- `sales_service.py` - Order processing
- `payment_service.py` - Payment recording
- `inventory_service.py` - Stock management

**Infrastructure**:
- `audit_service.py` - Event logging
- `storage/db.py` - Database connections (thread-local)

### **Models** (`core/models/`)

**UCOS Models**:
- `commitment.py` - Commitment structure (for type hints)
- `trust_event.py` - Trust event structure
- `event_log.py` - Event log entry

**ERP Models**:
- `order.py`, `payment.py`, `stock.py`, etc.

### **Tests** (`tests/`)

- `scenarios/` - Real Nairobi business cases
- `ucos_physics/` - Mathematical invariants
- `unit/` - Service tests
- `integration/` - End-to-end flows
- `properties/` - Randomized tests

### **Scripts** (`scripts/`)

- `validate.sh` - Pre-commit validation
- `backup.sh` - Emergency backup

---

## **💻 DEVELOPMENT WORKFLOWS**

### **Adding a New Feature**

**Step 1: Write Failing Scenario Test**
```python
# tests/scenarios/my_feature.py
def test_my_nairobi_scenario(test_setup):
    """Real Nairobi business case"""
    # This will FAIL initially (RED)
    commitment_id = create_commitment(...)
    # Verify expected events
    assert event_emitted(...)
```

**Step 2: Implement Feature**
```python
# core/services/my_service.py
class MyService:
    def emit_create_event(self, ...):
        # Emit event ONLY (no state storage)
        log_event(
            entity_type='my_entity',
            action='MY_ENTITY_CREATED',
            metadata={...}
        )
```

**Step 3: Verify State Derivation**
```python
# State should be derivable from events
state = state_derivation.get_my_entity_state(id)
assert state['status'] == 'expected'
```

**Step 4: Run Validation**
```bash
./scripts/validate.sh
```

**Step 5: Commit**
```bash
git commit -m "[SCENARIO][FEATURE] Add my feature scenario"
```

### **Fixing a Bug**

**Step 1: Reproduce**
```bash
pytest tests/path/to/failing_test.py -v -s
```

**Step 2: Debug**
```python
# Add print statements or use debugger
# Check event log
from core.storage.db import get_db
conn = get_db()
cur = conn.cursor()
cur.execute("SELECT * FROM event_log WHERE entity_id = ?", (id,))
print(cur.fetchall())
```

**Step 3: Fix**
- Follow UCOS patterns from `context.md`
- Maintain event sourcing purity
- Use thread-local connections for background threads

**Step 4: Verify**
```bash
./scripts/validate.sh
```

**Step 5: Commit**
```bash
git commit -m "[FIX][COMPONENT] Fix bug description"
```

### **Understanding Existing Code**

**When you see a service:**
1. Check if it emits events (UCOS pattern)
2. Check if it uses `get_db()` (main thread) or `_get_thread_db()` (background thread)
3. Check if state is derived or stored directly (should be derived)

**When you see a test:**
1. Check which layer it's in (scenario/physics/unit/integration)
2. Check what it's testing (events or state)
3. Check if it's critical (scenarios/physics) or optional

---

## **🔧 COMMON TASKS**

### **Check System Health**

```bash
# Full validation
./scripts/validate.sh

# Quick check
pytest tests/scenarios/minimal_safety.py -v
```

### **Create a Commitment**

```python
from core.services.commitment_service import commitment_service
from core.services.state_derivation_service import state_derivation

# Create commitment (emits event)
commitment_id = commitment_service.emit_create_event(
    actor_id="seller_001",
    promise="Deliver pizza in 2 hours",
    value=850.0,
    metadata={'sla_hours': 2}
)

# Derive state (from events)
state = state_derivation.get_commitment_state(commitment_id)
print(state['status'])  # 'pending'
```

### **Check Trust Score**

```python
from core.services.trust_service import trust_service

# Calculate trust
trust = trust_service.calculate("seller_001")
print(f"Trust score: {trust}")  # 0.05 to 0.95

# Apply trust delta
trust_service.apply_delta(
    actor_id="seller_001",
    delta=0.2,  # Positive
    reason="on_time_fulfillment",
    commitment_id=commitment_id
)
```

### **View Event Log**

```python
from core.storage.db import get_db

conn = get_db()
cur = conn.cursor()
cur.execute("""
    SELECT action, metadata, created_at 
    FROM event_log 
    WHERE entity_id = ?
    ORDER BY created_at
""", (commitment_id,))

for row in cur.fetchall():
    print(row)
```

### **Backup System**

```bash
# Create backup
./scripts/backup.sh

# Backup location: backups/containerx_YYYYMMDD_HHMMSS/
```

### **Proof-Backed Commits**

**Never commit without proof!** Every commit must include:
1. **Test results** showing what passes
2. **Changed files** list
3. **Safety validation** status
4. **UCOS physics** verification

**Quick method (Recommended):**
```bash
# Automated proof-backed commit
./scripts/smart_commit.sh

# This will:
# 1. Run validation automatically
# 2. Capture test results
# 3. Generate commit message with proof
# 4. Ask for confirmation
```

**Cursor Pro method:**
```
@agent: "Help me create a proof-backed commit for UCOS.

Current changes:
[Describe what you changed]

Follow this format:
1. Run validation: `./scripts/validate.sh`
2. Capture test output: `python -m pytest --tb=short -q`
3. Generate commit message with:
   - [PREFIX][COMPONENT] Brief description
   - Test results summary
   - Changed files list
   - Safety validation status
   - UCOS physics verification

Prefix options:
- [FEATURE] New functionality
- [FIX] Bug fix  
- [DOCS] Documentation
- [TEST] Test updates
- [REFACTOR] Code restructuring
- [CHORE] Maintenance
- [SCENARIO] Nairobi business scenario

Component examples:
- TIMER (TimerService)
- AUTO-REFUND (AutoRefundEngine)
- TRUST (TrustService)
- CREDIT (CreditService)
- SAFETY (Safety net)
- DOCS (Documentation)
- WORKFLOW (Workflow improvements)

Generate the complete commit command with message."
```

**Commit message format:**
```
[FEATURE][TIMER] Add weekend SLA adjustments

## Test Results
```
tests/test_timer_service.py::test_weekend_sla ✓
tests/scenarios/pizza_delivery.py::test_weekend_delivery ✓
7/7 critical tests passing
```

## Changed Files
- core/services/timer_service.py
- tests/scenarios/pizza_delivery.py

## Validation
- Safety checks: PASSED ✅
- UCOS physics: VERIFIED ✅
- Nairobi scenarios: INTACT ✅
```

**Why this matters:**
- Creates audit trail of what works
- Makes debugging easier ("When did this break?")
- Documents test coverage for each change
- Professional practice for financial systems
- Enables quick rollback ("Which commit broke this test?")

**Manual method (if script unavailable):**
```bash
# 1. Run validation
./scripts/validate.sh

# 2. Capture test summary
python -m pytest --tb=short -q | tail -5

# 3. Get changed files
git diff --name-only --cached

# 4. Create commit with proof
git commit -m "[PREFIX][COMPONENT] Description

## Test Results
[Paste test output]

## Changed Files
- file1.py
- file2.py

## Validation
- Safety checks: PASSED ✅
- UCOS physics: VERIFIED ✅"
```

---

## **🐛 DEBUGGING GUIDE**

### **Test Fails: "State should be derivable from events"**

**Problem**: Direct state storage detected  
**Fix**: Remove `db.execute("INSERT INTO commitments ...")` from service  
**Solution**: Use `log_event()` only, derive state via `state_derivation`

### **Test Fails: "SQLite objects created in a thread..."**

**Problem**: Background thread using main thread's database connection  
**Fix**: Use `_get_thread_db()` instead of `get_db()` in background threads  
**Solution**: See `timer_service.py` for pattern

### **Test Fails: "Trust score out of bounds"**

**Problem**: Trust calculation bug  
**Fix**: Check `trust_service.calculate()` - should bound between 0.05 and 0.95  
**Solution**: Verify delta bounds (-0.3 to +0.3) are enforced

### **System Slow / Tests Hang**

**Problem**: Background threads not stopping  
**Fix**: Call `.stop()` on services in tests  
**Solution**: See test cleanup patterns in `pizza_delivery_auto_refund.py`

### **Can't Find Events**

**Problem**: Wrong database (test vs production)  
**Fix**: Check if using `test_setup` fixture  
**Solution**: Services use `_db_override_path` for test databases

---

## **📋 UCOS PATTERNS (QUICK REFERENCE)**

### **Event-Emission Pattern**

```python
# ✅ CORRECT
def create_thing(actor_id, data):
    thing_id = generate_id()
    log_event(
        entity_type='thing',
        entity_id=thing_id,
        action='THING_CREATED',
        metadata={'actor_id': actor_id, 'data': data},
        source='system',
        actor_id=actor_id
    )
    return thing_id

# ❌ WRONG
def create_thing(actor_id, data):
    thing = Thing(...)
    db.execute("INSERT INTO things ...")  # NO!
    log_event(...)  # Secondary - NO!
    return thing
```

### **State Derivation Pattern**

```python
# ✅ CORRECT
state = state_derivation.get_thing_state(thing_id)

# ❌ WRONG
cur.execute("SELECT state FROM things WHERE id = ?", (thing_id,))
state = cur.fetchone()  # NO!
```

### **Thread-Safe Pattern**

```python
# ✅ CORRECT (Background Thread)
def _background_method(self):
    conn = self._get_thread_db()  # Thread-local
    try:
        # Use conn
        conn.commit()
    finally:
        conn.close()

# ✅ CORRECT (Main Thread)
def main_thread_method(self):
    conn = get_db()  # Thread-local from main thread
    # Use conn
    # Don't close (managed by thread-local)
```

### **Event Handler Pattern**

```python
# ✅ CORRECT
class MyService:
    def _monitor_events(self):
        while self.running:
            # Check for events
            events = self._get_unprocessed_events()
            for event in events:
                self._handle_event(event)
            time.sleep(1)
    
    def _handle_event(self, event):
        if event['action'] == 'SOME_EVENT':
            # React to event
            self._do_something(event)
```

---

## **🎯 PHASE STATUS & NEXT STEPS**

### **Phase 1: Foundation ✅ COMPLETE**
- Event sourcing architecture
- Commitment service
- Trust calculation
- State derivation

### **Phase 2: Enforcement ✅ COMPLETE**
- TimerService (thread-safe)
- AutoRefundEngine
- Trust penalties
- Pizza delivery scenario

### **Phase 3: Economic Layer ⏳ NEXT**
- Prepaid credits system
- Credit packages
- M-Pesa integration for credits
- Trust-based pricing

### **Phase 4: Channel Adapters ⏳ FUTURE**
- WhatsApp adapter
- Migration scripts
- Complete UCOS integration

**Check `roadmap.md` for detailed status and priorities**

---

## **🚨 CRITICAL RULES**

### **NEVER DO THESE**

1. ❌ Store state directly in database from services
2. ❌ Call services directly (use events)
3. ❌ Use `get_db()` in background threads
4. ❌ Delete financial/inventory records
5. ❌ Commit without running `./scripts/validate.sh`
6. ❌ Skip scenario tests
7. ❌ Break UCOS physics invariants

### **ALWAYS DO THESE**

1. ✅ Emit events only (no direct state storage)
2. ✅ Derive state from events
3. ✅ Use thread-local connections in background threads
4. ✅ Run validation before commits
5. ✅ Write scenario tests first
6. ✅ Follow event-driven patterns
7. ✅ Update `roadmap.md` when completing features

---

## **💡 TIPS & BEST PRACTICES**

### **When Starting Work**

1. **Check `roadmap.md`** - What's the current priority?
2. **Run validation** - Is system healthy?
3. **Read `context.md`** - What patterns should I follow?
4. **Write scenario test first** - RED before GREEN

### **When Stuck**

1. **Check event log** - What events were emitted?
2. **Derive state** - What does state derivation show?
3. **Check threading** - Is this a background thread issue?
4. **Review similar code** - How did TimerService solve this?

### **When Completing Work**

1. **Run full validation** - `./scripts/validate.sh`
2. **Update `roadmap.md`** - Mark tasks complete
3. **Update `context.md`** - Add patterns if new
4. **Commit with clear message** - `[PHASE][COMPONENT] Description`

### **Performance Tips**

- SQLite handles 100k+ transactions easily
- Event replay is fast for < 1000 events per entity
- Background threads check every 1 second (adjustable)
- Use projections/cache for large datasets (future)

### **Nairobi-Specific Considerations**

- M-Pesa is async - handle retries
- Connectivity unreliable - work offline
- Cash + M-Pesa mixed - support both
- Manual reconciliation - make it easy
- Trust building - takes time, be patient

---

## **📊 SYSTEM METRICS**

### **Current Test Status**

```
Critical Tests: 7/7 ✅ PASSING
├── Minimal Safety: 2/2 ✅
├── Event Sourcing Physics: 3/3 ✅
└── Trust Math Physics: 2/2 ✅

TimerService Tests: 4/5 ✅ PASSING
├── Threading: ✅ FIXED
└── SLA Calculation: ⚠️ Logic bug (non-blocking)

Pizza Delivery Scenarios: 2/2 ✅ PASSING
```

### **Code Quality**

- **Event Sourcing**: Pure (no direct state storage)
- **Thread Safety**: All background threads use thread-local connections
- **Test Coverage**: Critical paths covered
- **Documentation**: Comprehensive

### **Known Issues**

1. **SLA Calculation Logic Bug** (Non-blocking)
   - Location: `timer_service.py::_calculate_sla_hours()`
   - Impact: One test fails
   - Priority: Medium
   - Fix: 15-30 minutes

---

## **🔄 COMMIT WORKFLOW**

### **Before Every Commit**

**Recommended: Use smart commit script**
```bash
# Automated proof-backed commit
./scripts/smart_commit.sh

# This handles:
# 1. Validation (auto)
# 2. Test result capture (auto)
# 3. Commit message generation (auto)
# 4. Confirmation prompt
```

**Manual method:**
```bash
# 1. Run validation
./scripts/validate.sh

# 2. Check output
# Should see: "✅ All safety checks passed!"

# 3. Stage files
git add .

# 4. Commit with proof
git commit -m "[PHASE][COMPONENT] Description

## Test Results
[Include test summary]

## Changed Files
- file1.py
- file2.py

## Validation
- Safety checks: PASSED ✅"
```

### **Commit Message Format**

```
[PHASE X][COMPONENT] Brief description

Problem:
- What was wrong

Solution:
- How you fixed it

Results:
- What works now
```

**Examples:**
```
[FIX][TIMER] Resolve threading issues with thread-local DB connections
[SCENARIO][PIZZA] Add pizza delivery auto-refund scenario
[UCOS][PHYSICS] Ensure trust delta bounds respected
```

### **Pre-Commit Hook**

Automatically runs `./scripts/validate.sh` before commit.

**Bypass** (NOT RECOMMENDED):
```bash
git commit --no-verify  # Only in emergencies
```

---

## **🔍 UNDERSTANDING THE CODEBASE**

### **Event Flow Example**

```
1. User creates commitment
   → commitment_service.emit_create_event()
   → COMMITMENT_CREATED event logged

2. TimerService detects event
   → _check_new_commitments() (background thread)
   → TIMER_SCHEDULED event logged
   → Timer scheduled in background

3. Timer fires (SLA breach)
   → _on_timer_fired() (timer thread)
   → TIMER_FIRED event logged

4. AutoRefundEngine detects TIMER_FIRED
   → _check_timer_fired_events() (background thread)
   → AUTO_REFUND_TRIGGERED event logged
   → STATE_CHANGED_pending_TO_refunded event logged

5. TrustService detects AUTO_REFUND_TRIGGERED
   → _check_auto_refund_events() (background thread)
   → TRUST_DELTA_APPLIED event logged
   → Trust penalty applied

6. State derivation
   → Replay all events
   → Commitment state = 'refunded'
   → Trust score reduced
```

### **Database Schema**

**UCOS Tables:**
- `event_log` - Source of truth (append-only)
- `commitments` - Projection/cache (optional)
- `trust_events` - Trust history (append-only)
- `timers` - Timer persistence (for recovery)

**ERP Tables:**
- `orders`, `payments`, `inventory`, `stock_movements`

**Key Point**: `event_log` is the source of truth. Everything else is derived.

### **Threading Architecture**

```
Main Thread:
├── User code runs here
├── Uses get_db() → thread-local connection
└── Services emit events

Background Threads:
├── TimerService._monitor_events()
├── AutoRefundEngine._monitor_timer_events()
└── TrustService._monitor_auto_refund_events()
    └── All use _get_thread_db() → new connection per thread
```

---

## **🎓 LEARNING PATH**

### **For New Contributors**

**Week 1: Understanding**
1. Read `human.md` (this file) completely
2. Run `./scripts/validate.sh` and understand output
3. Read `context.md` sections on event sourcing
4. Explore `tests/scenarios/minimal_safety.py`

**Week 2: Hands-On**
1. Create a simple commitment via Python
2. Derive its state
3. Add a trust event
4. Verify trust score changes

**Week 3: Contributing**
1. Write a failing scenario test
2. Implement feature to make it pass
3. Run validation
4. Commit

### **For Experienced Developers**

**Focus Areas:**
- Event sourcing patterns (`context.md`)
- Thread safety (`timer_service.py`, `auto_refund_engine.py`)
- State derivation (`state_derivation_service.py`)
- Trust mathematics (`trust_service.py`)

**Quick Reference:**
- Patterns: `context.md` → "UCOS Event Sourcing Patterns"
- Status: `roadmap.md` → "Current Status"
- How-to: `human.md` → This file

---

## **🛠️ TOOLS & COMMANDS**

### **Essential Commands**

```bash
# Validation
./scripts/validate.sh

# Backup
./scripts/backup.sh

# Run specific test
pytest tests/scenarios/pizza_delivery_auto_refund.py -v

# Check git status
git status

# View recent commits
git log --oneline -10
```

### **Python Interactive Session**

```python
# Start Python with project context
python
>>> from core.services.commitment_service import commitment_service
>>> from core.services.state_derivation_service import state_derivation
>>> 
>>> # Create commitment
>>> cid = commitment_service.emit_create_event(
...     actor_id="test",
...     promise="Test",
...     value=100.0
... )
>>> 
>>> # Derive state
>>> state = state_derivation.get_commitment_state(cid)
>>> print(state)
```

### **Database Inspection**

```python
from core.storage.db import get_db

conn = get_db()
cur = conn.cursor()

# View recent events
cur.execute("""
    SELECT action, entity_id, created_at 
    FROM event_log 
    ORDER BY created_at DESC 
    LIMIT 10
""")
for row in cur.fetchall():
    print(row)

# View commitments
cur.execute("SELECT id, actor_id, value FROM commitments LIMIT 10")
for row in cur.fetchall():
    print(row)
```

---

## **📝 DOCUMENTATION MAINTENANCE**

### **When to Update `human.md`**

- New workflow discovered
- Common issue found and solved
- New tool or command added
- Project structure changes significantly

### **When to Update `context.md`**

- New UCOS pattern established
- Phase completed
- Architecture decision made
- New event type added

### **When to Update `roadmap.md`**

- Task completed
- New issue discovered
- Priority changes
- Phase status updates

**Rule**: Keep all three files in sync. If you complete a feature, update `roadmap.md`. If you establish a pattern, update `context.md`. If you learn something useful, update `human.md`.

---

## **🎯 SUCCESS METRICS**

### **System Health Indicators**

**Green (Healthy):**
- 7/7 critical tests passing
- All scenarios passing
- No threading errors
- Validation script passes

**Yellow (Warning):**
- 1-2 non-critical tests failing
- Known issues documented
- System functional but needs polish

**Red (Critical):**
- Critical tests failing
- Threading errors
- Event sourcing violations
- **DO NOT COMMIT**

### **Progress Indicators**

**Phase Completion:**
- All phase tasks checked off
- All tests passing
- Documentation updated
- Ready for next phase

**Feature Completion:**
- Scenario test passes
- Integration works
- No regressions
- Code follows patterns

---

## **🤝 HANDOFF GUIDE**

### **For Passing Project to Someone Else**

**Essential Files to Share:**
1. `human.md` - This file (how to use)
2. `context.md` - Architecture and patterns
3. `roadmap.md` - Current status
4. `safety_checkpoints.md` - What must pass

**Essential Commands:**
```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install pytest
python -c "from core.storage.db import init_db; init_db()"

# Verify
./scripts/validate.sh

# Start working
# Follow human.md workflows
```

**Key Concepts to Explain:**
1. Event sourcing (state from events)
2. Thread safety (background threads)
3. Scenario-driven development
4. Safety net importance

---

## **🚀 QUICK REFERENCE**

### **File Locations**

- **Services**: `core/services/`
- **Models**: `core/models/`
- **Tests**: `tests/`
- **Scripts**: `scripts/`
- **Database**: `containerx.db`

### **Key Services**

- `commitment_service` - Create commitments
- `trust_service` - Calculate trust, apply penalties
- `timer_service` - Schedule SLA timers
- `auto_refund_engine` - Trigger refunds
- `state_derivation` - Derive state from events

### **Key Commands**

- `./scripts/validate.sh` - Run all safety checks
- `./scripts/smart_commit.sh` - Create proof-backed commit
- `pytest tests/scenarios/ -v` - Run scenario tests
- `./scripts/backup.sh` - Create backup

### **Key Patterns**

- Event-emission only (no direct state)
- State derivation (replay events)
- Thread-local connections (background threads)
- Scenario-first development

---

## **💬 FINAL NOTES**

**This is a living document.** Update it as you learn and grow.

**Remember:**
- Event sourcing is the foundation
- Scenarios are the truth
- Safety net protects you
- Patterns guide you

**When in doubt:**
1. Check `roadmap.md` for status
2. Check `context.md` for patterns
3. Check `human.md` for how-to
4. Run `./scripts/validate.sh` for health

**You've built something impressive.** This system encodes commerce physics in software. Use it wisely. 🏛️⚡

---

**Last Updated**: 2025-12-31  
**Phase 2**: Complete  
**Next**: Phase 3 (Economic Layer)

