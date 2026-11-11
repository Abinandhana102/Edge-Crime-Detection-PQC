# -*- coding: utf-8 -*-
"""
Full Master Report Generator for MCET 23CSP701
Title: EDGE AI-BASED CRIME DETECTION AND QUANTUM-SAFE DIGITAL EVIDENCE MANAGEMENT FRAMEWORK
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

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
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

def update_table_of_contents(table):
    toc_data = [
        ("CHAPTER NO.", "TITLE", "PAGE NO."),
        ("", "ABSTRACT", "i"),
        ("", "LIST OF TABLES", "vii"),
        ("", "LIST OF FIGURES", "viii"),
        ("", "LIST OF ABBREVIATIONS", "ix"),
        ("1", "INTRODUCTION", "1"),
        ("", "1.1 Overview of Intelligent Surveillance and Threat Detection", "1"),
        ("", "1.2 Importance of Automated Edge-Level Crime Detection", "2"),
        ("", "1.3 Role of Post-Quantum Cryptography in Forensic Evidence Protection", "3"),
        ("", "1.4 Objective of the System", "5"),
        ("2", "LITERATURE SURVEY", "7"),
        ("", "2.1 Real-Time Deep Learning Architectures for Weapon Identification", "7"),
        ("", "2.2 Spatial-Temporal Optical Flow for Physical Violence Recognition", "8"),
        ("", "2.3 Geometric Ray-Casting for Perimeter Geo-Fencing Surveillance", "9"),
        ("", "2.4 Temporal Persistence Tracking for Abandoned Luggage Detection", "10"),
        ("", "2.5 NIST Post-Quantum Cryptography Standardization and Lattice KEMs", "11"),
        ("", "2.6 Authenticated Symmetric Video Encryption with AES-256-GCM", "12"),
        ("", "2.7 Tamper-Evident Hashing and Digital Forensics Chain of Custody", "13"),
        ("", "2.8 Edge Computing Paradigms for Low-Latency Video Analytics", "14"),
        ("", "2.9 Real-Time WebSocket Telemetry in Police Command Dispatch", "15"),
        ("", "2.10 Role-Based Cryptographic Access Control in Law Enforcement", "16"),
        ("3", "EXISTING SYSTEM", "18"),
        ("", "3.1 Overview of the Existing System", "18"),
        ("", "3.2 Block Diagram of the Existing System", "19"),
        ("", "3.3 Drawbacks of the Existing System", "20"),
        ("4", "PROPOSED SYSTEM", "22"),
        ("", "4.1 Overview of the Proposed System", "22"),
        ("", "4.2 Block Diagram of the Proposed System", "23"),
        ("", "4.3 Module Description", "24"),
        ("", "4.3.1 Data Acquisition and Video Stream Preprocessing Pipeline", "24"),
        ("", "4.3.2 Real-Time Edge AI Multi-Threat Detection Pipeline (YOLOv8)", "25"),
        ("", "4.3.3 Spatial-Temporal Optical Flow Violence & Anomaly Classifier", "26"),
        ("", "4.3.4 Restricted Area Perimeter Intrusion Engine (Ray-Casting Algorithm)", "27"),
        ("", "4.3.5 Stationary Luggage and Abandoned Object Tracker", "28"),
        ("", "4.3.6 Circular Rolling Video Buffer & Debounce Controller", "29"),
        ("", "4.3.7 Hybrid Post-Quantum Cryptographic Engine (AES-GCM + ML-KEM-768)", "30"),
        ("", "4.3.8 Police Command HQ Tactical Dashboard & Secure Evidence Vault", "31"),
        ("", "4.4 Mathematical and Cryptographic Formulations", "32"),
        ("5", "IMPLEMENTATION AND SETUP", "35"),
        ("", "5.1 Implementation Overview", "35"),
        ("", "5.2 Development Environment and Specifications", "35"),
        ("", "5.3 Dataset Preparation and Threat Category Mapping", "37"),
        ("", "5.4 Edge AI Detection Pipeline Integration", "38"),
        ("", "5.5 Post-Quantum Cryptographic Engine Integration (.qsep Container)", "40"),
        ("", "5.6 Command Dashboard and WebSocket Streaming Infrastructure", "41"),
        ("6", "RESULTS AND DISCUSSION", "43"),
        ("", "6.1 Experimental Setup and Evaluation Metrics", "43"),
        ("", "6.2 Threat Detection Performance Evaluation", "44"),
        ("", "6.3 Cryptographic Latency and Throughput Analysis", "46"),
        ("", "6.4 Evidence Tamper Verification and Chain of Custody Integrity", "47"),
        ("", "6.5 Comparative Discussion Against Conventional Architectures", "48"),
        ("7", "CONCLUSION AND FUTURE ENHANCEMENT", "50"),
        ("", "7.1 Conclusion", "50"),
        ("", "7.2 Future Enhancement", "51"),
        ("", "REFERENCES", "53"),
        ("", "APPENDIX A ( SOURCE CODE )", "56"),
        ("", "APPENDIX B ( SNAPSHOTS )", "66"),
        ("", "APPENDIX C ( CERTIFICATES )", "71"),
    ]

    for row_idx, item in enumerate(toc_data):
        if row_idx < len(table.rows):
            row = table.rows[row_idx]
            ch_num, title, pg_num = item
            row.cells[0].text = ch_num
            row.cells[1].text = title
            row.cells[4].text = pg_num

            is_main = bool(ch_num) or title.startswith("APPENDIX") or title in ["ABSTRACT", "LIST OF TABLES", "LIST OF FIGURES", "LIST OF ABBREVIATIONS", "REFERENCES"]
            for c_idx in [0, 1, 4]:
                cell = row.cells[c_idx]
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if c_idx == 4 else (WD_ALIGN_PARAGRAPH.CENTER if c_idx == 0 else WD_ALIGN_PARAGRAPH.LEFT)
                    for r in p.runs:
                        set_font(r, "Times New Roman", 12, bold=is_main)

def update_list_of_tables(table):
    tables_data = [
        ("TABLE NO.", "TITLE", "PAGE NO."),
        ("5.1", "Software and Hardware Environment Specifications", "36"),
        ("6.1", "Threat Detection Performance Evaluation Across AI Modules", "45"),
        ("6.2", "Post-Quantum Cryptographic and Vault Latency Benchmark", "46"),
        ("6.3", "Tamper-Evident SHA-256 Hash Verification Test Matrix", "47"),
        ("6.4", "Comprehensive Architectural Comparison Matrix", "49")
    ]
    while len(table.rows) < len(tables_data):
        table.add_row()
    for row_idx, (t_no, title, pg) in enumerate(tables_data):
        row = table.rows[row_idx]
        row.cells[0].text = t_no
        row.cells[1].text = title
        row.cells[2].text = pg
        is_header = (row_idx == 0)
        for c_idx, cell in enumerate(row.cells):
            if is_header:
                set_cell_background(cell, "EAEAEA")
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 2] else WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    set_font(r, "Times New Roman", 12, bold=is_header)

def update_list_of_figures(table):
    figures_data = [
        ("FIGURE NO.", "TITLE", "PAGE NO."),
        ("3.1", "Block Diagram of Existing Video Surveillance Systems", "19"),
        ("4.1", "Architecture of Proposed Edge AI and Quantum Evidence Framework", "23"),
        ("4.2", "Hybrid Post-Quantum Cryptographic Pipeline (AES-256-GCM + ML-KEM-768)", "30"),
        ("6.1", "Threat Detection Performance Metrics Across Modules", "45"),
        ("6.2", "Processing and Cryptographic Latency Benchmark", "46"),
        ("B.1", "Police Command HQ Real-Time Tactical Dashboard & Multi-Camera Grid", "66"),
        ("B.2", "YOLOv8 Weapon Detection and Optical Flow Violence Classification", "67"),
        ("B.3", "Geofenced Perimeter Intrusion Detection with Polygon Overlay", "68"),
        ("B.4", "Quantum Evidence Vault Decapsulation & Integrity Verification", "69")
    ]
    while len(table.rows) < len(figures_data):
        table.add_row()
    for row_idx, (f_no, title, pg) in enumerate(figures_data):
        row = table.rows[row_idx]
        row.cells[0].text = f_no
        row.cells[1].text = title
        row.cells[2].text = pg
        is_header = (row_idx == 0)
        for c_idx, cell in enumerate(row.cells):
            if is_header:
                set_cell_background(cell, "EAEAEA")
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 2] else WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    set_font(r, "Times New Roman", 12, bold=is_header)

def update_abbreviations(table):
    abbrevs = [
        ("AES", "Advanced Encryption Standard (AES-256-GCM)"),
        ("AI", "Artificial Intelligence"),
        ("API", "Application Programming Interface"),
        ("CCTV", "Closed-Circuit Television"),
        ("CNN", "Convolutional Neural Network"),
        ("CPU", "Central Processing Unit"),
        ("CUDA", "Compute Unified Device Architecture (NVIDIA)"),
        ("DVR", "Digital Video Recorder"),
        ("FIFO", "First-In, First-Out (Circular Video Ring Buffer)"),
        ("FPS", "Frames Per Second"),
        ("GCM", "Galois/Counter Mode (Authenticated Cipher)"),
        ("GPU", "Graphics Processing Unit"),
        ("HUD", "Heads-Up Display (Command Telemetry)"),
        ("IEEE", "Institute of Electrical and Electronics Engineers"),
        ("IoU", "Intersection over Union (Bounding Box Overlap)"),
        ("IV", "Initialization Vector (Random Nonce)"),
        ("JWT", "JSON Web Token (Authentication & RBAC)"),
        ("KEM", "Key Encapsulation Mechanism"),
        ("LWE", "Learning With Errors (Lattice-Based Math)"),
        ("ML", "Machine Learning"),
        ("ML-KEM", "Module-Lattice Key Encapsulation (NIST FIPS 203)"),
        ("mAP", "Mean Average Precision"),
        ("NVR", "Network Video Recorder"),
        ("NIST", "National Institute of Standards and Technology"),
        ("NTT", "Number Theoretic Transform"),
        ("PQC", "Post-Quantum Cryptography"),
        ("RBAC", "Role-Based Access Control"),
        ("REST", "Representational State Transfer"),
        ("RGB", "Red, Green, Blue Color Space"),
        ("RTSP", "Real-Time Streaming Protocol"),
        ("SDG", "Sustainable Development Goals (United Nations)"),
        ("SHA", "Secure Hash Algorithm (SHA-256)"),
        ("SPA", "Single-Page Application"),
        ("TRL", "Technology Readiness Level"),
        ("UI", "User Interface"),
        ("ViT", "Vision Transformer"),
        ("YOLO", "You Only Look Once (Real-Time Object Detector)")
    ]
    while len(table.rows) < len(abbrevs):
        table.add_row()
    for row_idx, (abbr, desc) in enumerate(abbrevs):
        row = table.rows[row_idx]
        row.cells[0].text = abbr
        row.cells[2].text = desc
        for c_idx in [0, 2]:
            cell = row.cells[c_idx]
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx == 0 else WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    set_font(r, "Times New Roman", 12, bold=(c_idx == 0))

print("Front matter updater configured.")
