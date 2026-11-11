import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

breaks = []
for idx, child in enumerate(body):
    if child.tag.endswith('p') and child.xpath('.//w:sectPr'):
        # Get preceding paragraph text
        prev_txt = ""
        for j in range(idx - 1, -1, -1):
            if body[j].tag.endswith('p'):
                txt = docx.text.paragraph.Paragraph(body[j], doc).text.strip()
                if txt:
                    prev_txt = txt
                    break
        breaks.append((idx, prev_txt))

print(f"Total breaks: {len(breaks)}")
for i, (b_idx, txt) in enumerate(breaks):
    print(f"Break {i:02d} at body[{b_idx:03d}] -> Preceded by: '{txt[:50]}'")
