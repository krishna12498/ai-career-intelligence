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

function App() {
  const [resume, setResume] = useState('')
  const [job, setJob] = useState('')
  const [match, setMatch] = useState<MatchResult | null>(null)
  const [advisor, setAdvisor] = useState<AdvisorResult | null>(null)
  const [improvement, setImprovement] = useState<ImprovementResult | null>(null)
  const [interviewQuestions, setInterviewQuestions] = useState<InterviewQuestion[]>([])
  const [selectedQuestion, setSelectedQuestion] = useState<InterviewQuestion | null>(null)
  const [interviewEvaluation, setInterviewEvaluation] = useState<InterviewEvaluation | null>(null)
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [advisorLoading, setAdvisorLoading] = useState(false)
  const [improvementLoading, setImprovementLoading] = useState(false)
  const [interviewLoading, setInterviewLoading] = useState(false)
  const [evaluationLoading, setEvaluationLoading] = useState(false)
  const [error, setError] = useState('')
  const [advisorError, setAdvisorError] = useState('')
  const [improvementError, setImprovementError] = useState('')
  const [interviewError, setInterviewError] = useState('')

  const runMatch = async () => {
    if (resume.trim().length < 50 || job.trim().length < 30) {
      setError('Add a resume of at least 50 characters and a job description of at least 30 characters.')
      return
    }
    setLoading(true)
    setError('')
    setAdvisor(null)
    setAdvisorError('')
    setImprovement(null)
    setImprovementError('')
    setInterviewQuestions([])
    setSelectedQuestion(null)
    setInterviewEvaluation(null)
    setAnswer('')
    setInterviewError('')
    try {
      const response = await fetch(`${API_BASE}/api/match/from-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: resume, job_description: job, use_semantic: true }),
      })
      if (!response.ok) throw new Error('The matching service could not process these inputs.')
      setMatch(await response.json())
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Something went wrong.')
    } finally {
      setLoading(false)
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
    setError('')
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
        <div className="detail-grid"><SkillColumn title="Strong signals" skills={match.strong_skills} tone="strong" /><SkillColumn title="Build confidence" skills={match.partial_skills} tone="partial" /><SkillColumn title="Priority gaps" skills={match.missing_skills} tone="missing" onSkillClick={explainGap} /></div>
        <div className="advisor-panel"><div className="advisor-heading"><span className="advisor-icon">+</span><div><p className="eyebrow">Next move</p><h3>Turn a gap into momentum</h3></div></div>{advisorLoading && <p className="advisor-muted">Advisor is reading the role and your background...</p>}{!advisorLoading && advisorError && <p className="advisor-error" role="alert">{advisorError}</p>}{!advisorLoading && !advisorError && !advisor && <p className="advisor-muted">Select a priority gap above to get a grounded learning plan from your local advisor.</p>}{advisor && <div className="advisor-copy"><p>{advisor.explanation}</p>{advisor.resource && <a href={advisor.resource.url} target="_blank" rel="noreferrer">Open {advisor.resource.title} <span aria-hidden="true">-&gt;</span></a>}</div>}</div>
          <div className="improvement-panel"><div className="results-header"><div><p className="eyebrow">V2 workflow</p><h3>Improve this application</h3></div><button className="text-button" type="button" onClick={buildImprovementPlan} disabled={improvementLoading}>{improvementLoading ? 'Building...' : 'Build plan -&gt;'}</button></div>{improvementError && <p className="advisor-error" role="alert">{improvementError}</p>}{improvement && <><p className="grounding-policy">{improvement.grounding_policy}</p><div className="suggestion-list">{improvement.suggestions.map((suggestion, index) => <article className="suggestion" key={`${suggestion.title}-${index}`}><div className="suggestion-meta"><span>{suggestion.category}</span><b>{suggestion.priority}</b></div><h4>{suggestion.title}</h4><p>{suggestion.action}</p>{suggestion.evidence.length > 0 && <small>Evidence: {suggestion.evidence.join(', ')}</small>}</article>)}</div></>}{!improvement && !improvementError && <p className="advisor-muted">Generate specific, fact-checked resume changes from this analysis.</p>}</div>
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
