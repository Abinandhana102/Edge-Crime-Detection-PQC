import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
body = doc._element.body

# Find Section 13 elements (Chapter 3 Content)
# Start is 254, End is 263
p_break = body[263]
elements_to_remove = [body[i] for i in range(254, 263)]

for el in elements_to_remove:
    body.remove(el)

print(f"Removed {len(elements_to_remove)} old elements from Section 13.")
doc.save('test_sect13_cleaned.docx')
print("Saved test_sect13_cleaned.docx successfully.")
