from pydantic import BaseModel, Field


class SkillEvidence(BaseModel):
    skill: str = Field(description="A job-related skill explicitly supported by the source")
    quote: str = Field(description="An exact, short quote copied from the source text")


class JobRequirementsOutput(BaseModel):
    required_skills: list[SkillEvidence] = Field(description="Skills stated as required or must-have")
    preferred_skills: list[SkillEvidence] = Field(description="Skills explicitly stated as preferred or nice-to-have")
    min_experience_years: float | None = Field(description="Explicit minimum years required, or null")
    experience_quote: str = Field(description="Exact quote supporting the minimum, or empty if none")


class CandidateProfileOutput(BaseModel):
    skills: list[SkillEvidence] = Field(description="Job-related skills explicitly supported by resume quotes")
    experience_years: float | None = Field(description="Explicit total experience in years, or null")
    experience_quote: str = Field(description="Exact quote supporting total years, or empty if none")


class GroundedClaim(BaseModel):
    statement: str = Field(description="A concise, job-related claim")
    evidence_quotes: list[str] = Field(description="Exact quotes from the provided evidence")


class ScreeningExplanationOutput(BaseModel):
    summary: str = Field(description="Short summary based only on the supplied score and evidence")
    summary_evidence: list[str] = Field(description="Exact supporting quotes for the summary")
    strengths: list[GroundedClaim] = Field(description="Supported strengths relevant to the job")
    considerations: list[GroundedClaim] = Field(
        description=(
            "Leave empty. Gaps and unknowns are reported directly from the deterministic scoring result; "
            "do not pair an absent skill with an unrelated positive resume quote."
        )
    )
