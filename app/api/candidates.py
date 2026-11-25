from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import CandidateAnalysisRead, CandidateCreate, CandidateRead
from app.db.session import get_db
from app.models import Candidate
from app.services.profile_analyzer import analyze_candidate_resume, merge_skills

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post("", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
def create_candidate(payload: CandidateCreate, db: Session = Depends(get_db)) -> Candidate:
    candidate = Candidate(**payload.model_dump())
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.get("", response_model=list[CandidateRead])
def list_candidates(
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[Candidate]:
    statement = select(Candidate).order_by(Candidate.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/{candidate_id}", response_model=CandidateRead)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)) -> Candidate:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return candidate


@router.post("/{candidate_id}/analyze", response_model=CandidateAnalysisRead)
def analyze_candidate(candidate_id: int, db: Session = Depends(get_db)) -> CandidateAnalysisRead:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    if not candidate.resume_text:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upload a resume before analyzing this candidate",
        )

    analysis = analyze_candidate_resume(candidate.resume_text)
    candidate.skills = merge_skills(candidate.skills, analysis["skills"])
    if candidate.experience_years is None:
        candidate.experience_years = analysis["experience_years"]
    if not candidate.experience_summary:
        candidate.experience_summary = analysis["experience_summary"]
    db.commit()

    return CandidateAnalysisRead(
        candidate_id=candidate.id,
        skills=candidate.skills,
        skill_evidence=analysis["skill_evidence"],
        experience_years=candidate.experience_years,
        experience_summary=candidate.experience_summary,
        experience_evidence=analysis["experience_evidence"],
        analyzer=analysis["analyzer"],
    )
