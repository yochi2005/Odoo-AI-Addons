# Guía Rápida: Odoo + Claude AI

**Inicio rápido en 5 minutos**

---

## 🚀 Instalación Express

### 1. Prerrequisitos

```bash
# Verificar versiones
python3 --version  # Debe ser 3.12+
psql --version     # Debe ser 14+

# Instalar Odoo
cd ~/odoo-18
git clone --depth 1 --branch 18.0 https://github.com/odoo/odoo.git
python3.12 -m venv venv
source venv/bin/activate
pip install -r odoo/requirements.txt
pip install anthropic
```

### 2. Configurar PostgreSQL

```bash
# Cambiar autenticación a 'trust' en desarrollo
sudo nano /var/lib/pgsql/data/pg_hba.conf
# Cambiar 'ident' a 'trust'

sudo systemctl restart postgresql
createdb odoo18_2
```

### 3. Clonar Módulo

```bash
cd ~/odoo-18
git clone git@github.com:yochi2005/Odoo-AI-Addons.git custom-addons
```

### 4. Configurar Odoo

```bash
cat > ~/odoo-18/config/odoo.conf << EOF
[options]
addons_path = /home/$USER/odoo-18/odoo/addons,/home/$USER/odoo-18/custom-addons
db_host = localhost
db_user = $USER
logfile = /home/$USER/odoo-18/logs/odoo.log
EOF

mkdir -p ~/odoo-18/logs
```

### 5. Iniciar Odoo

```bash
cd ~/odoo-18/odoo
source ../venv/bin/activate

# Instalar módulo
./odoo-bin -c ../config/odoo.conf -d odoo18_2 -i odoo_ai_tools --stop-after-init

# Iniciar servidor
./odoo-bin -c ../config/odoo.conf -d odoo18_2
```

### 6. Usar el Módulo

1. Abrir http://localhost:8069
2. Login: `admin` / `admin`
3. Ir a **AI Assistant → Conversations**
4. Click **Create**
5. Ingresar API key de Anthropic
6. Escribir mensaje: *"Genera un reporte de ventas por producto"*
7. Click **Send to Claude**

---

## 📚 Conceptos en 2 Minutos

### Flujo de Ejecución

```
Usuario → Odoo UI → Python Model → Claude Orchestrator
    ↓
Claude API (decide usar herramienta)
    ↓
Tool Function → Odoo API Client → Odoo Server
    ↓
Resultado → Claude → Respuesta al Usuario
```

### Componentes Clave

| Componente | Qué hace |
|------------|----------|
| `models/ai_assistant.py` | Guarda conversaciones en BD |
| `views/ai_assistant_views.xml` | UI de formulario |
| `tools/odoo_api_client.py` | Cliente XML-RPC para Odoo |
| `tools/sales_reports.py` | Herramienta de reportes |
| `tools/claude_orchestrator.py` | Maneja conversación con Claude |

### Anatomía de una Herramienta

```python
def my_tool(url, db, username, password, param1, param2):
    """
    1. Autenticar con Odoo
    2. Verificar permisos
    3. Ejecutar operación
    4. Retornar resultado estándar
    """
    try:
        client = OdooAPIClient(url, db, username, password)
        client.authenticate()

        if not client.check_access_rights('model', 'read'):
            return {'success': False, 'error': 'Permission denied'}

        data = client.search_read('model', domain, fields)

        return {
            'success': True,
            'data': data,
            'summary': {'count': len(data)},
            'error': None
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# Definición para Claude
MY_TOOL = {
    "name": "my_tool",
    "description": "What the tool does and when to use it",
    "input_schema": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."},
            "param2": {"type": "integer", "description": "..."}
        },
        "required": ["url", "db", "username", "password"]
    }
}
```

---

## 🔧 Comandos Útiles

### Desarrollo

```bash
# Reiniciar Odoo con módulo actualizado
./odoo-bin -c ../config/odoo.conf -d odoo18_2 -u odoo_ai_tools --stop-after-init

# Ver logs en tiempo real
tail -f ~/odoo-18/logs/odoo.log

# Limpiar cache Python
find ~/odoo-18/custom-addons/odoo_ai_tools -name "*.pyc" -delete
find ~/odoo-18/custom-addons/odoo_ai_tools -type d -name __pycache__ -exec rm -rf {} +

# Detener Odoo
pkill -f odoo-bin
```

### Testing

```bash
# Probar herramienta sin Claude
cd ~/odoo-18/custom-addons/odoo_ai_tools/tools
python3 -c "
from sales_reports import generate_sales_report
result = generate_sales_report(
    'http://localhost:8069', 'odoo18_2', 'admin', 'admin',
    date_from='2025-01-01', date_to='2025-12-31', group_by='product'
)
print(result)
"
```

### Debugging

```bash
# Modo debug
./odoo-bin -c ../config/odoo.conf -d odoo18_2 --log-level=debug

# Verificar módulo instalado
./odoo-bin shell -c ../config/odoo.conf -d odoo18_2 << EOF
env['ir.module.module'].search([('name', '=', 'odoo_ai_tools')]).state
exit()
EOF
```

---

## ⚠️ Problemas Comunes

### "Module has incompatible version"

```python
# En __manifest__.py, cambiar:
'version': 'saas~18.2.1.0.0',  # Debe empezar con serie de Odoo
```

### "Invalid view type: 'tree'"

```xml
<!-- Cambiar en views XML -->
<list>  <!-- Odoo 18+ usa 'list' en vez de 'tree' -->
```

### "anthropic not installed"

```bash
source ~/odoo-18/venv/bin/activate
pip install anthropic
```

### "Permission denied"

```python
# Verificar permisos antes de operación
if not client.check_access_rights('sale.order', 'read'):
    return {'success': False, 'error': 'No read permission'}
```

---

## 📖 Documentación Completa

Para documentación detallada paso a paso, ver:

**[ODOO_CLAUDE_INTEGRATION_COMPLETE_GUIDE.md](./ODOO_CLAUDE_INTEGRATION_COMPLETE_GUIDE.md)**

Incluye:
- ✅ Arquitectura completa del sistema
- ✅ Explicación de conceptos fundamentales
- ✅ Código comentado línea por línea
- ✅ Ejemplos de cada componente
- ✅ Resolución de problemas
- ✅ Mejores prácticas
- ✅ Guías de extensión

---

## 🎯 Próximos Pasos

1. **Agregar más herramientas**: Facturación, inventario, contabilidad
2. **Implementar streaming**: Respuestas en tiempo real
3. **Multi-usuario**: Historial por usuario, contexto persistente
4. **Webhooks**: Notificaciones asíncronas
5. **Analytics**: Dashboard de uso de herramientas

---

## 🔗 Enlaces Útiles

- **Repositorio**: https://github.com/yochi2005/Odoo-AI-Addons
- **Odoo Docs**: https://www.odoo.com/documentation/18.0/
- **Claude API**: https://docs.anthropic.com/
- **Tool Use**: https://docs.anthropic.com/en/docs/build-with-claude/tool-use

---

**Versión:** 1.0.0
**Última actualización:** 2025-12-08
