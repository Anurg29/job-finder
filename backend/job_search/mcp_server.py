if __package__ in (None, ""):
    import sys
    from pathlib import Path

    # Allow direct execution from backend or root: `python job_search/mcp_server.py`
    backend_path = str(Path(__file__).resolve().parents[1])
    root_path = str(Path(__file__).resolve().parents[2])
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    if root_path not in sys.path:
        sys.path.insert(0, root_path)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    try:
        from mcp.server.mcpserver import MCPServer as FastMCP
    except ImportError:
        from mcp.server.fastmcp import FastMCP

from job_search.groq_formatter import format_jobs_with_groq
from job_search.scrapers.job_scraper import fetch_jobs
from job_search.unified_scraper import search_all_portals

# Initialize MCP server
mcp = FastMCP("Job Search Server")

@mcp.tool()
def search_fresher_jobs(
    roles: str = "Python Developer, AI Developer, Java Developer",
    cities: str = "Hyderabad, Pune, Mumbai, Bangalore"
) -> str:
    """
    Search for fresher job openings in Python, Java, and AI/ML roles
    across major Indian cities.
    
    Args:
        roles: Comma-separated job roles to search
        cities: Comma-separated cities to search in
    """
    
    role_list = [r.strip() for r in roles.split(",") if r.strip()]
    city_list = [c.strip() for c in cities.split(",") if c.strip()]
    
    all_jobs = []
    
    for role in role_list:
        jobs = fetch_jobs(role, city_list)
        all_jobs.extend(jobs)
    
    # Remove duplicates by URL
    seen_urls = set()
    unique_jobs = []
    for job in all_jobs:
        if job["job_url"] not in seen_urls:
            seen_urls.add(job["job_url"])
            unique_jobs.append(job)
    
    query = f"Fresher {roles} jobs in {cities}"
    result = format_jobs_with_groq(unique_jobs, query)
    
    return result


@mcp.tool()
def search_jobs_custom(query: str) -> str:
    """
    Natural language job search.
    Example: 'Show me all Python fresher jobs in Hyderabad posted this week'
    
    Args:
        query: Natural language job search query
    """
    city_map = {
        "hyderabad": "Hyderabad, India",
        "pune": "Pune, India", 
        "mumbai": "Mumbai, India",
        "bangalore": "Bangalore, India",
        "bengaluru": "Bangalore, India"
    }
    
    cities = [v for k, v in city_map.items() if k in query.lower()]
    if not cities:
        cities = ["Hyderabad, India", "Pune, India", 
                  "Mumbai, India", "Bangalore, India"]
    
    roles = []
    if "python" in query.lower():
        roles.append("Python Developer")
    if "ai" in query.lower() or "ml" in query.lower():
        roles.append("AI ML Engineer")
    if not roles:
        roles = ["Python Developer"]
    
    all_jobs = []
    for role in roles:
        jobs = fetch_jobs(role, cities)
        all_jobs.extend(jobs)
    
    return format_jobs_with_groq(all_jobs, query)


@mcp.tool()
def search_all_jobs(
    query: str = "Python fresher jobs in Hyderabad, Pune, Mumbai, Bangalore",
    roles: str = "Python Developer, AI ML Engineer",
    cities: str = "Hyderabad, Pune, Mumbai, Bangalore",
    include_naukri: bool = True,
    include_internshala: bool = True,
) -> str:
    """
    Search across multiple job portals:
    - JobSpy sources: Indeed, LinkedIn, Glassdoor
    - Optional: Naukri
    - Optional: Internshala
    """
    role_list = [r.strip() for r in roles.split(",") if r.strip()]
    city_list = [c.strip() for c in cities.split(",") if c.strip()]

    all_jobs = search_all_portals(
        roles=role_list,
        cities=city_list,
        include_naukri=include_naukri,
        include_internshala=include_internshala,
        naukri_pages=2,
        internshala_pages=2,
    )
    return format_jobs_with_groq(all_jobs, query)


if __name__ == "__main__":
    mcp.run()
