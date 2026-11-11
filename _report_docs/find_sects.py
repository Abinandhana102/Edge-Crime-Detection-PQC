import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')

for i, p in enumerate(doc.paragraphs):
    if p._element.xpath('.//w:sectPr'):
        print(f"P{i}: len={len(p.text)}, text='{p.text[:40]}'")
