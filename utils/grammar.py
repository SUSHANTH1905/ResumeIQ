"""
grammar.py
-----------
Lightweight, dependency-free resume "quality" checks. These are
heuristics (not a full grammar engine) that flag common resume-writing
issues: weak verbs, overly long bullet points, passive-voice phrasing,
and repeated wording — the kind of feedback a career coach would give
without needing to install a large NLP model.
"""

import re

from config import MAX_BULLET_WORDS, STRONG_ACTION_VERBS, WEAK_VERBS


def _split_bullets(text: str) -> list:
    lines = text.split("\n")
    bullets = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^([-•*]|\d+\.)\s+", stripped):
            content = re.sub(r"^([-•*]|\d+\.)\s+", "", stripped)
            if content:
                bullets.append(content)
    return bullets


def find_weak_verb_bullets(text: str) -> list:
    """Returns bullets that start with (or heavily rely on) weak verbs."""
    bullets = _split_bullets(text)
    flagged = []
    for bullet in bullets:
        first_words = " ".join(bullet.lower().split()[:3])
        if any(first_words.startswith(w) for w in WEAK_VERBS):
            flagged.append(bullet)
    return flagged


def find_long_bullets(text: str, max_words: int = MAX_BULLET_WORDS) -> list:
    bullets = _split_bullets(text)
    return [b for b in bullets if len(b.split()) > max_words]


def detect_passive_voice(text: str) -> list:
    """
    Rough heuristic: flags sentences matching "was/were/is/are/been + past
    participle (word ending in -ed)" — a common (not perfect) signal of
    passive voice, which is generally weaker than active, achievement-led
    phrasing on a resume.
    """
    pattern = re.compile(
        r"\b(was|were|is|are|been|being)\s+\w+ed\b", re.IGNORECASE
    )
    sentences = re.split(r"(?<=[.!?])\s+", text)
    flagged = [s.strip() for s in sentences if pattern.search(s)]
    return flagged[:10]  # cap to avoid overwhelming the UI


def count_strong_action_verbs(text: str) -> int:
    lower_text = text.lower()
    count = 0
    for verb in STRONG_ACTION_VERBS:
        count += len(re.findall(r"\b" + re.escape(verb) + r"\b", lower_text))
    return count


def find_repeated_words(text: str, min_count: int = 5) -> dict:
    """
    Flags non-trivial words (4+ letters) repeated many times, which can
    indicate a lack of vocabulary variety.
    """
    stop_like = {
        "with", "that", "this", "from", "have", "using", "used", "into",
        "such", "will", "were", "been", "also", "their", "which",
    }
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    freq = {}
    for w in words:
        if w in stop_like:
            continue
        freq[w] = freq.get(w, 0) + 1
    return {w: c for w, c in freq.items() if c >= min_count}


def analyze_quality(text: str) -> dict:
    """
    Runs all quality heuristics and returns a consolidated report dict.
    Safe to call on any non-empty string; returns empty results for
    empty input rather than raising.
    """
    text = text or ""
    if not text.strip():
        return {
            "weak_verb_bullets": [],
            "long_bullets": [],
            "passive_voice_sentences": [],
            "strong_action_verb_count": 0,
            "repeated_words": {},
        }

    return {
        "weak_verb_bullets": find_weak_verb_bullets(text),
        "long_bullets": find_long_bullets(text),
        "passive_voice_sentences": detect_passive_voice(text),
        "strong_action_verb_count": count_strong_action_verbs(text),
        "repeated_words": find_repeated_words(text),
    }
