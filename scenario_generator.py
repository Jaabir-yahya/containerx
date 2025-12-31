#!/usr/bin/env python3
"""
🇰🇪 ContainerX Scenario Generator

Generates realistic Nairobi business scenarios for ERP core testing and SaaS planning.
Each scenario is a complete mini-business with history, inventory, orders, payments, and event logs.

Usage:
    python scenario_generator.py --industry retail --name "Mama's Shop"
    python scenario_generator.py --list-industries
    python scenario_generator.py --export-all
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse

class ScenarioGenerator:
    """Generates realistic Nairobi business scenarios for ERP testing."""

    def __init__(self):
        self.templates = self._load_templates()
        self.industries = {
            'retail': self._generate_retail_scenario,
            'hospitality': self._generate_hospitality_scenario,
            'marketplace': self._generate_marketplace_scenario,
            'logistics': self._generate_logistics_scenario
        }

    def _load_templates(self) -> Dict[str, Any]:
        """Load base scenario templates."""
        return {
            'retail': {
                'name': 'Retail Market Stall',
                'inventory_templates': [
                    {'category': 'vegetables', 'items': ['Tomatoes', 'Onions', 'Spinach', 'Cabbage', 'Carrots', 'Potatoes']},
                    {'category': 'fruits', 'items': ['Bananas', 'Oranges', 'Pineapples', 'Mangoes']},
                    {'category': 'essentials', 'items': ['Milk', 'Bread', 'Eggs', 'Sugar', 'Soap']}
                ],
                'payment_methods': ['cash', 'mpesa', 'mixed'],
                'challenges': ['perishable_stock', 'partial_payments', 'stockouts', 'network_delays']
            },
            'hospitality': {
                'name': 'Restaurant/Cafe',
                'inventory_templates': [
                    {'category': 'ingredients', 'items': ['Rice', 'Chicken', 'Beef', 'Vegetables', 'Oil', 'Spices']},
                    {'category': 'beverages', 'items': ['Tea', 'Coffee', 'Soda', 'Juice', 'Water']},
                    {'category': 'bakery', 'items': ['Bread', 'Cake', 'Cookies', 'Mandazi']}
                ],
                'payment_methods': ['cash', 'mpesa', 'card', 'deposit'],
                'challenges': ['booking_delays', 'ingredient_shortages', 'peak_hours', 'cancellations']
            },
            'marketplace': {
                'name': 'Multi-Vendor Marketplace',
                'inventory_templates': [
                    {'category': 'electronics', 'items': ['Phones', 'Laptops', 'Headphones', 'Chargers', 'Cables']},
                    {'category': 'fashion', 'items': ['Shirts', 'Shoes', 'Bags', 'Accessories']},
                    {'category': 'home', 'items': ['Utensils', 'Furniture', 'Decor', 'Appliances']}
                ],
                'payment_methods': ['mpesa', 'card', 'bank_transfer'],
                'challenges': ['vendor_coordination', 'payment_delays', 'returns', 'quality_control']
            },
            'logistics': {
                'name': 'Delivery/Logistics',
                'inventory_templates': [
                    {'category': 'packages', 'items': ['Small_Packages', 'Medium_Packages', 'Large_Packages']},
                    {'category': 'vehicles', 'items': ['Motorcycles', 'Cars', 'Trucks']},
                    {'category': 'supplies', 'items': ['Fuel', 'Packaging', 'Labels']}
                ],
                'payment_methods': ['mpesa', 'cash', 'invoice'],
                'challenges': ['delivery_delays', 'traffic', 'fuel_shortages', 'package_damage']
            }
        }

    def generate_scenario(self, industry: str, name: str = None, complexity: str = 'medium') -> Dict[str, Any]:
        """Generate a complete business scenario."""
        if industry not in self.industries:
            raise ValueError(f"Unknown industry: {industry}")

        template = self.templates[industry]
        scenario_name = name or f"{template['name']} - {random.choice(['Downtown', 'Westlands', 'CBD', 'Estate', 'Mall'])}"

        # Generate scenario based on industry
        scenario = self.industries[industry](scenario_name, template, complexity)

        # Add common elements
        scenario.update({
            'id': str(uuid.uuid4()),
            'industry': industry,
            'generated_at': datetime.now().isoformat(),
            'complexity': complexity,
            'version': '1.0',
            'future_hooks': self._generate_future_hooks(industry)
        })

        return scenario

    def _generate_retail_scenario(self, name: str, template: Dict, complexity: str) -> Dict[str, Any]:
        """Generate a retail scenario (Mama Mboga style)."""
        inventory = self._generate_inventory(template['inventory_templates'], complexity)
        customers = self._generate_customers(5, 'retail')
        orders = self._generate_retail_orders(customers, inventory, complexity)
        payments = self._generate_payments(orders)
        event_log = self._generate_event_log(orders, payments, inventory)

        return {
            'name': name,
            'description': f"A typical Nairobi retail stall selling fresh produce and essentials in {name.split('-')[1].strip() if '-' in name else 'the market'}.",
            'modules': ['sales', 'inventory', 'payments', 'basic_analytics'],
            'inventory': inventory,
            'customers': customers,
            'orders': orders,
            'payments': payments,
            'event_log': event_log,
            'goals': [
                'Test perishable stock management',
                'Validate partial payment handling',
                'Simulate Nairobi market chaos (stockouts, payment delays)',
                'Test manual reconciliation workflows'
            ],
            'challenges': [
                'Fresh produce spoils quickly - stock verification critical',
                'Customers often pay partially then complete later via M-Pesa',
                'Network issues cause M-Pesa delays',
                'Manual cash counting and reconciliation required'
            ],
            'notes': [
                'Represents 80% of Nairobi small businesses',
                'Cash + M-Pesa mixed payments very common',
                'Stock levels fluctuate with market supply',
                'Human error in cash handling and stock counting'
            ]
        }

    def _generate_hospitality_scenario(self, name: str, template: Dict, complexity: str) -> Dict[str, Any]:
        """Generate a hospitality scenario (restaurant/cafe)."""
        inventory = self._generate_inventory(template['inventory_templates'], complexity)
        customers = self._generate_customers(8, 'hospitality')
        orders = self._generate_hospitality_orders(customers, inventory, complexity)
        payments = self._generate_payments(orders)
        event_log = self._generate_event_log(orders, payments, inventory)

        return {
            'name': name,
            'description': f"A busy Nairobi restaurant/cafe serving local and continental dishes in {name.split('-')[1].strip() if '-' in name else 'a popular spot'}.",
            'modules': ['bookings', 'sales', 'inventory', 'payments', 'reservations', 'basic_loyalty'],
            'inventory': inventory,
            'customers': customers,
            'orders': orders,
            'payments': payments,
            'event_log': event_log,
            'goals': [
                'Test booking and reservation workflows',
                'Validate ingredient stock management',
                'Simulate peak hour chaos and delays',
                'Test deposit and advance payment handling'
            ],
            'challenges': [
                'Peak hours cause booking conflicts',
                'Ingredients spoil or run out unexpectedly',
                'Customers cancel or no-show after deposits',
                'M-Pesa payments delay during busy periods'
            ],
            'notes': [
                'Multi-step customer journey (book → arrive → order → pay)',
                'Advance deposits common for groups',
                'Ingredient stock affects menu availability',
                'Table/reservation management critical'
            ]
        }

    def _generate_marketplace_scenario(self, name: str, template: Dict, complexity: str) -> Dict[str, Any]:
        """Generate a marketplace scenario."""
        inventory = self._generate_inventory(template['inventory_templates'], complexity)
        customers = self._generate_customers(12, 'marketplace')
        orders = self._generate_marketplace_orders(customers, inventory, complexity)
        payments = self._generate_payments(orders)
        event_log = self._generate_event_log(orders, payments, inventory)

        return {
            'name': name,
            'description': f"A Nairobi online marketplace connecting vendors with customers across {name.split('-')[1].strip() if '-' in name else 'the city'}.",
            'modules': ['sales', 'inventory', 'payments', 'multi_vendor', 'reviews', 'analytics'],
            'inventory': inventory,
            'customers': customers,
            'orders': orders,
            'payments': payments,
            'event_log': event_log,
            'goals': [
                'Test multi-vendor inventory coordination',
                'Validate complex order routing',
                'Simulate marketplace payment delays',
                'Test vendor-customer communication flows'
            ],
            'challenges': [
                'Multiple vendors, single inventory view needed',
                'Payment delays affect vendor trust',
                'Returns and refunds complex across vendors',
                'Quality control and dispute resolution'
            ],
            'notes': [
                'Represents future of Nairobi e-commerce',
                'Vendor coordination is key challenge',
                'Payment reconciliation across multiple parties',
                'Review and rating systems important'
            ]
        }

    def _generate_logistics_scenario(self, name: str, template: Dict, complexity: str) -> Dict[str, Any]:
        """Generate a logistics scenario."""
        inventory = self._generate_inventory(template['inventory_templates'], complexity)
        customers = self._generate_customers(6, 'logistics')
        orders = self._generate_logistics_orders(customers, inventory, complexity)
        payments = self._generate_payments(orders)
        event_log = self._generate_event_log(orders, payments, inventory)

        return {
            'name': name,
            'description': f"A Nairobi logistics company providing delivery services across {name.split('-')[1].strip() if '-' in name else 'the city'}.",
            'modules': ['tracking', 'sales', 'inventory', 'payments', 'routing', 'fleet_management'],
            'inventory': inventory,
            'customers': customers,
            'orders': orders,
            'payments': payments,
            'event_log': event_log,
            'goals': [
                'Test delivery tracking and routing',
                'Validate fleet and fuel management',
                'Simulate traffic and delay scenarios',
                'Test package status communication'
            ],
            'challenges': [
                'Nairobi traffic causes massive delays',
                'Fuel shortages affect operations',
                'Package tracking critical for customer trust',
                'Weather and road conditions unpredictable'
            ],
            'notes': [
                'Delivery is core Nairobi business need',
                'Traffic and logistics are major pain points',
                'Real-time tracking builds customer confidence',
                'Fuel and maintenance costs significant'
            ]
        }

    def _generate_inventory(self, templates: List[Dict], complexity: str) -> Dict[str, Any]:
        """Generate realistic inventory for the scenario."""
        inventory = {}
        item_count = {'low': 8, 'medium': 15, 'high': 25}[complexity]

        for template in templates:
            category_items = template['items'][:item_count // len(templates)]
            for item in category_items:
                sku = item.upper().replace(' ', '_')
                base_qty = random.randint(5, 50)
                # Add some Nairobi realism - some items low stock
                if random.random() < 0.2:  # 20% chance of low stock
                    base_qty = random.randint(1, 5)
                inventory[sku] = {
                    'quantity': base_qty,
                    'unit': 'kg' if template['category'] in ['vegetables', 'fruits', 'ingredients'] else 'units',
                    'category': template['category'],
                    'last_updated': (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
                }

        return inventory

    def _generate_customers(self, count: int, industry: str) -> List[Dict[str, Any]]:
        """Generate realistic customer data."""
        customers = []
        names = [
            'John Maina', 'Mary Wanjiku', 'Peter Kiprop', 'Grace Achieng', 'David Oduya',
            'Sarah Nyambura', 'James Kiprotich', 'Ann Wairimu', 'Michael Otieno', 'Lucy Adhiambo',
            'Samuel Kipkorir', 'Rose Chebet', 'Daniel Kiprop', 'Faith Wanjira', 'Paul Kipkoech'
        ]

        for i in range(count):
            customer = {
                'id': f'CUST_{str(uuid.uuid4())[:8]}',
                'name': random.choice(names),
                'phone': f'07{random.randint(10000000, 99999999)}',
                'email': None,  # Nairobi reality - most don't have emails
                'payment_preference': random.choice(['cash', 'mpesa', 'mixed']),
                'total_orders': random.randint(1, 15),
                'total_spent': random.randint(500, 15000),
                'last_order': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
            }

            # Add industry-specific data
            if industry == 'hospitality':
                customer['preferred_table'] = random.choice(['window', 'corner', 'outdoor', None])
                customer['dietary_restrictions'] = random.choice([None, 'vegetarian', 'halal'])
            elif industry == 'marketplace':
                customer['preferred_payment'] = random.choice(['mpesa', 'card', 'bank'])
                customer['return_rate'] = random.randint(0, 3)

            customers.append(customer)

        return customers

    def _generate_retail_orders(self, customers: List[Dict], inventory: Dict, complexity: str) -> List[Dict[str, Any]]:
        """Generate retail orders with Nairobi characteristics."""
        orders = []
        skus = list(inventory.keys())
        order_count = {'low': 5, 'medium': 10, 'high': 20}[complexity]

        for i in range(order_count):
            customer = random.choice(customers)
            order_items = []
            total_amount = 0

            # 1-4 items per order
            item_count = random.randint(1, 4)
            for _ in range(item_count):
                sku = random.choice(skus)
                item_info = inventory[sku]
                max_qty = min(10, item_info['quantity'])  # Don't exceed stock
                qty = random.randint(1, max_qty) if max_qty > 0 else 1

                price_per_unit = random.randint(50, 500)  # Nairobi price range
                item_total = qty * price_per_unit
                total_amount += item_total

                order_items.append({
                    'sku': sku,
                    'quantity': qty,
                    'price_per_unit': price_per_unit,
                    'total': item_total
                })

            # Determine order status with Nairobi realism
            status_roll = random.random()
            if status_roll < 0.6:  # 60% completed
                status = 'COMPLETED'
            elif status_roll < 0.8:  # 20% pending
                status = 'PENDING'
            else:  # 20% failed
                status = 'FAILED'

            order = {
                'id': f'ORDER_{str(uuid.uuid4())[:8]}',
                'customer_id': customer['id'],
                'items': order_items,
                'total_amount': total_amount,
                'status': status,
                'created_at': (datetime.now() - timedelta(hours=random.randint(1, 168))).isoformat(),
                'notes': self._generate_order_notes(status, 'retail')
            }

            orders.append(order)

        return orders

    def _generate_hospitality_orders(self, customers: List[Dict], inventory: Dict, complexity: str) -> List[Dict[str, Any]]:
        """Generate hospitality orders (includes bookings)."""
        orders = []
        skus = list(inventory.keys())
        order_count = {'low': 8, 'medium': 15, 'high': 25}[complexity]

        for i in range(order_count):
            customer = random.choice(customers)
            order_type = random.choice(['dine_in', 'takeaway', 'booking'])

            if order_type == 'booking':
                # Generate booking/reservation
                party_size = random.randint(2, 12)
                deposit_amount = party_size * random.randint(100, 300)
                total_amount = party_size * random.randint(500, 1500)

                order = {
                    'id': f'BOOKING_{str(uuid.uuid4())[:8]}',
                    'customer_id': customer['id'],
                    'type': 'booking',
                    'party_size': party_size,
                    'total_amount': total_amount,
                    'deposit_amount': deposit_amount,
                    'status': random.choice(['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED']),
                    'booking_time': (datetime.now() + timedelta(hours=random.randint(1, 72))).isoformat(),
                    'created_at': (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
                    'notes': f"Table booking for {party_size} people"
                }
            else:
                # Generate food order
                order_items = []
                total_amount = 0

                item_count = random.randint(2, 6)
                for _ in range(item_count):
                    sku = random.choice(skus)
                    qty = random.randint(1, 3)
                    price_per_unit = random.randint(100, 800)
                    item_total = qty * price_per_unit
                    total_amount += item_total

                    order_items.append({
                        'sku': sku,
                        'quantity': qty,
                        'price_per_unit': price_per_unit,
                        'total': item_total
                    })

                order = {
                    'id': f'ORDER_{str(uuid.uuid4())[:8]}',
                    'customer_id': customer['id'],
                    'type': order_type,
                    'items': order_items,
                    'total_amount': total_amount,
                    'status': random.choice(['CREATED', 'PENDING', 'COMPLETED']),
                    'created_at': (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                    'notes': f"{order_type.title()} order for {customer['name']}"
                }

            orders.append(order)

        return orders

    def _generate_marketplace_orders(self, customers: List[Dict], inventory: Dict, complexity: str) -> List[Dict[str, Any]]:
        """Generate marketplace orders with vendor complexity."""
        orders = []
        skus = list(inventory.keys())
        order_count = {'low': 12, 'medium': 25, 'high': 40}[complexity]

        vendors = ['TechHub', 'FashionPlus', 'HomeStore', 'GadgetWorld']

        for i in range(order_count):
            customer = random.choice(customers)
            vendor = random.choice(vendors)

            # Marketplace orders often have multiple items from different categories
            order_items = []
            total_amount = 0

            item_count = random.randint(1, 5)
            for _ in range(item_count):
                sku = random.choice(skus)
                qty = 1  # Usually single items in marketplace
                price_per_unit = random.randint(500, 50000)  # Nairobi marketplace prices
                item_total = qty * price_per_unit
                total_amount += item_total

                order_items.append({
                    'sku': sku,
                    'quantity': qty,
                    'price_per_unit': price_per_unit,
                    'total': item_total,
                    'vendor': vendor
                })

            order = {
                'id': f'MP_ORDER_{str(uuid.uuid4())[:8]}',
                'customer_id': customer['id'],
                'vendor': vendor,
                'items': order_items,
                'total_amount': total_amount,
                'status': random.choice(['PENDING', 'COMPLETED', 'SHIPPED', 'DELIVERED']),
                'created_at': (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                'shipping_address': f"Nairobi, {random.choice(['Westlands', 'CBD', 'Karen', 'Kilimani'])}",
                'notes': f"Marketplace order from {vendor}"
            }

            orders.append(order)

        return orders

    def _generate_logistics_orders(self, customers: List[Dict], inventory: Dict, complexity: str) -> List[Dict[str, Any]]:
        """Generate logistics/delivery orders."""
        orders = []
        order_count = {'low': 6, 'medium': 12, 'high': 20}[complexity]

        package_types = ['Small_Packages', 'Medium_Packages', 'Large_Packages']
        delivery_zones = ['CBD', 'Westlands', 'Karen', 'Kilimani', 'Eastlands']

        for i in range(order_count):
            customer = random.choice(customers)
            package_type = random.choice(package_types)

            # Calculate delivery fee based on distance and package size
            base_fee = {'Small_Packages': 200, 'Medium_Packages': 350, 'Large_Packages': 500}[package_type]
            distance_multiplier = random.uniform(1.0, 2.5)
            delivery_fee = int(base_fee * distance_multiplier)

            order = {
                'id': f'DELIVERY_{str(uuid.uuid4())[:8]}',
                'customer_id': customer['id'],
                'package_type': package_type,
                'pickup_location': f"Nairobi CBD, Building {random.randint(1, 50)}",
                'delivery_location': f"Nairobi {random.choice(delivery_zones)}, Street {random.randint(1, 100)}",
                'total_amount': delivery_fee,
                'delivery_fee': delivery_fee,
                'status': random.choice(['PENDING', 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED', 'FAILED']),
                'estimated_delivery': (datetime.now() + timedelta(hours=random.randint(1, 8))).isoformat(),
                'created_at': (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                'assigned_rider': f"Rider_{random.randint(1, 20)}",
                'notes': f"{package_type.replace('_', ' ')} delivery"
            }

            orders.append(order)

        return orders

    def _generate_payments(self, orders: List[Dict]) -> List[Dict[str, Any]]:
        """Generate payment records for orders."""
        payments = []

        for order in orders:
            if order['status'] in ['CREATED', 'PENDING']:
                # Generate partial or failed payments
                if random.random() < 0.7:  # 70% have some payment
                    payment_amount = random.randint(100, order['total_amount'])
                    payment_method = random.choice(['cash', 'mpesa', 'mixed'])
                    reference = f"REF_{str(uuid.uuid4())[:12]}" if payment_method == 'mpesa' else None

                    payment = {
                        'id': f'PAY_{str(uuid.uuid4())[:8]}',
                        'order_id': order['id'],
                        'amount': payment_amount,
                        'method': payment_method,
                        'reference': reference,
                        'status': 'RECEIVED' if payment_amount > 0 else 'FAILED',
                        'created_at': (datetime.now() - timedelta(hours=random.randint(1, 12))).isoformat()
                    }
                    payments.append(payment)

            elif order['status'] == 'COMPLETED':
                # Full payment for completed orders
                payment = {
                    'id': f'PAY_{str(uuid.uuid4())[:8]}',
                    'order_id': order['id'],
                    'amount': order['total_amount'],
                    'method': random.choice(['cash', 'mpesa', 'card']),
                    'reference': f"REF_{str(uuid.uuid4())[:12]}" if random.random() < 0.6 else None,
                    'status': 'RECEIVED',
                    'created_at': order.get('created_at', datetime.now().isoformat())
                }
                payments.append(payment)

        return payments

    def _generate_event_log(self, orders: List[Dict], payments: List[Dict], inventory: Dict) -> List[Dict[str, Any]]:
        """Generate realistic event log entries."""
        events = []

        # Order events
        for order in orders:
            events.append({
                'id': str(uuid.uuid4()),
                'entity_type': 'order',
                'entity_id': order['id'],
                'action': 'created',
                'metadata': {
                    'customer_id': order['customer_id'],
                    'total_amount': order['total_amount'],
                    'item_count': len(order.get('items', []))
                },
                'created_at': order['created_at']
            })

            if order['status'] == 'COMPLETED':
                events.append({
                    'id': str(uuid.uuid4()),
                    'entity_type': 'order',
                    'entity_id': order['id'],
                    'action': 'completed',
                    'metadata': {'reason': 'full_payment'},
                    'created_at': (datetime.fromisoformat(order['created_at']) + timedelta(minutes=30)).isoformat()
                })

        # Payment events
        for payment in payments:
            events.append({
                'id': str(uuid.uuid4()),
                'entity_type': 'payment',
                'entity_id': payment['id'],
                'action': 'recorded',
                'metadata': {
                    'order_id': payment['order_id'],
                    'amount': payment['amount'],
                    'method': payment['method']
                },
                'created_at': payment['created_at']
            })

        # Inventory events (simulate some stock movements)
        for sku in random.sample(list(inventory.keys()), min(5, len(inventory))):
            events.append({
                'id': str(uuid.uuid4()),
                'entity_type': 'inventory',
                'entity_id': sku,
                'action': 'adjusted',
                'metadata': {
                    'quantity_change': random.randint(-10, 5),
                    'reason': random.choice(['sale', 'restock', 'adjustment'])
                },
                'created_at': (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
            })

        # Sort by timestamp
        events.sort(key=lambda x: x['created_at'])

        return events

    def _generate_order_notes(self, status: str, industry: str) -> str:
        """Generate realistic order notes."""
        notes = {
            'COMPLETED': [
                'Smooth transaction',
                'Customer paid in full',
                'Regular customer',
                'Quick service'
            ],
            'PENDING': [
                'Partial payment received',
                'Awaiting balance payment',
                'Customer will pay later',
                'M-Pesa delay expected'
            ],
            'FAILED': [
                'Insufficient stock',
                'Payment failed',
                'Order cancelled by customer',
                'Network issues'
            ]
        }

        return random.choice(notes.get(status, ['Order processed']))

    def _generate_future_hooks(self, industry: str) -> Dict[str, Any]:
        """Generate hooks for future SaaS expansion."""
        base_hooks = {
            'multi_tenant': {
                'enabled': True,
                'isolation_level': 'database',
                'scaling_strategy': 'horizontal'
            },
            'saas_integrations': {
                'whatsapp_business': {'status': 'planned', 'priority': 'high'},
                'mpesa_deep_integration': {'status': 'planned', 'priority': 'high'},
                'email_sms_notifications': {'status': 'planned', 'priority': 'medium'}
            }
        }

        # Industry-specific hooks
        if industry == 'retail':
            base_hooks.update({
                'modules': {
                    'loyalty_program': {'status': 'planned', 'complexity': 'medium'},
                    'inventory_alerts': {'status': 'ready', 'complexity': 'low'},
                    'customer_history': {'status': 'planned', 'complexity': 'medium'}
                }
            })
        elif industry == 'hospitality':
            base_hooks.update({
                'modules': {
                    'table_reservations': {'status': 'implemented', 'complexity': 'high'},
                    'menu_management': {'status': 'planned', 'complexity': 'medium'},
                    'customer_loyalty': {'status': 'planned', 'complexity': 'medium'}
                }
            })
        elif industry == 'marketplace':
            base_hooks.update({
                'modules': {
                    'vendor_management': {'status': 'critical', 'complexity': 'high'},
                    'review_ratings': {'status': 'planned', 'complexity': 'medium'},
                    'analytics_dashboard': {'status': 'planned', 'complexity': 'high'}
                }
            })

        return base_hooks

    def export_scenario(self, scenario: Dict[str, Any], format: str = 'json') -> str:
        """Export scenario in specified format."""
        if format == 'json':
            return json.dumps(scenario, indent=2, default=str)
        elif format == 'python':
            return f"scenario_data = {scenario!r}"
        else:
            raise ValueError(f"Unsupported format: {format}")

    def list_industries(self) -> List[str]:
        """List available industries."""
        return list(self.industries.keys())


def main():
    parser = argparse.ArgumentParser(description='Generate Nairobi business scenarios for ERP testing')
    parser.add_argument('--industry', choices=['retail', 'hospitality', 'marketplace', 'logistics'],
                       help='Industry type for the scenario')
    parser.add_argument('--name', help='Custom name for the scenario')
    parser.add_argument('--complexity', choices=['low', 'medium', 'high'], default='medium',
                       help='Scenario complexity level')
    parser.add_argument('--format', choices=['json', 'python'], default='json',
                       help='Output format')
    parser.add_argument('--export-all', action='store_true',
                       help='Generate and export all industry scenarios')
    parser.add_argument('--list-industries', action='store_true',
                       help='List available industries')

    args = parser.parse_args()

    generator = ScenarioGenerator()

    if args.list_industries:
        print("Available industries:")
        for industry in generator.list_industries():
            template = generator.templates[industry]
            print(f"  - {industry}: {template['name']}")
        return

    if args.export_all:
        print("Generating all industry scenarios...")
        for industry in generator.list_industries():
            print(f"\n🏭 Generating {industry} scenario...")
            scenario = generator.generate_scenario(industry, complexity='medium')
            filename = f"scenario_{industry}_{scenario['id'][:8]}.json"
            with open(filename, 'w') as f:
                f.write(generator.export_scenario(scenario, 'json'))
            print(f"✅ Exported to {filename}")
        return

    if not args.industry:
        parser.error("Must specify --industry or use --export-all or --list-industries")

    print(f"🏭 Generating {args.industry} scenario...")
    scenario = generator.generate_scenario(args.industry, args.name, args.complexity)

    if args.format == 'json':
        print(generator.export_scenario(scenario, 'json'))
    else:
        print(generator.export_scenario(scenario, 'python'))


if __name__ == "__main__":
    main()
