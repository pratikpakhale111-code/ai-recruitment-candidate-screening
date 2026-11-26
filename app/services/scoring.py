from __future__ import annotations

from typing import Any

from app.models import Candidate, Job
from app.services.profile_analyzer import SKILL_ALIASES, extract_skill_evidence

BASE_WEIGHTS = {
    "required_skills": 0.60,
    "preferred_skills": 0.20,
    "experience": 0.20,
}

_SKILL_NAMES = {
    alias.casefold(): canonical.casefold()
    for canonical, aliases in SKILL_ALIASES.items()
    for alias in (canonical, *aliases)
}


def _normalize_skill(value: str) -> str:
    normalized = value.strip().casefold()
    return _SKILL_NAMES.get(normalized, normalized)


def _score_skill_group(
    criteria: list[str],
    category: str,
    candidate_skills: set[str],
    has_profile_data: bool,
    resume_evidence: dict[str, list[str]],
) -> tuple[float | None, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if not criteria:
        return None, [], [], []

    matched: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    known_count = 0
    for criterion in criteria:
        normalized = _normalize_skill(criterion)
        if not has_profile_data:
            missing.append({"criterion": criterion, "category": category, "status": "unknown"})
            continue

        known_count += 1
        if normalized in candidate_skills:
            matched.append({"criterion": criterion, "category": category, "status": "matched"})
            snippets = resume_evidence.get(normalized, [])
            evidence.append(
                {
                    "criterion": criterion,
                    "category": category,
                    "status": "matched",
                    "source": "resume" if snippets else "candidate_profile",
                    "snippets": snippets,
                }
            )
        else:
            missing.append({"criterion": criterion, "category": category, "status": "missing"})

    score = 100.0 * len(matched) / known_count if known_count else None
    return score, matched, missing, evidence


def score_candidate(
    job: Job,
    candidate: Candidate,
    skill_evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    candidate_skills = {_normalize_skill(skill) for skill in (candidate.skills or [])}
    resume_evidence = {
        _normalize_skill(item["skill"]): item["evidence"]
        for item in extract_skill_evidence(candidate.resume_text or "")
    }
    for item in skill_evidence or []:
        normalized = _normalize_skill(item.get("skill", ""))
        quotes = item.get("evidence", [])
        if normalized and quotes:
            resume_evidence[normalized] = list(dict.fromkeys(resume_evidence.get(normalized, []) + quotes))
    has_profile_data = bool(candidate_skills or candidate.resume_text)

    required_score, required_matches, required_gaps, required_evidence = _score_skill_group(
        job.required_skills or [], "required_skill", candidate_skills, has_profile_data, resume_evidence
    )
    preferred_score, preferred_matches, preferred_gaps, preferred_evidence = _score_skill_group(
        job.preferred_skills or [], "preferred_skill", candidate_skills, has_profile_data, resume_evidence
    )

    category_scores: dict[str, float | None] = {
        "required_skills": round(required_score, 1) if required_score is not None else None,
        "preferred_skills": round(preferred_score, 1) if preferred_score is not None else None,
        "experience": None,
    }
    matches = required_matches + preferred_matches
    gaps = required_gaps + preferred_gaps
    evidence = required_evidence + preferred_evidence

    experience_score: float | None = None
    required_years = job.min_experience_years
    candidate_years = candidate.experience_years
    if required_years is not None:
        if candidate_years is None:
            gaps.append(
                {
                    "criterion": "experience_years",
                    "category": "experience",
                    "status": "unknown",
                    "required_years": required_years,
                }
            )
            evidence.append(
                {
                    "criterion": "experience_years",
                    "category": "experience",
                    "status": "unknown",
                    "source": "resume" if candidate.resume_text else "candidate_profile",
                    "snippets": [],
                }
            )
        else:
            experience_score = 100.0 if required_years <= 0 else min(candidate_years / required_years, 1.0) * 100.0
            experience_status = "meets" if candidate_years >= required_years else "below"
            matches.append(
                {
                    "criterion": "experience_years",
                    "category": "experience",
                    "status": experience_status,
                    "candidate_years": candidate_years,
                    "required_years": required_years,
                }
            )
            evidence.append(
                {
                    "criterion": "experience_years",
                    "category": "experience",
                    "status": experience_status,
                    "source": "resume" if candidate.experience_summary else "candidate_profile",
                    "snippets": [candidate.experience_summary] if candidate.experience_summary else [],
                }
            )
    category_scores["experience"] = round(experience_score, 1) if experience_score is not None else None

    available_categories = [
        (category, BASE_WEIGHTS[category], score)
        for category, score in (
            ("required_skills", required_score),
            ("preferred_skills", preferred_score),
            ("experience", experience_score),
        )
        if score is not None
    ]
    total_weight = sum(weight for _, weight, _ in available_categories)
    suitability_score = (
        round(sum(weight * score for _, weight, score in available_categories) / total_weight, 1)
        if total_weight
        else None
    )

    summary_parts = []
    for label, criteria, score in (
        ("required skills", job.required_skills or [], required_score),
        ("preferred skills", job.preferred_skills or [], preferred_score),
    ):
        if criteria:
            category = "required_skill" if label == "required skills" else "preferred_skill"
            matched_count = sum(
                1 for item in matches if item["category"] == category and item["status"] == "matched"
            )
            summary_parts.append(f"{label.title()}: {matched_count}/{len(criteria)} matched")
    if required_years is not None:
        summary_parts.append(
            f"Experience: candidate states {candidate_years:g} years against {required_years:g} required"
            if candidate_years is not None
            else f"Experience: {required_years:g} years required; candidate experience is not stated"
        )
    if suitability_score is None:
        summary_parts.append("Insufficient candidate data for a numeric score")
    else:
        summary_parts.append("Only criteria with available candidate data were included in the score")

    return {
        "suitability_score": suitability_score,
        "category_scores": category_scores,
        "matches": matches,
        "gaps": gaps,
        "evidence": evidence,
        "explanation": ". ".join(summary_parts) + ".",
    }
