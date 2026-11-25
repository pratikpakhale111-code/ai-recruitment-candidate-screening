from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    location: str | None = Field(default=None, max_length=200)
    min_experience_years: float | None = Field(default=None, ge=0, le=80)
    required_skills: list[str] = Field(default_factory=list, max_length=100)
    preferred_skills: list[str] = Field(default_factory=list, max_length=100)


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    location: str | None
    min_experience_years: float | None
    required_skills: list[str]
    preferred_skills: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


class CandidateCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    skills: list[str] = Field(default_factory=list, max_length=100)
    experience_years: float | None = Field(default=None, ge=0, le=80)
    experience_summary: str | None = None


class CandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str | None
    skills: list[str]
    experience_years: float | None
    experience_summary: str | None
    created_at: datetime


class ApplicationCreate(BaseModel):
    job_id: int = Field(gt=0)
    candidate_id: int = Field(gt=0)


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    candidate_id: int
    status: str
    decision_status: str
    created_at: datetime
