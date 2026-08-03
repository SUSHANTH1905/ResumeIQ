"""
ats.py
-------
Calculates an ATS (Applicant Tracking System) style score for a parsed
resume, broken down by category, per the rubric defined in config.py:

    Skills                 - 40
    Education              - 15
    Experience             - 15
    Projects               - 15
    Certifications         - 10
    Contact Information    - 5
    ------------------------------
    Total                  - 100
"""

from config import ATS_MAX_SCORES, TARGET_PROJECT_COUNT, TARGET_SKILL_COUNT


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def score_skills(skill_count: int) -> float:
    skill_count = max(0, int(skill_count or 0))
    ratio = min(skill_count / TARGET_SKILL_COUNT, 1.0)
    return round(ratio * ATS_MAX_SCORES["Skills"], 2)


def score_education(sections: dict) -> float:
    sections = sections or {}
    return float(ATS_MAX_SCORES["Education"]) if sections.get("Education") else 0.0


def score_experience(sections: dict) -> float:
    sections = sections or {}
    has_experience = (
        sections.get("Experience") or sections.get("Work Experience")
        or sections.get("Internship") or sections.get("Internships")
    )
    return float(ATS_MAX_SCORES["Experience"]) if has_experience else 0.0


def score_projects(project_count: int) -> float:
    project_count = max(0, int(project_count or 0))
    ratio = min(project_count / TARGET_PROJECT_COUNT, 1.0)
    return round(ratio * ATS_MAX_SCORES["Projects"], 2)


def score_certifications(sections: dict) -> float:
    sections = sections or {}
    return float(ATS_MAX_SCORES["Certifications"]) if sections.get("Certifications") else 0.0


def score_contact_info(parsed_resume: dict) -> float:
    parsed_resume = parsed_resume or {}
    fields_present = sum([
        bool(parsed_resume.get("email")),
        bool(parsed_resume.get("phone")),
        bool(parsed_resume.get("linkedin")) or bool(parsed_resume.get("github")),
    ])
    return round((fields_present / 3) * ATS_MAX_SCORES["Contact Information"], 2)


def calculate_ats_score(parsed_resume: dict, skills_found: list) -> dict:
    """
    Computes the full ATS score breakdown for a parsed resume.

    Args:
        parsed_resume: dict returned by parser.parse_resume(). Must
            contain at least 'sections' and 'project_count' keys;
            missing/None values are treated as "not present" rather
            than raising, so this never crashes the UI mid-analysis.
        skills_found: list of skills detected by
            skill_matcher.find_skills_in_text().

    Returns:
        dict with per-category scores, max scores, and total (0-100).
    """
    parsed_resume = parsed_resume or {}
    skills_found = skills_found or []
    sections = parsed_resume.get("sections", {}) or {}

    breakdown = {
        "Skills": score_skills(len(skills_found)),
        "Education": score_education(sections),
        "Experience": score_experience(sections),
        "Projects": score_projects(parsed_resume.get("project_count", 0)),
        "Certifications": score_certifications(sections),
        "Contact Information": score_contact_info(parsed_resume),
    }

    total = round(sum(breakdown.values()), 2)
    total = _clamp(total)  # defensive: never report outside 0-100

    return {
        "breakdown": breakdown,
        "max_scores": dict(ATS_MAX_SCORES),
        "total": total,
    }
