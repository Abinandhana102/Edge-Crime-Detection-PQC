import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')

print(f"Total paragraphs: {len(doc.paragraphs)}")

# Let's inspect where each chapter divider is and its section break
dividers = []
for i, p in enumerate(doc.paragraphs):
    if p.text.strip().startswith("CHAPTER") or p.text.strip().startswith("APPENDIX") or p.text.strip() in ["ABSTRACT", "ACKNOWLEDGEMENT", "TABLE OF CONTENTS", "LIST OF TABLES", "LIST OF FIGURES", "LIST OF ABBREVIATIONS", "REFERENCES"]:
        dividers.append((i, p.text.strip(), 'w:sectPr' in p._element.xml))

for d in dividers:
    print(d)
