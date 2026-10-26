"""Read public company-level Greenhouse / Lever job listings without private keys."""
from __future__ import annotations
import re
from datetime import datetime, timezone
import requests

from core import clean_text, deadline_from_description, infer_contract, normalize_job, safe_url

SAFE_SLUG = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$")
USER_AGENT = "CareerCollective-Demo/1.0 (educational project; public company postings)"


def _validate_slug(slug: str) -> str:
    slug = (slug or "").strip()
    if not SAFE_SLUG.fullmatch(slug):
        raise ValueError("Use a valid company board identifier, not an entire URL.")
    return slug


def _fetch_json(url: str, params: dict | None = None):
    response = requests.get(url, params=params, timeout=12, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    response.raise_for_status()
    return response.json()


def fetch_greenhouse(slug: str, max_items=250) -> list[dict]:
    slug = _validate_slug(slug)
    payload = _fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", {"content": "true"})
    items = payload.get("jobs", [])
    if not isinstance(items, list):
        raise ValueError("Unexpected Greenhouse response.")
    checked = datetime.now(timezone.utc).date().isoformat()
    jobs = []
    for raw in items[:max_items]:
        title = clean_text(raw.get("title", ""))
        desc = clean_text(raw.get("content", ""))
        city = clean_text((raw.get("location") or {}).get("name", ""))
        contract = infer_contract(title, desc)
        jobs.append(normalize_job({
            "id": f"greenhouse:{slug}:{raw.get('id')}", "title": title,
            "company": slug.replace("-", " ").title(), "city": city,
            "contract": contract, "sector": "Other", "description": desc,
            "skills": "", "language": raw.get("language", ""),
            "deadline": deadline_from_description(desc),
            "url": safe_url(raw.get("absolute_url", "")),
            "source": f"Greenhouse · {slug}", "source_type": "Live feed",
            "last_checked": checked, "feed_status": "Listed on latest refresh",
        }))
    return jobs


def fetch_lever(slug: str, region: str = "global", max_items=250) -> list[dict]:
    slug = _validate_slug(slug)
    if region not in ("global", "eu"):
        raise ValueError("Lever region must be global or eu.")
    base = "https://api.eu.lever.co" if region == "eu" else "https://api.lever.co"
    payload = _fetch_json(f"{base}/v0/postings/{slug}", {"mode": "json", "limit": max_items})
    if not isinstance(payload, list):
        raise ValueError("Unexpected Lever response.")
    checked = datetime.now(timezone.utc).date().isoformat()
    jobs = []
    for raw in payload[:max_items]:
        categories = raw.get("categories") or {}
        title = clean_text(raw.get("text", ""))
        desc = clean_text(raw.get("descriptionPlain", "") or raw.get("description", ""))
        category = clean_text(categories.get("commitment", ""))
        city = clean_text(categories.get("location", ""))
        team = clean_text(categories.get("team", ""))
        jobs.append(normalize_job({
            "id": f"lever:{region}:{slug}:{raw.get('id')}", "title": title,
            "company": slug.replace("-", " ").title(), "city": city,
            "contract": infer_contract(title, desc, category), "sector": team or "Other",
            "description": desc, "skills": "", "language": "",
            "deadline": deadline_from_description(desc),
            "url": safe_url(raw.get("hostedUrl", "")), "source": f"Lever · {slug}",
            "source_type": "Live feed", "last_checked": checked,
            "feed_status": "Listed on latest refresh",
        }))
    return jobs


def monitored_status(tracked_job: dict, new_jobs: list[dict], source_checked: bool) -> str:
    """No claim that a missing posting is conclusively closed."""
    if not source_checked:
        return "Not checked"
    urls = {j.get("url") for j in new_jobs if j.get("url")}
    ids = {j.get("id") for j in new_jobs}
    return ("Still listed" if tracked_job.get("job_id") in ids or (tracked_job.get("url") and tracked_job.get("url") in urls)
            else "Not found in latest feed  -  verify at source")


# Curated employers with publicly readable recruitment APIs. These identifiers are
# independently verifiable via their employer-hosted job board URLs. They are
# sources, not a guarantee that any particular vacancy remains available.
FEATURED_BOARDS = [
    ("Lever", "vestiairecollective", "Vestiaire Collective"),
    ("Lever", "bigblue", "Bigblue"),
    ("Lever", "cheerz", "Cheerz"),
    ("Lever", "scaleway", "Scaleway"),
    ("Lever", "ekimetrics", "Ekimetrics"),
    ("Lever", "c12qe", "C12 Quantum Electronics"),
    ("Greenhouse", "aircallioinc", "Aircall"),
    ("Greenhouse", "mirakl", "Mirakl"),
]

# Only treat a role as France-based when the published location gives adequate
# evidence. Ambiguous locations are NOT presented as France-based matches.
FRANCE_LOCATIONS = (
    "france", "paris", "lyon", "bordeaux", "lille", "nantes", "toulouse",
    "marseille", "strasbourg", "nice", "rennes", "montpellier", "grenoble",
    "rouen", "dijon", "cergy", "boulogne", "levallois", "neuilly",
    "courbevoie", "puteaux", "saint-denis", "la défense", "suresnes",
    "aix-en-provence", "île-de-france", "ile-de-france",
)


def france_location(location: str) -> bool:
    value = clean_text(location).casefold()
    return bool(value) and any(x in value for x in FRANCE_LOCATIONS)


def student_opportunity(job: dict) -> bool:
    """Stay conservative: identify explicit internships/apprenticeships only."""
    if job.get("contract") not in ("Internship", "Apprenticeship"):
        return False
    # A generic boilerplate sentence in a long description is not enough.
    title = (job.get("title") or "").casefold()
    return bool(re.search(r"stage|stagiaire|intern|alternan|apprenti|apprentice|trainee|work[ -]study", title)) or (
        job.get("contract") == "Apprenticeship" and "apprentice" in (job.get("description") or "").lower()[:250]
    ) or (job.get("contract") == "Internship" and "internship" in (job.get("description") or "").lower()[:200])


def fetch_featured_jobs() -> tuple[list[dict], list[str], int]:
    """Query a small fixed list of public employer boards. No scraping/login.

    Failures are reported explicitly and do not prevent other sources loading.
    Returned results are published public postings filtered for France and students.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def one_board(config):
        provider, slug, display_name = config
        results = fetch_greenhouse(slug) if provider == "Greenhouse" else fetch_lever(slug)
        relevant = []
        for job in results:
            if france_location(job.get("city", "")) and student_opportunity(job):
                job["company"] = display_name
                relevant.append(job)
        return relevant

    matching, errors, successful = [], [], 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        tasks = {pool.submit(one_board, board): board for board in FEATURED_BOARDS}
        for task in as_completed(tasks):
            board = tasks[task]
            try:
                matching.extend(task.result())
                successful += 1
            except Exception as exc:
                errors.append(f"{board[2]} ({type(exc).__name__})")
    return matching, sorted(errors), successful