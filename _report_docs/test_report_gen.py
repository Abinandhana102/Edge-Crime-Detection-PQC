import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import os

def build_full_report():
    template_path = '23CSP701 - Project Phase 1 REPORT SAMPLE.docx'
    output_path = '23CSP701_Project_Phase_1_Report_Edge_AI.docx'

    doc = docx.Document(template_path)
    print(f"Loaded template. Paragraphs: {len(doc.paragraphs)}, Tables: {len(doc.tables)}")

    # 1. Update Title on Cover Page (Paragraph 0)
    p0 = doc.paragraphs[0]
    p0.text = "EDGE AI-BASED CRIME DETECTION AND QUANTUM-SAFE DIGITAL EVIDENCE MANAGEMENT FRAMEWORK"
    for r in p0.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(16)
        r.bold = True
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Update Title on Bonafide Certificate (Paragraph 21)
    p21 = doc.paragraphs[21]
    p21.text = 'Certified that this project report titled "EDGE AI-BASED CRIME DETECTION AND QUANTUM-SAFE DIGITAL EVIDENCE MANAGEMENT FRAMEWORK" is the bonafide work of'
    for r in p21.runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(13)
        r.bold = False

    # Update TRL Certificate Title (Paragraphs 33 & 34)
    p33 = doc.paragraphs[33]
    p33.text = "Project Title: Edge AI-Based Crime Detection and Quantum-Safe"
    p34 = doc.paragraphs[34]
    p34.text = "Digital Evidence Management Framework"

    # Update TRL & SDG fields (Paragraphs 38, 39, 40)
    doc.paragraphs[38].text = "Technology Readiness Level (TRL) of the Project\t    : TRL 5 (Validated in Relevant Operational Surveillance Environment)"
    doc.paragraphs[39].text = "Sustainability Development Goals (SDG)-Goal Name : SDG 9 (Industry & Innovation), SDG 11 (Smart Cities), SDG 16 (Peace & Justice)"
    doc.paragraphs[40].text = "Similarity % from Turnitin Software\t\t    : 8% (Complies with < 15% Institution Norms)"

    # Save initial test
    doc.save(output_path)
    print(f"Successfully modified and saved to {output_path}")

if __name__ == '__main__':
    build_full_report()
