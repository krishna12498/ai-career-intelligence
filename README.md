# AI Career Intelligence Platform

An AI/ML job-search and career intelligence system: resume parsing, job matching, RAG knowledge base, multi-agent interview prep, and evaluation.

**Phase 3 (current):** ML Job Matching Engine (semantic skill matching + full match report)

## Tech stack (free-first)

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| PDF | PyMuPDF |
| ML | scikit-learn, sentence-transformers |
| RAG | LangChain, FAISS |
| Agents | LangGraph |
| Frontend | React (Phase 6) |
| DB | PostgreSQL / Supabase (Phase 6) |
| LLM | Ollama (local, free) |

## Project structure

```
AI-Career-Intelligence/
├── backend/app/          # FastAPI application
│   ├── api/              # Route handlers
│   ├── models/           # Pydantic schemas
│   ├── services/         # Business logic
│   └── data/             # Skills DB, constants
├── agents/               # Multi-agent system (Phase 5)
├── ml/                   # Embeddings + semantic skill detection
├── rag/                  # RAG pipeline (Phase 4)
├── frontend/             # React dashboard (Phase 6)
├── tests/
└── data/uploads/         # Uploaded resumes
```

## Quick start

### 1. Install dependencies

```bash
cd "k:\Ai job"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the API

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs for the interactive API.

### 3. Parse a resume (PDF)

```bash
curl -X POST "http://localhost:8000/api/resume/parse" -F "file=@your_resume.pdf"
```

### 4. Parse resume text (for testing)

```bash
curl -X POST "http://localhost:8000/api/resume/parse-text" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"John Doe ... Python FastAPI ...\"}"
```

### 5. Analyze a job description

```bash
curl -X POST "http://localhost:8000/api/job/analyze" ^
  -H "Content-Type: application/json" ^
  -d "{\"description\": \"We are looking for a Junior AI Engineer. Required: Python, FastAPI, Docker. Preferred: LangChain, RAG.\"}"
```

Set `use_semantic: false` in the JSON body to skip embedding-based skill detection (faster, keyword-only).

### 6. Run tests

```bash
pytest tests/ -v
```

## Phase roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Resume PDF parser + structured extraction | ✅ |
| 2 | Job description analyzer (keyword + semantic) | ✅ |
| 3 | ML semantic matching | 🔜 |
| 4 | RAG career knowledge base | 🔜 |
| 5 | Multi-agent system (LangGraph) | 🔜 |
| 6 | React dashboard | 🔜 |
| 7 | Evaluation & observability | 🔜 |
| 8 | Docker + deployment | 🔜 |

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/resume/parse` | Upload PDF → structured JSON |
| POST | `/api/resume/parse-text` | Paste text → structured JSON |
| POST | `/api/job/analyze` | Analyze JD → structured requirements |

## License

MIT
