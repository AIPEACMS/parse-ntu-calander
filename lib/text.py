"""PDF text extraction helpers (thin wrapper around poppler's pdftotext)."""

import re
import subprocess
from pathlib import Path


def pdf_to_text(pdf_path: Path) -> str:
    """Extract layout-preserved text from a PDF (requires pdftotext)."""
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def detect_year(text: str) -> str:
    """Extract the academic year, e.g. 'AY2026-27' from the header."""
    m = re.search(r"AY\s*(\d{4})-(\d{2})", text)
    if not m:
        raise ValueError("could not detect academic year (expected 'AY2026-27')")
    return f"{m.group(1)}-{m.group(2)}"


def clean(s: str) -> str:
    """Collapse runs of whitespace to a single space."""
    return re.sub(r"\s+", " ", s).strip()
