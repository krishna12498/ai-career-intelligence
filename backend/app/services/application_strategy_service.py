from backend.app.models.application_strategy import ApplicationStrategyResponse, StrategyPillar
from backend.app.models.multi_match import CrossJobGapAnalysis, MultiMatchJobResult, TargetRecommendation


def generate_application_strategy(
    job_results: list[MultiMatchJobResult],
    gap_analysis: CrossJobGapAnalysis | None = None,
    target_recommendation: TargetRecommendation | None = None,
) -> ApplicationStrategyResponse:
    """
    Generates a deterministic application strategy based on multi-match analysis,
    ranking, cross-job gap analysis, and target recommendation.
    """
    if not target_recommendation or target_recommendation.status == "no_completed_jobs":
        return ApplicationStrategyResponse(
            status="no_completed_jobs",
            primary_target_job_id=None,
            primary_target_label=None,
            timeline_status="no_target_resume_overhaul",
            headline="No completed job analysis available. Perform resume overhaul before applying.",
            reason_codes=["no_completed_jobs_resume_overhaul"],
            pillars=[
                StrategyPillar(
                    category="resume_tailoring",
                    title="Resume Overhaul Needed",
                    description="No target job could be analyzed. Ensure job descriptions and resume text are valid.",
                    items=["Check resume formatting and text clarity", "Provide complete job description requirements"],
                )
            ],
            scope_note="V4.5 Application strategy post-processing layer. No completed job analysis found.",
        )

    target_id = target_recommendation.selected_job_id
    target_job_result = next((j for j in job_results if j.job_id == target_id and j.status == "completed"), None)

    if not target_job_result or not target_job_result.match_report:
        return ApplicationStrategyResponse(
            status="no_completed_jobs",
            primary_target_job_id=target_id,
            primary_target_label=target_recommendation.selected_label,
            timeline_status="no_target_resume_overhaul",
            headline="Target job data unavailable. Re-verify analysis inputs.",
            reason_codes=["no_completed_jobs_resume_overhaul"],
            pillars=[],
            scope_note="V4.5 Application strategy post-processing layer. Selected target job match data missing.",
        )

    target_label = target_job_result.label or target_id
    report = target_job_result.match_report
    score = target_recommendation.selected_score or 0.0
    coverage = target_recommendation.selected_required_skill_coverage or 0.0

    reason_codes: list[str] = []
    
    # 1. Timeline & Readiness
    if score >= 80.0 and coverage >= 0.85:
        timeline_status = "apply_now"
        headline = f"Strong fit for {target_label} ({score:.0f}% match). Recommended for immediate application."
        reason_codes.append("high_match_immediate_apply")
    elif score >= 60.0 or coverage >= 0.60:
        timeline_status = "polish_and_apply"
        headline = f"Good match for {target_label} ({score:.0f}% match). Tailor resume before submitting."
        reason_codes.append("strong_coverage_minor_polish")
    else:
        timeline_status = "skill_up_first"
        headline = f"Skill gaps identified for {target_label} ({score:.0f}% match). Address key requirements before applying."
        reason_codes.append("critical_required_skills_missing")

    # 2. Cross-Job Quick-Win Skills
    quick_wins: list[str] = []
    if gap_analysis and gap_analysis.gaps:
        multi_gaps = [
            g.skill for g in gap_analysis.gaps
            if (g.missing_count + g.partial_count) > 1
        ]
        if multi_gaps:
            quick_wins = multi_gaps[:5]
            reason_codes.append("cross_job_leveraged_skill_focus")

    # 3. Resume Tailoring Items
    strong_skills = [
        m.job_skill for m in report.matches
        if getattr(m.status, "value", str(m.status)) in {"Strong Match", "strong_match"}
    ][:5]
    missing_required = [
        m.job_skill for m in report.matches
        if getattr(m.status, "value", str(m.status)) in {"Missing", "missing"} and m.match_type == "required"
    ][:5]
    
    tailoring_items: list[str] = []
    if strong_skills:
        tailoring_items.append(f"Prominently emphasize top matching skills: {', '.join(strong_skills)}")
    if missing_required:
        tailoring_items.append(f"Highlight any related/transferable experience for key missing requirements: {', '.join(missing_required)}")

    pillars: list[StrategyPillar] = [
        StrategyPillar(
            category="resume_tailoring",
            title=f"Tailoring Strategy for {target_label}",
            description="Customize your resume summary and experience bullet points for this specific role.",
            items=tailoring_items if tailoring_items else ["Align resume summary with core job responsibilities"],
        )
    ]

    if quick_wins:
        pillars.append(
            StrategyPillar(
                category="quick_win_skills",
                title="Cross-Job High-Leverage Skills",
                description="Skills missing across multiple target jobs that provide maximum career ROI.",
                items=[f"Prioritize learning/demonstrating: {s}" for s in quick_wins],
            )
        )

    if missing_required:
        pillars.append(
            StrategyPillar(
                category="project_focus",
                title="Targeted Project Recommendations",
                description="Build or feature mini-projects demonstrating required competencies.",
                items=[f"Create a hands-on proof-of-concept for {skill}" for skill in missing_required[:3]],
            )
        )

    pillars.append(
        StrategyPillar(
            category="interview_preparation",
            title="Interview Preparation Focus",
            description="Be prepared to discuss these core technical areas during screening interviews.",
            items=[f"Prepare STAR stories around {skill}" for skill in (strong_skills[:3] or ["key technical projects"])],
        )
    )

    return ApplicationStrategyResponse(
        status="strategy_generated",
        primary_target_job_id=target_id,
        primary_target_label=target_label,
        timeline_status=timeline_status,
        headline=headline,
        reason_codes=reason_codes,
        pillars=pillars,
        scope_note="V4.5 Application strategy post-processing layer. Advisory strategy generated deterministically.",
    )
