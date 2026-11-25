from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import JobAnalysisRead, JobCreate, JobRead
from app.db.session import get_db
from app.models import Job
from app.services.profile_analyzer import analyze_job_description, merge_skills

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db: Session = Depends(get_db)) -> Job:
    job = Job(**payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=list[JobRead])
def list_jobs(
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[Job]:
    statement = select(Job).order_by(Job.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("/{job_id}/analyze", response_model=JobAnalysisRead)
def analyze_job(job_id: int, db: Session = Depends(get_db)) -> JobAnalysisRead:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    analysis = analyze_job_description(job.description)
    job.required_skills = merge_skills(job.required_skills, analysis["required_skills"])
    job.preferred_skills = merge_skills(job.preferred_skills, analysis["preferred_skills"])
    required_folded = {skill.casefold() for skill in job.required_skills}
    job.preferred_skills = [skill for skill in job.preferred_skills if skill.casefold() not in required_folded]
    if job.min_experience_years is None:
        job.min_experience_years = analysis["min_experience_years"]

    db.commit()
    return JobAnalysisRead(
        job_id=job.id,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        skill_evidence=analysis["skill_evidence"],
        min_experience_years=job.min_experience_years,
        experience_evidence=analysis["experience_evidence"],
        analyzer=analysis["analyzer"],
    )
