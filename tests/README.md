# ERP Core Testing System

This directory contains a comprehensive testing system for the ContainerX ERP core. The tests are designed to prove correctness, safety under retries, resilience to partial failures, and maintainability.

## Test Philosophy

The ERP core follows strict invariants that must never be violated:

1. **Orders ≠ Payments ≠ Inventory**: These are separate concerns
2. **StockMovement is append-only and mandatory**: Every inventory change creates a movement
3. **EventLog records every critical action**: Full audit trail
4. **Partial payments supported with idempotency**: Safe retries
5. **Stock deducts only once, only on full payment**: No premature deductions
6. **Failures are first-class records**: Failed operations are stored, not just exceptions

Our tests prove these invariants hold under all conditions.

## Test Structure

```
tests/
├── conftest.py              # Shared pytest fixtures (db, services)
├── helpers.py               # Helper functions for debugging and assertions
├── factories/               # Test data factories
│   ├── order_factory.py
│   ├── payment_factory.py
│   └── inventory_factory.py
├── unit/                    # Unit tests (services in isolation)
│   ├── test_inventory_service.py
│   ├── test_payment_service.py
│   └── test_sales_service.py
├── integration/            # Integration tests (full DB, real services)
│   ├── test_retail_flow.py
│   ├── test_partial_payments.py
│   └── test_failure_states.py
├── scenarios/              # Scenario tests (idempotency, replay safety)
│   ├── test_idempotency.py
│   ├── test_replay_safety.py
│   └── test_double_execution.py
├── properties/             # Property/invariant tests (randomized sequences)
│   └── test_erp_invariants.py
└── test_invariants.py      # Original invariant tests (kept for compatibility)
```

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run by Category
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Scenario tests only
pytest tests/scenarios/

# Property tests only
pytest tests/properties/
```

### Run Specific Test File
```bash
pytest tests/unit/test_inventory_service.py
```

### Run with Verbose Output
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=core --cov-report=html
```

## Test Layers

### Unit Tests (`tests/unit/`)

Test individual services in isolation with real database but minimal dependencies.

**What they test:**
- Service methods work correctly
- Error handling
- Edge cases
- Service-level invariants

**Example:**
```python
def test_adjust_inventory_prevents_negative(clean_db, seeded_inventory):
    """Test that inventory adjustment prevents negative stock."""
    with pytest.raises(ValueError, match="negative"):
        adjust_inventory("MILK001", -150, "test", None)
```

### Integration Tests (`tests/integration/`)

Test complete flows with real database and all services working together.

**What they test:**
- End-to-end business flows
- Service orchestration
- Real-world scenarios
- Full system invariants

**Example:**
```python
def test_complete_retail_sale_flow(clean_db, seeded_inventory):
    """Test complete retail sale from start to finish."""
    order_id = process_retail_sale(...)
    assert get_order_status(order_id) == "COMPLETED"
    assert stock_was_deducted()
```

### Scenario Tests (`tests/scenarios/`)

Test specific scenarios like idempotency, replay safety, and double execution.

**What they test:**
- Payment replay with same reference
- System state after simulated crashes
- Concurrent operations
- Out-of-order payments

**Example:**
```python
def test_payment_replay_same_reference(clean_db, seeded_inventory):
    """Test replaying payment with same reference is idempotent."""
    apply_payment_to_order(order_id, 500.0, "mpesa", "REF123")
    apply_payment_to_order(order_id, 500.0, "mpesa", "REF123")  # Replay
    assert stock_not_double_deducted()
```

### Property Tests (`tests/properties/`)

Test invariants hold under randomized sequences of operations.

**What they test:**
- Invariants hold under random operations
- Stock never goes negative
- Movements match inventory changes
- Events exist for all operations

**Example:**
```python
@pytest.mark.parametrize("seed", [42, 123, 456])
def test_stock_never_negative_random_operations(clean_db, seeded_inventory, seed):
    """Test that stock never goes negative under random operations."""
    # Perform random operations
    # Verify stock never negative
```

## Test Coverage

### Required Coverage Areas

All tests must cover:

- ✅ Stock never goes negative (even under retries)
- ✅ StockMovement count matches inventory changes
- ✅ EventLog exists for every mutation
- ✅ Payment replay does not double deduct stock
- ✅ Order completion happens exactly once
- ✅ Failed orders remain queryable
- ✅ Partial payment does not affect stock
- ✅ Out-of-order payments still resolve correctly
- ✅ Concurrent orders for same SKU respect stock

## Helper Functions

The `tests/helpers.py` module provides utility functions:

### Debugging Helpers
```python
print_event_log(entity_type="order", entity_id=order_id)
print_stock_movements(sku="MILK001", order_id=order_id)
```

### Assertion Helpers
```python
assert_stock_movement_count(sku, expected_count)
assert_event_exists(entity_type, entity_id, action)
assert_no_negative_stock()
```

### Query Helpers
```python
get_inventory_quantity(sku)
get_order_status(order_id)
get_total_paid(order_id)
get_stock_movements(sku=sku, order_id=order_id)
get_event_log(entity_type="order", entity_id=order_id)
```

## Adding New Tests

### 1. Choose the Right Layer

- **Unit test**: Testing a single service method
- **Integration test**: Testing a complete flow
- **Scenario test**: Testing a specific business scenario
- **Property test**: Testing invariants under random conditions

### 2. Use Fixtures

Always use the `clean_db` fixture for database setup:

```python
def test_my_feature(clean_db, seeded_inventory):
    # Test code here
```

### 3. Use Factories

Create test data using factories:

```python
from tests.factories.order_factory import create_order_items_data

items = create_order_items_data([("MILK001", 10), ("BREAD001", 5)])
```

### 4. Use Helpers

Use helper functions for assertions and queries:

```python
from tests.helpers import assert_no_negative_stock, get_inventory_quantity

assert_no_negative_stock()
qty = get_inventory_quantity("MILK001")
```

### 5. Follow Naming Conventions

- Test functions: `test_<what_is_tested>`
- Test classes: `Test<FeatureName>`
- Use descriptive docstrings

## Debugging Test Failures

### 1. Check Event Log

```python
from tests.helpers import print_event_log

print_event_log(entity_type="order", entity_id=order_id)
```

### 2. Check Stock Movements

```python
from tests.helpers import print_stock_movements

print_stock_movements(sku="MILK001", order_id=order_id)
```

### 3. Check Database State

```python
from core.storage.db import get_db

conn = get_db()
cur = conn.cursor()
cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
print(cur.fetchone())
conn.close()
```

### 4. Run with Verbose Output

```bash
pytest tests/path/to/test.py -v -s
```

The `-s` flag shows print statements.

## Invariants That Must Never Be Broken

When writing or modifying tests, ensure these invariants are never violated:

1. **Stock Never Negative**: `assert_no_negative_stock()` should always pass
2. **StockMovement Mandatory**: Every inventory change must create a movement
3. **EventLog Complete**: Every critical action must be logged
4. **Idempotency**: Replaying operations with same reference is safe
5. **Stock Deduction Once**: Stock is deducted exactly once per completed order
6. **Partial Payments Safe**: Partial payments never move stock
7. **Failures Recorded**: Failed operations create records, not just exceptions

## Test Data

### Seeded Inventory

The `seeded_inventory` fixture provides standard test inventory:

- `MILK001`: 100 units
- `BREAD001`: 50 units
- `EGGS001`: 200 units
- `TEST001`: 100 units
- `TEST002`: 50 units

### Test Database

Each test gets an isolated database via the `clean_db` fixture. The database is:
- Created fresh for each test
- Initialized with schema
- Seeded with inventory (if using `seeded_inventory`)
- Cleaned up after test

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    pytest tests/ -v --cov=core --cov-report=xml
```

## Future Extensibility

The test system is designed to be extended:

1. **New Services**: Add unit tests in `tests/unit/`
2. **New Flows**: Add integration tests in `tests/integration/`
3. **New Scenarios**: Add scenario tests in `tests/scenarios/`
4. **New Invariants**: Add property tests in `tests/properties/`

All tests use the same fixtures and helpers, making them easy to maintain and extend.

## Questions?

If you have questions about:
- **Test structure**: Check this README
- **How to test something**: Look at similar tests in the same layer
- **Why a test fails**: Use debugging helpers
- **Adding new tests**: Follow the "Adding New Tests" section above

## Test Execution Time

- **Unit tests**: ~1-2 seconds
- **Integration tests**: ~2-5 seconds
- **Scenario tests**: ~3-8 seconds
- **Property tests**: ~10-30 seconds (due to randomization)

Total test suite: ~30-60 seconds

