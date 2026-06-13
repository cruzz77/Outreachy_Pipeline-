"""
stage1_ocean.py — Find lookalike companies using Ocean.io.

Input : seed domain (str)
Output: list[Company]

Ocean.io API docs: https://api.ocean.io/
Auth  : X-API-KEY header
"""

from typing import List

from src import config
from src.logger import log_info, log_success, log_warning, log_error
from src.models import Company
from src.utils import http_client

_BASE_URL = "https://api.ocean.io/v1"


def find_lookalikes(seed_domain: str) -> List[Company]:
    """
    Call Ocean.io /companies/lookalikes with the seed domain.
    Returns up to config.MAX_LOOKALIKES Company objects.
    """
    log_info(f"Querying Ocean.io for companies similar to: {seed_domain}")

    headers = {
        "X-API-KEY": config.OCEAN_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "domain": seed_domain,
        "limit": config.MAX_LOOKALIKES,
    }

    try:
        resp = http_client.post(
            f"{_BASE_URL}/companies/lookalikes",
            headers=headers,
            json=payload,
        )
    except Exception as exc:
        log_error(f"Ocean.io request failed: {exc}")
        return []

    if resp.status_code == 401:
        log_error("Ocean.io: invalid API key (401). Check OCEAN_API_KEY in .env.")
        return []

    if resp.status_code == 404:
        log_warning(f"Ocean.io: seed domain '{seed_domain}' not found (404). Try a larger company domain.")
        return []

    if not resp.ok:
        log_error(f"Ocean.io: unexpected status {resp.status_code} — {resp.text[:300]}")
        return []

    data = resp.json()

    # Ocean.io returns {"companies": [...]} or {"data": {"companies": [...]}}
    raw_companies = (
        data.get("companies")
        or data.get("data", {}).get("companies")
        or []
    )

    companies: List[Company] = []
    for item in raw_companies:
        domain = (item.get("domain") or "").strip().lower()
        name   = (item.get("name") or item.get("company_name") or "").strip()
        if domain:
            companies.append(Company(domain=domain, name=name))

    # De-duplicate by domain (shouldn't happen, but just in case)
    seen: set = set()
    unique: List[Company] = []
    for c in companies:
        if c.domain not in seen:
            seen.add(c.domain)
            unique.append(c)

    log_success(f"Ocean.io returned {len(unique)} lookalike companies.")
    return unique
