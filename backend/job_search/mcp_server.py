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


def _normalize_locations(locations: str | list[str] | None) -> list[str]:
    """Helper to convert any location input (string, comma-separated, list) into clean list."""
    if not locations:
        return []
    if isinstance(locations, list):
        return [str(loc).strip() for loc in locations if str(loc).strip()]
    return [loc.strip() for loc in str(locations).split(",") if loc.strip()]


def _normalize_roles(roles: str | list[str]) -> list[str]:
    """Helper to convert any job profile / tech stack input into clean list."""
    if not roles:
        return ["Software Engineer"]
    if isinstance(roles, list):
        return [str(r).strip() for r in roles if str(r).strip()]
    return [r.strip() for r in str(roles).split(",") if r.strip()]


@mcp.tool()
def search_jobs(
    roles: str = "Software Engineer",
    locations: str = "",
    experience: str = "Any",
    results_wanted: int = 15,
) -> str:
    """
    Search for jobs dynamically across ANY job profile / tech stack, ANY location worldwide, and ANY experience level.

    Args:
        roles: Any job profile, title, or tech stack (e.g., 'React Developer', 'DevOps Engineer', 'Golang', 'Data Scientist', 'Python', 'Product Manager'). Comma-separated for multiple.
        locations: Any city, state, country, or 'Remote' (e.g., 'Mumbai', 'Pune', 'Bangalore', 'London', 'New York', 'Berlin', 'Remote'). Comma-separated for multiple. If empty, searches remote & global openings.
        experience: Experience level filter (e.g., 'Fresher', '0-2 years', '3-5 years', 'Senior', or 'Any').
        results_wanted: Number of job listings to retrieve per role/location.
    """
    role_list = _normalize_roles(roles)
    loc_list = _normalize_locations(locations)

    # If no location specified, search remote/global dynamically
    target_locations = loc_list if loc_list else ["Remote"]

    all_jobs: list[dict[str, Any]] = []
    for role in role_list:
        jobs = fetch_jobs(role, target_locations, results_wanted=results_wanted)
        all_jobs.extend(jobs)

    # Deduplicate by job URL or title+company+location
    seen_keys: set[str] = set()
    unique_jobs: list[dict[str, Any]] = []
    for job in all_jobs:
        url = str(job.get("job_url", "")).strip()
        key = url if (url and url != "N/A") else f"{job.get('title')}|{job.get('company')}|{job.get('location')}"
        if key not in seen_keys:
            seen_keys.add(key)
            unique_jobs.append(job)

    loc_str = locations.strip() if locations.strip() else "Remote / Global"
    query_label = f"{roles} jobs in {loc_str} (Experience: {experience})"
    return format_jobs_with_pipeline(unique_jobs, query_label)


@mcp.tool()
def search_jobs_custom(query: str) -> str:
    """
    Natural language dynamic job search for ANY job profile, ANY location, and ANY experience level.
    Parses any freeform user query without hardcoded constraints or hardcoded default cities.

    Examples:
    - 'Find React developer jobs in Mumbai for 2 years experience'
    - 'Golang microservices backend in Berlin senior'
    - 'Remote DevOps engineer fresher openings'
    - 'Data scientist in London'
    - 'Flutter mobile app developer in Pune'
    - 'Java Spring Boot developer'

    Args:
        query: Freeform job search query mentioning any role, any location, and any experience level.
    """
    # 1. Check if query asks for remote / work from home
    is_remote = bool(re.search(r'\b(?:remote|wfh|work from home|anywhere)\b', query, re.IGNORECASE))

    # 2. Extract location dynamically via preposition patterns ('in Mumbai', 'at London', 'around Pune', 'near Berlin', etc.)
    loc_match = re.search(
        r'\b(?:in|at|around|near|based in|located in)\s+([A-Za-z\s]+?)(?:\s+(?:with|for|as|posted|this|experience|fresher|senior|junior|lead|\d+\+?\s*(?:years?|yrs?))|[^\w\s]|$)',
        query,
        re.IGNORECASE,
    )
    if loc_match:
        extracted_location = re.sub(r'[^A-Za-z\s]', '', loc_match.group(1)).strip()
    elif is_remote:
        extracted_location = "Remote"
    else:
        # Dynamic: no location restricted in query -> global / remote search without pinning to any arbitrary city
        extracted_location = ""

    # 3. Extract experience level dynamically ('fresher', '1-3 years', '5+ yrs', 'senior', 'lead', etc.)
    exp_match = re.search(
        r'\b(\d+\+?(?:-\d+)?\s*(?:years?|yrs?)|fresher|intern(?:ship)?|senior|junior|lead|entry\s*level)\b',
        query,
        re.IGNORECASE,
    )
    extracted_exp = exp_match.group(1).strip() if exp_match else "Any"

    # 4. Clean and isolate the dynamic job profile / role from query
    clean_role = query
    # Strip common query verbs and filler words
    clean_role = re.sub(
        r'\b(?:show|me|all|find|search|get|list|openings?|jobs?|roles?|positions?|looking for|recent|posted|this week)\b',
        '',
        clean_role,
        flags=re.IGNORECASE,
    )
    # Strip preposition + extracted location
    if extracted_location and extracted_location.lower() != "remote":
        clean_role = re.sub(rf'\b(?:in|at|around|near|based in|located in)\s+{re.escape(extracted_location)}\b', '', clean_role, flags=re.IGNORECASE)
        clean_role = re.sub(re.escape(extracted_location), '', clean_role, flags=re.IGNORECASE)
    # Strip remote terms
    clean_role = re.sub(r'\b(?:remote|wfh|work from home|anywhere)\b', '', clean_role, flags=re.IGNORECASE)
    # Strip experience mention or trailing qualifier (e.g. 'for senior engineers', 'with 2 years exp')
    clean_role = re.sub(r'\b(?:with|for)\s+(?:senior|junior|lead|freshers?|interns?|\d+).*$', '', clean_role, flags=re.IGNORECASE)
    if extracted_exp and extracted_exp.lower() != "any":
        clean_role = re.sub(r'\b(?:with|for)\s+' + re.escape(extracted_exp) + r'(?:\s+experience)?\b', '', clean_role, flags=re.IGNORECASE)
        clean_role = re.sub(re.escape(extracted_exp), '', clean_role, flags=re.IGNORECASE)
    clean_role = re.sub(r'\b(?:with|for|experience)\b', '', clean_role, flags=re.IGNORECASE)
    clean_role = re.sub(r'\s+', ' ', clean_role).strip()
    if not clean_role:
        clean_role = query.strip()

    target_locations = [extracted_location] if extracted_location else ["Remote"]
    all_jobs = fetch_jobs(clean_role, target_locations)
    return format_jobs_with_pipeline(all_jobs, query)


@mcp.tool()
def search_all_jobs(
    roles: str = "Software Engineer",
    locations: str = "",
    experience: str = "Any",
    include_naukri: bool = True,
    include_internshala: bool = True,
    query: str | None = None,
) -> str:
    """
    Multi-portal deep search across Indeed, LinkedIn, Naukri, and Internshala.
    Accepts ANY job profile / tech stack, ANY location worldwide, and ANY experience level dynamically.

    Args:
        roles: Any tech stack or job profile (e.g., 'React Developer', 'DevOps', 'Data Analyst', 'Golang')
        locations: Any location worldwide or 'Remote' (e.g., 'Mumbai', 'London', 'Pune', 'Bangalore', 'New York', 'Remote'). Comma-separated for multiple. Leave empty for remote/global.
        experience: Experience level (e.g., 'Fresher', '0-2 years', '3-5 years', 'Senior', or 'Any')
        include_naukri: Whether to query Naukri portal
        include_internshala: Whether to query Internshala portal
        query: Optional custom query label for AI summarization
    """
    role_list = _normalize_roles(roles)
    loc_list = _normalize_locations(locations)
    target_locations = loc_list if loc_list else ["Remote"]

    all_jobs = search_all_portals(
        roles=role_list,
        cities=target_locations,
        include_naukri=include_naukri,
        include_internshala=include_internshala,
        naukri_pages=2,
        internshala_pages=2,
        experience=experience,
    )

    effective_query = query or f"{roles} in {locations or 'Remote / Global'} ({experience})"
    return format_jobs_with_pipeline(all_jobs, effective_query)


@mcp.tool()
def search_fresher_jobs(
    roles: str = "Software Engineer",
    locations: str = "",
) -> str:
    """
    Search specifically for fresher / entry-level openings dynamically across ANY role and ANY location worldwide.

    Args:
        roles: Any job profile or tech stack (e.g., 'Python Developer', 'React', 'Data Analyst', 'DevOps')
        locations: Any location worldwide or 'Remote' (e.g., 'Mumbai', 'Pune', 'Bangalore', 'London', 'Remote')
    """
    return search_jobs(roles=roles, locations=locations, experience="Fresher")


if __name__ == "__main__":
    mcp.run()
