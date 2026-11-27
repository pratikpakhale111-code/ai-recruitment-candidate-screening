# AI Recruitment & Candidate Screening System

An API-first recruitment screening MVP that extracts job-relevant resume evidence, compares it with a job description, ranks candidates transparently, and leaves shortlist decisions with the recruiter.

## Start locally

1. Activate the Conda environment you already created: `conda activate aiproject`.
2. Use Python 3.11 or newer in that environment: `python --version`.
3. Install the project dependencies: `python -m pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and adjust settings if needed: `copy .env.example .env` (Anaconda Prompt on Windows).
5. Start the API: `uvicorn app.main:app --reload`.
6. Open `http://127.0.0.1:8000/docs` for the interactive REST API or `http://127.0.0.1:8000/health` for the health check.

The API foundation, SQLAlchemy schema, resume intake, profile analysis, and explainable ranking are implemented. The screening endpoint now runs a LangGraph workflow; it calls OpenAI's open-weight gpt-oss-120b through OpenRouter's free endpoint when configured and reports when it uses the keyword fallback.

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
| `POST` | `/api/v1/jobs/{job_id}/analyze` | Extract job skills and experience requirements with source evidence |
| `POST` | `/api/v1/candidates/{candidate_id}/analyze` | Extract candidate skill and experience mentions with source evidence |
| `POST` | `/api/v1/jobs/{job_id}/screen` | Score and rank active applications for a job |
| `GET` | `/api/v1/screening-runs/{run_id}` | Retrieve a saved screening run and its evidence |

Resume upload accepts files up to 10 MB and 50 PDF pages. The original file is not saved; extracted text and the supplied filename are kept with the candidate profile for screening. Scanned image-only PDFs are not supported until OCR is added.

The current profile analyzer uses a small exact-keyword skill catalog and evidence snippets. It does not yet understand synonyms beyond listed aliases or judge skill proficiency; review its extracted matches before using them in a screening decision.

Screening scores use a 60% required-skills, 20% preferred-skills, and 20% experience rubric. The weights are normalized across criteria with available data. Unknown experience is excluded from the calculation and shown as unknown, rather than treated as zero. Results include criterion-level matches, gaps, source snippets, and a recruiter-review notice; the score is decision support, not an automated hiring decision.

## LLM and agent workflow

`app/agents/screening_workflow.py` defines the LangGraph workflow with job-requirement, candidate-evidence, scoring, and explanation nodes. `app/agents/schemas.py` defines the structured outputs. The graph runs from `POST /api/v1/jobs/{job_id}/screen` and stores its analysis mode with the screening run.

The workflow uses OpenRouter's OpenAI-compatible API with the exact free model ID below. Put your OpenRouter API key in your local `.env` file; do not paste it into source code or commit it:

```text
LLM_PROVIDER=openrouter
LLM_API_KEY=your-openrouter-key
LLM_MODEL=openai/gpt-oss-120b:free
```

Restart the API after changing settings. With no API key, the LangGraph workflow still runs but uses the keyword baseline; the response reports `analysis_mode: "keyword_baseline"` and `llm_status: "api_key_missing"`. The app rejects any model setting other than `openai/gpt-oss-120b:free`, avoiding accidental use of a paid model. OpenRouter currently lists this free variant at $0, with limits of 20 requests per minute and 50 per day; availability and provider limits can change. Do not buy credits for this setup. LLM calls send the job description and resume text to OpenRouter, so only send candidate data when authorized. The workflow validates extracted quotes against the source text, and the recruiter remains responsible for decisions. See [OpenRouter's free model details and limits](https://openrouter.ai/collections/free-models/), the [gpt-oss-120b free model page](https://openrouter.ai/openai/gpt-oss-120b:free), the [OpenRouter API quickstart](https://openrouter.ai/docs/quickstart), the [LangGraph quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart), and [ChatOpenAI integration docs](https://docs.langchain.com/oss/python/integrations/chat/openai).

## Database

SQLAlchemy supports both databases through the same models. The local quick start uses SQLite, so you can run the project without a separate database service. PostgreSQL is supported through `DATABASE_URL` and is the intended deployment database. To use PostgreSQL locally, set a connection string such as `postgresql+psycopg://USER:PASSWORD@localhost:5432/ai_recruitment` in `.env` and make sure the PostgreSQL server and database are available.

## Project layout

```text
app/
  agents/       LangGraph workflow and structured LLM output schemas
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
