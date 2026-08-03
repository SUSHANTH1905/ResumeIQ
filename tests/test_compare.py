from utils.compare import build_comparison_table, find_common_and_unique_skills, rank_resumes


def _make_entry(label, total, skills, projects=1):
    return {
        "label": label,
        "parsed_resume": {"project_count": projects},
        "ats_result": {"total": total, "breakdown": {"Skills": total}},
        "skills_found": skills,
    }


class TestBuildComparisonTable:
    def test_returns_row_per_resume(self):
        entries = [_make_entry("A", 80, ["Python"]), _make_entry("B", 60, ["Java", "SQL"])]
        rows = build_comparison_table(entries)
        assert len(rows) == 2
        assert rows[0]["Resume"] == "A"
        assert rows[0]["ATS Score"] == 80
        assert rows[1]["Skills Count"] == 2

    def test_empty_list_returns_empty(self):
        assert build_comparison_table([]) == []


class TestRankResumes:
    def test_sorts_by_score_descending(self):
        entries = [_make_entry("Low", 40, []), _make_entry("High", 90, [])]
        ranked = rank_resumes(entries)
        assert ranked[0]["label"] == "High"
        assert ranked[1]["label"] == "Low"

    def test_tie_broken_by_skill_count(self):
        entries = [
            _make_entry("FewSkills", 70, ["Python"]),
            _make_entry("ManySkills", 70, ["Python", "SQL", "AWS"]),
        ]
        ranked = rank_resumes(entries)
        assert ranked[0]["label"] == "ManySkills"


class TestCommonAndUniqueSkills:
    def test_finds_common_skills(self):
        entries = [
            _make_entry("A", 80, ["Python", "SQL"]),
            _make_entry("B", 70, ["Python", "AWS"]),
        ]
        result = find_common_and_unique_skills(entries)
        assert result["common"] == ["Python"]

    def test_finds_unique_skills_per_resume(self):
        entries = [
            _make_entry("A", 80, ["Python", "SQL"]),
            _make_entry("B", 70, ["Python", "AWS"]),
        ]
        result = find_common_and_unique_skills(entries)
        assert result["unique"]["A"] == ["SQL"]
        assert result["unique"]["B"] == ["AWS"]

    def test_empty_list_handled(self):
        result = find_common_and_unique_skills([])
        assert result == {"common": [], "unique": {}}
