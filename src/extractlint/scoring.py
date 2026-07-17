import re
import fitz
from .core import ExtractedPage, PageDiagnostics

DENSITY_WARNING_THRESHOLD = 0.5
DENSITY_CRITICAL_THRESHOLD = 0.2
GARBLE_WARNING_THRESHOLD = 0.15
GARBLE_CRITICAL_THRESHOLD = 0.35

_GARBLE_PATTERN = re.compile(r"[^\w\s.,;:!?()\-'\"/%$]")


def _looks_like_scanned_page(pdf_page, expected_chars: int) -> bool:
    if expected_chars > 20:
        return False
    try:
        page_area = pdf_page.rect.width * pdf_page.rect.height
        image_area = 0.0
        for img in pdf_page.get_images(full=True):
            for rect in pdf_page.get_image_rects(img[0]):
                image_area += rect.width * rect.height
        return page_area > 0 and (image_area / page_area) > 0.5
    except Exception:
        return False


def _detect_table_likelihood(pdf_page) -> bool:
    try:
        return len(pdf_page.find_tables().tables) > 0
    except Exception:
        return False


def _garbled_ratio(text: str) -> float:
    if not text.strip():
        return 0.0
    return len(_GARBLE_PATTERN.findall(text)) / max(len(text), 1)


def score_page(pdf_page, extracted: ExtractedPage) -> PageDiagnostics:
    baseline_text = pdf_page.get_text("text")
    expected = len(baseline_text.strip())
    actual = extracted.char_count
    ratio = (actual / expected) if expected > 0 else (1.0 if actual == 0 else 0.0)

    scanned_page = _looks_like_scanned_page(pdf_page, expected)
    has_table_signal = _detect_table_likelihood(pdf_page)
    suspected_table_loss = has_table_signal and not extracted.has_tables
    garble = _garbled_ratio(extracted.text)

    reasons = []
    severity = "ok"

    if scanned_page:
        severity = "critical"
        reasons.append("page appears to be a scanned image with no real text layer -- extractor likely needs OCR")

    if ratio < DENSITY_CRITICAL_THRESHOLD:
        severity = "critical"
        reasons.append(f"only {ratio:.0%} of expected text extracted")
    elif ratio < DENSITY_WARNING_THRESHOLD:
        severity = "warning" if severity == "ok" else severity
        reasons.append(f"only {ratio:.0%} of expected text extracted")

    if suspected_table_loss:
        severity = "critical" if severity != "ok" else "warning"
        reasons.append("page appears to contain a table that wasn't captured")

    if garble > GARBLE_CRITICAL_THRESHOLD:
        severity = "critical"
        reasons.append(f"{garble:.0%} of extracted text looks garbled")
    elif garble > GARBLE_WARNING_THRESHOLD:
        severity = "warning" if severity == "ok" else severity
        reasons.append(f"{garble:.0%} of extracted text looks garbled")

    return PageDiagnostics(
        page_number=extracted.page_number,
        expected_char_estimate=expected,
        actual_char_count=actual,
        density_ratio=round(ratio, 3),
        suspected_table_loss=suspected_table_loss,
        suspected_scanned=scanned_page,
        extracted_text_snippet=extracted.text.strip()[:500],
        baseline_text_snippet=baseline_text.strip()[:500],
        garbled_text_ratio=round(garble, 3),
        severity=severity,
        reasons=reasons,
    )