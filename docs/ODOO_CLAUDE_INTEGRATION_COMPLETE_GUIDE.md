# Guía Completa: Integración de Claude AI con Odoo 18.2

**Documentación Paso a Paso para Crear un Módulo de IA desde Cero**

---

## 📑 Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Conceptos Fundamentales](#2-conceptos-fundamentales)
3. [Arquitectura del Sistema](#3-arquitectura-del-sistema)
4. [Requisitos y Preparación](#4-requisitos-y-preparación)
5. [Creación del Módulo Paso a Paso](#5-creación-del-módulo-paso-a-paso)
6. [Componentes Detallados](#6-componentes-detallados)
7. [Integración con Claude API](#7-integración-con-claude-api)
8. [Testing y Debugging](#8-testing-y-debugging)
9. [Resolución de Problemas Comunes](#9-resolución-de-problemas-comunes)
10. [Mejores Prácticas](#10-mejores-prácticas)
11. [Extensión y Personalización](#11-extensión-y-personalización)

---

## 1. Introducción

### 1.1 ¿Qué es este proyecto?

Este proyecto integra **Claude AI** (de Anthropic) con **Odoo 18.2** para crear un asistente inteligente que puede ejecutar operaciones de ERP mediante lenguaje natural.

**Ejemplo de uso:**
```
Usuario: "Genera un reporte de ventas por producto del último trimestre"
Claude: [Llama a la herramienta generate_sales_report]
Sistema: [Ejecuta consulta a Odoo vía API]
Claude: "Aquí están tus ventas del último trimestre..."
```

### 1.2 ¿Por qué este enfoque?

**Decisiones de arquitectura clave:**

1. **API-Only (Sin ORM)**:
   - ✅ Respeta permisos de usuario
   - ✅ Funciona sin acceso directo a BD
   - ✅ Portable y seguro
   - ❌ Más verboso que usar ORM

2. **Tool Calling de Claude**:
   - ✅ LLM decide qué herramienta usar
   - ✅ Convierte lenguaje natural a parámetros
   - ✅ Multi-step reasoning
   - ❌ Requiere API key de Anthropic (de pago)

3. **Módulo Odoo Nativo**:
   - ✅ Integración total con UI
   - ✅ Usa sistema de permisos de Odoo
   - ✅ Fácil de instalar/desinstalar
   - ❌ Requiere reinicio de Odoo

---

## 2. Conceptos Fundamentales

### 2.1 Odoo JSON-RPC Web API

Odoo expone una API XML-RPC que permite ejecutar métodos de modelos sin acceso directo a la base de datos.

**Flujo de autenticación:**
```python
import xmlrpc.client

# 1. Conectar al servicio común
common = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/common')

# 2. Autenticar
uid = common.authenticate('database', 'username', 'password', {})

# 3. Conectar al servicio de modelos
models = xmlrpc.client.ServerProxy('http://localhost:8069/xmlrpc/2/object')

# 4. Ejecutar métodos
result = models.execute_kw(
    'database',           # DB name
    uid,                  # User ID
    'password',           # Password
    'sale.order',         # Model
    'search_read',        # Method
    [[]],                 # Domain (search criteria)
    {'fields': ['name', 'partner_id', 'amount_total']}  # Options
)
```

**Métodos disponibles:**
- `search`: Buscar IDs de registros
- `read`: Leer campos de registros
- `search_read`: Buscar y leer en una llamada
- `create`: Crear nuevos registros
- `write`: Actualizar registros
- `unlink`: Eliminar registros
- `check_access_rights`: Verificar permisos

### 2.2 Claude Tool Calling

Claude puede invocar herramientas (funciones) basándose en conversaciones en lenguaje natural.

**Definición de herramienta:**
```python
SALES_REPORT_TOOL = {
    "name": "generate_sales_report",
    "description": "Generate sales reports from Odoo based on natural language",
    "input_schema": {
        "type": "object",
        "properties": {
            "date_from": {
                "type": "string",
                "description": "Start date in YYYY-MM-DD format"
            },
            "date_to": {
                "type": "string",
                "description": "End date in YYYY-MM-DD format"
            },
            "group_by": {
                "type": "string",
                "enum": ["product", "customer", "salesperson"],
                "description": "How to group the report"
            }
        },
        "required": ["url", "db", "username", "password"]
    }
}
```

**Uso con Claude:**
```python
from anthropic import Anthropic

client = Anthropic(api_key="sk-ant-...")

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    tools=[SALES_REPORT_TOOL],  # Lista de herramientas
    messages=[
        {"role": "user", "content": "Show me sales by product from Jan to March"}
    ]
)

# Claude decidirá llamar a generate_sales_report con parámetros apropiados
```

### 2.3 Estructura de Módulos Odoo

Un módulo Odoo tiene esta estructura mínima:

```
odoo_ai_tools/
├── __init__.py                 # Importa submódulos
├── __manifest__.py             # Metadatos del módulo
├── models/                     # Modelos de datos (Python)
│   ├── __init__.py
│   └── ai_assistant.py
├── views/                      # Vistas XML (UI)
│   └── ai_assistant_views.xml
├── security/                   # Permisos de acceso
│   └── ir.model.access.csv
├── controllers/                # Controladores HTTP (opcional)
│   ├── __init__.py
│   └── main.py
└── tools/                      # Lógica de negocio (custom)
    ├── __init__.py
    ├── odoo_api_client.py
    └── sales_reports.py
```

---

## 3. Arquitectura del Sistema

### 3.1 Diagrama de Flujo

```
┌─────────────┐
│   Usuario   │ "Genera reporte de ventas"
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│  Odoo UI (Form)      │ ai.assistant model
│  - user_message      │
│  - anthropic_api_key │
└──────┬───────────────┘
       │ action_send_message()
       ▼
┌──────────────────────────┐
│  ClaudeOrchestrator      │
│  - process_message()     │
│  - Conversation history  │
└──────┬───────────────────┘
       │ Claude API request
       ▼
┌──────────────────────────┐
│  Anthropic Claude API    │
│  - Analiza lenguaje      │
│  - Decide herramienta    │
│  - Extrae parámetros     │
└──────┬───────────────────┘
       │ Tool use: generate_sales_report
       ▼
┌──────────────────────────┐
│  Tool Function           │
│  - generate_sales_report │
└──────┬───────────────────┘
       │ API calls
       ▼
┌──────────────────────────┐
│  OdooAPIClient           │
│  - authenticate()        │
│  - execute_kw()          │
│  - check_access_rights() │
└──────┬───────────────────┘
       │ XML-RPC
       ▼
┌──────────────────────────┐
│  Odoo Server             │
│  - sale.order model      │
│  - account.move model    │
│  - product.product model │
└──────────────────────────┘
```

### 3.2 Componentes del Sistema

| Componente | Responsabilidad | Tecnología |
|------------|----------------|------------|
| UI (Views) | Interfaz de usuario | XML (Odoo views) |
| Model (ai.assistant) | Persistencia de conversaciones | Python (Odoo ORM) |
| Orchestrator | Manejo de conversaciones con Claude | Python + Anthropic SDK |
| Tools | Lógica de negocio específica | Python |
| API Client | Comunicación con Odoo | Python + xmlrpc.client |
| Odoo Server | Backend ERP | Odoo 18.2 |

---

## 4. Requisitos y Preparación

### 4.1 Requisitos del Sistema

**Software necesario:**
```bash
# Sistema operativo
- Linux (Fedora 42, Ubuntu 22.04, etc.)
- macOS
- Windows con WSL2

# Python
- Python 3.12+ (NO usar 3.13, incompatible con Odoo 18)

# PostgreSQL
- PostgreSQL 14+

# Odoo
- Odoo 18.2 (Community o Enterprise)

# Dependencias Python
- anthropic (Anthropic Python SDK)
- xmlrpc (incluido en Python estándar)
```

### 4.2 Configuración del Entorno

**Paso 1: Instalar Odoo 18.2**

```bash
# Crear directorio del proyecto
mkdir -p ~/odoo-18
cd ~/odoo-18

# Clonar Odoo Community
git clone --depth 1 --branch 18.0 https://github.com/odoo/odoo.git

# Crear virtualenv
python3.12 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r odoo/requirements.txt

# Instalar Anthropic SDK
pip install anthropic
```

**Paso 2: Configurar PostgreSQL**

```bash
# Instalar PostgreSQL
sudo dnf install postgresql-server postgresql-contrib  # Fedora
# sudo apt install postgresql postgresql-contrib      # Ubuntu

# Inicializar
sudo postgresql-setup --initdb

# Configurar autenticación (cambiar a 'trust' para desarrollo)
sudo nano /var/lib/pgsql/data/pg_hba.conf

# Cambiar líneas de 'ident' a 'trust':
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust

# Reiniciar
sudo systemctl restart postgresql

# Crear usuario y base de datos
sudo -u postgres createuser -s $USER
createdb odoo18_2
```

**Paso 3: Configurar Odoo**

```bash
# Crear directorio de configuración
mkdir -p ~/odoo-18/config

# Crear archivo de configuración
cat > ~/odoo-18/config/odoo.conf << EOF
[options]
addons_path = /home/$USER/odoo-18/odoo/addons,/home/$USER/odoo-18/enterprise,/home/$USER/odoo-18/custom-addons
admin_passwd = admin
db_host = localhost
db_port = 5432
db_user = $USER
db_password = False
logfile = /home/$USER/odoo-18/logs/odoo.log
log_level = info
EOF

# Crear directorio de logs
mkdir -p ~/odoo-18/logs
```

**Paso 4: Iniciar Odoo**

```bash
cd ~/odoo-18/odoo
source ../venv/bin/activate

# Primera vez: crear base de datos
./odoo-bin -c ../config/odoo.conf -d odoo18_2 -i base --stop-after-init

# Iniciar normalmente
./odoo-bin -c ../config/odoo.conf -d odoo18_2
```

Acceder a: http://localhost:8069

---

## 5. Creación del Módulo Paso a Paso

### 5.1 Paso 1: Crear Estructura del Módulo

```bash
cd ~/odoo-18
mkdir -p custom-addons/odoo_ai_tools/{models,views,security,controllers,tools}
cd custom-addons/odoo_ai_tools
```

### 5.2 Paso 2: Crear __manifest__.py

**Archivo:** `__manifest__.py`

```python
# -*- coding: utf-8 -*-
{
    'name': 'Odoo AI Tools - Claude Integration',
    'version': 'saas~18.2.1.0.0',  # IMPORTANTE: Debe coincidir con versión de Odoo
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
        'base',      # Módulo base de Odoo
        'sale',      # Ventas
        'account',   # Contabilidad
        'stock',     # Inventario
    ],
    'external_dependencies': {
        'python': ['anthropic'],  # Dependencia externa
    },
    'data': [
        'security/ir.model.access.csv',
        'views/ai_assistant_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,  # Aparece como aplicación en Apps
    'auto_install': False,
}
```

**Conceptos clave:**

- **version**: DEBE empezar con la serie de Odoo (ej: `saas~18.2` para Odoo SaaS 18.2)
- **depends**: Lista de módulos requeridos
- **external_dependencies**: Paquetes Python necesarios
- **data**: Archivos XML/CSV a cargar (en orden)
- **application**: True = aparece como app independiente

### 5.3 Paso 3: Crear __init__.py (Raíz)

**Archivo:** `__init__.py`

```python
# -*- coding: utf-8 -*-
from . import models
from . import controllers
# NO importar tools/ aquí (no es un submódulo de Odoo)
```

### 5.4 Paso 4: Crear Cliente API de Odoo

**Archivo:** `tools/odoo_api_client.py`

```python
# -*- coding: utf-8 -*-
"""
Odoo API Client
===============
Cliente para interactuar con Odoo vía JSON-RPC Web API.
NO usa ORM, solo llamadas API externas.
"""

import xmlrpc.client
from typing import Any, Dict, List, Optional


class OdooAPIClient:
    """Cliente para Odoo Web API usando XML-RPC."""

    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Inicializar cliente API.

        Args:
            url: URL del servidor Odoo (ej: http://localhost:8069)
            db: Nombre de la base de datos
            username: Usuario de Odoo (login)
            password: Contraseña del usuario
        """
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None  # User ID, se obtiene en authenticate()
        self._common = None
        self._models = None

    def authenticate(self) -> bool:
        """
        Autenticar con Odoo y obtener UID.

        Returns:
            bool: True si autenticación exitosa

        Raises:
            Exception: Si autenticación falla
        """
        try:
            # Conectar al servicio común (autenticación)
            self._common = xmlrpc.client.ServerProxy(
                f'{self.url}/xmlrpc/2/common'
            )

            # Obtener UID
            self.uid = self._common.authenticate(
                self.db,
                self.username,
                self.password,
                {}  # user_agent_env (opcional)
            )

            if not self.uid:
                raise Exception("Authentication failed: Invalid credentials")

            # Conectar al servicio de objetos (modelos)
            self._models = xmlrpc.client.ServerProxy(
                f'{self.url}/xmlrpc/2/object'
            )

            return True

        except Exception as e:
            raise Exception(f"Odoo API authentication error: {e}") from e

    def execute_kw(
        self,
        model: str,
        method: str,
        args: List,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        Ejecutar método de modelo vía API.

        Args:
            model: Nombre del modelo (ej: 'sale.order')
            method: Método a ejecutar (ej: 'search_read')
            args: Argumentos posicionales
            kwargs: Argumentos nombrados

        Returns:
            Resultado del método

        Example:
            >>> client.execute_kw(
            ...     'sale.order',
            ...     'search_read',
            ...     [[]],
            ...     {'fields': ['name', 'amount_total'], 'limit': 10}
            ... )
        """
        if not self.uid or not self._models:
            raise Exception("Not authenticated. Call authenticate() first.")

        try:
            return self._models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model,
                method,
                args,
                kwargs or {}
            )
        except Exception as e:
            raise Exception(f"Odoo API error: {e}") from e

    def search_read(
        self,
        model: str,
        domain: List,
        fields: List[str],
        limit: Optional[int] = None,
        offset: int = 0,
        order: str = 'id desc'
    ) -> List[Dict]:
        """
        Buscar y leer registros.

        Args:
            model: Nombre del modelo
            domain: Dominio de búsqueda (lista de tuplas)
            fields: Campos a leer
            limit: Número máximo de registros
            offset: Desplazamiento (paginación)
            order: Ordenamiento

        Returns:
            Lista de diccionarios con los registros

        Example:
            >>> client.search_read(
            ...     'sale.order',
            ...     [('state', '=', 'sale')],
            ...     ['name', 'partner_id', 'amount_total'],
            ...     limit=5
            ... )
        """
        kwargs = {
            'fields': fields,
            'offset': offset,
            'order': order
        }
        if limit:
            kwargs['limit'] = limit

        return self.execute_kw(model, 'search_read', [domain], kwargs)

    def create(self, model: str, values: Dict) -> int:
        """
        Crear un nuevo registro.

        Args:
            model: Nombre del modelo
            values: Diccionario con valores del registro

        Returns:
            ID del registro creado

        Example:
            >>> client.create('res.partner', {
            ...     'name': 'Test Company',
            ...     'email': 'test@example.com'
            ... })
        """
        return self.execute_kw(model, 'create', [values])

    def write(self, model: str, ids: List[int], values: Dict) -> bool:
        """
        Actualizar registros existentes.

        Args:
            model: Nombre del modelo
            ids: Lista de IDs a actualizar
            values: Diccionario con valores a actualizar

        Returns:
            True si actualización exitosa
        """
        return self.execute_kw(model, 'write', [ids, values])

    def unlink(self, model: str, ids: List[int]) -> bool:
        """
        Eliminar registros.

        Args:
            model: Nombre del modelo
            ids: Lista de IDs a eliminar

        Returns:
            True si eliminación exitosa
        """
        return self.execute_kw(model, 'unlink', [ids])

    def check_access_rights(
        self,
        model: str,
        operation: str,
        raise_exception: bool = False
    ) -> bool:
        """
        Verificar si el usuario tiene permisos.

        Args:
            model: Nombre del modelo
            operation: Operación ('read', 'write', 'create', 'unlink')
            raise_exception: Si lanzar excepción en caso de no tener permiso

        Returns:
            True si tiene permiso, False si no

        Example:
            >>> if client.check_access_rights('sale.order', 'read'):
            ...     # Proceder con lectura
        """
        return self.execute_kw(
            model,
            'check_access_rights',
            [operation],
            {'raise_exception': raise_exception}
        )
```

**Conceptos clave:**

- **xmlrpc.client**: Librería estándar de Python para XML-RPC
- **execute_kw**: Método universal para ejecutar cualquier método de modelo
- **check_access_rights**: CRÍTICO para respetar permisos de usuario
- **Manejo de errores**: Capturar excepciones y dar mensajes claros

### 5.5 Paso 5: Crear Herramienta de Ejemplo (Sales Reports)

**Archivo:** `tools/sales_reports.py`

```python
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
        -> Claude calls this with:
           date_from='2025-03-01', date_to='2025-07-31', group_by='product'
    """
    try:
        # 1. Autenticar con Odoo
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        # 2. Verificar permisos de lectura
        if not client.check_access_rights('sale.order', 'read'):
            return {
                'success': False,
                'data': None,
                'summary': None,
                'error': f"User '{username}' lacks read permission on sales orders"
            }

        # 3. Construir dominio de búsqueda
        domain = [('state', '=', 'sale')]  # Solo órdenes confirmadas

        if date_from:
            domain.append(('date_order', '>=', date_from))
        if date_to:
            domain.append(('date_order', '<=', date_to))
        if partner_ids:
            domain.append(('partner_id', 'in', partner_ids))

        # 4. Obtener órdenes de venta
        orders = client.search_read(
            'sale.order',
            domain,
            ['name', 'partner_id', 'user_id', 'date_order', 'amount_total']
        )

        if not orders:
            return {
                'success': True,
                'data': [],
                'summary': {'total_orders': 0, 'total_amount': 0.0},
                'error': None
            }

        # 5. Obtener líneas de orden para detalle por producto
        order_ids = [o['id'] for o in orders]
        lines = client.search_read(
            'sale.order.line',
            [('order_id', 'in', order_ids)],
            ['order_id', 'product_id', 'product_uom_qty', 'price_subtotal']
        )

        # 6. Agrupar datos según group_by
        grouped_data = {}

        if group_by == 'product':
            for line in lines:
                product_id = line['product_id'][0] if line['product_id'] else None
                product_name = line['product_id'][1] if line['product_id'] else 'Sin Producto'

                if product_name not in grouped_data:
                    grouped_data[product_name] = {
                        'name': product_name,
                        'quantity': 0.0,
                        'total_amount': 0.0
                    }

                grouped_data[product_name]['quantity'] += line.get('product_uom_qty', 0)
                grouped_data[product_name]['total_amount'] += line.get('price_subtotal', 0)

        elif group_by == 'customer':
            for order in orders:
                partner_name = order['partner_id'][1] if order['partner_id'] else 'Sin Cliente'

                if partner_name not in grouped_data:
                    grouped_data[partner_name] = {
                        'name': partner_name,
                        'order_count': 0,
                        'total_amount': 0.0
                    }

                grouped_data[partner_name]['order_count'] += 1
                grouped_data[partner_name]['total_amount'] += order.get('amount_total', 0)

        elif group_by == 'salesperson':
            for order in orders:
                user_name = order['user_id'][1] if order['user_id'] else 'Sin Vendedor'

                if user_name not in grouped_data:
                    grouped_data[user_name] = {
                        'name': user_name,
                        'order_count': 0,
                        'total_amount': 0.0
                    }

                grouped_data[user_name]['order_count'] += 1
                grouped_data[user_name]['total_amount'] += order.get('amount_total', 0)

        # 7. Ordenar por monto total descendente
        result_data = sorted(
            grouped_data.values(),
            key=lambda x: x['total_amount'],
            reverse=True
        )

        # 8. Calcular resumen
        summary = {
            'total_amount': sum(item['total_amount'] for item in result_data),
            'group_by': group_by,
            'date_from': date_from,
            'date_to': date_to
        }

        return {
            'success': True,
            'data': result_data,
            'summary': summary,
            'error': None
        }

    except Exception as e:
        return {
            'success': False,
            'data': None,
            'summary': None,
            'error': str(e)
        }


# Definición de la herramienta para Claude
SALES_REPORT_TOOL = {
    "name": "generate_sales_report",
    "description": """Generate sales reports from Odoo based on natural language parameters.

    This tool analyzes sales orders and can group results by:
    - Product: See which products are selling best
    - Customer: Identify top customers
    - Salesperson: Analyze sales team performance

    Supports date filtering and specific product/customer filtering.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Odoo server URL (e.g., http://localhost:8069)"
            },
            "db": {
                "type": "string",
                "description": "Database name"
            },
            "username": {
                "type": "string",
                "description": "Odoo username"
            },
            "password": {
                "type": "string",
                "description": "Odoo password"
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
                "description": "How to group the sales report",
                "default": "product"
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
```

**Conceptos clave:**

- **Función como herramienta**: Recibe credenciales + parámetros de negocio
- **Retorno estandarizado**: Siempre `{success, data, summary, error}`
- **Verificación de permisos**: ANTES de ejecutar operaciones
- **Manejo de errores**: Try-catch para retornar errores controlados
- **Schema de Claude**: Define exactamente qué parámetros puede usar Claude

### 5.6 Paso 6: Crear Orquestador de Claude

**Archivo:** `tools/claude_orchestrator.py`

```python
# -*- coding: utf-8 -*-
"""
Claude Orchestrator
===================
Manages conversations with Claude AI and tool execution.
"""

import json
from typing import Dict, List
from anthropic import Anthropic

# Importar herramientas (sin importación relativa para evitar problemas)
# En producción, se importarían correctamente
from sales_reports import generate_sales_report, SALES_REPORT_TOOL
# ... otras herramientas


# Registro de herramientas disponibles
TOOL_FUNCTIONS = {
    'generate_sales_report': generate_sales_report,
    # Agregar más herramientas aquí
}

ALL_TOOLS = [
    SALES_REPORT_TOOL,
    # Agregar más definiciones aquí
]


class ClaudeOrchestrator:
    """Orquestador para conversaciones con Claude AI."""

    def __init__(
        self,
        api_key: str,
        odoo_url: str,
        odoo_db: str,
        odoo_username: str,
        odoo_password: str,
        model: str = "claude-3-5-sonnet-20241022"
    ):
        """
        Inicializar orquestador.

        Args:
            api_key: Anthropic API key
            odoo_url: URL del servidor Odoo
            odoo_db: Nombre de la base de datos
            odoo_username: Usuario de Odoo
            odoo_password: Contraseña de Odoo
            model: Modelo de Claude a usar
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.conversation_history = []

        # Credenciales de Odoo (se inyectan en llamadas a herramientas)
        self.odoo_credentials = {
            'url': odoo_url,
            'db': odoo_db,
            'username': odoo_username,
            'password': odoo_password
        }

    def process_message(self, user_message: str, max_turns: int = 5) -> Dict:
        """
        Procesar mensaje del usuario y ejecutar herramientas si es necesario.

        Args:
            user_message: Mensaje del usuario
            max_turns: Máximo número de turnos de conversación

        Returns:
            dict: {
                'response': str,
                'tools_used': list[str],
                'success': bool,
                'error': str or None
            }
        """
        # Agregar mensaje del usuario al historial
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        tools_used = []

        try:
            for turn in range(max_turns):
                # Llamar a Claude con el historial y herramientas
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    tools=ALL_TOOLS,
                    messages=self.conversation_history
                )

                # Analizar respuesta
                if response.stop_reason == "end_turn":
                    # Claude terminó sin usar herramientas
                    final_text = self._extract_text(response.content)
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    return {
                        'response': final_text,
                        'tools_used': tools_used,
                        'success': True,
                        'error': None
                    }

                elif response.stop_reason == "tool_use":
                    # Claude quiere usar herramientas
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response.content
                    })

                    # Ejecutar herramientas solicitadas
                    tool_results = []
                    for content_block in response.content:
                        if content_block.type == "tool_use":
                            tool_name = content_block.name
                            tool_input = content_block.input
                            tool_use_id = content_block.id

                            tools_used.append(tool_name)

                            # Inyectar credenciales de Odoo
                            tool_input.update(self.odoo_credentials)

                            # Ejecutar herramienta
                            tool_result = self._execute_tool(tool_name, tool_input)

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": json.dumps(tool_result)
                            })

                    # Agregar resultados al historial
                    self.conversation_history.append({
                        "role": "user",
                        "content": tool_results
                    })

                else:
                    # Otro stop_reason
                    raise Exception(f"Unexpected stop_reason: {response.stop_reason}")

            # Si llegamos aquí, alcanzamos max_turns
            return {
                'response': "Conversation exceeded maximum turns.",
                'tools_used': tools_used,
                'success': False,
                'error': "Max turns exceeded"
            }

        except Exception as e:
            return {
                'response': f"Error: {str(e)}",
                'tools_used': tools_used,
                'success': False,
                'error': str(e)
            }

    def _execute_tool(self, tool_name: str, tool_input: Dict) -> Dict:
        """
        Ejecutar una herramienta.

        Args:
            tool_name: Nombre de la herramienta
            tool_input: Parámetros de entrada

        Returns:
            Resultado de la herramienta
        """
        if tool_name not in TOOL_FUNCTIONS:
            return {
                'success': False,
                'error': f"Unknown tool: {tool_name}"
            }

        tool_function = TOOL_FUNCTIONS[tool_name]

        try:
            result = tool_function(**tool_input)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': f"Tool execution error: {str(e)}"
            }

    def _extract_text(self, content: List) -> str:
        """Extraer texto de la respuesta de Claude."""
        texts = []
        for block in content:
            if hasattr(block, 'text'):
                texts.append(block.text)
        return '\n'.join(texts)


# Función helper para crear orquestador desde configuración
def create_orchestrator(
    api_key: str,
    odoo_url: str,
    odoo_db: str,
    odoo_username: str,
    odoo_password: str
) -> ClaudeOrchestrator:
    """
    Crear instancia de orquestador.

    Example:
        >>> orchestrator = create_orchestrator(
        ...     api_key="sk-ant-...",
        ...     odoo_url="http://localhost:8069",
        ...     odoo_db="odoo18_2",
        ...     odoo_username="admin",
        ...     odoo_password="admin"
        ... )
        >>> result = orchestrator.process_message(
        ...     "Show me sales by product this month"
        ... )
    """
    return ClaudeOrchestrator(
        api_key=api_key,
        odoo_url=odoo_url,
        odoo_db=odoo_db,
        odoo_username=odoo_username,
        odoo_password=odoo_password
    )
```

**Conceptos clave:**

- **Historial de conversación**: Claude mantiene contexto entre mensajes
- **Loop de tool use**: Claude puede usar múltiples herramientas en secuencia
- **Inyección de credenciales**: Las credenciales de Odoo se agregan automáticamente
- **Stop reasons**: `end_turn` (terminó) vs `tool_use` (quiere herramienta)

---

## 6. Componentes Detallados

### 6.1 Modelos Odoo (ORM)

**Archivo:** `models/__init__.py`

```python
# -*- coding: utf-8 -*-
from . import ai_assistant
```

**Archivo:** `models/ai_assistant.py`

```python
# -*- coding: utf-8 -*-
"""
AI Assistant Models
===================
Modelos de Odoo para gestionar conversaciones con Claude AI.
"""

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AIAssistant(models.Model):
    """Modelo para conversaciones con Claude AI."""

    _name = 'ai.assistant'
    _description = 'AI Assistant Conversation'
    _order = 'create_date desc'

    # Campos básicos
    name = fields.Char(
        string='Conversation Title',
        required=True,
        default='New Conversation'
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        readonly=True
    )

    # Mensaje del usuario
    user_message = fields.Text(
        string='Your Message',
        required=True,
        help='Ask Claude to help with Odoo tasks'
    )

    # Respuesta del asistente
    assistant_response = fields.Text(
        string='Assistant Response',
        readonly=True
    )

    # Herramientas usadas
    tools_used = fields.Text(
        string='Tools Used',
        readonly=True,
        help='List of tools Claude used to answer'
    )

    # Estado
    success = fields.Boolean(
        string='Success',
        readonly=True,
        default=False
    )
    error_message = fields.Text(
        string='Error Message',
        readonly=True
    )

    # Configuración
    anthropic_api_key = fields.Char(
        string='Anthropic API Key',
        help='Your Anthropic API key (starts with sk-ant-...)'
    )

    @api.model
    def action_send_message(self):
        """
        Enviar mensaje a Claude y procesar respuesta.

        Este método se llama cuando el usuario hace clic en el botón
        'Send to Claude' en la vista de formulario.
        """
        for record in self:
            try:
                # Importar aquí para evitar problemas de importación circular
                import sys
                import os
                tools_path = os.path.join(
                    os.path.dirname(__file__), '..', 'tools'
                )
                sys.path.insert(0, tools_path)

                from claude_orchestrator import create_orchestrator

                # Obtener credenciales de Odoo
                # Nota: En producción, el password debería venir de configuración
                odoo_url = self.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url',
                    default='http://localhost:8069'
                )
                odoo_db = self.env.cr.dbname
                odoo_user = self.env.user.login

                # IMPORTANTE: En producción, el password debe manejarse de forma segura
                # Aquí usamos un campo de configuración
                config = self.env['ai.assistant.config'].search([], limit=1)
                if config and config.user_password:
                    odoo_password = config.user_password
                else:
                    # Fallback: solicitar al usuario que configure
                    record.write({
                        'success': False,
                        'error_message': 'Please configure Odoo password in AI Assistant → Configuration'
                    })
                    continue

                # Verificar API key
                if not record.anthropic_api_key:
                    record.write({
                        'success': False,
                        'error_message': 'Please provide your Anthropic API key'
                    })
                    continue

                # Crear orquestador
                orchestrator = create_orchestrator(
                    api_key=record.anthropic_api_key,
                    odoo_url=odoo_url,
                    odoo_db=odoo_db,
                    odoo_username=odoo_user,
                    odoo_password=odoo_password
                )

                # Procesar mensaje
                result = orchestrator.process_message(record.user_message)

                # Actualizar registro
                tools_used_str = ', '.join(result.get('tools_used', [])) if result.get('tools_used') else 'None'

                record.write({
                    'assistant_response': result.get('response', ''),
                    'tools_used': tools_used_str,
                    'success': result.get('success', False),
                    'error_message': result.get('error', '')
                })

                _logger.info(f"AI Assistant processed message for user {odoo_user}")

            except Exception as e:
                _logger.error(f"Error in AI Assistant: {str(e)}")
                record.write({
                    'success': False,
                    'error_message': str(e)
                })


class AIAssistantConfig(models.TransientModel):
    """Modelo de configuración para AI Assistant."""

    _name = 'ai.assistant.config'
    _description = 'AI Assistant Configuration'

    anthropic_api_key = fields.Char(
        string='Anthropic API Key',
        help='Get your API key from https://console.anthropic.com/'
    )
    user_password = fields.Char(
        string='Odoo Password',
        help='Your Odoo password for API authentication'
    )
    test_message = fields.Text(
        string='Test Message',
        readonly=True
    )

    def action_test_connection(self):
        """Probar conexión con Claude y Odoo."""
        for record in self:
            try:
                import sys
                import os
                tools_path = os.path.join(
                    os.path.dirname(__file__), '..', 'tools'
                )
                sys.path.insert(0, tools_path)

                from odoo_api_client import OdooAPIClient

                # Probar autenticación con Odoo
                client = OdooAPIClient(
                    url=self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                    db=self.env.cr.dbname,
                    username=self.env.user.login,
                    password=record.user_password
                )
                client.authenticate()

                record.write({
                    'test_message': f'✅ Connection successful!\nUser ID: {client.uid}\nYou can now use AI Assistant.'
                })

            except Exception as e:
                record.write({
                    'test_message': f'❌ Connection failed:\n{str(e)}'
                })
```

**Conceptos clave:**

- **_name**: Identificador único del modelo (crea tabla en BD)
- **fields**: Tipos de campos: Char, Text, Boolean, Many2one, etc.
- **@api.model**: Decorador para métodos que trabajan con conjuntos de registros
- **self.env**: Acceso al entorno de Odoo (usuario, BD, configuración)
- **TransientModel**: Modelo temporal (no persiste datos, para wizards)

### 6.2 Vistas XML

**Archivo:** `views/ai_assistant_views.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Vista de Formulario -->
    <record id="view_ai_assistant_form" model="ir.ui.view">
        <field name="name">ai.assistant.form</field>
        <field name="model">ai.assistant</field>
        <field name="arch" type="xml">
            <form string="AI Assistant">
                <header>
                    <!-- Botón para enviar mensaje -->
                    <button name="action_send_message"
                            string="Send to Claude"
                            type="object"
                            class="oe_highlight"
                            invisible="assistant_response"/>
                </header>
                <sheet>
                    <div class="oe_title">
                        <h1>
                            <field name="name" placeholder="Conversation Title"/>
                        </h1>
                    </div>
                    <group>
                        <group>
                            <field name="user_id" readonly="1"/>
                            <field name="create_date" readonly="1"/>
                            <field name="success" invisible="1"/>
                        </group>
                        <group>
                            <field name="anthropic_api_key" password="True"
                                   placeholder="sk-ant-..."/>
                        </group>
                    </group>

                    <!-- Mensaje del usuario -->
                    <group string="Your Message">
                        <field name="user_message" nolabel="1"
                               placeholder="Ask Claude to help with Odoo tasks...&#10;&#10;Examples:&#10;- Generate a sales report by product from March to July&#10;- Create invoices for the last 3 sales&#10;- What expenses can be tax deductible?&#10;- Which quotations need follow-up this week?&#10;- What products should I order before Friday?"
                               widget="text"/>
                    </group>

                    <!-- Respuesta del asistente -->
                    <group string="Assistant Response" invisible="not assistant_response">
                        <field name="assistant_response" nolabel="1"
                               widget="text" readonly="1"/>
                    </group>

                    <!-- Herramientas usadas -->
                    <group string="Tools Used" invisible="not tools_used">
                        <field name="tools_used" nolabel="1"
                               widget="text" readonly="1"/>
                    </group>

                    <!-- Mensajes de error -->
                    <group string="Error" invisible="not error_message">
                        <field name="error_message" nolabel="1"
                               widget="text" readonly="1"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <!-- Vista de Lista (cambió de 'tree' a 'list' en Odoo 18) -->
    <record id="view_ai_assistant_list" model="ir.ui.view">
        <field name="name">ai.assistant.list</field>
        <field name="model">ai.assistant</field>
        <field name="arch" type="xml">
            <list string="AI Conversations">
                <field name="name"/>
                <field name="user_id"/>
                <field name="create_date"/>
                <field name="success"/>
            </list>
        </field>
    </record>

    <!-- Vista de Búsqueda -->
    <record id="view_ai_assistant_search" model="ir.ui.view">
        <field name="name">ai.assistant.search</field>
        <field name="model">ai.assistant</field>
        <field name="arch" type="xml">
            <search string="Search Conversations">
                <field name="name"/>
                <field name="user_message"/>
                <field name="user_id"/>
                <!-- Filtros predefinidos -->
                <filter name="my_conversations" string="My Conversations"
                        domain="[('user_id', '=', uid)]"/>
                <filter name="successful" string="Successful"
                        domain="[('success', '=', True)]"/>
                <filter name="with_errors" string="With Errors"
                        domain="[('error_message', '!=', False)]"/>
                <!-- Agrupación -->
                <group expand="0" string="Group By">
                    <filter name="group_user" string="User"
                            context="{'group_by': 'user_id'}"/>
                    <filter name="group_date" string="Date"
                            context="{'group_by': 'create_date:day'}"/>
                </group>
            </search>
        </field>
    </record>

    <!-- Acción de Ventana -->
    <record id="action_ai_assistant" model="ir.actions.act_window">
        <field name="name">AI Assistant</field>
        <field name="res_model">ai.assistant</field>
        <field name="view_mode">list,form</field>  <!-- Cambió de tree a list -->
        <field name="context">{'search_default_my_conversations': 1}</field>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Start a conversation with Claude AI
            </p>
            <p>
                Ask Claude to help you with Odoo tasks using natural language.
                Claude can generate reports, create invoices, analyze expenses, and more.
            </p>
        </field>
    </record>

    <!-- Menú Principal -->
    <menuitem id="menu_ai_assistant_root"
              name="AI Assistant"
              sequence="100"/>

    <!-- Submenú: Conversaciones -->
    <menuitem id="menu_ai_assistant"
              name="Conversations"
              parent="menu_ai_assistant_root"
              action="action_ai_assistant"
              sequence="10"/>

    <!-- Submenú: Configuración -->
    <menuitem id="menu_ai_assistant_config"
              name="Configuration"
              parent="menu_ai_assistant_root"
              action="action_ai_assistant_config"
              sequence="100"/>
</odoo>
```

**Conceptos clave:**

- **`<list>` en Odoo 18**: Reemplaza `<tree>` de versiones anteriores
- **invisible**: Ocultar campos condicionalmente
- **widget**: Tipo de widget para el campo (text, html, many2one, etc.)
- **password="True"**: Campo de contraseña (oculto)
- **help type="html"**: Mensaje cuando no hay registros

### 6.3 Permisos de Acceso

**Archivo:** `security/ir.model.access.csv`

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_ai_assistant_user,ai.assistant.user,model_ai_assistant,base.group_user,1,1,1,1
access_ai_assistant_config_user,ai.assistant.config.user,model_ai_assistant_config,base.group_user,1,1,1,1
```

**Formato:**
- **id**: ID único del permiso
- **name**: Nombre descriptivo
- **model_id:id**: Referencia al modelo (model_NOMBRE_MODELO)
- **group_id:id**: Grupo de usuarios (base.group_user = todos los usuarios)
- **perm_read/write/create/unlink**: Permisos (1=permitido, 0=negado)

---

## 7. Integración con Claude API

### 7.1 Obtener API Key

1. Ir a https://console.anthropic.com/
2. Crear cuenta o iniciar sesión
3. Navegar a **API Keys**
4. Click en **Create Key**
5. Copiar la clave (empieza con `sk-ant-...`)

### 7.2 Modelos Disponibles

| Modelo | Descripción | Tokens | Costo (por 1M tokens) |
|--------|-------------|--------|----------------------|
| claude-3-5-sonnet-20241022 | Mejor balance calidad/velocidad | 200K | Input: $3, Output: $15 |
| claude-3-opus-20240229 | Máxima calidad | 200K | Input: $15, Output: $75 |
| claude-3-haiku-20240307 | Más rápido y económico | 200K | Input: $0.25, Output: $1.25 |

**Recomendación**: Usar `claude-3-5-sonnet-20241022` (balance ideal)

### 7.3 Ejemplo de Conversación con Tools

```python
from anthropic import Anthropic

client = Anthropic(api_key="sk-ant-...")

# Conversación multi-turn
messages = []

# Usuario: mensaje inicial
messages.append({
    "role": "user",
    "content": "Show me sales by product from January to March"
})

# 1er turno: Claude decide usar herramienta
response1 = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    tools=[SALES_REPORT_TOOL],
    messages=messages
)

# response1.stop_reason == "tool_use"
# response1.content contiene:
# [
#   TextBlock(text="I'll generate that sales report for you."),
#   ToolUseBlock(
#       id="toolu_123",
#       name="generate_sales_report",
#       input={
#           "date_from": "2025-01-01",
#           "date_to": "2025-03-31",
#           "group_by": "product"
#       }
#   )
# ]

# Agregar respuesta de Claude al historial
messages.append({
    "role": "assistant",
    "content": response1.content
})

# Ejecutar herramienta
tool_result = generate_sales_report(
    url="http://localhost:8069",
    db="odoo18_2",
    username="admin",
    password="admin",
    date_from="2025-01-01",
    date_to="2025-03-31",
    group_by="product"
)

# Devolver resultado a Claude
messages.append({
    "role": "user",
    "content": [
        {
            "type": "tool_result",
            "tool_use_id": "toolu_123",
            "content": json.dumps(tool_result)
        }
    ]
})

# 2do turno: Claude procesa resultado y responde
response2 = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    tools=[SALES_REPORT_TOOL],
    messages=messages
)

# response2.stop_reason == "end_turn"
# response2.content contiene:
# [
#   TextBlock(text="Here are your sales by product from January to March:\n\n1. Product A: $10,000\n2. Product B: $8,500\n...")
# ]
```

---

## 8. Testing y Debugging

### 8.1 Testing Manual de Tools

**Script de prueba:** `tools/test_tools.py`

```python
#!/usr/bin/env python3
"""Test individual tools without Claude."""

from sales_reports import generate_sales_report
from datetime import datetime, timedelta

# Configuración
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'odoo18_2'
ODOO_USER = 'admin'
ODOO_PASS = 'admin'

# Calcular fechas
today = datetime.now()
last_month = (today - timedelta(days=30)).strftime('%Y-%m-%d')
today_str = today.strftime('%Y-%m-%d')

print("Testing Sales Report Tool")
print("=" * 60)

result = generate_sales_report(
    url=ODOO_URL,
    db=ODOO_DB,
    username=ODOO_USER,
    password=ODOO_PASS,
    date_from=last_month,
    date_to=today_str,
    group_by='product'
)

if result['success']:
    print("✅ Success!")
    print(f"Total: ${result['summary']['total_amount']:,.2f}")
    print("\nTop 5 products:")
    for i, item in enumerate(result['data'][:5], 1):
        print(f"{i}. {item['name']}: ${item['total_amount']:,.2f}")
else:
    print(f"❌ Error: {result['error']}")
```

Ejecutar:
```bash
cd ~/odoo-18/custom-addons/odoo_ai_tools/tools
python3 test_tools.py
```

### 8.2 Logging y Debugging

**Habilitar logging detallado en Odoo:**

```bash
./odoo-bin -c ../config/odoo.conf -d odoo18_2 --log-level=debug
```

**En el código Python:**

```python
import logging

_logger = logging.getLogger(__name__)

# En funciones:
_logger.info("Starting sales report generation")
_logger.debug(f"Domain: {domain}")
_logger.error(f"Failed to authenticate: {e}")
```

**Ver logs en tiempo real:**

```bash
tail -f ~/odoo-18/logs/odoo.log
```

### 8.3 Debugging con Claude

**Agregar información de debug a respuestas:**

```python
def generate_sales_report(...):
    try:
        # ... código ...

        return {
            'success': True,
            'data': result_data,
            'summary': summary,
            'error': None,
            # DEBUG INFO (remover en producción)
            'debug': {
                'domain': domain,
                'order_count': len(orders),
                'line_count': len(lines)
            }
        }
```

---

## 9. Resolución de Problemas Comunes

### 9.1 Error: "Module has incompatible version"

**Causa**: La versión del módulo no coincide con la serie de Odoo.

**Solución**:

```bash
# 1. Detectar versión de Odoo
cd ~/odoo-18/odoo
source ../venv/bin/activate
python3 -c "from odoo import release; print(release.major_version)"
# Output: saas~18.2

# 2. Actualizar __manifest__.py
'version': 'saas~18.2.1.0.0',  # DEBE empezar con saas~18.2
```

### 9.2 Error: "Invalid view type: 'tree'"

**Causa**: En Odoo 18, `<tree>` fue reemplazado por `<list>`.

**Solución**:

```xml
<!-- ANTES (Odoo 17 y anteriores) -->
<tree string="Lista">
    ...
</tree>

<!-- DESPUÉS (Odoo 18+) -->
<list string="Lista">
    ...
</list>
```

También cambiar en acciones:

```xml
<!-- ANTES -->
<field name="view_mode">tree,form</field>

<!-- DESPUÉS -->
<field name="view_mode">list,form</field>
```

### 9.3 Error: "anthropic package not installed"

**Causa**: El paquete `anthropic` no está instalado en el virtualenv.

**Solución**:

```bash
cd ~/odoo-18/odoo
source ../venv/bin/activate
pip install anthropic
```

### 9.4 Error: "Authentication failed"

**Causa**: Credenciales incorrectas o usuario sin permisos.

**Solución**:

```python
# Verificar credenciales manualmente
from odoo_api_client import OdooAPIClient

client = OdooAPIClient(
    url='http://localhost:8069',
    db='odoo18_2',
    username='admin',
    password='admin'  # Verificar que sea correcto
)

try:
    client.authenticate()
    print(f"✅ Authenticated! UID: {client.uid}")
except Exception as e:
    print(f"❌ Error: {e}")
```

### 9.5 Error: "Permission denied"

**Causa**: Usuario sin permisos para el modelo/operación.

**Solución**:

```python
# Verificar permisos
if not client.check_access_rights('sale.order', 'read'):
    return {
        'success': False,
        'error': f"User '{username}' lacks read permission on sales orders"
    }
```

**Otorgar permisos en Odoo:**
1. Settings → Users & Companies → Users
2. Seleccionar usuario
3. Verificar grupos de acceso (Sales Manager, etc.)

### 9.6 Error: "Invalid field 'qty_available'"

**Causa**: Campo no existe en el modelo o es computado de forma diferente en Odoo 18.

**Solución**:

```python
# Para cantidad disponible en Odoo 18, usar stock.quant
quants = client.search_read(
    'stock.quant',
    [('product_id', '=', product_id)],
    ['quantity', 'location_id']
)

# O usar campo computado correcto
products = client.search_read(
    'product.product',
    [('id', '=', product_id)],
    ['qty_at_date']  # Campo correcto en Odoo 18
)
```

---

## 10. Mejores Prácticas

### 10.1 Seguridad

**1. Nunca hardcodear credenciales:**

```python
# ❌ MAL
password = "admin123"

# ✅ BIEN
password = os.environ.get('ODOO_PASSWORD')
# o usar configuración de Odoo
password = self.env['ir.config_parameter'].sudo().get_param('odoo_ai.password')
```

**2. Validar permisos SIEMPRE:**

```python
# Antes de cualquier operación
if not client.check_access_rights(model, operation):
    return {'success': False, 'error': 'Permission denied'}
```

**3. Sanitizar inputs de usuario:**

```python
# Escapar/validar entradas
date_from = str(date_from)  # Convertir a string
if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_from):
    return {'success': False, 'error': 'Invalid date format'}
```

### 10.2 Performance

**1. Limitar resultados:**

```python
# Siempre usar límites en búsquedas
orders = client.search_read(
    'sale.order',
    domain,
    fields,
    limit=100  # Evitar cargar miles de registros
)
```

**2. Pedir solo campos necesarios:**

```python
# ❌ MAL (trae todos los campos)
orders = client.search_read('sale.order', [], [])

# ✅ BIEN (solo campos necesarios)
orders = client.search_read('sale.order', [], ['name', 'partner_id', 'amount_total'])
```

**3. Usar búsquedas eficientes:**

```python
# ❌ MAL (dos llamadas)
order_ids = client.execute_kw('sale.order', 'search', [[]])
orders = client.execute_kw('sale.order', 'read', [order_ids])

# ✅ BIEN (una llamada)
orders = client.search_read('sale.order', [], fields)
```

### 10.3 Manejo de Errores

**1. Retorno estandarizado:**

```python
def my_tool(...):
    try:
        # ... lógica ...
        return {
            'success': True,
            'data': result,
            'summary': summary,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'summary': None,
            'error': str(e)
        }
```

**2. Errores específicos:**

```python
# Dar contexto en errores
if not orders:
    return {
        'success': True,  # No es error, simplemente no hay datos
        'data': [],
        'summary': {'message': 'No sales orders found for the specified period'},
        'error': None
    }
```

### 10.4 Documentación de Tools

**Descripciones claras para Claude:**

```python
TOOL_DEFINITION = {
    "name": "my_tool",
    "description": """
    [Qué hace]: Generate reports from sales data
    [Cuándo usar]: Use when user asks about sales, revenue, or performance
    [Capacidades]: Can group by product, customer, or time period
    [Limitaciones]: Only shows confirmed sales orders (not quotations)
    """,
    "input_schema": {
        "properties": {
            "date_from": {
                "description": "Start date in YYYY-MM-DD format. Use relative dates like 'last month', 'this quarter'."
            }
        }
    }
}
```

---

## 11. Extensión y Personalización

### 11.1 Agregar Nueva Herramienta

**Paso 1: Crear archivo de herramienta**

```python
# tools/inventory_alerts.py

def check_stock_alerts(url, db, username, password, threshold=10):
    """
    Check products below minimum stock threshold.

    Returns products that need restocking.
    """
    try:
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        # Buscar productos con stock bajo
        products = client.search_read(
            'product.product',
            [('qty_available', '<', threshold)],
            ['name', 'qty_available', 'qty_forecasted']
        )

        return {
            'success': True,
            'data': products,
            'summary': {'count': len(products), 'threshold': threshold},
            'error': None
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


INVENTORY_ALERTS_TOOL = {
    "name": "check_stock_alerts",
    "description": "Check inventory for products below minimum stock",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "db": {"type": "string"},
            "username": {"type": "string"},
            "password": {"type": "string"},
            "threshold": {
                "type": "integer",
                "description": "Minimum stock quantity threshold",
                "default": 10
            }
        },
        "required": ["url", "db", "username", "password"]
    }
}
```

**Paso 2: Registrar en orchestrator**

```python
# tools/claude_orchestrator.py

from inventory_alerts import check_stock_alerts, INVENTORY_ALERTS_TOOL

TOOL_FUNCTIONS['check_stock_alerts'] = check_stock_alerts
ALL_TOOLS.append(INVENTORY_ALERTS_TOOL)
```

**Paso 3: Usar**

```
Usuario: "¿Qué productos tienen poco stock?"
Claude: [Llama a check_stock_alerts con threshold=10]
```

### 11.2 Personalizar Prompts del Sistema

```python
class ClaudeOrchestrator:
    def __init__(self, ..., system_prompt=None):
        self.system_prompt = system_prompt or """
You are an AI assistant integrated with Odoo ERP.

Your role:
- Help users with sales, inventory, and accounting tasks
- Use tools to fetch and analyze data from Odoo
- Provide clear, actionable insights

Guidelines:
- Always verify data before making recommendations
- Respect user permissions (if a tool fails, explain why)
- Format numbers clearly (use currency symbols, thousands separators)
- Be concise but thorough

Example:
User: "Show me top customers"
You: "I'll analyze your customer sales data." [use generate_sales_report]
        """

    def process_message(self, user_message):
        response = self.client.messages.create(
            ...,
            system=self.system_prompt  # Agregar system prompt
        )
```

### 11.3 Multi-idioma

```python
# Detectar idioma del usuario
def detect_language(text):
    # Heurística simple
    if any(word in text.lower() for word in ['ventas', 'productos', 'cliente']):
        return 'es'
    return 'en'

# Prompts por idioma
SYSTEM_PROMPTS = {
    'es': "Eres un asistente de IA integrado con Odoo ERP...",
    'en': "You are an AI assistant integrated with Odoo ERP..."
}

# Usar en orchestrator
lang = detect_language(user_message)
system_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS['en'])
```

### 11.4 Streaming de Respuestas

```python
# Para respuestas en tiempo real
def process_message_stream(self, user_message):
    with self.client.messages.stream(
        model=self.model,
        max_tokens=4096,
        tools=ALL_TOOLS,
        messages=self.conversation_history
    ) as stream:
        for text in stream.text_stream:
            yield text  # Enviar al frontend en tiempo real
```

---

## 12. Recursos Adicionales

### 12.1 Documentación Oficial

- **Odoo API**: https://www.odoo.com/documentation/18.0/developer/reference/external_api.html
- **Anthropic API**: https://docs.anthropic.com/
- **Claude Tool Use**: https://docs.anthropic.com/en/docs/build-with-claude/tool-use

### 12.2 Comunidad

- **Odoo Forum**: https://www.odoo.com/forum
- **Anthropic Discord**: https://discord.gg/anthropic

### 12.3 Ejemplos de Código

- **Repositorio del proyecto**: git@github.com:yochi2005/Odoo-AI-Addons.git
- **Odoo Apps**: https://apps.odoo.com/

---

## 13. Conclusión

Has aprendido a crear un módulo completo de integración IA para Odoo desde cero, cubriendo:

✅ **Arquitectura**: API-only, tool calling, permisos
✅ **Componentes**: Models, Views, Tools, Orchestrator
✅ **Integración**: Claude API, Odoo Web API
✅ **Testing**: Manual, debugging, logging
✅ **Producción**: Seguridad, performance, errores
✅ **Extensión**: Nuevas herramientas, personalización

**Próximos pasos:**

1. Crear herramientas adicionales (facturación, inventario, etc.)
2. Implementar streaming para respuestas en tiempo real
3. Agregar soporte multi-usuario con historial persistente
4. Integrar con más módulos de Odoo (HR, Project, etc.)
5. Desplegar en producción con HTTPS y autenticación robusta

¡Felicidades por completar esta guía! 🎉

---

**Versión:** 1.0.0
**Última actualización:** 2025-12-08
**Autor:** Proyecto Odoo-AI-Addons
**Licencia:** LGPL-3
