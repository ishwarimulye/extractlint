from typing import Optional, Union
import fitz

from .core import ExtractedPage, PageDiagnostics, InspectionReport
from .scoring import score_page
from .registry import get_adapter, register_adapter  # re-exported


def _normalize_user_supplied(extracted) -> list:
    """
    Accepts whatever a developer already has lying around and converts
    it to list[ExtractedPage].

    Supported inputs:
      - list[ExtractedPage]   (already normalized)
      - list[str]              (one string per page, in order)
      - str                    (single blob -- one page, or split on \\f if present)
      - dict[int, str]         ({page_number: text})
    """
    if isinstance(extracted, list) and extracted and isinstance(extracted[0], ExtractedPage):
        return extracted

    if isinstance(extracted, list):
        return [ExtractedPage(page_number=i + 1, text=t or "") for i, t in enumerate(extracted)]

    if isinstance(extracted, dict):
        return [ExtractedPage(page_number=k, text=v or "") for k, v in sorted(extracted.items())]

    if isinstance(extracted, str):
        if "\f" in extracted:
            parts = extracted.split("\f")
            return [ExtractedPage(page_number=i + 1, text=t) for i, t in enumerate(parts)]
        return [ExtractedPage(page_number=1, text=extracted)]

    raise TypeError(
        "extracted must be list[ExtractedPage], list[str], dict[int, str], or str. "
        f"Got {type(extracted)}."
    )


def inspect(
    pdf_path: str,
    extracted: Optional[Union[list, dict, str]] = None,
    extractor: Optional[str] = None,
) -> InspectionReport:
    """
    Inspect how well a PDF was extracted.

    1. You already ran extraction yourself:
        report = inspect("doc.pdf", extracted=my_text_or_list)

    2. Let this tool run a known extractor for you:
        report = inspect("doc.pdf", extractor="pymupdf")

    Exactly one of `extracted` or `extractor` must be given.
    """
    if (extracted is None) == (extractor is None):
        raise ValueError("Pass exactly one of `extracted` or `extractor`.")

    if extractor is not None:
        adapter_fn = get_adapter(extractor)
        extracted_pages = adapter_fn(pdf_path)
        extractor_name = extractor
    else:
        extracted_pages = _normalize_user_supplied(extracted)
        extractor_name = "user-supplied"

    doc = fitz.open(pdf_path)
    diagnostics = []
    extracted_by_num = {p.page_number: p for p in extracted_pages}

    for i, pdf_page in enumerate(doc):
        page_num = i + 1
        ext_page = extracted_by_num.get(page_num, ExtractedPage(page_number=page_num, text=""))
        diagnostics.append(score_page(pdf_page, ext_page))

    doc.close()

    return InspectionReport(
        pdf_path=pdf_path,
        extractor_name=extractor_name,
        pages=diagnostics,
    )