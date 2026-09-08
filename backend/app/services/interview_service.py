"""Grounded interview question generation and rubric-based answer feedback."""

from backend.app.models.interview import (
    InterviewEvaluation,
    InterviewEvaluationRequest,
    InterviewQuestion,
    InterviewQuestionsResponse,
)
from backend.app.services.match_service import match_from_text
from backend.app.services.resume_service import parse_resume_text
from backend.app.services.job_analyzer import analyze_job_description

GROUNDING_POLICY = (
    "Questions use only skills and role details extracted from the job description "
    "and claims or skills extracted from the resume. Answer feedback measures coverage "
    "and clarity; it does not verify that a candidate's claims are true."
)


def _question(
    question_id: str,
    category: str,
    text: str,
    evidence: list[str],
) -> InterviewQuestion:
    return InterviewQuestion(
        id=question_id,
        category=category,
        question=text,
        evidence=evidence,
        grounding_note="Evidence lists the source terms used to form this question.",
    )


def _build_questions(resume_text: str, job_description: str, limit: int) -> list[InterviewQuestion]:
    resume = parse_resume_text(resume_text)
    job = analyze_job_description(job_description, use_semantic=False)
    match = match_from_text(resume_text, job_description, use_semantic=False)
    questions: list[InterviewQuestion] = []

    technical_skills = job.required_skills[:limit]
    for index, skill in enumerate(technical_skills, start=1):
        questions.append(
            _question(
                f"technical-{index}",
                "technical",
                f"How would you use {skill} to contribute in this role?",
                [skill],
            )
        )

    resume_evidence: list[tuple[str, str, list[str]]] = []
    for experience in resume.experience:
        evidence = [term for term in [experience.title, experience.company] if term and term != "Unknown"]
        if experience.description:
            evidence.append(experience.description[:120])
        if evidence:
            resume_evidence.append((experience.title, experience.company, evidence))
    for project in resume.projects:
        evidence = [term for term in [project.name, project.description] if term]
        if evidence:
            resume_evidence.append((project.name, "project", evidence))

    for index, (title, context, evidence) in enumerate(resume_evidence[:limit], start=1):
        questions.append(
            _question(
                f"resume-{index}",
                "resume-specific",
                f"Walk us through your work on {title} ({context}) and the contribution you made.",
                evidence,
            )
        )

    role = job.job_title if job.job_title != "Not specified" else "this role"
    questions.append(
        _question(
            "behavioral-1",
            "behavioral",
            f"Tell us about a time you solved a difficult problem relevant to {role}.",
            [role] if role != "this role" else [],
        )
    )
    if limit > 1:
        questions.append(
            _question(
                "behavioral-2",
                "behavioral",
                "Describe how you prioritize work when a project has competing requirements.",
                [],
            )
        )

    gap_matches = [
        skill_match
        for skill_match in match.matches
        if skill_match.status.value in {"Missing", "Partial Match"}
    ]
    for index, skill_match in enumerate(gap_matches[:limit], start=1):
        if skill_match.candidate_skill:
            text = (
                f"How would your experience with {skill_match.candidate_skill} transfer to "
                f"{skill_match.job_skill} in this role?"
            )
            evidence = [skill_match.candidate_skill, skill_match.job_skill]
        else:
            text = f"How would you approach developing {skill_match.job_skill} for this role?"
            evidence = [skill_match.job_skill]
        questions.append(_question(f"gap-{index}", "gap", text, evidence))

    return questions


def generate_interview_questions(
    resume_text: str,
    job_description: str,
    questions_per_category: int = 2,
    use_semantic: bool = True,
) -> InterviewQuestionsResponse:
    # Keep the public switch compatible with the matching workflow; questions use
    # explicit keyword evidence so semantic inference cannot invent resume claims.
    del use_semantic
    questions = _build_questions(resume_text, job_description, questions_per_category)
    return InterviewQuestionsResponse(questions=questions, grounding_policy=GROUNDING_POLICY)


def evaluate_interview_answer(request: InterviewEvaluationRequest) -> InterviewEvaluation:
    answer = " ".join(request.answer.lower().split())
    evidence_hits = [term for term in request.question.evidence if term.lower() in answer]
    has_detail = len(answer.split()) >= 20
    score = 35
    strengths: list[str] = []
    improvements: list[str] = []

    if has_detail:
        score += 25
        strengths.append("The answer provides enough detail to discuss further.")
    else:
        improvements.append("Add a specific example with your action and the result.")

    if evidence_hits:
        score += 30
        strengths.append(f"It addresses the grounded topic: {', '.join(evidence_hits)}.")
    elif request.question.evidence:
        improvements.append(
            f"Connect the answer explicitly to the question evidence: {', '.join(request.question.evidence[:2])}."
        )
    else:
        score += 10

    if "result" not in answer and "impact" not in answer and "outcome" not in answer:
        improvements.append("End with an outcome, result, or lesson learned.")
    else:
        score += 10
        strengths.append("It includes an outcome-oriented reflection.")

    return InterviewEvaluation(
        question_id=request.question.id,
        score=min(score, 100),
        strengths=strengths,
        improvements=improvements,
        feedback="This rubric evaluates answer structure and coverage, not whether the candidate's claims are factual.",
        grounding_note="Feedback is based only on the submitted answer and the question evidence.",
    )
