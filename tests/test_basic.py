import fitz
import pytest
import extractlint


@pytest.fixture(scope="module")
def sample_pdf(tmp_path_factory):
    """Builds a small 2-page PDF: one normal text page, one scanned-image page."""
    path = tmp_path_factory.mktemp("data") / "sample.pdf"
    doc = fitz.open()

    p1 = doc.new_page()
    p1.insert_textbox(fitz.Rect(72, 72, 500, 300),
                       "This is a normal page with plenty of readable text content for testing purposes.",
                       fontsize=11)

    p2 = doc.new_page()
    tmp = fitz.open()
    tp = tmp.new_page()
    tp.insert_textbox(fitz.Rect(50, 50, 500, 300), "Scanned content", fontsize=14)
    pix = tp.get_pixmap(matrix=fitz.Matrix(1, 1))
    p2.insert_image(fitz.Rect(0, 0, 595, 842), pixmap=pix)
    tmp.close()

    doc.save(str(path))
    doc.close()
    return str(path)


def test_good_extraction_scores_ok(sample_pdf):
    report = extractlint.inspect(sample_pdf, extractor="pymupdf")
    page1 = report.pages[0]
    assert page1.severity == "ok"
    assert page1.density_ratio == 1.0


def test_scanned_page_flagged_critical(sample_pdf):
    report = extractlint.inspect(sample_pdf, extractor="pymupdf")
    page2 = report.pages[1]
    assert page2.severity == "critical"
    assert page2.suspected_scanned is True


def test_user_supplied_text_low_density_flagged(sample_pdf):
    report = extractlint.inspect(sample_pdf, extracted={1: "tiny", 2: ""})
    assert report.pages[0].severity in ("warning", "critical")
    assert len(report.flagged_pages) == 2


def test_user_supplied_list_of_strings(sample_pdf):
    report = extractlint.inspect(
        sample_pdf,
        extracted=["This is a normal page with plenty of readable text content for testing purposes.", ""],
    )
    assert report.pages[0].severity == "ok"


def test_custom_adapter_registration(sample_pdf):
    def dummy(pdf_path):
        return [extractlint.ExtractedPage(page_number=1, text="x" * 100),
                extractlint.ExtractedPage(page_number=2, text="")]

    extractlint.register_adapter("dummy_test_adapter", dummy)
    report = extractlint.inspect(sample_pdf, extractor="dummy_test_adapter")
    assert report.extractor_name == "dummy_test_adapter"


def test_raises_if_both_or_neither_arg_given(sample_pdf):
    with pytest.raises(ValueError):
        extractlint.inspect(sample_pdf)
    with pytest.raises(ValueError):
        extractlint.inspect(sample_pdf, extracted="x", extractor="pymupdf")


def test_unknown_extractor_raises(sample_pdf):
    with pytest.raises(ValueError):
        extractlint.inspect(sample_pdf, extractor="does_not_exist")


def test_report_save_produces_html(sample_pdf, tmp_path):
    report = extractlint.inspect(sample_pdf, extractor="pymupdf")
    out = tmp_path / "out.html"
    report.save(str(out))
    assert out.exists()
    content = out.read_text()
    assert "<html>" in content
    assert "Page 1" in content