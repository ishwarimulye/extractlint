import fitz

doc = fitz.open()

# Page 1: normal text page (should score OK)
page1 = doc.new_page()
page1.insert_text((72, 72), "Project Report", fontsize=16)
body = ("This document summarizes the quarterly progress of the project.\n"
        "Development is on track, with all major milestones completed on schedule. "
        "The team has resolved outstanding issues and testing is proceeding smoothly. "
        "Next steps include final review and deployment.")
page1.insert_textbox(fitz.Rect(72, 100, 500, 300), body, fontsize=11)

# Page 2: a real table (tests table-detection)
page2 = doc.new_page()
page2.insert_text((72, 72), "Budget Summary", fontsize=16)
rows = [
    ["Category", "Amount", "Status"],
    ["Development", "$12,000", "On track"],
    ["Marketing", "$4,500", "Under budget"],
    ["Operations", "$3,200", "On track"],
]
y = 110
for row in rows:
    x = 72
    for cell in row:
        page2.insert_text((x, y), cell, fontsize=10)
        x += 150
    y += 25
page2.draw_rect(fitz.Rect(70, 95, 470, 205))

# Page 3: scanned-image page, no real text layer -- should get flagged critical
page3 = doc.new_page()
tmp_doc = fitz.open()
tmp_page = tmp_doc.new_page()
tmp_page.insert_textbox(fitz.Rect(50, 50, 500, 300),
    "Signed Approval Form\nApproved by: A. Sharma\nDate: 12 July 2026\nStatus: Final sign-off complete",
    fontsize=14)
pix = tmp_page.get_pixmap(matrix=fitz.Matrix(1, 1))
page3.insert_image(fitz.Rect(0, 0, 595, 842), pixmap=pix)
tmp_doc.close()

doc.save("sample_report.pdf", garbage=4, deflate=True)
doc.close()
print("Created sample_report.pdf (3 pages: normal, table, scanned-image)")