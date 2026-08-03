"""
ResumeIQ Advanced - AI Resume Analyzer
========================================
Main Streamlit application entry point.

Run with:
    streamlit run app.py
"""

import traceback

import streamlit as st
import plotly.graph_objects as go

from utils.parser import parse_resume
from utils.skill_matcher import (
    load_skills_dataset, find_skills_in_text, extract_missing_skills,
    compute_match_percentage, skill_category_breakdown,
)
from utils.ats import calculate_ats_score
from utils.grammar import analyze_quality
from utils.suggestions import generate_suggestions
from utils.report import build_pdf_report, build_docx_report
from utils.compare import build_comparison_table, rank_resumes, find_common_and_unique_skills
from utils.db import save_analysis, get_all_analyses, clear_history
from utils.exceptions import ResumeIQError
from utils.logging_config import get_logger

logger = get_logger("app")

st.set_page_config(
    page_title="ResumeIQ Advanced - AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
)


# ----------------------------- Session State -----------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "comparison_pool" not in st.session_state:
    st.session_state.comparison_pool = []  # list of {label, parsed_resume, ats_result, skills_found}
if "auto_save_history" not in st.session_state:
    st.session_state.auto_save_history = True


def apply_theme(dark_mode: bool) -> None:
    if dark_mode:
        bg, fg, card, card_border, accent, accent2 = (
            "#0B0E14", "#F5F6FA", "#161B24", "#232935", "#5DADE2", "#8E7CF5"
        )
        muted = "#8B93A7"
    else:
        bg, fg, card, card_border, accent, accent2 = (
            "#FAFBFD", "#1B2028", "#FFFFFF", "#E7EAF0", "#2874A6", "#6C5CE7"
        )
        muted = "#6B7280"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
        .stApp {{ background-color: {bg}; color: {fg}; }}

        .hero {{
            padding: 1.6rem 1.8rem; border-radius: 18px; margin-bottom: 0.5rem;
            background: linear-gradient(120deg, {accent}15, {accent2}10);
            border: 1px solid {card_border};
        }}
        .main-title {{
            font-size: 2.3rem; font-weight: 800; margin-bottom: 0.1rem;
            background: linear-gradient(120deg, {accent}, {accent2});
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .sub-title {{ font-size: 1.02rem; color: {muted}; margin-top: 0; font-weight: 500; }}

        .metric-card {{
            padding: 1.1rem 1.3rem; border-radius: 14px;
            background-color: {card}; border: 1px solid {card_border};
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        }}
        .metric-card .label {{ font-size: 0.82rem; color: {muted}; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.2rem; }}
        .metric-card .value {{ font-size: 1.9rem; font-weight: 800; color: {fg}; }}

        .section-card {{
            padding: 1.2rem 1.4rem; border-radius: 14px;
            background-color: {card}; border: 1px solid {card_border};
            margin-bottom: 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        }}
        .section-title {{ font-size: 1.05rem; font-weight: 700; color: {fg}; margin-bottom: 0.6rem; }}

        .pill {{
            display: inline-block; padding: 0.28rem 0.7rem; margin: 0.18rem;
            border-radius: 999px; font-size: 0.84rem; font-weight: 600;
        }}
        .pill-found {{ background: {accent}20; color: {accent}; border: 1px solid {accent}55; }}
        .pill-missing {{ background: #E74C3C18; color: #E74C3C; border: 1px solid #E74C3C55; }}
        .pill-section-on {{ background: #27AE6020; color: #1E8449; border: 1px solid #27AE6055; }}
        .pill-section-off {{ background: {muted}15; color: {muted}; border: 1px solid {muted}35; }}

        .badge-row {{ line-height: 2.4; }}
        hr {{ border-color: {card_border} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_theme(st.session_state.dark_mode)

st.markdown(
    """
    <div class="hero">
        <p class="main-title">📄 ResumeIQ Advanced</p>
        <p class="sub-title">AI-Powered Resume Analyzer, ATS Score Checker &amp; Multi-Resume Comparison</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")


# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    st.header("⚙️ Options")
    st.session_state.dark_mode = st.toggle("🌙 Dark mode", value=st.session_state.dark_mode)
    st.session_state.auto_save_history = st.toggle(
        "💾 Auto-save analyses to history", value=st.session_state.auto_save_history,
        help="When on, every resume you analyze is saved to the History Dashboard automatically — no extra click needed.",
    )
    st.markdown("---")
    st.markdown(
        "**About**\n\n"
        "ResumeIQ Advanced extracts skills from your resume, calculates an "
        "ATS score, checks writing quality, compares multiple resumes, "
        "keeps a local history dashboard, and exports PDF/DOCX reports."
    )
    st.markdown("---")
    st.caption("Every module is covered by an automated test suite (85 tests).")


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """
    Plotly color properties (e.g. fillcolor) don't accept 8-digit hex
    (RRGGBBAA); they need rgba(). This converts a '#RRGGBB' string plus
    an alpha value into a Plotly-safe 'rgba(r,g,b,a)' string.
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def metric_card(label: str, value: str) -> str:
    return f"""<div class="metric-card"><div class="label">{label}</div><div class="value">{value}</div></div>"""


def pills_html(items: list, css_class: str) -> str:
    if not items:
        return ""
    spans = "".join(f'<span class="pill {css_class}">{s}</span>' for s in items)
    return f'<div class="badge-row">{spans}</div>'


def build_gauge_chart(value: float, title: str, accent: str = "#2874A6") -> "go.Figure":
    if value >= 75:
        bar_color = "#27AE60"
    elif value >= 50:
        bar_color = "#F39C12"
    else:
        bar_color = "#E74C3C"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"size": 36}},
        title={"text": title, "font": {"size": 15}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": bar_color, "thickness": 0.28},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50], "color": "rgba(231,76,60,0.12)"},
                {"range": [50, 75], "color": "rgba(243,156,18,0.12)"},
                {"range": [75, 100], "color": "rgba(39,174,96,0.12)"},
            ],
        },
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=10),
                       paper_bgcolor="rgba(0,0,0,0)", font={"color": accent})
    return fig


def build_radar_chart(breakdown: dict, max_scores: dict, accent: str = "#2874A6") -> "go.Figure":
    categories = list(breakdown.keys())
    # normalize each category to a 0-100 scale so the radar isn't skewed by max-point differences
    normalized = [
        round((breakdown[c] / max_scores[c]) * 100, 1) if max_scores.get(c) else 0
        for c in categories
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=normalized + [normalized[0]], theta=categories + [categories[0]],
        fill="toself", name="Your Resume", line_color=accent, fillcolor=hex_to_rgba(accent, 0.2),
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=True, ticksuffix="%")),
        showlegend=False, height=380, margin=dict(l=40, r=40, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def run_analysis(uploaded_file, job_description: str) -> dict:
    """
    Runs the full analysis pipeline for one uploaded file. Raises
    ResumeIQError subclasses on failure — callers should catch these
    and show a friendly message rather than crashing the app.
    """
    parsed_resume = parse_resume(uploaded_file)
    skills_df = load_skills_dataset()
    skills_found = find_skills_in_text(parsed_resume["raw_text"], skills_df)
    missing_skills = extract_missing_skills(skills_found, job_description, skills_df)
    ats_result = calculate_ats_score(parsed_resume, skills_found)
    quality_report = analyze_quality(parsed_resume["raw_text"])
    suggestions = generate_suggestions(parsed_resume, ats_result, missing_skills, quality_report)

    match_percentage = None
    if job_description and job_description.strip():
        match_percentage = compute_match_percentage(parsed_resume["raw_text"], job_description)

    category_breakdown = skill_category_breakdown(skills_found, skills_df)

    return {
        "parsed_resume": parsed_resume,
        "skills_found": skills_found,
        "missing_skills": missing_skills,
        "ats_result": ats_result,
        "quality_report": quality_report,
        "suggestions": suggestions,
        "match_percentage": match_percentage,
        "category_breakdown": category_breakdown,
    }


def render_analysis_result(result: dict, key_prefix: str = "") -> None:
    parsed_resume = result["parsed_resume"]
    ats_result = result["ats_result"]
    skills_found = result["skills_found"]
    missing_skills = result["missing_skills"]
    quality_report = result["quality_report"]
    suggestions = result["suggestions"]
    match_percentage = result["match_percentage"]
    category_breakdown = result["category_breakdown"]

    accent = "#5DADE2" if st.session_state.dark_mode else "#2874A6"

    top_col1, top_col2, top_col3 = st.columns(3)
    with top_col1:
        st.markdown(metric_card("Skills Detected", str(len(skills_found))), unsafe_allow_html=True)
    with top_col2:
        st.markdown(metric_card(
            "Job Description Match",
            f"{match_percentage}%" if match_percentage is not None else "N/A",
        ), unsafe_allow_html=True)
    with top_col3:
        st.markdown(metric_card("Projects Detected", str(parsed_resume.get("project_count", 0))),
                     unsafe_allow_html=True)

    st.write("")
    st.subheader("👤 Candidate Information")
    info_cols = st.columns(4)
    info_cols[0].markdown(f"**Name:**\n\n{parsed_resume['name']}")
    info_cols[1].markdown(f"**Email:**\n\n{parsed_resume['email'] or 'Not found'}")
    info_cols[2].markdown(f"**Phone:**\n\n{parsed_resume['phone'] or 'Not found'}")
    links = " ".join(filter(None, [parsed_resume["linkedin"], parsed_resume["github"]]))
    info_cols[3].markdown(f"**Links:**\n\n{links or 'Not found'}")

    st.divider()
    st.subheader("📊 ATS Score Breakdown")
    chart_col1, chart_col2, chart_col3 = st.columns([1, 1.3, 1])
    with chart_col1:
        try:
            gauge_fig = build_gauge_chart(ats_result["total"], "Overall ATS Score", accent)
            st.plotly_chart(gauge_fig, width='stretch', key=f"{key_prefix}_gauge")
        except Exception as exc:
            logger.exception("Gauge chart failed to render")
            st.warning("Couldn't render the score gauge.")
            with st.expander("Technical details"):
                st.code(traceback.format_exc())

    with chart_col2:
        try:
            radar_fig = build_radar_chart(ats_result["breakdown"], ats_result["max_scores"], accent)
            st.plotly_chart(radar_fig, width='stretch', key=f"{key_prefix}_radar")
        except Exception as exc:
            logger.exception("Radar chart failed to render")
            st.warning("Couldn't render the category radar chart.")
            with st.expander("Technical details"):
                st.code(traceback.format_exc())

    with chart_col3:
        try:
            if category_breakdown:
                fig2 = go.Figure(go.Pie(
                    labels=[f"{k} ({len(v)})" for k, v in category_breakdown.items()],
                    values=[len(v) for v in category_breakdown.values()],
                    hole=0.55,
                    marker=dict(colors=["#2874A6", "#6C5CE7", "#27AE60", "#F39C12", "#E74C3C", "#8E7CF5", "#5DADE2"]),
                ))
                fig2.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=10),
                                    title="Skills by Category", showlegend=False,
                                    paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, width='stretch', key=f"{key_prefix}_pie")
            else:
                st.info("No categorized skills detected to plot.")
        except Exception as exc:
            logger.exception("Category pie chart failed to render")
            st.warning("Couldn't render the skills-by-category chart.")
            with st.expander("Technical details"):
                st.code(traceback.format_exc())

    try:
        with st.expander("See exact score breakdown per category"):
            for cat, score in ats_result["breakdown"].items():
                max_val = ats_result["max_scores"][cat]
                ratio = max(0.0, min(score / max_val, 1.0)) if max_val else 0.0
                st.progress(ratio, text=f"{cat}: {score} / {max_val}")
    except Exception:
        logger.exception("Score breakdown progress bars failed to render")
        st.warning("Couldn't render the detailed score breakdown.")

    st.divider()
    skill_col1, skill_col2 = st.columns(2)
    with skill_col1:
        st.markdown('<div class="section-card"><div class="section-title">✅ Skills Found</div>'
                     + (pills_html(skills_found, "pill-found") or "No known skills detected.")
                     + "</div>", unsafe_allow_html=True)
    with skill_col2:
        if missing_skills:
            body = pills_html(missing_skills, "pill-missing")
        elif match_percentage is not None:
            body = "Great match! No missing skills detected."
        else:
            body = "Paste a job description to see missing skills."
        st.markdown('<div class="section-card"><div class="section-title">❌ Missing Skills</div>'
                     + body + "</div>", unsafe_allow_html=True)

    st.divider()
    st.subheader("🧩 Resume Sections Detected")
    section_labels = []
    for section, present in parsed_resume["sections"].items():
        css = "pill-section-on" if present else "pill-section-off"
        icon = "✓" if present else "—"
        section_labels.append(f'<span class="pill {css}">{icon} {section}</span>')
    st.markdown(f'<div class="badge-row">{"".join(section_labels)}</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("✍️ Writing Quality")
    q_col1, q_col2 = st.columns(2)
    with q_col1:
        st.markdown(metric_card("Strong Action Verbs Used", str(quality_report["strong_action_verb_count"])),
                     unsafe_allow_html=True)
        st.write("")
        if quality_report["weak_verb_bullets"]:
            with st.expander(f"⚠️ {len(quality_report['weak_verb_bullets'])} bullet(s) start with weak verbs"):
                for b in quality_report["weak_verb_bullets"]:
                    st.write(f"- {b}")
    with q_col2:
        if quality_report["passive_voice_sentences"]:
            with st.expander(f"⚠️ {len(quality_report['passive_voice_sentences'])} possibly passive-voice sentence(s)"):
                for s in quality_report["passive_voice_sentences"]:
                    st.write(f"- {s}")
        if quality_report["long_bullets"]:
            with st.expander(f"⚠️ {len(quality_report['long_bullets'])} bullet(s) are too long"):
                for b in quality_report["long_bullets"]:
                    st.write(f"- {b}")

    st.divider()
    st.subheader("💡 Suggestions for Improvement")
    for s in suggestions:
        st.markdown(f"- {s}")

    st.divider()
    st.subheader("⬇️ Download Report")
    dl_col1, dl_col2, dl_col3 = st.columns(3)

    safe_name = (parsed_resume["name"] or "resume").replace(" ", "_")

    with dl_col1:
        try:
            pdf_bytes = build_pdf_report(
                parsed_resume, ats_result, skills_found, missing_skills,
                suggestions, match_percentage,
            )
            st.download_button(
                "📄 Download PDF Report", data=pdf_bytes,
                file_name=f"ResumeIQ_Report_{safe_name}.pdf",
                mime="application/pdf", key=f"{key_prefix}_pdf",
            )
        except ResumeIQError as exc:
            st.error(f"Could not generate PDF report: {exc}")

    with dl_col2:
        try:
            docx_bytes = build_docx_report(
                parsed_resume, ats_result, skills_found, missing_skills,
                suggestions, match_percentage,
            )
            st.download_button(
                "📝 Download DOCX Report", data=docx_bytes,
                file_name=f"ResumeIQ_Report_{safe_name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"{key_prefix}_docx",
            )
        except ResumeIQError as exc:
            st.error(f"Could not generate DOCX report: {exc}")

    with dl_col3:
        if st.button("💾 Save to History", key=f"{key_prefix}_save"):
            try:
                save_analysis(parsed_resume, ats_result, skills_found, missing_skills, match_percentage)
                st.success("Saved to history.")
            except ResumeIQError as exc:
                st.error(f"Could not save to history: {exc}")


# ----------------------------- Tabs -----------------------------
tab_analyze, tab_compare, tab_history = st.tabs(["🔍 Analyze", "⚖️ Compare Resumes", "📚 History Dashboard"])


# ============================= TAB 1: ANALYZE =============================
with tab_analyze:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1️⃣ Upload Resume")
        uploaded_file = st.file_uploader("Choose a PDF resume (max 10 MB)", type=["pdf"], key="single_upload")
    with col2:
        st.subheader("2️⃣ Paste Job Description (optional)")
        job_description = st.text_area(
            "Paste the job description here for skill matching",
            height=180,
            placeholder="e.g. We are looking for a Python developer with experience in "
                        "Docker, AWS, REST APIs, and Machine Learning...",
            key="single_jd",
        )

    analyze_clicked = st.button("🔍 Analyze Resume", type="primary", key="single_analyze")

    if analyze_clicked:
        if uploaded_file is None:
            st.error("Please upload a PDF resume first.")
        else:
            try:
                with st.spinner("Analyzing resume..."):
                    result = run_analysis(uploaded_file, job_description)
                st.session_state.single_result = result
                st.session_state.single_result_filename = uploaded_file.name
                st.session_state.single_result_saved = False  # fresh result, not yet auto-saved
            except ResumeIQError as exc:
                st.session_state.single_result = None
                st.error(f"⚠️ {exc}")
            except Exception:
                st.session_state.single_result = None
                logger.exception("Unexpected error during analysis")
                st.error("An unexpected error occurred while analyzing this resume.")
                with st.expander("🔧 Technical details (share this if the problem persists)"):
                    st.code(traceback.format_exc())

    # Render from session_state (not just on the click run) so the results stay visible
    # while the user clicks downloads, saves, dark mode, etc. on later reruns.
    if st.session_state.get("single_result"):
        result = st.session_state.single_result
        filename = st.session_state.get("single_result_filename", "resume")

        st.success("Analysis complete!")

        if st.session_state.auto_save_history and not st.session_state.get("single_result_saved"):
            try:
                save_analysis(
                    result["parsed_resume"], result["ats_result"], result["skills_found"],
                    result["missing_skills"], result["match_percentage"],
                )
                st.session_state.single_result_saved = True
                st.caption("💾 Automatically saved to history.")
            except ResumeIQError as exc:
                st.warning(f"Analysis complete, but auto-save to history failed: {exc}")

        st.divider()
        render_analysis_result(result, key_prefix="single")

        if st.button("➕ Add this result to Compare tab", key="add_to_pool"):
            st.session_state.comparison_pool.append({
                "label": filename,
                "parsed_resume": result["parsed_resume"],
                "ats_result": result["ats_result"],
                "skills_found": result["skills_found"],
            })
            st.success(f"Added '{filename}' to the comparison pool.")
    elif not analyze_clicked:
        st.info("Upload a resume and click **Analyze Resume** to get started.")


# ============================= TAB 2: COMPARE =============================
with tab_compare:
    st.subheader("Upload multiple resumes to compare them side by side")
    compare_files = st.file_uploader(
        "Choose 2+ PDF resumes", type=["pdf"], accept_multiple_files=True, key="multi_upload"
    )

    if st.button("⚖️ Compare Resumes", type="primary", key="compare_button"):
        if not compare_files or len(compare_files) < 2:
            st.error("Please upload at least 2 resumes to compare.")
        else:
            entries = []
            errors = []
            with st.spinner("Analyzing all resumes..."):
                for f in compare_files:
                    try:
                        result = run_analysis(f, "")
                        entries.append({
                            "label": f.name,
                            "parsed_resume": result["parsed_resume"],
                            "ats_result": result["ats_result"],
                            "skills_found": result["skills_found"],
                        })
                    except ResumeIQError as exc:
                        errors.append(f"{f.name}: {exc}")
                    except Exception:
                        logger.exception("Unexpected error analyzing %s", f.name)
                        errors.append(f"{f.name}: unexpected error, skipped.")

            for err in errors:
                st.warning(f"⚠️ {err}")

            if len(entries) < 2:
                st.error("At least 2 resumes must parse successfully to run a comparison.")
            else:
                st.success(f"Compared {len(entries)} resumes.")
                ranked = rank_resumes(entries)
                table_rows = build_comparison_table(ranked)

                accent = "#5DADE2" if st.session_state.dark_mode else "#2874A6"
                chart_col, table_col = st.columns([1, 1])

                with chart_col:
                    st.subheader("📊 ATS Score Comparison")
                    labels = [row["Resume"] for row in table_rows]
                    scores = [row["ATS Score"] for row in table_rows]
                    bar_colors = ["#27AE60" if s >= 75 else "#F39C12" if s >= 50 else "#E74C3C" for s in scores]
                    fig = go.Figure(go.Bar(
                        x=scores, y=labels, orientation="h", marker_color=bar_colors,
                        text=[f"{s}%" for s in scores], textposition="outside",
                    ))
                    fig.update_layout(
                        height=max(260, 60 * len(labels)), xaxis_range=[0, 105],
                        margin=dict(l=10, r=30, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, width='stretch', key="compare_bar")

                with table_col:
                    st.subheader("📋 Comparison Table (ranked)")
                    st.dataframe(table_rows, width='stretch', height=max(260, 40 * len(table_rows)))

                skill_overlap = find_common_and_unique_skills(entries)
                st.divider()
                st.subheader("🧠 Skill Overlap")
                st.markdown(
                    '<div class="section-card"><div class="section-title">Common to all resumes</div>'
                    + (pills_html(skill_overlap["common"], "pill-found") or "None") + "</div>",
                    unsafe_allow_html=True,
                )
                for label, unique_skills in skill_overlap["unique"].items():
                    st.markdown(
                        f'<div class="section-card"><div class="section-title">Unique to {label}</div>'
                        + (pills_html(unique_skills, "pill-missing") or "None") + "</div>",
                        unsafe_allow_html=True,
                    )

    elif st.session_state.comparison_pool:
        st.info(
            f"You have {len(st.session_state.comparison_pool)} resume(s) saved from the Analyze tab. "
            "Upload files above and click Compare to run a fresh comparison."
        )


# ============================= TAB 3: HISTORY =============================
with tab_history:
    st.subheader("📚 Analysis History")
    try:
        records = get_all_analyses()
    except ResumeIQError as exc:
        records = []
        st.error(f"Could not load history: {exc}")

    if not records:
        st.info("No saved analyses yet. Analyze a resume and click 'Save to History'.")
    else:
        accent = "#5DADE2" if st.session_state.dark_mode else "#2874A6"

        avg_score = sum(r["ats_total"] for r in records) / len(records)
        best_score = max(r["ats_total"] for r in records)
        m1, m2, m3 = st.columns(3)
        m1.markdown(metric_card("Saved Analyses", str(len(records))), unsafe_allow_html=True)
        m2.markdown(metric_card("Average ATS Score", f"{avg_score:.1f}%"), unsafe_allow_html=True)
        m3.markdown(metric_card("Best ATS Score", f"{best_score:.1f}%"), unsafe_allow_html=True)

        st.write("")
        chronological = list(reversed(records))  # oldest first, for a left-to-right trend

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.subheader("📈 ATS Score Trend")
            fig_trend = go.Figure(go.Scatter(
                x=list(range(1, len(chronological) + 1)),
                y=[r["ats_total"] for r in chronological],
                mode="lines+markers", line=dict(color=accent, width=3),
                marker=dict(size=8, color=accent),
                text=[r["name"] for r in chronological], hovertemplate="%{text}: %{y}%<extra></extra>",
            ))
            fig_trend.update_layout(
                height=300, xaxis_title="Analysis #", yaxis_title="ATS Score (%)",
                yaxis_range=[0, 100], margin=dict(l=10, r=10, t=20, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_trend, width='stretch', key="history_trend")

        with chart_col2:
            st.subheader("📊 Average Score by Category")
            category_totals, category_counts = {}, {}
            for r in records:
                for cat, score in (r["breakdown"] or {}).items():
                    category_totals[cat] = category_totals.get(cat, 0) + score
                    category_counts[cat] = category_counts.get(cat, 0) + 1
            if category_totals:
                cats = list(category_totals.keys())
                avgs = [round(category_totals[c] / category_counts[c], 1) for c in cats]
                fig_cat = go.Figure(go.Bar(x=cats, y=avgs, marker_color=accent,
                                            text=avgs, textposition="outside"))
                fig_cat.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10),
                                       paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_cat, width='stretch', key="history_category")
            else:
                st.info("No category breakdown data available yet.")

        st.divider()
        st.subheader("📋 All Saved Analyses")
        display_rows = [
            {
                "Date": r["created_at"][:19].replace("T", " "),
                "Name": r["name"],
                "Email": r["email"],
                "ATS Score": r["ats_total"],
                "Skills": len(r["skills_found"] or []),
                "JD Match %": r["match_percentage"],
            }
            for r in records
        ]
        st.dataframe(display_rows, width='stretch')

        if st.button("🗑️ Clear History", key="clear_history"):
            try:
                clear_history()
                st.success("History cleared. Refresh the tab to see the change.")
            except ResumeIQError as exc:
                st.error(f"Could not clear history: {exc}")
