import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

breaks = []
for idx, child in enumerate(body):
    if child.tag.endswith('p') and child.xpath('.//w:sectPr'):
        breaks.append(idx)

for b_idx in [15, 16, 17, 18, 19]:
    idx = breaks[b_idx]
    p_elem = body[idx]
    txt = ''.join(p_elem.itertext()).strip()
    print(f"=== Break {b_idx} at body[{idx}]: '{txt[:60]}' ===")
    for k in range(max(0, idx-4), idx):
        print(f"   pre[{k}]: {''.join(body[k].itertext()).strip()[:60]}")
    for k in range(idx+1, min(len(body), idx+5)):
        print(f"   post[{k}]: {''.join(body[k].itertext()).strip()[:60]}")
