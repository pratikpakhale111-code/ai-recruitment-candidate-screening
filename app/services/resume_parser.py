from __future__ import annotations

import re
from io import BytesIO

from docx import Document
from pypdf import PdfReader

MAX_RESUME_BYTES = 10 * 1024 * 1024
MAX_RESUME_PAGES = 50
MAX_EXTRACTED_CHARACTERS = 250_000


class ResumeProcessingError(ValueError):
    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


def _safe_filename(filename: str) -> str:
    return filename.replace("\\", "/").split("/")[-1].strip()


def extract_resume_text(filename: str, contents: bytes) -> tuple[str, str]:
    """Extract text from a PDF or DOCX without saving the uploaded file."""
    safe_filename = _safe_filename(filename)
    extension = safe_filename.rsplit(".", maxsplit=1)[-1].lower() if "." in safe_filename else ""

    if extension not in {"pdf", "docx"}:
        raise ResumeProcessingError("Upload a PDF or DOCX resume.", status_code=415)
    if not safe_filename or not contents:
        raise ResumeProcessingError("The uploaded resume is empty or has no filename.")

    try:
        if extension == "pdf":
            if not contents.startswith(b"%PDF-"):
                raise ResumeProcessingError("The file does not appear to be a valid PDF.")
            reader = PdfReader(BytesIO(contents), strict=False)
            if reader.is_encrypted:
                raise ResumeProcessingError("Password-protected PDFs are not supported.")
            if len(reader.pages) > MAX_RESUME_PAGES:
                raise ResumeProcessingError(f"Resumes may contain at most {MAX_RESUME_PAGES} pages.")
            extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            if not contents.startswith(b"PK\x03\x04"):
                raise ResumeProcessingError("The file does not appear to be a valid DOCX document.")
            document = Document(BytesIO(contents))
            parts = [paragraph.text for paragraph in document.paragraphs]
            parts.extend(
                cell.text
                for table in document.tables
                for row in table.rows
                for cell in row.cells
            )
            extracted = "\n".join(parts)
    except ResumeProcessingError:
        raise
    except Exception as exc:
        raise ResumeProcessingError("The resume could not be read. Check the file and try again.") from exc

    text = re.sub(r"\x00", "", extracted).strip()
    if not text:
        raise ResumeProcessingError(
            "No readable text was found. Scanned image-only PDFs need OCR before upload."
        )
    if len(text) > MAX_EXTRACTED_CHARACTERS:
        raise ResumeProcessingError("The extracted resume text is too long to process safely.")

    return safe_filename[:255], text
