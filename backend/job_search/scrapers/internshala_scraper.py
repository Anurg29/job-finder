import json
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def _slug(value: str) -> str:
    return value.strip().lower().replace(" ", "-")


def _candidate_urls(role: str, city: str, page: int) -> list[str]:
    role_slug = _slug(role)
    city_slug = _slug(city)

    page_suffix = "" if page <= 1 else f"/page-{page}"
    return [
        f"https://internshala.com/jobs/{role_slug}-jobs-in-{city_slug}{page_suffix}",
        f"https://internshala.com/jobs/keywords-{role_slug}/location-{city_slug}{page_suffix}",
        f"https://internshala.com/jobs/{role_slug}-jobs{page_suffix}",
    ]


def _extract_from_json_ld(
    soup: BeautifulSoup, source_url: str, fallback_city: str
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})

    for script in scripts:
        text = script.string or script.get_text() or ""
        if not text.strip():
            continue
        try:
            payload = json.loads(text)
        except Exception:
            continue

        objects: list[Any]
        if isinstance(payload, list):
            objects = payload
        else:
            objects = [payload]

        for item in objects:
            if not isinstance(item, dict):
                continue
            kind = item.get("@type")
            if kind != "JobPosting":
                continue

            org = item.get("hiringOrganization")
            if isinstance(org, dict):
                company = org.get("name", "N/A")
            else:
                company = "N/A"

            loc = fallback_city
            job_location = item.get("jobLocation")
            if isinstance(job_location, dict):
                address = job_location.get("address", {})
                if isinstance(address, dict):
                    loc = (
                        address.get("addressLocality")
                        or address.get("addressRegion")
                        or fallback_city
                    )

            jobs.append(
                {
                    "title": item.get("title", "N/A"),
                    "company": company,
                    "location": loc,
                    "date_posted": str(item.get("datePosted", "N/A")),
                    "job_url": item.get("url", source_url),
                    "source": "internshala",
                    "description": str(item.get("description", ""))[:500],
                    "min_exp": "Fresher",
                }
            )

    return jobs


def _extract_from_html(
    soup: BeautifulSoup, source_url: str, fallback_city: str
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    anchors = soup.select("a[href*='/job/detail/']")

    for anchor in anchors:
        href = anchor.get("href", "")
        title = anchor.get_text(strip=True) or "N/A"

        container = anchor.find_parent("div")
        company = "N/A"
        if container:
            company_node = container.select_one(".company_name, .company-name, h4")
            if company_node:
                company = company_node.get_text(strip=True) or "N/A"

        jobs.append(
            {
                "title": title,
                "company": company,
                "location": fallback_city,
                "date_posted": "N/A",
                "job_url": urljoin(source_url, href),
                "source": "internshala",
                "description": "",
                "min_exp": "Fresher",
            }
        )

    return jobs


def scrape_internshala(role: str, location: str, pages: int = 2) -> list[dict[str, Any]]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        )
    }

    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for page in range(1, pages + 1):
        page_jobs: list[dict[str, Any]] = []
        for url in _candidate_urls(role=role, city=location, page=page):
            try:
                response = requests.get(url, headers=headers, timeout=20)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                page_jobs = _extract_from_json_ld(soup, url, location)
                if not page_jobs:
                    page_jobs = _extract_from_html(soup, url, location)
                if page_jobs:
                    break
            except Exception:
                continue

        for job in page_jobs:
            job_url = str(job.get("job_url", "")).strip()
            if not job_url or job_url == "N/A" or job_url in seen_urls:
                continue
            seen_urls.add(job_url)
            results.append(job)

    return results
