import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

for idx, child in enumerate(body):
    if child.tag.endswith('p'):
        p = docx.text.paragraph.Paragraph(child, doc)
        txt = p.text.strip()
        if any(k in txt.lower() for k in ['experimental results', 'performance evaluation', 'conclusion and future', 'references']):
            print(f"[{idx}] {p.style.name}: '{txt[:60]}'")
