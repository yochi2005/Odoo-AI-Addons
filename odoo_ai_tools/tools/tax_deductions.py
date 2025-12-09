# -*- coding: utf-8 -*-
"""
Tool 3: Tax Deductions (Mexico)
================================
Suggest tax-deductible expenses from accounting entries.
Focused on Mexican tax regulations (SAT).
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .odoo_api_client import OdooAPIClient


# Deductible expense categories (Mexico SAT)
DEDUCTIBLE_CATEGORIES = {
    'office_supplies': {
        'keywords': ['papelería', 'office', 'suministros', 'toner', 'papel'],
        'description': 'Gastos de papelería y suministros de oficina',
        'sat_requirement': 'Factura con RFC'
    },
    'rent': {
        'keywords': ['renta', 'arrendamiento', 'rent', 'lease'],
        'description': 'Arrendamiento de inmuebles',
        'sat_requirement': 'Factura + Contrato de arrendamiento'
    },
    'utilities': {
        'keywords': ['luz', 'agua', 'teléfono', 'internet', 'electricity', 'water'],
        'description': 'Servicios (luz, agua, teléfono, internet)',
        'sat_requirement': 'Facturas de servicios'
    },
    'fuel': {
        'keywords': ['gasolina', 'diesel', 'combustible', 'fuel', 'gas'],
        'description': 'Combustibles y lubricantes',
        'sat_requirement': 'Factura + Tarjeta de control vehicular'
    },
    'maintenance': {
        'keywords': ['mantenimiento', 'reparación', 'maintenance', 'repair'],
        'description': 'Mantenimiento y reparaciones',
        'sat_requirement': 'Factura con descripción detallada'
    },
    'professional_fees': {
        'keywords': ['honorarios', 'consultoría', 'asesoría', 'consulting', 'fees'],
        'description': 'Honorarios profesionales',
        'sat_requirement': 'Factura + Retención de ISR/IVA'
    },
    'advertising': {
        'keywords': ['publicidad', 'marketing', 'advertising', 'promoción'],
        'description': 'Gastos de publicidad y promoción',
        'sat_requirement': 'Factura con concepto detallado'
    },
    'travel': {
        'keywords': ['viaje', 'hotel', 'hospedaje', 'travel', 'viático'],
        'description': 'Gastos de viaje y viáticos',
        'sat_requirement': 'Facturas + Comprobante de viaje de negocios'
    },
    'insurance': {
        'keywords': ['seguro', 'insurance', 'póliza'],
        'description': 'Seguros y fianzas',
        'sat_requirement': 'Factura + Póliza'
    },
    'technology': {
        'keywords': ['software', 'computadora', 'equipo', 'technology', 'hardware'],
        'description': 'Equipos de cómputo y software',
        'sat_requirement': 'Factura con descripción del bien/servicio'
    }
}


def suggest_tax_deductions(
    url: str,
    db: str,
    username: str,
    password: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_amount: Optional[float] = None,
    include_categories: Optional[List[str]] = None
) -> Dict:
    """
    Suggest tax-deductible expenses from accounting entries (Mexico).

    This function is designed to be called by Claude AI as a tool.

    Args:
        url (str): Odoo server URL
        db (str): Database name
        username (str): User login
        password (str): User password
        date_from (str, optional): Start date (YYYY-MM-DD)
        date_to (str, optional): End date (YYYY-MM-DD)
        min_amount (float, optional): Minimum amount to consider
        include_categories (list[str], optional): Specific categories to check

    Returns:
        dict: {
            'success': bool,
            'deductible_expenses': list[dict] or None,
            'summary': dict or None,
            'error': str or None
        }

    Example Claude prompt:
        "What recent expenses can be tax deductible?"
        → date_from=last_month, date_to=today
    """
    try:
        # Initialize API client
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        # Check permissions
        if not client.check_access_rights('account.move.line', 'read'):
            return {
                'success': False,
                'deductible_expenses': None,
                'summary': None,
                'error': f"User '{username}' lacks permission to read accounting entries"
            }

        # Default dates (last 3 months if not specified)
        if not date_from:
            date_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')

        # Build domain for expense entries
        domain = [
            ('move_id.move_type', 'in', ['in_invoice', 'in_refund']),  # Vendor bills
            ('move_id.state', '=', 'posted'),  # Posted only
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('debit', '>', 0)  # Expense entries (debit > 0)
        ]

        if min_amount:
            domain.append(('debit', '>=', min_amount))

        # Get account move lines
        move_lines = client.search_read(
            'account.move.line',
            domain,
            ['move_id', 'name', 'date', 'debit', 'partner_id', 'account_id'],
            limit=500,
            order='date desc'
        )

        if not move_lines:
            return {
                'success': True,
                'deductible_expenses': [],
                'summary': {'total_deductible': 0, 'entry_count': 0},
                'error': 'No expenses found in the specified period'
            }

        # Categorize expenses
        categorized_expenses = _categorize_expenses(
            move_lines,
            include_categories
        )

        # Calculate summary
        total_deductible = sum(exp['amount'] for exp in categorized_expenses)
        by_category = {}
        for exp in categorized_expenses:
            cat = exp['category']
            if cat not in by_category:
                by_category[cat] = {
                    'count': 0,
                    'total_amount': 0
                }
            by_category[cat]['count'] += 1
            by_category[cat]['total_amount'] += exp['amount']

        summary = {
            'total_deductible': total_deductible,
            'entry_count': len(categorized_expenses),
            'date_from': date_from,
            'date_to': date_to,
            'by_category': by_category
        }

        return {
            'success': True,
            'deductible_expenses': categorized_expenses,
            'summary': summary,
            'error': None
        }

    except PermissionError as e:
        return {
            'success': False,
            'deductible_expenses': None,
            'summary': None,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'deductible_expenses': None,
            'summary': None,
            'error': f"Error analyzing deductions: {str(e)}"
        }


def _categorize_expenses(
    move_lines: List[Dict],
    include_categories: Optional[List[str]] = None
) -> List[Dict]:
    """
    Categorize expenses based on description keywords.

    Args:
        move_lines (list[dict]): Account move lines
        include_categories (list[str], optional): Filter by categories

    Returns:
        list[dict]: Categorized expenses
    """
    categorized = []

    for line in move_lines:
        description = (line.get('name') or '').lower()
        partner_name = ''
        if line.get('partner_id'):
            partner_name = line['partner_id'][1].lower()

        # Try to match category
        matched_category = None
        for cat_key, cat_data in DEDUCTIBLE_CATEGORIES.items():
            if include_categories and cat_key not in include_categories:
                continue

            for keyword in cat_data['keywords']:
                if keyword in description or keyword in partner_name:
                    matched_category = cat_key
                    break

            if matched_category:
                break

        # If matched, add to results
        if matched_category:
            category_info = DEDUCTIBLE_CATEGORIES[matched_category]

            categorized.append({
                'move_id': line['move_id'][0],
                'move_name': line['move_id'][1],
                'description': line['name'],
                'date': line['date'],
                'amount': line['debit'],
                'partner': line['partner_id'][1] if line.get('partner_id') else 'N/A',
                'category': matched_category,
                'category_description': category_info['description'],
                'sat_requirement': category_info['sat_requirement']
            })

    return categorized


# Tool definition for Claude API
TAX_DEDUCTIONS_TOOL = {
    "name": "suggest_tax_deductions",
    "description": "Analyze accounting entries to suggest tax-deductible expenses according to Mexican SAT regulations. Categorizes expenses and provides SAT requirements for each.",
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
                "description": "Start date in YYYY-MM-DD format (optional, defaults to 3 months ago)"
            },
            "date_to": {
                "type": "string",
                "description": "End date in YYYY-MM-DD format (optional, defaults to today)"
            },
            "min_amount": {
                "type": "number",
                "description": "Minimum expense amount to consider (optional)"
            },
            "include_categories": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": list(DEDUCTIBLE_CATEGORIES.keys())
                },
                "description": "Specific expense categories to analyze (optional, analyzes all if not specified)"
            }
        },
        "required": ["url", "db", "username", "password"]
    }
}
