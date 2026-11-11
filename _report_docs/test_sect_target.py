import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

# Find the section break paragraph for Chapter 3
sect13_break = body[263]
p = docx.text.paragraph.Paragraph(sect13_break, doc)
print("Sect 13 break paragraph found. Has sectPr:", bool(sect13_break.xpath('.//w:sectPr')))
