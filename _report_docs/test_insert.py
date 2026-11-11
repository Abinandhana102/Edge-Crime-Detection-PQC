import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')
p = doc.paragraphs[180]
new_p = p.insert_paragraph_before("Test inserted paragraph", "cfr_Chaptercontent")
print("Inserted successfully! Style:", new_p.style.name)
