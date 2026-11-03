import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq

# Multi-tier .env discovery: checks cwd, backend/.env, and job/.env
_CANDIDATE_ENVS = [
    Path.cwd() / ".env",
    Path(__file__).resolve().parents[1] / ".env",
    Path(__file__).resolve().parents[2] / ".env",
]
for _env_file in _CANDIDATE_ENVS:
    if _env_file.exists():
        load_dotenv(dotenv_path=_env_file)
        break


def _compact_jobs(jobs: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for job in jobs[:limit]:
        compact.append(
            {
                "title": job.get("title", "N/A"),
                "company": job.get("company", "N/A"),
                "location": job.get("location", "N/A"),
                "date_posted": str(job.get("date_posted", "N/A")),
                "min_exp": str(job.get("min_exp", "N/A")),
                "job_url": job.get("job_url", "N/A"),
            }
        )
    return compact


def format_jobs_with_groq(jobs: list[dict[str, Any]], query: str) -> str:
    if not jobs:
        return "No jobs found for this query."

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    compact_jobs = _compact_jobs(jobs)

    if not api_key:
        return json.dumps(
            {"query": query, "total_jobs": len(jobs), "jobs": compact_jobs}, indent=2
        )

    # Allow custom model from env, defaulting to active fast Groq model
    model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()

    prompt = (
        "You are a job assistant. Given the query and job results, return a concise "
        "markdown response with:\n"
        "1) Top matches section\n"
        "2) Bullet list of jobs with title, company, location, date, URL\n"
        "3) Short suggestion line at end\n\n"
        f"Query: {query}\n"
        f"Jobs JSON: {json.dumps(compact_jobs)}"
    )

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You format job search results clearly."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return content or "No formatted response generated."
    except Exception as exc:
        fallback = {
            "query": query,
            "total_jobs": len(jobs),
            "note": f"Groq formatting failed: {exc}",
            "jobs": compact_jobs,
        }
        return json.dumps(fallback, indent=2)
