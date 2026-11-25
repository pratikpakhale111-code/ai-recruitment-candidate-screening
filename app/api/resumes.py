from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Application, Candidate, Job
from app.services.resume_parser import MAX_RESUME_BYTES, ResumeProcessingError, extract_resume_text

router = APIRouter(tags=["resumes"])


class ResumeUploadRead(BaseModel):
    application_id: int
    job_id: int
    candidate_id: int
    candidate_name: str
    resume_filename: str
    extracted_characters: int


@router.post(
    "/jobs/{job_id}/applications/upload",
    response_model=ResumeUploadRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF or DOCX resume for a job",
)
async def upload_resume_for_job(
    job_id: int,
    full_name: Annotated[str, Form(min_length=1, max_length=200)],
    resume: Annotated[UploadFile, File()],
    email: Annotated[str | None, Form(max_length=320)] = None,
    db: Session = Depends(get_db),
) -> ResumeUploadRead:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    filename = resume.filename or ""
    contents = await resume.read(MAX_RESUME_BYTES + 1)
    if len(contents) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Resume must be 10 MB or smaller")

    try:
        safe_filename, resume_text = extract_resume_text(filename, contents)
    except ResumeProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    candidate_name = full_name.strip()
    if not candidate_name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Candidate name cannot be blank")

    candidate = Candidate(
        full_name=candidate_name,
        email=email.strip() if email and email.strip() else None,
        resume_filename=safe_filename,
        resume_text=resume_text,
    )
    db.add(candidate)
    db.flush()

    application = Application(job_id=job_id, candidate_id=candidate.id)
    db.add(application)
    db.commit()
    db.refresh(application)

    return ResumeUploadRead(
        application_id=application.id,
        job_id=job_id,
        candidate_id=candidate.id,
        candidate_name=candidate.full_name,
        resume_filename=safe_filename,
        extracted_characters=len(resume_text),
    )
