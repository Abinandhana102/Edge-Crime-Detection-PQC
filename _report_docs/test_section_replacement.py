import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

# Let's inspect Section 13 (Chapter 3 Content) between 254 and 263
p_break = body[263]
p_break_obj = docx.text.paragraph.Paragraph(p_break, doc)

# Create a test paragraph and add it before p_break
test_p = doc.add_paragraph("TEST NEW PARAGRAPH", style="cfr_Chaptercontent")
# Move it before p_break
p_break.addprevious(test_p._element)

print("Added paragraph before break. Success!")
