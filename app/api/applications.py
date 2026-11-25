from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas import ApplicationCreate, ApplicationRead
from app.db.session import get_db
from app.models import Application, Candidate, Job

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)) -> Application:
    if db.get(Job, payload.job_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if db.get(Candidate, payload.candidate_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")

    application = Application(**payload.model_dump())
    db.add(application)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This candidate already has an application for the job",
        ) from exc
    db.refresh(application)
    return application


@router.get("", response_model=list[ApplicationRead])
def list_applications(
    job_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[Application]:
    statement = select(Application).order_by(Application.created_at.desc()).offset(offset).limit(limit)
    if job_id is not None:
        statement = statement.where(Application.job_id == job_id)
    return list(db.scalars(statement).all())
