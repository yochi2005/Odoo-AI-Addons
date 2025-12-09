# -*- coding: utf-8 -*-
"""
Tool 4: Quotation Summary
==========================
Intelligent summary of quotations requiring follow-up.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .odoo_api_client import OdooAPIClient


# Activity urgency mapping
URGENCY_LEVELS = {
    'overdue': {
        'priority': 1,
        'description': 'Vencida - Requiere atención inmediata'
    },
    'today': {
        'priority': 2,
        'description': 'Vence hoy - Urgente'
    },
    'this_week': {
        'priority': 3,
        'description': 'Vence esta semana - Alta prioridad'
    },
    'next_week': {
        'priority': 4,
        'description': 'Vence próxima semana - Media prioridad'
    },
    'later': {
        'priority': 5,
        'description': 'Sin vencimiento próximo'
    }
}


def summarize_quotations(
    url: str,
    db: str,
    username: str,
    password: str,
    days_ahead: Optional[int] = 7,
    min_amount: Optional[float] = None,
    salesperson_id: Optional[int] = None,
    include_activities: bool = True
) -> Dict:
    """
    Generate intelligent summary of quotations requiring follow-up.

    This function is designed to be called by Claude AI as a tool.

    Args:
        url (str): Odoo server URL
        db (str): Database name
        username (str): User login
        password (str): User password
        days_ahead (int): Look ahead N days for follow-up (default: 7)
        min_amount (float, optional): Minimum quotation amount
        salesperson_id (int, optional): Filter by salesperson
        include_activities (bool): Include scheduled activities

    Returns:
        dict: {
            'success': bool,
            'quotations': list[dict] or None,
            'summary': dict or None,
            'error': str or None
        }

    Example Claude prompt:
        "Which quotations need follow-up this week?"
        → days_ahead=7
    """
    try:
        # Initialize API client
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        # Check permissions
        if not client.check_access_rights('sale.order', 'read'):
            return {
                'success': False,
                'quotations': None,
                'summary': None,
                'error': f"User '{username}' lacks permission to read quotations"
            }

        # Build domain for quotations
        domain = [
            ('state', 'in', ['draft', 'sent']),  # Only quotations, not confirmed sales
        ]

        if min_amount:
            domain.append(('amount_total', '>=', min_amount))
        if salesperson_id:
            domain.append(('user_id', '=', salesperson_id))

        # Get quotations
        quotations = client.search_read(
            'sale.order',
            domain,
            ['name', 'partner_id', 'user_id', 'date_order', 'validity_date',
             'amount_total', 'state', 'activity_ids'],
            order='validity_date asc'
        )

        if not quotations:
            return {
                'success': True,
                'quotations': [],
                'summary': {'total_quotations': 0, 'total_amount': 0},
                'error': 'No quotations found'
            }

        # Analyze each quotation
        analyzed_quotations = []
        total_amount = 0

        for quote in quotations:
            analysis = _analyze_quotation(
                client,
                quote,
                days_ahead,
                include_activities
            )
            analyzed_quotations.append(analysis)
            total_amount += quote['amount_total']

        # Sort by urgency
        analyzed_quotations.sort(key=lambda x: x['urgency_priority'])

        # Calculate summary
        by_urgency = {}
        for quote in analyzed_quotations:
            urgency = quote['urgency_level']
            if urgency not in by_urgency:
                by_urgency[urgency] = {
                    'count': 0,
                    'total_amount': 0
                }
            by_urgency[urgency]['count'] += 1
            by_urgency[urgency]['total_amount'] += quote['amount']

        summary = {
            'total_quotations': len(analyzed_quotations),
            'total_amount': total_amount,
            'by_urgency': by_urgency,
            'days_ahead': days_ahead
        }

        return {
            'success': True,
            'quotations': analyzed_quotations,
            'summary': summary,
            'error': None
        }

    except PermissionError as e:
        return {
            'success': False,
            'quotations': None,
            'summary': None,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'quotations': None,
            'summary': None,
            'error': f"Error analyzing quotations: {str(e)}"
        }


def _analyze_quotation(
    client: OdooAPIClient,
    quote: Dict,
    days_ahead: int,
    include_activities: bool
) -> Dict:
    """
    Analyze a quotation to determine urgency and actions needed.

    Args:
        client (OdooAPIClient): Authenticated API client
        quote (dict): Quotation data
        days_ahead (int): Days to look ahead
        include_activities (bool): Include activities

    Returns:
        dict: Analysis result
    """
    today = datetime.now().date()
    validity_date = None

    if quote.get('validity_date'):
        validity_date = datetime.strptime(quote['validity_date'], '%Y-%m-%d').date()

    # Determine urgency
    urgency_level = 'later'
    days_until_expiry = None

    if validity_date:
        days_until_expiry = (validity_date - today).days

        if days_until_expiry < 0:
            urgency_level = 'overdue'
        elif days_until_expiry == 0:
            urgency_level = 'today'
        elif days_until_expiry <= 7:
            urgency_level = 'this_week'
        elif days_until_expiry <= 14:
            urgency_level = 'next_week'

    urgency_info = URGENCY_LEVELS[urgency_level]

    # Get activities if requested
    activities = []
    if include_activities and quote.get('activity_ids'):
        activity_data = client.read(
            'mail.activity',
            quote['activity_ids'],
            ['activity_type_id', 'summary', 'date_deadline', 'user_id']
        )

        for act in activity_data:
            act_deadline = datetime.strptime(act['date_deadline'], '%Y-%m-%d').date()
            days_until_act = (act_deadline - today).days

            if days_until_act <= days_ahead:
                activities.append({
                    'type': act['activity_type_id'][1] if act.get('activity_type_id') else 'Activity',
                    'summary': act.get('summary', ''),
                    'deadline': act['date_deadline'],
                    'days_until': days_until_act,
                    'assigned_to': act['user_id'][1] if act.get('user_id') else 'Unassigned'
                })

    # Build analysis
    analysis = {
        'quotation_id': quote['id'],
        'quotation_number': quote['name'],
        'customer': quote['partner_id'][1] if quote.get('partner_id') else 'N/A',
        'salesperson': quote['user_id'][1] if quote.get('user_id') else 'Unassigned',
        'amount': quote['amount_total'],
        'state': quote['state'],
        'date_order': quote.get('date_order'),
        'validity_date': quote.get('validity_date'),
        'days_until_expiry': days_until_expiry,
        'urgency_level': urgency_level,
        'urgency_priority': urgency_info['priority'],
        'urgency_description': urgency_info['description'],
        'has_activities': len(activities) > 0,
        'activities': activities,
        'recommended_action': _get_recommended_action(
            urgency_level,
            quote['state'],
            len(activities)
        )
    }

    return analysis


def _get_recommended_action(urgency_level: str, state: str, activity_count: int) -> str:
    """
    Get recommended action based on quotation status.

    Args:
        urgency_level (str): Urgency level
        state (str): Quotation state
        activity_count (int): Number of pending activities

    Returns:
        str: Recommended action
    """
    if urgency_level == 'overdue':
        return "URGENTE: Cotización vencida. Contactar cliente para renovar o cerrar."

    if urgency_level == 'today':
        return "Vence hoy. Contactar cliente inmediatamente para confirmar."

    if urgency_level == 'this_week':
        if state == 'draft':
            return "Enviar cotización al cliente cuanto antes."
        else:
            return "Hacer seguimiento para confirmar antes del vencimiento."

    if activity_count > 0:
        return f"Completar {activity_count} actividad(es) pendiente(s)."

    if state == 'draft':
        return "Revisar y enviar cotización al cliente."

    return "Monitorear y hacer seguimiento periódico."


# Tool definition for Claude API
QUOTATION_SUMMARY_TOOL = {
    "name": "summarize_quotations",
    "description": "Generate intelligent summary of quotations requiring follow-up. Analyzes urgency, expiration dates, and pending activities. Provides recommended actions.",
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
            "days_ahead": {
                "type": "integer",
                "description": "Look ahead N days for follow-up (default: 7)"
            },
            "min_amount": {
                "type": "number",
                "description": "Minimum quotation amount to consider (optional)"
            },
            "salesperson_id": {
                "type": "integer",
                "description": "Filter by salesperson ID (optional)"
            },
            "include_activities": {
                "type": "boolean",
                "description": "Include scheduled activities in analysis (default: true)"
            }
        },
        "required": ["url", "db", "username", "password"]
    }
}
