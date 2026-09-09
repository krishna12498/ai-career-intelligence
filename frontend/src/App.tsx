import { useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const demoResume = `Alex Morgan
Python backend engineer with experience building APIs and data products.

Skills
Python, FastAPI, SQL, Git, Docker, machine learning

Experience
Backend Engineer | Northstar Labs | 2022 - Present
Built FastAPI services, automated data workflows, and containerized deployments.

Projects
Career match assistant | Built a resume and job matching tool with Python and embeddings.`

const demoJob = `Junior AI Engineer

We are looking for a Python engineer to build practical machine learning products.

Required: Python, FastAPI, SQL, Docker, AWS, machine learning.
Preferred: LangChain, RAG, LangGraph.`

type MatchResult = {
  overall_match: number
  skills_match: number
  project_relevance: number
  experience_relevance: number
  education_match: number
  semantic_similarity: number
  strong_skills: string[]
  partial_skills: string[]
  missing_skills: string[]
  recommended_priority: string[]
}

type ReadinessBlocker = {
  skill: string
  status: string
  reason: string
}

type ReadinessResult = {
  readiness_score: number
  required_skill_coverage: number
  experience_evidence: number
  project_evidence: number
  blockers: ReadinessBlocker[]
  reasons: string[]
  scope_note: string
}

type RoadmapItem = {
  order: number
  horizon: string
  skill: string
  priority: string
  status?: string
  reason: string
  resource?: { title: string; summary: string; level: string; url: string; source: string }
  grounding_note: string
}

type RoadmapResult = {
  items: RoadmapItem[]
  source: string
  grounding_policy: string
}

type OptimizationEvidence = {
  source_type: string
  source_text: string
  source_section?: string
  support: string
}

type OptimizationSuggestion = {
  id: string
  section: string
  operation: string
  original_text?: string
  proposed_text: string
  evidence: OptimizationEvidence[]
  status: string
  risk_flags: string[]
  grounding_note: string
}

type OptimizationResult = {
  base_version_id: string
  target_role: string
  grounding_policy: string
  suggestions: OptimizationSuggestion[]
}

type AdvisorResult = {
  explanation: string
  resource?: { title: string; url: string; level: string }
}

type ImprovementSuggestion = {
  category: string
  priority: string
  title: string
  action: string
  evidence: string[]
  grounding_note: string
}

type ImprovementResult = {
  missing_required_skills: string[]
  missing_preferred_skills: string[]
  suggestions: ImprovementSuggestion[]
  grounding_policy: string
}

type InterviewQuestion = {
  id: string
  category: string
  question: string
  evidence: string[]
  grounding_note: string
}

type InterviewEvaluation = {
  question_id: string
  score: number
  strengths: string[]
  improvements: string[]
  feedback: string
  grounding_note: string
}

type InterviewSessionAnswer = {
  question_id: string
  answer: string
  evaluation: InterviewEvaluation
  submitted_at: string
}

type InterviewSession = {
  session_id: string
  status: string
  questions: InterviewQuestion[]
  answers: InterviewSessionAnswer[]
  created_at: string
  grounding_policy: string
  progress_percent: number
  summary?: {
    overall_structure_coverage: number
    category_structure_coverage: Record<string, number>
    recurring_feedback_themes: string[]
    answered: number
    total_questions: number
    completion_status: string
  }
}

function App() {
  const [resume, setResume] = useState('')
  const [job, setJob] = useState('')
  const [match, setMatch] = useState<MatchResult | null>(null)
  const [readiness, setReadiness] = useState<ReadinessResult | null>(null)
  const [roadmap, setRoadmap] = useState<RoadmapResult | null>(null)
  const [optimization, setOptimization] = useState<OptimizationResult | null>(null)
  const [advisor, setAdvisor] = useState<AdvisorResult | null>(null)
  const [improvement, setImprovement] = useState<ImprovementResult | null>(null)
  const [interviewQuestions, setInterviewQuestions] = useState<InterviewQuestion[]>([])
  const [selectedQuestion, setSelectedQuestion] = useState<InterviewQuestion | null>(null)
  const [interviewEvaluation, setInterviewEvaluation] = useState<InterviewEvaluation | null>(null)
  const [interviewSession, setInterviewSession] = useState<InterviewSession | null>(null)
  const [sessionQuestion, setSessionQuestion] = useState<InterviewQuestion | null>(null)
  const [sessionAnswer, setSessionAnswer] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [advisorLoading, setAdvisorLoading] = useState(false)
  const [improvementLoading, setImprovementLoading] = useState(false)
  const [interviewLoading, setInterviewLoading] = useState(false)
  const [roadmapLoading, setRoadmapLoading] = useState(false)
  const [optimizationLoading, setOptimizationLoading] = useState(false)
  const [evaluationLoading, setEvaluationLoading] = useState(false)
  const [error, setError] = useState('')
  const [advisorError, setAdvisorError] = useState('')
  const [improvementError, setImprovementError] = useState('')
  const [interviewError, setInterviewError] = useState('')
  const [sessionError, setSessionError] = useState('')
  const [roadmapError, setRoadmapError] = useState('')
  const [optimizationError, setOptimizationError] = useState('')

  const runMatch = async () => {
    if (resume.trim().length < 50 || job.trim().length < 30) {
      setError('Add a resume of at least 50 characters and a job description of at least 30 characters.')
      return
    }
    setLoading(true)
    setError('')
    setReadiness(null)
    setRoadmap(null)
    setOptimization(null)
    setAdvisor(null)
    setAdvisorError('')
    setImprovement(null)
    setImprovementError('')
    setInterviewQuestions([])
    setSelectedQuestion(null)
    setInterviewEvaluation(null)
    setAnswer('')
    setInterviewError('')
    setInterviewSession(null)
    setSessionQuestion(null)
    setSessionAnswer('')
    setSessionError('')
    setRoadmapError('')
    setOptimizationError('')
    try {
      const response = await fetch(`${API_BASE}/api/match/from-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resume, job_description: job, use_semantic: true }),
      })
      if (!response.ok) throw new Error('The matching service could not process these inputs.')
      const matchResult: MatchResult = await response.json()
      setMatch(matchResult)

      const readinessResponse = await fetch(`${API_BASE}/api/readiness`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ match_report: matchResult }),
      })
      if (!readinessResponse.ok) throw new Error('Could not calculate job readiness.')
      setReadiness(await readinessResponse.json())
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  const buildRoadmap = async () => {
    if (!match) return
    setRoadmapLoading(true)
    setRoadmapError('')
    try {
      const response = await fetch(`${API_BASE}/api/roadmap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ match_report: match, candidate_context: resume.slice(0, 4000), max_items: 6 }),
      })
      if (!response.ok) throw new Error('Could not build the learning roadmap.')
      setRoadmap(await response.json())
    } catch (requestError) {
      setRoadmapError(requestError instanceof Error ? requestError.message : 'Could not build the learning roadmap.')
    } finally {
      setRoadmapLoading(false)
    }
  }

  const buildOptimizationSuggestions = async () => {
    setOptimizationLoading(true)
    setOptimizationError('')
    try {
      const response = await fetch(`${API_BASE}/api/resume/optimization/suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ master_resume_text: resume, job_description: job, base_version_id: 'master', use_semantic: false }),
      })
      if (!response.ok) throw new Error('Could not build resume optimization suggestions.')
      setOptimization(await response.json())
    } catch (requestError) {
      setOptimizationError(requestError instanceof Error ? requestError.message : 'Could not build resume optimization suggestions.')
    } finally {
      setOptimizationLoading(false)
    }
  }

  const buildImprovementPlan = async () => {
    setImprovementLoading(true)
    setImprovementError('')
    try {
      const response = await fetch(`${API_BASE}/api/improvement`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resume, job_description: job, use_semantic: true }),
      })
      if (!response.ok) throw new Error('Could not build the improvement plan.')
      setImprovement(await response.json())
    } catch (requestError) {
      setImprovementError(requestError instanceof Error ? requestError.message : 'Could not build the improvement plan.')
    } finally {
      setImprovementLoading(false)
    }
  }

  const prepareInterview = async () => {
    setInterviewLoading(true)
    setInterviewError('')
    try {
      const response = await fetch(`${API_BASE}/api/interview/questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resume, job_description: job, use_semantic: true, questions_per_category: 2 }),
      })
      if (!response.ok) throw new Error('Could not prepare interview questions.')
      const result = await response.json()
      setInterviewQuestions(result.questions)
      setSelectedQuestion(result.questions[0] ?? null)
      setInterviewEvaluation(null)
    } catch (requestError) {
      setInterviewError(requestError instanceof Error ? requestError.message : 'Could not prepare interview questions.')
    } finally {
      setInterviewLoading(false)
    }
  }

  const startMockInterview = async () => {
    setInterviewLoading(true)
    setSessionError('')
    try {
      const response = await fetch(`${API_BASE}/api/interview/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resume, job_description: job, questions_per_category: 2 }),
      })
      if (!response.ok) throw new Error('Could not start the mock interview.')
      const created = await response.json()
      const result: InterviewSession = {
        ...created,
        answers: [],
        progress_percent: 0,
      }
      setInterviewSession(result)
      setSessionQuestion(result.questions[0] ?? null)
      setSessionAnswer('')
    } catch (requestError) {
      setSessionError(requestError instanceof Error ? requestError.message : 'Could not start the mock interview.')
    } finally {
      setInterviewLoading(false)
    }
  }

  const submitSessionAnswer = async () => {
    if (!interviewSession || !sessionQuestion || !sessionAnswer.trim()) return
    setInterviewLoading(true)
    setSessionError('')
    try {
      const response = await fetch(`${API_BASE}/api/interview/sessions/${interviewSession.session_id}/answers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: sessionQuestion.id, answer: sessionAnswer }),
      })
      if (response.status === 409) throw new Error('This question already has an answer.')
      if (!response.ok) throw new Error('Could not submit this session answer.')
      const updated = await fetch(`${API_BASE}/api/interview/sessions/${interviewSession.session_id}`)
      if (!updated.ok) throw new Error('Could not refresh the mock interview session.')
      const result: InterviewSession = await updated.json()
      setInterviewSession(result)
      setSessionAnswer('')
      setSessionQuestion(result.questions.find((question) => !result.answers.some((answer) => answer.question_id === question.id)) ?? null)
    } catch (requestError) {
      setSessionError(requestError instanceof Error ? requestError.message : 'Could not submit this session answer.')
    } finally {
      setInterviewLoading(false)
    }
  }

  const completeMockInterview = async () => {
    if (!interviewSession) return
    setInterviewLoading(true)
    setSessionError('')
    try {
      const response = await fetch(`${API_BASE}/api/interview/sessions/${interviewSession.session_id}/complete`, { method: 'POST' })
      if (!response.ok) throw new Error('Could not complete the mock interview.')
      setInterviewSession(await response.json())
      setSessionQuestion(null)
    } catch (requestError) {
      setSessionError(requestError instanceof Error ? requestError.message : 'Could not complete the mock interview.')
    } finally {
      setInterviewLoading(false)
    }
  }

  const evaluateAnswer = async () => {
    if (!selectedQuestion || !answer.trim()) return
    setEvaluationLoading(true)
    setInterviewError('')
    try {
      const response = await fetch(`${API_BASE}/api/interview/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: selectedQuestion, answer }),
      })
      if (!response.ok) throw new Error('Could not evaluate this answer.')
      setInterviewEvaluation(await response.json())
    } catch (requestError) {
      setInterviewError(requestError instanceof Error ? requestError.message : 'Could not evaluate this answer.')
    } finally {
      setEvaluationLoading(false)
    }
  }

  const explainGap = async (skill: string) => {
    setAdvisorLoading(true)
    setAdvisorError('')
    try {
      const response = await fetch(`${API_BASE}/api/advisor/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill, candidate_context: resume.slice(0, 4000) }),
      })
      if (!response.ok) throw new Error(response.status === 503 || response.status === 504 ? 'AI advisor is unavailable right now.' : 'Could not generate advice.')
      setAdvisor(await response.json())
    } catch (requestError) {
      setAdvisorError(requestError instanceof Error ? requestError.message : 'Could not generate advice.')
    } finally {
      setAdvisorLoading(false)
    }
  }

  const fillDemo = () => {
    setResume(demoResume)
    setJob(demoJob)
    setMatch(null)
    setReadiness(null)
    setRoadmap(null)
    setOptimization(null)
    setError('')
    setRoadmapError('')
    setOptimizationError('')
    setInterviewSession(null)
    setSessionQuestion(null)
    setSessionAnswer('')
    setSessionError('')
  }

  return (
    <main className="app-shell">
      <nav className="topbar">
        <a className="brand" href="/" aria-label="AI Career Intelligence home"><span className="brand-mark">AI</span><span>Career Intelligence</span></a>
        <div className="topbar-status"><span className="status-dot" /> Local analysis workspace</div>
      </nav>

      <header className="hero">
        <p className="eyebrow">Career fit, made legible</p>
        <h1>See where your experience meets the role.</h1>
        <p className="hero-copy">Compare a resume with a job description, uncover the gaps that matter, and turn them into a focused next step.</p>
      </header>

      <section className="input-grid" aria-label="Match inputs">
        <div className="input-panel">
          <div className="panel-heading"><span className="panel-index">01</span><div><h2>Your resume</h2><p>Paste the text of your resume to build a candidate profile.</p></div></div>
          <textarea value={resume} onChange={(event) => setResume(event.target.value)} placeholder="Paste resume text here..." aria-label="Resume text" />
          <span className="character-count">{resume.length} characters</span>
        </div>
        <div className="input-panel accent-panel">
          <div className="panel-heading"><span className="panel-index">02</span><div><h2>Target role</h2><p>Give the analyzer the full job description.</p></div></div>
          <textarea value={job} onChange={(event) => setJob(event.target.value)} placeholder="Paste job description here..." aria-label="Job description" />
          <span className="character-count">{job.length} characters</span>
        </div>
      </section>

      <div className="action-row"><button className="text-button" type="button" onClick={fillDemo}>Load example</button><button className="primary-button" type="button" onClick={runMatch} disabled={loading}>{loading ? 'Analyzing...' : 'Analyze fit'} <span aria-hidden="true">-&gt;</span></button></div>
      {error && <p className="error-message" role="alert">{error}</p>}

      {match && <section className="results" aria-live="polite">
        <div className="results-header"><div><p className="eyebrow">Analysis complete</p><h2>Your match profile</h2></div><span className="result-note">Semantic analysis enabled</span></div>
        <div className="score-layout">
          <div className="score-card"><div className="score-ring" style={{ '--score': `${match.overall_match * 3.6}deg` } as React.CSSProperties}><strong>{Math.round(match.overall_match)}<small>%</small></strong></div><p>Overall match</p><span>Based on skills, relevance, and context</span></div>
          <div className="signal-grid"><Signal label="Skills match" value={match.skills_match} /><Signal label="Project relevance" value={match.project_relevance} /><Signal label="Experience relevance" value={match.experience_relevance} /><Signal label="Education match" value={match.education_match} /></div>
        </div>
        {readiness && <section className="readiness-panel" aria-label="Job readiness">
          <div className="readiness-heading"><div><p className="eyebrow">V3.1 readiness</p><h3>How prepared are you for this role?</h3><p className="readiness-note">Resume evidence only, not a hiring-probability estimate.</p></div><strong className="readiness-score">{Math.round(readiness.readiness_score)}<small>%</small></strong></div>
          <div className="readiness-components"><Signal label="Required skills" value={readiness.required_skill_coverage} /><Signal label="Experience evidence" value={readiness.experience_evidence} /><Signal label="Project evidence" value={readiness.project_evidence} /></div>
          <div className="readiness-bottom"><div><p className="readiness-label">What shaped the score</p>{readiness.reasons.map((reason) => <p className="readiness-reason" key={reason}>{reason}</p>)}</div><div><p className="readiness-label">Readiness blockers</p>{readiness.blockers.length ? <ul className="blocker-list">{readiness.blockers.map((blocker) => <li key={blocker.skill}><strong>{blocker.skill}</strong><span>{blocker.status} - {blocker.reason}</span></li>)}</ul> : <p className="readiness-reason">No required-skill blockers identified.</p>}</div></div>
        </section>}
        <section className="roadmap-panel" aria-label="Personalized learning roadmap">
          <div className="results-header"><div><p className="eyebrow">V3.2 roadmap</p><h3>Turn priority gaps into a learning sequence</h3></div><button className="text-button" type="button" onClick={buildRoadmap} disabled={roadmapLoading || !match.recommended_priority}>{roadmapLoading ? 'Building...' : 'Build roadmap -&gt;'}</button></div>
          {roadmapError && <p className="advisor-error" role="alert">{roadmapError}</p>}
          {roadmap && <><p className="grounding-policy">{roadmap.grounding_policy}</p><div className="roadmap-list">{roadmap.items.map((item) => <article className="roadmap-item" key={`${item.order}-${item.skill}`}><div className="roadmap-meta"><span>{item.horizon}</span><b>{item.priority}</b></div><h4>{item.skill}</h4><p>{item.reason}</p>{item.resource ? <div className="roadmap-resource"><strong>{item.resource.title}</strong><span>{item.resource.level} · {item.resource.source}</span><p>{item.resource.summary}</p><a href={item.resource.url} target="_blank" rel="noreferrer">Open resource <span aria-hidden="true">-&gt;</span></a></div> : <p className="advisor-muted">{item.grounding_note}</p>}</article>)}</div>{roadmap.items.length === 0 && <p className="advisor-muted">No prioritized gaps were identified for a roadmap.</p>}</>}
          {!roadmap && !roadmapError && <p className="advisor-muted">Build a grounded 30, 60, and 90-day sequence from the prioritized gaps above.</p>}
        </section>
        <section className="optimization-panel" aria-label="Resume optimization suggestions">
          <div className="results-header"><div><p className="eyebrow">V3.3 review mode</p><h3>Shape a role-specific resume version</h3></div><button className="text-button" type="button" onClick={buildOptimizationSuggestions} disabled={optimizationLoading}>{optimizationLoading ? 'Reviewing...' : 'Review suggestions -&gt;'}</button></div>
          {optimizationError && <p className="advisor-error" role="alert">{optimizationError}</p>}
          {optimization && <><p className="grounding-policy">{optimization.grounding_policy}</p><div className="optimization-list">{optimization.suggestions.map((suggestion) => <article className="optimization-item" key={suggestion.id}><div className="optimization-meta"><span>{suggestion.section} · {suggestion.operation}</span><b className={`optimization-status ${suggestion.status}`}>{suggestion.status}</b></div>{suggestion.original_text && <div className="optimization-copy"><small>Existing text</small><p>{suggestion.original_text}</p></div>}<div className="optimization-copy proposed"><small>{suggestion.original_text ? 'Proposed text' : 'Review action'}</small><p>{suggestion.proposed_text}</p></div>{suggestion.evidence.length > 0 && <div className="optimization-evidence"><small>Evidence</small>{suggestion.evidence.map((evidence) => <p key={`${suggestion.id}-${evidence.source_text}`}>{evidence.source_text} <span>({evidence.support})</span></p>)}</div>}<small className="optimization-note">{suggestion.grounding_note}</small></article>)}</div>{optimization.suggestions.length === 0 && <p className="advisor-muted">No deterministic suggestions were found.</p>}</>}
          {!optimization && !optimizationError && <p className="advisor-muted">Review fact-preserving wording and evidence alignment before creating a tailored version. Nothing is changed automatically.</p>}
        </section>
        <div className="detail-grid"><SkillColumn title="Strong signals" skills={match.strong_skills} tone="strong" /><SkillColumn title="Build confidence" skills={match.partial_skills} tone="partial" /><SkillColumn title="Priority gaps" skills={match.missing_skills} tone="missing" onSkillClick={explainGap} /></div>
        <div className="advisor-panel"><div className="advisor-heading"><span className="advisor-icon">+</span><div><p className="eyebrow">Next move</p><h3>Turn a gap into momentum</h3></div></div>{advisorLoading && <p className="advisor-muted">Advisor is reading the role and your background...</p>}{!advisorLoading && advisorError && <p className="advisor-error" role="alert">{advisorError}</p>}{!advisorLoading && !advisorError && !advisor && <p className="advisor-muted">Select a priority gap above to get a grounded learning plan from your local advisor.</p>}{advisor && <div className="advisor-copy"><p>{advisor.explanation}</p>{advisor.resource && <a href={advisor.resource.url} target="_blank" rel="noreferrer">Open {advisor.resource.title} <span aria-hidden="true">-&gt;</span></a>}</div>}</div>
          <div className="improvement-panel"><div className="results-header"><div><p className="eyebrow">V2 workflow</p><h3>Improve this application</h3></div><button className="text-button" type="button" onClick={buildImprovementPlan} disabled={improvementLoading}>{improvementLoading ? 'Building...' : 'Build plan -&gt;'}</button></div>{improvementError && <p className="advisor-error" role="alert">{improvementError}</p>}{improvement && <><p className="grounding-policy">{improvement.grounding_policy}</p><div className="suggestion-list">{improvement.suggestions.map((suggestion, index) => <article className="suggestion" key={`${suggestion.title}-${index}`}><div className="suggestion-meta"><span>{suggestion.category}</span><b>{suggestion.priority}</b></div><h4>{suggestion.title}</h4><p>{suggestion.action}</p>{suggestion.evidence.length > 0 && <small>Evidence: {suggestion.evidence.join(', ')}</small>}</article>)}</div></>}{!improvement && !improvementError && <p className="advisor-muted">Generate specific, fact-checked resume changes from this analysis.</p>}</div>
        <div className="session-panel"><div className="results-header"><div><p className="eyebrow">V3.4 mock interview</p><h3>Practice a complete interview session</h3></div>{!interviewSession && <button className="text-button" type="button" onClick={startMockInterview} disabled={interviewLoading}>{interviewLoading ? 'Starting...' : 'Start session -&gt;'}</button>}</div>{sessionError && <p className="advisor-error" role="alert">{sessionError}</p>}{interviewSession && <><div className="session-progress"><span>{interviewSession.status === 'completed' ? 'Session complete' : `${interviewSession.answers.length} of ${interviewSession.questions.length} answered`}</span><strong>{Math.round(interviewSession.progress_percent)}%</strong><div className="meter"><i style={{ width: `${interviewSession.progress_percent}%` }} /></div></div>{sessionQuestion && interviewSession.status !== 'completed' && <div className="answer-area"><p className="coach-question">{sessionQuestion.question}</p><textarea value={sessionAnswer} onChange={(event) => setSessionAnswer(event.target.value)} placeholder="Write your answer..." aria-label="Session answer" /><button className="primary-button" type="button" onClick={submitSessionAnswer} disabled={interviewLoading || !sessionAnswer.trim()}>{interviewLoading ? 'Submitting...' : 'Submit answer -&gt;'}</button></div>}{interviewSession.status !== 'completed' && !sessionQuestion && <button className="primary-button" type="button" onClick={completeMockInterview} disabled={interviewLoading}>{interviewLoading ? 'Completing...' : 'Complete session -&gt;'}</button>}{interviewSession.summary && <div className="evaluation"><strong>{interviewSession.summary.overall_structure_coverage}% structure and coverage summary</strong><p>Completion status: {interviewSession.summary.completion_status}. This feedback measures answer structure and evidence coverage, not factual correctness or hiring probability.</p>{interviewSession.summary.recurring_feedback_themes.map((theme) => <p className="evaluation-improvement" key={theme}>{theme}</p>)}</div>}</>}</div>
        <div className="coach-panel"><div className="results-header"><div><p className="eyebrow">V2 Step 2</p><h3>Practice for the interview</h3></div><button className="text-button" type="button" onClick={prepareInterview} disabled={interviewLoading}>{interviewLoading ? 'Preparing...' : 'Prepare questions -&gt;'}</button></div>{interviewError && <p className="advisor-error" role="alert">{interviewError}</p>}{interviewQuestions.length > 0 && <><div className="question-list">{interviewQuestions.map((question) => <button className={`question-item ${selectedQuestion?.id === question.id ? 'selected' : ''}`} type="button" key={question.id} onClick={() => { setSelectedQuestion(question); setInterviewEvaluation(null) }}><span>{question.category}</span>{question.question}</button>)}</div>{selectedQuestion && <div className="answer-area"><p className="coach-question">{selectedQuestion.question}</p><textarea value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="Write your answer..." aria-label="Interview answer" /><button className="primary-button" type="button" onClick={evaluateAnswer} disabled={evaluationLoading || !answer.trim()}>{evaluationLoading ? 'Evaluating...' : 'Evaluate answer -&gt;'}</button></div>}{interviewEvaluation && <div className="evaluation"><strong>{interviewEvaluation.score}% structure score</strong><p>{interviewEvaluation.feedback}</p>{interviewEvaluation.strengths.map((strength) => <p className="evaluation-positive" key={strength}>{strength}</p>)}{interviewEvaluation.improvements.map((improvementItem) => <p className="evaluation-improvement" key={improvementItem}>{improvementItem}</p>)}</div>}</>}{!interviewQuestions.length && !interviewError && <p className="advisor-muted">Generate grounded technical, resume-specific, behavioral, and gap questions.</p>}</div>
      </section>}
      <footer><span>AI Career Intelligence</span><span>Private by default. Powered locally.</span></footer>
    </main>
  )
}

function Signal({ label, value }: { label: string; value: number }) {
  return <div className="signal"><div><span>{label}</span><strong>{Math.round(value)}%</strong></div><div className="meter"><i style={{ width: `${Math.min(value, 100)}%` }} /></div></div>
}

function SkillColumn({ title, skills, tone, onSkillClick }: { title: string; skills: string[]; tone: string; onSkillClick?: (skill: string) => void }) {
  return <div className={`skill-column ${tone}`}><div className="column-title"><span>{title}</span><b>{skills.length}</b></div>{skills.length ? <ul>{skills.map((skill) => <li key={skill}>{onSkillClick ? <button type="button" onClick={() => onSkillClick(skill)}>{skill}<span aria-hidden="true">-&gt;</span></button> : skill}</li>)}</ul> : <p className="empty-list">Nothing here yet.</p>}</div>
}

export default App
