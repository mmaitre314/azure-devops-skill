"""
Low-level HTTP client for Azure DevOps REST API.

All read-only operations go through this module. Handles authentication,
base URL construction, pagination, and error reporting.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

from . import auth

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEFAULT_API_VERSION = "7.2-preview"
_DEFAULT_TIMEOUT = 60  # seconds
_SEARCH_TIMEOUT = 120  # search endpoints are notoriously slow
_MAX_RETRIES = 2
_RETRY_BACKOFF = 2  # seconds, doubles each retry

_org_url: str | None = None


def set_org(org: str) -> None:
    """Set the ADO organization. Called once from CLI before any request."""
    global _org_url
    if org.startswith("https://"):
        _org_url = org.rstrip("/")
    else:
        _org_url = f"https://dev.azure.com/{org}"


def _org() -> str:
    if not _org_url:
        raise RuntimeError("Organization not set. Pass --org to the CLI.")
    return _org_url


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _headers() -> Dict[str, str]:
    token = auth.get_token()
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def _build_url(path: str, *, project: Optional[str] = None, area: str = "dev.azure.com") -> str:
    """Build full REST URL.

    `area` controls the subdomain:
      - "dev.azure.com"    → normal APIs
      - "vsrm.dev.azure.com"  → release management
      - "almsearch.dev.azure.com" → search
      - "vssps.dev.azure.com"     → identity / profile
    """
    org_url = _org()

    if area != "dev.azure.com":
        # Replace dev.azure.com with the subdomain variant
        org_url = org_url.replace("dev.azure.com", area)

    if project:
        return f"{org_url}/{quote(project, safe='')}/{path}"
    return f"{org_url}/{path}"


# ---------------------------------------------------------------------------
# Public request helpers
# ---------------------------------------------------------------------------


def _timeout_for_area(area: str) -> int:
    """Return the appropriate timeout for the given API area."""
    if "search" in area:
        return _SEARCH_TIMEOUT
    return _DEFAULT_TIMEOUT


def _request_with_retry(
    method: str,
    url: str,
    *,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
    timeout: int = _DEFAULT_TIMEOUT,
) -> requests.Response:
    """Issue an HTTP request with automatic retry on transient failures."""
    last_exc: Optional[Exception] = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            if method == "GET":
                resp = requests.get(url, headers=headers, params=params, timeout=timeout)
            else:
                resp = requests.post(url, headers=headers, params=params, json=json_body, timeout=timeout)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < _MAX_RETRIES:
                wait = _RETRY_BACKOFF * (2 ** attempt)
                print(f"[retry] HTTP {resp.status_code} on {method} {url}, waiting {wait}s (attempt {attempt + 1}/{_MAX_RETRIES + 1})", file=sys.stderr)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                wait = _RETRY_BACKOFF * (2 ** attempt)
                print(f"[retry] {type(exc).__name__} on {method} {url}, waiting {wait}s (attempt {attempt + 1}/{_MAX_RETRIES + 1})", file=sys.stderr)
                time.sleep(wait)
            else:
                raise
    raise last_exc  # should not reach here, but satisfy type checker


def get(
    path: str,
    *,
    project: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    api_version: str = _DEFAULT_API_VERSION,
    area: str = "dev.azure.com",
) -> Any:
    """Issue an authenticated GET and return the JSON body."""
    url = _build_url(path, project=project, area=area)
    p: Dict[str, Any] = {"api-version": api_version}
    if params:
        p.update(params)
    resp = _request_with_retry("GET", url, headers=_headers(), params=p, timeout=_timeout_for_area(area))
    content_type = resp.headers.get("Content-Type", "")
    if "application/json" in content_type:
        return resp.json()
    return resp.text


def post(
    path: str,
    *,
    project: Optional[str] = None,
    json_body: Optional[Any] = None,
    params: Optional[Dict[str, Any]] = None,
    api_version: str = _DEFAULT_API_VERSION,
    area: str = "dev.azure.com",
) -> Any:
    """Issue an authenticated POST (used for search / batch-read endpoints)."""
    url = _build_url(path, project=project, area=area)
    p: Dict[str, Any] = {"api-version": api_version}
    if params:
        p.update(params)
    hdrs = _headers()
    hdrs["Content-Type"] = "application/json"
    resp = _request_with_retry("POST", url, headers=hdrs, params=p, json_body=json_body, timeout=_timeout_for_area(area))
    content_type = resp.headers.get("Content-Type", "")
    if "application/json" in content_type:
        return resp.json()
    return resp.text


def get_text(
    path: str,
    *,
    project: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    api_version: str = _DEFAULT_API_VERSION,
    area: str = "dev.azure.com",
) -> str:
    """Issue an authenticated GET expecting a plain-text response."""
    url = _build_url(path, project=project, area=area)
    p: Dict[str, Any] = {"api-version": api_version}
    if params:
        p.update(params)
    hdrs = _headers()
    hdrs["Accept"] = "text/plain"
    resp = _request_with_retry("GET", url, headers=hdrs, params=p, timeout=_timeout_for_area(area))
    return resp.text


def get_all(
    path: str,
    *,
    project: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    api_version: str = _DEFAULT_API_VERSION,
    area: str = "dev.azure.com",
    max_pages: int = 20,
) -> List[Any]:
    """GET with continuation-token–based pagination.  Returns all items."""
    all_items: List[Any] = []
    p = dict(params or {})
    for _ in range(max_pages):
        data = get(path, project=project, params=p, api_version=api_version, area=area)
        if isinstance(data, dict):
            all_items.extend(data.get("value", []))
            ct = data.get("continuationToken") or data.get("x-ms-continuationtoken")
            if not ct:
                break
            p["continuationToken"] = ct
        else:
            break
    return all_items


# ---------------------------------------------------------------------------
# Output helper – used by CLI
# ---------------------------------------------------------------------------


_output_file: str | None = None


def set_output_file(path: str | None) -> None:
    """Set an optional file path for output (instead of stdout)."""
    global _output_file
    _output_file = path


def output(data: Any) -> None:
    """Pretty-print JSON to stdout or to the configured output file."""
    if _output_file:
        import pathlib
        pathlib.Path(_output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(_output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
            f.write("\n")
        print(f"Output written to {_output_file}")
    else:
        json.dump(data, sys.stdout, indent=2, default=str)
        print()


def output_text(text: str) -> None:
    """Write raw text to stdout or to the configured output file."""
    if _output_file:
        import pathlib
        pathlib.Path(_output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(_output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Output written to {_output_file}")
    else:
        print(text)
