import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body
breaks = [child for child in body if child.tag.endswith('p') and child.xpath('.//w:sectPr')]

for idx, b in enumerate(breaks):
    runs = b.xpath('.//w:r')
    txt = ''.join(b.itertext()).strip()
    if runs or txt:
        print(f"Break {idx}: runs={len(runs)} | text='{txt[:60]}'")
