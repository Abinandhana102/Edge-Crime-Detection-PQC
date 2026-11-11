import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

break_info = []
for idx, child in enumerate(body):
    if child.tag.endswith('p') and child.xpath('.//w:sectPr'):
        p_text = ''.join(child.itertext()).strip()
        prev_txt = ''
        if idx > 0 and body[idx-1].tag.endswith('p'):
            prev_txt = ''.join(body[idx-1].itertext()).strip()
        next_txt = ''
        if idx+1 < len(body) and body[idx+1].tag.endswith('p'):
            next_txt = ''.join(body[idx+1].itertext()).strip()
        break_info.append((idx, p_text, prev_txt, next_txt))

print(f"Total breaks found: {len(break_info)}")
for i, (idx, txt, prev, nxt) in enumerate(break_info):
    print(f"Break {i:02d} at body[{idx}]: curr='{txt[:30]}' | prev='{prev[:30]}' | next='{nxt[:30]}'")
