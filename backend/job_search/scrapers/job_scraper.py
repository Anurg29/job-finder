from jobspy import scrape_jobs


def fetch_jobs(
    role: str,
    locations: list[str],
    site_names: list[str] | None = None,
    results_wanted: int = 10,
    hours_old: int = 72,
) -> list[dict]:
    if site_names is None:
        site_names = ["indeed", "linkedin"]

    all_jobs = []

    for location in locations:
        try:
            # Remove ", India" suffix if present for jobspy
            clean_location = location.replace(", India", "").strip()
            
            jobs = scrape_jobs(
                site_name=site_names,
                search_term=role,
                location=clean_location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                country_indeed="India",
            )

            for _, row in jobs.iterrows():
                all_jobs.append({
                    "title": row.get("title", "N/A"),
                    "company": row.get("company", "N/A"),
                    "location": row.get("location", location),
                    "date_posted": str(row.get("date_posted", "N/A")),
                    "job_url": row.get("job_url", "N/A"),
                    "source": row.get("site", "jobspy"),
                    "description": str(row.get("description", ""))[:500],  # trim
                    "min_exp": row.get("min_amount", "Fresher"),
                })
        except Exception as e:
            print(f"Error scraping {location}: {e}")

    return all_jobs
