# -*- coding: utf-8 -*-
"""
Full Document Builder for MCET 23CSP701 Project Phase 1 Report
Generates complete, rigorous, professional, exhaustive chapters 3, 4, 5, 6, 7.
"""
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import os

from generate_complete_mcet_report import (
    update_table_of_contents,
    update_list_of_tables,
    update_list_of_figures,
    update_abbreviations,
    set_font,
    set_cell_background,
    set_cell_margins
)

def add_p(doc, text, style_name="cfr_Chaptercontent", align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12, bold=False, italic=False, space_after=6, line_spacing=1.5):
    p = doc.add_paragraph(style=style_name)
    p.text = text
    p.alignment = align
    p.paragraph_format.line_spacing = line_spacing
    p.paragraph_format.space_after = Pt(space_after)
    for r in p.runs:
        set_font(r, "Times New Roman", size, bold=bold, italic=italic)
    return p

def add_heading(doc, text, level=2, style_name="Heading 2", space_before=12, space_after=6):
    p = doc.add_paragraph(style=style_name)
    p.text = text
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.keep_with_next = True
    size = 14 if level <= 2 else 13
    for r in p.runs:
        set_font(r, "Times New Roman", size, bold=True)
    return p

def add_img(doc, img_path, caption_text, width_inches=5.6):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_after = Pt(4)
    if os.path.exists(img_path):
        p_img.add_run().add_picture(img_path, width=Inches(width_inches))
    
    p_cap = doc.add_paragraph()
    p_cap.text = caption_text
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_after = Pt(12)
    p_cap.paragraph_format.keep_with_next = True
    for r in p_cap.runs:
        set_font(r, "Times New Roman", 12, bold=True)
    return [p_img, p_cap]

def build_table(doc, col_widths, headers, data, header_bg="D9E1F2"):
    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    
    # Headers
    for i, title in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = title
        set_cell_background(cell, header_bg)
        set_cell_margins(cell, 120, 120, 150, 150)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            set_font(r, "Times New Roman", 11, bold=True)
            
    # Data
    for r_idx, row_vals in enumerate(data):
        row = table.rows[r_idx + 1]
        for c_idx, val in enumerate(row_vals):
            cell = row.cells[c_idx]
            cell.text = str(val)
            set_cell_margins(cell, 100, 100, 140, 140)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, len(row_vals)-1] or len(str(val)) <= 10 else WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                set_font(r, "Times New Roman", 10.5, bold=False)
                
    # Widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = Inches(width)
            
    return table

print("Document building blocks compiled.")
