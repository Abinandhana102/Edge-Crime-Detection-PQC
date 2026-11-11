import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')

for t_idx in [4, 5, 6, 7]:
    tbl = doc.tables[t_idx]
    print(f"\n=== Table {t_idx} (rows: {len(tbl.rows)}, cols: {len(tbl.columns)}) ===")
    for r_idx in range(min(5, len(tbl.rows))):
        row = tbl.rows[r_idx]
        vals = [c.text.strip().replace('\n', ' ') for c in row.cells]
        print(f"Row {r_idx}: {vals}")
