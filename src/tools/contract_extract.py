"""Turn a PDF or plain-text file into raw contract text.

Equivalent role to the original repo's tools/plan_extract.py, minus the S3 /
AI Hub dependencies — this just reads a local file.
"""

from __future__ import annotations

from pathlib import Path


def load_contract_text(path: str) -> str:
    """Read a contract from a local .pdf or .txt file into plain text."""
    file_path = Path(path).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"No file at {file_path}")

    if file_path.suffix.lower() == ".pdf":
        return _extract_pdf_text(file_path)
    return file_path.read_text(encoding="utf-8", errors="replace")


def extract_text_from_bytes(filename: str, data: bytes) -> str:
    """Same extraction as `load_contract_text`, for bytes already in memory
    (e.g. a browser file upload) instead of a path on the server's disk."""
    if filename.lower().endswith(".pdf"):
        import fitz  # PyMuPDF

        text_parts: list[str] = []
        with fitz.open(stream=data, filetype="pdf") as doc:
            for page in doc:
                text_parts.append(page.get_text())
        return "\n".join(text_parts).strip()
    return data.decode("utf-8", errors="replace")


def _extract_pdf_text(file_path: Path) -> str:
    import fitz  # PyMuPDF

    text_parts: list[str] = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts).strip()
