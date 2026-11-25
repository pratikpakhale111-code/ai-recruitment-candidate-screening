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
