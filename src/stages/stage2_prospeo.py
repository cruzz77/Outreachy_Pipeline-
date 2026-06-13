"""
stage2_prospeo.py — Find decision-makers (C-suite / VP) via Prospeo.

Input : list[Company]
Output: list[Contact]

API: POST https://api.prospeo.io/search-person
Auth: X-KEY header
"""

from typing import List

from src import config
from src.logger import log_info, log_success, log_warning, log_error
from src.models import Company, Contact
from src.utils import http_client

_SEARCH_URL = "https://api.prospeo.io/search-person"

_TARGET_SENIORITIES = ["C-Suite", "Vice President", "Director", "Founder/Owner", "Partner"]


def find_decision_makers(companies: List[Company]) -> List[Contact]:
    all_contacts: List[Contact] = []
    for company in companies:
        contacts = _fetch_for_domain(company)
        all_contacts.extend(contacts)

    log_success(
        f"Prospeo resolved {len(all_contacts)} decision-maker(s) "
        f"across {len(companies)} company/companies."
    )
    return all_contacts


def _fetch_for_domain(company: Company) -> List[Contact]:
    log_info(f"  Prospeo › fetching contacts for {company.domain}")

    headers = {
        "X-KEY": config.PROSPEO_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "page": 1,
        "filters": {
            "company": {
                "websites": {
                    "include": [company.domain]
                }
            },
            "person_seniority": {
                "include": _TARGET_SENIORITIES
            },
            "max_person_per_company": config.MAX_CONTACTS_PER_COMPANY,
        }
    }

    try:
        resp = http_client.post(_SEARCH_URL, headers=headers, json=payload)
    except Exception as exc:
        log_error(f"  Prospeo request failed for {company.domain}: {exc}")
        return []

    if resp.status_code == 401:
        log_error("  Prospeo: invalid API key (401). Check PROSPEO_API_KEY in .env.")
        return []

    if not resp.ok:
        log_warning(f"  Prospeo: status {resp.status_code} for {company.domain} — {resp.text[:200]}")
        return []

    data = resp.json()

    if data.get("error"):
        log_warning(f"  Prospeo error: {data.get('error_code')} — {data.get('filter_error', '')}")
        return []

    results = data.get("results") or []
    contacts: List[Contact] = []

    for result in results[: config.MAX_CONTACTS_PER_COMPANY]:
        person = result.get("person") or result
        first = person.get("first_name") or ""
        last  = person.get("last_name")  or ""
        title = person.get("current_job_title") or person.get("job_title") or ""
        linkedin = (person.get("linkedin_url") or "").strip()

        if not linkedin:
            log_warning(f"    Skipping {first} {last} — no LinkedIn URL.")
            continue

        contacts.append(Contact(
            company=company,
            first_name=first,
            last_name=last,
            title=title,
            linkedin_url=linkedin,
        ))

    log_info(f"    → {len(contacts)} decision-maker(s) found for {company.domain}")
    return contacts