from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.job import router as job_router
from backend.app.api.knowledge import router as knowledge_router
from backend.app.api.match import router as match_router
from backend.app.api.resume import router as resume_router
from backend.app.api.advisor import router as advisor_router
from backend.app.api.improvement import router as improvement_router
from backend.app.api.interview import router as interview_router
from backend.app.api.readiness import router as readiness_router
from backend.app.config import settings

app = FastAPI(
    title=settings.app_name,
    description="AI Career Intelligence — resume parsing, job matching, RAG, and agents",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router, prefix="/api")
app.include_router(job_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(match_router, prefix="/api")
app.include_router(advisor_router, prefix="/api")
app.include_router(improvement_router, prefix="/api")
app.include_router(interview_router, prefix="/api")
app.include_router(readiness_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": "0.3.0",
        "phase": "3 — ML Job Matching Engine (+ Phase 1 & 2)",
        "endpoints": {
            "health": "/health",
            "parse_pdf": "POST /api/resume/parse",
            "parse_text": "POST /api/resume/parse-text",
            "analyze_job": "POST /api/job/analyze",
            "knowledge_search": "POST /api/knowledge/search",
            "match_skills": "POST /api/match/skills",
            "match": "POST /api/match",
            "match_from_text": "POST /api/match/from-text",
            "advisor_explain": "POST /api/advisor/explain",
            "improvement": "POST /api/improvement",
            "interview_questions": "POST /api/interview/questions",
            "interview_evaluate": "POST /api/interview/evaluate",
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
