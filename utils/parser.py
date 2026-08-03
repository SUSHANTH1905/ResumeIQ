"""
parser.py
----------
Extracts raw text and structured fields (name, email, phone, links,
sections) from an uploaded resume (PDF). Every function validates its
inputs and raises a specific ResumeIQ exception on failure instead of
letting a raw library exception (or a silent bad value) leak upward.
"""

import os
import re

import pdfplumber

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, MIN_EXTRACTED_WORD_COUNT
from utils.exceptions import EmptyResumeError, InvalidFileError, ResumeParsingError
from utils.logging_config import get_logger

logger = get_logger("parser")

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
LINKEDIN_REGEX = r"(https?://)?(www\.)?linkedin\.com/[a-zA-Z0-9\-_/]+"
GITHUB_REGEX = r"(https?://)?(www\.)?github\.com/[a-zA-Z0-9\-_/]+"

SECTION_HEADERS = [
    "summary", "objective", "education", "experience", "work experience",
    "projects", "skills", "certifications", "achievements", "languages",
    "contact", "profile", "internship", "internships", "publications",
]


def _get_file_size_bytes(file_obj) -> int:
    """
    Works for both a filesystem path (str/Path) and a file-like object
    (e.g. Streamlit's UploadedFile, which exposes .size and .seek()).
    """
    if hasattr(file_obj, "size"):
        return file_obj.size
    if hasattr(file_obj, "read"):
        pos = file_obj.tell() if hasattr(file_obj, "tell") else 0
        file_obj.seek(0, os.SEEK_END)
        size = file_obj.tell()
        file_obj.seek(pos)
        return size
    return os.path.getsize(file_obj)


def _get_file_name(file_obj) -> str:
    if hasattr(file_obj, "name"):
        return file_obj.name
    return str(file_obj)


def validate_uploaded_file(file_obj) -> None:
    """
    Validates a file before any parsing is attempted.

    Raises:
        InvalidFileError: if the extension is unsupported or the file is
            missing / oversized.
    """
    if file_obj is None:
        raise InvalidFileError("No file was provided.")

    name = _get_file_name(file_obj)
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileError(
            f"Unsupported file type '{ext or 'unknown'}'. "
            f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    try:
        size_bytes = _get_file_size_bytes(file_obj)
    except OSError as exc:
        raise InvalidFileError(f"Could not read file size: {exc}") from exc

    if size_bytes <= 0:
        raise InvalidFileError("The uploaded file is empty.")

    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise InvalidFileError(
            f"File is too large ({size_bytes / (1024 * 1024):.1f} MB). "
            f"Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
        )


def extract_text_from_pdf(file_path_or_buffer) -> str:
    """
    Extracts raw text from a PDF resume using pdfplumber.

    Raises:
        ResumeParsingError: if the PDF cannot be opened or read at all
            (corrupted file, password-protected, unsupported format).
    """
    text_chunks = []
    try:
        with pdfplumber.open(file_path_or_buffer) as pdf:
            if len(pdf.pages) == 0:
                raise ResumeParsingError("The PDF contains no pages.")
            for page_number, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text()
                except Exception as exc:  # pdfplumber can raise various low-level errors
                    logger.warning("Failed to extract text from page %s: %s", page_number, exc)
                    page_text = None
                if page_text:
                    text_chunks.append(page_text)
    except ResumeParsingError:
        raise
    except Exception as exc:
        logger.exception("Failed to open/parse PDF")
        raise ResumeParsingError(
            "Could not read the PDF. It may be corrupted, password-protected, "
            "or in an unsupported format."
        ) from exc

    return "\n".join(text_chunks)


def extract_email(text: str) -> str:
    match = re.search(EMAIL_REGEX, text or "")
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    for match in re.finditer(PHONE_REGEX, text or ""):
        digits = re.sub(r"\D", "", match.group(0))
        if 9 <= len(digits) <= 13:
            return match.group(0).strip()
    return ""


def extract_linkedin(text: str) -> str:
    match = re.search(LINKEDIN_REGEX, text or "", re.IGNORECASE)
    return match.group(0) if match else ""


def extract_github(text: str) -> str:
    match = re.search(GITHUB_REGEX, text or "", re.IGNORECASE)
    return match.group(0) if match else ""


def extract_name(text: str) -> str:
    """
    Heuristic: the candidate's name is usually the first non-empty line
    that doesn't look like an email, phone number, URL, or section header.
    """
    lines = [l.strip() for l in (text or "").split("\n") if l.strip()]
    for line in lines[:5]:
        lower = line.lower()
        if "@" in line or re.search(PHONE_REGEX, line):
            continue
        if "linkedin.com" in lower or "github.com" in lower or "http" in lower:
            continue
        if any(h in lower for h in SECTION_HEADERS):
            continue
        if 0 < len(line.split()) <= 5 and len(line) < 60:
            return line
    return "Not Found"


def detect_sections(text: str) -> dict:
    lower_text = (text or "").lower()
    return {header.title(): (header in lower_text) for header in SECTION_HEADERS}


def count_projects(text: str) -> int:
    lower_text = (text or "").lower()
    if "projects" not in lower_text:
        return 0

    start = lower_text.find("projects")
    end = len(text)
    for header in SECTION_HEADERS:
        if header == "projects":
            continue
        idx = lower_text.find(header, start + len("projects"))
        if idx != -1:
            end = min(end, idx)

    section_text = text[start:end]
    bullets = re.findall(r"(?:^|\n)\s*(?:[-•*]|\d+\.)\s+", section_text)
    if bullets:
        return len(bullets)

    lines = [l for l in section_text.split("\n") if l.strip()]
    return max(len(lines) - 1, 0)


def parse_resume(file_obj, skip_validation: bool = False) -> dict:
    """
    Main entry point: validates, extracts, and structures a resume PDF.

    Args:
        file_obj: path string/Path, or file-like object (e.g. Streamlit
            UploadedFile).
        skip_validation: set True only for trusted, already-validated
            in-memory buffers (e.g. inside test fixtures).

    Raises:
        InvalidFileError, ResumeParsingError, EmptyResumeError
    """
    if not skip_validation:
        validate_uploaded_file(file_obj)

    text = extract_text_from_pdf(file_obj)

    word_count = len(text.split())
    if word_count < MIN_EXTRACTED_WORD_COUNT:
        raise EmptyResumeError(
            "Very little or no text could be extracted from this PDF. "
            "It may be a scanned image without OCR text, or empty."
        )

    return {
        "raw_text": text,
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "linkedin": extract_linkedin(text),
        "github": extract_github(text),
        "sections": detect_sections(text),
        "project_count": count_projects(text),
        "word_count": word_count,
    }
