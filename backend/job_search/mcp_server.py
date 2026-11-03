if __package__ in (None, ""):
    import sys
    from pathlib import Path

    backend_path = str(Path(__file__).resolve().parents[1])
    root_path = str(Path(__file__).resolve().parents[2])
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    if root_path not in sys.path:
        sys.path.insert(0, root_path)

import re
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    try:
        from mcp.server.mcpserver import MCPServer as FastMCP
    except ImportError:
        from mcp.server.fastmcp import FastMCP

from job_search.ai_pipeline import format_jobs_with_pipeline
from job_search.scrapers.job_scraper import fetch_jobs
from job_search.unified_scraper import search_all_portals

# Initialize FastMCP server
mcp = FastMCP("Job Search Server")


@mcp.tool()
def search_jobs(
    roles: str = "Python Developer",
    locations: str = "Mumbai",
    experience: str = "Fresher"
) -> str:
    """
    Search for jobs dynamically across any tech stack, any location, and any experience level.
    
    Args:
        roles: Comma-separated tech stacks/roles (e.g., 'Python Developer', 'React Developer', 'DevOps')
        locations: Comma-separated cities or regions (e.g., 'Mumbai', 'Pune', 'London', 'Remote')
        experience: Experience level (e.g., 'Fresher', '1-3 years', 'Senior', or 'Any')
    """
    role_list = [r.strip() for r in roles.split(",") if r.strip()]
    location_list = [loc.strip() for loc in locations.split(",") if loc.strip()]
    
    all_jobs: list[dict[str, Any]] = []
    
    for role in role_list:
        jobs = fetch_jobs(role, location_list)
        all_jobs.extend(jobs)
    
    # Deduplicate by URL
    seen_urls = set()
    unique_jobs: list[dict[str, Any]] = []
    for job in all_jobs:
        url = str(job.get("job_url", "")).strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_jobs.append(job)
    
    query = f"{roles} jobs in {locations} ({experience})"
    return format_jobs_with_pipeline(unique_jobs, query)


@mcp.tool()
def search_jobs_custom(query: str) -> str:
    """
    Natural language job search for any tech stack, location, and experience.
    Example: 'Show me all React developer jobs in Mumbai for 2 years experience'
    
    Args:
        query: Freeform job search query
    """
    # Dynamic location extraction (handles 'in <City>' or 'at <City>')
    location_match = re.search(r'\b(?:in|at|around|for)\s+([A-Za-z\s]+?)(?:\s+(?:with|for|as|posted|this|experience)|$)', query, re.IGNORECASE)
    if location_match:
        extracted_location = location_match.group(1).strip()
    else:
        extracted_location = "Mumbai"

    # Dynamic experience extraction
    exp_match = re.search(r'\b(\d+\+?\s*(?:years?|yrs?)|fresher|intern(?:ship)?|senior|junior|lead)\b', query, re.IGNORECASE)
    extracted_exp = exp_match.group(1).strip() if exp_match else "Any"

    # Clean roles from query by removing stopwords and locations
    clean_query = re.sub(r'\b(?:show|me|all|jobs?|openings?|in|at|for|with|experience|posted|this|week|recent|find)\b', '', query, flags=re.IGNORECASE)
    clean_role = clean_query.replace(extracted_location, "").strip() or query

    all_jobs = fetch_jobs(clean_role, [extracted_location])
    return format_jobs_with_pipeline(all_jobs, query)


@mcp.tool()
def search_all_jobs(
    query: str = "Software Developer in Mumbai",
    roles: str = "Software Developer",
    locations: str = "Mumbai",
    experience: str = "Fresher",
    include_naukri: bool = True,
    include_internshala: bool = True,
) -> str:
    """
    Multi-portal deep search across Indeed, LinkedIn, Naukri, and Internshala.
    Supports any role, location, and experience level.
    """
    role_list = [r.strip() for r in roles.split(",") if r.strip()]
    location_list = [loc.strip() for loc in locations.split(",") if loc.strip()]

    all_jobs = search_all_portals(
        roles=role_list,
        cities=location_list,
        include_naukri=include_naukri,
        include_internshala=include_internshala,
        naukri_pages=2,
        internshala_pages=2,
        experience=experience,
    )
    return format_jobs_with_pipeline(all_jobs, query)


@mcp.tool()
def search_fresher_jobs(
    roles: str = "Python Developer",
    locations: str = "Mumbai",
) -> str:
    """Search for fresher openings dynamically across any tech stack and location."""
    return search_jobs(roles=roles, locations=locations, experience="Fresher")


if __name__ == "__main__":
    mcp.run()
