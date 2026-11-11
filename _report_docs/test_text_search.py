import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

def get_text(el):
    if el.tag.endswith('p'):
        return docx.text.paragraph.Paragraph(el, doc).text.strip()
    return ""

for idx, child in enumerate(body):
    txt = get_text(child)
    has_sect = bool(child.xpath('.//w:sectPr'))
    if any(k in txt for k in ['CHAPTER', 'EXISTING SYSTEM', 'PROPOSED SYSTEM', 'IMPLEMENTATION AND SETUP', 'RESULT AND DISCUSSION', 'CONCLUSION AND FUTURE']):
        print(f"[{idx}] (sectPr={has_sect}): '{txt}'")
