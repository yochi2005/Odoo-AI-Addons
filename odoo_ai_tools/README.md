# Odoo AI Tools - Claude Integration

AI-powered assistant for Odoo using **Claude** (Anthropic) with **tool calling** and **Odoo Web API**.

---

## Features

This module integrates Claude AI with Odoo to enable natural language operations:

### 5 Intelligent Tools

1. **Sales Reports** - Generate sales reports from natural language
   - Group by product, customer, or salesperson
   - Flexible date ranges
   - Automatic calculations

2. **Invoice Creation** - Create draft invoices automatically
   - From recent sales orders
   - Batch invoice creation
   - Automatic line items

3. **Tax Deductions (Mexico)** - Suggest tax-deductible expenses
   - SAT compliance
   - Automatic categorization
   - Deduction requirements

4. **Quotation Summary** - Intelligent quotation follow-up
   - Urgency analysis
   - Expiration tracking
   - Recommended actions

5. **Inventory Restock** - Detect products needing restock
   - Sales velocity analysis
   - Stock level monitoring
   - Suggested order quantities

---

## Architecture

```
┌─────────────┐
│   User      │ "Generate a sales report by product from March to July"
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Claude (LLM)   │ Understands natural language
└────────┬────────┘ Decides which tool to call
         │
         ▼
┌──────────────────┐
│  Claude Tools    │ 5 specialized functions
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Odoo Web API    │ Execute operations (respects permissions)
└──────────────────┘
```

---

## Requirements

- **Odoo**: 18.2+
- **Python**: 3.12+
- **Python packages**:
  - `anthropic` (Anthropic Python SDK)
  - Already installed in your venv

- **Anthropic API Key**: Get one at https://console.anthropic.com/

---

## Installation

### 1. Module is already created

The module is located at:
```
~/odoo-18/custom-addons/odoo_ai_tools/
```

### 2. Install in Odoo

```bash
# Restart Odoo to detect the module
cd ~/odoo-18/odoo
source ../venv/bin/activate
./odoo-bin -c ../config/odoo.conf -d odoo18_2 -u all --stop-after-init

# Start Odoo
./odoo-bin -c ../config/odoo.conf -d odoo18_2
```

### 3. Install module from Odoo UI

1. Go to **Apps**
2. Search for "**AI Tools**"
3. Click **Install**

---

##Configuration

### 1. Get Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to **API Keys**
4. Create a new API key
5. Copy the key (starts with `sk-ant-...`)

### 2. Configure in Odoo

**Method 1: Via Configuration Wizard**

1. Go to **AI Assistant → Configuration**
2. Enter your **Anthropic API Key**
3. Enter your **Odoo Password** (for API authentication)
4. Click **Test Connection**

**Method 2: Per Conversation**

You can provide the API key when creating a new conversation.

---

##Usage

### Example 1: Sales Report

**You ask:**
> "Generate a sales report by product from March to July"

**Claude:**
- Calls `generate_sales_report` tool
- Parameters: `date_from='2025-03-01'`, `date_to='2025-07-31'`, `group_by='product'`
- Returns grouped sales data with totals

### Example 2: Invoice Creation

**You ask:**
> "Create invoices for the last 3 sales"

**Claude:**
- Calls `create_invoice_from_sales` tool
- Parameters: `last_n_orders=3`
- Creates draft invoices

### Example 3: Tax Deductions

**You ask:**
> "What expenses can be tax deductible?"

**Claude:**
- Calls `suggest_tax_deductions` tool
- Analyzes recent expenses
- Categorizes by SAT requirements

### Example 4: Quotation Follow-up

**You ask:**
> "Which quotations need follow-up this week?"

**Claude:**
- Calls `summarize_quotations` tool
- Parameters: `days_ahead=7`
- Returns prioritized list with actions

### Example 5: Inventory Restock

**You ask:**
> "What products should I order before Friday?"

**Claude:**
- Calls `detect_restock_needs` tool
- Analyzes stock levels and sales velocity
- Returns products with urgency levels

---

## Security

### Permission-Based Access

All tools respect Odoo permissions:

- **Read permissions**: Required to view data
- **Create permissions**: Required to create records
- **User isolation**: Each user only sees/modifies data they have access to

### No Direct Database Access

- Uses **Odoo JSON-RPC Web API** exclusively
- No SQL queries
- No direct database connections
- Respects all Odoo security rules

### API Key Storage

- API keys are stored per user/conversation
- Use environment variables in production
- Never commit API keys to version control

---

## Module Structure

```
odoo_ai_tools/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── ai_assistant.py          # Odoo model
├── views/
│   └── ai_assistant_views.xml   # UI views
├── controllers/
│   ├── __init__.py
│   └── main.py                   # HTTP controllers
├── security/
│   └── ir.model.access.csv      # Access rights
├── tools/
│   ├── __init__.py
│   ├── odoo_api_client.py       # Odoo API client
│   ├── sales_reports.py         # Tool 1
│   ├── invoice_creation.py      # Tool 2
│   ├── tax_deductions.py        # Tool 3
│   ├── quotation_summary.py     # Tool 4
│   ├── inventory_restock.py     # Tool 5
│   └── claude_orchestrator.py   # Claude integration
└── static/
    └── description/
        └── icon.png (optional)
```

---

## Development

### Adding a New Tool

1. Create a new file in `tools/` (e.g., `my_new_tool.py`)

2. Implement the tool function:

```python
def my_new_tool(
    url: str,
    db: str,
    username: str,
    password: str,
    # ... your parameters
) -> Dict:
    """Tool description."""
    try:
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        # Your logic here
        result = client.search_read(...)

        return {
            'success': True,
            'data': result,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'error': str(e)
        }
```

3. Define the tool schema for Claude:

```python
MY_TOOL_DEFINITION = {
    "name": "my_new_tool",
    "description": "What this tool does",
    "input_schema": {
        "type": "object",
        "properties": {
            # ... parameters
        },
        "required": ["url", "db", "username", "password"]
    }
}
```

4. Register in `claude_orchestrator.py`:

```python
from .my_new_tool import my_new_tool, MY_TOOL_DEFINITION

TOOL_FUNCTIONS['my_new_tool'] = my_new_tool
ALL_TOOLS.append(MY_TOOL_DEFINITION)
```

---

## Troubleshooting

### Error: "anthropic package not installed"

```bash
cd ~/odoo-18/odoo
source ../venv/bin/activate
pip install anthropic
```

### Error: "Authentication failed"

- Verify your Anthropic API key is correct
- Check your Odoo password
- Ensure user has required permissions

### Tool Execution Fails

- Check Odoo logs: `tail -f ~/odoo-18/logs/odoo.log`
- Verify user permissions for the operation
- Check if data exists (e.g., sales orders for invoicing)

### Module Not Appearing

```bash
# Update module list
cd ~/odoo-18/odoo
source ../venv/bin/activate
./odoo-bin -c ../config/odoo.conf -d odoo18_2 -u base --stop-after-init
```

---

## Testing

### Manual Testing

1. Go to **AI Assistant → Conversations**
2. Click **Create**
3. Enter your API key
4. Type a message
5. Click **Send to Claude**

### Example Test Messages

```
"Hello, can you help me with Odoo?"
"Generate a sales report by customer"
"Create invoices for recent sales"
"Which products need restocking?"
```

---

## Learn More

### Claude API Documentation
- https://docs.anthropic.com/
- https://docs.anthropic.com/en/docs/build-with-claude/tool-use

### Odoo API Documentation
- https://www.odoo.com/documentation/18.0/developer/reference/external_api.html

### Tool Calling with Claude
- https://docs.anthropic.com/en/docs/build-with-claude/tool-use

---

## License

LGPL-3

---

## 👥 Author

Created for Odoo 18.2 + Claude integration

---

## Roadmap

Future improvements:

- [ ] Streaming responses
- [ ] Multi-turn conversations with context
- [ ] Custom tool creation from UI
- [ ] Tool analytics and logging
- [ ] Webhook support for async operations
- [ ] Integration with more Odoo modules

---

**Version:** 18.2.1.0.0
**Last Updated:** 2025-12-08
