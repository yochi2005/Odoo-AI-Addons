# Installation Guide - Odoo AI Tools

Quick guide to install and use the AI Tools module.

---

## 📋 Prerequisites

- ✅ Odoo 18.2 installed and running
- ✅ Python 3.12+ with virtualenv
- ✅ Anthropic Python SDK installed (`pip install anthropic`)
- ✅ Anthropic API key (get at https://console.anthropic.com/)

---

## 🚀 Installation Steps

### 1. Module is Ready

The module is already created at:
```
~/odoo-18/custom-addons/odoo_ai_tools/
```

### 2. Update Module List

```bash
cd ~/odoo-18/odoo
source ../venv/bin/activate

# Update all modules
./odoo-bin -c ../config/odoo.conf -d odoo18_2 -u all --stop-after-init
```

### 3. Restart Odoo

```bash
# Start Odoo (if not running)
./odoo-bin -c ../config/odoo.conf -d odoo18_2
```

### 4. Install Module from UI

1. Open browser: http://localhost:8069
2. Login: `admin` / `admin`
3. Go to **Apps**
4. Remove "Apps" filter
5. Search for "**Odoo AI Tools**" or "**Claude**"
6. Click **Install**

---

## 🔧 First-Time Configuration

### 1. Get Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Click on **API Keys**
4. **Create Key**
5. Copy the key (starts with `sk-ant-...`)

### 2. Test Connection

1. In Odoo, go to **AI Assistant → Configuration**
2. Paste your **Anthropic API Key**
3. Enter your **Odoo Password**
4. Click **Test Connection**
5. You should see a success message

---

## 💬 Using the AI Assistant

### Create Your First Conversation

1. Go to **AI Assistant → Conversations**
2. Click **Create**
3. Enter your **Anthropic API Key** (once per conversation or save it)
4. In "Your Message" field, type:
   ```
   Hello! Can you help me generate a sales report?
   ```
5. Click **Send to Claude**
6. Wait for response (usually 2-5 seconds)

### Example Prompts to Try

```
"Generate a sales report by product from last month"

"Create invoices for the last 5 sales orders"

"What expenses from the last 3 months can be tax deductible?"

"Which quotations are expiring this week?"

"What products should I restock before next week?"
```

---

## 🔍 Verification

### Check Module Installation

```bash
# Connect to database
psql -d odoo18_2

# Check if model exists
SELECT COUNT(*) FROM ir_model WHERE model = 'ai.assistant';
# Should return 1

# Exit
\q
```

### Check Logs

```bash
tail -f ~/odoo-18/logs/odoo.log | grep -i "ai_assistant"
```

---

## 🐛 Troubleshooting

### Module Not Found in Apps

**Solution:**
```bash
cd ~/odoo-18/odoo
source ../venv/bin/activate
./odoo-bin -c ../config/odoo.conf -d odoo18_2 -u base --stop-after-init
```

### Import Error: anthropic

**Solution:**
```bash
cd ~/odoo-18/odoo
source ../venv/bin/activate
pip install anthropic
```

### Permission Error

**Solution:** Verify the user has:
- Read access to sale.order, account.move, stock, etc.
- Create access to account.move (for invoice creation)

### API Key Error

**Solutions:**
- Verify API key starts with `sk-ant-`
- Check you have credits in your Anthropic account
- Try creating a new API key

---

## 📊 Module Statistics

| Component | Count |
|-----------|-------|
| **Tools** | 5 |
| **Models** | 2 (ai.assistant, ai.assistant.config) |
| **Views** | 5 |
| **Controllers** | 1 |
| **Python Files** | 10 |
| **Total Lines** | ~2500+ |

---

## ✅ Success Checklist

- [ ] Module appears in Apps
- [ ] Module installed successfully
- [ ] AI Assistant menu visible
- [ ] Can create new conversation
- [ ] Test connection works
- [ ] Claude responds to messages
- [ ] Tools execute successfully

---

**Last Updated:** 2025-12-08
