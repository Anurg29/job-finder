from job_search.groq_formatter import format_jobs_with_groq


def test_empty_jobs():
    res = format_jobs_with_groq([], "Python Developer")
    assert res == "No jobs found for this query."


def test_groq_formatting_with_fallback():
    sample_jobs = [
        {
            "title": "Python Junior Dev",
            "company": "Acme Corp",
            "location": "Pune",
            "job_url": "https://example.com/pune-dev",
            "date_posted": "2026-11-01",
            "min_exp": "Fresher"
        }
    ]
    res = format_jobs_with_groq(sample_jobs, "Python Developer in Pune")
    assert isinstance(res, str)
    assert len(res) > 0
    # Either valid markdown top matches or graceful JSON fallback
    assert "Python Junior Dev" in res or "Acme Corp" in res or "total_jobs" in res
