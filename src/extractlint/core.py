from dataclasses import dataclass, field


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    has_tables: bool = False
    table_count: int = 0
    char_count: int = field(init=False)

    def __post_init__(self):
        self.char_count = len(self.text.strip())


@dataclass
class PageDiagnostics:
    page_number: int
    expected_char_estimate: int
    actual_char_count: int
    density_ratio: float
    suspected_table_loss: bool
    garbled_text_ratio: float
    severity: str
    suspected_scanned: bool = False
    extracted_text_snippet: str = ""
    baseline_text_snippet: str = ""
    reasons: list = field(default_factory=list)

    @property
    def is_flagged(self) -> bool:
        return self.severity in ("warning", "critical")


@dataclass
class InspectionReport:
    pdf_path: str
    extractor_name: str
    pages: list

    @property
    def flagged_pages(self):
        return [p for p in self.pages if p.is_flagged]

    @property
    def critical_pages(self):
        return [p for p in self.pages if p.severity == "critical"]

    def summary(self) -> str:
        total = len(self.pages)
        flagged = len(self.flagged_pages)
        critical = len(self.critical_pages)
        lines = [
            f"Inspected {total} pages using extractor '{self.extractor_name}'",
            f"  {total - flagged} OK",
            f"  {flagged - critical} warnings",
            f"  {critical} critical (likely broken extraction)",
        ]
        if self.flagged_pages:
            lines.append("Flagged pages:")
            for p in self.flagged_pages:
                lines.append(f"  - page {p.page_number} [{p.severity}]: {', '.join(p.reasons)}")
        return "\n".join(lines)

    def save(self, path: str):
        from .render import render_html_report
        render_html_report(self, path)

    def show(self):
        import tempfile, webbrowser, os
        fd, path = tempfile.mkstemp(suffix=".html")
        os.close(fd)
        self.save(path)
        webbrowser.open(f"file://{path}")
        return path