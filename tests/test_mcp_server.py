from unittest.mock import patch
from job_search.mcp_server import mcp, search_jobs, search_jobs_custom, search_all_jobs, search_fresher_jobs


def test_mcp_server_initialization():
    assert mcp.name == "Job Search Server"


def test_mcp_tools_registered():
    # Verify that the tools are properly exposed
    tool_names = [tool.name for tool in mcp._tool_manager.list_tools()]
    assert "search_jobs" in tool_names
    assert "search_fresher_jobs" in tool_names
    assert "search_jobs_custom" in tool_names
    assert "search_all_jobs" in tool_names


@patch("job_search.mcp_server.fetch_jobs")
@patch("job_search.mcp_server.format_jobs_with_pipeline")
def test_search_jobs_dynamic_location_and_role(mock_format, mock_fetch):
    mock_fetch.return_value = [{"title": "React Engineer", "company": "Tech Corp", "location": "London"}]
    mock_format.return_value = "Formatted Result"

    # Test with custom international location and role
    res = search_jobs(roles="React Engineer", locations="London", experience="2-4 years")
    assert res == "Formatted Result"
    mock_fetch.assert_called_with("React Engineer", ["London"], results_wanted=15)

    # Test with multiple dynamic locations
    search_jobs(roles="DevOps", locations="Mumbai, Pune, Remote", experience="Senior")
    assert mock_fetch.call_count == 2
    mock_fetch.assert_called_with("DevOps", ["Mumbai", "Pune", "Remote"], results_wanted=15)


@patch("job_search.mcp_server.fetch_jobs")
@patch("job_search.mcp_server.format_jobs_with_pipeline")
def test_search_jobs_custom_nlp_dynamic_parsing(mock_format, mock_fetch):
    mock_fetch.return_value = []
    mock_format.return_value = "Custom Result"

    # Query 1: Berlin Golang senior
    search_jobs_custom("Find Golang backend jobs in Berlin for senior engineers")
    mock_fetch.assert_called_with("Golang backend", ["Berlin"])

    # Query 2: Remote DevOps fresher
    search_jobs_custom("Remote DevOps engineer fresher openings")
    mock_fetch.assert_called_with("DevOps engineer", ["Remote"])

    # Query 3: Without location (should not hardcode Mumbai, searches Remote/Global)
    search_jobs_custom("Machine Learning Engineer")
    mock_fetch.assert_called_with("Machine Learning Engineer", ["Remote"])
