"""
exceptions.py
--------------
Custom exception hierarchy for ResumeIQ so calling code (and the UI
layer) can distinguish between different failure modes instead of
catching a generic Exception everywhere.
"""


class ResumeIQError(Exception):
    """Base class for all ResumeIQ application errors."""


class InvalidFileError(ResumeIQError):
    """Raised when an uploaded file fails validation (type, size, etc.)."""


class EmptyResumeError(ResumeIQError):
    """Raised when a PDF yields no extractable / usable text."""


class ResumeParsingError(ResumeIQError):
    """Raised when the PDF cannot be opened or parsed (corrupt file, etc.)."""


class SkillsDatasetError(ResumeIQError):
    """Raised when the skills dataset is missing, empty, or malformed."""


class ReportGenerationError(ResumeIQError):
    """Raised when PDF/DOCX report generation fails."""


class DatabaseError(ResumeIQError):
    """Raised when a history/database operation fails."""
