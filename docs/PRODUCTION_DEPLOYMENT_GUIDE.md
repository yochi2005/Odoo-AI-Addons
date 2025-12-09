# Guía Completa: Despliegue de Odoo a Producción en AWS

**De Desarrollo Local a Producción Funcional**

---

## 📑 Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Arquitectura de Producción](#2-arquitectura-de-producción)
3. [Preparación en AWS](#3-preparación-en-aws)
4. [Instalación del Servidor](#4-instalación-del-servidor)
5. [Configuración de Base de Datos](#5-configuración-de-base-de-datos)
6. [Despliegue de Odoo](#6-despliegue-de-odoo)
7. [Nginx y SSL](#7-nginx-y-ssl)
8. [Configuración de Correo](#8-configuración-de-correo)
9. [Configuración de Módulos](#9-configuración-de-módulos)
10. [Datos Maestros y Localización](#10-datos-maestros-y-localización)
11. [Módulos AI en Producción](#11-módulos-ai-en-producción)
12. [Backups y Monitoreo](#12-backups-y-monitoreo)
13. [Optimización](#13-optimización)

---

## 1. Introducción

### 1.1 ¿Qué necesitamos para producción?

Para que Odoo funcione completamente en producción necesitas:

**Infraestructura:**
- ✅ Servidor con IP pública (AWS EC2)
- ✅ Base de datos PostgreSQL
- ✅ Nginx como reverse proxy
- ✅ Certificado SSL (HTTPS)
- ✅ Dominio propio (ej: tuempresa.com)

**Servicios:**
- ✅ Servidor de correo (SMTP) para enviar emails
- ✅ Storage para archivos (S3 o similar)
- ✅ Backups automáticos

**Configuración:**
- ✅ Datos de la empresa configurados
- ✅ Plan de cuentas (contabilidad)
- ✅ Productos y servicios
- ✅ Clientes y proveedores
- ✅ Almacenes e inventarios
- ✅ Impuestos (IVA, retenciones, etc.)

---

## 2. Arquitectura de Producción

### 2.1 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERNET                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Route 53 (DNS)                                               │
│  tuempresa.com → IP Pública del servidor                      │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  AWS EC2 Instance (Ubuntu 22.04)                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Nginx (Puerto 80/443)                                 │  │
│  │  - Reverse Proxy                                       │  │
│  │  - SSL Termination (Let's Encrypt)                     │  │
│  │  - Compression                                         │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                         │                                     │
│                         ▼                                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Odoo Server (Puerto 8069)                             │  │
│  │  - Odoo 18.2                                           │  │
│  │  - Custom Addons (odoo_ai_tools)                       │  │
│  │  - Enterprise Modules                                  │  │
│  │  - Workers: 4-8                                        │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                         │                                     │
└─────────────────────────┼─────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  Amazon RDS PostgreSQL 14+                                    │
│  - Multi-AZ Deployment (Alta disponibilidad)                  │
│  - Automated Backups                                          │
│  - Read Replicas (opcional)                                   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Amazon S3                                                     │
│  - Filestore (archivos adjuntos)                              │
│  - Backups                                                     │
│  - Reportes generados                                          │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  Amazon SES (Simple Email Service)                            │
│  - Envío de correos                                           │
│  - Facturas, cotizaciones, notificaciones                     │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Componentes

| Servicio | AWS | Función |
|----------|-----|---------|
| Servidor | EC2 (t3.medium o superior) | Correr Odoo |
| Base de Datos | RDS PostgreSQL | Almacenar datos |
| DNS | Route 53 | Dominio → IP |
| Storage | S3 | Archivos y backups |
| Email | SES | Envío de correos |
| CDN | CloudFront (opcional) | Acelerar contenido estático |
| Balanceador | ALB (opcional) | Múltiples instancias |

---

## 3. Preparación en AWS

### 3.1 Crear Cuenta AWS

1. Ir a https://aws.amazon.com/
2. Crear cuenta (requiere tarjeta de crédito)
3. Habilitar MFA (autenticación de dos factores)

### 3.2 Configurar VPC y Seguridad

**Crear VPC:**
```bash
# VPC con subredes públicas y privadas
# Usar wizard de AWS: VPC with Public and Private Subnets
CIDR: 10.0.0.0/16
Public Subnet: 10.0.1.0/24
Private Subnet: 10.0.2.0/24
```

**Security Groups:**

**SG-Web (Nginx):**
```
Inbound:
- HTTP (80) desde 0.0.0.0/0
- HTTPS (443) desde 0.0.0.0/0
- SSH (22) desde TU_IP/32 (solo tu IP)

Outbound:
- Todo el tráfico
```

**SG-Odoo (Aplicación):**
```
Inbound:
- Puerto 8069 desde SG-Web (solo nginx)
- SSH (22) desde TU_IP/32

Outbound:
- PostgreSQL (5432) a SG-Database
- HTTPS (443) para APIs externas (Anthropic)
- SMTP (587/465) para correos
```

**SG-Database (PostgreSQL):**
```
Inbound:
- PostgreSQL (5432) desde SG-Odoo

Outbound:
- Ninguno (o restringido)
```

### 3.3 Crear Instancia EC2

**Especificaciones recomendadas:**

| Uso | Tipo | vCPUs | RAM | Storage |
|-----|------|-------|-----|---------|
| Desarrollo/Pruebas | t3.small | 2 | 2 GB | 30 GB |
| Producción (10-50 usuarios) | t3.medium | 2 | 4 GB | 50 GB |
| Producción (50-100 usuarios) | t3.large | 2 | 8 GB | 100 GB |
| Producción (100+ usuarios) | t3.xlarge | 4 | 16 GB | 200 GB |

**Pasos:**

1. **EC2 Dashboard → Launch Instance**

2. **Configuración:**
   - **Name:** odoo-production
   - **AMI:** Ubuntu Server 22.04 LTS
   - **Instance Type:** t3.medium (o superior)
   - **Key Pair:** Crear nuevo key pair (descargar .pem)
   - **Network:** Tu VPC
   - **Subnet:** Public Subnet
   - **Auto-assign Public IP:** Enable
   - **Security Group:** SG-Web + SG-Odoo
   - **Storage:** 50 GB gp3 (mejor performance que gp2)

3. **Launch Instance**

4. **Asignar Elastic IP:**
   ```bash
   # En AWS Console
   EC2 → Elastic IPs → Allocate Elastic IP
   # Asociar a tu instancia
   ```

### 3.4 Crear Base de Datos RDS

**Pasos:**

1. **RDS Dashboard → Create Database**

2. **Configuración:**
   - **Engine:** PostgreSQL 14.x
   - **Templates:** Production (o Free Tier para pruebas)
   - **DB Instance Identifier:** odoo-production-db
   - **Master Username:** odoo_admin
   - **Master Password:** [Contraseña segura - guárdala]
   - **DB Instance Class:** db.t3.micro (Free Tier) o db.t3.medium (Producción)
   - **Storage:** 20 GB gp3, con autoscaling hasta 100 GB
   - **VPC:** Tu VPC
   - **Subnet Group:** Private Subnets
   - **Public Access:** No
   - **VPC Security Group:** SG-Database
   - **Initial Database Name:** postgres
   - **Automated Backups:** Enable (7-35 días)
   - **Backup Window:** 03:00-04:00 (horario de bajo uso)

3. **Create Database**

4. **Guardar Endpoint:**
   ```
   Endpoint: odoo-production-db.xxxxx.us-east-1.rds.amazonaws.com
   Port: 5432
   ```

### 3.5 Configurar Route 53 (DNS)

**Si tienes dominio:**

1. **Route 53 → Hosted Zones → Create Hosted Zone**
   - Domain: tuempresa.com

2. **Crear registro A:**
   ```
   Name: tuempresa.com
   Type: A
   Value: [Tu Elastic IP]
   TTL: 300
   ```

3. **Actualizar nameservers en tu registrador de dominios**

**Si NO tienes dominio:**
- Puedes usar el IP público directamente (no recomendado para producción)
- O comprar dominio en Route 53 (~$12/año)

---

## 4. Instalación del Servidor

### 4.1 Conectar al Servidor

```bash
# Cambiar permisos del key
chmod 400 tu-key.pem

# Conectar vía SSH
ssh -i tu-key.pem ubuntu@[TU_ELASTIC_IP]
```

### 4.2 Actualizar Sistema

```bash
# Actualizar paquetes
sudo apt update && sudo apt upgrade -y

# Instalar utilidades
sudo apt install -y \
    git \
    curl \
    wget \
    build-essential \
    python3-pip \
    python3-dev \
    python3-venv \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    libjpeg-dev \
    libpq-dev \
    liblcms2-dev \
    libblas-dev \
    libatlas-base-dev \
    npm \
    nodejs \
    fonts-liberation \
    gdebi-core
```

### 4.3 Instalar Python 3.12

```bash
# Agregar PPA deadsnakes
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Instalar Python 3.12
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# Verificar versión
python3.12 --version
```

### 4.4 Instalar wkhtmltopdf (para PDFs)

```bash
# Descargar e instalar wkhtmltopdf
cd /tmp
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb
sudo gdebi -n wkhtmltox_0.12.6.1-2.jammy_amd64.deb

# Crear symlinks
sudo ln -s /usr/local/bin/wkhtmltopdf /usr/bin/
sudo ln -s /usr/local/bin/wkhtmltoimage /usr/bin/

# Verificar
wkhtmltopdf --version
```

### 4.5 Crear Usuario Odoo

```bash
# Crear usuario del sistema para Odoo
sudo adduser --system --home=/opt/odoo --group odoo

# Verificar
id odoo
```

---

## 5. Configuración de Base de Datos

### 5.1 Instalar Cliente PostgreSQL

```bash
# Instalar cliente PostgreSQL
sudo apt install -y postgresql-client-14

# Verificar
psql --version
```

### 5.2 Conectar a RDS y Crear Base de Datos

```bash
# Conectar a RDS (reemplazar con tu endpoint)
psql -h odoo-production-db.xxxxx.us-east-1.rds.amazonaws.com \
     -U odoo_admin \
     -d postgres

# En el prompt de PostgreSQL:
CREATE DATABASE odoo_production;
CREATE USER odoo WITH PASSWORD 'tu_password_seguro';
GRANT ALL PRIVILEGES ON DATABASE odoo_production TO odoo;

# Salir
\q
```

### 5.3 Probar Conexión

```bash
# Probar conexión con usuario odoo
psql -h odoo-production-db.xxxxx.us-east-1.rds.amazonaws.com \
     -U odoo \
     -d odoo_production

# Si funciona:
\l  # Listar bases de datos
\q  # Salir
```

---

## 6. Despliegue de Odoo

### 6.1 Clonar Repositorios

```bash
# Cambiar a usuario odoo
sudo su - odoo

# Crear estructura de directorios
mkdir -p /opt/odoo/{odoo,custom-addons,enterprise,config,logs,backups}

# Clonar Odoo Community
cd /opt/odoo
git clone --depth 1 --branch 18.0 https://github.com/odoo/odoo.git

# Clonar tus módulos custom
cd custom-addons
git clone git@github.com:yochi2005/Odoo-AI-Addons.git

# Si tienes Enterprise (opcional)
cd /opt/odoo
git clone --depth 1 --branch 18.0 [URL_ENTERPRISE] enterprise

# Salir de usuario odoo
exit
```

### 6.2 Crear Virtual Environment

```bash
# Como usuario odoo
sudo su - odoo

# Crear venv con Python 3.12
cd /opt/odoo
python3.12 -m venv venv

# Activar venv
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip setuptools wheel

# Instalar dependencias de Odoo
pip install -r odoo/requirements.txt

# Instalar dependencias adicionales
pip install anthropic boto3 psycopg2-binary

# Salir
exit
```

### 6.3 Crear Archivo de Configuración

```bash
# Como root
sudo nano /opt/odoo/config/odoo.conf
```

**Contenido:**

```ini
[options]
# Básico
admin_passwd = TU_MASTER_PASSWORD_SUPER_SEGURO
db_host = odoo-production-db.xxxxx.us-east-1.rds.amazonaws.com
db_port = 5432
db_user = odoo
db_password = tu_password_seguro
db_name = odoo_production
db_filter = ^odoo_production$

# Paths
addons_path = /opt/odoo/odoo/addons,/opt/odoo/enterprise,/opt/odoo/custom-addons/Odoo-AI-Addons
data_dir = /opt/odoo/.local/share/Odoo

# Server
http_port = 8069
workers = 4
max_cron_threads = 2
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_request = 8192
limit_time_cpu = 600
limit_time_real = 1200

# Logging
logfile = /opt/odoo/logs/odoo.log
log_level = info
log_handler = :INFO

# Security
proxy_mode = True
xmlrpc = False
xmlrpcs = True

# Email (configuraremos después)
# email_from = noreply@tuempresa.com
# smtp_server = email-smtp.us-east-1.amazonaws.com
# smtp_port = 587
# smtp_ssl = True
# smtp_user = TU_SES_SMTP_USERNAME
# smtp_password = TU_SES_SMTP_PASSWORD
```

**Ajustar permisos:**

```bash
sudo chown odoo:odoo /opt/odoo/config/odoo.conf
sudo chmod 640 /opt/odoo/config/odoo.conf
```

### 6.4 Calcular Workers Óptimos

**Fórmula:**
```
workers = (número_de_cores * 2) + 1
```

**Ejemplos:**
- t3.medium (2 cores): workers = 5
- t3.large (2 cores): workers = 5
- t3.xlarge (4 cores): workers = 9

**Memoria por worker:**
```
limit_memory_hard = (RAM_total - 1GB) / workers
```

### 6.5 Crear Systemd Service

```bash
sudo nano /etc/systemd/system/odoo.service
```

**Contenido:**

```ini
[Unit]
Description=Odoo 18 Production
Documentation=https://www.odoo.com/documentation/18.0
After=network.target postgresql.service

[Service]
Type=simple
User=odoo
Group=odoo
Environment="PATH=/opt/odoo/venv/bin"
ExecStart=/opt/odoo/venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /opt/odoo/config/odoo.conf
WorkingDirectory=/opt/odoo
StandardOutput=journal+console
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Habilitar e iniciar:**

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar inicio automático
sudo systemctl enable odoo

# Iniciar Odoo
sudo systemctl start odoo

# Verificar estado
sudo systemctl status odoo

# Ver logs en tiempo real
sudo journalctl -u odoo -f
```

### 6.6 Verificar que Funciona

```bash
# Verificar puerto
sudo netstat -tlnp | grep 8069

# Deberías ver:
tcp  0  0.0.0.0:8069  0.0.0.0:*  LISTEN  [PID]/python3

# Probar con curl
curl http://localhost:8069

# Debería retornar HTML de Odoo
```

---

## 7. Nginx y SSL

### 7.1 Instalar Nginx

```bash
sudo apt install -y nginx
```

### 7.2 Configurar Nginx para Odoo

```bash
sudo nano /etc/nginx/sites-available/odoo
```

**Contenido:**

```nginx
# Upstream para Odoo
upstream odoo {
    server 127.0.0.1:8069;
}

upstream odoochat {
    server 127.0.0.1:8072;
}

# Mapeo de headers
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

# HTTP → HTTPS redirect
server {
    listen 80;
    server_name tuempresa.com www.tuempresa.com;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect todo a HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name tuempresa.com www.tuempresa.com;

    # SSL certificates (configuraremos con Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/tuempresa.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tuempresa.com/privkey.pem;
    ssl_session_timeout 30m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Logs
    access_log /var/log/nginx/odoo.access.log;
    error_log /var/log/nginx/odoo.error.log;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy settings
    proxy_read_timeout 720s;
    proxy_connect_timeout 720s;
    proxy_send_timeout 720s;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_redirect off;

    # Max upload size
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_types text/css text/scss text/plain text/xml application/xml application/json application/javascript;
    gzip_min_length 1000;

    # Odoo backend
    location / {
        proxy_pass http://odoo;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }

    # Longpolling (chat)
    location /longpolling {
        proxy_pass http://odoochat;
    }

    # Cache static files
    location ~* /web/static/ {
        proxy_cache_valid 200 60m;
        proxy_buffering on;
        expires 864000;
        proxy_pass http://odoo;
    }
}
```

**Habilitar sitio:**

```bash
# Crear symlink
sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/

# Eliminar default
sudo rm /etc/nginx/sites-enabled/default

# Probar configuración
sudo nginx -t

# Si está OK, recargar
sudo systemctl reload nginx
```

### 7.3 Instalar Certbot (Let's Encrypt)

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tuempresa.com -d www.tuempresa.com

# Seguir el wizard:
# - Email: tu_email@example.com
# - Aceptar términos: Yes
# - Compartir email: No
# - Redirect HTTP → HTTPS: Yes (opción 2)

# Certbot actualizará automáticamente la configuración de Nginx
```

**Renovación automática:**

```bash
# Verificar timer de renovación
sudo systemctl status certbot.timer

# Probar renovación
sudo certbot renew --dry-run

# Si funciona, la renovación será automática cada 12 horas
```

### 7.4 Verificar HTTPS

```bash
# Acceder desde navegador
https://tuempresa.com

# Deberías ver:
# - Candado verde (SSL válido)
# - Página de configuración de Odoo
```

---

## 8. Configuración de Correo

### 8.1 Configurar Amazon SES

**Paso 1: Verificar Dominio**

1. **SES Console → Verified Identities → Create Identity**
2. **Identity Type:** Domain
3. **Domain:** tuempresa.com
4. **Advanced DKIM settings:** Easy DKIM (RSA_2048_BIT)
5. **Create Identity**

6. **Copiar registros DNS:**
   - 3 registros CNAME para DKIM
   - 1 registro TXT para SPF
   - 1 registro TXT para DMARC

7. **Agregar en Route 53:**
   ```
   # DKIM (3 registros)
   xxx._domainkey.tuempresa.com → CNAME → xxx.dkim.amazonses.com

   # SPF
   tuempresa.com → TXT → "v=spf1 include:amazonses.com ~all"

   # DMARC
   _dmarc.tuempresa.com → TXT → "v=DMARC1; p=none; rua=mailto:dmarc@tuempresa.com"
   ```

8. **Esperar verificación (puede tardar hasta 72 horas)**

**Paso 2: Salir del Sandbox**

```
1. SES Console → Account Dashboard
2. Click "Request production access"
3. Llenar formulario:
   - Use case: Transactional emails (facturas, notificaciones)
   - Website: https://tuempresa.com
   - Descripción: "Odoo ERP system sending invoices, quotes, and notifications"
   - Volumen esperado: XXX emails/día
   - Manejo de bounces: Implemented
4. Submit

Aprobación tarda 24-48 horas
```

**Paso 3: Crear Credenciales SMTP**

1. **SES → SMTP Settings**
2. **Create SMTP Credentials**
3. **IAM User Name:** odoo-ses-smtp
4. **Create**
5. **¡GUARDAR CREDENCIALES!**
   ```
   SMTP Username: AKIAXXXXXXXXXXXXXXXX
   SMTP Password: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```

6. **Anotar también:**
   ```
   SMTP Endpoint: email-smtp.us-east-1.amazonaws.com
   SMTP Port: 587 (TLS) o 465 (SSL)
   ```

### 8.2 Configurar Odoo para Enviar Correos

**Actualizar odoo.conf:**

```bash
sudo nano /opt/odoo/config/odoo.conf
```

**Descomentar y configurar:**

```ini
# Email configuration
email_from = noreply@tuempresa.com
smtp_server = email-smtp.us-east-1.amazonaws.com
smtp_port = 587
smtp_ssl = True
smtp_user = AKIAXXXXXXXXXXXXXXXX
smtp_password = XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Reiniciar Odoo:**

```bash
sudo systemctl restart odoo
```

### 8.3 Probar Envío desde Odoo

1. **Acceder a Odoo:** https://tuempresa.com
2. **Configurar base de datos** (si es primera vez)
3. **Settings → Technical → Email → Outgoing Mail Servers**
4. **Verificar configuración**
5. **Click "Test Connection"**
6. **Enviar email de prueba**

---

## 9. Configuración de Módulos

### 9.1 Instalar Módulos Básicos

**Desde Odoo UI:**

1. **Apps → Update Apps List**
2. **Buscar e instalar:**
   - **Sales Management** (sale_management)
   - **Invoicing** (account)
   - **Inventory** (stock)
   - **CRM** (crm)
   - **Purchase** (purchase)
   - **Project** (project)
   - **Contacts** (contacts)
   - **Website** (website) - opcional
   - **AI Tools** (odoo_ai_tools) - tu módulo custom

### 9.2 Configurar Sales (Ventas)

**Configuración General:**

1. **Sales → Configuration → Settings**

**Activar:**
- ✅ Quotation & Orders → Quotation Templates
- ✅ Quotation & Orders → Online Signature
- ✅ Quotation & Orders → Online Payment
- ✅ Pricing → Pricelists
- ✅ Pricing → Discounts
- ✅ Invoicing → Invoice Orders

**Crear Productos:**

1. **Sales → Products → Products → Create**

**Ejemplo: Producto de Servicio**
```
Nombre: Consultoría IT
Tipo de Producto: Service
Precio de Venta: $1,500.00
Costo: $500.00
Categoría: Services
Impuestos Cliente: IVA 16%
Descripción: Consultoría técnica especializada en infraestructura
```

**Ejemplo: Producto Físico**
```
Nombre: Laptop Dell XPS 15
Tipo de Producto: Storable Product
Precio de Venta: $25,000.00
Costo: $18,000.00
Categoría: Computers & Electronics
Impuestos Cliente: IVA 16%
Código Interno: LAPTOP-001
Código de Barras: 123456789
```

### 9.3 Configurar Accounting (Contabilidad)

**Configuración Inicial:**

1. **Accounting → Configuration → Settings**

**Fiscal Localization: México**
- País: México
- **Instalar Localización Mexicana:**
  - Accounting → Configuration → Chart of Accounts
  - Seleccionar: "México - Plan de Cuentas General"
  - Install

**Configurar Empresa:**

1. **Settings → Companies → Update Info**
```
Nombre: Tu Empresa S.A. de C.V.
RFC: XAXX010101000
Dirección: Calle 123, Col. Centro
Ciudad: Ciudad de México
Estado: Ciudad de México
CP: 01000
País: México
Teléfono: +52 55 1234 5678
Email: contacto@tuempresa.com
Website: https://tuempresa.com
```

**Configurar Impuestos:**

1. **Accounting → Configuration → Taxes**

**IVA 16% (Venta):**
```
Nombre: IVA 16% Ventas
Tipo: Sales
Alcance: Invoices
Cálculo: Percentage of Price
Porcentaje: 16%
Cuenta: IVA por Pagar
```

**IVA 16% (Compra):**
```
Nombre: IVA 16% Compras
Tipo: Purchase
Alcance: Bills
Cálculo: Percentage of Price
Porcentaje: 16%
Cuenta: IVA Acreditable
```

**ISR Retención 10%:**
```
Nombre: Retención ISR 10%
Tipo: Purchase
Alcance: Bills
Cálculo: Percentage of Price
Porcentaje: -10%  (negativo = retención)
Cuenta: ISR Retenido por Pagar
```

**Configurar Diarios:**

1. **Accounting → Configuration → Journals**

**Diario de Ventas:**
```
Nombre: Facturas de Cliente
Tipo: Sale
Cuenta por Defecto: Cuentas por Cobrar Clientes
Secuencia: FAC/2025/0001
```

**Diario de Compras:**
```
Nombre: Facturas de Proveedor
Tipo: Purchase
Cuenta por Defecto: Cuentas por Pagar Proveedores
Secuencia: BILL/2025/0001
```

**Diario de Banco:**
```
Nombre: Banco Principal
Tipo: Bank
Cuenta de Banco: [Configurar cuenta bancaria]
```

### 9.4 Configurar Inventory (Inventario)

**Configuración:**

1. **Inventory → Configuration → Settings**

**Activar:**
- ✅ Operations → Multi-Step Routes
- ✅ Operations → Storage Locations
- ✅ Operations → Packages
- ✅ Traceability → Lots & Serial Numbers
- ✅ Traceability → Expiration Dates
- ✅ Valuation → Automated Inventory Valuation

**Crear Almacén:**

1. **Inventory → Configuration → Warehouses**
```
Nombre: Almacén Principal
Nombre Corto: ALM-01
Dirección: [Dirección física del almacén]
```

**Configurar Ubicaciones:**

1. **Inventory → Configuration → Locations**
```
Ubicaciones de Stock:
- Almacén Principal / Stock
- Almacén Principal / Stock / Estantería A
- Almacén Principal / Stock / Estantería B
- Almacén Principal / Stock / Productos Dañados
```

**Crear Rutas de Reabastecimiento:**

1. **Inventory → Configuration → Routes**
```
Nombre: Compra → Stock
Reglas:
  - Si: Cantidad en stock < Mínimo
  - Entonces: Crear Orden de Compra
  - Proveedor: Proveedor Preferido
```

### 9.5 Crear Datos Maestros

**Clientes:**

1. **Contacts → Create**
```
Nombre: Cliente Ejemplo S.A. de C.V.
Tipo: Company
RFC: XAXX010101000
Dirección: Calle 456, Col. Industrial
CP: 01020
Ciudad: Ciudad de México
Teléfono: +52 55 9876 5432
Email: cliente@ejemplo.com
Categoría: Cliente Premium
Términos de Pago: 30 días
Lista de Precios: Pública
```

**Proveedores:**

1. **Contacts → Create**
```
Nombre: Proveedor Tech S.A.
Tipo: Company
RFC: PROV010101AAA
Es Proveedor: ✅
Dirección: Av. Tecnología 789
Email: ventas@proveedortech.com
Términos de Pago: 15 días
```

---

## 10. Datos Maestros y Localización

### 10.1 Configuración México (Facturación Electrónica)

**Instalar Módulo de Facturación Electrónica:**

1. **Apps → Search: "Mexico"**
2. **Instalar:**
   - **l10n_mx**: México - Contabilidad
   - **l10n_mx_edi**: México - Factura Electrónica (CFDI)
   - **l10n_mx_edi_40**: México - CFDI 4.0

**Configurar PAC:**

1. **Accounting → Configuration → Settings**
2. **Electronic Invoicing (Mexico)**
   - PAC: Seleccionar proveedor (ej: SW Sapien, Finkok, etc.)
   - Certificados: Subir .cer y .key del SAT
   - Contraseña Llave Privada: [password del .key]

**Configurar Regímenes Fiscales:**

```
Accounting → Configuration → Settings → Electronic Invoicing

Régimen Fiscal de la Empresa: 601 (General de Ley Personas Morales)

Otros régimenes disponibles:
- 612: Personas Físicas con Actividades Empresariales
- 605: Sueldos y Salarios
- 608: Demás ingresos
- 626: Régimen Simplificado de Confianza
```

**Configurar Uso de CFDI por Cliente:**

1. **Contacts → [Cliente] → Sales & Purchase**
```
Uso de CFDI: G03 (Gastos en General)

Otros usos comunes:
- G01: Adquisición de Mercancías
- G02: Devoluciones, descuentos o bonificaciones
- I01: Construcciones
- I02: Mobiliario y equipo de oficina
- I03: Equipo de transporte
- I04: Equipo de cómputo
- P01: Por definir
```

### 10.2 Crear Catálogo de Productos Completo

**Categorías de Productos:**

1. **Sales → Configuration → Product Categories**

```
- Servicios
  - Consultoría
  - Soporte Técnico
  - Capacitación

- Hardware
  - Computadoras
  - Periféricos
  - Componentes

- Software
  - Licencias
  - Suscripciones

- Consumibles
  - Papelería
  - Toner
  - Accesorios
```

**Productos de Ejemplo:**

**Servicio:**
```python
Nombre: Soporte Técnico Mensual
Categoría: Servicios → Soporte Técnico
Tipo: Service
Precio: $5,000.00
Impuestos: IVA 16%
Descripción: Soporte técnico 24/7 durante un mes
```

**Producto con Inventario:**
```python
Nombre: Mouse Logitech MX Master 3
Categoría: Hardware → Periféricos
Tipo: Storable Product
Código Interno: MOUSE-001
Código de Barras: 097855134660
Precio: $1,500.00
Costo: $900.00
Impuestos Venta: IVA 16%
Impuestos Compra: IVA 16%
Unidad de Medida: Pieza
Ubicación: Almacén Principal / Stock / Estantería A
Stock Mínimo: 5
Stock Máximo: 20
Proveedor Preferido: Proveedor Tech S.A.
```

### 10.3 Configurar Listas de Precios

1. **Sales → Configuration → Pricelists**

**Lista Pública:**
```
Nombre: Precio Público
Moneda: MXN
Reglas: Precio base del producto
```

**Lista Mayorista:**
```
Nombre: Precio Mayorista
Moneda: MXN
Reglas:
  - Si cantidad >= 10: Descuento 10%
  - Si cantidad >= 50: Descuento 15%
  - Si cantidad >= 100: Descuento 20%
```

**Lista VIP:**
```
Nombre: Clientes VIP
Moneda: MXN
Reglas:
  - Categoría "Servicios": Descuento 15%
  - Categoría "Hardware": Descuento 10%
  - Todos los demás: Descuento 5%
```

---

## 11. Módulos AI en Producción

### 11.1 Variables de Entorno para API Keys

**Crear archivo de environment:**

```bash
sudo nano /etc/odoo/environment
```

**Contenido:**

```bash
# Anthropic API Key
ANTHROPIC_API_KEY="sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# AWS Credentials (si usas S3)
AWS_ACCESS_KEY_ID="AKIAXXXXXXXXXXXXXXXX"
AWS_SECRET_ACCESS_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
AWS_DEFAULT_REGION="us-east-1"

# OpenAI (si usas también)
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**Proteger archivo:**

```bash
sudo chown odoo:odoo /etc/odoo/environment
sudo chmod 600 /etc/odoo/environment
```

**Actualizar systemd service:**

```bash
sudo nano /etc/systemd/system/odoo.service
```

**Agregar:**

```ini
[Service]
EnvironmentFile=/etc/odoo/environment
```

**Reiniciar:**

```bash
sudo systemctl daemon-reload
sudo systemctl restart odoo
```

### 11.2 Configurar AI Assistant en Producción

**Actualizar modelo ai.assistant:**

```python
# En models/ai_assistant.py

import os

class AIAssistant(models.Model):
    _name = 'ai.assistant'

    # Cambiar para usar variable de entorno
    def get_anthropic_api_key(self):
        # Prioridad: 1. Campo, 2. Var entorno, 3. Config
        if self.anthropic_api_key:
            return self.anthropic_api_key

        # Desde variable de entorno
        env_key = os.environ.get('ANTHROPIC_API_KEY')
        if env_key:
            return env_key

        # Desde configuración del sistema
        return self.env['ir.config_parameter'].sudo().get_param(
            'odoo_ai_tools.anthropic_api_key'
        )
```

### 11.3 Configuración Global de API Keys

1. **Settings → Technical → System Parameters**
2. **Create:**

```
Key: odoo_ai_tools.anthropic_api_key
Value: sk-ant-api03-xxxxxxxxxxxxxxxxxxxxx
```

### 11.4 Rate Limiting

**Implementar límite de requests:**

```python
# En claude_orchestrator.py

from datetime import datetime, timedelta
from functools import wraps

# Cache simple de rate limiting
_rate_limit_cache = {}

def rate_limit(max_calls=10, period=60):
    """Limitar llamadas a Claude."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = datetime.now()
            user_id = args[0] if args else 'anonymous'

            # Limpiar cache viejo
            cutoff = now - timedelta(seconds=period)
            _rate_limit_cache[user_id] = [
                ts for ts in _rate_limit_cache.get(user_id, [])
                if ts > cutoff
            ]

            # Verificar límite
            if len(_rate_limit_cache.get(user_id, [])) >= max_calls:
                raise Exception(
                    f"Rate limit exceeded. Max {max_calls} calls per {period} seconds."
                )

            # Registrar llamada
            if user_id not in _rate_limit_cache:
                _rate_limit_cache[user_id] = []
            _rate_limit_cache[user_id].append(now)

            return func(*args, **kwargs)
        return wrapper
    return decorator


class ClaudeOrchestrator:
    @rate_limit(max_calls=20, period=60)  # 20 llamadas por minuto
    def process_message(self, user_message):
        # ... código existente
```

---

## 12. Backups y Monitoreo

### 12.1 Configurar Backups Automáticos

**Crear script de backup:**

```bash
sudo nano /opt/odoo/bin/backup.sh
```

**Contenido:**

```bash
#!/bin/bash

# Configuración
BACKUP_DIR="/opt/odoo/backups"
DB_NAME="odoo_production"
DB_HOST="odoo-production-db.xxxxx.us-east-1.rds.amazonaws.com"
DB_USER="odoo"
DB_PASSWORD="tu_password"
S3_BUCKET="s3://tu-empresa-odoo-backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Crear directorio si no existe
mkdir -p $BACKUP_DIR

# Backup de base de datos
echo "Starting database backup..."
PGPASSWORD=$DB_PASSWORD pg_dump \
    -h $DB_HOST \
    -U $DB_USER \
    -F c \
    -b \
    -v \
    -f "$BACKUP_DIR/odoo_${DATE}.dump" \
    $DB_NAME

# Comprimir filestore
echo "Backing up filestore..."
tar -czf "$BACKUP_DIR/filestore_${DATE}.tar.gz" \
    /opt/odoo/.local/share/Odoo/filestore/$DB_NAME

# Subir a S3
echo "Uploading to S3..."
aws s3 cp "$BACKUP_DIR/odoo_${DATE}.dump" "$S3_BUCKET/"
aws s3 cp "$BACKUP_DIR/filestore_${DATE}.tar.gz" "$S3_BUCKET/"

# Limpiar backups locales viejos
echo "Cleaning old local backups..."
find $BACKUP_DIR -name "*.dump" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

# Limpiar backups S3 viejos
echo "Cleaning old S3 backups..."
aws s3 ls $S3_BUCKET/ | while read -r line; do
    createDate=$(echo $line | awk {'print $1" "$2'})
    createDate=$(date -d "$createDate" +%s)
    olderThan=$(date -d "$RETENTION_DAYS days ago" +%s)
    if [[ $createDate -lt $olderThan ]]; then
        fileName=$(echo $line | awk {'print $4'})
        if [[ $fileName != "" ]]; then
            aws s3 rm $S3_BUCKET/$fileName
        fi
    fi
done

echo "Backup completed: $DATE"
```

**Permisos:**

```bash
sudo chmod +x /opt/odoo/bin/backup.sh
sudo chown odoo:odoo /opt/odoo/bin/backup.sh
```

**Configurar cron:**

```bash
sudo crontab -e -u odoo
```

**Agregar:**

```cron
# Backup diario a las 2 AM
0 2 * * * /opt/odoo/bin/backup.sh >> /opt/odoo/logs/backup.log 2>&1

# Backup cada 6 horas (adicional para seguridad)
0 */6 * * * /opt/odoo/bin/backup.sh >> /opt/odoo/logs/backup.log 2>&1
```

### 12.2 Monitoreo con CloudWatch

**Instalar CloudWatch Agent:**

```bash
# Descargar agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb

# Instalar
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
```

**Configurar:**

```bash
sudo nano /opt/aws/amazon-cloudwatch-agent/etc/config.json
```

**Contenido:**

```json
{
  "metrics": {
    "namespace": "Odoo/Production",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          {
            "name": "cpu_usage_idle",
            "rename": "CPU_IDLE",
            "unit": "Percent"
          }
        ],
        "totalcpu": false
      },
      "disk": {
        "measurement": [
          {
            "name": "used_percent",
            "rename": "DISK_USED",
            "unit": "Percent"
          }
        ],
        "resources": [
          "*"
        ]
      },
      "mem": {
        "measurement": [
          {
            "name": "mem_used_percent",
            "rename": "MEM_USED",
            "unit": "Percent"
          }
        ]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/opt/odoo/logs/odoo.log",
            "log_group_name": "/odoo/production",
            "log_stream_name": "{instance_id}/odoo"
          },
          {
            "file_path": "/var/log/nginx/odoo.access.log",
            "log_group_name": "/odoo/production",
            "log_stream_name": "{instance_id}/nginx-access"
          },
          {
            "file_path": "/var/log/nginx/odoo.error.log",
            "log_group_name": "/odoo/production",
            "log_stream_name": "{instance_id}/nginx-error"
          }
        ]
      }
    }
  }
}
```

**Iniciar agent:**

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

### 12.3 Crear Alarmas CloudWatch

**Alarma de CPU Alta:**

```bash
aws cloudwatch put-metric-alarm \
    --alarm-name odoo-high-cpu \
    --alarm-description "CPU > 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/EC2 \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:odoo-alerts
```

**Alarma de Memoria Alta:**

```bash
aws cloudwatch put-metric-alarm \
    --alarm-name odoo-high-memory \
    --alarm-description "Memory > 85%" \
    --metric-name MEM_USED \
    --namespace Odoo/Production \
    --statistic Average \
    --period 300 \
    --threshold 85 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:odoo-alerts
```

---

## 13. Optimización

### 13.1 Optimización de PostgreSQL

**Conectar a RDS y optimizar:**

```sql
-- Configuración óptima para RDS
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

-- Reiniciar RDS instance para aplicar cambios
```

### 13.2 Optimización de Odoo

**odoo.conf optimizado:**

```ini
[options]
# Workers (ajustar según CPU)
workers = 5
max_cron_threads = 2

# Limites de memoria (ajustar según RAM)
limit_memory_hard = 2684354560  # 2.5 GB
limit_memory_soft = 2147483648  # 2 GB

# Timeouts
limit_time_cpu = 600     # 10 minutos
limit_time_real = 1200   # 20 minutos
limit_request = 8192

# Database pooling
db_maxconn = 64
db_template = template0

# Logging
log_level = warn  # Solo warnings y errores en producción
logrotate = True

# Cache
session_gc = True
```

### 13.3 Nginx Caching

**Agregar a configuración Nginx:**

```nginx
# Cache de proxy
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=odoo_cache:10m max_size=1g inactive=60m use_temp_path=off;

server {
    # ... configuración existente ...

    location /web/static/ {
        proxy_cache odoo_cache;
        proxy_cache_valid 200 60m;
        proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
        add_header X-Cache-Status $upstream_cache_status;
        proxy_pass http://odoo;
    }
}
```

---

## 14. Checklist Final de Producción

### ✅ Infraestructura
- [ ] EC2 instance corriendo
- [ ] RDS PostgreSQL configurado
- [ ] Elastic IP asignado
- [ ] Security Groups configurados
- [ ] Route 53 DNS configurado
- [ ] SSL certificado instalado

### ✅ Odoo
- [ ] Odoo 18.2 instalado
- [ ] Módulos instalados (sales, accounting, inventory, AI)
- [ ] Workers configurados correctamente
- [ ] Systemd service activo
- [ ] Logs funcionando

### ✅ Correo
- [ ] SES verificado
- [ ] Fuera de sandbox
- [ ] SMTP configurado en odoo.conf
- [ ] Email de prueba enviado exitosamente

### ✅ Datos
- [ ] Empresa configurada (RFC, dirección, etc.)
- [ ] Plan de cuentas instalado
- [ ] Impuestos configurados (IVA, retenciones)
- [ ] Productos creados
- [ ] Clientes/proveedores agregados
- [ ] Almacenes configurados

### ✅ Seguridad
- [ ] Master password fuerte
- [ ] SSL activo (HTTPS)
- [ ] Backups automáticos configurados
- [ ] API keys en variables de entorno
- [ ] Firewall configurado
- [ ] MFA habilitado para admin

### ✅ Monitoreo
- [ ] CloudWatch agent instalado
- [ ] Alarmas configuradas
- [ ] Logs centralizados
- [ ] Backup alerts activos

---

## 15. Uso Real del Sistema

### 15.1 Crear Primera Cotización

1. **Sales → Quotations → Create**
```
Cliente: Cliente Ejemplo S.A.
Productos:
  - Laptop Dell XPS 15 x 2 = $50,000.00
  - Soporte Técnico Mensual x 3 = $15,000.00
Subtotal: $65,000.00
IVA 16%: $10,400.00
Total: $75,400.00
```

2. **Send by Email** (usando SES)
3. **Customer Confirms → Confirm Sale**
4. **Create Invoice**
5. **Send Invoice by Email**

### 15.2 Generar Factura Electrónica (CFDI)

1. **Accounting → Customers → Invoices**
2. **Abrir factura → Validate → Generate CFDI**
3. **Sistema automáticamente:**
   - Genera XML
   - Firma con certificados del SAT
   - Envía a PAC para timbrado
   - Recibe UUID
   - Guarda XML timbrado
   - Envía por email al cliente

### 15.3 Usar AI Assistant en Producción

1. **AI Assistant → Conversations → Create**
2. **Ingresar API key** (o usar global)
3. **Mensajes de ejemplo:**

```
"Genera un reporte de ventas del último mes"
→ Claude llama a generate_sales_report
→ Retorna datos agrupados

"¿Qué productos necesitan reabastecimiento?"
→ Claude llama a detect_restock_needs
→ Lista productos con stock bajo

"Crea facturas de las últimas 5 órdenes de venta"
→ Claude llama a create_invoice_from_sales
→ Genera facturas draft

"Envía por correo las cotizaciones pendientes a los clientes"
→ Claude usa herramientas de Odoo para enviar emails
```

---

## 16. Costos Estimados AWS (Mensual)

| Servicio | Especificación | Costo Aprox. |
|----------|---------------|--------------|
| EC2 t3.medium | 2 vCPU, 4 GB RAM | $30 |
| RDS db.t3.medium | PostgreSQL 14, 20 GB | $35 |
| EBS Storage | 100 GB gp3 | $8 |
| S3 Storage | 50 GB | $1 |
| Data Transfer | 100 GB out | $9 |
| Route 53 | 1 hosted zone | $0.50 |
| SES | 10,000 emails | $1 |
| Backups (S3) | 100 GB | $2 |
| **TOTAL** | | **~$86/mes** |

**Nota:** Costos pueden variar según región y uso real.

---

## 17. Siguientes Pasos

**Semana 1:**
- [x] Configurar infraestructura AWS
- [x] Instalar Odoo
- [x] Configurar correo

**Semana 2:**
- [ ] Migrar datos desde desarrollo
- [ ] Configurar todos los módulos
- [ ] Capacitar usuarios

**Semana 3:**
- [ ] Testing completo
- [ ] Ajustes finos
- [ ] Go live

**Mantenimiento Continuo:**
- [ ] Backups diarios
- [ ] Monitoreo semanal
- [ ] Updates mensuales
- [ ] Optimización trimestral

---

**Fin de Guía de Producción**

¿Tienes alguna pregunta sobre algún paso específico?
