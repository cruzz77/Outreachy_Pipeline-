"""
stage3_eazyreach.py — Resolve LinkedIn profile URLs → verified work emails.

Input : list[Contact]  (linkedin_url filled, email = None)
Output: list[Contact]  (email filled where resolved; contacts without
                        a verified email are dropped)

Eazyreach API docs: https://eazyreach.app/api-docs
Auth  : Authorization: Bearer <key>
"""

from typing import List

from src import config
from src.logger import log_info, log_success, log_warning, log_error
from src.models import Contact
from src.utils import http_client

_BASE_URL = "https://api.eazyreach.app/v1"


def resolve_emails(contacts: List[Contact]) -> List[Contact]:
    """
    For each Contact with a LinkedIn URL, call Eazyreach to get the
    verified work email. Contacts where resolution fails are dropped.
    Returns only contacts that have a confirmed email.
    """
    resolved: List[Contact] = []

    for contact in contacts:
        email = _resolve_one(contact)
        if email:
            contact.email = email
            resolved.append(contact)

    log_success(
        f"Eazyreach resolved {len(resolved)}/{len(contacts)} email(s)."
    )
    return resolved


def _resolve_one(contact: Contact) -> str:
    """Returns a verified email string, or '' on failure."""
    log_info(f"  Eazyreach › resolving {contact.first_name} {contact.last_name} "
             f"@ {contact.company.domain}")

    headers = {
        "Authorization": f"Bearer {config.EAZYREACH_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {"linkedin_url": contact.linkedin_url}

    try:
        resp = http_client.post(
            f"{_BASE_URL}/email-finder",
            headers=headers,
            json=payload,
        )
    except Exception as exc:
        log_error(f"    Eazyreach request failed: {exc}")
        return ""

    if resp.status_code == 401:
        log_error("    Eazyreach: invalid API key (401). Check EAZYREACH_API_KEY in .env.")
        return ""

    if resp.status_code == 402:
        log_error("    Eazyreach: out of credits (402). Top up and retry.")
        return ""

    if resp.status_code == 404:
        log_warning(f"    Eazyreach: could not find email for {contact.linkedin_url}")
        return ""

    if not resp.ok:
        log_warning(f"    Eazyreach: status {resp.status_code} — skipping.")
        return ""

    data = resp.json()

    # Eazyreach may return {"email": "..."} or {"data": {"email": "..."}}
    email = (
        data.get("email")
        or data.get("data", {}).get("email")
        or ""
    ).strip().lower()

    # Basic sanity check — must look like an email
    if "@" not in email or "." not in email.split("@")[-1]:
        log_warning(f"    Eazyreach returned malformed email '{email}' — skipping.")
        return ""

    log_info(f"    → {email}")
    return email
