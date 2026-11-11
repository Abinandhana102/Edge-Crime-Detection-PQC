import docx

doc = docx.Document('23CSP701_Project_Phase_1_Report_Final_Submission.docx')
body = doc._element.body

def get_text(el):
    if el.tag.endswith('p'):
        return docx.text.paragraph.Paragraph(el, doc).text.strip()
    return ""

found = False
for idx, child in enumerate(body):
    txt = get_text(child)
    if "CHAPTER 3" in txt:
        print(f"CHAPTER 3 found at body[{idx}]: '{txt}'")
        found = True

if not found:
    print("CHAPTER 3 was NOT found!")
