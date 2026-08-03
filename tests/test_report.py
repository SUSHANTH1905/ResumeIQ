from utils.report import build_docx_report, build_pdf_report


SAMPLE_PARSED_RESUME = {
    "name": "Jane Smith", "email": "jane@example.com", "phone": "9876543210",
    "linkedin": "linkedin.com/in/janesmith", "github": "github.com/janesmith",
    "project_count": 3,
}
SAMPLE_ATS_RESULT = {
    "breakdown": {"Skills": 40, "Education": 15, "Experience": 15,
                  "Projects": 15, "Certifications": 10, "Contact Information": 5},
    "max_scores": {"Skills": 40, "Education": 15, "Experience": 15,
                   "Projects": 15, "Certifications": 10, "Contact Information": 5},
    "total": 100,
}


class TestPdfReport:
    def test_builds_nonempty_pdf(self):
        pdf_bytes = build_pdf_report(
            SAMPLE_PARSED_RESUME, SAMPLE_ATS_RESULT,
            ["Python", "SQL"], ["Docker"], ["Add more projects."], 80.0,
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

    def test_handles_empty_skills_and_suggestions(self):
        pdf_bytes = build_pdf_report(SAMPLE_PARSED_RESUME, SAMPLE_ATS_RESULT, [], [], [])
        assert pdf_bytes.startswith(b"%PDF")

    def test_handles_missing_optional_fields(self):
        minimal_resume = {"project_count": 0}
        pdf_bytes = build_pdf_report(minimal_resume, SAMPLE_ATS_RESULT, [], [], [])
        assert pdf_bytes.startswith(b"%PDF")


class TestDocxReport:
    def test_builds_nonempty_docx(self):
        docx_bytes = build_docx_report(
            SAMPLE_PARSED_RESUME, SAMPLE_ATS_RESULT,
            ["Python", "SQL"], ["Docker"], ["Add more projects."], 80.0,
        )
        assert isinstance(docx_bytes, bytes)
        assert len(docx_bytes) > 0
        # DOCX files are ZIP archives and start with the ZIP magic number
        assert docx_bytes[:2] == b"PK"

    def test_handles_missing_optional_fields(self):
        minimal_resume = {"project_count": 0}
        docx_bytes = build_docx_report(minimal_resume, SAMPLE_ATS_RESULT, [], [], [])
        assert docx_bytes[:2] == b"PK"
