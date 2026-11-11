import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

for idx, child in enumerate(body):
    if child.tag.endswith('p') and child.xpath('.//w:sectPr'):
        p = docx.text.paragraph.Paragraph(child, doc)
        # also print previous 2 elements text
        prev_txt = []
        for prev_idx in range(max(0, idx - 2), idx + 1):
            prev_child = body[prev_idx]
            if prev_child.tag.endswith('p'):
                prev_txt.append(docx.text.paragraph.Paragraph(prev_child, doc).text.strip())
        print(f"Break at body[{idx}]: {prev_txt}")
