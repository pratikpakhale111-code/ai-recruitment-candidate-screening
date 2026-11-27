# AI Recruitment & Candidate Screening System

## 15-day MVP roadmap

**Schedule:** November 25–December 9, 2026. Day 1 is today; each day ends with a usable, reviewable increment.

**MVP outcome:** A recruiter can create a job, upload candidate resumes, review extracted job-relevant evidence, compare candidates using a transparent score, and make a human-controlled shortlist decision in a web dashboard.

| Day | Focus | Deliverable |
|---|---|---|
| 1 · Nov 25 | Scope and project foundation | Working FastAPI project, configuration template, setup guide, and this roadmap |
| 2 · Nov 26 | Data model and persistence | Jobs, candidates, applications, screening runs/results, and recruiter decisions stored through SQLAlchemy; REST routes for creating and listing jobs, candidates, and applications |
| 3 · Nov 27 | Resume intake | Validated PDF/DOCX upload, safe file handling, and text extraction |
| 4 · Nov 28 | Job description analysis | Job form/API and structured must-have skills, preferred skills, and experience expectations, with source snippets |
| 5 · Nov 29 | Candidate profile extraction | Normalized skill mentions and experience with supporting text snippets; later replace/augment the baseline with LLM extraction |
| 6 · Nov 30 | Explainable scoring | Versioned rubric with criterion-level matches, gaps, scores, and evidence; unknown experience is not treated as zero |
| 7 · Dec 1 | Ranking and agent workflow | LangGraph nodes for job analysis, candidate evidence, deterministic scoring, and explanations; OpenRouter free-model calls when configured and a visible fallback when unavailable |
| 8 · Dec 2 | Knowledge retrieval | Resume evidence retrieval for each criterion using a vector store; citations point back to candidate text |
| 9 · Dec 3 | AI explanations | Improve grounded summaries of strengths, gaps, and uncertainty, with source quote validation and a deterministic fallback |
| 10 · Dec 4 | Recruiter dashboard | Create a job, add candidates, see ranked results, and open evidence-backed candidate details |
| 11 · Dec 5 | Shortlisting workflow | Recruiter-controlled advance/reject/hold decisions, notes, and a basic decision history |
| 12 · Dec 6 | Reliability and API handoff | Clear validation/errors, privacy-minded logging, API examples, and a Postman collection |
| 13 · Dec 7 | Cache and deployment setup | Redis used for a bounded, useful cache; production settings and PaaS deployment configuration |
| 14 · Dec 8 | Release candidate | Deployed app, sample job/candidates, usable public URL, and setup/deployment documentation |
| 15 · Dec 9 | Submission package | Final walkthrough, GitHub repository cleanup, project showcase material, and LinkedIn final post |

## Working principles

- Keep a recruiter in control. The system recommends and explains; it does not make or execute hiring decisions.
- Score only job-relevant criteria. Do not infer protected traits or use them in ranking.
- Show evidence and uncertainty next to every recommendation so a recruiter can inspect the source.
- Keep an API-first design. The dashboard calls the same REST API that can be explored through Swagger and Postman.
- Make external AI services optional during development. Never commit API keys or candidate resumes.
- Commit each finished increment with a clear message. Share progress posts around Days 1, 3, 7, 10, and 15.

## Initial scope choices

- **Backend:** Python + FastAPI REST API.
- **Data:** SQLAlchemy with SQLite for the local quick start and PostgreSQL for deployment.
- **Dashboard:** A small web UI served by the application to keep the 15-day delivery manageable.
- **Agent workflow:** LangGraph for explicit screening steps, added after the core data flow exists.
- **Retrieval:** A vector store for finding evidence in resume text; choose the smallest deployment-friendly option during implementation.
- **Cache/state:** Redis for a concrete cache or background state use, not as a requirement for local startup.

## Risks to manage

- Resume files contain sensitive personal information. Store only what the MVP needs, restrict file types and size, avoid logging resume text, and document deletion behavior.
- LLM extraction can miss or misread evidence. Preserve source snippets, mark uncertainty, and let recruiters correct or disregard recommendations.
- A 15-day schedule is tight. Prioritize the end-to-end upload → evidence → score → dashboard → human decision path; treat advanced multi-agent behavior as an extension after that path works.

## Daily progress log

| Date | Progress | Next |
|---|---|---|
| Nov 26 | Explainable weighted scoring and ranked screening runs added; LangGraph job, candidate, scoring, and explanation nodes wired with OpenAI structured outputs and a visible baseline fallback | Configure a no-cost model provider, then improve RAG evidence retrieval |
| Nov 27 | Configured OpenRouter and `openai/gpt-oss-120b:free`; added a guard that prevents the workflow from using a different, potentially paid model ID | Restart the API and try screening with the free model, then improve RAG evidence retrieval |
