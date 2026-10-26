import os
import io
import csv
import json
import zipfile
import html
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas com numeração de página profissional 'Página X de Y'"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#718096"))
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(A4[0] - 54, 36, page_text)
        self.drawString(54, 36, "SOUZAIA Document Engine")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 50, A4[0] - 54, 50)
        self.restoreState()


class DocumentEngine:
    """
    Motor universal de documentos: PDF, DOCX, TXT, MD, HTML, CSV, XLSX, JSON, XML.
    """

    # =========================================================================
    # PDF CONVERSIONS
    # =========================================================================

    @classmethod
    def pdf_to_docx(
        cls,
        pdf_path: str,
        output_docx_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """Converte PDF para documento DOCX preservando parágrafos, cabeçalhos e estrutura"""
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        paragraphs_data = []

        for pno in range(total_pages):
            if progress_callback:
                pct = (pno / total_pages) * 70.0
                progress_callback(pct, f"Lendo página {pno + 1}/{total_pages} do PDF...")

            page = doc[pno]
            blocks = page.get_text("blocks")
            for b in blocks:
                text = b[4].strip()
                if not text:
                    continue
                # Simple heuristic for headings based on length and lines
                is_heading = len(text.splitlines()) == 1 and len(text) < 60 and not text.endswith('.')
                paragraphs_data.append({
                    'text': text,
                    'is_heading': is_heading,
                    'page': pno + 1
                })

        doc.close()

        if progress_callback:
            progress_callback(80.0, "Construindo documento DOCX...")

        cls._create_docx_file(paragraphs_data, output_docx_path)

        if progress_callback:
            progress_callback(100.0, "Conversão PDF -> DOCX finalizada!")

        return output_docx_path

    @classmethod
    def pdf_to_text(cls, pdf_path: str, output_path: str, fmt: str = 'txt') -> str:
        """Extrai texto do PDF formatado como TXT ou Markdown"""
        doc = pymupdf.open(pdf_path)
        content = []

        for pno, page in enumerate(doc):
            if fmt == 'md':
                content.append(f"\n\n## Página {pno + 1}\n\n")
            text = page.get_text("text")
            content.append(text)

        doc.close()
        full_text = "".join(content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)

        return output_path

    @classmethod
    def pdf_to_html(cls, pdf_path: str, output_path: str) -> str:
        """Converte PDF para HTML com layout e formatação estilizada"""
        doc = pymupdf.open(pdf_path)
        html_pages = []

        for pno, page in enumerate(doc):
            page_html = page.get_text("html")
            html_pages.append(f"<div class='pdf-page' id='page-{pno+1}'>{page_html}</div>")

        doc.close()

        full_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Documento Convertido</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }}
  .pdf-page {{ background: #fff; max-width: 800px; margin: 20px auto; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 8px; }}
</style>
</head>
<body>
{''.join(html_pages)}
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_html)

        return output_path

    @classmethod
    def pdf_to_images(
        cls,
        pdf_path: str,
        output_dir: str,
        target_fmt: str = "png",
        dpi: int = 300,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[str]:
        """Renderiza cada página do PDF em imagem de altíssima definição (300 DPI)"""
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        output_paths = []
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = Path(pdf_path).stem

        zoom = dpi / 72.0
        mat = pymupdf.Matrix(zoom, zoom)

        for pno in range(total_pages):
            if progress_callback:
                pct = (pno / total_pages) * 100.0
                progress_callback(pct, f"Renderizando página {pno + 1}/{total_pages} a {dpi} DPI...")

            page = doc[pno]
            pix = page.get_pixmap(matrix=mat, alpha=(target_fmt.lower() == 'png'))
            page_filename = f"{stem}_pagina_{pno + 1:03d}.{target_fmt.lower()}"
            page_path = str(out_dir / page_filename)
            pix.save(page_path)
            output_paths.append(page_path)

        doc.close()
        return output_paths

    # =========================================================================
    # DOCX CONVERSIONS
    # =========================================================================

    @classmethod
    def docx_to_pdf(
        cls,
        docx_path: str,
        output_pdf_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """Converte documento DOCX para PDF com diagramação estilizada e paginação"""
        if progress_callback:
            progress_callback(10.0, "Lendo estrutura do arquivo DOCX...")

        elements_data = cls._parse_docx_file(docx_path)

        if progress_callback:
            progress_callback(40.0, "Diagramando páginas do PDF...")

        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=A4,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#1A202C")
        )
        h1_style = ParagraphStyle(
            'CustomH1',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#2B6CB0"),
            spaceAfter=12,
            spaceBefore=14
        )
        h2_style = ParagraphStyle(
            'CustomH2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#2D3748"),
            spaceAfter=8,
            spaceBefore=10
        )

        story = []
        for el in elements_data:
            el_type = el.get('type')
            if el_type == 'heading1':
                story.append(Paragraph(html.escape(el['text']), h1_style))
            elif el_type == 'heading2':
                story.append(Paragraph(html.escape(el['text']), h2_style))
            elif el_type == 'paragraph':
                text = el['text']
                if text.strip():
                    story.append(Paragraph(html.escape(text), normal_style))
                    story.append(Spacer(1, 8))
            elif el_type == 'table':
                table_rows = []
                for r in el['rows']:
                    row_cells = [Paragraph(html.escape(c), normal_style) for c in r]
                    table_rows.append(row_cells)
                if table_rows:
                    t = Table(table_rows, colWidths=None)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#2D3748")),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 12))

        if not story:
            story.append(Paragraph("Documento sem conteúdo legível.", normal_style))

        if progress_callback:
            progress_callback(80.0, "Renderizando PDF com alta fidelidade...")

        doc.build(story, canvasmaker=NumberedCanvas)

        if progress_callback:
            progress_callback(100.0, "Conversão DOCX -> PDF concluída!")

        return output_pdf_path

    @classmethod
    def docx_to_text(cls, docx_path: str, output_path: str, fmt: str = 'txt') -> str:
        """Converte DOCX para TXT, MD ou HTML"""
        elements = cls._parse_docx_file(docx_path)
        out_lines = []

        for el in elements:
            t = el.get('type')
            if t == 'heading1':
                out_lines.append(f"# {el['text']}\n" if fmt == 'md' else f"{el['text'].upper()}\n")
            elif t == 'heading2':
                out_lines.append(f"## {el['text']}\n" if fmt == 'md' else f"{el['text']}\n")
            elif t == 'paragraph':
                out_lines.append(f"{el['text']}\n")
            elif t == 'table':
                for r in el['rows']:
                    out_lines.append(" | ".join(r) + "\n")
                out_lines.append("\n")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(out_lines))

        return output_path

    # =========================================================================
    # TEXT / MARKDOWN / HTML TO PDF / DOCX
    # =========================================================================

    @classmethod
    def text_to_pdf(cls, text_path: str, output_pdf_path: str, is_markdown: bool = False) -> str:
        """Converte arquivo de texto simples ou Markdown para PDF elegante"""
        with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_text = f.read()

        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=A4,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        normal_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#2D3748")
        )
        h1_style = ParagraphStyle(
            'H1',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#1A365D"),
            spaceBefore=14,
            spaceAfter=8
        )
        h2_style = ParagraphStyle(
            'H2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#2B6CB0"),
            spaceBefore=10,
            spaceAfter=6
        )

        story = []
        for line in raw_text.splitlines():
            line_str = line.strip()
            if not line_str:
                story.append(Spacer(1, 6))
                continue

            if is_markdown:
                if line_str.startswith('# '):
                    story.append(Paragraph(html.escape(line_str[2:]), h1_style))
                elif line_str.startswith('## '):
                    story.append(Paragraph(html.escape(line_str[3:]), h2_style))
                elif line_str.startswith('### '):
                    story.append(Paragraph(html.escape(line_str[4:]), h2_style))
                elif line_str.startswith('- ') or line_str.startswith('* '):
                    bullet_text = f"• {html.escape(line_str[2:])}"
                    story.append(Paragraph(bullet_text, normal_style))
                else:
                    story.append(Paragraph(html.escape(line_str), normal_style))
            else:
                story.append(Paragraph(html.escape(line_str), normal_style))

        doc.build(story, canvasmaker=NumberedCanvas)
        return output_pdf_path

    @classmethod
    def text_to_docx(cls, text_path: str, output_docx_path: str) -> str:
        with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        paragraphs = []
        for l in lines:
            t = l.strip()
            if t:
                is_h = t.startswith('# ') or (len(t) < 60 and t.isupper())
                clean_t = t.lstrip('#').strip()
                paragraphs.append({'text': clean_t, 'is_heading': is_h})

        cls._create_docx_file(paragraphs, output_docx_path)
        return output_docx_path

    # =========================================================================
    # SPREADSHEETS: CSV, XLSX, JSON, XML
    # =========================================================================

    @classmethod
    def csv_to_xlsx(cls, csv_path: str, output_xlsx_path: str) -> str:
        """Converte CSV para XLSX com cabeçalho estilizado e ajuste inteligente de colunas"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Dados"

        # Detect delimiter
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            sample = f.read(4096)
            try:
                dialect = csv.Sniffer().sniff(sample)
                delimiter = dialect.delimiter
            except Exception:
                delimiter = ',' if ',' in sample else ';'

        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f, delimiter=delimiter)
            for r_idx, row in enumerate(reader, 1):
                for c_idx, val in enumerate(row, 1):
                    cell = ws.cell(row=r_idx, column=c_idx)
                    # Convert to numeric if possible
                    try:
                        if '.' in val or ',' in val:
                            cell.value = float(val.replace(',', '.'))
                        else:
                            cell.value = int(val)
                    except ValueError:
                        cell.value = val

        # Style header row
        header_fill = PatternFill(start_color="2B6CB0", end_color="2B6CB0", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )

        for col in range(1, ws.max_column + 1):
            h_cell = ws.cell(row=1, column=col)
            h_cell.fill = header_fill
            h_cell.font = header_font
            h_cell.alignment = Alignment(horizontal="center", vertical="center")

        # Auto-fit column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(50, max(max_len + 3, 12))

        wb.save(output_xlsx_path)
        return output_xlsx_path

    @classmethod
    def xlsx_to_csv(cls, xlsx_path: str, output_csv_path: str) -> str:
        """Converte planilha XLSX para CSV em UTF-8 com delimitador padrão"""
        wb = openpyxl.load_workbook(xlsx_path, data_only=True)
        ws = wb.active

        with open(output_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for row in ws.iter_rows(values_only=True):
                # Filter out completely empty rows
                if any(v is not None for v in row):
                    writer.writerow([str(v) if v is not None else '' for v in row])

        wb.close()
        return output_csv_path

    @classmethod
    def spreadsheet_to_pdf(cls, input_path: str, output_pdf_path: str) -> str:
        """Renderiza CSV ou XLSX em uma tabela PDF elegante e legível"""
        ext = Path(input_path).suffix.lower()
        rows_data = []

        if ext == '.csv':
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                rows_data = list(reader)
        elif ext in ['.xlsx', '.xls']:
            wb = openpyxl.load_workbook(input_path, data_only=True)
            ws = wb.active
            for r in ws.iter_rows(values_only=True):
                if any(v is not None for v in r):
                    rows_data.append([str(v) if v is not None else '' for v in r])
            wb.close()

        if not rows_data:
            raise ValueError("Planilha vazia ou sem dados para converter.")

        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        cell_style = ParagraphStyle(
            'Cell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#2D3748")
        )
        h_cell_style = ParagraphStyle(
            'HCell',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#FFFFFF")
        )

        formatted_rows = []
        for r_idx, row in enumerate(rows_data[:500]):  # Limit to 500 rows for PDF safety
            row_cells = []
            for c in row:
                st = h_cell_style if r_idx == 0 else cell_style
                row_cells.append(Paragraph(html.escape(str(c)[:100]), st))
            formatted_rows.append(row_cells)

        t = Table(formatted_rows, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F7FAFC")]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

        doc.build([t], canvasmaker=NumberedCanvas)
        return output_pdf_path

    @classmethod
    def json_to_csv_or_xlsx(cls, json_path: str, output_path: str, target_fmt: str) -> str:
        """Converte JSON estruturado em CSV ou XLSX tabular"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict):
            # Try to find list inside dict
            list_key = next((k for k, v in data.items() if isinstance(v, list)), None)
            data = data[list_key] if list_key else [data]

        if not isinstance(data, list) or not data:
            raise ValueError("O arquivo JSON não contém uma lista de registros válidos para tabela.")

        # Extract all unique keys as columns
        keys = list({k for row in data if isinstance(row, dict) for k in row.keys()})

        if target_fmt == 'csv':
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for item in data:
                    if isinstance(item, dict):
                        writer.writerow({k: item.get(k, '') for k in keys})
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "JSON Export"
            ws.append(keys)
            for item in data:
                if isinstance(item, dict):
                    ws.append([str(item.get(k, '')) for k in keys])
            wb.save(output_path)

        return output_path

    # =========================================================================
    # INTERNAL DOCX PACKAGING & PARSING (ZERO EXTERNAL DEPENDENCY)
    # =========================================================================

    @classmethod
    def _create_docx_file(cls, paragraphs: List[Dict[str, Any]], output_path: str):
        """Cria um arquivo DOCX padrão Office Open XML limpo e compatível com Microsoft Word"""
        content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

        rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

        body_elements = []
        for p in paragraphs:
            text = html.escape(p.get('text', ''))
            is_heading = p.get('is_heading', False)

            if is_heading:
                # Heading styled paragraph
                p_xml = f"""    <w:p>
      <w:pPr>
        <w:pStyle w:val="Heading1"/>
        <w:spacing w:before="240" w:after="120"/>
        <w:rPr>
          <w:b/>
          <w:color w:val="2B6CB0"/>
          <w:sz w:val="32"/>
        </w:rPr>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:b/>
          <w:color w:val="2B6CB0"/>
          <w:sz w:val="32"/>
        </w:rPr>
        <w:t xml:space="preserve">{text}</w:t>
      </w:r>
    </w:p>"""
            else:
                p_xml = f"""    <w:p>
      <w:pPr>
        <w:spacing w:after="160" w:line="276" w:lineRule="auto"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:sz w:val="22"/>
          <w:color w:val="1A202C"/>
        </w:rPr>
        <w:t xml:space="preserve">{text}</w:t>
      </w:r>
    </w:p>"""
            body_elements.append(p_xml)

        doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
{chr(10).join(body_elements)}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>"""

        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml', content_types)
            z.writestr('_rels/.rels', rels)
            z.writestr('word/document.xml', doc_xml)

    @classmethod
    def _parse_docx_file(cls, docx_path: str) -> List[Dict[str, Any]]:
        """Lê os elementos estruturais de um arquivo DOCX (parágrafos, títulos e tabelas)"""
        elements = []
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

        with zipfile.ZipFile(docx_path, 'r') as z:
            doc_xml = z.read('word/document.xml')

        root = ET.fromstring(doc_xml)
        body = root.find('w:body', ns)
        if body is None:
            return elements

        for child in body:
            tag = child.tag.split('}')[-1]
            if tag == 'p':
                # Paragraph
                text = "".join(child.itertext()).strip()
                if not text:
                    continue

                # Check if heading
                pPr = child.find('w:pPr', ns)
                is_h1 = False
                is_h2 = False
                if pPr is not None:
                    pStyle = pPr.find('w:pStyle', ns)
                    if pStyle is not None:
                        val = pStyle.attrib.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '')
                        if 'Heading1' in val or 'heading 1' in val.lower():
                            is_h1 = True
                        elif 'Heading2' in val or 'heading 2' in val.lower():
                            is_h2 = True

                if is_h1:
                    elements.append({'type': 'heading1', 'text': text})
                elif is_h2:
                    elements.append({'type': 'heading2', 'text': text})
                else:
                    elements.append({'type': 'paragraph', 'text': text})

            elif tag == 'tbl':
                # Table
                table_rows = []
                for tr in child.findall('w:tr', ns):
                    row_cells = []
                    for tc in tr.findall('w:tc', ns):
                        cell_text = "".join(tc.itertext()).strip()
                        row_cells.append(cell_text)
                    table_rows.append(row_cells)
                if table_rows:
                    elements.append({'type': 'table', 'rows': table_rows})

        return elements
