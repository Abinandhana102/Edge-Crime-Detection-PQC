import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

print(f"Total elements in body: {len(body)}")
counts = {}
for child in body:
    tag = child.tag.split('}')[-1]
    counts[tag] = counts.get(tag, 0) + 1

print("Body element tags:", counts)
