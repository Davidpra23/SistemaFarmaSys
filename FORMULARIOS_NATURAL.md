Documentación en lenguaje natural — Formularios principales

Última actualización: 2025-11-09

A continuación encontrarás una explicación en lenguaje natural y directa de los formularios principales del sistema, tal como se muestran en el proyecto. Cada bloque describe qué hace el formulario, los campos esenciales que pide y las validaciones mínimas que debe aplicar.

---

Formulario de Login

Este formulario permite a un usuario autenticarse en el sistema. Pide dos datos básicos: su nombre de usuario o correo electrónico y su contraseña. Ambos campos son obligatorios. Si las credenciales no coinciden con una cuenta válida, la interfaz debe mostrar un mensaje de error claro para que la persona sepa que debe revisar sus datos.


Formulario Producto / Inventario (para `inventory.html`)

El formulario de producto se usa tanto para crear un nuevo producto como para editar uno existente. En su versión mínima solicita: el SKU o código que identifica al producto, el nombre, el precio de venta, el precio de costo (opcional), la cantidad en stock actual, un valor de stock mínimo para reordenar, la categoría (opcional) y, si aplica, la fecha de caducidad.

Las validaciones básicas son sencillas: SKU y nombre no pueden quedar vacíos; los precios deben ser números mayores o iguales a cero; el stock debe ser un número entero no negativo; si se ingresa una fecha de caducidad, ésta debe ser posterior a la fecha de hoy. Una práctica habitual es combinar alta y edición en el mismo formulario y manejar los cambios de stock mediante acciones separadas (entrada/salida) para conservar trazabilidad.


Formulario Venta / TPV (para `sales.html`)

Este formulario es el punto de venta. Permite buscar o escanear productos y añadirlos a la venta en forma de líneas. Cada línea incluye el producto, la cantidad, el precio unitario y un posible descuento. El formulario muestra los totales calculados (subtotal, impuestos, total) y pide el método de pago y el monto recibido cuando corresponde.

Validaciones relevantes: cada línea debe tener cantidad mayor a cero; el sistema debe verificar que hay stock disponible (o, si la política lo permite, avisar que quedará en saldo negativo); si el cliente paga en efectivo, el monto recibido debe ser al menos igual al total para poder cerrar la venta.


Formulario Recibos / Búsqueda e impresión (para `receipts.html` y `receipt_print.html`)

En la pantalla de recibos hay dos usos principales: filtrar/buscar recibos y preparar uno para impresión. El formulario de búsqueda permite filtrar por fechas (desde/hasta), número de recibo, cliente o vendedor. Para imprimir, el formulario recibe el identificador del recibo (o la plantilla) y opciones de formato como tamaño de papel o impresora.

Validaciones: el rango de fechas debe ser lógico (fecha desde no mayor que fecha hasta) y al pedir imprimir se debe verificar que el número de recibo exista antes de intentar generar la impresión.


Formulario Reportes (para `reports.html`)

Este formulario sirve para generar reportes del sistema. Pide qué tipo de reporte se quiere (por ejemplo: ventas, inventario, caducidades), el rango de fechas a analizar y filtros opcionales como producto, categoría, proveedor o vendedor. También permite elegir el formato de salida (ver en pantalla, PDF o CSV).

Validaciones mínimas: se debe seleccionar el tipo de reporte y proveer un rango de fechas válido.


Formulario Configuración / Ajustes (para `settings.html`)

Aquí se guardan los datos de la empresa y parámetros del sistema. Campos típicos: nombre de la empresa, RUC o identificación fiscal, dirección, la posibilidad de subir un logo, parámetros de impresión (encabezado y pie del recibo) y la tasa de impuesto por defecto.

Validaciones: cuando el sistema va a emitir facturas electrónicas, los campos fiscales importantes deben ser obligatorios; el logo es opcional.

---

Si quieres, puedo convertir estas explicaciones en un PDF, integrarlas en la interfaz de ayuda del sistema o añadir ejemplos visuales (mockups) para cada formulario. ¿Qué prefieres que haga ahora?