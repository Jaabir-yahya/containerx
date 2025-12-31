# UCOS Safety Checkpoints

## What Scenarios MUST Pass

This document tracks which Nairobi business scenarios must pass before any commit.

### **Critical Scenarios (MUST PASS)**

1. **Minimal Safety** (`tests/scenarios/minimal_safety.py`)
   - Can create and derive commitments
   - Event sourcing integrity
   - **Status**: ✅ Baseline established

2. **Event Sourcing Physics** (`tests/ucos_physics/test_event_sourcing.py`)
   - All state from events
   - Event immutability
   - State replay consistency
   - **Status**: ✅ Validated

3. **Trust Math Physics** (`tests/ucos_physics/test_trust_math.py`)
   - Trust bounds (0.05 - 0.95)
   - Delta bounds (-0.3 to +0.3)
   - **Status**: ✅ Validated

### **Phase 2 Scenarios (COMPLETE)**

4. **Timer Service** (`tests/test_timer_service.py`)
   - Timer scheduling on commitment creation
   - Timer firing and event emission
   - **Status**: ✅ Implemented, ✅ Threading fixed, 4/5 tests passing

5. **Pizza Delivery with SLA Breach** (`tests/scenarios/pizza_delivery_auto_refund.py`)
   - Real Nairobi pizza shop scenario
   - Customer orders, seller misses SLA, auto-refund
   - **Status**: ✅ Complete, 2/2 tests passing

### **Phase 2.5: Horizontal Coverage (8 Nairobi Scenarios)**

6. **M-Pesa Retry & Reconciliation** (`tests/scenarios/mpesa_retry_network_outage.py`) ✅ COMPLETE (2025-01-01)
   - Idempotent payment recording (same reference = same payment)
   - Webhook reconciliation for delayed callbacks
   - Network outage queuing
   - **Status**: ✅ Complete, 4/4 tests passing

### **Future Scenarios (TO ADD)**

7. **Cash + M-Pesa Hybrid Payments** (TODO)
   - Mama Mboga scenario
   - Mixed payment methods in same transaction

8. **Partial Fulfillment** (TODO)
   - Proportional settlement (80% delivered = 80% payment)

9. **Network Outage Resilience** (TODO)
   - Offline transaction queuing and reconciliation

10. **Capacity-Based Queuing** (TODO)
    - Seller capacity limits and fair queuing

11. **Trust-Based SLA & Pricing** (TODO)
    - Dynamic pricing based on trust scores

12. **Dispute Escalation** (TODO)
    - Evidence attachment and resolution paths

13. **Repeat Customer Recognition** (TODO)
    - Loyalty tracking and preferential treatment

---

## How to Add New Scenarios

1. Create scenario test in `tests/scenarios/`
2. Make it represent a REAL Nairobi business case
3. Test end-to-end UCOS flow
4. Add to this checklist
5. Ensure it passes before committing

---

## Emergency Recovery

If scenarios fail:

1. **Check git log**: `git log --oneline | grep -i "scenario.*pass"`
2. **Revert to last good commit**: `git checkout <commit-hash>`
3. **Run scenarios**: `./scripts/validate.sh`
4. **Fix from known good state**

---

## Last Validated

- **Date**: 2025-01-01
- **Commit**: Scenario 1 (M-Pesa Retry & Reconciliation) complete
- **Scenarios Passing**: 
  - Minimal Safety: 2/2 ✅
  - Event Sourcing Physics: 3/3 ✅
  - Trust Math Physics: 2/2 ✅
  - Pizza Delivery: 2/2 ✅
  - TimerService: 5/5 ✅
  - M-Pesa Retry & Reconciliation: 4/4 ✅
- **Total Critical**: 7/7 ✅
- **Phase 2**: ✅ Complete
- **Phase 2.5**: 1/8 scenarios complete (M-Pesa Retry)

