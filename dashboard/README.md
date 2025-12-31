# ContainerX Core + Scenario Lab Dashboard

A comprehensive web-based dashboard for monitoring, testing, and interacting with ContainerX ERP scenarios.

## Features

### 📊 Dashboard Overview
- **Scenario List Sidebar**: Browse all loaded scenarios with health status indicators
- **Search & Filter**: Find scenarios by name, industry, or health status
- **Health Metrics**: Real-time core invariant validation and system health
- **Alert System**: Color-coded notifications for violations and warnings

### 🔍 Scenario Detail Explorer
- **Interactive Tables**: Orders, payments, inventory with sorting and filtering
- **Event Timeline**: Complete audit trail with visual timeline
- **Health Validation**: Real-time invariant checking and violation reporting
- **Export Functionality**: Download scenario data as JSON

### 🎮 Interactive Sandbox
- **Order Creation**: Test new order processing with custom parameters
- **Payment Application**: Apply payments to existing orders
- **Stock Verification**: Check inventory availability
- **Inventory Adjustment**: Modify stock levels with audit logging
- **Real-time Results**: Immediate feedback on all actions

### 📈 Analytics & Reporting
- **Cross-Scenario Metrics**: Compare health across all scenarios
- **Performance Tracking**: Response times and operation success rates
- **Export Capabilities**: Generate reports and data exports
- **Audit Compliance**: Complete operation logging

## Quick Start

### 1. Install Dependencies
```bash
pip install flask
```

### 2. Start Dashboard
```bash
cd dashboard
python app.py
```

### 3. Access Dashboard
Open http://localhost:5000 in your browser

### 4. Load Scenarios
The dashboard automatically loads all `scenario_*.json` files from the project root.

## API Endpoints

### Core Endpoints
- `GET /` - Main dashboard
- `GET /scenario/<id>` - Scenario detail view

### API Endpoints
- `GET /api/scenarios` - List all scenarios with metrics
- `GET /api/scenario/<id>/export` - Export scenario as JSON
- `POST /api/scenario/<id>/simulate` - Run interactive actions

## Scenario Management

### Loading Scenarios
Scenarios are automatically loaded from JSON files in the project root:
```
scenario_retail_*.json
scenario_hospitality_*.json
scenario_marketplace_*.json
scenario_logistics_*.json
scenario_construction_*.json
scenario_healthcare_*.json
```

### Health Status Indicators
- 🟢 **Healthy**: No violations, all invariants maintained
- 🟡 **Warning**: Minor issues (low stock, partial payments)
- 🔴 **Critical**: Core invariant violations detected

## Interactive Testing

### Order Creation
```javascript
// Simulate creating a new order
{
  "action": "create_order",
  "params": {
    "customer_id": "CUST_001",
    "items": [{"sku": "TOMATOES", "qty": 2, "price": 120}],
    "payment_amount": 240,
    "payment_method": "cash"
  }
}
```

### Payment Application
```javascript
// Apply payment to existing order
{
  "action": "apply_payment",
  "params": {
    "order_id": "ORDER_123",
    "amount": 100,
    "method": "mpesa",
    "reference": "MPESA_TXN_123"
  }
}
```

### Stock Operations
```javascript
// Verify stock availability
{
  "action": "verify_stock",
  "params": {
    "sku": "TOMATOES",
    "quantity": 5
  }
}

// Adjust inventory
{
  "action": "adjust_inventory",
  "params": {
    "sku": "TOMATOES",
    "quantity_change": -2,
    "reason": "sale"
  }
}
```

## Core Invariant Validation

The dashboard automatically validates these ERP invariants:

1. **Orders represent human intent** - All orders have event log entries
2. **Payments represent cash reality** - All payments are logged
3. **Inventory represents physical reality** - All stock changes audited
4. **Stock verified before commitment** - No overselling
5. **Stock moves only once, only on completion** - Single stock deductions
6. **Failed orders/payments preserved** - No data loss
7. **No deletes for financial records** - Immutable audit trail
8. **Status reflects reality** - Accurate order/payment states
9. **All actions auditable** - Complete event logging
10. **Correctness > convenience** - Safety over ease
11. **Ambiguity logged** - No silent failures

## Nairobi Business Scenarios

### Supported Industries
- **Retail**: Vegetable stalls, general stores (perishable goods focus)
- **Hospitality**: Restaurants, cafes (bookings, ingredients)
- **Marketplace**: Multi-vendor platforms (coordination, payments)
- **Logistics**: Delivery services (tracking, packages)
- **Construction**: Building supplies (bulk orders, heavy materials)
- **Healthcare**: Pharmacies, clinics (prescriptions, expiry management)

### Scenario Realism
- **M-Pesa Integration**: Async callbacks, reference tracking, delays
- **Cash + Digital Mix**: Multiple payment methods per transaction
- **Stock Challenges**: Perishables, bulk items, low stock alerts
- **Human Factors**: Partial payments, manual reconciliation, errors
- **Nairobi Scale**: Realistic customer counts, transaction volumes

## Architecture

### Tech Stack
- **Backend**: Flask (Python web framework)
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Data**: JSON scenario files, SQLite core database
- **Real-time**: AJAX for interactive operations

### Directory Structure
```
dashboard/
├── app.py                 # Flask application
├── templates/
│   ├── dashboard.html     # Main dashboard
│   └── scenario_detail.html # Scenario detail view
└── static/
    ├── css/
    │   └── dashboard.css  # Custom styles
    └── js/
        └── dashboard.js   # Frontend interactions
```

## Development

### Adding New Features
1. **Backend**: Add routes to `app.py`
2. **Frontend**: Update templates in `templates/`
3. **Styling**: Modify `static/css/dashboard.css`
4. **Interactivity**: Enhance `static/js/dashboard.js`

### Testing
```bash
# Start dashboard
python dashboard/app.py

# Test API endpoints
curl http://localhost:5000/api/scenarios

# Test scenario simulation
curl -X POST http://localhost:5000/api/scenario/<id>/simulate \
  -H "Content-Type: application/json" \
  -d '{"action": "create_order", "params": {...}}'
```

## Troubleshooting

### Common Issues
- **Scenarios not loading**: Check JSON file format and naming
- **API errors**: Verify core functions are imported correctly
- **Display issues**: Check browser console for JavaScript errors

### Debug Mode
```python
# Run with debug logging
FLASK_ENV=development python dashboard/app.py
```

## Contributing

### Code Standards
- **Python**: Type hints, docstrings, PEP 8
- **JavaScript**: ES6+, async/await patterns
- **HTML/CSS**: Semantic markup, responsive design

### Testing
- **Unit Tests**: Core function validation
- **Integration Tests**: API endpoint testing
- **Scenario Tests**: Business logic validation

## License

ContainerX Core + Scenario Lab Dashboard - Internal development tool for ERP validation and testing.

---

**Ready to explore your ContainerX scenarios? Start the dashboard and dive in!** 🚀
