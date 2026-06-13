"""
stage4_brevo.py — Send personalized outreach emails via Brevo (Sendinblue).

Input : list[Contact]  (email filled)
Output: list[OutreachRecord]  (email_sent=True/False per contact)

Brevo API docs: https://developers.brevo.com/reference/sendtransacemail
Auth  : api-key header
"""

from typing import List

from src import config
from src.logger import log_info, log_success, log_warning, log_error
from src.models import Contact, OutreachRecord
from src.utils import http_client

_SEND_URL = "https://api.brevo.com/v3/smtp/email"


def send_outreach(contacts: List[Contact]) -> List[OutreachRecord]:
    """
    Send one personalized email to each contact.
    Returns a list of OutreachRecord with send status per contact.
    """
    records: List[OutreachRecord] = []

    for contact in contacts:
        record = _send_one(contact)
        records.append(record)

    sent  = sum(1 for r in records if r.email_sent)
    total = len(records)
    log_success(f"Brevo › {sent}/{total} email(s) dispatched successfully.")
    return records


def _send_one(contact: Contact) -> OutreachRecord:
    record = OutreachRecord(contact=contact)

    subject, html_body = _compose_email(contact)

    if config.DRY_RUN:
        log_info(f"  [DRY RUN] Would send to {contact.email} — skipping actual send.")
        record.email_sent = True   # treat dry-run as "sent" for reporting
        return record

    headers = {
        "api-key": config.BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "sender": {
            "name":  config.BREVO_SENDER_NAME,
            "email": config.BREVO_SENDER_EMAIL,
        },
        "to": [
            {
                "email": contact.email,
                "name":  f"{contact.first_name} {contact.last_name}".strip(),
            }
        ],
        "subject": subject,
        "htmlContent": html_body,
    }

    log_info(f"  Brevo › sending to {contact.email} ({contact.first_name} {contact.last_name})")

    try:
        resp = http_client.post(_SEND_URL, headers=headers, json=payload)
    except Exception as exc:
        log_error(f"    Brevo request failed: {exc}")
        record.send_error = str(exc)
        return record

    if resp.status_code in (200, 201):
        log_success(f"    ✔ Sent to {contact.email}")
        record.email_sent = True
    else:
        msg = f"Status {resp.status_code}: {resp.text[:200]}"
        log_warning(f"    ✘ Failed for {contact.email} — {msg}")
        record.send_error = msg

    return record


def _compose_email(contact: Contact) -> tuple[str, str]:
    """
    Returns (subject, html_body) personalized for this contact.
    Edit the copy here — the pipeline wires everything else automatically.
    """
    first   = contact.first_name or "there"
    company = contact.company.name or contact.company.domain
    title   = contact.title or "your role"

    subject = f"Quick question, {first} — streamlining outreach at {company}?"

    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; font-size: 15px; color: #222; max-width: 600px;">

<p>Hi {first},</p>

<p>
  I came across {company} and noticed the team is doing impressive work.
  Given your position as <strong>{title}</strong>, I wanted to reach out directly.
</p>

<p>
  We help growth-focused teams automate their outbound motion — finding the right
  prospects, surfacing verified contacts, and delivering personalized emails at
  scale. Most teams we work with cut manual prospecting time by 80 % in the first
  month.
</p>

<p>
  Would a 15-minute call this week make sense? I'd love to show you what we've
  built for companies similar to {company}.
</p>

<p>
  Happy to find a slot that works for you — just reply here.
</p>

<p>
  Best,<br/>
  <strong>{config.BREVO_SENDER_NAME}</strong><br/>
  <a href="mailto:{config.BREVO_SENDER_EMAIL}">{config.BREVO_SENDER_EMAIL}</a>
</p>

<p style="font-size:11px; color:#999;">
  If this isn't relevant, just let me know and I won't reach out again.
</p>

</body>
</html>
"""
    return subject, html_body
