# -*- coding: utf-8 -*-
"""
Odoo Web API Client
===================
Secure client for interacting with Odoo using JSON-RPC API.
No direct database access, respects user permissions.
"""

import xmlrpc.client
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class OdooAPIClient:
    """Client for Odoo JSON-RPC Web API with authentication."""

    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Initialize Odoo API client.

        Args:
            url (str): Odoo server URL (e.g., 'http://localhost:8069')
            db (str): Database name
            username (str): User login
            password (str): User password
        """
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self._common = None
        self._models = None

    def authenticate(self) -> bool:
        """
        Authenticate user and get UID.

        Returns:
            bool: True if authentication successful

        Raises:
            Exception: If authentication fails
        """
        try:
            self._common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = self._common.authenticate(
                self.db,
                self.username,
                self.password,
                {}
            )

            if not self.uid:
                raise Exception(f"Authentication failed for user: {self.username}")

            self._models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            return True

        except Exception as e:
            raise Exception(f"Odoo API authentication error: {str(e)}")

    def execute_kw(self, model: str, method: str, args: List = None, kwargs: Dict = None) -> Any:
        """
        Execute Odoo model method via API.

        Args:
            model (str): Odoo model name (e.g., 'sale.order')
            method (str): Method name (e.g., 'search_read')
            args (list): Positional arguments
            kwargs (dict): Keyword arguments

        Returns:
            Any: Method result

        Raises:
            Exception: If execution fails or user lacks permissions
        """
        if not self.uid:
            self.authenticate()

        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        try:
            result = self._models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model,
                method,
                args,
                kwargs
            )
            return result

        except xmlrpc.client.Fault as e:
            # Permission error handling
            if 'AccessError' in str(e):
                raise PermissionError(
                    f"User '{self.username}' lacks permission to {method} on {model}"
                )
            raise Exception(f"Odoo API error: {str(e)}")

    def search(self, model: str, domain: List, limit: Optional[int] = None) -> List[int]:
        """
        Search for record IDs.

        Args:
            model (str): Model name
            domain (list): Search domain
            limit (int, optional): Max records

        Returns:
            list[int]: Record IDs
        """
        kwargs = {}
        if limit:
            kwargs['limit'] = limit

        return self.execute_kw(model, 'search', [domain], kwargs)

    def read(self, model: str, ids: List[int], fields: List[str]) -> List[Dict]:
        """
        Read record data.

        Args:
            model (str): Model name
            ids (list[int]): Record IDs
            fields (list[str]): Fields to read

        Returns:
            list[dict]: Record data
        """
        return self.execute_kw(model, 'read', [ids], {'fields': fields})

    def search_read(
        self,
        model: str,
        domain: List,
        fields: List[str],
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[Dict]:
        """
        Search and read records in one call.

        Args:
            model (str): Model name
            domain (list): Search domain
            fields (list[str]): Fields to read
            limit (int, optional): Max records
            order (str, optional): Sort order

        Returns:
            list[dict]: Record data
        """
        kwargs = {'fields': fields}
        if limit:
            kwargs['limit'] = limit
        if order:
            kwargs['order'] = order

        return self.execute_kw(model, 'search_read', [domain], kwargs)

    def create(self, model: str, values: Dict) -> int:
        """
        Create a new record.

        Args:
            model (str): Model name
            values (dict): Field values

        Returns:
            int: New record ID
        """
        return self.execute_kw(model, 'create', [[values]])

    def write(self, model: str, ids: List[int], values: Dict) -> bool:
        """
        Update records.

        Args:
            model (str): Model name
            ids (list[int]): Record IDs
            values (dict): Field values

        Returns:
            bool: True if successful
        """
        return self.execute_kw(model, 'write', [ids, values])

    def unlink(self, model: str, ids: List[int]) -> bool:
        """
        Delete records.

        Args:
            model (str): Model name
            ids (list[int]): Record IDs

        Returns:
            bool: True if successful
        """
        return self.execute_kw(model, 'unlink', [ids])

    def fields_get(self, model: str, fields: Optional[List[str]] = None) -> Dict:
        """
        Get model field definitions.

        Args:
            model (str): Model name
            fields (list[str], optional): Specific fields

        Returns:
            dict: Field definitions
        """
        args = []
        if fields:
            args = [fields]

        return self.execute_kw(model, 'fields_get', args)

    def check_access_rights(self, model: str, operation: str) -> bool:
        """
        Check if user has access rights for operation.

        Args:
            model (str): Model name
            operation (str): Operation ('read', 'write', 'create', 'unlink')

        Returns:
            bool: True if user has access
        """
        try:
            return self.execute_kw(
                model,
                'check_access_rights',
                [operation],
                {'raise_exception': False}
            )
        except:
            return False
