"""
pipeline.py — Orchestrator: wires all four stages end-to-end.

Usage:
    python pipeline.py <seed_domain>

Example:
    python pipeline.py stripe.com
"""

import sys

from rich.table import Table

from src import config
from src.logger import console, log_info, log_success, log_warning, log_error, log_stage
from src.stages.stage1_ocean    import find_lookalikes
from src.stages.stage2_prospeo  import find_decision_makers
from src.stages.stage3_eazyreach import resolve_emails
from src.stages.stage4_brevo    import send_outreach


# ─────────────────────────────────────────────────────────────────────────────

def run(seed_domain: str) -> None:
    console.rule(f"[bold blue]Outreach Pipeline · seed: {seed_domain}[/bold blue]")

    # ── Stage 1 ──────────────────────────────────────────────────────────────
    log_stage(1, "Ocean.io — Lookalike Companies")
    companies = find_lookalikes(seed_domain)

    if not companies:
        log_error("No lookalike companies found. Aborting.")
        sys.exit(1)

    # ── Stage 2 ──────────────────────────────────────────────────────────────
    log_stage(2, "Prospeo — Decision-Makers")
    contacts = find_decision_makers(companies)

    if not contacts:
        log_error("No decision-makers found. Aborting.")
        sys.exit(1)

    # ── Stage 3 ──────────────────────────────────────────────────────────────
    log_stage(3, "Eazyreach — Email Resolution")
    contacts = resolve_emails(contacts)

    if not contacts:
        log_error("No emails could be resolved. Aborting.")
        sys.exit(1)

    # ── Safety Checkpoint ────────────────────────────────────────────────────
    console.rule("[bold yellow]⚠  Safety Checkpoint — Review Before Sending[/bold yellow]")
    _print_summary(contacts)

    if config.DRY_RUN:
        log_warning("DRY_RUN=true — emails will NOT actually be sent.")
    else:
        console.print(
            f"\n[bold]About to send [green]{len(contacts)}[/green] email(s).[/bold]  "
            "Type [bold green]yes[/bold green] to confirm, anything else to abort: ",
            end="",
        )
        answer = input().strip().lower()
        if answer != "yes":
            log_warning("Aborted by user. No emails sent.")
            sys.exit(0)

    # ── Stage 4 ──────────────────────────────────────────────────────────────
    log_stage(4, "Brevo — Outreach Emails")
    records = send_outreach(contacts)

    # ── Final Report ─────────────────────────────────────────────────────────
    console.rule("[bold blue]Pipeline Complete[/bold blue]")
    sent   = sum(1 for r in records if r.email_sent)
    failed = len(records) - sent

    log_success(f"Emails sent    : {sent}")
    if failed:
        log_warning(f"Failed / skipped: {failed}")

    for r in records:
        if not r.email_sent:
            log_warning(f"  ✘ {r.contact.email} — {r.send_error or 'unknown error'}")


# ─────────────────────────────────────────────────────────────────────────────

def _print_summary(contacts) -> None:
    """Pretty-print a table of contacts that will receive emails."""
    table = Table(
        title="Contacts to be emailed",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name",    style="bold white", no_wrap=True)
    table.add_column("Title",   style="white")
    table.add_column("Company", style="cyan")
    table.add_column("Email",   style="green")

    for c in contacts:
        table.add_row(
            f"{c.first_name} {c.last_name}",
            c.title,
            c.company.name or c.company.domain,
            c.email or "—",
        )

    console.print(table)
    console.print()


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) != 2:
        console.print(
            "[bold red]Usage:[/bold red]  python pipeline.py [bold]<seed_domain>[/bold]\n"
            "Example: python pipeline.py stripe.com"
        )
        sys.exit(1)

    seed = sys.argv[1].strip().lower().removeprefix("https://").removeprefix("http://").rstrip("/")

    try:
        run(seed)
    except EnvironmentError as exc:
        log_error(str(exc))
        sys.exit(1)
    except KeyboardInterrupt:
        log_warning("\nInterrupted by user.")
        sys.exit(0)
