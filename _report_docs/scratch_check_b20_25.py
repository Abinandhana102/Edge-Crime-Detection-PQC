import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

breaks = []
for idx, child in enumerate(body):
    if child.tag.endswith('p') and child.xpath('.//w:sectPr'):
        breaks.append(idx)

for b_idx in range(20, len(breaks)):
    idx = breaks[b_idx]
    txt = ''.join(body[idx].itertext()).strip()
    print(f"=== Break {b_idx} at body[{idx}]: '{txt[:40]}' ===")
    for k in range(max(0, idx-2), idx):
        print(f"   pre[{k}]: {''.join(body[k].itertext()).strip()[:50]}")
    for k in range(idx+1, min(len(body), idx+3)):
        print(f"   post[{k}]: {''.join(body[k].itertext()).strip()[:50]}")
