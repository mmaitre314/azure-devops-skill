"""Search operations – code, wiki, work items."""

from __future__ import annotations

from typing import Any, Dict, Optional

from . import client


def search_code(
    search_text: str,
    *,
    project: Optional[str] = None,
    repository: Optional[str] = None,
    branch: Optional[str] = None,
    path: Optional[str] = None,
    top: Optional[int] = None,
    skip: Optional[int] = None,
) -> Any:
    """Search code across repositories."""
    body: Dict[str, Any] = {"searchText": search_text, "$top": top or 25, "$skip": skip or 0}
    filters: Dict[str, list] = {}
    if project:
        filters["Project"] = [project]
    if repository:
        filters["Repository"] = [repository]
    if branch:
        filters["Branch"] = [branch]
    if path:
        filters["Path"] = [path]
    if filters:
        body["filters"] = filters
    return client.post(
        "_apis/search/codesearchresults",
        json_body=body,
        area="almsearch.dev.azure.com",
    )


def search_wiki(
    search_text: str,
    *,
    project: Optional[str] = None,
    wiki: Optional[str] = None,
    top: Optional[int] = None,
    skip: Optional[int] = None,
) -> Any:
    """Search wiki pages."""
    body: Dict[str, Any] = {"searchText": search_text, "$top": top or 25, "$skip": skip or 0}
    filters: Dict[str, list] = {}
    if project:
        filters["Project"] = [project]
    if wiki:
        filters["Wiki"] = [wiki]
    if filters:
        body["filters"] = filters
    return client.post(
        "_apis/search/wikisearchresults",
        json_body=body,
        area="almsearch.dev.azure.com",
    )


def search_work_items(
    search_text: str,
    *,
    project: Optional[str] = None,
    work_item_type: Optional[str] = None,
    state: Optional[str] = None,
    assigned_to: Optional[str] = None,
    area_path: Optional[str] = None,
    top: Optional[int] = None,
    skip: Optional[int] = None,
) -> Any:
    """Search work items."""
    body: Dict[str, Any] = {"searchText": search_text, "$top": top or 25, "$skip": skip or 0}
    filters: Dict[str, list] = {}
    if project:
        filters["Project"] = [project]
    if work_item_type:
        filters["Work Item Type"] = [work_item_type]
    if state:
        filters["State"] = [state]
    if assigned_to:
        filters["Assigned To"] = [assigned_to]
    if area_path:
        filters["Area Path"] = [area_path]
    if filters:
        body["filters"] = filters
    return client.post(
        "_apis/search/workitemsearchresults",
        json_body=body,
        area="almsearch.dev.azure.com",
    )
