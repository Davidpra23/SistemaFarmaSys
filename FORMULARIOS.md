# Documentación de Formularios — Sistema de Farmacia

Última actualización: 2025-11-09

Este documento resume los formularios principales del proyecto, sus campos esenciales, validaciones mínimas y ejemplos de JSON schema para integrar validación en frontend o APIs.

## Objetivo
Proveer una referencia única y compacta de los formularios que necesita el sistema (MVP), de modo que desarrolladores y diseñadores puedan implementarlos de forma consistente.

## Alcance
Basado en las plantillas actuales del proyecto (`login.html`, `inventory.html`, `sales.html`, `receipts.html`, `receipt_print.html`, `reports.html`, `settings.html`). Se propone una versión simplificada orientada al MVP.

---

## Formularios principales (simplificados)

A continuación se listan los formularios MVP, con campos mínimos y validaciones básicas.

### 1) Login
- Ruta de uso: pantalla `login.html`.
- Campos:
  - `username` (string) — requerido
  - `password` (string) — requerido
- Validaciones:
  - Ambos campos obligatorios.
  - Mensaje claro en caso de credenciales inválidas.

JSON schema (ejemplo):
{
  "type": "object",
  "properties": {
    "username": {"type": "string", "minLength": 1},
    "password": {"type": "string", "minLength": 1}
  },
  "required": ["username", "password"]
}

---

### 2) Producto / Inventario (alta/edición)
- Ruta de uso: `inventory.html`.
- Campos mínimos:
  - `sku` (string) — requerido, único
  - `name` (string) — requerido
  - `sale_price` (number) — requerido, >= 0
  - `cost_price` (number) — opcional, >= 0
  - `stock` (integer) — requerido, >= 0
  - `min_stock` (integer) — opcional
  - `category` (string) — opcional
  - `expiry_date` (date) — opcional (si presente, debe ser > hoy)
- Validaciones:
  - `sku` y `name` obligatorios;
  - precios >= 0;
  - `stock` entero >= 0.

JSON schema (ejemplo):
{
  "type": "object",
  "properties": {
    "sku": {"type": "string", "minLength": 1},
    "name": {"type": "string", "minLength": 1},
    "sale_price": {"type": "number", "minimum": 0},
    "cost_price": {"type": ["number", "null"], "minimum": 0},
    "stock": {"type": "integer", "minimum": 0},
    "min_stock": {"type": ["integer", "null"], "minimum": 0},
    "expiry_date": {"type": ["string", "null"], "format": "date"}
  },
  "required": ["sku", "name", "sale_price", "stock"]
}

Notas:
- `stock` puede ser de solo lectura en la edición si se controla por movimientos.
- Control de SKU único debe hacerse en servidor.

---

### 3) Venta / Punto de Venta (TPV)
- Ruta de uso: `sales.html`.
- Campos principales:
  - `lines` (array de objetos): cada línea contiene:
    - `sku` o `product_id` (string/int) — requerido
    - `quantity` (number) — requerido, > 0
    - `unit_price` (number) — requerido, >= 0
    - `discount` (number) — opcional, >= 0
  - `subtotal`, `tax_total`, `discount_total`, `total` (números calculados)
  - `payment_method` (string) — requerido (e.g., cash, card)
  - `amount_received` (number) — requerido si método cash
  - `customer_id` (opcional)
  - `user_id` (vendedor)
- Validaciones:
  - Al menos una línea válida;
  - cada `quantity` > 0;
  - `amount_received` >= `total` si aplica;
  - stock disponible (si la política lo exige).

JSON schema (esquema parcial para `lines`):
{
  "type": "object",
  "properties": {
    "lines": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "sku": {"type": "string"},
          "quantity": {"type": "number", "minimum": 0.0001},
          "unit_price": {"type": "number", "minimum": 0}
        },
        "required": ["sku", "quantity", "unit_price"]
      },
      "minItems": 1
    },
    "payment_method": {"type": "string"}
  },
  "required": ["lines", "payment_method"]
}

Notas:
- El cálculo de totales e impuestos idealmente se hace en servidor para evitar manipulación.
- Soportar scan por `sku` en la UI.

---

### 4) Recibos — búsqueda e impresión
- Ruta de uso: `receipts.html` y `receipt_print.html`.
- Formulario de búsqueda / filtro (receipts):
  - `date_from`, `date_to` (dates)
  - `receipt_number` (string)
  - `customer` (string)
  - `seller` (string)
- Validaciones: rango de fechas lógico (from <= to).

- Impresión: recibir `receipt_id` y devolver contenido/formato para imprimir.

---

### 5) Reportes (básicos)
- Ruta de uso: `reports.html`.
- Campos:
  - `report_type` (enum: sales, inventory, expiry, top_sellers)
  - `date_from`, `date_to`
  - filtros opcionales: `product_id`, `category`, `seller_id`, `supplier_id`
  - `output_format` (screen, csv, pdf)
- Validaciones: `report_type` requerido; fechas válidas.

---

### 6) Configuración / Ajustes
- Ruta de uso: `settings.html`.
- Campos típicos:
  - `company_name`, `tax_id`, `address`, `logo` (archivo)
  - `default_tax_rate`
- Validaciones: campos fiscales si se usan facturas.

---

## Recomendaciones de implementación
- Validaciones primarias en servidor (redundancia con validación en cliente para mejor UX).
- Usar JSON schemas para front-end validation y para documentación de API.
- Mantener la lógica de negocio (stock decremento, cálculos de impuesto y totales) en servidor.
- Auditar cambios críticos (ajustes de stock, cambios de precio, eliminaciones).

## Prioridades (MVP)
1. Login
2. Venta (TPV)
3. Producto / Inventario (alta/edición)
4. Recibos (imprimir y búsqueda)
5. Reportes básicos
6. Configuración

## Ejemplos de payloads (JSON) — rápidos

Venta (POST /api/sales):
{
  "lines": [
    {"sku": "12345", "quantity": 2, "unit_price": 12.50},
    {"sku": "67890", "quantity": 1, "unit_price": 5.00, "discount": 0.5}
  ],
  "payment_method": "cash",
  "amount_received": 30.0,
  "customer_id": null
}

Producto (POST /api/products):
{
  "sku": "12345",
  "name": "Paracetamol 500mg",
  "sale_price": 3.50,
  "cost_price": 2.00,
  "stock": 100,
  "expiry_date": "2026-06-30"
}

---

## Siguientes pasos (opciones)
- Generar archivos WTForms/Flask y endpoints mínimos para los formularios MVP.
- Crear JSON schemas individuales en archivos `.json` en `schemas/` para integrarlos con la UI.
- Proveer plantillas HTML (Bootstrap) para cada formulario si se desea.

---

Si quieres, puedo: (A) generar los JSON schemas individuales en la carpeta `schemas/`, (B) implementar WTForms y handlers en `main.py` para Login/Producto/Venta, o (C) añadir plantillas HTML simplificadas para cada formulario. Indica la opción y la implemento.
