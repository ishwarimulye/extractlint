import extractlint

print("=== pymupdf adapter ===")
report = extractlint.inspect("sample_report.pdf", extractor="pymupdf")
print(report.summary())
report.save("inspection_report.html")

print("\n=== pdfplumber adapter ===")
report2 = extractlint.inspect("sample_report.pdf", extractor="pdfplumber")
print(report2.summary())

print("\n=== user-supplied text (simulating a bad extractor) ===")
bad_extraction = {
    1: "Project Report quarterly",  # deliberately truncated
    2: "",                          # simulating extractor that choked on the table
    3: "",
}
report3 = extractlint.inspect("sample_report.pdf", extracted=bad_extraction)
print(report3.summary())