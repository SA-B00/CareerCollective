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
            else "Not found in latest feed — verify at source")