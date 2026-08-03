"""
conftest.py
------------
Shared pytest fixtures: an in-memory sample resume PDF (built with
reportlab so the test suite has zero external file dependencies), plus
convenience text fixtures.
"""

import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from reportlab.pdfgen import canvas


SAMPLE_RESUME_LINES = [
    "Jane Smith",
    "jane.smith@email.com | +1 9876543210",
    "linkedin.com/in/janesmith | github.com/janesmith",
    "",
    "Education",
    "B.Tech Computer Science, XYZ University, 2024",
    "",
    "Experience",
    "Software Engineering Intern at ABC Corp",
    "- Built a chatbot using Python and NLP",
    "",
    "Projects",
    "- Built a chatbot using Python and NLP",
    "- Developed a web app using Flask and React",
    "- Created a machine learning model with scikit-learn",
    "",
    "Skills",
    "Python, SQL, Machine Learning, Git, Docker, Flask, React",
    "",
    "Certifications",
    "AWS Certified Cloud Practitioner",
]


def _build_pdf_bytes(lines) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    y = 800
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
        if y < 50:
            c.showPage()
            y = 800
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def sample_resume_pdf_bytes() -> bytes:
    return _build_pdf_bytes(SAMPLE_RESUME_LINES)


@pytest.fixture
def sample_resume_pdf_buffer(sample_resume_pdf_bytes):
    buf = io.BytesIO(sample_resume_pdf_bytes)
    buf.name = "sample_resume.pdf"
    return buf


@pytest.fixture
def empty_pdf_buffer():
    buf = io.BytesIO(_build_pdf_bytes([""]))
    buf.name = "empty.pdf"
    return buf


@pytest.fixture
def sample_resume_text() -> str:
    return "\n".join(SAMPLE_RESUME_LINES)


@pytest.fixture
def sample_job_description() -> str:
    return (
        "We are looking for a Python developer with experience in "
        "AWS, Docker, Kubernetes, REST API, and Machine Learning."
    )


@pytest.fixture
def isolated_db_path(tmp_path) -> str:
    """Every test that touches the DB gets its own throwaway SQLite file
    (passed explicitly to db.py functions via their db_path parameter)."""
    return str(tmp_path / "test_resumeiq.db")
