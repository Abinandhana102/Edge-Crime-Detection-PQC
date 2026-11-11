import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

breaks = []
for idx, child in enumerate(body):
    if child.tag.endswith('p') and child.xpath('.//w:sectPr'):
        breaks.append(idx)

for i in range(len(breaks) - 1):
    b_curr = breaks[i]
    b_next = breaks[i+1]
    elements = [body[j] for j in range(b_curr + 1, b_next)]
    texts = []
    for el in elements:
        t = ''.join(el.itertext()).strip()
        if t:
            texts.append(t)
    snippet = ' // '.join(texts[:3]) if texts else '(EMPTY)'
    print(f"Between Break {i:02d} (body[{b_curr}]) and Break {i+1:02d} (body[{b_next}]) [{len(elements)} items]: {snippet[:100]}")
