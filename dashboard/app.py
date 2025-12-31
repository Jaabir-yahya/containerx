#!/usr/bin/env python3
"""
ContainerX Core + Scenario Lab Dashboard

Developer dashboard for monitoring scenario health, core functionality,
and interactive ERP operations testing.

Features:
- Scenario management and monitoring
- Core health metrics and invariant validation
- Interactive sandbox for order/payment simulation
- Real-time alerts and notifications
- Audit trail exploration
"""

import os
import json
import glob
from datetime import datetime
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import sys

# Add project root to path for core imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.sales_service import process_retail_sale, apply_payment_to_order
from core.services.inventory_service import verify_stock, adjust_inventory, get_inventory_quantity
from core.services.payment_service import record_payment, get_total_paid

app = Flask(__name__)
app.secret_key = 'containerx_dashboard_secret_key'

# Global scenario cache
SCENARIO_CACHE = {}

def load_scenarios():
    """Load all scenario files into cache."""
    global SCENARIO_CACHE
    scenario_files = glob.glob('scenarios/scenario_*.json')
    SCENARIO_CACHE = {}

    for file_path in scenario_files:
        try:
            with open(file_path, 'r') as f:
                scenario = json.load(f)
                scenario_id = scenario.get('id', file_path.split('/')[-1].replace('.json', ''))
                SCENARIO_CACHE[scenario_id] = scenario
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    return SCENARIO_CACHE

def get_scenario_metrics(scenario):
    """Calculate health metrics for a scenario."""
    orders = scenario.get('orders', [])
    payments = scenario.get('payments', [])
    inventory = scenario.get('inventory', {})

    # Order metrics
    order_status = {}
    for order in orders:
        status = order.get('status', 'UNKNOWN')
        order_status[status] = order_status.get(status, 0) + 1

    # Payment metrics
    payment_status = {}
    for payment in payments:
        status = payment.get('status', 'UNKNOWN')
        payment_status[status] = payment_status.get(status, 0) + 1

    # Inventory alerts
    low_stock_alerts = []
    for sku, data in inventory.items():
        quantity = data.get('quantity', 0)
        if quantity <= 5:  # Low stock threshold
            low_stock_alerts.append({
                'sku': sku,
                'quantity': quantity,
                'category': data.get('category', 'unknown')
            })

    # Invariant violations check
    violations = []

    # Check: Failed orders preserved
    failed_orders = [o for o in orders if o.get('status') == 'FAILED']
    if not failed_orders and any(o.get('status') in ['COMPLETED', 'PENDING'] for o in orders):
        violations.append("No failed orders found - may indicate over-optimistic testing")

    # Check: Stock levels realistic
    negative_stock = [sku for sku, data in inventory.items() if data.get('quantity', 0) < 0]
    if negative_stock:
        violations.append(f"Negative stock found: {negative_stock}")

    # Check: Payment amounts reasonable
    for payment in payments:
        amount = payment.get('amount', 0)
        if amount <= 0:
            violations.append(f"Invalid payment amount: {payment.get('id')}")

    return {
        'orders': order_status,
        'payments': payment_status,
        'inventory_alerts': low_stock_alerts,
        'violations': violations,
        'total_orders': len(orders),
        'total_payments': len(payments),
        'total_inventory_items': len(inventory)
    }

def validate_core_invariants(scenario):
    """Validate core ERP invariants for a scenario."""
    violations = []

    orders = scenario.get('orders', [])
    payments = scenario.get('payments', [])
    inventory = scenario.get('inventory', {})
    event_log = scenario.get('event_log', [])

    # Invariant 1: Orders represent human intent
    order_ids = {o['id'] for o in orders}
    event_order_ids = {e['entity_id'] for e in event_log if e['entity_type'] == 'order'}
    if not order_ids.issubset(event_order_ids):
        violations.append("Not all orders have corresponding events")

    # Invariant 2: Payments represent cash reality
    payment_ids = {p['id'] for p in payments}
    event_payment_ids = {e['entity_id'] for e in event_log if e['entity_type'] == 'payment'}
    if not payment_ids.issubset(event_payment_ids):
        violations.append("Not all payments have corresponding events")

    # Invariant 3: Inventory represents physical reality
    for sku in inventory.keys():
        inventory_events = [e for e in event_log if e['entity_type'] == 'inventory' and e['entity_id'] == sku]
        if not inventory_events:
            violations.append(f"No inventory events for {sku}")

    # Invariant 5: Stock moves only once, only on completion
    completed_orders = [o for o in orders if o.get('status') == 'COMPLETED']
    for order in completed_orders:
        order_events = [e for e in event_log if e['entity_type'] == 'order' and e['entity_id'] == order['id']]
        completed_events = [e for e in order_events if e['action'] == 'completed']
        if len(completed_events) > 1:
            violations.append(f"Order {order['id']} completed multiple times")

    # Invariant 6: Failed orders preserved
    failed_orders = [o for o in orders if o.get('status') == 'FAILED']
    if not failed_orders:
        violations.append("No failed orders found")

    return violations

@app.route('/')
def dashboard():
    """Main dashboard page."""
    load_scenarios()
    scenarios = []

    for scenario_id, scenario in SCENARIO_CACHE.items():
        metrics = get_scenario_metrics(scenario)
        violations = validate_core_invariants(scenario)

        scenarios.append({
            'id': scenario_id,
            'name': scenario.get('name', 'Unknown'),
            'industry': scenario.get('industry', 'unknown'),
            'modules': scenario.get('modules', []),
            'metrics': metrics,
            'violations': violations,
            'health_status': 'critical' if violations else ('warning' if metrics['inventory_alerts'] else 'healthy')
        })

    # Sort by health status (critical first)
    scenarios.sort(key=lambda x: {'critical': 0, 'warning': 1, 'healthy': 2}[x['health_status']])

    return render_template('dashboard.html', scenarios=scenarios)

@app.route('/scenario/<scenario_id>')
def scenario_detail(scenario_id):
    """Scenario detail page."""
    load_scenarios()

    if scenario_id not in SCENARIO_CACHE:
        flash('Scenario not found', 'error')
        return redirect(url_for('dashboard'))

    scenario = SCENARIO_CACHE[scenario_id]
    metrics = get_scenario_metrics(scenario)
    violations = validate_core_invariants(scenario)

    return render_template('scenario_detail.html',
                         scenario=scenario,
                         metrics=metrics,
                         violations=violations)

@app.route('/api/scenarios')
def api_scenarios():
    """API endpoint for scenario list."""
    load_scenarios()
    scenarios = []

    for scenario_id, scenario in SCENARIO_CACHE.items():
        metrics = get_scenario_metrics(scenario)
        scenarios.append({
            'id': scenario_id,
            'name': scenario.get('name'),
            'industry': scenario.get('industry'),
            'health_status': 'critical' if validate_core_invariants(scenario) else 'healthy',
            'metrics': metrics
        })

    return jsonify(scenarios)

@app.route('/api/scenario/<scenario_id>/simulate', methods=['POST'])
def simulate_action(scenario_id):
    """Simulate core actions on a scenario."""
    load_scenarios()

    if scenario_id not in SCENARIO_CACHE:
        return jsonify({'error': 'Scenario not found'}), 404

    data = request.get_json()
    action = data.get('action')
    params = data.get('params', {})

    try:
        result = {}

        if action == 'create_order':
            # Simulate order creation
            customer_id = params.get('customer_id')
            items = params.get('items', [])
            payment_amount = params.get('payment_amount', 0)
            payment_method = params.get('payment_method', 'cash')

            order_result = process_retail_sale(
                customer_id, items, payment_amount, payment_method
            )
            result = {'order_id': order_result, 'status': 'success'}

        elif action == 'apply_payment':
            # Simulate payment application
            order_id = params.get('order_id')
            amount = params.get('amount', 0)
            method = params.get('method', 'cash')
            reference = params.get('reference')

            payment_result = apply_payment_to_order(
                order_id, amount, method, reference
            )
            result = payment_result

        elif action == 'verify_stock':
            # Simulate stock verification
            sku = params.get('sku')
            quantity = params.get('quantity', 1)
            stock_available = verify_stock(sku, quantity)
            result = {'available': stock_available, 'sku': sku, 'requested': quantity}

        elif action == 'adjust_inventory':
            # Simulate inventory adjustment
            sku = params.get('sku')
            quantity_change = params.get('quantity_change', 0)
            reason = params.get('reason', 'adjustment')

            adjustment_result = adjust_inventory(sku, quantity_change, reason)
            result = {'movement_id': adjustment_result.id, 'sku': sku, 'change': quantity_change}

        # Log the simulation action
        simulation_event = {
            'id': f"sim_{datetime.now().isoformat()}",
            'entity_type': 'simulation',
            'entity_id': f"{action}_{datetime.now().timestamp()}",
            'action': action,
            'metadata': {'params': params, 'result': result},
            'created_at': datetime.now().isoformat()
        }

        return jsonify({
            'success': True,
            'action': action,
            'result': result,
            'simulation_event': simulation_event
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'action': action
        }), 400

@app.route('/api/scenario/<scenario_id>/export')
def export_scenario(scenario_id):
    """Export scenario as JSON."""
    load_scenarios()

    if scenario_id not in SCENARIO_CACHE:
        return jsonify({'error': 'Scenario not found'}), 404

    scenario = SCENARIO_CACHE[scenario_id]
    return jsonify(scenario)

if __name__ == '__main__':
    load_scenarios()
    print(f"Loaded {len(SCENARIO_CACHE)} scenarios")
    app.run(debug=True, host='0.0.0.0', port=5000)
