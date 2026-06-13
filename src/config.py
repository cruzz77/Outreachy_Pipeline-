"""
config.py — Load and validate all environment variables.
Fail fast at startup if anything critical is missing.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise EnvironmentError(
            f"Missing required environment variable: {key}\n"
            f"Copy .env.example → .env and fill in your API keys."
        )
    return val


# ── API Keys ──────────────────────────────────────────────
OCEAN_API_KEY      = _require("OCEAN_API_KEY")
PROSPEO_API_KEY    = _require("PROSPEO_API_KEY")
EAZYREACH_API_KEY  = _require("EAZYREACH_API_KEY")
BREVO_API_KEY      = _require("BREVO_API_KEY")

# ── Brevo sender identity ─────────────────────────────────
BREVO_SENDER_NAME  = _require("BREVO_SENDER_NAME")
BREVO_SENDER_EMAIL = _require("BREVO_SENDER_EMAIL")

# ── Pipeline tuning ───────────────────────────────────────
MAX_LOOKALIKES            = int(os.getenv("MAX_LOOKALIKES", "10"))
MAX_CONTACTS_PER_COMPANY  = int(os.getenv("MAX_CONTACTS_PER_COMPANY", "3"))
DRY_RUN                   = os.getenv("DRY_RUN", "false").lower() == "true"
