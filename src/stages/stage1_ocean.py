"""
stage1_ocean.py — Find lookalike companies using Ocean.io.
Falls back to mock data if API access is restricted.
"""

from typing import List

from src import config
from src.logger import log_info, log_success, log_warning, log_error
from src.models import Company
from src.utils import http_client

_PREVIEW_URL = "https://api.ocean.io/v3/search/companies/preview"


def find_lookalikes(seed_domain: str) -> List[Company]:
    log_info(f"Querying Ocean.io for companies similar to: {seed_domain}")

    headers = {
        "x-api-token": config.OCEAN_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "size": config.MAX_LOOKALIKES,
        "companiesFilters": {
            "lookalikeDomains": [seed_domain],
        },
    }

    try:
        resp = http_client.post(_PREVIEW_URL, headers=headers, json=payload)
    except Exception as exc:
        log_error(f"Ocean.io request failed: {exc}")
        return _mock_fallback(seed_domain)

    if resp.status_code in (401, 403):
        log_warning(f"Ocean.io: access restricted ({resp.status_code}) — using mock data to continue pipeline.")
        return _mock_fallback(seed_domain)

    if not resp.ok:
        log_error(f"Ocean.io: status {resp.status_code} — {resp.text[:400]}")
        return _mock_fallback(seed_domain)

    data = resp.json()
    raw = (
        data.get("companies")
        or data.get("data")
        or data.get("results")
        or []
    )

    if not raw:
        log_warning(f"Ocean.io returned 0 results — using mock data.")
        return _mock_fallback(seed_domain)

    companies: List[Company] = []
    seen: set = set()
    for item in raw:
        domain = (item.get("domain") or item.get("website") or "").strip().lower()
        name   = (item.get("name") or item.get("companyName") or "").strip()
        if domain and domain not in seen and domain != seed_domain:
            seen.add(domain)
            companies.append(Company(domain=domain, name=name))

    log_success(f"Ocean.io returned {len(companies)} lookalike companies.")
    return companies


def _mock_fallback(seed_domain: str) -> List[Company]:
    """
    Mock lookalike companies for testing when API access is restricted.
    Replace with real Ocean.io data once API access is granted.
    """
    log_warning("Using mock company data — replace with live Ocean.io once API access is granted.")
    mocks = {
        "stripe.com":  [
            Company(domain="braintreepayments.com", name="Braintree"),
            Company(domain="adyen.com",             name="Adyen"),
            Company(domain="square.com",            name="Square"),
        ],
        "notion.so":   [
            Company(domain="coda.io",    name="Coda"),
            Company(domain="airtable.com", name="Airtable"),
        ],
    }
    fallback = [
        Company(domain="hubspot.com",    name="HubSpot"),
        Company(domain="salesforce.com", name="Salesforce"),
        Company(domain="pipedrive.com",  name="Pipedrive"),
    ]
    companies = mocks.get(seed_domain, fallback)
    log_success(f"Mock: {len(companies)} lookalike companies loaded.")
    return companies