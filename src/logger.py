"""
logger.py — Shared Rich console and helper log functions.
Import `console` or the helpers anywhere in the pipeline.
"""

from rich.console import Console
from rich.theme import Theme

_theme = Theme(
    {
        "info":    "cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error":   "bold red",
        "stage":   "bold magenta",
        "data":    "dim white",
    }
)

console = Console(theme=_theme)


def log_info(msg: str) -> None:
    console.print(f"[info]  ℹ  {msg}[/info]")


def log_success(msg: str) -> None:
    console.print(f"[success]  ✔  {msg}[/success]")


def log_warning(msg: str) -> None:
    console.print(f"[warning]  ⚠  {msg}[/warning]")


def log_error(msg: str) -> None:
    console.print(f"[error]  ✖  {msg}[/error]")


def log_stage(n: int, name: str) -> None:
    console.rule(f"[stage]Stage {n} · {name}[/stage]")
