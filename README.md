# Automated Outreach Pipeline

A fully automated cold-outreach engine. One domain in — outreach emails out. Zero manual steps in between.

```
python pipeline.py stripe.com
```

---

## How it works

```
[Human] seed domain
    │
    ▼
[Stage 1] Ocean.io       →  lookalike company domains
    │
    ▼
[Stage 2] Prospeo        →  C-suite / VP contacts + LinkedIn URLs
    │
    ▼
[Stage 3] Eazyreach      →  verified work emails
    │
    ▼  ← safety checkpoint (shows table, asks for confirmation)
    │
    ▼
[Stage 4] Brevo          →  personalized outreach emails sent
```

---

## Setup

### 1. Clone & install dependencies

```bash
git clone https://github.com/cruzz77/Outreachy_Pipeline-
cd outreach-pipeline
pip install -r requirements.txt
```

### 2. Get your API keys

| Tool      | Signup                       | Notes                                      |
|-----------|------------------------------|--------------------------------------------|
| Ocean.io  | https://ocean.io             | Requires company email (get a domain first)|
| Prospeo   | https://app.prospeo.io/api   | Free tier available                        |
| Eazyreach | https://eazyreach.app        | Credits provided by the team               |
| Brevo     | https://app.brevo.com        | Free tier: 300 emails/day                  |

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your API keys and sender details
```

### 4. Run

```bash
python pipeline.py <seed_domain>

# Examples:
python pipeline.py stripe.com
python pipeline.py notion.so

# Dry run (skips actual email send):
DRY_RUN=true python pipeline.py stripe.com
```

---

## Configuration (`.env`)

| Variable                 | Description                                      | Default |
|--------------------------|--------------------------------------------------|---------|
| `OCEAN_API_KEY`          | Ocean.io API key                                 | required|
| `PROSPEO_API_KEY`        | Prospeo API key                                  | required|
| `EAZYREACH_API_KEY`      | Eazyreach API key                                | required|
| `BREVO_API_KEY`          | Brevo (Sendinblue) API key                       | required|
| `BREVO_SENDER_NAME`      | Your name shown in outreach emails               | required|
| `BREVO_SENDER_EMAIL`     | Your verified sender email                       | required|
| `MAX_LOOKALIKES`         | Max companies to fetch from Ocean.io             | 10      |
| `MAX_CONTACTS_PER_COMPANY` | Max decision-makers per company               | 3       |
| `DRY_RUN`                | `true` = skip actual email send                  | false   |

---

## Project structure

```
outreach-pipeline/
├── pipeline.py              # Entry point & orchestrator
├── requirements.txt
├── .env.example
└── src/
    ├── config.py            # Env loading & validation
    ├── logger.py            # Rich-based pretty logging
    ├── models.py            # Shared dataclasses (Company, Contact, OutreachRecord)
    ├── stages/
    │   ├── stage1_ocean.py      # Lookalike company discovery
    │   ├── stage2_prospeo.py    # Decision-maker surfacing
    │   ├── stage3_eazyreach.py  # LinkedIn → email resolution
    │   └── stage4_brevo.py      # Personalized email dispatch
    └── utils/
        └── http_client.py   # Shared session with retry / rate-limit handling
```

---

## Safety checkpoint

Before any emails fire, the pipeline pauses and shows a table of every contact and their email. You type **yes** to confirm. Set `DRY_RUN=true` to skip the send entirely (useful for testing the first three stages).

---

## Resilience built-in

- **Retries**: 3 automatic retries with exponential backoff on 429/5xx
- **Rate limits**: Honours `Retry-After` headers
- **Partial failures**: Missing contacts / unresolved emails are skipped, not crashes
- **Deduplication**: Domains and contacts de-duplicated before any API call
- **Validation**: Malformed emails are dropped before reaching Brevo
