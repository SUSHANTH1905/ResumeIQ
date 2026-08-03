import pandas as pd
import pytest

from utils.exceptions import SkillsDatasetError
from utils.skill_matcher import (
    compute_match_percentage, extract_missing_skills, find_skills_in_text,
    load_skills_dataset, skill_category_breakdown,
)


class TestLoadSkillsDataset:
    def test_loads_real_dataset(self):
        df = load_skills_dataset()
        assert not df.empty
        assert {"skill", "category"}.issubset(df.columns)

    def test_missing_file_raises(self):
        with pytest.raises(SkillsDatasetError):
            load_skills_dataset("/nonexistent/path/skills.csv")

    def test_empty_file_raises(self, tmp_path):
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")
        with pytest.raises(SkillsDatasetError):
            load_skills_dataset(str(empty_file))

    def test_missing_columns_raises(self, tmp_path):
        bad_file = tmp_path / "bad.csv"
        bad_file.write_text("name,type\nPython,lang\n")
        with pytest.raises(SkillsDatasetError):
            load_skills_dataset(str(bad_file))

    def test_deduplicates_skills(self, tmp_path):
        dupe_file = tmp_path / "dupes.csv"
        dupe_file.write_text("skill,category\nPython,Programming\nPython,Programming\n")
        df = load_skills_dataset(str(dupe_file))
        assert len(df) == 1


class TestFindSkillsInText:
    def test_finds_exact_skills(self, sample_resume_text):
        skills = find_skills_in_text(sample_resume_text)
        assert "Python" in skills
        assert "SQL" in skills
        assert "Docker" in skills

    def test_empty_text_returns_empty_list(self):
        assert find_skills_in_text("") == []
        assert find_skills_in_text(None) == []

    def test_no_false_positive_substring_match(self):
        # "Java" should not match inside "JavaScript" incorrectly attributed,
        # and whole-word matching should correctly find both independently
        skills_df = pd.DataFrame({"skill": ["Java", "JavaScript"], "category": ["x", "x"]})
        found = find_skills_in_text("I use JavaScript daily", skills_df, use_fuzzy=False)
        assert "JavaScript" in found
        assert "Java" not in found  # whole-word boundary prevents partial match

    def test_fuzzy_matching_catches_variant(self):
        skills_df = pd.DataFrame({"skill": ["React"], "category": ["Frontend"]})
        found = find_skills_in_text("Experienced with Reactjs applications", skills_df, use_fuzzy=True)
        assert "React" in found


class TestMissingSkills:
    def test_finds_missing_skills(self, sample_resume_text, sample_job_description):
        skills_df = load_skills_dataset()
        found = find_skills_in_text(sample_resume_text, skills_df)
        missing = extract_missing_skills(found, sample_job_description, skills_df)
        assert "Kubernetes" in missing

    def test_empty_job_description_returns_empty(self, sample_resume_text):
        skills_df = load_skills_dataset()
        found = find_skills_in_text(sample_resume_text, skills_df)
        assert extract_missing_skills(found, "", skills_df) == []
        assert extract_missing_skills(found, None, skills_df) == []


class TestMatchPercentage:
    def test_returns_reasonable_range(self, sample_resume_text, sample_job_description):
        pct = compute_match_percentage(sample_resume_text, sample_job_description)
        assert 0.0 <= pct <= 100.0

    def test_empty_job_description_returns_zero(self, sample_resume_text):
        assert compute_match_percentage(sample_resume_text, "") == 0.0

    def test_empty_resume_returns_zero(self, sample_job_description):
        assert compute_match_percentage("", sample_job_description) == 0.0

    def test_identical_text_scores_high(self):
        text = "Python developer with AWS and Docker experience"
        pct = compute_match_percentage(text, text)
        assert pct > 90.0


class TestCategoryBreakdown:
    def test_groups_by_category(self):
        skills_df = load_skills_dataset()
        breakdown = skill_category_breakdown(["Python", "AWS", "Docker"], skills_df)
        assert isinstance(breakdown, dict)
        assert sum(len(v) for v in breakdown.values()) == 3
