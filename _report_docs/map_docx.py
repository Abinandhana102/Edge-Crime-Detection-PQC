import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')

print(f"Total paragraphs: {len(doc.paragraphs)}")
print(f"Total tables: {len(doc.tables)}")

sections_map = []
for i, p in enumerate(doc.paragraphs):
    txt = p.text.strip()
    if txt.startswith("CHAPTER") or txt in ["ABSTRACT", "ACKNOWLEDGEMENT", "TABLE OF CONTENTS", "LIST OF TABLES", "LIST OF FIGURES", "LIST OF ABBREVIATIONS", "REFERENCES", "APPENDIX A", "APPENDIX B", "APPENDIX C"]:
        sections_map.append((i, p.style.name, txt))

for item in sections_map:
    print(item)
