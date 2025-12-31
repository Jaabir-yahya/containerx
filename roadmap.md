# **UCOS CONTAINERX - PHASE 2 PRIORITY**

## **CURRENT STATUS: WEEK 3 - PHASE 2 IMPLEMENTATION**

### **✅ PHASE 1 COMPLETE**
- Pure event sourcing implemented
- StateDerivationService working
- CommitmentService (event-emission only)
- TrustService (mathematical trust calculation)
- All services follow UCOS event-driven patterns

### **✅ SAFETY NET ESTABLISHED (2025-12-31)**
- Scenario-driven tests (`tests/scenarios/`)
- UCOS physics validation (`tests/ucos_physics/`)
- Pre-commit hooks (auto-validation)
- Backup/recovery scripts (`scripts/`)
- Safety documentation (`safety_checkpoints.md`)
- **Status**: 7/7 critical tests passing ✅

### **🎯 PHASE 2: ENFORCEMENT ENGINE (WEEKS 3-4)**

**CURRENT PRIORITY (WEEK 3):**
1. **TimerService**: Reacts to COMMITMENT_CREATED events, schedules SLA timers
2. **AutoRefundEngine**: Reacts to TIMER_FIRED events, triggers auto-refunds
3. **Event integration**: End-to-end commitment → timer → auto-refund flow

**DO NOT:**
- ❌ Add build automation yet (save for Week 8)
- ❌ Add FastAPI/Flask enhancements (out of scope per context.md)
- ❌ Add complex CI/CD (manual testing works fine)
- ❌ Add unnecessary dependencies

**DO:**
- ✅ Implement TimerService with event handlers
- ✅ Focus on UCOS patterns from context.md
- ✅ Use existing SQLite + threading patterns
- ✅ Test event-driven flow (commitment → timer → refund)

---

## **ARCHITECTURE REFERENCE**

### **Current Architecture (FROM context.md):**
- ✅ Pure event sourcing
- ✅ StateDerivationService (derives state from events)
- ✅ CommitmentService (event-emission only)
- ✅ TrustService (mathematical trust calculation)
- ✅ Thread-local database connections (core/storage/db.py)

### **Files to Reference:**
- `context.md` - UCOS patterns and event types
- `core/services/commitment_service.py` - Event-emission pattern
- `core/services/state_derivation_service.py` - State derivation pattern
- `core/services/audit_service.py` - Event logging
- `core/storage/db.py` - Database connection patterns

---

## **PHASE 2 IMPLEMENTATION PLAN**

### **Week 3: TimerService**
- [x] Create `core/services/timer_service.py`
- [x] Implement event handler for COMMITMENT_CREATED
- [x] Schedule timers based on SLA (from trust scores)
- [x] Emit TIMER_SCHEDULED events
- [x] Handle TIMER_FIRED events
- [x] Persist timers to database (timers table)
- [x] Background thread for timer monitoring
- [x] Tests for event-driven timer flow
- [x] **FIXED**: Threading issue (SQLite thread-local connections) - ✅ Complete

**Status**: ✅ Implemented, ✅ Threading fixed, ⚠️ SLA calculation logic bug (non-blocking)

### **Week 4: AutoRefundEngine**
- [ ] Create `core/services/auto_refund_engine.py`
- [ ] React to TIMER_FIRED events
- [ ] Check commitment state (via StateDerivationService)
- [ ] Emit AUTO_REFUND_TRIGGERED events
- [ ] Integration with TrustService (trust penalties)
- [ ] End-to-end tests
- [ ] Add Nairobi scenario: pizza delivery with SLA breach

**Approach**: Scenario-first development (write failing scenario, then implement)

---

## **NEXT FILE TO CREATE**

**File**: `core/services/timer_service.py`

**Pattern**: Follow event-driven pattern from `commitment_service.py`
- React to events (don't call services directly)
- Emit events (don't store state directly)
- Use StateDerivationService for current state
- Use thread-local database connections

**Reference**: See `context.md` section "Phase 2: Timer Service (Event-Driven)"

---

## **CONSTRAINTS (FROM context.md)**

- NO web frameworks (FastAPI/Flask out of scope for now)
- NO additional dependencies unless essential
- NO direct state storage (events only)
- NO service-to-service direct calls (events only)
- SQLite + threading is sufficient
- Event sourcing mandatory

---

## **SUCCESS CRITERIA**

Phase 2 complete when:
- ✅ TimerService schedules timers on COMMITMENT_CREATED
- ✅ TimerService threading fixed (✅ Complete 2025-12-31)
- ✅ Timers fire and emit TIMER_FIRED events
- [ ] AutoRefundEngine reacts to TIMER_FIRED
- [ ] Auto-refund triggers trust penalties
- [ ] End-to-end flow tested
- [ ] All state derived from events (no direct storage)
- [ ] 5+ Nairobi business scenarios passing

## **KNOWN ISSUES**

### **TimerService SLA Calculation (Non-Blocking)**
- **Issue**: SLA calculation not reducing hours for high trust scores as expected
- **Impact**: One test fails (test_timer_service_calculates_sla_from_trust)
- **Status**: Logic bug, separate from threading fix
- **Priority**: Medium (doesn't block AutoRefundEngine)
- **Location**: `timer_service.py::_calculate_sla_hours()`

### **Next Fix Priority:**
1. ✅ Fix TimerService threading (✅ Complete)
2. [ ] Fix SLA calculation logic bug (15-30 min, non-blocking)
3. [ ] Start AutoRefundEngine implementation

---

## **FUTURE PHASES (NOT NOW)**

- **Phase 3 (Weeks 5-6)**: Economic Layer (Credits system)
- **Phase 4 (Weeks 7-8)**: Channel Adapters + Build Tools

**Build tools can wait until Phase 4.**

---

## **SAFETY NET STATUS**

**Last Updated**: 2025-12-31

**Critical Tests Passing**: 7/7 ✅
- Minimal Safety: 2/2 ✅
- Event Sourcing Physics: 3/3 ✅
- Trust Math Physics: 2/2 ✅

**TimerService Tests**: 4/5 ✅
- Threading issues: ✅ FIXED
- SLA calculation: ⚠️ Logic bug (non-blocking)

**Safety Scripts**:
- `./scripts/validate.sh` - Pre-commit validation
- `./scripts/backup.sh` - Emergency backup

**Pre-Commit Hook**: ✅ Active (blocks unsafe commits)

**See**: `safety_checkpoints.md` for scenario tracking

