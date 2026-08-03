"""
config.py
----------
Centralized configuration constants for ResumeIQ Advanced.
Keeping these in one place avoids "magic numbers" scattered across
modules and makes the scoring rubric and validation limits easy to audit.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SKILLS_CSV_PATH = os.path.join(DATA_DIR, "skills.csv")
DB_PATH = os.path.join(BASE_DIR, "resumeiq.db")

# --- Upload validation ---
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = {".pdf"}
MIN_EXTRACTED_WORD_COUNT = 20  # below this, treat as unreadable/scanned PDF

# --- ATS scoring rubric (must sum to 100) ---
ATS_MAX_SCORES = {
    "Skills": 40,
    "Education": 15,
    "Experience": 15,
    "Projects": 15,
    "Certifications": 10,
    "Contact Information": 5,
}
assert sum(ATS_MAX_SCORES.values()) == 100, "ATS rubric must total 100 points"

TARGET_SKILL_COUNT = 10
TARGET_PROJECT_COUNT = 3

# --- Fuzzy skill matching ---
FUZZY_MATCH_THRESHOLD = 0.86  # difflib SequenceMatcher ratio, 0-1

# --- Resume quality heuristics ---
WEAK_VERBS = {
    "helped", "worked", "did", "was responsible for", "handled",
    "involved in", "assisted", "participated",
}
STRONG_ACTION_VERBS = {
    "built", "designed", "developed", "implemented", "optimized",
    "automated", "led", "architected", "launched", "reduced",
    "increased", "improved", "created", "engineered", "deployed",
}
MAX_RECOMMENDED_WORDS = 1200
MIN_RECOMMENDED_WORDS = 150
MAX_BULLET_WORDS = 30  # bullets longer than this hurt readability

LOG_LEVEL = os.environ.get("RESUMEIQ_LOG_LEVEL", "INFO")
