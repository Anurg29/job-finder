from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from job_search.api import app
from job_search.ai_pipeline import AIPipeline, compact_jobs
from job_search.mcp_server import search_jobs, search_jobs_custom
from job_search.scrapers.job_scraper import _detect_country, fetch_jobs

client = TestClient(app)


# ==============================================================================
# 1. GOOD CASES (HAPPY PATHS)
# ==============================================================================

def test_good_case_api_mcp_info():
    """Verify MCP info endpoint returns active tools, valid paths, and configs."""
    response = client.get("/api/mcp/info")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["server_name"] == "Job Search Server"
    assert len(data["tools"]) >= 4
    tool_names = [t["name"] for t in data["tools"]]
    assert "search_jobs" in tool_names
    assert "search_jobs_custom" in tool_names
    assert "search_all_jobs" in tool_names
    assert "search_fresher_jobs" in tool_names
    assert "configs" in data
    assert "claude_desktop_stdio" in data["configs"]
    assert "claude_desktop_sse" in data["configs"]


@patch("job_search.api.search_all_portals")
@patch("job_search.api.pipeline.process")
def test_good_case_search_jobs_api(mock_process, mock_search):
    """Verify search API produces structured responses when inputs are valid."""
    mock_search.return_value = [
        {"title": "Senior Golang Engineer", "company": "Acme", "location": "Berlin", "job_url": "https://example.com/1"}
    ]
    mock_res = MagicMock()
    mock_res.summary = "### Key Opportunities\n- Senior Golang Engineer in Berlin"
    mock_res.provider = "gemini"
    mock_process.return_value = mock_res

    payload = {
        "query": "Golang Engineer jobs in Berlin",
        "roles": ["Golang Engineer"],
        "cities": ["Berlin"],
        "experience": "Senior",
        "max_results": 10,
    }
    response = client.post("/api/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_jobs"] == 1
    assert "Senior Golang Engineer" in data["summary"]
    assert len(data["jobs"]) == 1


# ==============================================================================
# 2. WORST CASES (NEGATIVE, MALFORMED & ADVERSARIAL INPUTS)
# ==============================================================================

def test_worst_case_search_empty_roles():
    """Search with empty roles list must return 400 Bad Request."""
    response = client.post("/api/search", json={"roles": [], "cities": ["Mumbai"]})
    assert response.status_code == 400
    assert "At least one role is required" in response.json()["detail"]


def test_worst_case_search_empty_cities():
    """Search with empty cities list must return 400 Bad Request."""
    response = client.post("/api/search", json={"roles": ["Developer"], "cities": []})
    assert response.status_code == 400
    assert "At least one city is required" in response.json()["detail"]


def test_worst_case_search_invalid_bounds():
    """Search with max_results = 0 or negative pages must be rejected by Pydantic."""
    res_zero = client.post("/api/search", json={"roles": ["Dev"], "cities": ["Pune"], "max_results": 0})
    assert res_zero.status_code == 422

    res_neg = client.post("/api/search", json={"roles": ["Dev"], "cities": ["Pune"], "naukri_pages": -1})
    assert res_neg.status_code == 422


def test_worst_case_auth_invalid_mobiles():
    """Registration with letters, short numbers, or extreme lengths must be rejected."""
    # Letters in mobile
    res1 = client.post("/api/auth/register", json={
        "full_name": "Test", "mobile_no": "98765abcde", "dob": "2000-01-01", "password": "Password123"
    })
    assert res1.status_code == 400

    # Short mobile (5 digits)
    res2 = client.post("/api/auth/register", json={
        "full_name": "Test", "mobile_no": "12345", "dob": "2000-01-01", "password": "Password123"
    })
    assert res2.status_code == 400


def test_worst_case_auth_future_dob_and_short_password():
    """Registration with future DOB or password < 6 chars must be rejected."""
    # Future DOB
    res1 = client.post("/api/auth/register", json={
        "full_name": "Test", "mobile_no": "9876543210", "dob": "2099-01-01", "password": "Password123"
    })
    assert res1.status_code == 400
    assert "future" in res1.json()["detail"]

    # Short password
    res2 = client.post("/api/auth/register", json={
        "full_name": "Test", "mobile_no": "9876543210", "dob": "2000-01-01", "password": "123"
    })
    assert res2.status_code == 400
    assert "6 characters" in res2.json()["detail"]


def test_worst_case_auth_sql_injection_attempt():
    """SQL Injection attack payloads in mobile or password must fail safely with 401."""
    injection_payload = {
        "mobile_no": "' OR '1'='1",
        "password": "' OR '1'='1"
    }
    response = client.post("/api/auth/login", json=injection_payload)
    assert response.status_code == 401
    assert "Invalid mobile number or password" in response.json()["detail"]


# ==============================================================================
# 3. AI PIPELINE CASCADING FAULT INJECTION (GEMINI -> GROQ -> LOCAL)
# ==============================================================================

def test_worst_case_ai_pipeline_double_failure_fallback():
    """
    Simulate worst-case AI outage:
    1. Gemini throws 403 / quota limit.
    2. Groq throws 500 network timeout.
    -> Pipeline MUST NOT crash or raise 500. It must gracefully return deterministic Markdown.
    """
    pipe = AIPipeline()
    sample_jobs = [
        {"title": "DevOps Engineer", "company": "CloudCorp", "location": "Remote", "job_url": "https://example.com/job"}
    ]

    with patch.object(pipe, "_call_gemini", side_effect=Exception("403 PERMISSION_DENIED: CONSUMER_SUSPENDED")):
        with patch.object(pipe, "_call_groq", side_effect=Exception("500 Internal Server Error: Groq Timeout")):
            result = pipe.process(sample_jobs, "DevOps Engineer Remote")
            assert result.provider == "Deterministic Engine"
            assert result.job_count == 1
            assert "DevOps Engineer" in result.summary
            assert "CloudCorp" in result.summary


def test_worst_case_ai_pipeline_corrupted_job_data():
    """Corrupted job objects with None values, missing keys, or unexpected types must not crash compact_jobs."""
    corrupted_jobs = [
        {},  # Completely empty
        {"title": None, "company": None, "location": None},  # Null fields
        {"title": 12345, "company": ["Invalid", "Type"], "job_url": None},  # Non-string types
    ]
    compact = compact_jobs(corrupted_jobs)
    assert len(compact) == 3
    assert compact[0]["title"] == "N/A"
    assert compact[1]["company"] == "N/A"
    assert str(compact[2]["title"]) == "12345"


# ==============================================================================
# 4. MCP NLP EXTRACTION ADVERSARIAL EDGE CASES
# ==============================================================================

@patch("job_search.mcp_server.fetch_jobs")
@patch("job_search.mcp_server.format_jobs_with_pipeline")
def test_worst_case_mcp_extreme_punctuation_and_length(mock_format, mock_fetch):
    """MCP parser must handle extreme punctuation and long queries without regex explosion."""
    mock_fetch.return_value = []
    mock_format.return_value = "Result"

    # Extreme punctuation query
    search_jobs_custom("??? !!! @@@ React Developer $$$ ### in Mumbai *** ???")
    # Verify it doesn't crash and still recognizes Mumbai
    mock_fetch.assert_called()
    called_location = mock_fetch.call_args[0][1]
    assert called_location == ["Mumbai"]


def test_scraper_country_detection_fictitious_and_remote():
    """Scraper country detection handles imaginary or unusual locations gracefully."""
    # Unknown location defaults to India
    assert _detect_country("Atlantis") == "India"
    assert _detect_country("Gotham City") == "India"
    # Supported global locations
    assert _detect_country("New York") == "USA"
    assert _detect_country("London") == "UK"
    assert _detect_country("Berlin") == "Germany"
    assert _detect_country("Paris") == "France"
    assert _detect_country("Sydney") == "Australia"


@patch("job_search.scrapers.job_scraper.scrape_jobs", side_effect=Exception("ConnectionRefusedError: Network Timeout"))
def test_worst_case_scraper_network_failure(mock_scrape):
    """When external scraper network fails, fetch_jobs must catch and return [] without raising."""
    jobs = fetch_jobs("Rust Engineer", ["Remote"])
    assert jobs == []
