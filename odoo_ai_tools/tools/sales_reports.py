# -*- coding: utf-8 -*-
"""
Tool 1: Sales Reports
=====================
Generate sales reports from natural language using Claude + Odoo API.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .odoo_api_client import OdooAPIClient


def generate_sales_report(
    url: str,
    db: str,
    username: str,
    password: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    group_by: str = 'product',
    product_ids: Optional[List[int]] = None,
    partner_ids: Optional[List[int]] = None
) -> Dict:
    """
    Generate sales report from natural language parameters.

    This function is designed to be called by Claude AI as a tool.

    Args:
        url (str): Odoo server URL
        db (str): Database name
        username (str): User login
        password (str): User password
        date_from (str, optional): Start date (YYYY-MM-DD)
        date_to (str, optional): End date (YYYY-MM-DD)
        group_by (str): Group by 'product', 'customer', or 'salesperson'
        product_ids (list[int], optional): Filter by products
        partner_ids (list[int], optional): Filter by customers

    Returns:
        dict: {
            'success': bool,
            'data': list[dict] or None,
            'summary': dict or None,
            'error': str or None
        }

    Example Claude prompt:
        "Generate a sales report by product from March to July"
        →
 date_from='2025-03-01', date_to='2025-07-31', group_by='product'
    """
    try:
        # Initialize API client
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        # Check permissions
        if not client.check_access_rights('sale.order', 'read'):
            return {
                'success': False,
                'data': None,
                'summary': None,
                'error': f"User '{username}' lacks permission to read sales orders"
            }

        # Build domain
        domain = [('state', 'in', ['sale', 'done'])]  # Only confirmed sales

        if date_from:
            domain.append(('date_order', '>=', date_from))
        if date_to:
            domain.append(('date_order', '<=', date_to))
        if partner_ids:
            domain.append(('partner_id', 'in', partner_ids))

        # Get sales orders
        orders = client.search_read(
            'sale.order',
            domain,
            ['name', 'partner_id', 'date_order', 'amount_total', 'user_id', 'order_line']
        )

        if not orders:
            return {
                'success': True,
                'data': [],
                'summary': {'total_sales': 0, 'order_count': 0},
                'error': None
            }

        # Get order lines
        all_line_ids = []
        for order in orders:
            all_line_ids.extend(order.get('order_line', []))

        line_domain = [('id', 'in', all_line_ids)]
        if product_ids:
            line_domain.append(('product_id', 'in', product_ids))

        lines = client.search_read(
            'sale.order.line',
            line_domain,
            ['order_id', 'product_id', 'product_uom_qty', 'price_subtotal']
        )

        # Group data
        if group_by == 'product':
            report_data = _group_by_product(lines, client)
        elif group_by == 'customer':
            report_data = _group_by_customer(orders, lines, client)
        elif group_by == 'salesperson':
            report_data = _group_by_salesperson(orders, client)
        else:
            report_data = _group_by_product(lines, client)  # Default

        # Calculate summary
        summary = {
            'total_sales': sum(item['total_amount'] for item in report_data),
            'order_count': len(orders),
            'line_count': len(lines),
            'date_from': date_from or 'N/A',
            'date_to': date_to or 'N/A',
            'group_by': group_by
        }

        return {
            'success': True,
            'data': report_data,
            'summary': summary,
            'error': None
        }

    except PermissionError as e:
        return {
            'success': False,
            'data': None,
            'summary': None,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'summary': None,
            'error': f"Error generating report: {str(e)}"
        }


def _group_by_product(lines: List[Dict], client: OdooAPIClient) -> List[Dict]:
    """Group sales lines by product."""
    product_data = {}

    for line in lines:
        product_id = line['product_id'][0] if line['product_id'] else None
        if not product_id:
            continue

        product_name = line['product_id'][1]

        if product_id not in product_data:
            product_data[product_id] = {
                'product_id': product_id,
                'product_name': product_name,
                'quantity_sold': 0,
                'total_amount': 0,
                'line_count': 0
            }

        product_data[product_id]['quantity_sold'] += line.get('product_uom_qty', 0)
        product_data[product_id]['total_amount'] += line.get('price_subtotal', 0)
        product_data[product_id]['line_count'] += 1

    # Sort by total amount descending
    result = sorted(
        product_data.values(),
        key=lambda x: x['total_amount'],
        reverse=True
    )

    return result


def _group_by_customer(orders: List[Dict], lines: List[Dict], client: OdooAPIClient) -> List[Dict]:
    """Group sales by customer."""
    customer_data = {}

    for order in orders:
        partner_id = order['partner_id'][0] if order['partner_id'] else None
        if not partner_id:
            continue

        partner_name = order['partner_id'][1]

        if partner_id not in customer_data:
            customer_data[partner_id] = {
                'customer_id': partner_id,
                'customer_name': partner_name,
                'order_count': 0,
                'total_amount': 0
            }

        customer_data[partner_id]['order_count'] += 1
        customer_data[partner_id]['total_amount'] += order.get('amount_total', 0)

    result = sorted(
        customer_data.values(),
        key=lambda x: x['total_amount'],
        reverse=True
    )

    return result


def _group_by_salesperson(orders: List[Dict], client: OdooAPIClient) -> List[Dict]:
    """Group sales by salesperson."""
    salesperson_data = {}

    for order in orders:
        user_id = order['user_id'][0] if order['user_id'] else None
        if not user_id:
            continue

        user_name = order['user_id'][1]

        if user_id not in salesperson_data:
            salesperson_data[user_id] = {
                'salesperson_id': user_id,
                'salesperson_name': user_name,
                'order_count': 0,
                'total_amount': 0
            }

        salesperson_data[user_id]['order_count'] += 1
        salesperson_data[user_id]['total_amount'] += order.get('amount_total', 0)

    result = sorted(
        salesperson_data.values(),
        key=lambda x: x['total_amount'],
        reverse=True
    )

    return result


# Tool definition for Claude API
SALES_REPORT_TOOL = {
    "name": "generate_sales_report",
    "description": "Generate sales reports from Odoo based on natural language parameters. Can group by product, customer, or salesperson. Respects user permissions.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Odoo server URL (e.g., 'http://localhost:8069')"
            },
            "db": {
                "type": "string",
                "description": "Odoo database name"
            },
            "username": {
                "type": "string",
                "description": "Odoo user login"
            },
            "password": {
                "type": "string",
                "description": "Odoo user password"
            },
            "date_from": {
                "type": "string",
                "description": "Start date in YYYY-MM-DD format (optional)"
            },
            "date_to": {
                "type": "string",
                "description": "End date in YYYY-MM-DD format (optional)"
            },
            "group_by": {
                "type": "string",
                "enum": ["product", "customer", "salesperson"],
                "description": "How to group the report"
            },
            "product_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Filter by specific product IDs (optional)"
            },
            "partner_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Filter by specific customer IDs (optional)"
            }
        },
        "required": ["url", "db", "username", "password"]
    }
}
