import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

INPUT_MD = os.path.join(os.path.dirname(__file__), '..', 'FORMULARIOS_NATURAL.md')
OUTPUT_PDF = os.path.join(os.path.dirname(__file__), '..', 'FORMULARIOS_NATURAL.pdf')

def read_md(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def make_pdf(text, out_path):
    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    x = margin
    y = height - margin
    line_height = 10

    # First page: enumerated list of main forms
    forms = [
        "1. Formulario de Login",
        "2. Formulario Producto / Inventario (inventory.html)",
        "3. Formulario Venta / TPV (sales.html)",
        "4. Formulario Recibos / Búsqueda e impresión (receipts.html + receipt_print.html)",
        "5. Formulario Reportes (reports.html)",
        "6. Formulario Configuración / Ajustes (settings.html)"
    ]

    c.setFont('Helvetica-Bold', 16)
    c.drawString(x, y, "Formularios principales — índice")
    y -= 2 * line_height
    c.setFont('Helvetica', 11)
    for ftext in forms:
        if y < margin + 40:
            c.showPage()
            y = height - margin
            c.setFont('Helvetica', 11)
        c.drawString(x, y, ftext)
        y -= line_height

    # Add a page break
    c.showPage()

    # Now write the full markdown text (plain) into the PDF
    c.setFont('Helvetica-Bold', 14)
    y = height - margin
    c.drawString(x, y, "Documentación de Formularios (texto)")
    y -= 2 * line_height
    c.setFont('Helvetica', 10)

    # Wrap lines to page width
    max_width = width - 2 * margin

    def wrap_and_draw(line, cur_y):
        words = line.split(' ')
        cur = ''
        for w in words:
            test = (cur + ' ' + w).strip()
            if c.stringWidth(test, 'Helvetica', 10) <= max_width:
                cur = test
            else:
                cur_y -= line_height
                if cur_y < margin:
                    c.showPage()
                    cur_y = height - margin
                    c.setFont('Helvetica', 10)
                c.drawString(x, cur_y, cur)
                cur = w
        if cur:
            cur_y -= line_height
            if cur_y < margin:
                c.showPage()
                cur_y = height - margin
                c.setFont('Helvetica', 10)
            c.drawString(x, cur_y, cur)
        return cur_y

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            y -= line_height
            if y < margin:
                c.showPage()
                y = height - margin
                c.setFont('Helvetica', 10)
            continue
        if line.startswith('Formulario') or line.startswith('Formulario de') or line.startswith('###') or line.startswith('---'):
            # treat as heading
            c.setFont('Helvetica-Bold', 12)
            y = wrap_and_draw(line, y)
            c.setFont('Helvetica', 10)
        else:
            y = wrap_and_draw(line, y)

    c.save()
    return out_path


if __name__ == '__main__':
    md = read_md(INPUT_MD)
    out = make_pdf(md, OUTPUT_PDF)
    print(f'PDF generado en: {out}')
