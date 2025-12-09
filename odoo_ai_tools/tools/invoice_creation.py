# -*- coding: utf-8 -*-
"""
Tool 2: Invoice Creation
=========================
Create draft invoices automatically from natural language using Claude + Odoo API.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from .odoo_api_client import OdooAPIClient


def create_invoice_from_sales(
    url: str,
    db: str,
    username: str,
    password: str,
    sale_order_ids: Optional[List[int]] = None,
    last_n_orders: Optional[int] = None,
    partner_id: Optional[int] = None,
    invoice_date: Optional[str] = None
) -> Dict:
    """
    Create draft invoices from sales orders.

    This function is designed to be called by Claude AI as a tool.

    Args:
        url (str): Odoo server URL
        db (str): Database name
        username (str): User login
        password (str): User password
        sale_order_ids (list[int], optional): Specific sale order IDs
        last_n_orders (int, optional): Create invoices for last N orders
        partner_id (int, optional): Filter by customer
        invoice_date (str, optional): Invoice date (YYYY-MM-DD)

    Returns:
        dict: {
            'success': bool,
            'invoices_created': list[dict] or None,
            'summary': dict or None,
            'error': str or None
        }

    Example Claude prompt:
        "Generate invoices for the last 3 sales"
        → last_n_orders=3
    """
    try:
        # Initialize API client
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        # Check permissions
        if not client.check_access_rights('account.move', 'create'):
            return {
                'success': False,
                'invoices_created': None,
                'summary': None,
                'error': f"User '{username}' lacks permission to create invoices"
            }

        # Build domain for sales orders
        domain = [
            ('state', '=', 'sale'),  # Only confirmed sales
            ('invoice_status', 'in', ['to invoice', 'no'])  # Not fully invoiced
        ]

        if sale_order_ids:
            domain.append(('id', 'in', sale_order_ids))
        if partner_id:
            domain.append(('partner_id', '=', partner_id))

        # Get sales orders
        orders = client.search_read(
            'sale.order',
            domain,
            ['name', 'partner_id', 'amount_total', 'order_line'],
            limit=last_n_orders,
            order='date_order desc'
        )

        if not orders:
            return {
                'success': True,
                'invoices_created': [],
                'summary': {'total_invoices': 0, 'total_amount': 0},
                'error': 'No sales orders found matching criteria'
            }

        invoices_created = []
        total_amount = 0

        for order in orders:
            try:
                # Create invoice from sale order
                invoice_id = _create_invoice_from_order(
                    client,
                    order,
                    invoice_date
                )

                if invoice_id:
                    # Read created invoice
                    invoice_data = client.read(
                        'account.move',
                        [invoice_id],
                        ['name', 'partner_id', 'amount_total', 'state', 'invoice_date']
                    )[0]

                    invoices_created.append({
                        'invoice_id': invoice_id,
                        'invoice_number': invoice_data['name'],
                        'sale_order': order['name'],
                        'customer': order['partner_id'][1],
                        'amount': invoice_data['amount_total'],
                        'state': invoice_data['state'],
                        'invoice_date': invoice_data.get('invoice_date')
                    })

                    total_amount += invoice_data['amount_total']

            except Exception as e:
                # Log error but continue with other orders
                print(f"Error creating invoice for order {order['name']}: {str(e)}")
                continue

        summary = {
            'total_invoices': len(invoices_created),
            'total_amount': total_amount,
            'source_orders': len(orders)
        }

        return {
            'success': True,
            'invoices_created': invoices_created,
            'summary': summary,
            'error': None
        }

    except PermissionError as e:
        return {
            'success': False,
            'invoices_created': None,
            'summary': None,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'invoices_created': None,
            'summary': None,
            'error': f"Error creating invoices: {str(e)}"
        }


def _create_invoice_from_order(
    client: OdooAPIClient,
    order: Dict,
    invoice_date: Optional[str] = None
) -> Optional[int]:
    """
    Create a draft invoice from a sale order.

    Args:
        client (OdooAPIClient): Authenticated API client
        order (dict): Sale order data
        invoice_date (str, optional): Invoice date

    Returns:
        int: Invoice ID or None
    """
    # Get order lines
    line_ids = order.get('order_line', [])
    if not line_ids:
        return None

    lines = client.search_read(
        'sale.order.line',
        [('id', 'in', line_ids)],
        ['product_id', 'name', 'product_uom_qty', 'price_unit', 'tax_id']
    )

    # Prepare invoice lines
    invoice_lines = []
    for line in lines:
        invoice_line = {
            'product_id': line['product_id'][0] if line['product_id'] else False,
            'name': line['name'],
            'quantity': line['product_uom_qty'],
            'price_unit': line['price_unit'],
        }

        if line.get('tax_id'):
            invoice_line['tax_ids'] = [(6, 0, line['tax_id'])]

        invoice_lines.append((0, 0, invoice_line))

    # Prepare invoice values
    invoice_vals = {
        'partner_id': order['partner_id'][0],
        'move_type': 'out_invoice',  # Customer invoice
        'invoice_line_ids': invoice_lines,
    }

    if invoice_date:
        invoice_vals['invoice_date'] = invoice_date

    # Create invoice
    invoice_id = client.create('account.move', invoice_vals)

    return invoice_id


# Tool definition for Claude API
INVOICE_CREATION_TOOL = {
    "name": "create_invoice_from_sales",
    "description": "Create draft customer invoices from confirmed sales orders. Can process specific orders or the last N orders. Respects user permissions.",
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
            "sale_order_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Specific sale order IDs to invoice (optional)"
            },
            "last_n_orders": {
                "type": "integer",
                "description": "Create invoices for the last N confirmed orders (optional)"
            },
            "partner_id": {
                "type": "integer",
                "description": "Filter by customer ID (optional)"
            },
            "invoice_date": {
                "type": "string",
                "description": "Invoice date in YYYY-MM-DD format (optional, defaults to today)"
            }
        },
        "required": ["url", "db", "username", "password"]
    }
}
