# Ejemplos de Código - Odoo + Claude AI

**Colección de ejemplos prácticos y casos de uso reales**

---

## 📋 Índice

1. [Herramientas Básicas](#herramientas-básicas)
2. [Integraciones Avanzadas](#integraciones-avanzadas)
3. [Casos de Uso Reales](#casos-de-uso-reales)
4. [Snippets Útiles](#snippets-útiles)

---

## 1. Herramientas Básicas

### 1.1 Cliente API Simple

```python
"""Ejemplo mínimo de cliente API de Odoo"""
import xmlrpc.client

# Conectar
url = 'http://localhost:8069'
db = 'odoo18_2'
username = 'admin'
password = 'admin'

# Autenticar
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

# Ejecutar búsqueda
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
partners = models.execute_kw(
    db, uid, password,
    'res.partner', 'search_read',
    [[('is_company', '=', True)]],
    {'fields': ['name', 'email'], 'limit': 5}
)

print(f"Encontrados {len(partners)} clientes:")
for p in partners:
    print(f"  - {p['name']}: {p['email']}")
```

### 1.2 Herramienta de Creación de Contactos

```python
"""Crear contactos desde lenguaje natural"""

def create_contact(
    url: str,
    db: str,
    username: str,
    password: str,
    name: str,
    email: str = None,
    phone: str = None,
    is_company: bool = False
):
    """
    Create a new contact in Odoo.

    Example Claude prompts:
    - "Create a contact named John Doe with email john@example.com"
    - "Add a company called Acme Corp with phone 555-1234"
    """
    try:
        from odoo_api_client import OdooAPIClient

        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        # Verificar permisos
        if not client.check_access_rights('res.partner', 'create'):
            return {
                'success': False,
                'error': 'No create permission on contacts'
            }

        # Preparar datos
        values = {
            'name': name,
            'is_company': is_company
        }
        if email:
            values['email'] = email
        if phone:
            values['phone'] = phone

        # Crear contacto
        contact_id = client.create('res.partner', values)

        # Leer contacto creado
        contact = client.search_read(
            'res.partner',
            [('id', '=', contact_id)],
            ['name', 'email', 'phone', 'is_company']
        )[0]

        return {
            'success': True,
            'data': {
                'id': contact_id,
                'contact': contact
            },
            'summary': {
                'message': f"Contact '{name}' created successfully",
                'id': contact_id
            },
            'error': None
        }

    except Exception as e:
        return {
            'success': False,
            'data': None,
            'summary': None,
            'error': str(e)
        }


# Definición para Claude
CREATE_CONTACT_TOOL = {
    "name": "create_contact",
    "description": """Create a new contact (person or company) in Odoo.

    Use this when user wants to:
    - Add a new customer
    - Create a supplier record
    - Register a new person or company

    Examples:
    - "Add John Smith as a contact"
    - "Create a company called Tech Solutions with email info@tech.com"
    """,
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "db": {"type": "string"},
            "username": {"type": "string"},
            "password": {"type": "string"},
            "name": {
                "type": "string",
                "description": "Full name of person or company"
            },
            "email": {
                "type": "string",
                "description": "Email address (optional)"
            },
            "phone": {
                "type": "string",
                "description": "Phone number (optional)"
            },
            "is_company": {
                "type": "boolean",
                "description": "True if this is a company, False if person",
                "default": False
            }
        },
        "required": ["url", "db", "username", "password", "name"]
    }
}
```

### 1.3 Búsqueda de Productos

```python
"""Buscar productos por nombre, categoría o código"""

def search_products(
    url: str,
    db: str,
    username: str,
    password: str,
    search_term: str = None,
    category: str = None,
    min_price: float = None,
    max_price: float = None,
    in_stock_only: bool = False,
    limit: int = 20
):
    """
    Search products in Odoo catalog.

    Example prompts:
    - "Find products containing 'laptop'"
    - "Show me products in Electronics category under $500"
    - "What products do we have in stock?"
    """
    try:
        from odoo_api_client import OdooAPIClient

        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        if not client.check_access_rights('product.product', 'read'):
            return {'success': False, 'error': 'No read permission on products'}

        # Construir dominio de búsqueda
        domain = []

        if search_term:
            domain.append(('name', 'ilike', search_term))

        if category:
            # Buscar categoría primero
            categories = client.search_read(
                'product.category',
                [('name', 'ilike', category)],
                ['id']
            )
            if categories:
                domain.append(('categ_id', 'in', [c['id'] for c in categories]))

        if min_price is not None:
            domain.append(('list_price', '>=', min_price))

        if max_price is not None:
            domain.append(('list_price', '<=', max_price))

        if in_stock_only:
            # Nota: qty_available puede requerir permisos de stock
            domain.append(('qty_at_date', '>', 0))

        # Buscar productos
        products = client.search_read(
            'product.product',
            domain,
            ['name', 'default_code', 'list_price', 'categ_id'],
            limit=limit
        )

        return {
            'success': True,
            'data': products,
            'summary': {
                'count': len(products),
                'search_term': search_term,
                'filters': {
                    'category': category,
                    'min_price': min_price,
                    'max_price': max_price,
                    'in_stock_only': in_stock_only
                }
            },
            'error': None
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


SEARCH_PRODUCTS_TOOL = {
    "name": "search_products",
    "description": "Search and filter products in Odoo catalog",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "db": {"type": "string"},
            "username": {"type": "string"},
            "password": {"type": "string"},
            "search_term": {
                "type": "string",
                "description": "Text to search in product names"
            },
            "category": {
                "type": "string",
                "description": "Product category name"
            },
            "min_price": {
                "type": "number",
                "description": "Minimum price filter"
            },
            "max_price": {
                "type": "number",
                "description": "Maximum price filter"
            },
            "in_stock_only": {
                "type": "boolean",
                "description": "Only show products in stock",
                "default": False
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results",
                "default": 20
            }
        },
        "required": ["url", "db", "username", "password"]
    }
}
```

---

## 2. Integraciones Avanzadas

### 2.1 Pipeline de Ventas

```python
"""Analizar pipeline de ventas y predecir cierre"""

def analyze_sales_pipeline(
    url: str,
    db: str,
    username: str,
    password: str,
    stage: str = None,
    min_probability: float = 0.0,
    forecast_days: int = 30
):
    """
    Analyze sales pipeline and forecast revenue.

    Prompts:
    - "What opportunities do we have in qualification stage?"
    - "Show me deals likely to close this month"
    - "What's our pipeline revenue for Q1?"
    """
    from datetime import datetime, timedelta
    from odoo_api_client import OdooAPIClient

    try:
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        domain = [('type', '=', 'opportunity')]

        if stage:
            stages = client.search_read(
                'crm.stage',
                [('name', 'ilike', stage)],
                ['id']
            )
            if stages:
                domain.append(('stage_id', 'in', [s['id'] for s in stages]))

        if min_probability > 0:
            domain.append(('probability', '>=', min_probability))

        # Filtro de fecha de cierre esperado
        forecast_date = (datetime.now() + timedelta(days=forecast_days)).strftime('%Y-%m-%d')
        domain.append(('date_deadline', '<=', forecast_date))

        # Obtener oportunidades
        opportunities = client.search_read(
            'crm.lead',
            domain,
            ['name', 'partner_id', 'expected_revenue', 'probability',
             'stage_id', 'date_deadline', 'user_id']
        )

        # Calcular métricas
        total_revenue = sum(opp.get('expected_revenue', 0) for opp in opportunities)
        weighted_revenue = sum(
            opp.get('expected_revenue', 0) * opp.get('probability', 0) / 100
            for opp in opportunities
        )

        # Agrupar por etapa
        by_stage = {}
        for opp in opportunities:
            stage_name = opp['stage_id'][1] if opp.get('stage_id') else 'Sin etapa'
            if stage_name not in by_stage:
                by_stage[stage_name] = {
                    'count': 0,
                    'total_revenue': 0,
                    'weighted_revenue': 0
                }
            by_stage[stage_name]['count'] += 1
            by_stage[stage_name]['total_revenue'] += opp.get('expected_revenue', 0)
            by_stage[stage_name]['weighted_revenue'] += (
                opp.get('expected_revenue', 0) * opp.get('probability', 0) / 100
            )

        return {
            'success': True,
            'data': {
                'opportunities': opportunities,
                'by_stage': by_stage
            },
            'summary': {
                'total_opportunities': len(opportunities),
                'total_revenue': total_revenue,
                'weighted_revenue': weighted_revenue,
                'forecast_days': forecast_days,
                'conversion_rate': (
                    weighted_revenue / total_revenue * 100
                    if total_revenue > 0 else 0
                )
            },
            'error': None
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### 2.2 Seguimiento de Tareas

```python
"""Gestionar tareas y proyectos"""

def manage_tasks(
    url: str,
    db: str,
    username: str,
    password: str,
    action: str = 'list',  # list, create, update, complete
    task_id: int = None,
    title: str = None,
    description: str = None,
    assigned_to: str = None,
    project_name: str = None,
    priority: str = '0',  # 0=Normal, 1=Urgent
    deadline: str = None
):
    """
    Manage tasks and projects in Odoo.

    Prompts:
    - "Create a task to review invoices, assign to John"
    - "Show me all urgent tasks"
    - "Mark task #45 as complete"
    - "What are my tasks for today?"
    """
    from odoo_api_client import OdooAPIClient

    try:
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        if action == 'list':
            # Listar tareas
            domain = []
            if assigned_to:
                users = client.search_read(
                    'res.users',
                    [('name', 'ilike', assigned_to)],
                    ['id']
                )
                if users:
                    domain.append(('user_ids', 'in', [u['id'] for u in users]))

            if priority in ['1', 'urgent']:
                domain.append(('priority', '=', '1'))

            tasks = client.search_read(
                'project.task',
                domain,
                ['name', 'description', 'user_ids', 'project_id',
                 'priority', 'date_deadline', 'stage_id'],
                limit=50
            )

            return {
                'success': True,
                'data': tasks,
                'summary': {'count': len(tasks)},
                'error': None
            }

        elif action == 'create':
            # Crear tarea
            if not client.check_access_rights('project.task', 'create'):
                return {'success': False, 'error': 'No create permission'}

            values = {'name': title or 'Nueva tarea'}

            if description:
                values['description'] = description

            if assigned_to:
                users = client.search_read(
                    'res.users',
                    [('name', 'ilike', assigned_to)],
                    ['id']
                )
                if users:
                    values['user_ids'] = [(6, 0, [users[0]['id']])]

            if project_name:
                projects = client.search_read(
                    'project.project',
                    [('name', 'ilike', project_name)],
                    ['id']
                )
                if projects:
                    values['project_id'] = projects[0]['id']

            if priority:
                values['priority'] = '1' if priority in ['1', 'urgent'] else '0'

            if deadline:
                values['date_deadline'] = deadline

            task_id = client.create('project.task', values)

            return {
                'success': True,
                'data': {'id': task_id},
                'summary': {'message': f"Task created with ID {task_id}"},
                'error': None
            }

        elif action == 'complete':
            # Marcar como completada
            if not task_id:
                return {'success': False, 'error': 'task_id required for complete action'}

            # Buscar etapa "Hecho" o similar
            done_stages = client.search_read(
                'project.task.type',
                [('name', 'in', ['Done', 'Completed', 'Hecho'])],
                ['id']
            )

            if done_stages:
                client.write('project.task', [task_id], {
                    'stage_id': done_stages[0]['id']
                })

                return {
                    'success': True,
                    'data': {'id': task_id},
                    'summary': {'message': f"Task {task_id} marked as complete"},
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'error': 'No "Done" stage found in project'
                }

    except Exception as e:
        return {'success': False, 'error': str(e)}
```

---

## 3. Casos de Uso Reales

### 3.1 Dashboard Ejecutivo

```python
"""Generar dashboard con KPIs principales"""

def executive_dashboard(
    url: str,
    db: str,
    username: str,
    password: str,
    period: str = 'month'  # day, week, month, quarter, year
):
    """
    Generate executive dashboard with key metrics.

    Returns:
    - Sales revenue (current vs previous period)
    - New customers
    - Pipeline value
    - Outstanding invoices
    - Inventory value
    - Top products
    - Top customers
    """
    from datetime import datetime, timedelta
    from odoo_api_client import OdooAPIClient

    try:
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        # Calcular fechas según período
        today = datetime.now()

        if period == 'day':
            start_current = today.strftime('%Y-%m-%d 00:00:00')
            end_current = today.strftime('%Y-%m-%d 23:59:59')
            start_previous = (today - timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')
            end_previous = (today - timedelta(days=1)).strftime('%Y-%m-%d 23:59:59')
        elif period == 'week':
            start_current = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            end_current = today.strftime('%Y-%m-%d')
            start_previous = (today - timedelta(days=today.weekday() + 7)).strftime('%Y-%m-%d')
            end_previous = (today - timedelta(days=today.weekday() + 1)).strftime('%Y-%m-%d')
        elif period == 'month':
            start_current = today.strftime('%Y-%m-01')
            end_current = today.strftime('%Y-%m-%d')
            prev_month = today.replace(day=1) - timedelta(days=1)
            start_previous = prev_month.strftime('%Y-%m-01')
            end_previous = prev_month.strftime('%Y-%m-%d')
        # ... implementar quarter, year

        # 1. Revenue actual vs anterior
        sales_current = client.search_read(
            'sale.order',
            [('date_order', '>=', start_current),
             ('date_order', '<=', end_current),
             ('state', '=', 'sale')],
            ['amount_total']
        )
        revenue_current = sum(s['amount_total'] for s in sales_current)

        sales_previous = client.search_read(
            'sale.order',
            [('date_order', '>=', start_previous),
             ('date_order', '<=', end_previous),
             ('state', '=', 'sale')],
            ['amount_total']
        )
        revenue_previous = sum(s['amount_total'] for s in sales_previous)

        # 2. Nuevos clientes
        new_customers = client.search_read(
            'res.partner',
            [('create_date', '>=', start_current),
             ('is_company', '=', True)],
            ['name']
        )

        # 3. Pipeline
        pipeline = client.search_read(
            'crm.lead',
            [('type', '=', 'opportunity'),
             ('probability', '>', 0)],
            ['expected_revenue', 'probability']
        )
        pipeline_value = sum(
            p['expected_revenue'] * p['probability'] / 100
            for p in pipeline
        )

        # 4. Facturas pendientes
        overdue_invoices = client.search_read(
            'account.move',
            [('move_type', '=', 'out_invoice'),
             ('state', '=', 'posted'),
             ('payment_state', 'in', ['not_paid', 'partial']),
             ('invoice_date_due', '<', today.strftime('%Y-%m-%d'))],
            ['amount_residual']
        )
        overdue_amount = sum(i['amount_residual'] for i in overdue_invoices)

        return {
            'success': True,
            'data': {
                'revenue': {
                    'current': revenue_current,
                    'previous': revenue_previous,
                    'growth': (
                        (revenue_current - revenue_previous) / revenue_previous * 100
                        if revenue_previous > 0 else 0
                    )
                },
                'customers': {
                    'new': len(new_customers),
                    'list': [c['name'] for c in new_customers]
                },
                'pipeline': {
                    'value': pipeline_value,
                    'opportunities': len(pipeline)
                },
                'receivables': {
                    'overdue_amount': overdue_amount,
                    'overdue_count': len(overdue_invoices)
                }
            },
            'summary': {
                'period': period,
                'date_range': f"{start_current} to {end_current}"
            },
            'error': None
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### 3.2 Alertas Inteligentes

```python
"""Sistema de alertas automáticas"""

def smart_alerts(
    url: str,
    db: str,
    username: str,
    password: str,
    alert_types: list = None  # ['stock', 'invoices', 'tasks', 'opportunities']
):
    """
    Generate smart alerts for important business events.

    Detects:
    - Low stock products
    - Overdue invoices
    - Stale opportunities
    - Overdue tasks
    - Quotations about to expire
    """
    from datetime import datetime, timedelta
    from odoo_api_client import OdooAPIClient

    try:
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        alerts = []

        if not alert_types:
            alert_types = ['stock', 'invoices', 'tasks', 'opportunities']

        # Alerta: Stock bajo
        if 'stock' in alert_types:
            # Nota: Requiere permisos de stock
            low_stock = client.search_read(
                'product.product',
                [('qty_at_date', '<', 10),
                 ('qty_at_date', '>', 0)],
                ['name', 'qty_at_date'],
                limit=10
            )

            if low_stock:
                alerts.append({
                    'type': 'stock',
                    'severity': 'warning',
                    'title': f"{len(low_stock)} products with low stock",
                    'description': "Products need restocking soon",
                    'data': low_stock
                })

        # Alerta: Facturas vencidas
        if 'invoices' in alert_types:
            overdue = client.search_read(
                'account.move',
                [('move_type', '=', 'out_invoice'),
                 ('state', '=', 'posted'),
                 ('payment_state', '!=', 'paid'),
                 ('invoice_date_due', '<', datetime.now().strftime('%Y-%m-%d'))],
                ['name', 'partner_id', 'amount_residual', 'invoice_date_due'],
                limit=10
            )

            if overdue:
                total_overdue = sum(i['amount_residual'] for i in overdue)
                alerts.append({
                    'type': 'invoices',
                    'severity': 'urgent',
                    'title': f"${total_overdue:,.2f} in overdue invoices",
                    'description': f"{len(overdue)} invoices past due date",
                    'data': overdue
                })

        # Alerta: Oportunidades estancadas
        if 'opportunities' in alert_types:
            stale_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            stale_opps = client.search_read(
                'crm.lead',
                [('type', '=', 'opportunity'),
                 ('write_date', '<', stale_date),
                 ('probability', '>', 0),
                 ('probability', '<', 100)],
                ['name', 'partner_id', 'expected_revenue', 'write_date'],
                limit=10
            )

            if stale_opps:
                alerts.append({
                    'type': 'opportunities',
                    'severity': 'warning',
                    'title': f"{len(stale_opps)} opportunities need attention",
                    'description': "No activity in the last 30 days",
                    'data': stale_opps
                })

        # Alerta: Tareas vencidas
        if 'tasks' in alert_types:
            overdue_tasks = client.search_read(
                'project.task',
                [('date_deadline', '<', datetime.now().strftime('%Y-%m-%d')),
                 ('stage_id.name', '!=', 'Done')],
                ['name', 'user_ids', 'date_deadline', 'project_id'],
                limit=10
            )

            if overdue_tasks:
                alerts.append({
                    'type': 'tasks',
                    'severity': 'urgent',
                    'title': f"{len(overdue_tasks)} overdue tasks",
                    'description': "Tasks past their deadline",
                    'data': overdue_tasks
                })

        return {
            'success': True,
            'data': {
                'alerts': alerts,
                'summary_by_severity': {
                    'urgent': len([a for a in alerts if a['severity'] == 'urgent']),
                    'warning': len([a for a in alerts if a['severity'] == 'warning']),
                    'info': len([a for a in alerts if a['severity'] == 'info'])
                }
            },
            'summary': {
                'total_alerts': len(alerts),
                'requires_action': len([a for a in alerts if a['severity'] == 'urgent'])
            },
            'error': None
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}
```

---

## 4. Snippets Útiles

### 4.1 Paginación de Resultados

```python
"""Manejar grandes volúmenes de datos con paginación"""

def fetch_all_records(client, model, domain, fields, batch_size=100):
    """
    Fetch all records from a model using pagination.

    Args:
        client: OdooAPIClient instance
        model: Model name
        domain: Search domain
        fields: Fields to read
        batch_size: Records per batch

    Returns:
        List of all records
    """
    all_records = []
    offset = 0

    while True:
        batch = client.search_read(
            model,
            domain,
            fields,
            limit=batch_size,
            offset=offset
        )

        if not batch:
            break

        all_records.extend(batch)
        offset += batch_size

        # Opcional: log progreso
        print(f"Fetched {len(all_records)} records so far...")

    return all_records


# Uso
client = OdooAPIClient(url, db, username, password)
client.authenticate()

all_products = fetch_all_records(
    client,
    'product.product',
    [('sale_ok', '=', True)],
    ['name', 'list_price', 'categ_id']
)

print(f"Total products: {len(all_products)}")
```

### 4.2 Manejo de Relaciones Many2one

```python
"""Trabajar con campos relacionales"""

def get_order_with_details(client, order_id):
    """
    Get sales order with all related data.

    Demonstrates:
    - Reading Many2one fields (partner_id, user_id)
    - Reading One2many fields (order_line)
    - Following relations
    """
    # 1. Leer orden principal
    order = client.search_read(
        'sale.order',
        [('id', '=', order_id)],
        ['name', 'partner_id', 'user_id', 'date_order', 'amount_total']
    )[0]

    # 2. Obtener cliente completo (partner_id devuelve [id, name])
    if order.get('partner_id'):
        partner_id = order['partner_id'][0]
        partner = client.search_read(
            'res.partner',
            [('id', '=', partner_id)],
            ['name', 'email', 'phone', 'street', 'city']
        )[0]
        order['partner_details'] = partner

    # 3. Obtener vendedor completo
    if order.get('user_id'):
        user_id = order['user_id'][0]
        user = client.search_read(
            'res.users',
            [('id', '=', user_id)],
            ['name', 'email']
        )[0]
        order['salesperson_details'] = user

    # 4. Obtener líneas de orden
    lines = client.search_read(
        'sale.order.line',
        [('order_id', '=', order_id)],
        ['product_id', 'product_uom_qty', 'price_unit', 'price_subtotal']
    )

    # 5. Para cada línea, obtener detalles del producto
    for line in lines:
        if line.get('product_id'):
            product_id = line['product_id'][0]
            product = client.search_read(
                'product.product',
                [('id', '=', product_id)],
                ['name', 'default_code', 'categ_id']
            )[0]
            line['product_details'] = product

    order['order_lines'] = lines

    return order


# Uso
order_full = get_order_with_details(client, 42)
print(f"Order: {order_full['name']}")
print(f"Customer: {order_full['partner_details']['name']}")
print(f"Lines: {len(order_full['order_lines'])}")
```

### 4.3 Búsqueda Avanzada con Dominios

```python
"""Ejemplos de dominios de búsqueda complejos"""

# AND implícito (todas las condiciones deben cumplirse)
domain = [
    ('state', '=', 'sale'),
    ('amount_total', '>', 1000),
    ('date_order', '>=', '2025-01-01')
]

# OR explícito
domain = [
    '|',  # Operador OR
    ('state', '=', 'sale'),
    ('state', '=', 'done')
]

# Combinación AND + OR
domain = [
    ('date_order', '>=', '2025-01-01'),
    '|',  # OR para las siguientes 2 condiciones
    ('amount_total', '>', 5000),
    ('partner_id.is_company', '=', True)
]

# NOT (negación)
domain = [
    ('state', '!=', 'cancel'),  # No canceladas
    ('partner_id', '!=', False)  # Tienen cliente asignado
]

# IN (en lista)
domain = [
    ('state', 'in', ['sale', 'done']),
    ('user_id', 'in', [1, 2, 3])
]

# LIKE (búsqueda de texto)
domain = [
    ('name', 'ilike', '%laptop%'),  # Contiene "laptop" (case-insensitive)
    ('email', 'like', '%@gmail.com')  # Termina en @gmail.com
]

# Relaciones (punto para seguir relación)
domain = [
    ('partner_id.country_id.code', '=', 'US'),  # Cliente de USA
    ('order_line.product_id.categ_id.name', '=', 'Electronics')  # Tiene producto de Electrónicos
]

# Fechas
from datetime import datetime, timedelta

today = datetime.now()
last_month = (today - timedelta(days=30)).strftime('%Y-%m-%d')

domain = [
    ('create_date', '>=', last_month),
    ('create_date', '<=', today.strftime('%Y-%m-%d'))
]
```

### 4.4 Crear Registros con Relaciones

```python
"""Crear registros con campos relacionales"""

def create_sale_order_complete(client):
    """
    Create a complete sales order with lines.

    Demonstrates:
    - Creating main record
    - Creating related records (One2many)
    - Setting Many2one relations
    """

    # 1. Buscar/crear cliente
    partner_id = client.search_read(
        'res.partner',
        [('email', '=', 'customer@example.com')],
        ['id']
    )

    if partner_id:
        partner_id = partner_id[0]['id']
    else:
        # Crear cliente si no existe
        partner_id = client.create('res.partner', {
            'name': 'New Customer',
            'email': 'customer@example.com',
            'phone': '555-1234'
        })

    # 2. Buscar productos
    products = client.search_read(
        'product.product',
        [('sale_ok', '=', True)],
        ['id', 'name', 'list_price'],
        limit=2
    )

    # 3. Crear orden de venta con líneas
    order_id = client.create('sale.order', {
        'partner_id': partner_id,
        'order_line': [
            (0, 0, {  # (0, 0, {...}) = crear nuevo registro
                'product_id': products[0]['id'],
                'product_uom_qty': 2,
                'price_unit': products[0]['list_price']
            }),
            (0, 0, {
                'product_id': products[1]['id'],
                'product_uom_qty': 1,
                'price_unit': products[1]['list_price']
            })
        ]
    })

    return order_id


# Sintaxis de comandos para relaciones One2many y Many2many:
# (0, 0, {...})      - Crear nuevo registro
# (1, id, {...})     - Actualizar registro existente
# (2, id)            - Eliminar registro
# (3, id)            - Desvincular registro (sin eliminar)
# (4, id)            - Vincular registro existente
# (5,)               - Desvincular todos
# (6, 0, [ids])      - Reemplazar con lista de IDs
```

---

## 5. Testing y Validación

### 5.1 Suite de Tests

```python
"""Test suite para herramientas"""

def test_tool(tool_function, test_cases):
    """
    Test a tool with multiple test cases.

    Args:
        tool_function: Function to test
        test_cases: List of dicts with 'name', 'input', 'expected'
    """
    results = []

    for case in test_cases:
        print(f"\nTesting: {case['name']}")
        print("-" * 60)

        try:
            result = tool_function(**case['input'])

            # Validar resultado
            success = result.get('success', False)
            error = result.get('error')

            if case.get('should_fail', False):
                # Este test debe fallar
                if success:
                    print(f"❌ FAIL: Expected failure but got success")
                    results.append(False)
                else:
                    print(f"✅ PASS: Failed as expected: {error}")
                    results.append(True)
            else:
                # Este test debe tener éxito
                if success:
                    print(f"✅ PASS: {case['name']}")
                    if case.get('validate'):
                        # Validación adicional
                        if case['validate'](result):
                            print(f"  ✓ Custom validation passed")
                        else:
                            print(f"  ✗ Custom validation failed")
                            results.append(False)
                            continue
                    results.append(True)
                else:
                    print(f"❌ FAIL: {error}")
                    results.append(False)

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append(False)

    # Resumen
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)

    return all(results)


# Uso
test_cases = [
    {
        'name': 'Search products by name',
        'input': {
            'url': 'http://localhost:8069',
            'db': 'odoo18_2',
            'username': 'admin',
            'password': 'admin',
            'search_term': 'laptop'
        },
        'validate': lambda r: len(r['data']) > 0
    },
    {
        'name': 'Search with invalid credentials',
        'input': {
            'url': 'http://localhost:8069',
            'db': 'odoo18_2',
            'username': 'invalid',
            'password': 'wrong',
            'search_term': 'laptop'
        },
        'should_fail': True
    },
    {
        'name': 'Search with price filter',
        'input': {
            'url': 'http://localhost:8069',
            'db': 'odoo18_2',
            'username': 'admin',
            'password': 'admin',
            'min_price': 100,
            'max_price': 500
        },
        'validate': lambda r: all(
            100 <= item['list_price'] <= 500
            for item in r['data']
        )
    }
]

from search_products import search_products
test_tool(search_products, test_cases)
```

---

**Fin de Ejemplos**

Para más información, consultar:
- [ODOO_CLAUDE_INTEGRATION_COMPLETE_GUIDE.md](./ODOO_CLAUDE_INTEGRATION_COMPLETE_GUIDE.md)
- [QUICK_START.md](./QUICK_START.md)
