import re
import time
from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager


def _slug(value: str) -> str:
    return value.strip().lower().replace(" ", "-")


def scrape_naukri(
    role: str,
    location: str,
    pages: int = 2,
    headless: bool = True,
    use_stealth: bool = True,
    experience: int | str | None = None,
) -> list[dict[str, Any]]:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    if use_stealth:
        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL",
            fix_hairline=True,
        )

    jobs: list[dict[str, Any]] = []

    # Parse dynamic experience parameter
    exp_param = ""
    if experience is not None:
        exp_str = str(experience).strip().lower()
        if exp_str in ["fresher", "0", "entry"]:
            exp_param = "&experience=0"
        else:
            numbers = re.findall(r"\d+", exp_str)
            if numbers:
                exp_param = f"&experience={numbers[0]}"

    try:
        role_slug = _slug(role)
        city_slug = _slug(location)

        for page in range(1, pages + 1):
            url = (
                f"https://www.naukri.com/{role_slug}-jobs-in-{city_slug}"
                f"?pageNo={page}{exp_param}"
            )
            driver.get(url)
            time.sleep(3)

            cards = driver.find_elements(By.CLASS_NAME, "srp-jobtuple-wrapper")
            if not cards:
                cards = driver.find_elements(By.CLASS_NAME, "jobTuple")

            for card in cards:
                try:
                    title_el = card.find_element(By.CSS_SELECTOR, "a.title")
                    title = title_el.text.strip()
                    link = title_el.get_attribute("href")

                    company = "N/A"
                    location_text = location

                    company_nodes = card.find_elements(By.CSS_SELECTOR, "a.comp-name")
                    if company_nodes:
                        company = company_nodes[0].text.strip()

                    location_nodes = card.find_elements(By.CSS_SELECTOR, "span.locWdth")
                    if location_nodes:
                        location_text = location_nodes[0].text.strip()

                    jobs.append(
                        {
                            "title": title or "N/A",
                            "company": company or "N/A",
                            "location": location_text or location,
                            "date_posted": "Recent",
                            "job_url": link or "N/A",
                            "source": "naukri",
                            "description": "",
                            "min_exp": str(experience or "Dynamic"),
                        }
                    )
                except Exception:
                    continue
    finally:
        driver.quit()

    return jobs
