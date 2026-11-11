import docx

doc = docx.Document('23CSP701_Project_Phase_1_Report_Final_Submission.docx')

current_ch = 'FRONT MATTER'
ch_map = {current_ch: []}

for i, p in enumerate(doc.paragraphs):
    txt = p.text.strip()
    if 'CHAPTER' in txt.upper() and len(txt) < 30:
        current_ch = txt
        ch_map[current_ch] = []
    elif txt:
        ch_map[current_ch].append((i, p.style.name, txt))

print("=== VERIFICATION OF ALL CHAPTERS ===")
for ch, items in ch_map.items():
    headings = [f"{st}: {t[:60]}" for idx, st, t in items if st.startswith('Heading') or st == 'cfr_ChapterHead']
    print(f"\n{ch} ({len(items)} paragraphs total):")
    for h in headings[:10]:
        print("  *", h)
    body_samples = [t[:90] for idx, st, t in items if st == 'cfr_Chaptercontent']
    if body_samples:
        print(f"   Sample Body text: \"{body_samples[0]}...\"")

print(f"\nTotal Tables in document: {len(doc.tables)}")
for idx, tbl in enumerate(doc.tables[9:], start=1):
    print(f"  Table {idx}: {len(tbl.rows)} rows x {len(tbl.columns)} cols -> Header: {[c.text.strip() for c in tbl.rows[0].cells]}")
