# Guía Completa: Cómo Hacer que Odoo Funcione Realmente

**De la Instalación a la Operación: Configuración Funcional de Odoo 18**

---

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Configuración Inicial de la Empresa](#2-configuración-inicial-de-la-empresa)
3. [Configuración de Correo Saliente (SMTP)](#3-configuración-de-correo-saliente-smtp)
4. [Activación de Módulos Necesarios](#4-activación-de-módulos-necesarios)
5. [Configuración del Módulo de Ventas](#5-configuración-del-módulo-de-ventas)
6. [Configuración del Módulo de Contabilidad](#6-configuración-del-módulo-de-contabilidad)
7. [Creación de Datos Maestros](#7-creación-de-datos-maestros)
8. [Flujo Completo: Cotización → Venta → Factura](#8-flujo-completo-cotización--venta--factura)
9. [Configuración de Inventario](#9-configuración-de-inventario)
10. [Órdenes de Compra](#10-órdenes-de-compra)
11. [Verificación de Funcionamiento](#11-verificación-de-funcionamiento)
12. [Troubleshooting](#12-troubleshooting)
13. [Checklist de Configuración](#13-checklist-de-configuración)
14. [Mejores Prácticas](#14-mejores-prácticas)

---

## 1. Introducción

### ¿Por qué esta guía?

Muchos desarrolladores y empresas instalan Odoo exitosamente, pero al intentar usarlo descubren que:
- ❌ Los correos no se envían
- ❌ Las facturas no tienen datos fiscales
- ❌ El inventario no se actualiza
- ❌ Los XML del SAT no se generan (México)
- ❌ Los documentos no tienen logo ni formato profesional

**Esta guía resuelve todos estos problemas.**

### ¿Qué aprenderás?

Al finalizar esta guía, tu Odoo podrá:
- ✅ Enviar correos automáticos (cotizaciones, facturas, recordatorios)
- ✅ Generar facturas con datos fiscales correctos
- ✅ Crear XML timbrados (CFDI 4.0 para México)
- ✅ Gestionar inventario en tiempo real
- ✅ Procesar órdenes de venta y compra
- ✅ Registrar asientos contables automáticamente

### Prerequisitos

- Odoo 18.2+ instalado y corriendo
- Acceso como administrador
- Para México: Certificados del SAT (.cer y .key) y cuenta en un PAC

---

## 2. Configuración Inicial de la Empresa

### 2.1. Acceder a Configuración de Empresa

**Ruta:** `Settings → General Settings → Companies → Update Info`

### 2.2. Datos Obligatorios

Configurar los siguientes campos:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Company Name** | Nombre legal de la empresa | "Tecnología Avanzada SA de CV" |
| **Address** | Dirección fiscal completa | "Av. Reforma 123, Piso 5" |
| **City** | Ciudad | "Ciudad de México" |
| **State** | Estado | "CDMX" |
| **ZIP** | Código postal | "06600" |
| **Country** | País | "Mexico" |
| **Phone** | Teléfono principal | "+52 55 5555 1234" |
| **Email** | Email de la empresa | "contacto@empresa.com" |
| **Website** | Sitio web | "https://www.empresa.com" |
| **Tax ID (RFC)** | RFC (México) | "TAV850101ABC" |
| **Currency** | Moneda | "MXN" (Peso Mexicano) |

### 2.3. Subir Logo

El logo aparecerá en:
- Facturas
- Cotizaciones
- Órdenes de compra
- Reportes
- Portal del cliente

**Formato recomendado:**
- Tamaño: 300x100 px o similar (proporción 3:1)
- Formato: PNG con fondo transparente
- Peso: < 100 KB

**Cómo subirlo:**
```
Settings → Companies → [Tu empresa] → Upload logo (botón con ícono de cámara)
```

### 2.4. Configurar Régimen Fiscal (México)

Para facturación electrónica:

```
Settings → Companies → [Tu empresa] → Sales & Purchase tab
```

**Campos importantes:**
- **Fiscal Regime (México):** Seleccionar el régimen que corresponda:
  - 601 - General de Ley Personas Morales
  - 612 - Personas Físicas con Actividades Empresariales
  - 625 - Régimen de las Actividades Empresariales con ingresos a través de Plataformas
  - etc.

### 2.5. Configurar Idioma y Zona Horaria

```
Settings → General Settings → Language & Time zone
```

- **Language:** Spanish (Mexico) / Español (México)
- **Timezone:** America/Mexico_City

**Guardar cambios.**

---

## 3. Configuración de Correo Saliente (SMTP)

### 3.1. ¿Por qué es Crítico?

**SIN SMTP CONFIGURADO, ODOO NO PUEDE:**
- Enviar cotizaciones por email
- Enviar facturas a clientes
- Enviar notificaciones
- Recuperar contraseñas
- Enviar recordatorios de pago

### 3.2. Acceder a Configuración SMTP

**Activar modo desarrollador:**
```
Settings → Activate Developer Mode (al final de la página)
```

**Ir a servidores de correo:**
```
Settings → Technical → Email → Outgoing Mail Servers
```

### 3.3. Opción A: Gmail (Desarrollo/Pruebas)

⚠️ **No recomendado para producción** (límite de 500 emails/día)

**Crear nuevo servidor SMTP:**

```
Name: Gmail SMTP
Description: Servidor de correo Gmail para desarrollo
SMTP Server: smtp.gmail.com
SMTP Port: 587
Connection Security: TLS (STARTTLS)
Username: tu-email@gmail.com
Password: [App Password - NO tu contraseña normal]
From Filter: tu-email@gmail.com (opcional)
```

#### Obtener App Password de Gmail

1. Ve a https://myaccount.google.com/security
2. Habilita "2-Step Verification" si no está activado
3. Ve a https://myaccount.google.com/apppasswords
4. Selecciona:
   - App: Mail
   - Device: Other (Odoo)
5. Genera → Copia la contraseña de 16 caracteres
6. Pega esa contraseña en el campo "Password" de Odoo

#### Probar Conexión

```
[Botón "Test Connection"]
```

Deberías ver: ✅ **"Connection Test Succeeded! Everything seems properly set up!"**

### 3.4. Opción B: Amazon SES (Producción)

✅ **Recomendado para producción** (escalable, confiable, económico)

#### Prerequisitos

1. Cuenta de AWS
2. Verificar dominio en SES
3. Salir del "sandbox mode" de SES
4. Crear credenciales SMTP en SES

#### Crear Credenciales SMTP en AWS SES

1. Ir a AWS Console → Amazon SES → SMTP Settings
2. Click en "Create My SMTP Credentials"
3. Descargar credenciales:
   - SMTP Username: AKIA...
   - SMTP Password: BMrG...

#### Configurar en Odoo

```
Name: Amazon SES
Description: Servidor SMTP producción
SMTP Server: email-smtp.us-east-1.amazonaws.com
SMTP Port: 587
Connection Security: TLS (STARTTLS)
Username: AKIAXXXXXXXXXXXXXXXX
Password: BMrGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
From Filter: noreply@tuempresa.com
```

**Importante:** El "From Filter" debe ser un email de un dominio verificado en SES.

### 3.5. Opción C: Servidor SMTP Propio

Si tienes tu propio servidor de correo:

```
SMTP Server: smtp.tudominio.com
SMTP Port: 587 (TLS) o 465 (SSL)
Connection Security: TLS o SSL según tu servidor
Username: correo@tudominio.com
Password: [Tu contraseña]
```

### 3.6. Configurar Email Predeterminado

En `odoo.conf` o en la configuración de la empresa:

```ini
[options]
email_from = noreply@tuempresa.com
```

Este será el remitente predeterminado para emails automáticos.

### 3.7. Verificar Logs de Email

Después de enviar un correo de prueba:

```
Settings → Technical → Email → Emails
```

Estados posibles:
- **Sent:** ✅ Enviado exitosamente
- **Bounced:** ❌ Rebotado (email inválido)
- **Exception:** ❌ Error de conexión SMTP
- **Outgoing:** ⏳ En cola para envío

---

## 4. Activación de Módulos Necesarios

### 4.1. Acceder a Apps

```
Apps (menú principal)
```

Si no ves el menú "Apps", actívalo:
```
Settings → Users & Companies → Users → [Tu usuario]
→ Technical Settings → Administration: "Access Rights"
```

### 4.2. Módulos Esenciales

#### Ventas
```
App: Sales
Technical Name: sale_management
Descripción: Gestión de cotizaciones, órdenes de venta, clientes
```

#### Contabilidad
```
App: Invoicing o Accounting
Technical Name: account
Descripción: Facturación, contabilidad, impuestos, pagos
```

#### Inventario
```
App: Inventory
Technical Name: stock
Descripción: Gestión de almacenes, movimientos de stock, entregas
```

#### Compras (opcional)
```
App: Purchase
Technical Name: purchase
Descripción: Órdenes de compra, gestión de proveedores
```

#### CRM (opcional)
```
App: CRM
Technical Name: crm
Descripción: Gestión de oportunidades, pipeline de ventas
```

### 4.3. Módulos para México (Facturación Electrónica)

#### Localización Mexicana
```
App: Mexico - Accounting
Technical Name: l10n_mx
Descripción: Plan contable mexicano, impuestos, configuración fiscal
```

**Incluye:**
- Plan de cuentas según normativa mexicana
- Impuestos (IVA 16%, IVA 0%, IEPS, ISR)
- Catálogos del SAT

#### Facturación Electrónica (CFDI)
```
App: EDI for Mexico
Technical Name: l10n_mx_edi
Descripción: Generación de XML CFDI 4.0, timbrado con PAC
```

**Incluye:**
- Generación de XML CFDI 4.0
- Integración con PACs (Finkok, SW Sapien, etc.)
- Addendas
- Complemento de pagos
- Carta porte

### 4.4. Instalar Módulos

Para cada módulo:
1. Buscar por nombre
2. Click en el módulo
3. Click en "Install" o "Activate"
4. Esperar a que termine la instalación
5. Click en "Apply" si se solicita

⚠️ **Algunos módulos requieren reiniciar el servidor:**
```bash
sudo systemctl restart odoo
```

---

## 5. Configuración del Módulo de Ventas

### 5.1. Acceder a Configuración

```
Sales → Configuration → Settings
```

### 5.2. Quotations & Orders

#### A. Quotation Templates
```
☑ Quotation Templates
```

**Beneficio:** Crear plantillas de cotización reutilizables con productos predefinidos.

**Ejemplo de uso:**
- Plantilla "Paquete Básico Web": Hosting + Dominio + Diseño básico
- Plantilla "Paquete Premium Web": Todo lo anterior + SEO + Mantenimiento

#### B. Online Signature
```
☑ Online Signature
```

**Beneficio:** El cliente puede firmar la cotización digitalmente desde su navegador.

**Flujo:**
1. Envías cotización por email
2. Cliente abre link
3. Cliente firma digitalmente
4. Odoo convierte automáticamente a orden de venta

#### C. Online Payment
```
☑ Online Payment
```

**Beneficio:** El cliente puede pagar directamente desde la cotización.

**Requiere configurar:**
- Payment Providers (Stripe, PayPal, Mercado Pago, etc.)
```
Sales → Configuration → Payment Providers
```

#### D. Pro-forma Invoice
```
☑ Pro-forma Invoice
```

**Beneficio:** Generar facturas pro-forma (cotizaciones con formato de factura).

### 5.3. Shipping

#### A. Delivery Methods
```
☑ Delivery Methods
```

**Configurar métodos de envío:**
```
Sales → Configuration → Delivery → Shipping Methods
```

Ejemplos:
- **Entrega en sitio:** $0.00
- **Envío nacional:** $150.00 fijo
- **Envío express:** $300.00 fijo
- **Basado en peso:** Tabla de precios según kg

### 5.4. Pricing

#### A. Discounts
```
☑ Discounts
```

**Beneficio:** Aplicar descuentos en líneas de cotización.

Ejemplo:
```
Product: Laptop
Price: $15,000.00
Discount: 10%
Subtotal: $13,500.00
```

#### B. Pricelists
```
☑ Pricelists
```

**Beneficio:** Crear listas de precios diferentes según:
- Cliente (mayorista vs minorista)
- Región (nacional vs exportación)
- Temporada (promoción navideña)

**Configurar:**
```
Sales → Configuration → Pricelists
```

Ejemplo:
```
Pricelist: Mayorista
Aplicar: Descuento 15% en todos los productos
Condición: Cantidad mínima 10 unidades
```

### 5.5. Invoicing

#### A. Automatic Invoice
```
☑ Automatic Invoice
Opciones:
  ○ Invoice what is ordered
  ○ Invoice what is delivered
```

**Recomendación:**
- **Servicios:** "Invoice what is ordered" (facturar al confirmar venta)
- **Productos físicos:** "Invoice what is delivered" (facturar al entregar)

#### B. Down Payments
```
☑ Down Payments
```

**Beneficio:** Solicitar anticipos antes de entregar.

Ejemplo:
```
Total de venta: $100,000.00
Anticipo: 50% = $50,000.00
Al entregar: 50% = $50,000.00
```

### 5.6. Guardar Configuración

```
[Save]
```

---

## 6. Configuración del Módulo de Contabilidad

### 6.1. Acceder a Configuración

```
Accounting → Configuration → Settings
```

### 6.2. Fiscal Localization

Si instalaste `l10n_mx`, ya tienes:
- ✅ Plan de cuentas mexicano
- ✅ Impuestos (IVA 16%, IVA 0%, etc.)
- ✅ Posiciones fiscales

Para revisar/modificar:
```
Accounting → Configuration → Chart of Accounts
```

### 6.3. Configurar Impuestos

#### A. Acceder a Impuestos

```
Accounting → Configuration → Taxes
```

#### B. IVA 16% (México)

Si no existe, crear:

```
Tax Name: IVA 16%
Tax Type: Sales
Tax Scope: Goods / Services
Tax Computation: Percentage of Price
Rate: 16%
Label on Invoices: IVA
Distribution for Invoices:
  Tax: 16%
  On Invoice: 16.00%

Tax Grids (SAT México):
  Base Account: Ventas con IVA
  Tax Account: IVA Trasladado
```

**Crear también para compras:**

```
Tax Name: IVA 16% Compra
Tax Type: Purchase
Tax Scope: Goods / Services
Tax Computation: Percentage of Price
Rate: 16%
```

#### C. IVA 0% (Tasa 0)

```
Tax Name: IVA 0%
Tax Type: Sales
Tax Computation: Percentage of Price
Rate: 0%
Label on Invoices: IVA 0%
```

**Usar para:**
- Exportaciones
- Alimentos básicos
- Medicinas

#### D. Retención ISR 10%

```
Tax Name: Retención ISR 10%
Tax Type: Sales
Tax Computation: Percentage of Price
Rate: -10% (negativo)
Label on Invoices: Ret. ISR
```

### 6.4. Configurar Diarios Contables

#### A. Acceder a Diarios

```
Accounting → Configuration → Journals
```

Odoo crea automáticamente:

| Diario | Código | Tipo | Uso |
|--------|--------|------|-----|
| Customer Invoices | INV | Sale | Facturas a clientes |
| Vendor Bills | BILL | Purchase | Facturas de proveedores |
| Bank | BNK1 | Bank | Movimientos bancarios |
| Cash | CSH1 | Cash | Movimientos de efectivo |
| Miscellaneous | MISC | General | Asientos manuales |

#### B. Configurar Numeración de Facturas

Ejemplo: `INV` (Customer Invoices)

```
Accounting → Configuration → Journals → Customer Invoices
→ Advanced Settings → Sequence
```

**Configuración recomendada:**

```
Sequence Name: Customer Invoices Sequence
Prefix: FAC/%(year)s/
Number padding: 5
Next Number: 1
```

**Resultado:**
- FAC/2025/00001
- FAC/2025/00002
- FAC/2026/00001 (reinicia cada año)

### 6.5. Configurar PAC (Facturación Electrónica México)

#### A. Prerequisitos

1. **Certificados del SAT:**
   - Archivo .cer (certificado público)
   - Archivo .key (llave privada)
   - Contraseña de la llave privada

2. **Cuenta en un PAC:**
   - Finkok
   - SW Sapien
   - Solución Factible
   - etc.

#### B. Configurar PAC en Odoo

```
Accounting → Configuration → Settings → Mexican Localization
```

**Campos:**

```
PAC: [Seleccionar tu PAC]
PAC Username: [Usuario del PAC]
PAC Password: [Contraseña del PAC]
Certificate (.cer): [Upload archivo .cer]
Certificate Key (.key): [Upload archivo .key]
Certificate Password: [Contraseña de la llave]
Environment: Production (o Test para pruebas)
```

#### C. Verificar Certificados

```
Accounting → Configuration → Settings → Mexican Localization
→ [Botón "Load Certificate"]
```

Debe mostrar:
- ✅ Certificate loaded successfully
- Fecha de expiración del certificado

#### D. Probar Conexión con PAC

Crear factura de prueba:
```
Accounting → Customers → Invoices → Create
```

Llenar datos mínimos y confirmar.

Si está bien configurado, el XML se timbra automáticamente al confirmar.

### 6.6. Configurar Métodos de Pago (México)

```
Accounting → Configuration → Payment Methods
```

**Catálogo SAT (requerido para CFDI):**

| Código | Método de Pago |
|--------|----------------|
| 01 | Efectivo |
| 02 | Cheque nominativo |
| 03 | Transferencia electrónica |
| 04 | Tarjeta de crédito |
| 28 | Tarjeta de débito |
| 99 | Por definir |

**Configurar cada uno:**

```
Name: Transferencia Electrónica
Code: 03_transfer
Type: Bank
SAT Payment Method: 03
```

### 6.7. Configurar Formas de Pago (SAT)

```
Accounting → Configuration → Settings → Mexican Localization
→ Payment Way Codes
```

Ejemplos:
- **PUE:** Pago en una sola exhibición
- **PPD:** Pago en parcialidades o diferido

### 6.8. Configurar Uso CFDI (Catálogo SAT)

```
Contacts → [Cliente] → Sales & Purchase tab → Fiscal Information
```

**Catálogo:**
- **G01:** Adquisición de mercancías
- **G02:** Devoluciones, descuentos o bonificaciones
- **G03:** Gastos en general
- **P01:** Por definir
- etc.

---

## 7. Creación de Datos Maestros

### 7.1. Crear Clientes

#### A. Acceder

```
Sales → Orders → Customers → Create
```

o

```
Contacts → Create
```

#### B. Datos Generales

```
Name: Juan Pérez SA de CV
Company Type: Company (para empresas) o Individual (personas físicas)
Is a Company: ☑ (si es empresa)
```

#### C. Datos de Contacto

```
Address:
  Street: Av. Insurgentes Sur 1234
  Street2: Col. Del Valle, Piso 3
  City: Ciudad de México
  State: Ciudad de México
  ZIP: 03100
  Country: Mexico

Phone: +52 55 5555 6789
Mobile: +52 55 1234 5678
Email: contacto@juanperez.com
Website: https://www.juanperez.com
```

#### D. Datos Fiscales (México)

```
Sales & Purchase tab:
  Tax ID (RFC): PERJ850101ABC
  Fiscal Regime: 612 - Personas Físicas con Actividades Empresariales
  CFDI Use: G03 - Gastos en general (predeterminado)
```

**RFC debe cumplir:**
- 12 caracteres (personas físicas) o 13 (morales)
- Formato válido según SAT
- Sin espacios ni caracteres especiales

#### E. Términos de Pago

```
Sales & Purchase tab:
  Payment Terms: 30 días neto
  Pricelist: Lista de precios estándar
```

#### F. Agregar Contactos Adicionales

Si el cliente tiene varios contactos (ventas, facturación, entrega):

```
[Contacts & Addresses] → Add
```

Ejemplo:
```
Name: María García (Contabilidad)
Email: contabilidad@juanperez.com
Phone: +52 55 5555 6789 ext. 102
Type: Invoice Address
```

#### G. Guardar

```
[Save]
```

### 7.2. Crear Productos

#### A. Acceder

```
Sales → Products → Products → Create
```

o

```
Inventory → Products → Products → Create
```

#### B. Producto Físico (Storable)

Ejemplo: Laptop

```
General Information:
  Product Name: Laptop Dell Inspiron 15
  Product Type: Storable Product
  Product Category: Todos / Vendible
  Internal Reference: LAP-DELL-INS15
  Barcode: 7501234567890

Sales:
  Sales Price: 15,000.00
  Customer Taxes: IVA 16%

Purchase:
  Cost: 10,000.00
  Vendor Taxes: IVA 16%

Inventory:
  Weight: 2.5 kg
  Volume: 0.05 m³

Accounting:
  Income Account: 401.01.01 Ventas de mercancía
  Expense Account: 501.01.01 Costo de ventas
```

**Configurar Inventario Inicial:**

```
Inventory → Operations → Inventory Adjustments → Create
Product: Laptop Dell Inspiron 15
Counted Quantity: 100
Location: WH/Stock
[Validate]
```

#### C. Producto Consumible (Consumable)

Ejemplo: Cable USB

```
General Information:
  Product Name: Cable USB-C 2m
  Product Type: Consumable
  Internal Reference: CBL-USBC-2M

Sales:
  Sales Price: 150.00
  Customer Taxes: IVA 16%
```

**Diferencia:**
- No se rastrea inventario
- No genera movimientos de stock
- Útil para accesorios de bajo valor

#### D. Servicio

Ejemplo: Consultoría

```
General Information:
  Product Name: Hora de Consultoría de Software
  Product Type: Service
  Internal Reference: SRV-CONS-HORA

Sales:
  Sales Price: 2,000.00
  Unit of Measure: Horas
  Customer Taxes: IVA 16%

Invoicing Policy:
  ○ Ordered quantities (facturar al crear la orden)
```

#### E. Configurar Proveedores

```
Purchase tab → Vendor → Add a line
```

```
Vendor: Proveedor ABC SA
Vendor Product Name: DELL-INSPIRON-15-I7
Vendor Product Code: DINSP15I7
Price: 10,000.00
Minimal Quantity: 5
Delivery Lead Time: 10 days
```

#### F. Configurar Rutas (Opcional)

Para productos que se fabrican o se compran bajo pedido:

```
Inventory tab:
  Routes:
    ☑ Buy (comprar bajo pedido)
    ☑ Make To Order (fabricar bajo pedido)
```

### 7.3. Crear Proveedores

Similar a crear clientes:

```
Purchase → Orders → Vendors → Create
```

```
Name: Distribuidora ABC SA de CV
Is a Company: ☑
Address: [Dirección completa]
Tax ID (RFC): DABC900101XYZ
Phone: +52 55 5555 1111
Email: ventas@abc.com

Sales & Purchase tab:
  Payment Terms: 15 días
  Fiscal Regime: 601 - General de Ley Personas Morales
```

### 7.4. Configurar Usuarios

#### A. Crear Usuario

```
Settings → Users & Companies → Users → Create
```

```
Name: Carlos Vendedor
Email Address: carlos@tuempresa.com
```

#### B. Permisos de Acceso

```
Access Rights tab:

Sales:
  ○ User: Own Documents Only
  ○ User: All Documents
  ● Administrator

Accounting:
  ○ Billing
  ● Accountant

Inventory:
  ○ User
  ● Administrator
```

**Recomendación:**
- **Vendedores:** Sales User + Billing
- **Contadores:** Accountant
- **Administradores:** Administrator en todo

#### C. Enviar Invitación

```
[Send Password Reset Instructions]
```

El usuario recibirá email para configurar su contraseña.

---

## 8. Flujo Completo: Cotización → Venta → Factura

### 8.1. PASO 1: Crear Cotización

```
Sales → Orders → Quotations → Create
```

#### A. Encabezado

```
Customer: Juan Pérez SA de CV
Quotation Date: [Se llena automático]
Expiration: [7 días después por defecto]
Pricelist: Lista de precios estándar
Payment Terms: 30 días neto
```

#### B. Agregar Líneas de Producto

```
Order Lines → Add a product

Product: Laptop Dell Inspiron 15
Quantity: 2
Unit Price: 15,000.00 (se llena automático)
Taxes: IVA 16% (se llena automático)
```

**Cálculo automático:**
```
Subtotal línea: 2 × 15,000.00 = 30,000.00
IVA 16%: 4,800.00
Total línea: 34,800.00
```

#### C. Agregar Más Productos

```
Add a product

Product: Cable USB-C 2m
Quantity: 5
Unit Price: 150.00
Taxes: IVA 16%
```

```
Subtotal línea: 5 × 150.00 = 750.00
IVA 16%: 120.00
Total línea: 870.00
```

#### D. Totales

```
Untaxed Amount: 30,750.00
Taxes (IVA 16%): 4,920.00
Total: 35,670.00
```

#### E. Información Adicional (Opcional)

```
Other Info tab:
  Salesperson: [Tu usuario]
  Sales Team: Ventas
  Customer Reference: OC-2025-001

Notes tab:
  Terms and Conditions: [Términos de venta]
  Customer Note: "Entrega en sucursal CDMX"
```

#### F. Guardar

```
[Save]
```

Estado: **Quotation**

### 8.2. PASO 2: Enviar Cotización por Email

```
[Send by Email]
```

**Se abre ventana de email:**

```
Recipients: contacto@juanperez.com
Subject: Cotización (Ref SO001)
Body: [Mensaje predeterminado]

  Buenos días,

  Adjunto encontrará nuestra cotización SO001.

  No dude en contactarnos si tiene alguna pregunta.

  Saludos,
  [Tu nombre]
  [Tu empresa]

Attachments:
  ☑ Quotation_SO001.pdf
```

**Opciones adicionales:**

```
☑ Send a copy to myself
☐ Use a template
```

```
[Send]
```

#### Verificar Envío

```
Settings → Technical → Email → Emails
```

Buscar el email enviado, debe mostrar:
- Estado: **Sent** ✅
- Fecha de envío
- Destinatario

**El cliente recibe:**
- Email con PDF adjunto
- Link para ver online (si está habilitado el portal)
- Botón "Accept & Pay" (si está habilitado pago online)

### 8.3. PASO 3: Confirmar Venta

Cuando el cliente acepta (por email, teléfono, firma digital):

```
[Confirm]
```

**Cambios automáticos:**
- Estado: **Quotation** → **Sales Order**
- Se genera número de orden: SO001 → SO002 (secuencial)
- Se registra fecha de confirmación
- Si está configurado: Se crea automáticamente la factura o entrega

**Acciones automáticas posibles:**
- ✅ Reserva inventario (productos storable)
- ✅ Crea orden de entrega (Delivery Order)
- ✅ Crea factura borrador (si está configurado)

### 8.4. PASO 4: Crear Factura

```
[Create Invoice]
```

**Ventana emergente - Opciones:**

```
Create Invoice:
  ● Regular invoice (Factura normal)
  ○ Down payment (percentage) (Anticipo %)
  ○ Down payment (fixed amount) (Anticipo fijo)

Invoice Date: [Hoy]
```

Seleccionar **Regular invoice** → `[Create and View Invoice]`

**Se crea factura borrador:**

```
State: Draft
Customer: Juan Pérez SA de CV
Invoice Date: 2025-12-09
Due Date: 2026-01-08 (según payment terms)
Journal: Customer Invoices

Invoice Lines: (copiadas de la orden de venta)
  - Laptop Dell Inspiron 15 × 2: $30,000.00 + IVA
  - Cable USB-C 2m × 5: $750.00 + IVA

Subtotal: $30,750.00
IVA 16%: $4,920.00
Total: $35,670.00
```

### 8.5. PASO 5: Validar y Timbrar Factura

#### A. Revisar Datos Fiscales

Verificar antes de confirmar:

```
Customer: Juan Pérez SA de CV
RFC: PERJ850101ABC ✅
Fiscal Regime: 612 ✅
CFDI Use: G03 ✅
Payment Method: 99 - Por definir ✅
Payment Way: PUE - Pago en una exhibición ✅
```

Si algo falta, editar el cliente antes de confirmar.

#### B. Confirmar Factura

```
[Confirm]
```

**Proceso automático:**

1. **Genera asiento contable:**
```
Date: 2025-12-09
Reference: INV/2025/00001

Account                          Debit       Credit
───────────────────────────────────────────────────
105.01.01 Clientes por cobrar   35,670.00
  401.01.01 Ventas de mercancía              30,750.00
  208.01.01 IVA Trasladado                    4,920.00
```

2. **Timbre XML (México):**
   - Odoo genera XML CFDI 4.0
   - Envía al PAC configurado
   - PAC timbra el XML
   - Devuelve UUID y sello digital
   - Odoo guarda XML timbrado
   - Genera código QR

3. **Actualiza estado:**
   - Draft → **Posted**
   - Asignado: INV/2025/00001

#### C. Verificar Timbrado (México)

```
Other Info tab → Electronic Invoicing
```

Debe mostrar:
```
CFDI Status: ✅ Valid
UUID: 12345678-1234-1234-1234-123456789012
SAT Certificate: 00001000000123456789
```

**Si falla el timbrado:**
- Revisar configuración del PAC
- Ver mensaje de error del PAC
- Verificar certificados
- Ver sección [Troubleshooting](#12-troubleshooting)

### 8.6. PASO 6: Enviar Factura al Cliente

```
[Send & Print]
```

**Ventana de email:**

```
Recipients: contacto@juanperez.com
Subject: Invoice INV/2025/00001

Attachments:
  ☑ INV_2025_00001.pdf
  ☑ INV_2025_00001.xml (si es México)
```

```
[Send]
```

**El cliente recibe:**
- PDF de la factura con:
  - Datos fiscales completos
  - Logo de la empresa
  - Código QR (México)
  - UUID (México)
  - Desglose de IVA
- XML timbrado (México)
- Link para pagar online (si está configurado)

### 8.7. PASO 7: Registrar Pago

Cuando el cliente paga:

```
[Register Payment]
```

**Ventana emergente:**

```
Journal: Bank
Payment Method: 03 - Transferencia electrónica
Amount: 35,670.00
Payment Date: 2025-12-10
Memo: Pago factura INV/2025/00001
```

```
[Create Payment]
```

**Asiento contable generado:**

```
Date: 2025-12-10
Reference: BNK1/2025/00001

Account                          Debit       Credit
───────────────────────────────────────────────────
102.01.01 Banco BBVA             35,670.00
  105.01.01 Clientes por cobrar              35,670.00
```

**Estado de factura:**
- Payment Status: **Paid** ✅
- Estado de cuenta del cliente: $0.00

---

## 9. Configuración de Inventario

### 9.1. Configurar Almacenes

```
Inventory → Configuration → Warehouses
```

Por defecto existe: **WH** (Warehouse)

**Configurar ubicaciones:**

```
Warehouse: WH
Location:
  - WH/Stock (inventario principal)
  - WH/Input (recepción)
  - WH/Output (salida)
  - WH/Packing (empaque)
```

### 9.2. Reglas de Reabastecimiento

Para productos que deben reordenarse automáticamente:

```
Inventory → Configuration → Reordering Rules → Create
```

```
Product: Laptop Dell Inspiron 15
Warehouse: WH
Location: WH/Stock
Min Quantity: 10
Max Quantity: 50
Quantity Multiple: 5
```

**Funcionamiento:**
- Cuando stock < 10: Odoo genera solicitud de compra
- Cantidad a ordenar: hasta llegar a 50
- En múltiplos de 5

### 9.3. Operaciones de Inventario

#### A. Ajuste de Inventario

```
Inventory → Operations → Inventory Adjustments → Create
```

```
Product: Laptop Dell Inspiron 15
Counted Quantity: 100
Location: WH/Stock
```

```
[Validate]
```

#### B. Transferencia Entre Ubicaciones

```
Inventory → Operations → Transfers → Create
```

```
Operation Type: Internal Transfer
Source Location: WH/Stock
Destination Location: WH/Output
Products:
  - Laptop Dell Inspiron 15 × 10
```

```
[Validate]
```

### 9.4. Trazabilidad

Para productos que requieren números de serie o lotes:

```
Product → [Laptop] → Inventory tab
Tracking: By Unique Serial Number
```

Al recibir o entregar, se solicitará número de serie.

---

## 10. Órdenes de Compra

### 10.1. Crear Orden de Compra

```
Purchase → Orders → Create
```

```
Vendor: Distribuidora ABC SA de CV
Order Deadline: 2025-12-20

Order Lines:
  Product: Laptop Dell Inspiron 15
  Quantity: 20
  Unit Price: 10,000.00
  Taxes: IVA 16%
```

```
Subtotal: 200,000.00
IVA 16%: 32,000.00
Total: 232,000.00
```

### 10.2. Confirmar Orden

```
[Confirm Order]
```

Estado: Purchase Order

### 10.3. Enviar al Proveedor

```
[Send by Email]
```

### 10.4. Recibir Productos

Cuando llegan los productos:

```
[Receive Products]
```

Odoo abre la orden de recepción:

```
Source Location: Vendors
Destination: WH/Input → WH/Stock
Products:
  - Laptop Dell Inspiron 15 × 20
```

```
[Validate]
```

**Inventario actualizado:**
- Stock anterior: 100
- Recibido: 20
- Stock nuevo: 120

### 10.5. Crear Factura de Proveedor

```
[Create Bill]
```

```
Vendor: Distribuidora ABC SA de CV
Bill Date: 2025-12-10
Due Date: 2025-12-25
Reference: FACT-ABC-001 (número de factura del proveedor)

Lines: (copiadas de la orden de compra)
Total: 232,000.00
```

```
[Confirm]
```

**Asiento contable:**

```
Account                          Debit       Credit
───────────────────────────────────────────────────
501.01.01 Compras de mercancía   200,000.00
119.01.01 IVA Acreditable         32,000.00
  201.01.01 Proveedores                      232,000.00
```

---

## 11. Verificación de Funcionamiento

### 11.1. Test 1: Envío de Correos

#### Crear cotización y enviarla

```
Sales → Quotations → Create → [Llenar datos] → Send by Email
```

#### Verificar en logs

```
Settings → Technical → Email → Emails
```

**Verificar:**
- ✅ Estado: **Sent**
- ✅ Fecha de envío reciente
- ✅ Sin errores

#### Verificar recepción

Revisar la bandeja del cliente:
- ✅ Email recibido
- ✅ PDF adjunto
- ✅ Formato correcto

### 11.2. Test 2: Factura con Datos Fiscales

```
Accounting → Customers → Invoices → [Factura validada]
```

**Descargar PDF y verificar:**

```
✅ Logo de la empresa en header
✅ Nombre legal de la empresa
✅ RFC de la empresa
✅ Dirección fiscal completa
✅ RFC del cliente
✅ Datos fiscales del cliente (régimen, uso CFDI)
✅ Desglose correcto de IVA
✅ Total correcto
✅ Método de pago (México)
✅ Forma de pago (México)
✅ UUID (México)
✅ Código QR (México)
✅ Sello digital SAT (México)
```

### 11.3. Test 3: XML Timbrado (México)

```
Accounting → Customers → Invoices → [Factura] → Download XML
```

**Verificar XML:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Comprobante
    Version="4.0"
    Serie="FAC"
    Folio="00001"
    Fecha="2025-12-09T10:30:00"
    Total="35670.00"
    ...>

    <cfdi:Emisor Rfc="TAV850101ABC" Nombre="Tecnología Avanzada SA" .../>
    <cfdi:Receptor Rfc="PERJ850101ABC" Nombre="Juan Pérez SA de CV" .../>

    <cfdi:Conceptos>
        <cfdi:Concepto
            ClaveProdServ="43211500"
            Cantidad="2"
            Descripcion="Laptop Dell Inspiron 15"
            ValorUnitario="15000.00"
            Importe="30000.00"
            .../>
    </cfdi:Conceptos>

    <cfdi:Complemento>
        <tfd:TimbreFiscalDigital
            Version="1.1"
            UUID="12345678-1234-1234-1234-123456789012"
            FechaTimbrado="2025-12-09T10:31:00"
            SelloCFD="..."
            SelloSAT="..."
            .../>
    </cfdi:Complemento>
</cfdi:Comprobante>
```

**Validar en el SAT:**

https://verificacfdi.facturaelectronica.sat.gob.mx/

```
RFC Emisor: TAV850101ABC
RFC Receptor: PERJ850101ABC
Total: 35670.00
UUID: 12345678-1234-1234-1234-123456789012
```

Resultado esperado: ✅ **"Estado del comprobante: Vigente"**

### 11.4. Test 4: Actualización de Inventario

#### Antes de la venta

```
Inventory → Products → Laptop Dell Inspiron 15
```

```
On Hand: 100
Reserved: 0
Forecasted: 100
```

#### Crear y confirmar venta de 2 laptops

```
Sales → Create → Laptop × 2 → Confirm
```

#### Después de la venta

```
Inventory → Products → Laptop Dell Inspiron 15
```

```
On Hand: 100
Reserved: 2 ✅ (reservado para entregar)
Forecasted: 98
```

#### Después de la entrega

```
Inventory → Operations → Delivery Orders → [DO] → Validate
```

```
On Hand: 98 ✅ (reducido)
Reserved: 0
Forecasted: 98
```

### 11.5. Test 5: Asientos Contables

```
Accounting → Accounting → Journal Entries
```

**Factura de venta:**

```
Date: 2025-12-09
Reference: INV/2025/00001
Journal: Customer Invoices

Lines:
  105.01.01 Clientes por cobrar    35,670.00 (Dr)
  401.01.01 Ventas de mercancía                30,750.00 (Cr)
  208.01.01 IVA Trasladado                      4,920.00 (Cr)

Balance: 0.00 ✅
State: Posted ✅
```

**Pago de cliente:**

```
Date: 2025-12-10
Reference: BNK1/2025/00001
Journal: Bank

Lines:
  102.01.01 Banco BBVA              35,670.00 (Dr)
  105.01.01 Clientes por cobrar                35,670.00 (Cr)

Balance: 0.00 ✅
State: Posted ✅
Reconciled: ✅ (con INV/2025/00001)
```

### 11.6. Test 6: Reportes

#### A. Reporte de Ventas

```
Sales → Reporting → Sales
```

Filtros:
- Fecha: Último mes
- Equipo de ventas: Todos

**Verificar:**
- ✅ Ventas totales
- ✅ Desglose por producto
- ✅ Desglose por cliente
- ✅ Margen de ganancia

#### B. Reporte de Facturas

```
Accounting → Reporting → Aged Receivable
```

**Verificar:**
- ✅ Facturas por cobrar
- ✅ Antigüedad (0-30 días, 30-60, etc.)
- ✅ Total por cliente

#### C. Balance General

```
Accounting → Reporting → Balance Sheet
```

**Verificar:**
```
Activo:
  Banco: $35,670.00 ✅
  Clientes: $0.00 ✅ (pagado)
  Inventario: $980,000.00 ✅ (98 laptops × $10,000)

Pasivo:
  Proveedores: $232,000.00 ✅

Capital:
  Utilidades: $30,750.00 ✅
```

---

## 12. Troubleshooting

### 12.1. "Los correos no se envían"

#### Síntoma
Al hacer clic en "Send by Email", el correo queda en estado "Outgoing" o "Exception".

#### Diagnóstico

```
Settings → Technical → Email → Emails → [Email fallido]
```

**Ver campo "Failure Reason":**

##### Error: "[Errno 111] Connection refused"

**Causa:** Servidor SMTP incorrecto o puerto bloqueado

**Solución:**
```
Settings → Technical → Outgoing Mail Servers → [Tu servidor]
```

Verificar:
- SMTP Server: correcto (smtp.gmail.com, email-smtp.us-east-1.amazonaws.com, etc.)
- SMTP Port: 587 (TLS) o 465 (SSL)
- Probar con Test Connection

##### Error: "535 Authentication failed"

**Causa:** Usuario o contraseña incorrectos

**Solución Gmail:**
1. Usar App Password, NO la contraseña normal
2. Generar en: https://myaccount.google.com/apppasswords
3. Copiar la contraseña de 16 caracteres
4. Actualizar en Odoo

**Solución SES:**
1. Verificar SMTP Username (AKIA...)
2. Verificar SMTP Password (BMrG...)
3. Generar nuevas credenciales si es necesario

##### Error: "554 Message rejected: Email address is not verified"

**Causa:** Dominio no verificado en Amazon SES

**Solución:**
1. AWS Console → Amazon SES → Verified Identities
2. Agregar y verificar dominio
3. Esperar verificación DNS
4. Salir de "sandbox mode" si es necesario

#### Workaround Temporal

Si necesitas enviar correos urgentemente:

```bash
# Enviar correos en cola manualmente
cd ~/odoo-18/odoo
source ../venv/bin/activate
./odoo-bin shell -c ../config/odoo.conf -d tu_database

>>> env['mail.mail'].sudo().search([('state', '=', 'outgoing')]).send()
```

### 12.2. "No se genera el XML timbrado (México)"

#### Síntoma
Al confirmar factura, no se genera UUID y queda sin timbrar.

#### Diagnóstico

```
Accounting → Customers → Invoices → [Factura] → Other Info
→ Electronic Invoicing
```

**Ver campo "EDI Status" y mensajes de error.**

##### Error: "Certificado expirado"

**Causa:** Certificado .cer del SAT venció

**Solución:**
1. Renovar certificado en SAT
2. Descargar nuevo .cer y .key
3. Subir en Odoo:
```
Accounting → Configuration → Settings → Mexican Localization
→ Certificate (.cer): [Upload nuevo]
→ Certificate Key (.key): [Upload nuevo]
→ Certificate Password: [Actualizar si cambió]
```

##### Error: "RFC del receptor no válido"

**Causa:** Cliente no tiene RFC o está mal formado

**Solución:**
```
Contacts → [Cliente] → Sales & Purchase tab
Tax ID: [Verificar formato RFC]
```

RFC válido:
- Personas físicas: 13 caracteres (XAXX010101000)
- Personas morales: 12 caracteres (ABC010101000)
- Sin espacios ni caracteres especiales

##### Error: "PAC: Usuario o contraseña incorrectos"

**Causa:** Credenciales del PAC incorrectas

**Solución:**
1. Verificar credenciales en el portal del PAC
2. Actualizar en Odoo:
```
Accounting → Configuration → Settings → Mexican Localization
→ PAC Username: [Corregir]
→ PAC Password: [Corregir]
```

##### Error: "Régimen fiscal no válido"

**Causa:** Cliente no tiene régimen fiscal configurado

**Solución:**
```
Contacts → [Cliente] → Sales & Purchase tab
Fiscal Regime: [Seleccionar régimen correcto]
```

#### Forzar Re-timbrado

Si la factura está confirmada pero no timbrada:

```
Accounting → Customers → Invoices → [Factura]
→ [Action] → Reset to Draft
→ [Confirm] (intentará timbrar de nuevo)
```

### 12.3. "La factura no tiene RFC del cliente"

#### Síntoma
PDF de factura no muestra RFC del cliente.

#### Causa
Cliente no tiene Tax ID configurado.

#### Solución

```
Contacts → [Cliente]
→ Tax ID: [Agregar RFC]
→ Save
```

Luego regenerar la factura o cancelar y crear una nueva.

### 12.4. "El IVA no se calcula"

#### Síntoma
Al agregar producto a cotización o factura, no aparece IVA.

#### Causa
Producto no tiene impuesto configurado.

#### Solución

```
Sales → Products → [Producto]
→ Sales tab
→ Customer Taxes: [Seleccionar "IVA 16%"]
→ Save
```

Si el impuesto no existe:

```
Accounting → Configuration → Taxes → Create
Name: IVA 16%
Tax Type: Sales
Rate: 16%
```

### 12.5. "No aparece el logo en la factura"

#### Síntoma
PDF no muestra logo de la empresa.

#### Solución

```
Settings → Companies → [Tu empresa]
→ Click en ícono de cámara para subir logo
→ Seleccionar archivo PNG (recomendado 300x100px)
→ Save
```

Regenerar PDF de factura:
```
Accounting → Invoices → [Factura] → Print
```

### 12.6. "El inventario no se actualiza"

#### Síntoma
Después de confirmar venta, el stock no disminuye.

#### Causa
Producto configurado como "Consumable" o "Service" en lugar de "Storable Product".

#### Solución

```
Inventory → Products → [Producto]
→ General Information tab
→ Product Type: Storable Product
→ Save
```

Nota: Cambiar el tipo no afecta ventas anteriores.

### 12.7. "Error al confirmar factura: Unbalanced Journal Entry"

#### Síntoma
Al confirmar factura, error: "The journal entry is unbalanced".

#### Causa
Producto no tiene cuentas contables configuradas.

#### Solución

```
Inventory → Products → [Producto]
→ Accounting tab
→ Income Account: 401.01.01 Ventas de mercancía
→ Expense Account: 501.01.01 Costo de ventas
→ Save
```

Si las cuentas no existen:

```
Accounting → Configuration → Chart of Accounts → Create
```

### 12.8. "No puedo acceder a Settings"

#### Síntoma
Menú "Settings" no aparece para tu usuario.

#### Causa
Usuario no tiene permisos de administración.

#### Solución

Login como admin y:

```
Settings → Users & Companies → Users → [Tu usuario]
→ Access Rights tab
→ Administration: Access Rights
→ Save
```

### 12.9. "XML no valida en el SAT"

#### Síntoma
El XML se genera pero al validarlo en el portal del SAT muestra "No encontrado".

#### Posibles Causas y Soluciones

##### 1. Ambiente de pruebas vs producción

**Verificar:**
```
Accounting → Configuration → Settings → Mexican Localization
Environment: Production (no Test)
```

##### 2. Certificado de prueba en lugar de producción

**Solución:**
- Usar certificado de PRODUCCIÓN del SAT
- No usar CSD de prueba

##### 3. UUID no asignado correctamente

**Verificar en el XML:**
```xml
<tfd:TimbreFiscalDigital UUID="12345678-1234-1234-1234-123456789012" .../>
```

Si el UUID es todo ceros o está vacío, hubo error en el timbrado.

### 12.10. "Error 403 al instalar módulo"

#### Síntoma
Al instalar módulo desde Apps, error de permisos.

#### Solución

Instalar desde línea de comandos:

```bash
cd ~/odoo-18/odoo
source ../venv/bin/activate
./odoo-bin -c ../config/odoo.conf -d tu_database -i nombre_modulo --stop-after-init
./odoo-bin -c ../config/odoo.conf -d tu_database
```

---

## 13. Checklist de Configuración

### 13.1. Checklist: Configuración Inicial

```
☐ 1. Configurar datos de la empresa
    ☐ Nombre legal
    ☐ Dirección fiscal completa
    ☐ RFC (México) / Tax ID
    ☐ Teléfono y email
    ☐ Moneda (MXN)
    ☐ Idioma (es_MX)

☐ 2. Subir logo de la empresa
    ☐ Formato PNG 300x100px
    ☐ Fondo transparente
    ☐ Peso < 100 KB

☐ 3. Configurar servidor SMTP
    ☐ Crear servidor (Gmail o SES)
    ☐ Configurar usuario y contraseña
    ☐ Probar conexión
    ☐ Verificar estado "Sent" en logs

☐ 4. Activar módulos necesarios
    ☐ Sales Management
    ☐ Invoicing / Accounting
    ☐ Inventory
    ☐ Purchase (si aplica)
    ☐ l10n_mx (México)
    ☐ l10n_mx_edi (México)
```

### 13.2. Checklist: Configuración de Ventas

```
☐ 5. Configurar módulo de Ventas
    ☐ Quotation Templates
    ☐ Online Signature
    ☐ Delivery Methods
    ☐ Discounts
    ☐ Pricelists
    ☐ Automatic Invoice

☐ 6. Configurar términos de pago
    ☐ Crear: "Inmediato"
    ☐ Crear: "15 días"
    ☐ Crear: "30 días"
    ☐ Crear: "30/60/90 días"
```

### 13.3. Checklist: Configuración de Contabilidad

```
☐ 7. Configurar impuestos
    ☐ IVA 16% (Venta)
    ☐ IVA 16% (Compra)
    ☐ IVA 0% (Exportación)
    ☐ Retención ISR 10% (si aplica)

☐ 8. Configurar diarios contables
    ☐ Customer Invoices (INV)
    ☐ Vendor Bills (BILL)
    ☐ Bank (BNK1)
    ☐ Configurar numeración

☐ 9. Configurar PAC (México)
    ☐ Elegir PAC (Finkok, SW Sapien, etc.)
    ☐ Configurar usuario y contraseña PAC
    ☐ Subir certificado .cer del SAT
    ☐ Subir llave .key del SAT
    ☐ Ingresar contraseña de llave
    ☐ Probar timbrado con factura de prueba

☐ 10. Configurar métodos y formas de pago (México)
    ☐ 01 - Efectivo
    ☐ 03 - Transferencia
    ☐ 04 - Tarjeta de crédito
    ☐ 28 - Tarjeta de débito
    ☐ PUE - Pago en una exhibición
    ☐ PPD - Pago en parcialidades
```

### 13.4. Checklist: Datos Maestros

```
☐ 11. Crear productos/servicios
    ☐ Al menos 3 productos de prueba
    ☐ Configurar tipo (Storable/Consumable/Service)
    ☐ Configurar precio de venta
    ☐ Configurar costo
    ☐ Asignar IVA 16%
    ☐ Configurar cuentas contables
    ☐ Agregar código de barras (opcional)

☐ 12. Crear clientes
    ☐ Al menos 2 clientes de prueba
    ☐ Configurar RFC
    ☐ Configurar régimen fiscal (México)
    ☐ Configurar uso CFDI (México)
    ☐ Configurar email
    ☐ Configurar términos de pago

☐ 13. Crear proveedores
    ☐ Al menos 1 proveedor de prueba
    ☐ Configurar RFC
    ☐ Configurar email
    ☐ Configurar términos de pago

☐ 14. Configurar inventario inicial
    ☐ Hacer ajuste de inventario
    ☐ Asignar cantidades a productos
    ☐ Validar movimiento
```

### 13.5. Checklist: Testing

```
☐ 15. Test de correo electrónico
    ☐ Crear cotización
    ☐ Enviar por email
    ☐ Verificar recepción
    ☐ Verificar PDF adjunto

☐ 16. Test de factura completa
    ☐ Crear cotización
    ☐ Confirmar venta
    ☐ Crear factura
    ☐ Validar factura
    ☐ Verificar datos fiscales en PDF
    ☐ Verificar UUID (México)
    ☐ Enviar factura por email
    ☐ Descargar XML (México)
    ☐ Validar XML en portal SAT (México)

☐ 17. Test de inventario
    ☐ Verificar stock inicial
    ☐ Crear venta de producto
    ☐ Confirmar venta
    ☐ Verificar reserva de stock
    ☐ Validar entrega
    ☐ Verificar reducción de stock

☐ 18. Test de asientos contables
    ☐ Crear factura
    ☐ Validar factura
    ☐ Verificar asiento contable creado
    ☐ Verificar cuentas correctas
    ☐ Verificar balance = 0
    ☐ Registrar pago
    ☐ Verificar asiento de pago
    ☐ Verificar conciliación

☐ 19. Test de reportes
    ☐ Generar reporte de ventas
    ☐ Generar reporte de facturas por cobrar
    ☐ Generar balance general
    ☐ Verificar datos correctos
```

### 13.6. Checklist: Configuración Adicional

```
☐ 20. Configurar usuarios
    ☐ Crear usuarios para cada departamento
    ☐ Asignar permisos correctos
    ☐ Enviar invitaciones
    ☐ Probar accesos

☐ 21. Configurar secuencias
    ☐ Facturas: FAC/%(year)s/
    ☐ Cotizaciones: COT/%(year)s/
    ☐ Órdenes de compra: OC/%(year)s/

☐ 22. Configurar notificaciones
    ☐ Actividades pendientes
    ☐ Facturas vencidas
    ☐ Stock bajo
    ☐ Aprobaciones requeridas
```

---

## 14. Mejores Prácticas

### 14.1. Datos Maestros

#### ✅ Mantener datos limpios

**Clientes:**
- RFC siempre en mayúsculas
- Sin espacios en RFC
- Validar RFC antes de guardar
- Email válido y actualizado
- Teléfono con formato consistente (+52 55 5555 5555)

**Productos:**
- Códigos internos únicos y descriptivos
- Nomenclatura consistente (LAP-DELL-001, LAP-HP-001)
- Descripciones claras y completas
- Precios actualizados
- Costos actualizados

#### ✅ Usar categorías

```
Productos:
  → Electrónica
    → Computadoras
      → Laptops
      → Desktops
    → Accesorios
      → Cables
      → Mouse
```

Beneficio: Filtros, reportes, y análisis más fáciles.

### 14.2. Facturación

#### ✅ Validar datos antes de timbrar

Lista de verificación antes de confirmar factura:
1. RFC del cliente correcto
2. Régimen fiscal configurado
3. Uso CFDI apropiado
4. Método de pago correcto
5. Forma de pago correcta
6. IVA calculado correctamente
7. Totales correctos

**¿Por qué?** Una vez timbrada, no se puede modificar. Solo cancelar y crear nueva (con límites del SAT).

#### ✅ Cancelaciones (México)

**Límite SAT:** Máximo 3 cancelaciones relacionadas en 72 horas.

**Proceso:**
```
Accounting → Invoices → [Factura] → Request EDI Cancellation
```

**Motivos válidos:**
- 01 - Comprobante emitido con errores con relación
- 02 - Comprobante emitido con errores sin relación
- 03 - No se llevó a cabo la operación
- 04 - Operación nominativa relacionada en una factura global

**Siempre documentar el motivo internamente.**

### 14.3. Inventario

#### ✅ Hacer inventarios físicos periódicos

**Frecuencia recomendada:**
- Productos de alto valor: Mensual
- Productos de rotación media: Trimestral
- Productos de baja rotación: Semestral

**Proceso:**
```
Inventory → Operations → Inventory Adjustments
1. Contar físicamente
2. Registrar en Odoo
3. Investigar diferencias > 5%
4. Validar ajuste
```

#### ✅ Configurar reordering rules

Para productos críticos, configurar mínimos/máximos:

```
Min: 10 unidades (2 semanas de venta)
Max: 50 unidades (8 semanas de venta)
Lead time: 10 días
```

Beneficio: Odoo genera solicitudes de compra automáticamente.

### 14.4. Seguridad

#### ✅ Principio de mínimo privilegio

No dar permisos de administrador a todos:

**Vendedores:**
- Sales: User (solo sus documentos)
- Invoicing: Billing (crear facturas borradores)

**Contadores:**
- Accounting: Accountant (todas las funciones contables)
- Invoicing: Billing

**Gerentes:**
- Sales: Administrator
- Invoicing: Billing

**Admin:**
- Solo para configuración inicial
- No usar para operación diaria

#### ✅ Auditoría

```
Settings → Technical → Audit → Logs
```

Revisar periódicamente:
- Cambios en configuración fiscal
- Eliminación de registros
- Cambios en permisos de usuarios
- Cancelaciones de facturas

#### ✅ Backups

**Base de datos:**
```bash
# Backup manual
cd ~/odoo-18
pg_dump -U odoo -F c -b -v -f "backup_$(date +%Y%m%d).backup" tu_database
```

**Backup automático diario:**
```bash
# Agregar a crontab
0 2 * * * /home/odoo/scripts/backup_odoo.sh
```

**Guardar en ubicación externa:**
- AWS S3
- Google Cloud Storage
- Servidor FTP externo

### 14.5. Performance

#### ✅ Limpiar datos periódicamente

**Emails enviados:**
```
Settings → Technical → Email → Emails
Filtrar por: Sent, fecha > 6 meses
Action → Delete
```

**Logs antiguos:**
```
Settings → Technical → Logging → Logs
Filtrar por: fecha > 3 meses
Action → Delete
```

**Adjuntos innecesarios:**
```
Settings → Technical → Database Structure → Attachments
Revisar archivos grandes no utilizados
```

#### ✅ Indexar búsquedas frecuentes

Si tienes miles de productos/clientes, considera índices adicionales:

```sql
CREATE INDEX idx_product_default_code ON product_product(default_code);
CREATE INDEX idx_partner_ref ON res_partner(ref);
```

#### ✅ Monitorear uso de recursos

```bash
# Ver procesos Odoo
ps aux | grep odoo-bin

# Ver memoria usada
free -h

# Ver espacio en disco
df -h
```

### 14.6. Comunicación con Clientes

#### ✅ Plantillas de email personalizadas

```
Settings → Technical → Email → Email Templates
```

Crear plantillas para:
- Cotizaciones
- Confirmación de orden
- Facturas
- Recordatorios de pago
- Agradecimiento post-venta

**Usar variables dinámicas:**
```
Hola ${object.partner_id.name},

Adjunto encontrará su factura ${object.name} por $${object.amount_total}.

Gracias por su preferencia.
```

#### ✅ Portal del cliente

Activar para que clientes puedan:
- Ver sus cotizaciones
- Firmar digitalmente
- Ver sus facturas
- Descargar XMLs
- Ver estado de entregas

```
Settings → Users & Companies → Invite Users
→ Portal User (external access)
```

### 14.7. Documentación Interna

#### ✅ Documentar procesos

Crear manuales para:
- Cómo crear una cotización
- Cómo validar una factura
- Cómo registrar un pago
- Cómo hacer devoluciones
- Procedimiento de cierre mensual

#### ✅ Documentar configuración

Mantener registro de:
- Credenciales del PAC
- Fecha de vencimiento de certificados SAT
- Usuarios SMTP
- APIs de terceros integradas
- Customizaciones realizadas

#### ✅ Capacitación

Al incorporar nuevos usuarios:
1. Dar acceso limitado inicial
2. Capacitar en ambiente de prueba
3. Hacer ejercicios prácticos
4. Supervisar primeras operaciones
5. Dar acceso completo gradualmente

---

## Conclusión

### Has aprendido a:

✅ **Configurar Odoo desde cero** para operación real
✅ **Enviar correos automáticos** con SMTP (Gmail/SES)
✅ **Generar facturas profesionales** con datos fiscales completos
✅ **Timbrar XMLs** (CFDI 4.0 para México)
✅ **Gestionar inventario** en tiempo real
✅ **Procesar ventas y compras** de principio a fin
✅ **Registrar contabilidad** automáticamente

### Próximos Pasos

1. **Importar datos existentes:**
   - Clientes desde Excel/CSV
   - Productos desde Excel/CSV
   - Inventario inicial

2. **Configurar integraciones:**
   - Tienda en línea (Odoo eCommerce)
   - Punto de venta (Odoo POS)
   - Mercado Libre / Amazon
   - Stripe / PayPal

3. **Personalizar:**
   - Crear reportes personalizados
   - Agregar campos custom
   - Desarrollar módulos propios
   - Automatizar procesos con Odoo Studio

4. **Escalar:**
   - Migrar a servidor dedicado
   - Configurar backups automáticos
   - Implementar balanceo de carga
   - Monitorear con herramientas profesionales

### Recursos Adicionales

**Documentación oficial:**
- https://www.odoo.com/documentation/18.0/
- https://www.odoo.com/documentation/18.0/developer/

**Comunidad:**
- https://www.odoo.com/forum
- https://github.com/odoo/odoo

**SAT (México):**
- https://www.sat.gob.mx/
- https://www.sat.gob.mx/consulta/09658/valida-cfdi

---

**Versión:** 1.0.0
**Última actualización:** 2025-12-09
**Autor:** Odoo AI Tools Documentation Team
**Licencia:** LGPL-3

---

**¡Tu Odoo ahora está completamente funcional! 🎉**
