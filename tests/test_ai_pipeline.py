from job_search.ai_pipeline import pipeline, compact_jobs


def test_compact_jobs():
    raw = [
        {
            "title": "Backend Dev",
            "company": "Google",
            "location": "Bangalore",
            "date_posted": "2026-11-03",
            "extra_bloat": "x" * 1000,
            "html": "<div>huge raw payload</div>",
            "job_url": "https://careers.google.com/123"
        }
    ]
    compact = compact_jobs(raw)
    assert len(compact) == 1
    assert "extra_bloat" not in compact[0]
    assert "html" not in compact[0]
    assert compact[0]["company"] == "Google"


def test_pipeline_processing():
    sample = [
        {
            "title": "AI Engineer Fresher",
            "company": "DeepMind Partner",
            "location": "Hyderabad",
            "job_url": "https://example.com/ai-1",
            "date_posted": "2026-11-03",
            "source": "linkedin"
        }
    ]
    result = pipeline.process(sample, "AI Engineer in Hyderabad")
    assert result.job_count == 1
    assert len(result.summary) > 0
    assert result.latency_ms > 0
    assert result.provider != "none"


def test_diagnostics_probe():
    diag = pipeline.test_providers()
    assert "gemini" in diag
    assert "groq" in diag
