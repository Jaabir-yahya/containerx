# Scenario Goals: Mama Mboga Fresh Produce Stall

## Primary Objectives

### Core Validation
- **Invariant 3**: Inventory represents physical reality
- **Invariant 4**: Stock verified before commitment
- **Invariant 5**: Stock moves once, only on completion
- **Invariant 8**: Status reflects reality, not expectations

### Nairobi Reality Testing
- **Perishable Goods Management**: Critical stock verification for vegetables/fruits
- **Partial Payment Handling**: Common practice in Nairobi markets
- **Cash + M-Pesa Integration**: Mixed payment methods
- **Real-time Inventory Accuracy**: Essential for fresh produce business

## Secondary Objectives

### Business Process Validation
- **Order Fulfillment**: Complete customer journey from selection to payment
- **Stock Level Monitoring**: Prevent overselling perishable items
- **Payment Reconciliation**: Match payments to orders accurately
- **Daily Sales Tracking**: Revenue and inventory reconciliation

### Edge Case Exploration
- **Insufficient Stock**: Customer wants more than available
- **Payment Failures**: M-Pesa network issues during peak hours
- **Partial Payments**: Customer pays what they can, completes later
- **Stock Changes**: Inventory updates between order and payment

## Success Criteria

### Technical Validation
- [ ] All orders maintain audit trail integrity
- [ ] Stock levels never go negative
- [ ] Failed orders preserved forever
- [ ] Payment reconciliation possible

### Business Reality
- [ ] Perishable stock handling matches Nairobi market practices
- [ ] Payment flows reflect actual customer behavior
- [ ] Inventory alerts prevent stockouts of popular items
- [ ] Manual reconciliation workflows supported

## Expected Core Pressure Points

### Current Validation
- **Stock Verification**: Critical for perishable goods (vegetables spoil quickly)
- **Partial Payments**: Nairobi customers often pay in installments
- **Real-time Updates**: Fresh produce requires immediate stock accuracy
- **Failure Preservation**: Disputes require complete transaction history

### Potential Future Patterns
- **Expiry Management**: Vegetables have short shelf life (1-3 days)
- **Quality Tracking**: Visual inspection required before sale
- **Supplier Integration**: Daily restocking from wholesale markets
- **Customer Loyalty**: Repeat customers with preferred payment methods

## Scenario Evolution
This scenario represents the most common Nairobi retail business type. Patterns validated here may become universal requirements for retail SaaS solutions targeting Kenyan markets.
