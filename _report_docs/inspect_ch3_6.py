import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

sect_boundaries = [
    ("Chapter 3 Content", 254, 263),
    ("Chapter 4 Content", 282, 295),
    ("Chapter 5 Content", 314, 348),
    ("Chapter 6 Content", 362, 385)
]

for name, start, end in sect_boundaries:
    print(f"\n=== {name} (indices {start} to {end}) ===")
    for idx in range(start, end + 1):
        child = body[idx]
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            p = docx.text.paragraph.Paragraph(child, doc)
            txt = p.text.strip()
            print(f"  [{idx}] p ({p.style.name}): '{txt[:70]}'")
        elif tag == 'tbl':
            t = docx.table.Table(child, doc)
            print(f"  [{idx}] tbl ({len(t.rows)} rows, {len(t.columns)} cols)")
