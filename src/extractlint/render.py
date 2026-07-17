import base64
import html
import fitz

_SEVERITY_COLOR = {
    "ok": "#2e7d32",
    "warning": "#e6a700",
    "critical": "#c62828",
}


def _page_to_base64_png(pdf_page, zoom=1.5) -> str:
    mat = fitz.Matrix(zoom, zoom)
    pix = pdf_page.get_pixmap(matrix=mat)
    return base64.b64encode(pix.tobytes("png")).decode("ascii")


def render_html_report(report, out_path: str):
    doc = fitz.open(report.pdf_path)

    rows = []
    for diag in report.pages:
        pdf_page = doc[diag.page_number - 1]
        img_b64 = _page_to_base64_png(pdf_page)
        color = _SEVERITY_COLOR[diag.severity]
        reasons_html = "".join(f"<li>{html.escape(r)}</li>" for r in diag.reasons) or "<li>no issues detected</li>"

        rows.append(f"""
        <div class="page-row">
          <div class="page-img"><img src="data:image/png;base64,{img_b64}" /></div>
          <div class="page-info">
            <div class="badge" style="background:{color}">
              Page {diag.page_number} &mdash; {diag.severity.upper()}
            </div>
            <table class="metrics">
              <tr><td>Expected chars (baseline)</td><td>{diag.expected_char_estimate}</td></tr>
              <tr><td>Extracted chars</td><td>{diag.actual_char_count}</td></tr>
              <tr><td>Density ratio</td><td>{diag.density_ratio}</td></tr>
              <tr><td>Garbled text ratio</td><td>{diag.garbled_text_ratio}</td></tr>
              <tr><td>Suspected table loss</td><td>{diag.suspected_table_loss}</td></tr>
            </table>
            <ul class="reasons">{reasons_html}</ul>
            <div class="text-compare">
              <div class="text-col">
                <div class="text-label">Extracted text (what your extractor returned)</div>
                <pre>{html.escape(diag.extracted_text_snippet) or "(empty)"}</pre>
              </div>
              <div class="text-col">
                <div class="text-label">Baseline text (PyMuPDF's own reading of this page)</div>
                <pre>{html.escape(diag.baseline_text_snippet) or "(empty)"}</pre>
              </div>
            </div>
          </div>
        </div>
        """)

    html_doc = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>PDF Extraction Inspection Report</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; background:#fafafa; color:#222; margin:0; padding:24px; }}
  h1 {{ font-size: 20px; }}
  .summary {{ background:#fff; border:1px solid #ddd; border-radius:8px; padding:16px; margin-bottom:24px; white-space:pre-wrap; font-family: monospace; font-size: 13px; }}
  .page-row {{ display:flex; gap:20px; background:#fff; border:1px solid #ddd; border-radius:8px; margin-bottom:16px; padding:16px; }}
  .page-img img {{ max-width: 320px; border:1px solid #ccc; }}
  .page-info {{ flex:1; }}
  .badge {{ display:inline-block; color:#fff; padding:4px 10px; border-radius:6px; font-size:13px; font-weight:600; margin-bottom:10px; }}
  table.metrics {{ border-collapse: collapse; font-size: 13px; margin-bottom: 10px; }}
  table.metrics td {{ padding: 2px 10px 2px 0; }}
  ul.reasons {{ font-size: 13px; margin:0; padding-left: 18px; }}
  .text-compare {{ display:flex; gap:12px; margin-top:12px; }}
  .text-col {{ flex:1; min-width:0; }}
  .text-label {{ font-size:11px; color:#666; margin-bottom:4px; font-weight:600; }}
  .text-col pre {{ background:#f4f4f4; border:1px solid #ddd; border-radius:6px; padding:8px; font-size:12px; max-height:180px; overflow:auto; white-space:pre-wrap; word-break:break-word; margin:0; }}
</style></head>
<body>
  <h1>PDF Extraction Inspection &mdash; {html.escape(report.pdf_path)}</h1>
  <div class="summary">{html.escape(report.summary())}</div>
  {''.join(rows)}
</body></html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_doc)

    doc.close()
    return out_path