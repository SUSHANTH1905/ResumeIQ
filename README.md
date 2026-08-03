<<<<<<< HEAD
# 📄 ResumeIQ Advanced – AI Resume Analyzer

A hardened, test-covered version of ResumeIQ: validated inputs, custom
exceptions instead of crashes, fuzzy skill matching, writing-quality
checks, multi-resume comparison, a local history dashboard, dark mode,
and PDF **and** DOCX report export.

**Quality bar:** 85 automated tests, 93% code coverage on `utils/` and
`config.py`, verified with a live headless run of the Streamlit app
before delivery.

---

## ✨ What's new vs. the basic version

| Area | Basic version | Advanced version |
|---|---|---|
| Errors | Could crash the app on bad input | Custom exception hierarchy (`InvalidFileError`, `ResumeParsingError`, `EmptyResumeError`, etc.), caught and shown as friendly messages |
| File validation | None | Type, size (10 MB max), and empty-file checks before parsing |
| Skill matching | Exact word match only | Exact match **+ fuzzy matching** (catches "Reactjs" vs "React", "Node JS" vs "Node.js") |
| Writing quality | Not checked | Detects weak verbs, passive voice, overlong bullets, repeated vocabulary |
| Reports | PDF only | PDF **and** DOCX export |
| History | None | SQLite-backed history dashboard with average-score tracking |
| Comparison | Single resume only | Upload 2+ resumes, get a ranked table + common/unique skill breakdown |
| UI | Single page | Tabbed UI (Analyze / Compare / History) with a working dark-mode toggle |
| Logging | `print()` / silent failures | Structured logging via `utils/logging_config.py` |
| Tests | None | 85 pytest tests covering every module, including edge cases and error paths |
| Config | Hardcoded constants | Centralized `config.py`, with an assertion that the ATS rubric always sums to 100 |

---

## 🗂️ Project Structure

```
ResumeIQ_Advanced/
│
├── app.py                    # Streamlit UI (Analyze / Compare / History tabs)
├── config.py                 # Centralized constants & scoring rubric
├── requirements.txt
├── README.md
│
├── data/
│   └── skills.csv             # 60+ skill dataset (skill, category)
│
├── utils/
│   ├── __init__.py
│   ├── exceptions.py           # Custom exception hierarchy
│   ├── logging_config.py       # Structured logging setup
│   ├── parser.py                # PDF validation + text/field extraction
│   ├── skill_matcher.py          # Exact + fuzzy skill matching, JD comparison
│   ├── ats.py                    # ATS score calculation
│   ├── grammar.py                # Writing-quality heuristics
│   ├── suggestions.py            # Personalized improvement suggestions
│   ├── report.py                  # PDF + DOCX report generation
│   ├── compare.py                 # Multi-resume comparison & ranking
│   └── db.py                       # SQLite history storage
│
├── tests/                     # 85 tests, one file per module
│   ├── conftest.py             # Shared fixtures (in-memory sample PDF, etc.)
│   ├── test_parser.py
│   ├── test_skill_matcher.py
│   ├── test_ats.py
│   ├── test_grammar.py
│   ├── test_suggestions.py
│   ├── test_report.py
│   ├── test_compare.py
│   └── test_db.py
│
├── uploads/                   # (runtime) uploaded resumes, if persisted
├── reports/                    # (runtime) generated reports, if persisted
└── sample_resumes/             # Place sample PDF resumes here for manual testing
```

---

## 🚀 Getting Started

```bash
cd ResumeIQ_Advanced
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`. A `.streamlit/config.toml` is
included with upload-friendly defaults (disabled XSRF/CORS checks that
otherwise block file uploads in some browser/proxy setups, and a 10 MB
upload limit matching the app's own validation) — no command-line flags
needed.

### History is saved automatically

By default, every resume you analyze is saved to the History Dashboard
the moment analysis completes — no extra click required. Turn this off
anytime with the "💾 Auto-save analyses to history" toggle in the
sidebar if you'd rather save selectively via the "Save to History"
button under each result.


### Run the test suite

```bash
pip install pytest pytest-cov
pytest -v                                   # run all 85 tests
pytest --cov=utils --cov=config --cov-report=term-missing   # with coverage
```

---

## 🧮 ATS Scoring Rubric

| Category             | Max Marks | Logic                                                        |
|-----------------------|-----------|-----------------------------------------------------------|
| Skills                | 40        | Scales with matched skills (target: 10+), capped at 40    |
| Education             | 15        | Full marks if an Education section is detected            |
| Experience            | 15        | Full marks if Experience/Internship section is detected   |
| Projects              | 15        | Scales with detected projects (target: 3+), capped at 15  |
| Certifications        | 10        | Full marks if a Certifications section is detected        |
| Contact Information   | 5         | Split across email, phone, LinkedIn/GitHub presence       |
| **Total**             | **100**   | A `config.py`-level assertion guarantees this always sums to 100 |

Every scoring function clamps its output (never negative, never above
its category max), and `calculate_ats_score` clamps the final total to
`[0, 100]` as a defensive last line.

---

## 🛡️ Error Handling Philosophy

Nothing in `utils/` raises a raw, unhandled exception on bad input:

- Uploading a non-PDF, empty, or 15 MB file → `InvalidFileError` with a
  clear message, before any parsing is attempted.
- A corrupted or password-protected PDF → `ResumeParsingError`.
- A scanned PDF with no extractable text → `EmptyResumeError`.
- A missing/corrupt `skills.csv` → `SkillsDatasetError`.
- A PDF/DOCX build failure → `ReportGenerationError`.
- A SQLite failure → `DatabaseError` (with automatic rollback).

`app.py` catches all `ResumeIQError` subclasses and shows a friendly
`st.error(...)` message instead of a stack trace, and falls back to a
generic message (while logging the full traceback) for any truly
unexpected exception.

---

## 🛠️ Tech Stack

| Component       | Technology              |
|------------------|--------------------------|
| Language         | Python 3.10+              |
| UI               | Streamlit                 |
| PDF Parsing      | pdfplumber                 |
| Matching / ML    | scikit-learn (TF-IDF), difflib (fuzzy match) |
| Visualization    | Plotly                     |
| PDF Reports      | reportlab                   |
| DOCX Reports     | python-docx                  |
| History Storage  | SQLite (stdlib)               |
| Testing          | pytest, pytest-cov             |
| Data             | pandas, CSV                     |

---

## 🧩 Extending Further

- Swap the fuzzy/TF-IDF matcher for a spaCy or sentence-transformer
  embedding model for true semantic matching
- Add authentication so the history dashboard is per-user
- Plug in an LLM (e.g. via the Anthropic API) for AI-generated rewrite
  suggestions layered on top of the rule-based ones
- Deploy to Streamlit Community Cloud, Render, or Hugging Face Spaces
- Add CI (GitHub Actions) to run `pytest` on every push

---

## 📄 License

Provided as-is for educational and portfolio purposes. Feel free to
modify and use it in your own projects.
=======
# ResumeIQ
>>>>>>> 2a2728fcf43fefb9c80d0792ec18835231f4647f
