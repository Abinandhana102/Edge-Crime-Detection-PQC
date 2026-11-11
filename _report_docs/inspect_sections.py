import docx

doc = docx.Document('23CSP701 - Project Phase 1 REPORT SAMPLE.docx')

sections = [
    ("ABSTRACT", 76, 82),
    ("ACKNOWLEDGEMENT", 83, 114),
    ("TOC", 115, 123),
    ("LIST OF TABLES", 124, 135),
    ("LIST OF FIGURES", 136, 143),
    ("LIST OF ABBREVIATIONS", 144, 169),
    ("CHAPTER 1", 170, 218),
    ("CHAPTER 2", 219, 242),
    ("CHAPTER 3", 243, 270),
    ("CHAPTER 4", 271, 302),
    ("CHAPTER 5", 303, 337),
    ("CHAPTER 6", 338, 373),
    ("CHAPTER 7", 374, 397),
    ("REFERENCES", 398, 422),
    ("APPENDIX A", 423, 476),
    ("APPENDIX B", 477, 511),
    ("APPENDIX C", 512, 525)
]

for name, start, end in sections:
    print(f"\n--- {name} (P{start} to P{end}) ---")
    for i in range(start, min(start + 6, end + 1)):
        p = doc.paragraphs[i]
        if p.text.strip():
            print(f"  P{i} [{p.style.name}]: {p.text[:80]}")
