from utils.db import clear_history, get_all_analyses, init_db, save_analysis


class TestDatabase:
    def test_init_db_creates_table(self, isolated_db_path):
        init_db(isolated_db_path)
        # should not raise, and a second call should be idempotent
        init_db(isolated_db_path)

    def test_save_and_retrieve_analysis(self, isolated_db_path):
        parsed_resume = {"name": "Jane Smith", "email": "jane@example.com"}
        ats_result = {"total": 82.5, "breakdown": {"Skills": 40}}
        row_id = save_analysis(
            parsed_resume, ats_result, ["Python", "SQL"], ["Docker"],
            match_percentage=75.0, db_path=isolated_db_path,
        )
        assert row_id is not None and row_id > 0

        records = get_all_analyses(isolated_db_path)
        assert len(records) == 1
        record = records[0]
        assert record["name"] == "Jane Smith"
        assert record["ats_total"] == 82.5
        assert record["skills_found"] == ["Python", "SQL"]
        assert record["missing_skills"] == ["Docker"]
        assert record["match_percentage"] == 75.0

    def test_multiple_analyses_ordered_most_recent_first(self, isolated_db_path):
        for i in range(3):
            save_analysis(
                {"name": f"Candidate {i}", "email": f"c{i}@example.com"},
                {"total": i * 10, "breakdown": {}},
                [], [], db_path=isolated_db_path,
            )
        records = get_all_analyses(isolated_db_path)
        assert len(records) == 3
        # most recently inserted should be first (id descending due to timestamp ties broken by insertion order)
        assert records[0]["name"] == "Candidate 2"

    def test_clear_history_removes_all_rows(self, isolated_db_path):
        save_analysis({"name": "X"}, {"total": 50, "breakdown": {}}, [], [], db_path=isolated_db_path)
        assert len(get_all_analyses(isolated_db_path)) == 1
        clear_history(isolated_db_path)
        assert len(get_all_analyses(isolated_db_path)) == 0

    def test_empty_database_returns_empty_list(self, isolated_db_path):
        assert get_all_analyses(isolated_db_path) == []
