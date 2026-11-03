from job_search.mcp_server import mcp


def test_mcp_server_initialization():
    assert mcp.name == "Job Search Server"


def test_mcp_tools_registered():
    # Verify that the 3 tools are properly exposed
    tool_names = [tool.name for tool in mcp._tool_manager.list_tools()]
    assert "search_fresher_jobs" in tool_names
    assert "search_jobs_custom" in tool_names
    assert "search_all_jobs" in tool_names
