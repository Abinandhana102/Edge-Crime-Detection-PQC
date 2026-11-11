import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

# Find Section 13 break (index 263)
p_break = body[263]

# Create a test table
table = doc.add_table(rows=2, cols=2)
table.rows[0].cells[0].text = "Header 1"
table.rows[0].cells[1].text = "Header 2"
table.rows[1].cells[0].text = "Data 1"
table.rows[1].cells[1].text = "Data 2"

# Move table before p_break
p_break.addprevious(table._element)

print("Moved table before p_break successfully!")
