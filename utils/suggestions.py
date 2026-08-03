"""
suggestions.py
---------------
Generates rule-based, personalized resume improvement suggestions from
the parsed resume, ATS score breakdown, missing-skills analysis, and
(optionally) the quality/grammar report from grammar.py.
"""

from config import MAX_RECOMMENDED_WORDS, MIN_RECOMMENDED_WORDS


def generate_suggestions(parsed_resume: dict, ats_result: dict,
                          missing_skills: list, quality_report: dict = None) -> list:
    parsed_resume = parsed_resume or {}
    ats_result = ats_result or {"breakdown": {}, "max_scores": {}}
    missing_skills = missing_skills or []
    suggestions = []

    breakdown = ats_result.get("breakdown", {})
    max_scores = ats_result.get("max_scores", {})

    # --- Contact info ---
    if not parsed_resume.get("email"):
        suggestions.append("Add a professional email address near the top of your resume.")
    if not parsed_resume.get("phone"):
        suggestions.append("Include a reachable phone number in your contact section.")
    if not parsed_resume.get("linkedin") and not parsed_resume.get("github"):
        suggestions.append("Add a LinkedIn and/or GitHub profile link so recruiters can verify your work.")

    # --- Skills ---
    if breakdown.get("Skills", 0) < max_scores.get("Skills", 40):
        suggestions.append("List more relevant technical skills — aim for at least 10 that match your target role.")
    if missing_skills:
        top_missing = ", ".join(missing_skills[:5])
        suggestions.append(f"Consider adding these in-demand skills mentioned in the job description: {top_missing}.")

    # --- Education ---
    if breakdown.get("Education", 0) < max_scores.get("Education", 15):
        suggestions.append("Add an Education section with your degree, institution, and graduation year.")

    # --- Experience ---
    if breakdown.get("Experience", 0) < max_scores.get("Experience", 15):
        suggestions.append("Add an Experience or Internship section, even for part-time or academic roles.")

    # --- Projects ---
    if breakdown.get("Projects", 0) < max_scores.get("Projects", 15):
        suggestions.append("Showcase at least 3 projects with clear outcomes, tech stack, and links to code.")
    else:
        suggestions.append("Quantify your project outcomes (e.g. 'reduced processing time by 30%').")

    # --- Certifications ---
    if breakdown.get("Certifications", 0) < max_scores.get("Certifications", 10):
        suggestions.append("Add relevant certifications (e.g. AWS, Coursera, Google) to strengthen credibility.")

    # --- Length ---
    word_count = parsed_resume.get("word_count", 0)
    if word_count < MIN_RECOMMENDED_WORDS:
        suggestions.append("Your resume looks quite short — consider elaborating on projects and responsibilities.")
    elif word_count > MAX_RECOMMENDED_WORDS:
        suggestions.append("Your resume is lengthy — trim redundant details and focus on the most relevant content.")

    # --- Quality / grammar heuristics ---
    if quality_report:
        if quality_report.get("weak_verb_bullets"):
            suggestions.append(
                "Replace weak phrases (e.g. 'helped', 'was responsible for') with strong action verbs "
                "like 'built', 'led', or 'optimized'."
            )
        if quality_report.get("long_bullets"):
            suggestions.append("Shorten long bullet points — aim for one concise, impact-focused line each.")
        if quality_report.get("passive_voice_sentences"):
            suggestions.append("Rewrite passive-voice sentences (e.g. 'was developed by') in active voice.")
        if quality_report.get("strong_action_verb_count", 0) < 3:
            suggestions.append("Use more strong action verbs to start bullet points (built, designed, automated).")
        if quality_report.get("repeated_words"):
            repeated = ", ".join(list(quality_report["repeated_words"].keys())[:5])
            suggestions.append(f"Vary your vocabulary — these words repeat often: {repeated}.")
    else:
        suggestions.append("Use strong action verbs (built, designed, optimized, automated) to start bullet points.")

    suggestions.append("Keep the resume to 1-2 pages and use consistent formatting throughout.")

    # De-duplicate while preserving order (defensive, in case of overlapping rules)
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique_suggestions.append(s)

    return unique_suggestions
