from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Multi-tier .env discovery
_CANDIDATE_ENVS = [
    Path.cwd() / ".env",
    Path(__file__).resolve().parents[1] / ".env",
    Path(__file__).resolve().parents[2] / ".env",
]
for _env_file in _CANDIDATE_ENVS:
    if _env_file.exists():
        load_dotenv(dotenv_path=_env_file)
        break

logger = logging.getLogger("job_search.ai_pipeline")


@dataclass
class PipelineResult:
    summary: str
    provider: str
    latency_ms: float
    job_count: int
    error: str | None = None


def compact_jobs(jobs: list[dict[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    """Token-efficient projection: strip raw HTML and retain only core hiring metadata."""
    compact: list[dict[str, Any]] = []
    for job in jobs[:limit]:
        compact.append(
            {
                "title": job.get("title", "N/A"),
                "company": job.get("company", "N/A"),
                "location": job.get("location", "N/A"),
                "date_posted": str(job.get("date_posted", "N/A")),
                "min_exp": str(job.get("min_exp") or "Fresher"),
                "source": job.get("source", "portal"),
                "job_url": job.get("job_url", "N/A"),
            }
        )
    return compact


class AIPipeline:
    """
    Industry-Grade AI Orchestration Pipeline.
    Supports Google Gemini (Primary) with automated zero-downtime failover to Groq,
    and a local deterministic fallback engine.
    """

    def __init__(self) -> None:
        self.gemini_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GEMINI")
            or ""
        ).strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
        self.groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()

    def _build_prompt(self, query: str, compact: list[dict[str, Any]]) -> str:
        return (
            "You are an expert career and hiring intelligence advisor. Given the user's search query "
            "and the live job openings below, provide an actionable briefing:\n\n"
            "1) **Top Match**: Highlight the best-matching role based on the requested tech stack, location, and experience level.\n"
            "2) **Curated Opportunities**: Bulleted list with Job Title, Company, Location, Date Posted, and direct Apply URL.\n"
            "3) **Hiring & Skill Insights**: Key technical requirements and tips to stand out for this exact search.\n\n"
            f"Search Criteria: {query}\n"
            f"Job Listings JSON: {json.dumps(compact)}"
        )

    def _call_gemini(self, prompt: str) -> str:
        """Execute inference using Google GenAI SDK."""
        from google import genai

        client = genai.Client(api_key=self.gemini_key)
        response = client.models.generate_content(
            model=self.gemini_model,
            contents=prompt,
        )
        if not response.text:
            raise ValueError("Empty response received from Gemini API.")
        return response.text

    def _call_groq(self, prompt: str) -> str:
        """Execute inference using Groq SDK."""
        from groq import Groq

        client = Groq(api_key=self.groq_key)
        response = client.chat.completions.create(
            model=self.groq_model,
            messages=[
                {"role": "system", "content": "You format job search results clearly and professionally."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response received from Groq API.")
        return content

    def _local_fallback(self, query: str, compact: list[dict[str, Any]], reason: str) -> str:
        """Zero-dependency deterministic markdown generation."""
        lines = [
            f"## Opportunities for: {query}",
            f"*{len(compact)} listings retrieved (Engine: Local Formatter | Note: {reason})*\n",
        ]
        for job in compact[:10]:
            lines.append(
                f"- **{job['title']}** at **{job['company']}**\n"
                f"  *Location:* {job['location']} | *Posted:* {job['date_posted']} | [Apply on {job['source']}]({job['job_url']})"
            )
        lines.append("\n> **Tip:** Review minimum qualifications and apply directly on the portal.")
        return "\n".join(lines)

    def process(self, jobs: list[dict[str, Any]], query: str) -> PipelineResult:
        """Run the cascading multi-provider pipeline."""
        start_time = time.perf_counter()

        if not jobs:
            return PipelineResult(
                summary="No jobs found for this query.",
                provider="none",
                latency_ms=0.0,
                job_count=0,
            )

        compact = compact_jobs(jobs)
        prompt = self._build_prompt(query, compact)

        # 1. Attempt Primary: Google Gemini
        if self.gemini_key:
            try:
                summary = self._call_gemini(prompt)
                latency = (time.perf_counter() - start_time) * 1000
                return PipelineResult(
                    summary=summary,
                    provider=f"Google Gemini ({self.gemini_model})",
                    latency_ms=latency,
                    job_count=len(compact),
                )
            except Exception as gemini_err:
                logger.warning(f"[AI Pipeline] Gemini provider failed: {gemini_err}. Falling back to Groq.")

        # 2. Attempt Secondary: Groq LLM
        if self.groq_key:
            try:
                summary = self._call_groq(prompt)
                latency = (time.perf_counter() - start_time) * 1000
                return PipelineResult(
                    summary=summary,
                    provider=f"Groq ({self.groq_model})",
                    latency_ms=latency,
                    job_count=len(compact),
                )
            except Exception as groq_err:
                logger.warning(f"[AI Pipeline] Groq provider failed: {groq_err}. Falling back to local engine.")

        # 3. Tertiary: Local Deterministic Engine
        latency = (time.perf_counter() - start_time) * 1000
        reason = "AI API keys missing or unavailable"
        if self.gemini_key and not self.groq_key:
            reason = "Gemini API unavailable"
        elif self.gemini_key and self.groq_key:
            reason = "Cloud LLM services unavailable"

        summary = self._local_fallback(query, compact, reason)
        return PipelineResult(
            summary=summary,
            provider="Deterministic Engine",
            latency_ms=latency,
            job_count=len(compact),
            error=reason,
        )

    def test_providers(self) -> dict[str, Any]:
        """Diagnostic probe for all configured AI providers."""
        diagnostics = {
            "gemini": {"configured": bool(self.gemini_key), "model": self.gemini_model, "status": "untested"},
            "groq": {"configured": bool(self.groq_key), "model": self.groq_model, "status": "untested"},
        }

        if self.gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=self.gemini_key)
                res = client.models.generate_content(model=self.gemini_model, contents="Ping")
                diagnostics["gemini"]["status"] = "operational" if res.text else "empty"
            except Exception as e:
                diagnostics["gemini"]["status"] = f"error: {e}"

        if self.groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=self.groq_key)
                res = client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": "Ping"}],
                    max_tokens=5,
                )
                diagnostics["groq"]["status"] = "operational"
            except Exception as e:
                diagnostics["groq"]["status"] = f"error: {e}"

        return diagnostics


# Default singleton instance
pipeline = AIPipeline()


def format_jobs_with_pipeline(jobs: list[dict[str, Any]], query: str) -> str:
    """Drop-in functional wrapper returning formatted markdown."""
    result = pipeline.process(jobs, query)
    return result.summary
