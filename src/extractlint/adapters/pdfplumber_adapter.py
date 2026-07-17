import pdfplumber
from ..core import ExtractedPage


def extract(pdf_path: str) -> list:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            tables = page.extract_tables()
            pages.append(ExtractedPage(
                page_number=i + 1,
                text=text,
                has_tables=len(tables) > 0,
                table_count=len(tables),
            ))
    return pages