"""
stage2_prospeo.py — Find decision-makers (C-suite / VP) via Prospeo.

Input : list[Company]
Output: list[Contact]  (LinkedIn URL filled; email = None yet)

Prospeo API docs: https://prospeo.io/api
Auth  : X-KEY header
"""

from typing import List

from src import config
from src.logger import log_info, log_success, log_warning, log_error
from src.models import Company, Contact
from src.utils import http_client

_BASE_URL = "https://api.prospeo.io"

# Seniority levels we care about
_TARGET_SENIORITY = {"c_suite", "vp", "director", "owner", "partner", "founder"}


def find_decision_makers(companies: List[Company]) -> List[Contact]:
    """
    For each company domain, call Prospeo to surface senior contacts.
    Returns a flat list[Contact] across all companies.
    """
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
        "company_domain": company.domain,
        "limit": config.MAX_CONTACTS_PER_COMPANY,
        "seniority_level": list(_TARGET_SENIORITY),   # filter server-side where supported
    }

    try:
        resp = http_client.post(
            f"{_BASE_URL}/domain-search",
            headers=headers,
            json=payload,
        )
    except Exception as exc:
        log_error(f"  Prospeo request failed for {company.domain}: {exc}")
        return []

    if resp.status_code == 401:
        log_error("  Prospeo: invalid API key (401). Check PROSPEO_API_KEY in .env.")
        return []

    if resp.status_code == 404:
        log_warning(f"  Prospeo: no results for {company.domain}")
        return []

    if not resp.ok:
        log_warning(f"  Prospeo: status {resp.status_code} for {company.domain} — skipping.")
        return []

    data = resp.json()

    # Prospeo may wrap under "response" or return "contacts" directly
    raw_list = (
        data.get("response", {}).get("contacts")
        or data.get("contacts")
        or []
    )

    contacts: List[Contact] = []
    for person in raw_list[: config.MAX_CONTACTS_PER_COMPANY]:
        seniority = (person.get("seniority_level") or "").lower()

        # If the API didn't filter server-side, do it client-side
        if seniority and not any(s in seniority for s in _TARGET_SENIORITY):
            continue

        linkedin = (
            person.get("linkedin_url")
            or person.get("linkedin")
            or ""
        ).strip()

        if not linkedin:
            log_warning(f"    Skipping {person.get('first_name', '?')} — no LinkedIn URL.")
            continue

        contacts.append(
            Contact(
                company=company,
                first_name=person.get("first_name", ""),
                last_name=person.get("last_name", ""),
                title=person.get("title") or person.get("job_title") or "",
                linkedin_url=linkedin,
            )
        )

    log_info(f"    → {len(contacts)} decision-maker(s) found for {company.domain}")
    return contacts
