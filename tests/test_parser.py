import io

import pytest

from utils.exceptions import EmptyResumeError, InvalidFileError, ResumeParsingError
from utils.parser import (
    extract_email, extract_github, extract_linkedin, extract_name, extract_phone,
    parse_resume, validate_uploaded_file,
)


class TestFieldExtraction:
    def test_extract_email_found(self):
        assert extract_email("Contact: jane.smith@email.com please") == "jane.smith@email.com"

    def test_extract_email_not_found(self):
        assert extract_email("No email here") == ""

    def test_extract_email_handles_none(self):
        assert extract_email(None) == ""

    def test_extract_phone_found(self):
        assert extract_phone("Call me at +1 9876543210 anytime") != ""

    def test_extract_phone_ignores_short_numbers(self):
        # A 4-digit number (e.g. a year-like token) should not be treated as a phone
        assert extract_phone("Graduated in 2024") == ""

    def test_extract_linkedin_found(self):
        assert "linkedin.com" in extract_linkedin("Profile: linkedin.com/in/janesmith")

    def test_extract_github_found(self):
        assert "github.com" in extract_github("Code: github.com/janesmith")

    def test_extract_name_skips_email_line(self):
        text = "jane.smith@email.com\nJane Smith\nEducation"
        # first non-email/phone/header line should be picked
        name = extract_name(text)
        assert name in ("Jane Smith", "Not Found")  # heuristic; must not crash

    def test_extract_name_empty_text(self):
        assert extract_name("") == "Not Found"

    def test_extract_name_handles_none(self):
        assert extract_name(None) == "Not Found"


class TestValidation:
    def test_validate_rejects_none(self):
        with pytest.raises(InvalidFileError):
            validate_uploaded_file(None)

    def test_validate_rejects_wrong_extension(self):
        buf = io.BytesIO(b"hello")
        buf.name = "resume.docx"
        with pytest.raises(InvalidFileError):
            validate_uploaded_file(buf)

    def test_validate_rejects_empty_file(self):
        buf = io.BytesIO(b"")
        buf.name = "resume.pdf"
        with pytest.raises(InvalidFileError):
            validate_uploaded_file(buf)

    def test_validate_rejects_oversized_file(self):
        buf = io.BytesIO(b"0" * (11 * 1024 * 1024))  # 11 MB > 10 MB limit
        buf.name = "resume.pdf"
        with pytest.raises(InvalidFileError):
            validate_uploaded_file(buf)

    def test_validate_accepts_valid_pdf(self, sample_resume_pdf_buffer):
        # should not raise
        validate_uploaded_file(sample_resume_pdf_buffer)


class TestParseResume:
    def test_parse_resume_full_pipeline(self, sample_resume_pdf_buffer):
        result = parse_resume(sample_resume_pdf_buffer)
        assert result["email"] == "jane.smith@email.com"
        assert result["phone"] != ""
        assert "linkedin.com" in result["linkedin"]
        assert "github.com" in result["github"]
        assert result["sections"]["Education"] is True
        assert result["sections"]["Projects"] is True
        assert result["project_count"] >= 1
        assert result["word_count"] > 0

    def test_parse_resume_rejects_invalid_file_type(self):
        buf = io.BytesIO(b"not a pdf")
        buf.name = "resume.txt"
        with pytest.raises(InvalidFileError):
            parse_resume(buf)

    def test_parse_resume_raises_on_near_empty_pdf(self, empty_pdf_buffer):
        with pytest.raises((EmptyResumeError, ResumeParsingError)):
            parse_resume(empty_pdf_buffer)

    def test_parse_resume_raises_on_corrupt_pdf(self):
        buf = io.BytesIO(b"%PDF-1.4 this is not really a valid pdf structure")
        buf.name = "corrupt.pdf"
        with pytest.raises((ResumeParsingError, InvalidFileError)):
            parse_resume(buf)
