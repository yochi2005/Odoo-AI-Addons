# -*- coding: utf-8 -*-
"""
Claude Orchestrator
===================
Orchestrates Claude AI with Odoo tools using Anthropic's tool calling API.
"""

import json
import os
from typing import Dict, List, Optional, Any

try:
    import anthropic
except ImportError:
    anthropic = None

from .sales_reports import generate_sales_report, SALES_REPORT_TOOL
from .invoice_creation import create_invoice_from_sales, INVOICE_CREATION_TOOL
from .tax_deductions import suggest_tax_deductions, TAX_DEDUCTIONS_TOOL
from .quotation_summary import summarize_quotations, QUOTATION_SUMMARY_TOOL
from .inventory_restock import detect_restock_needs, INVENTORY_RESTOCK_TOOL


# Tool function mapping
TOOL_FUNCTIONS = {
    'generate_sales_report': generate_sales_report,
    'create_invoice_from_sales': create_invoice_from_sales,
    'suggest_tax_deductions': suggest_tax_deductions,
    'summarize_quotations': summarize_quotations,
    'detect_restock_needs': detect_restock_needs,
}

# All tools for Claude
ALL_TOOLS = [
    SALES_REPORT_TOOL,
    INVOICE_CREATION_TOOL,
    TAX_DEDUCTIONS_TOOL,
    QUOTATION_SUMMARY_TOOL,
    INVENTORY_RESTOCK_TOOL,
]


class ClaudeOrchestrator:
    """
    Orchestrates Claude AI with Odoo tools.

    This class manages the interaction between Claude (LLM) and Odoo (ERP),
    allowing natural language queries to trigger Odoo operations via tools.
    """

    def __init__(
        self,
        api_key: str,
        odoo_url: str,
        odoo_db: str,
        odoo_username: str,
        odoo_password: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Claude orchestrator.

        Args:
            api_key (str): Anthropic API key
            odoo_url (str): Odoo server URL
            odoo_db (str): Odoo database name
            odoo_username (str): Odoo user login
            odoo_password (str): Odoo user password
            model (str): Claude model to use
        """
        if not anthropic:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Odoo credentials (will be passed to tools)
        self.odoo_credentials = {
            'url': odoo_url,
            'db': odoo_db,
            'username': odoo_username,
            'password': odoo_password
        }

        self.conversation_history = []

    def process_message(
        self,
        user_message: str,
        max_turns: int = 5
    ) -> Dict[str, Any]:
        """
        Process a user message through Claude with tool calling.

        Args:
            user_message (str): User's natural language query
            max_turns (int): Maximum conversation turns (prevents infinite loops)

        Returns:
            dict: {
                'response': str,  # Claude's final response
                'tools_used': list[dict],  # Tools that were called
                'success': bool,
                'error': str or None
            }
        """
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            tools_used = []
            turn_count = 0

            while turn_count < max_turns:
                turn_count += 1

                # Call Claude with tools
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    tools=ALL_TOOLS,
                    messages=self.conversation_history
                )

                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Check if Claude wants to use tools
                tool_use_blocks = [
                    block for block in response.content
                    if block.type == "tool_use"
                ]

                if not tool_use_blocks:
                    # Claude provided final answer
                    final_text = self._extract_text_response(response.content)

                    return {
                        'response': final_text,
                        'tools_used': tools_used,
                        'success': True,
                        'error': None
                    }

                # Process tool calls
                tool_results = []

                for tool_block in tool_use_blocks:
                    tool_name = tool_block.name
                    tool_input = tool_block.input

                    # Add Odoo credentials to tool input
                    tool_input.update(self.odoo_credentials)

                    # Execute tool
                    tool_result = self._execute_tool(tool_name, tool_input)

                    # Record tool usage
                    tools_used.append({
                        'tool': tool_name,
                        'input': tool_input,
                        'result': tool_result
                    })

                    # Prepare result for Claude
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })

                # Add tool results to conversation
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })

            # Max turns reached
            return {
                'response': "I've reached the maximum number of conversation turns. Please try rephrasing your question.",
                'tools_used': tools_used,
                'success': False,
                'error': 'Max conversation turns reached'
            }

        except Exception as e:
            return {
                'response': f"Error processing message: {str(e)}",
                'tools_used': [],
                'success': False,
                'error': str(e)
            }

    def _execute_tool(self, tool_name: str, tool_input: Dict) -> Dict:
        """
        Execute a tool function.

        Args:
            tool_name (str): Tool function name
            tool_input (dict): Tool parameters

        Returns:
            dict: Tool execution result
        """
        try:
            if tool_name not in TOOL_FUNCTIONS:
                return {
                    'success': False,
                    'error': f"Unknown tool: {tool_name}"
                }

            tool_function = TOOL_FUNCTIONS[tool_name]
            result = tool_function(**tool_input)

            return result

        except Exception as e:
            return {
                'success': False,
                'error': f"Tool execution error: {str(e)}"
            }

    def _extract_text_response(self, content_blocks: List) -> str:
        """
        Extract text response from Claude's content blocks.

        Args:
            content_blocks (list): Claude response content blocks

        Returns:
            str: Extracted text
        """
        text_parts = []

        for block in content_blocks:
            if hasattr(block, 'type') and block.type == "text":
                text_parts.append(block.text)

        return '\n'.join(text_parts)

    def reset_conversation(self):
        """Reset conversation history."""
        self.conversation_history = []


def create_orchestrator(
    api_key: str,
    odoo_url: str,
    odoo_db: str,
    odoo_username: str,
    odoo_password: str
) -> ClaudeOrchestrator:
    """
    Factory function to create a Claude orchestrator.

    Args:
        api_key (str): Anthropic API key
        odoo_url (str): Odoo server URL
        odoo_db (str): Odoo database name
        odoo_username (str): Odoo user login
        odoo_password (str): Odoo user password

    Returns:
        ClaudeOrchestrator: Configured orchestrator instance
    """
    return ClaudeOrchestrator(
        api_key=api_key,
        odoo_url=odoo_url,
        odoo_db=odoo_db,
        odoo_username=odoo_username,
        odoo_password=odoo_password
    )
