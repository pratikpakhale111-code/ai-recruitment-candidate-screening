from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "FastAPI": ("fastapi", "fast api"),
    "Django": ("django",),
    "Flask": ("flask",),
    "Java": ("java",),
    "JavaScript": ("javascript",),
    "TypeScript": ("typescript",),
    "C++": ("c++",),
    "C#": ("c#",),
    "SQL": ("sql",),
    "PostgreSQL": ("postgresql", "postgres"),
    "MySQL": ("mysql",),
    "Redis": ("redis",),
    "React": ("react",),
    "Node.js": ("node.js", "node js"),
    "REST API": ("rest api", "rest apis"),
    "GraphQL": ("graphql",),
    "Git": ("git",),
    "Linux": ("linux",),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes",),
    "AWS": ("aws", "amazon web services"),
    "Azure": ("azure",),
    "Google Cloud": ("google cloud", "gcp"),
    "Machine Learning": ("machine learning",),
    "Natural Language Processing": ("natural language processing", "nlp"),
    "Retrieval-Augmented Generation": ("retrieval-augmented generation", "rag"),
    "LangChain": ("langchain",),
    "LangGraph": ("langgraph",),
    "PyTorch": ("pytorch",),
    "TensorFlow": ("tensorflow",),
    "scikit-learn": ("scikit-learn", "sklearn"),
    "pandas": ("pandas",),
    "NumPy": ("numpy",),
    "Excel": ("excel",),
    "Power BI": ("power bi",),
    "Tableau": ("tableau",),
    "Agile": ("agile",),
    "CI/CD": ("ci/cd", "continuous integration", "continuous delivery"),
}

PREFERRED_CUES = ("preferred", "nice to have", "bonus", "desirable", "a plus")
EXPERIENCE_PATTERN = re.compile(
    r"(?<!\d)(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:professional\s+)?experience\b",
    re.IGNORECASE,
)


def _evidence_snippet(text: str, start: int, end: int, max_length: int = 280) -> str:
    left = max(text.rfind(delimiter, 0, start) for delimiter in ("\n", ".", ";")) + 1
    right_candidates = [position for delimiter in ("\n", ".", ";") if (position := text.find(delimiter, end)) >= 0]
    right = min(right_candidates) if right_candidates else len(text)
    snippet = " ".join(text[left:right].split())
    if len(snippet) <= max_length:
        return snippet

    match_offset = start - left
    snippet_start = max(0, match_offset - max_length // 2)
    snippet_end = min(len(snippet), snippet_start + max_length)
    if snippet_end - snippet_start < max_length:
        snippet_start = max(0, snippet_end - max_length)
    return snippet[snippet_start:snippet_end].strip()


def extract_skill_evidence(text: str) -> list[dict[str, Any]]:
    """Find known skill mentions and return short source snippets for review."""
    findings: list[dict[str, Any]] = []
    for canonical, aliases in SKILL_ALIASES.items():
        evidence: list[str] = []
        for alias in aliases:
            pattern = re.compile(rf"(?<!\w){re.escape(alias)}(?!\w)", re.IGNORECASE)
            for match in pattern.finditer(text):
                snippet = _evidence_snippet(text, match.start(), match.end())
                if snippet and snippet not in evidence:
                    evidence.append(snippet)
        if evidence:
            findings.append({"skill": canonical, "evidence": evidence[:3]})
    return findings


def _merge_case_insensitive(existing: Iterable[str], additions: Iterable[str]) -> list[str]:
    merged = list(existing)
    seen = {value.casefold() for value in merged}
    for value in additions:
        if value.casefold() not in seen:
            merged.append(value)
            seen.add(value.casefold())
    return merged


def analyze_job_description(description: str) -> dict[str, Any]:
    findings = extract_skill_evidence(description)
    required: list[str] = []
    preferred: list[str] = []
    for finding in findings:
        context = " ".join(finding["evidence"]).casefold()
        destination = preferred if any(cue in context for cue in PREFERRED_CUES) else required
        destination.append(finding["skill"])

    experience_match = EXPERIENCE_PATTERN.search(description)
    experience_years = float(experience_match.group(1)) if experience_match else None
    experience_evidence = (
        [_evidence_snippet(description, experience_match.start(), experience_match.end())]
        if experience_match
        else []
    )
    return {
        "required_skills": required,
        "preferred_skills": preferred,
        "skill_evidence": findings,
        "min_experience_years": experience_years,
        "experience_evidence": experience_evidence,
        "analyzer": "keyword_baseline",
    }


def analyze_candidate_resume(resume_text: str) -> dict[str, Any]:
    findings = extract_skill_evidence(resume_text)
    experience_matches = list(EXPERIENCE_PATTERN.finditer(resume_text))
    experience_years = (
        max(float(match.group(1)) for match in experience_matches) if experience_matches else None
    )
    experience_evidence = [
        _evidence_snippet(resume_text, match.start(), match.end())
        for match in experience_matches[:3]
    ]
    summary = " ".join(experience_evidence)[:1000] or None
    return {
        "skills": [finding["skill"] for finding in findings],
        "skill_evidence": findings,
        "experience_years": experience_years,
        "experience_summary": summary,
        "experience_evidence": experience_evidence,
        "analyzer": "keyword_baseline",
    }


def merge_skills(existing: list[str], additions: list[str]) -> list[str]:
    return _merge_case_insensitive(existing, additions)
