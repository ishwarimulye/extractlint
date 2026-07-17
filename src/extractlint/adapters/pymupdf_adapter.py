import fitz
from ..core import ExtractedPage


def extract(pdf_path: str) -> list:
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        try:
            tables = page.find_tables()
            table_count = len(tables.tables)
        except Exception:
            table_count = 0
        pages.append(ExtractedPage(
            page_number=i + 1,
            text=text,
            has_tables=table_count > 0,
            table_count=table_count,
        ))
    doc.close()
    return pages