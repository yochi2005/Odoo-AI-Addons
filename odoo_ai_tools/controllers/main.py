# -*- coding: utf-8 -*-
"""
AI Assistant Controllers
========================
HTTP controllers for AI Assistant (future use for webhooks, API endpoints, etc.)
"""

from odoo import http
from odoo.http import request
import json


class AIAssistantController(http.Controller):
    """HTTP controller for AI Assistant."""

    @http.route('/ai_assistant/health', type='http', auth='public', methods=['GET'])
    def health_check(self, **kwargs):
        """Health check endpoint."""
        return json.dumps({
            'status': 'ok',
            'module': 'odoo_ai_tools',
            'version': '18.2.1.0.0'
        })

    # Future endpoints:
    # - /ai_assistant/chat (for real-time chat interface)
    # - /ai_assistant/webhook (for Claude streaming responses)
    # - /ai_assistant/tools (list available tools)
