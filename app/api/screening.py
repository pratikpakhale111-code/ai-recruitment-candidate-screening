from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models import Application, Candidate, Job, ScreeningResult, ScreeningRun
from app.services.profile_analyzer import analyze_candidate_resume, analyze_job_description, merge_skills
from app.services.scoring import BASE_WEIGHTS, score_candidate

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
        results=response_results,
    )


def _prepare_candidate(candidate: Candidate) -> None:
    if not candidate.resume_text:
        return
    analysis = analyze_candidate_resume(candidate.resume_text)
    candidate.skills = merge_skills(candidate.skills or [], analysis["skills"])
    if candidate.experience_years is None:
        candidate.experience_years = analysis["experience_years"]
    if not candidate.experience_summary:
        candidate.experience_summary = analysis["experience_summary"]


@router.post("/jobs/{job_id}/screen", response_model=ScreeningRunRead, status_code=status.HTTP_201_CREATED)
def screen_job(job_id: int, db: Session = Depends(get_db)) -> ScreeningRunRead:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if not job.required_skills and not job.preferred_skills and job.min_experience_years is None:
        analysis = analyze_job_description(job.description)
        job.required_skills = analysis["required_skills"]
        job.preferred_skills = analysis["preferred_skills"]
        job.min_experience_years = analysis["min_experience_years"]

    if not job.required_skills and not job.preferred_skills and job.min_experience_years is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No supported screening criteria were found. Add job skills or experience requirements first.",
        )

    applications = db.scalars(
        select(Application)
        .where(Application.job_id == job_id, Application.status == "active")
        .options(joinedload(Application.candidate))
        .order_by(Application.id)
    ).unique().all()
    if not applications:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Add at least one candidate application first")

    for application in applications:
        _prepare_candidate(application.candidate)

    now = datetime.now(timezone.utc)
    run = ScreeningRun(
        job_id=job_id,
        status="running",
        criteria_snapshot={
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or [],
            "min_experience_years": job.min_experience_years,
            "weights": BASE_WEIGHTS,
        },
        started_at=now,
    )
    db.add(run)
    db.flush()

    scored: list[tuple[Application, dict[str, Any]]] = [
        (application, score_candidate(job, application.candidate)) for application in applications
    ]
    ranked = sorted(
        (item for item in scored if item[1]["suitability_score"] is not None),
        key=lambda item: (-item[1]["suitability_score"], item[0].candidate.full_name.casefold(), item[0].id),
    )
    rank_by_application = {application.id: rank for rank, (application, _) in enumerate(ranked, start=1)}

    for application, score in scored:
        category_scores = score["category_scores"]
        stored_matches = [{"status": "category_scores", "category_scores": category_scores}, *score["matches"]]
        db.add(
            ScreeningResult(
                screening_run_id=run.id,
                application_id=application.id,
                rank=rank_by_application.get(application.id),
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
