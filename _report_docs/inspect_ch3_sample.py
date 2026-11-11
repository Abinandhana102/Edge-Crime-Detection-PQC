import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

def get_text(el):
    if el.tag.endswith('p'):
        return docx.text.paragraph.Paragraph(el, doc).text.strip()
    return ""

# find all p with CHAPTER 3
for idx, child in enumerate(body):
    txt = get_text(child)
    if "CHAPTER 3" in txt:
        print(f"CHAPTER 3 at body[{idx}]: '{txt}'")
        # print next 15 elements
        for j in range(idx, min(idx + 15, len(body))):
            print(f"  body[{j}] (has sectPr={bool(body[j].xpath('.//w:sectPr'))}): '{get_text(body[j])[:50]}'")
