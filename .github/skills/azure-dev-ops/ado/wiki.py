"""Wiki operations – list, pages, content (read-only)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import client


def list_wikis(*, project: Optional[str] = None) -> List[Dict[str, Any]]:
    """List wikis in the organization or a specific project."""
    data = client.get("_apis/wiki/wikis", project=project)
    return data.get("value", []) if isinstance(data, dict) else data


def get_wiki(wiki_id: str, *, project: Optional[str] = None) -> Dict[str, Any]:
    """Get details of a specific wiki."""
    return client.get(f"_apis/wiki/wikis/{wiki_id}", project=project)


def list_pages(
    project: str,
    wiki_id: str,
    *,
    top: Optional[int] = None,
    continuation_token: Optional[str] = None,
    page_views_for_days: Optional[int] = None,
) -> Any:
    """List pages in a wiki."""
    params: Dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    if continuation_token:
        params["continuationToken"] = continuation_token
    if page_views_for_days is not None:
        params["pageViewsForDays"] = page_views_for_days
    return client.get(
        f"_apis/wiki/wikis/{wiki_id}/pagesbatch",
        project=project,
        params=params,
    )


def get_page(
    project: str,
    wiki_id: str,
    path: str,
    *,
    recursion_level: Optional[str] = None,
) -> Dict[str, Any]:
    """Get wiki page metadata (without content)."""
    params: Dict[str, Any] = {"path": path}
    if recursion_level:
        params["recursionLevel"] = recursion_level
    return client.get(
        f"_apis/wiki/wikis/{wiki_id}/pages",
        project=project,
        params=params,
    )


def get_page_content(
    project: str,
    wiki_id: str,
    path: str,
) -> str:
    """Retrieve wiki page content as text."""
    return client.get_text(
        f"_apis/wiki/wikis/{wiki_id}/pages",
        project=project,
        params={"path": path, "includeContent": "true"},
    )
