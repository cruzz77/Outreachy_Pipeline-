"""
http_client.py — Shared HTTP session with automatic retry + backoff.
All stages use this instead of raw `requests` calls.
"""

import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.logger import log_warning


def _build_session(total_retries: int = 3, backoff_factor: float = 1.0) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


_session = _build_session()


def get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> requests.Response:
    resp = _session.get(url, headers=headers, params=params, timeout=timeout)
    _handle_rate_limit(resp)
    return resp


def post(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
) -> requests.Response:
    resp = _session.post(url, headers=headers, json=json, timeout=timeout)
    _handle_rate_limit(resp)
    return resp


def _handle_rate_limit(resp: requests.Response) -> None:
    """If the API returns 429, honour the Retry-After header (or wait 60 s)."""
    if resp.status_code == 429:
        wait = int(resp.headers.get("Retry-After", 60))
        log_warning(f"Rate-limited. Waiting {wait}s before continuing…")
        time.sleep(wait)
