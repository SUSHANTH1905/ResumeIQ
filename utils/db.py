"""
db.py
------
SQLite-backed storage for resume analysis history, enabling the
"Dashboard" / multi-resume comparison features. Uses parameterized
queries throughout (no string-formatted SQL) to avoid injection issues,
and wraps every operation in explicit error handling.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from config import DB_PATH
from utils.exceptions import DatabaseError
from utils.logging_config import get_logger

logger = get_logger("db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    name TEXT,
    email TEXT,
    ats_total REAL,
    skills_found TEXT,   -- JSON list
    missing_skills TEXT, -- JSON list
    breakdown TEXT,       -- JSON dict
    match_percentage REAL
);
"""


@contextmanager
def _get_connection(db_path: str = DB_PATH):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    except sqlite3.Error as exc:
        if conn:
            conn.rollback()
        logger.exception("Database operation failed")
        raise DatabaseError(f"Database operation failed: {exc}") from exc
    finally:
        if conn:
            conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    with _get_connection(db_path) as conn:
        conn.execute(SCHEMA)


def save_analysis(parsed_resume: dict, ats_result: dict, skills_found: list,
                   missing_skills: list, match_percentage: float = None,
                   db_path: str = DB_PATH) -> int:
    """
    Persists one analysis run. Returns the new row's id.
    """
    init_db(db_path)
    with _get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO analyses
                (created_at, name, email, ats_total, skills_found,
                 missing_skills, breakdown, match_percentage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                parsed_resume.get("name", "Unknown"),
                parsed_resume.get("email", ""),
                ats_result.get("total", 0),
                json.dumps(skills_found or []),
                json.dumps(missing_skills or []),
                json.dumps(ats_result.get("breakdown", {})),
                match_percentage,
            ),
        )
        return cursor.lastrowid


def get_all_analyses(db_path: str = DB_PATH) -> list:
    """
    Returns all saved analyses, most recent first, with JSON fields
    deserialized back into Python objects.
    """
    init_db(db_path)
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM analyses ORDER BY created_at DESC"
        ).fetchall()

    results = []
    for row in rows:
        record = dict(row)
        for json_field in ("skills_found", "missing_skills", "breakdown"):
            try:
                record[json_field] = json.loads(record[json_field] or "null")
            except (TypeError, json.JSONDecodeError):
                record[json_field] = None
        results.append(record)
    return results


def clear_history(db_path: str = DB_PATH) -> None:
    init_db(db_path)
    with _get_connection(db_path) as conn:
        conn.execute("DELETE FROM analyses")
