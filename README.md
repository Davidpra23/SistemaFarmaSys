# SistemaFarmaSys

SistemaFarmaSys es un sistema de gestión para farmacias, diseñado para facilitar el control de inventario, ventas, usuarios y reportes. El sistema cuenta con una interfaz web intuitiva y funcionalidades para la impresión de recibos, generación de reportes y administración de productos.


## Tecnologías y Lenguajes Utilizados

- **Python**: Lenguaje principal para el backend y scripts.
- **Flask**: Framework web para la creación de la aplicación.
- **HTML**: Estructura de las páginas web.
- **CSS**: Estilos y diseño visual (ubicados en `static/css/`).
- **JavaScript**: Funcionalidad interactiva en el frontend (ubicado en `static/js/`).
- **Jinja2**: Motor de plantillas para la generación dinámica de HTML.

### Procesamiento de códigos QR y de barras

El sistema permite escanear códigos QR para agilizar la venta de productos, utilizando la librería **html5-qrcode** en la interfaz web. Para la generación y visualización de códigos de barras (SKU), se emplea **JsBarcode**. Estas tecnologías facilitan la identificación rápida de productos y la impresión de etiquetas.

## Estructura del Proyecto

- `app.py`, `main.py`: Archivos principales de la aplicación.
- `static/`: Archivos estáticos (CSS, JS).
- `templates/`: Plantillas HTML.
- `tools/`: Herramientas y scripts auxiliares.
- `FORMULARIOS.md`, `FORMULARIOS_NATURAL.md`: Documentación y formularios.

## Funcionalidades

- Gestión de inventario de productos.
- Registro y control de ventas.
- Administración de usuarios.
- Generación e impresión de recibos.
- Reportes de ventas e inventario.
- Panel de control y configuración.

## Instalación y Ejecución

1. Clona el repositorio.
2. Instala las dependencias de Python (Flask, etc.).
3. Ejecuta `app.py` o `main.py` para iniciar el sistema.

## Contribución

Puedes contribuir mejorando el sistema, agregando nuevas funcionalidades o corrigiendo errores. Para ello, realiza un fork del repositorio y envía un pull request.

## Licencia

Este proyecto es de uso libre para fines educativos y comerciales.
