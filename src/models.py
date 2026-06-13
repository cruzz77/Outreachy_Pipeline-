"""
models.py — Shared data models passed between pipeline stages.
Each stage consumes and/or produces these objects.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Company:
    """Output of Stage 1 (Ocean.io). Input to Stage 2 (Prospeo)."""
    domain: str
    name: str = ""


@dataclass
class Contact:
    """Output of Stage 2 (Prospeo). Input to Stage 3 (Eazyreach)."""
    company: Company
    first_name: str
    last_name: str
    title: str
    linkedin_url: str
    email: Optional[str] = None       # filled in by Stage 3


@dataclass
class OutreachRecord:
    """Fully resolved record — output of Stage 3, input to Stage 4."""
    contact: Contact
    email_sent: bool = False
    send_error: str = ""
