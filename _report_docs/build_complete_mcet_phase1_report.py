# -*- coding: utf-8 -*-
"""
Definitive Master Phase 1 Report Generator for MCET 23CSP701
Complete in-depth descriptions for Chapters 1, 2, 3, 4, 5, 6, 7 and Appendices
"""
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import os

def set_font(run, name="Times New Roman", size_pt=12, bold=False, italic=False, color_rgb=(0,0,0)):
    run.font.name = name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    if color_rgb:
        run.font.color.rgb = RGBColor(*color_rgb)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_background(cell, fill_hex="F2F2F2"):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def create_p(doc, text, style_name="cfr_Chaptercontent", align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, bold=False, italic=False, space_after=6, line_spacing=1.5):
    p = doc.add_paragraph(style=style_name)
    p.text = text
    p.alignment = align
    p.paragraph_format.line_spacing = line_spacing
    p.paragraph_format.space_after = Pt(space_after)
    for r in p.runs:
        set_font(r, "Times New Roman", size, bold=bold, italic=italic)
    return p

def create_img_p(doc, img_path, caption_text, width_inches=5.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    if os.path.exists(img_path):
        p.add_run().add_picture(img_path, width=Inches(width_inches))
    
    p_cap = doc.add_paragraph()
    p_cap.text = caption_text
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_after = Pt(12)
    for r in p_cap.runs:
        set_font(r, "Times New Roman", 12, bold=True)
    return p, p_cap

def format_table(table, col_widths, headers, data, header_bg="EAEAEA"):
    # Set header row
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], header_bg)
        set_cell_margins(hdr_cells[i], 120, 120, 150, 150)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            set_font(r, "Times New Roman", 11, bold=True)
    
    # Set data rows
    for r_idx, row_data in enumerate(data):
        row_cells = table.rows[r_idx + 1].cells
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].text = str(val)
            set_cell_margins(row_cells[c_idx], 100, 100, 140, 140)
            p = row_cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, len(row_data)-1] or len(val) <= 10 else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                set_font(r, "Times New Roman", 10.5, bold=False)
    
    # Set column widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = Inches(width)

print("Base builder helpers defined.")
