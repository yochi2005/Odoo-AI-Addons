# -*- coding: utf-8 -*-
{
    'name': 'Odoo AI Tools - Claude Integration',
    'version': '18.2.1.0.0',
    'category': 'Artificial Intelligence',
    'summary': 'Claude AI integration with Odoo using tool calling and Web API',
    'description': """
        Odoo AI Tools - Claude Integration
        ===================================

        This module integrates Anthropic's Claude AI with Odoo using:
        - Claude API (tool calling capability)
        - Odoo JSON-RPC Web API (secure, permission-based)
        - Natural language processing for ERP operations

        Features:
        ---------
        1. **Sales Reports**: Generate sales reports from natural language
        2. **Invoice Creation**: Create draft invoices automatically
        3. **Tax Deductions**: Suggest tax-deductible expenses (Mexico)
        4. **Quotation Summary**: Intelligent quotation follow-up
        5. **Inventory Restock**: Detect products needing restock

        All operations respect user permissions via Odoo Web API.
        No direct database access.

        Requirements:
        -------------
        - anthropic Python package
        - Odoo 18.2+
        - Valid Anthropic API key
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'account',
        'stock',
    ],
    'external_dependencies': {
        'python': ['anthropic'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/ai_assistant_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
