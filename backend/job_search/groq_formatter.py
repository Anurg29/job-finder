"""
Compatibility bridge for AI job formatting.
Delegates to the industry-grade multi-provider AIPipeline.
"""
from typing import Any
from job_search.ai_pipeline import format_jobs_with_pipeline, compact_jobs


def _compact_jobs(jobs: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    return compact_jobs(jobs, limit=limit)


def format_jobs_with_groq(jobs: list[dict[str, Any]], query: str) -> str:
    """Format job search results using the AI pipeline (Gemini -> Groq -> Local)."""
    return format_jobs_with_pipeline(jobs, query)
