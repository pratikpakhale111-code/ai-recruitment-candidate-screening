from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.agents.screening_workflow import get_screening_workflow, initial_screening_state
from app.db.session import get_db
from app.models import Application, Job, ScreeningResult, ScreeningRun
from app.services.scoring import BASE_WEIGHTS

router = APIRouter(tags=["screening"])


class ScreeningCandidateRead(BaseModel):
    application_id: int
    candidate_id: int
    candidate_name: str
    rank: int | None
    suitability_score: float | None
    category_scores: dict[str, float | None]
    matches: list[dict[str, Any]]
    gaps: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    explanation: str


class ScreeningRunRead(BaseModel):
    id: int
    job_id: int
    status: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    weights: dict[str, float]
    analysis_mode: str
    llm_status: str
    results: list[ScreeningCandidateRead]
    notice: str = "Screening scores support recruiter review; they do not make hiring decisions."


def _run_response(db: Session, run: ScreeningRun) -> ScreeningRunRead:
    results = db.scalars(
        select(ScreeningResult)
        .where(ScreeningResult.screening_run_id == run.id)
        .options(joinedload(ScreeningResult.application).joinedload(Application.candidate))
        .order_by(ScreeningResult.rank.is_(None), ScreeningResult.rank, ScreeningResult.id)
    ).all()
    response_results = [
        ScreeningCandidateRead(
            application_id=result.application_id,
            candidate_id=result.application.candidate_id,
            candidate_name=result.application.candidate.full_name,
            rank=result.rank,
            suitability_score=result.suitability_score,
            category_scores=result.matches[0].get("category_scores", {}) if result.matches else {},
            matches=[item for item in result.matches if item.get("status") != "category_scores"],
            gaps=result.gaps,
            evidence=result.evidence,
            explanation=result.explanation or "",
        )
        for result in results
    ]
    return ScreeningRunRead(
        id=run.id,
        job_id=run.job_id,
        status=run.status,
        created_at=run.created_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        weights=run.criteria_snapshot.get("weights", BASE_WEIGHTS),
        analysis_mode=run.criteria_snapshot.get("analysis_mode", "keyword_baseline"),
        llm_status=run.criteria_snapshot.get("llm_status", "unknown"),
        results=response_results,
    )


@router.post("/jobs/{job_id}/screen", response_model=ScreeningRunRead, status_code=status.HTTP_201_CREATED)
def screen_job(job_id: int, db: Session = Depends(get_db)) -> ScreeningRunRead:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    applications = db.scalars(
        select(Application)
        .where(Application.job_id == job_id, Application.status == "active")
        .options(joinedload(Application.candidate))
        .order_by(Application.id)
    ).unique().all()
    if not applications:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Add at least one candidate application first")

    run_started_at = datetime.now(timezone.utc)
    workflow_input = initial_screening_state(
        job={
            "title": job.title,
            "description": job.description,
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or [],
            "min_experience_years": job.min_experience_years,
        },
        candidates=[
            {
                "application_id": application.id,
                "candidate_id": application.candidate_id,
                "candidate_name": application.candidate.full_name,
                "skills": application.candidate.skills or [],
                "experience_years": application.candidate.experience_years,
                "experience_summary": application.candidate.experience_summary,
                "resume_text": application.candidate.resume_text or "",
            }
            for application in applications
        ],
    )
    workflow_result = get_screening_workflow().invoke(workflow_input)
    job_analysis = workflow_result["job_analysis"]
    if not job_analysis["required_skills"] and not job_analysis["preferred_skills"] and job_analysis["min_experience_years"] is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No supported screening criteria were found. Add job skills or experience requirements first.",
        )

    job.required_skills = job_analysis["required_skills"]
    job.preferred_skills = job_analysis["preferred_skills"]
    job.min_experience_years = job_analysis["min_experience_years"]
    candidate_analyses = {
        analysis["candidate_id"]: analysis for analysis in workflow_result["candidate_analyses"]
    }
    for application in applications:
        candidate = application.candidate
        analysis = candidate_analyses[candidate.id]
        candidate.skills = analysis["skills"]
        if candidate.experience_years is None:
            candidate.experience_years = analysis["experience_years"]
        if not candidate.experience_summary:
            candidate.experience_summary = analysis["experience_summary"]

    run = ScreeningRun(
        job_id=job_id,
        status="running",
        criteria_snapshot={
            "required_skills": job_analysis["required_skills"],
            "preferred_skills": job_analysis["preferred_skills"],
            "min_experience_years": job_analysis["min_experience_years"],
            "weights": BASE_WEIGHTS,
            "analysis_mode": workflow_result["analysis_mode"],
            "llm_status": workflow_result["llm_status"],
            "llm_successes": workflow_result["llm_successes"],
            "fallback_count": workflow_result["fallback_count"],
        },
        started_at=run_started_at,
    )
    db.add(run)
    db.flush()

    for score in workflow_result["results"]:
        category_scores = score["category_scores"]
        stored_matches = [{"status": "category_scores", "category_scores": category_scores}, *score["matches"]]
        db.add(
            ScreeningResult(
                screening_run_id=run.id,
                application_id=score["application_id"],
                rank=score["rank"],
                suitability_score=score["suitability_score"],
                matches=stored_matches,
                gaps=score["gaps"],
                evidence=score["evidence"],
                explanation=score["explanation"],
            )
        )

    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return _run_response(db, run)


@router.get("/screening-runs/{run_id}", response_model=ScreeningRunRead)
def get_screening_run(run_id: int, db: Session = Depends(get_db)) -> ScreeningRunRead:
    run = db.get(ScreeningRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screening run not found")
    return _run_response(db, run)
