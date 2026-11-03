from typing import Any

from job_search.scrapers.internshala_scraper import scrape_internshala
from job_search.scrapers.job_scraper import fetch_jobs
from job_search.scrapers.naukri_scraper import scrape_naukri


def _dedupe_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []

    for job in jobs:
        key = str(job.get("job_url", "")).strip()
        if not key or key == "N/A":
            key = (
                f"{job.get('title', '')}|"
                f"{job.get('company', '')}|"
                f"{job.get('location', '')}"
            )
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)

    return unique


def search_all_portals(
    roles: list[str],
    cities: list[str],
    include_naukri: bool = True,
    include_internshala: bool = True,
    naukri_pages: int = 2,
    internshala_pages: int = 2,
) -> list[dict[str, Any]]:
    all_jobs: list[dict[str, Any]] = []

    for role in roles:
        for city in cities:
            location = city if city.lower().endswith("india") else f"{city}, India"

            print(f"[Scraper] Fetching jobs for {role} in {location}")
            try:
                source_jobs = fetch_jobs(
                    role=role,
                    locations=[location],
                    site_names=["indeed", "linkedin"],
                    results_wanted=20,
                    hours_old=72,
                )
                print(f"[Scraper] Found {len(source_jobs)} jobs from JobSpy")
                all_jobs.extend(source_jobs)
            except Exception as exc:
                print(f"[Scraper] JobSpy error for {role} in {location}: {exc}")

            if include_naukri:
                print(f"[Scraper] Fetching Naukri jobs for {role} in {city}")
                try:
                    naukri_jobs = scrape_naukri(role=role, location=city, pages=naukri_pages)
                    print(f"[Scraper] Found {len(naukri_jobs)} jobs from Naukri")
                    all_jobs.extend(naukri_jobs)
                except Exception as exc:
                    print(f"[Scraper] Naukri error for {role} in {city}: {exc}")

            if include_internshala:
                print(f"[Scraper] Fetching Internshala jobs for {role} in {city}")
                try:
                    internshala_jobs = scrape_internshala(
                        role=role, location=city, pages=internshala_pages
                    )
                    print(f"[Scraper] Found {len(internshala_jobs)} jobs from Internshala")
                    all_jobs.extend(internshala_jobs)
                except Exception as exc:
                    print(f"[Scraper] Internshala error for {role} in {city}: {exc}")

    print(f"[Scraper] Total jobs found before deduplication: {len(all_jobs)}")
    unique_jobs = _dedupe_jobs(all_jobs)
    print(f"[Scraper] Total unique jobs after deduplication: {len(unique_jobs)}")
    return unique_jobs
