import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')

print("=== CHECKING SECTIONS AND BREAKS ===")
for i in range(168, 177):
    p = doc.paragraphs[i]
    print(f"P{i}: len={len(p.text)}, has_br={'w:br' in p._element.xml}, has_sect={'w:sectPr' in p._element.xml}, text='{p.text[:40]}'")

print("\n=== PARAGRAPH 174 DETAILS ===")
p174 = doc.paragraphs[174]
for r in p174.runs:
    print(f"Run text: '{r.text}', font={r.font.name}, size={r.font.size.pt if r.font.size else None}, bold={r.bold}")

print("\n=== PARAGRAPH 175 DETAILS ===")
p175 = doc.paragraphs[175]
for r in p175.runs:
    print(f"Run text: '{r.text}', font={r.font.name}, size={r.font.size.pt if r.font.size else None}, bold={r.bold}")
