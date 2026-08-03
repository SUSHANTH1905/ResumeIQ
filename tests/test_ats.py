from config import ATS_MAX_SCORES
from utils.ats import calculate_ats_score, score_projects, score_skills


class TestScoreSkills:
    def test_zero_skills_scores_zero(self):
        assert score_skills(0) == 0.0

    def test_target_count_scores_max(self):
        assert score_skills(10) == ATS_MAX_SCORES["Skills"]

    def test_exceeding_target_caps_at_max(self):
        assert score_skills(50) == ATS_MAX_SCORES["Skills"]

    def test_negative_input_handled_gracefully(self):
        # should not raise or go negative
        assert score_skills(-5) == 0.0

    def test_none_input_handled_gracefully(self):
        assert score_skills(None) == 0.0


class TestScoreProjects:
    def test_zero_projects_scores_zero(self):
        assert score_projects(0) == 0.0

    def test_full_projects_scores_max(self):
        assert score_projects(3) == ATS_MAX_SCORES["Projects"]

    def test_partial_projects_scales_linearly(self):
        assert score_projects(1) == round((1 / 3) * ATS_MAX_SCORES["Projects"], 2)


class TestCalculateAtsScore:
    def test_full_resume_scores_100(self):
        parsed_resume = {
            "email": "a@b.com", "phone": "1234567890", "linkedin": "linkedin.com/x",
            "github": "github.com/x", "project_count": 5,
            "sections": {
                "Education": True, "Experience": True, "Certifications": True,
            },
        }
        skills_found = [f"skill{i}" for i in range(15)]
        result = calculate_ats_score(parsed_resume, skills_found)
        assert result["total"] == 100.0

    def test_empty_resume_scores_zero(self):
        result = calculate_ats_score({}, [])
        assert result["total"] == 0.0

    def test_handles_none_inputs_without_crashing(self):
        result = calculate_ats_score(None, None)
        assert result["total"] == 0.0

    def test_handles_missing_sections_key(self):
        result = calculate_ats_score({"project_count": 1}, ["Python"])
        assert 0.0 <= result["total"] <= 100.0

    def test_breakdown_never_exceeds_max_per_category(self):
        parsed_resume = {
            "email": "a@b.com", "phone": "1", "linkedin": "x", "github": "y",
            "project_count": 999,
            "sections": {"Education": True, "Experience": True, "Certifications": True},
        }
        skills_found = [f"skill{i}" for i in range(999)]
        result = calculate_ats_score(parsed_resume, skills_found)
        for category, score in result["breakdown"].items():
            assert score <= ATS_MAX_SCORES[category]

    def test_total_always_between_0_and_100(self):
        # fuzz a handful of combinations
        cases = [
            ({}, []),
            ({"project_count": 3, "sections": {"Education": True}}, ["Python"] * 3),
            ({"project_count": -1, "sections": None}, None),
        ]
        for parsed_resume, skills in cases:
            result = calculate_ats_score(parsed_resume, skills)
            assert 0.0 <= result["total"] <= 100.0
