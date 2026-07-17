_ADAPTERS = {}


def register_adapter(name: str, fn):
    """
    Register a new extractor adapter.
    `fn` must be a callable: fn(pdf_path: str) -> list[ExtractedPage]
    """
    _ADAPTERS[name] = fn


def get_adapter(name: str):
    if name not in _ADAPTERS:
        available = ", ".join(sorted(_ADAPTERS.keys())) or "(none registered)"
        raise ValueError(
            f"Unknown extractor '{name}'. Available adapters: {available}. "
            f"Register a new one with extractlint.register_adapter()."
        )
    return _ADAPTERS[name]


def _register_builtins():
    from .adapters import pymupdf_adapter, pdfplumber_adapter
    register_adapter("pymupdf", pymupdf_adapter.extract)
    register_adapter("pdfplumber", pdfplumber_adapter.extract)


_register_builtins()