# Odoo AI Addons

AI-powered modules for Odoo using Claude (Anthropic) integration.

## 📦 Modules

### odoo_ai_tools - Claude Integration

AI assistant for Odoo 18.2+ that uses **Claude** (Anthropic) with **tool calling** and **Odoo Web API**.

**Features:**
- 📊 **Sales Reports** - Generate reports from natural language
- 📄 **Invoice Creation** - Auto-create draft invoices from sales orders
- 💰 **Tax Deductions (Mexico)** - Suggest SAT-compliant deductible expenses
- 📋 **Quotation Summary** - Intelligent follow-up with urgency analysis
- 📦 **Inventory Restock** - Detect products needing restock based on sales velocity

**Architecture:**
- Uses Anthropic Claude API for natural language understanding
- Integrates with Odoo exclusively via JSON-RPC Web API (no ORM, no direct DB access)
- Permission-based access control
- Multi-turn conversations with context

[📖 Full Documentation](./odoo_ai_tools/README.md)

---

## 🚀 Quick Start

### Requirements
- Odoo 18.2+
- Python 3.12+
- Anthropic API Key

### Installation

1. **Clone this repository:**
```bash
cd ~/odoo-18/custom-addons/
git clone git@github.com:yochi2005/Odoo-AI-Addons.git
```

2. **Install Python dependencies:**
```bash
cd ~/odoo-18/odoo
source ../venv/bin/activate
pip install anthropic
```

3. **Restart Odoo and install module:**
```bash
./odoo-bin -c ../config/odoo.conf -d your_database -u all --stop-after-init
./odoo-bin -c ../config/odoo.conf -d your_database
```

4. **Configure in Odoo:**
   - Go to **Apps** → Search "AI Tools" → Install
   - Go to **AI Assistant → Configuration**
   - Enter your Anthropic API Key
   - Start chatting with Claude!

---

## 📖 Documentation

Each module contains detailed documentation:
- **README.md** - Features, usage examples, architecture
- **INSTALLATION.md** - Step-by-step installation guide

---

## 🔒 Security

- All tools respect Odoo user permissions
- API-only access (no direct database queries)
- Credentials stored per user/conversation
- Use environment variables for production API keys

---

## 📝 License

LGPL-3

---

## 👥 Contributing

Contributions are welcome! Please ensure:
- No direct database access (use Odoo Web API only)
- Respect user permissions
- Follow existing tool patterns
- Include documentation

---

**Version:** 18.2.1.0.0
**Last Updated:** 2025-12-08
