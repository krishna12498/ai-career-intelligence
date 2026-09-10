from backend.app.models.application_strategy import ApplicationStrategyResponse
from backend.app.models.multi_match import CrossJobGapAnalysis, MultiMatchJobResult, TargetRecommendation
from backend.app.models.target_action_package import (
    TargetActionStep,
    TargetActionPackageResponse,
    TargetInterviewQuestion,
    TargetResumeTailoringGuidance,
)


SCOPE_NOTE = (
    "V4.6 Target Action Package post-processing layer. All recommendations are grounded in explicit "
    "target job requirements, candidate resume evidence, and cross-job gap analysis without fabricated claims."
)


def generate_target_action_package(
    job_results: list[MultiMatchJobResult],
    gap_analysis: CrossJobGapAnalysis | None = None,
    target_recommendation: TargetRecommendation | None = None,
    application_strategy: ApplicationStrategyResponse | None = None,
) -> TargetActionPackageResponse:
    """
    Generates a grounded, job-specific target action execution package.
    """
    if not target_recommendation or target_recommendation.status == "no_completed_jobs":
        return TargetActionPackageResponse(
            status="no_completed_jobs",
            primary_target_job_id=None,
            primary_target_label=None,
            reason_codes=["no_completed_jobs_action_package"],
            action_plan=[],
            interview_blueprint=[],
            resume_tailoring=[],
            scope_note=SCOPE_NOTE,
        )

    target_id = target_recommendation.selected_job_id
    target_job_result = next((j for j in job_results if j.job_id == target_id and j.status == "completed"), None)

    if not target_job_result or not target_job_result.match_report:
        return TargetActionPackageResponse(
            status="no_completed_jobs",
            primary_target_job_id=target_id,
            primary_target_label=target_recommendation.selected_label,
            reason_codes=["no_completed_jobs_action_package"],
            action_plan=[],
            interview_blueprint=[],
            resume_tailoring=[],
            scope_note=SCOPE_NOTE,
        )

    target_label = target_job_result.label or target_id
    report = target_job_result.match_report

    reason_codes: list[str] = []
    timeline_status = application_strategy.timeline_status if application_strategy else "polish_and_apply"

    # Timeline reason code
    if timeline_status == "apply_now":
        reason_codes.append("action_plan_immediate_application")
    else:
        reason_codes.append("action_plan_focused_upskilling")

    # Categorize matches
    strong_matches = [
        m for m in report.matches
        if getattr(m.status, "value", str(m.status)) in {"Strong Match", "strong_match"}
    ]
    partial_matches = [
        m for m in report.matches
        if getattr(m.status, "value", str(m.status)) in {"Partial Match", "partial_match"}
    ]
    missing_required = [
        m for m in report.matches
        if getattr(m.status, "value", str(m.status)) in {"Missing", "missing"} and m.match_type == "required"
    ]
    missing_preferred = [
        m for m in report.matches
        if getattr(m.status, "value", str(m.status)) in {"Missing", "missing"} and m.match_type == "preferred"
    ]

    # 1. Resume Tailoring Guidance & Claim Protection
    resume_tailoring: list[TargetResumeTailoringGuidance] = []

    # Handle missing required skills with strict claim protection
    if missing_required or missing_preferred:
        reason_codes.append("resume_claim_protection_applied")

    for m in missing_required:
        resume_tailoring.append(
            TargetResumeTailoringGuidance(
                target_skill=m.job_skill,
                requirement_type="required",
                current_gap_status="missing",
                section="Experience / Projects",
                current_evidence=None,
                recommended_action=f"Do not claim '{m.job_skill}' unless you have genuine experience. Focus on learning and building evidence.",
                risk_warning="Do not claim this skill unless you have genuine experience. Consider adding evidence after completing a relevant project.",
                grounding_note=f"Requirement '{m.job_skill}' is marked as missing in candidate resume evidence.",
            )
        )

    for m in partial_matches:
        resume_tailoring.append(
            TargetResumeTailoringGuidance(
                target_skill=m.job_skill,
                requirement_type=m.match_type if m.match_type in {"required", "preferred"} else "required",
                current_gap_status="partial",
                section="Experience / Projects",
                current_evidence=f"Candidate evidence: '{m.candidate_skill}'",
                recommended_action=f"Rephrase experience to explicitly connect '{m.candidate_skill}' to target requirement '{m.job_skill}'.",
                risk_warning=None,
                grounding_note=f"Partial match found between '{m.candidate_skill}' and '{m.job_skill}'.",
            )
        )

    for m in strong_matches[:3]:
        resume_tailoring.append(
            TargetResumeTailoringGuidance(
                target_skill=m.job_skill,
                requirement_type=m.match_type if m.match_type in {"required", "preferred"} else "required",
                current_gap_status="strong_match",
                section="Summary / Top Core Competencies",
                current_evidence=f"Verified strong match for '{m.job_skill}'",
                recommended_action=f"Prominently place '{m.job_skill}' near top of resume summary.",
                risk_warning=None,
                grounding_note=f"Verified strong match for target role requirement '{m.job_skill}'.",
            )
        )

    reason_codes.append("resume_edits_grounded_in_target_requirements")

    # 2. Technical Interview Blueprint
    interview_blueprint: list[TargetInterviewQuestion] = []

    for m in strong_matches[:3]:
        interview_blueprint.append(
            TargetInterviewQuestion(
                topic_id=f"topic-{m.job_skill.lower().replace(' ', '-')}",
                category="Core Competency",
                question_type="technical_deep_dive",
                question=f"Can you explain your experience and architecture decisions when working with {m.job_skill}?",
                target_skill=m.job_skill,
                recommended_focus=f"Prepare a STAR story demonstrating practical production experience with {m.job_skill}.",
                grounding_note=f"Grounded in verified strong skill '{m.job_skill}'.",
            )
        )

    if missing_required:
        reason_codes.append("interview_blueprint_gap_defense_included")
        for m in missing_required[:2]:
            interview_blueprint.append(
                TargetInterviewQuestion(
                    topic_id=f"gap-{m.job_skill.lower().replace(' ', '-')}",
                    category="Requirement Defense",
                    question_type="gap_defense",
                    question=f"The role requires {m.job_skill}. How would you bridge your current experience to meet this requirement?",
                    target_skill=m.job_skill,
                    recommended_focus=f"Emphasize transferable skills, rapid learning capability, and related conceptual knowledge.",
                    grounding_note=f"Grounded in missing target requirement '{m.job_skill}'.",
                )
            )

    # 3. Action Plan Steps
    action_plan: list[TargetActionStep] = []
    step_num = 1

    # Step 1: Immediate Resume Alignment
    if strong_matches:
        action_plan.append(
            TargetActionStep(
                step_number=step_num,
                priority="immediate",
                skill=strong_matches[0].job_skill,
                action_type="resume_polish",
                title=f"Align Resume Summary for {target_label}",
                description=f"Tailor top core competencies around verified strengths: {', '.join(m.job_skill for m in strong_matches[:3])}.",
                grounding_note="Based on strong match requirements for selected target job.",
            )
        )
        step_num += 1

    # Step 2: Cross-job quick wins or missing requirements
    quick_win_skills: list[str] = []
    if gap_analysis and gap_analysis.gaps:
        quick_win_skills = [
            g.skill for g in gap_analysis.gaps
            if (g.missing_count + g.partial_count) > 1
        ][:3]

    if quick_win_skills:
        reason_codes.append("cross_job_quick_wins_integrated")
        action_plan.append(
            TargetActionStep(
                step_number=step_num,
                priority="short_term",
                skill=quick_win_skills[0],
                action_type="skill_upskilling",
                title=f"Address High-Leverage Cross-Job Skill: {quick_win_skills[0]}",
                description=f"Skill '{quick_win_skills[0]}' is required across multiple target roles. Focus learning here first.",
                grounding_note="Cross-job gap analysis identified high multi-job ROI.",
            )
        )
        step_num += 1
    elif missing_required:
        action_plan.append(
            TargetActionStep(
                step_number=step_num,
                priority="short_term",
                skill=missing_required[0].job_skill,
                action_type="skill_upskilling",
                title=f"Target Required Skill Upskilling: {missing_required[0].job_skill}",
                description=f"Complete a focused hands-on tutorial or mini-project on {missing_required[0].job_skill}.",
                grounding_note="Target job has explicit missing requirement.",
            )
        )
        step_num += 1

    # Step 3: Evidence Strengthening
    if partial_matches:
        action_plan.append(
            TargetActionStep(
                step_number=step_num,
                priority="medium_term",
                skill=partial_matches[0].job_skill,
                action_type="evidence_strengthening",
                title=f"Strengthen Evidence for {partial_matches[0].job_skill}",
                description=f"Refine experience bullet points to explicitly demonstrate proficiency in {partial_matches[0].job_skill}.",
                grounding_note="Partial skill match candidate evidence identified.",
            )
        )
        step_num += 1

    # Step 4: Technical Interview Preparation
    action_plan.append(
        TargetActionStep(
            step_number=step_num,
            priority="medium_term",
            skill=strong_matches[0].job_skill if strong_matches else "Target Skills",
            action_type="interview_prep",
            title=f"Mock Interview Preparation for {target_label}",
            description="Practice technical responses and STAR scenario stories focusing on primary role requirements.",
            grounding_note="Tailored to target job blueprint.",
        )
    )

    return TargetActionPackageResponse(
        status="action_package_generated",
        target_job_id=target_id,
        target_label=target_label,
        reason_codes=reason_codes,
        action_plan=action_plan,
        interview_blueprint=interview_blueprint,
        resume_tailoring=resume_tailoring,
        scope_note=SCOPE_NOTE,
    )
