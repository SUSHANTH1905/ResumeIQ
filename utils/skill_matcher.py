"""
skill_matcher.py
-----------------
Loads the skills dataset and matches skills found in the resume against
skills required by a job description. Uses exact whole-word matching
plus difflib-based fuzzy matching to catch near-variants and typos
(e.g. "Reactjs" vs "React", "Node JS" vs "Node.js") without requiring
a heavyweight NLP model download.
"""

import difflib
import os
import re

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import FUZZY_MATCH_THRESHOLD, SKILLS_CSV_PATH
from utils.exceptions import SkillsDatasetError
from utils.logging_config import get_logger

logger = get_logger("skill_matcher")

REQUIRED_COLUMNS = {"skill", "category"}


def load_skills_dataset(path: str = SKILLS_CSV_PATH) -> pd.DataFrame:
    """
    Loads and validates the skills dataset.

    Raises:
        SkillsDatasetError: if the file is missing, empty, malformed,
            or missing required columns.
    """
    if not os.path.exists(path):
        raise SkillsDatasetError(f"Skills dataset not found at: {path}")

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise SkillsDatasetError("Skills dataset file is empty.") from exc
    except pd.errors.ParserError as exc:
        raise SkillsDatasetError(f"Skills dataset is malformed: {exc}") from exc

    if not REQUIRED_COLUMNS.issubset(set(df.columns)):
        missing = REQUIRED_COLUMNS - set(df.columns)
        raise SkillsDatasetError(f"Skills dataset missing required columns: {missing}")

    df = df.dropna(subset=["skill"])
    df["skill"] = df["skill"].astype(str).str.strip()
    df = df[df["skill"] != ""]

    if df.empty:
        raise SkillsDatasetError("Skills dataset contains no valid skill entries.")

    if df["skill"].duplicated().any():
        dupes = df.loc[df["skill"].duplicated(), "skill"].tolist()
        logger.warning("Duplicate skills found in dataset (deduplicating): %s", dupes)
        df = df.drop_duplicates(subset=["skill"])

    return df.reset_index(drop=True)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _fuzzy_ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def find_skills_in_text(text: str, skills_df: pd.DataFrame = None,
                         use_fuzzy: bool = True) -> list:
    """
    Returns known skills (from the skills dataset) that appear in the
    given text. Exact whole-word/phrase matches are checked first;
    if `use_fuzzy` is True, tokens that don't exactly match are also
    compared against each skill using a similarity ratio, which catches
    minor spelling/formatting variants.
    """
    if not text or not text.strip():
        return []

    if skills_df is None:
        skills_df = load_skills_dataset()

    normalized_text = _normalize(text)
    found = set()

    # --- exact whole-word / phrase matches ---
    for skill in skills_df["skill"]:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, normalized_text):
            found.add(skill)

    # --- fuzzy matching for near-variants ---
    if use_fuzzy:
        # tokenize on non-alphanumeric to get candidate words/short phrases
        tokens = set(re.findall(r"[a-zA-Z0-9+#.]{2,}", normalized_text))
        remaining_skills = [s for s in skills_df["skill"] if s not in found]
        for skill in remaining_skills:
            skill_lower = skill.lower()
            for token in tokens:
                if len(token) < 3 or len(skill_lower) < 3:
                    continue  # too short to fuzzy-match reliably
                # Short suffix/prefix variants (e.g. "reactjs" vs "react",
                # "nodejs" vs "node") won't clear a pure ratio threshold
                # because the extra characters dilute the score, so treat
                # a close containment relationship as a match too.
                is_close_containment = (
                    (token.startswith(skill_lower) or skill_lower.startswith(token))
                    and abs(len(token) - len(skill_lower)) <= 3
                )
                if abs(len(token) - len(skill_lower)) > 4 and not is_close_containment:
                    continue  # cheap pre-filter before the O(n*m) ratio calc
                if is_close_containment or _fuzzy_ratio(token, skill_lower) >= FUZZY_MATCH_THRESHOLD:
                    found.add(skill)
                    break

    return sorted(found)


def extract_missing_skills(resume_skills: list, job_description: str,
                            skills_df: pd.DataFrame = None) -> list:
    """
    Skills mentioned in the job description (from the known skill list)
    that are NOT present in the resume's detected skills.
    """
    if not job_description or not job_description.strip():
        return []

    jd_skills = find_skills_in_text(job_description, skills_df)
    resume_set = {s.lower() for s in resume_skills}
    return sorted([s for s in jd_skills if s.lower() not in resume_set])


def compute_match_percentage(resume_text: str, job_description: str) -> float:
    """
    Computes a similarity score (0-100) between the resume and job
    description using TF-IDF + cosine similarity.
    """
    if not job_description or not job_description.strip():
        return 0.0
    if not resume_text or not resume_text.strip():
        return 0.0

    documents = [resume_text, job_description]
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        # empty vocabulary after stop-word removal (e.g. JD is just "a the")
        return 0.0

    if tfidf_matrix.shape[1] == 0:
        return 0.0

    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    similarity = max(0.0, min(1.0, float(similarity)))  # clamp for safety
    return round(similarity * 100, 2)


def skill_category_breakdown(skills_found: list, skills_df: pd.DataFrame = None) -> dict:
    if skills_df is None:
        skills_df = load_skills_dataset()

    lookup = dict(zip(skills_df["skill"], skills_df["category"]))
    breakdown = {}
    for skill in skills_found:
        category = lookup.get(skill, "Other")
        breakdown.setdefault(category, []).append(skill)
    return breakdown
