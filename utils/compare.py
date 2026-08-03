"""
compare.py
-----------
Compares multiple already-analyzed resumes side by side — useful for a
candidate testing several resume versions, or a recruiter shortlisting
candidates.
"""


def build_comparison_table(analyses: list) -> list:
    """
    Args:
        analyses: list of dicts, each shaped like:
            {
                "label": str,               # e.g. filename or candidate name
                "parsed_resume": dict,
                "ats_result": dict,
                "skills_found": list,
            }

    Returns:
        A list of row dicts suitable for direct display in a table:
        [{"Resume": ..., "ATS Score": ..., "Skills Count": ..., ...}, ...]
    """
    rows = []
    for entry in analyses:
        ats_result = entry.get("ats_result", {}) or {}
        breakdown = ats_result.get("breakdown", {}) or {}
        row = {
            "Resume": entry.get("label", "Untitled"),
            "ATS Score": ats_result.get("total", 0),
            "Skills Count": len(entry.get("skills_found", []) or []),
            "Projects": entry.get("parsed_resume", {}).get("project_count", 0),
        }
        row.update(breakdown)
        rows.append(row)
    return rows


def rank_resumes(analyses: list) -> list:
    """
    Returns the input analyses sorted by ATS total score, descending.
    Ties are broken by skill count.
    """
    def sort_key(entry):
        ats_total = (entry.get("ats_result") or {}).get("total", 0)
        skill_count = len(entry.get("skills_found", []) or [])
        return (-ats_total, -skill_count)

    return sorted(analyses, key=sort_key)


def find_common_and_unique_skills(analyses: list) -> dict:
    """
    Returns skills common to ALL resumes, and skills unique to each
    individual resume — helpful for spotting differentiators.
    """
    skill_sets = [set(entry.get("skills_found", []) or []) for entry in analyses]
    if not skill_sets:
        return {"common": [], "unique": {}}

    common = set.intersection(*skill_sets) if skill_sets else set()

    unique = {}
    for i, entry in enumerate(analyses):
        others = set()
        for j, other_set in enumerate(skill_sets):
            if i != j:
                others |= other_set
        unique_to_this = skill_sets[i] - others
        unique[entry.get("label", f"Resume {i + 1}")] = sorted(unique_to_this)

    return {"common": sorted(common), "unique": unique}
