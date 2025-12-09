# -*- coding: utf-8 -*-
"""
Tool 5: Inventory Restock Detection
====================================
Detect products that need restocking based on inventory levels and sales velocity.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .odoo_api_client import OdooAPIClient


# Restock urgency levels
RESTOCK_URGENCY = {
    'critical': {
        'priority': 1,
        'description': 'Stock crítico - Ordenar inmediatamente',
        'threshold': 0  # Out of stock
    },
    'urgent': {
        'priority': 2,
        'description': 'Stock bajo - Ordenar esta semana',
        'threshold': 0.2  # Below 20% of min
    },
    'soon': {
        'priority': 3,
        'description': 'Stock moderado - Planificar orden',
        'threshold': 0.5  # Below 50% of min
    },
    'normal': {
        'priority': 4,
        'description': 'Stock adecuado',
        'threshold': 1.0  # Above minimum
    }
}


def detect_restock_needs(
    url: str,
    db: str,
    username: str,
    password: str,
    warehouse_id: Optional[int] = None,
    category_ids: Optional[List[int]] = None,
    days_for_velocity: int = 30,
    include_forecasted: bool = True
) -> Dict:
    """
    Detect products that need restocking.

    This function is designed to be called by Claude AI as a tool.

    Args:
        url (str): Odoo server URL
        db (str): Database name
        username (str): User login
        password (str): User password
        warehouse_id (int, optional): Filter by warehouse
        category_ids (list[int], optional): Filter by product categories
        days_for_velocity (int): Days to calculate sales velocity (default: 30)
        include_forecasted (bool): Include forecasted quantities (default: true)

    Returns:
        dict: {
            'success': bool,
            'products_to_restock': list[dict] or None,
            'summary': dict or None,
            'error': str or None
        }

    Example Claude prompt:
        "What products should I order before Friday?"
        → analyze with urgency levels
    """
    try:
        # Initialize API client
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        # Check permissions
        if not client.check_access_rights('product.product', 'read'):
            return {
                'success': False,
                'products_to_restock': None,
                'summary': None,
                'error': f"User '{username}' lacks permission to read products"
            }

        # Build domain for storable products
        domain = [
            ('type', '=', 'product'),  # Storable products only
            ('active', '=', True)
        ]

        if category_ids:
            domain.append(('categ_id', 'in', category_ids))

        # Get products
        products = client.search_read(
            'product.product',
            domain,
            ['name', 'default_code', 'categ_id', 'qty_available',
             'virtual_available', 'seller_ids'],
            limit=500
        )

        if not products:
            return {
                'success': True,
                'products_to_restock': [],
                'summary': {'total_products': 0},
                'error': 'No products found'
            }

        # Analyze each product
        products_to_restock = []

        for product in products:
            analysis = _analyze_product_stock(
                client,
                product,
                warehouse_id,
                days_for_velocity,
                include_forecasted
            )

            # Only include if needs restock
            if analysis and analysis['urgency_level'] != 'normal':
                products_to_restock.append(analysis)

        # Sort by urgency
        products_to_restock.sort(key=lambda x: x['urgency_priority'])

        # Calculate summary
        by_urgency = {}
        for prod in products_to_restock:
            urgency = prod['urgency_level']
            if urgency not in by_urgency:
                by_urgency[urgency] = {
                    'count': 0,
                    'total_qty_needed': 0
                }
            by_urgency[urgency]['count'] += 1
            by_urgency[urgency]['total_qty_needed'] += prod.get('suggested_order_qty', 0)

        summary = {
            'total_products': len(products_to_restock),
            'analyzed_products': len(products),
            'by_urgency': by_urgency,
            'warehouse_id': warehouse_id or 'All'
        }

        return {
            'success': True,
            'products_to_restock': products_to_restock,
            'summary': summary,
            'error': None
        }

    except PermissionError as e:
        return {
            'success': False,
            'products_to_restock': None,
            'summary': None,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'products_to_restock': None,
            'summary': None,
            'error': f"Error detecting restock needs: {str(e)}"
        }


def _analyze_product_stock(
    client: OdooAPIClient,
    product: Dict,
    warehouse_id: Optional[int],
    days_for_velocity: int,
    include_forecasted: bool
) -> Optional[Dict]:
    """
    Analyze a product's stock level and determine restock needs.

    Args:
        client (OdooAPIClient): Authenticated API client
        product (dict): Product data
        warehouse_id (int, optional): Warehouse ID
        days_for_velocity (int): Days for velocity calculation
        include_forecasted (bool): Use forecasted quantities

    Returns:
        dict or None: Analysis result
    """
    product_id = product['id']
    qty_available = product.get('qty_available', 0)
    virtual_available = product.get('virtual_available', 0)

    current_qty = virtual_available if include_forecasted else qty_available

    # Get reordering rules (minimum stock levels)
    reorder_domain = [('product_id', '=', product_id)]
    if warehouse_id:
        reorder_domain.append(('warehouse_id', '=', warehouse_id))

    try:
        reorder_rules = client.search_read(
            'stock.warehouse.orderpoint',
            reorder_domain,
            ['product_min_qty', 'product_max_qty', 'qty_multiple']
        )
    except:
        # Model might not be accessible
        reorder_rules = []

    # Determine minimum quantity
    min_qty = 0
    max_qty = 0
    qty_multiple = 1

    if reorder_rules:
        rule = reorder_rules[0]
        min_qty = rule.get('product_min_qty', 0)
        max_qty = rule.get('product_max_qty', 0)
        qty_multiple = rule.get('qty_multiple', 1)

    # Calculate sales velocity (last N days)
    sales_velocity = _calculate_sales_velocity(
        client,
        product_id,
        days_for_velocity
    )

    # Determine urgency
    urgency_level = 'normal'

    if current_qty <= 0:
        urgency_level = 'critical'
    elif min_qty > 0:
        stock_ratio = current_qty / min_qty
        if stock_ratio <= 0.2:
            urgency_level = 'urgent'
        elif stock_ratio <= 0.5:
            urgency_level = 'soon'

    urgency_info = RESTOCK_URGENCY[urgency_level]

    # Calculate suggested order quantity
    suggested_order_qty = 0
    if urgency_level != 'normal':
        if max_qty > 0:
            suggested_order_qty = max(max_qty - current_qty, 0)
        elif min_qty > 0:
            suggested_order_qty = max(min_qty * 2 - current_qty, 0)
        else:
            # Estimate based on sales velocity
            suggested_order_qty = max(sales_velocity * 30, 10)  # 30 days worth

        # Round to qty_multiple
        if qty_multiple > 1:
            suggested_order_qty = ((suggested_order_qty // qty_multiple) + 1) * qty_multiple

    # Get supplier info
    supplier_info = _get_supplier_info(client, product)

    # Build analysis
    analysis = {
        'product_id': product_id,
        'product_name': product['name'],
        'product_code': product.get('default_code', ''),
        'category': product['categ_id'][1] if product.get('categ_id') else 'N/A',
        'qty_available': qty_available,
        'virtual_available': virtual_available,
        'min_qty': min_qty,
        'max_qty': max_qty,
        'sales_velocity_per_day': round(sales_velocity, 2),
        'days_of_stock_remaining': round(current_qty / sales_velocity, 1) if sales_velocity > 0 else 999,
        'urgency_level': urgency_level,
        'urgency_priority': urgency_info['priority'],
        'urgency_description': urgency_info['description'],
        'suggested_order_qty': int(suggested_order_qty),
        'supplier': supplier_info,
        'recommended_action': _get_restock_action(urgency_level, suggested_order_qty, supplier_info)
    }

    return analysis


def _calculate_sales_velocity(
    client: OdooAPIClient,
    product_id: int,
    days: int
) -> float:
    """
    Calculate average daily sales velocity.

    Args:
        client (OdooAPIClient): Authenticated API client
        product_id (int): Product ID
        days (int): Number of days to analyze

    Returns:
        float: Average units sold per day
    """
    date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    try:
        # Get sold quantities from confirmed sales orders
        lines = client.search_read(
            'sale.order.line',
            [
                ('product_id', '=', product_id),
                ('order_id.state', 'in', ['sale', 'done']),
                ('order_id.date_order', '>=', date_from)
            ],
            ['product_uom_qty']
        )

        total_qty = sum(line.get('product_uom_qty', 0) for line in lines)
        velocity = total_qty / days if days > 0 else 0

        return velocity

    except:
        return 0.0


def _get_supplier_info(client: OdooAPIClient, product: Dict) -> Optional[Dict]:
    """
    Get supplier information for a product.

    Args:
        client (OdooAPIClient): Authenticated API client
        product (dict): Product data

    Returns:
        dict or None: Supplier info
    """
    seller_ids = product.get('seller_ids', [])

    if not seller_ids:
        return None

    try:
        sellers = client.read(
            'product.supplierinfo',
            seller_ids[:1],  # First supplier only
            ['partner_id', 'price', 'min_qty', 'delay']
        )

        if sellers:
            seller = sellers[0]
            return {
                'supplier_name': seller['partner_id'][1] if seller.get('partner_id') else 'N/A',
                'price': seller.get('price', 0),
                'min_order_qty': seller.get('min_qty', 0),
                'lead_time_days': seller.get('delay', 0)
            }

    except:
        pass

    return None


def _get_restock_action(urgency_level: str, qty: float, supplier: Optional[Dict]) -> str:
    """
    Get recommended restock action.

    Args:
        urgency_level (str): Urgency level
        qty (float): Suggested order quantity
        supplier (dict, optional): Supplier info

    Returns:
        str: Recommended action
    """
    if urgency_level == 'critical':
        action = f"URGENTE: Ordenar {int(qty)} unidades INMEDIATAMENTE"
    elif urgency_level == 'urgent':
        action = f"Ordenar {int(qty)} unidades esta semana"
    elif urgency_level == 'soon':
        action = f"Planificar orden de {int(qty)} unidades"
    else:
        return "Stock adecuado, no requiere acción"

    if supplier:
        lead_time = supplier.get('lead_time_days', 0)
        if lead_time > 0:
            action += f" (Tiempo de entrega: {lead_time} días)"

    return action


# Tool definition for Claude API
INVENTORY_RESTOCK_TOOL = {
    "name": "detect_restock_needs",
    "description": "Detect products that need restocking based on current stock levels, minimum quantities, and sales velocity. Provides urgency levels and suggested order quantities.",
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
            "warehouse_id": {
                "type": "integer",
                "description": "Filter by warehouse ID (optional)"
            },
            "category_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Filter by product category IDs (optional)"
            },
            "days_for_velocity": {
                "type": "integer",
                "description": "Days to calculate sales velocity (default: 30)"
            },
            "include_forecasted": {
                "type": "boolean",
                "description": "Include forecasted quantities in analysis (default: true)"
            }
        },
        "required": ["url", "db", "username", "password"]
    }
}
