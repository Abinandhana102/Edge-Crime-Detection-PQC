import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

sect_indices = []
for idx, child in enumerate(body):
    if child.tag.endswith('p') and child.xpath('.//w:sectPr'):
        p = docx.text.paragraph.Paragraph(child, doc)
        sect_indices.append((idx, p.text.strip()[:40]))

print(f"Total section-break paragraphs in body: {len(sect_indices)}")
for item in sect_indices:
    print(item)
