from typing import Any
from jobspy import scrape_jobs


def _detect_country(location: str) -> str:
    """Detect country for JobSpy based on location query."""
    loc_lower = location.lower()
    if any(k in loc_lower for k in ["usa", "united states", "new york", "san francisco", "california", "texas"]):
        return "USA"
    if any(k in loc_lower for k in ["uk", "united kingdom", "london", "manchester"]):
        return "UK"
    if any(k in loc_lower for k in ["canada", "toronto", "vancouver"]):
        return "Canada"
    if any(k in loc_lower for k in ["australia", "sydney", "melbourne"]):
        return "Australia"
    if any(k in loc_lower for k in ["germany", "berlin", "munich"]):
        return "Germany"
    if any(k in loc_lower for k in ["singapore"]):
        return "Singapore"
    # Default to India
    return "India"


def fetch_jobs(
    role: str,
    locations: list[str],
    site_names: list[str] | None = None,
    results_wanted: int = 15,
    hours_old: int = 120,
) -> list[dict[str, Any]]:
    if site_names is None:
        site_names = ["indeed", "linkedin"]

    all_jobs: list[dict[str, Any]] = []

    for location in locations:
        clean_location = location.strip()
        country = _detect_country(clean_location)

        try:
            # Scrape jobs dynamically for any role and any location
            jobs = scrape_jobs(
                site_name=site_names,
                search_term=role,
                location=clean_location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                country_indeed=country,
            )

            for _, row in jobs.iterrows():
                all_jobs.append(
                    {
                        "title": row.get("title", "N/A"),
                        "company": row.get("company", "N/A"),
                        "location": row.get("location") or clean_location,
                        "date_posted": str(row.get("date_posted", "Recent")),
                        "job_url": row.get("job_url", "N/A"),
                        "source": row.get("site", "jobspy"),
                        "description": str(row.get("description", ""))[:500],
                        "min_exp": str(row.get("job_type") or "All Levels"),
                    }
                )
        except Exception as e:
            print(f"[JobSpy] Error scraping role='{role}' in location='{clean_location}': {e}")

    return all_jobs
