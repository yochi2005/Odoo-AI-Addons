# -*- coding: utf-8 -*-
"""
AI Assistant Model
==================
Odoo model for interacting with Claude AI assistant.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class AIAssistant(models.Model):
    """AI Assistant powered by Claude for Odoo operations."""

    _name = 'ai.assistant'
    _description = 'AI Assistant (Claude + Odoo)'
    _order = 'create_date desc'

    name = fields.Char(
        string='Conversation Title',
        compute='_compute_name',
        store=True
    )
    user_message = fields.Text(
        string='Your Message',
        required=True
    )
    assistant_response = fields.Text(
        string='Assistant Response',
        readonly=True
    )
    tools_used = fields.Text(
        string='Tools Used',
        readonly=True,
        help='JSON data of tools called during conversation'
    )
    success = fields.Boolean(
        string='Success',
        default=False,
        readonly=True
    )
    error_message = fields.Text(
        string='Error',
        readonly=True
    )
    anthropic_api_key = fields.Char(
        string='Anthropic API Key',
        help='Your Anthropic API key (stored securely per conversation)'
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        readonly=True
    )
    create_date = fields.Datetime(
        string='Date',
        readonly=True
    )

    @api.depends('user_message')
    def _compute_name(self):
        """Generate conversation title from first message."""
        for record in self:
            if record.user_message:
                # Take first 50 chars as title
                record.name = record.user_message[:50] + ('...' if len(record.user_message) > 50 else '')
            else:
                record.name = 'New Conversation'

    def action_send_message(self):
        """Send message to Claude and get response."""
        self.ensure_one()

        if not self.user_message:
            raise UserError(_('Please enter a message'))

        if not self.anthropic_api_key:
            raise UserError(_(
                'Please configure your Anthropic API key.\n'
                'Get one at: https://console.anthropic.com/'
            ))

        try:
            # Import orchestrator
            from ..tools.claude_orchestrator import create_orchestrator

            # Get Odoo credentials (current user)
            odoo_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url',
                default='http://localhost:8069'
            )
            odoo_db = self.env.cr.dbname
            odoo_user = self.env.user.login

            # Note: For security, password should be entered by user
            # In production, use API keys or OAuth instead
            odoo_password = self.env.context.get('user_password')
            if not odoo_password:
                raise UserError(_(
                    'Password required for Odoo API access.\n'
                    'Please provide your password in the context.'
                ))

            # Create orchestrator
            orchestrator = create_orchestrator(
                api_key=self.anthropic_api_key,
                odoo_url=odoo_url,
                odoo_db=odoo_db,
                odoo_username=odoo_user,
                odoo_password=odoo_password
            )

            # Process message
            result = orchestrator.process_message(self.user_message)

            # Update record with response
            self.write({
                'assistant_response': result.get('response', ''),
                'tools_used': str(result.get('tools_used', [])),
                'success': result.get('success', False),
                'error_message': result.get('error')
            })

            _logger.info(f"AI Assistant processed message for user {self.env.user.login}")

        except ImportError as e:
            error_msg = _(
                'Anthropic package not installed.\n'
                'Install with: pip install anthropic'
            )
            self.write({
                'error_message': error_msg,
                'success': False
            })
            raise UserError(error_msg)

        except Exception as e:
            _logger.error(f"AI Assistant error: {str(e)}")
            self.write({
                'error_message': str(e),
                'success': False
            })
            raise UserError(_(f'Error: {str(e)}'))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Response received from AI Assistant'),
                'type': 'success',
                'sticky': False,
            }
        }


class AIAssistantConfig(models.TransientModel):
    """Configuration wizard for AI Assistant."""

    _name = 'ai.assistant.config'
    _description = 'AI Assistant Configuration'

    anthropic_api_key = fields.Char(
        string='Anthropic API Key',
        required=True,
        help='Get your API key at https://console.anthropic.com/'
    )
    user_password = fields.Char(
        string='Your Odoo Password',
        required=True,
        help='Required for Odoo API authentication'
    )
    test_message = fields.Char(
        string='Test Message',
        default='Hello, can you help me with Odoo?'
    )

    def action_test_connection(self):
        """Test Claude connection."""
        self.ensure_one()

        try:
            from ..tools.claude_orchestrator import create_orchestrator

            odoo_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url',
                default='http://localhost:8069'
            )

            orchestrator = create_orchestrator(
                api_key=self.anthropic_api_key,
                odoo_url=odoo_url,
                odoo_db=self.env.cr.dbname,
                odoo_username=self.env.user.login,
                odoo_password=self.user_password
            )

            result = orchestrator.process_message(self.test_message)

            if result.get('success'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Successful!'),
                        'message': result.get('response', ''),
                        'type': 'success',
                        'sticky': True,
                    }
                }
            else:
                raise UserError(result.get('error', 'Unknown error'))

        except Exception as e:
            raise UserError(_(f'Connection test failed: {str(e)}'))
