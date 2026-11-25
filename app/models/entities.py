from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    min_experience_years: Mapped[float | None] = mapped_column(Float)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    applications: Mapped[list[Application]] = relationship(back_populates="job", cascade="all, delete-orphan")
    screening_runs: Mapped[list[ScreeningRun]] = relationship(back_populates="job", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    resume_filename: Mapped[str | None] = mapped_column(String(255))
    resume_text: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    experience_years: Mapped[float | None] = mapped_column(Float)
    experience_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    applications: Mapped[list[Application]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_application_job_candidate"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    decision_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[Job] = relationship(back_populates="applications")
    candidate: Mapped[Candidate] = relationship(back_populates="applications")
    screening_results: Mapped[list[ScreeningResult]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    decisions: Mapped[list[RecruiterDecision]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class ScreeningRun(Base):
    __tablename__ = "screening_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False)
    criteria_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[Job] = relationship(back_populates="screening_runs")
    results: Mapped[list[ScreeningResult]] = relationship(back_populates="screening_run", cascade="all, delete-orphan")


class ScreeningResult(Base):
    __tablename__ = "screening_results"
    __table_args__ = (
        UniqueConstraint("screening_run_id", "application_id", name="uq_result_run_application"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    screening_run_id: Mapped[int] = mapped_column(ForeignKey("screening_runs.id", ondelete="CASCADE"), index=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    rank: Mapped[int | None] = mapped_column(Integer)
    suitability_score: Mapped[float | None] = mapped_column(Float)
    matches: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    gaps: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    screening_run: Mapped[ScreeningRun] = relationship(back_populates="results")
    application: Mapped[Application] = relationship(back_populates="screening_results")


class RecruiterDecision(Base):
    __tablename__ = "recruiter_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    recruiter_name: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped[Application] = relationship(back_populates="decisions")
