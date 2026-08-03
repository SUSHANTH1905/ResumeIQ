from utils.grammar import (
    analyze_quality, count_strong_action_verbs, detect_passive_voice,
    find_long_bullets, find_repeated_words, find_weak_verb_bullets,
)


class TestWeakVerbBullets:
    def test_flags_weak_verb_start(self):
        text = "- Helped the team with testing\n- Built a chatbot using Python"
        flagged = find_weak_verb_bullets(text)
        assert any("Helped" in b for b in flagged)
        assert not any("Built" in b for b in flagged)

    def test_no_bullets_returns_empty(self):
        assert find_weak_verb_bullets("Just a plain sentence.") == []


class TestLongBullets:
    def test_flags_long_bullet(self):
        long_bullet = "- " + " ".join(["word"] * 40)
        flagged = find_long_bullets(long_bullet)
        assert len(flagged) == 1

    def test_short_bullet_not_flagged(self):
        short_bullet = "- Built a chatbot using Python"
        assert find_long_bullets(short_bullet) == []


class TestPassiveVoice:
    def test_detects_passive_sentence(self):
        text = "The application was developed by the team."
        flagged = detect_passive_voice(text)
        assert len(flagged) >= 1

    def test_active_sentence_not_flagged(self):
        text = "I built the application from scratch."
        flagged = detect_passive_voice(text)
        assert flagged == []


class TestStrongActionVerbs:
    def test_counts_known_verbs(self):
        text = "Built a system. Designed the schema. Optimized performance."
        assert count_strong_action_verbs(text) == 3

    def test_zero_when_none_present(self):
        assert count_strong_action_verbs("This is a plain sentence.") == 0


class TestRepeatedWords:
    def test_flags_frequent_word(self):
        text = " ".join(["python"] * 6 + ["developer"])
        repeated = find_repeated_words(text, min_count=5)
        assert "python" in repeated

    def test_ignores_infrequent_words(self):
        text = "python java docker aws kubernetes"
        repeated = find_repeated_words(text, min_count=5)
        assert repeated == {}


class TestAnalyzeQuality:
    def test_returns_all_expected_keys(self):
        report = analyze_quality("Built a chatbot. Was developed by me.")
        expected_keys = {
            "weak_verb_bullets", "long_bullets", "passive_voice_sentences",
            "strong_action_verb_count", "repeated_words",
        }
        assert expected_keys.issubset(report.keys())

    def test_empty_text_does_not_crash(self):
        report = analyze_quality("")
        assert report["weak_verb_bullets"] == []
        assert report["strong_action_verb_count"] == 0

    def test_none_text_does_not_crash(self):
        report = analyze_quality(None)
        assert isinstance(report, dict)
