"""Core operations – projects, teams, identities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import client


def list_projects(
    *,
    top: Optional[int] = None,
    skip: Optional[int] = None,
    state_filter: Optional[str] = None,
    name_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List all projects in the organization."""
    params: Dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    if skip is not None:
        params["$skip"] = skip
    if state_filter:
        params["stateFilter"] = state_filter
    if name_filter:
        params["projectNameFilter"] = name_filter
    return client.get_all("_apis/projects", params=params)


def list_project_teams(
    project: str,
    *,
    top: Optional[int] = None,
    skip: Optional[int] = None,
    mine: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """List teams within a project."""
    params: Dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    if skip is not None:
        params["$skip"] = skip
    if mine is not None:
        params["$mine"] = str(mine).lower()
    return client.get_all(f"_apis/projects/{project}/teams", params=params)


def get_identity_ids(search_filter: str) -> Any:
    """Look up identity IDs by search filter (e.g. display name or email)."""
    return client.get(
        "_apis/identities",
        params={"searchFilter": "General", "filterValue": search_filter},
        area="vssps.dev.azure.com",
    )
