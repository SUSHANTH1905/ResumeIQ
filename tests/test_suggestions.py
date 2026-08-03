from utils.ats import calculate_ats_score
from utils.suggestions import generate_suggestions


class TestGenerateSuggestions:
    def test_returns_list_of_strings(self):
        parsed_resume = {"email": "", "phone": "", "linkedin": "", "github": "", "word_count": 500}
        ats_result = calculate_ats_score(parsed_resume, [])
        suggestions = generate_suggestions(parsed_resume, ats_result, [])
        assert isinstance(suggestions, list)
        assert all(isinstance(s, str) for s in suggestions)
        assert len(suggestions) > 0

    def test_flags_missing_contact_info(self):
        parsed_resume = {"email": "", "phone": "", "linkedin": "", "github": "", "word_count": 500}
        ats_result = calculate_ats_score(parsed_resume, [])
        suggestions = generate_suggestions(parsed_resume, ats_result, [])
        joined = " ".join(suggestions).lower()
        assert "email" in joined
        assert "phone" in joined

    def test_no_duplicate_suggestions(self):
        parsed_resume = {"email": "", "phone": "", "linkedin": "", "github": "", "word_count": 50}
        ats_result = calculate_ats_score(parsed_resume, [])
        suggestions = generate_suggestions(parsed_resume, ats_result, ["Docker", "AWS"])
        assert len(suggestions) == len(set(suggestions))

    def test_handles_empty_inputs_without_crashing(self):
        suggestions = generate_suggestions({}, {"breakdown": {}, "max_scores": {}}, [])
        assert isinstance(suggestions, list)

    def test_mentions_missing_skills(self):
        parsed_resume = {"email": "a@b.com", "phone": "123", "linkedin": "x", "github": "y", "word_count": 500}
        ats_result = calculate_ats_score(parsed_resume, ["Python"])
        suggestions = generate_suggestions(parsed_resume, ats_result, ["Docker", "AWS"])
        joined = " ".join(suggestions)
        assert "Docker" in joined or "AWS" in joined

    def test_includes_quality_feedback_when_report_provided(self):
        parsed_resume = {"email": "a@b.com", "phone": "123", "linkedin": "x", "github": "y", "word_count": 500}
        ats_result = calculate_ats_score(parsed_resume, ["Python"])
        quality_report = {
            "weak_verb_bullets": ["helped with testing"],
            "long_bullets": [],
            "passive_voice_sentences": [],
            "strong_action_verb_count": 1,
            "repeated_words": {},
        }
        suggestions = generate_suggestions(parsed_resume, ats_result, [], quality_report)
        joined = " ".join(suggestions).lower()
        assert "action verb" in joined or "weak" in joined
