# Scenario Goals: Koinange Street Food Court

## Primary Objectives

### Core Validation
- **Invariant 3:** Inventory reality with fresh ingredients
- **Invariant 4:** Stock verification before commitment (ingredients)
- **Invariant 5:** Single stock movement on completion
- **Invariant 8:** Status reflects reality (reservations, service flow)

### Nairobi Reality Testing
- **Reservation Management:** Advance bookings with deposits
- **Peak Hour Chaos:** Rapid order processing during lunch rush
- **Ingredient Stock:** Fresh food inventory with short shelf life
- **Mixed Service Models:** Walk-ins + reservations + deliveries

## Secondary Objectives

### Business Process Validation
- **Multi-Step Customer Journey:** Book → Arrive → Order → Pay
- **Advance Payment Handling:** Deposits for group reservations
- **Ingredient Tracking:** Recipe-based stock deduction
- **Service Completion:** Table turnover and payment reconciliation

### Edge Case Exploration
- **No-Show Handling:** Reserved tables not used
- **Overbooking Prevention:** Capacity management
- **Ingredient Shortages:** Menu availability changes
- **Payment Method Mix:** Cash + M-Pesa during service

## Success Criteria

### Technical Validation
- [ ] Reservation deposits handled correctly
- [ ] Ingredient stock reflects actual usage
- [ ] Peak hour order surges managed
- [ ] Payment reconciliation across methods

### Business Reality
- [ ] Walk-in vs reservation flows work
- [ ] Ingredient stock prevents menu gaps
- [ ] Table management supports turnover
- [ ] Payment delays don't block service

## Expected Core Pressure Points

### Current Validation
- **Advance Payments:** Deposits require PENDING status management
- **Service Completion:** Multi-step journeys need clear status tracking
- **Capacity Management:** Table availability affects reservations
- **Ingredient Precision:** Recipe-based stock deduction required

### Potential Future Patterns
- **Reservation Systems:** Time-based order management
- **Capacity Tracking:** Resource availability management
- **Advance Payments:** Deposit handling for services
- **Multi-Step Fulfillment:** Complex order state management

## Scenario Evolution
This scenario validates hospitality service models. Patterns here may extend to hotels, event spaces, and other reservation-based businesses.
