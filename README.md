# AI Recruitment & Candidate Screening System

An API-first recruitment screening MVP that extracts job-relevant resume evidence, compares it with a job description, ranks candidates transparently, and leaves shortlist decisions with the recruiter.

## Start locally

1. Activate the Conda environment you already created: `conda activate aiproject`.
2. Use Python 3.11 or newer in that environment: `python --version`.
3. Install the project dependencies: `python -m pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and adjust settings if needed: `copy .env.example .env` (Anaconda Prompt on Windows).
5. Start the API: `uvicorn app.main:app --reload`.
6. Open `http://127.0.0.1:8000/docs` for the interactive REST API or `http://127.0.0.1:8000/health` for the health check.

The initial increment includes the API foundation and SQLAlchemy database schema. Resume processing, AI analysis, and the recruiter dashboard will arrive in the roadmap sequence.

## Current API routes

The API is available under `/api/v1`; the interactive Swagger page at `/docs` lists request fields and response schemas.

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/api/v1/jobs` | Create a job |
| `GET` | `/api/v1/jobs` | List jobs |
| `GET` | `/api/v1/jobs/{job_id}` | Get a job |
| `POST` | `/api/v1/candidates` | Create a candidate profile |
| `GET` | `/api/v1/candidates` | List candidate profiles |
| `GET` | `/api/v1/candidates/{candidate_id}` | Get a candidate profile |
| `POST` | `/api/v1/applications` | Link a candidate to a job |
| `GET` | `/api/v1/applications` | List applications; optionally filter with `?job_id=...` |
| `POST` | `/api/v1/jobs/{job_id}/applications/upload` | Upload a PDF/DOCX resume, extract text, and create the candidate application |

Resume upload accepts files up to 10 MB and 50 PDF pages. The original file is not saved; extracted text and the supplied filename are kept with the candidate profile for screening. Scanned image-only PDFs are not supported until OCR is added.

## Database

SQLAlchemy supports both databases through the same models. The local quick start uses SQLite, so you can run the project without a separate database service. PostgreSQL is supported through `DATABASE_URL` and is the intended deployment database. To use PostgreSQL locally, set a connection string such as `postgresql+psycopg://USER:PASSWORD@localhost:5432/ai_recruitment` in `.env` and make sure the PostgreSQL server and database are available.

## Project layout

```text
app/
  api/          HTTP routes
  db/           SQLAlchemy base, connection, and sessions
  models/       Jobs, candidates, applications, screening, and decisions
  main.py       FastAPI application
  settings.py   Environment-based configuration
ROADMAP.md      15-day plan and progress log
```

## Configuration

Copy `.env.example` to `.env` for local settings. Keep credentials in `.env` or deployment secrets; never commit secrets or real candidate files.

## Responsible use

This tool supports initial screening. It must present job-related evidence and uncertainty, and a recruiter must make every hiring decision. Do not use protected characteristics to score or rank candidates.
