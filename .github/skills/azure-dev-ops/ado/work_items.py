"""Work item operations – get, batch, comments, revisions, queries."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import client


def get_work_item(
    project: str,
    work_item_id: int,
    *,
    fields: Optional[str] = None,
    expand: Optional[str] = None,
    as_of: Optional[str] = None,
) -> Dict[str, Any]:
    """Get a single work item by ID."""
    params: Dict[str, Any] = {}
    if fields:
        params["fields"] = fields
    if expand:
        params["$expand"] = expand
    if as_of:
        params["asOf"] = as_of
    return client.get(f"_apis/wit/workitems/{work_item_id}", project=project, params=params)


def get_work_items_batch(
    project: str,
    ids: List[int],
    *,
    fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Retrieve multiple work items by IDs (batch)."""
    body: Dict[str, Any] = {"ids": ids}
    if fields:
        body["fields"] = fields
    data = client.post("_apis/wit/workitemsbatch", project=project, json_body=body)
    return data.get("value", []) if isinstance(data, dict) else data


def list_comments(
    project: str,
    work_item_id: int,
    *,
    top: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """List comments on a work item."""
    params: Dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    data = client.get(
        f"_apis/wit/workitems/{work_item_id}/comments",
        project=project,
        params=params,
    )
    return data.get("comments", []) if isinstance(data, dict) else data


def list_revisions(
    project: str,
    work_item_id: int,
    *,
    top: Optional[int] = None,
    skip: Optional[int] = None,
    expand: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get revision history of a work item."""
    params: Dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    if skip is not None:
        params["$skip"] = skip
    if expand:
        params["$expand"] = expand
    data = client.get(
        f"_apis/wit/workitems/{work_item_id}/revisions",
        project=project,
        params=params,
    )
    return data.get("value", []) if isinstance(data, dict) else data


def get_work_item_type(project: str, type_name: str) -> Dict[str, Any]:
    """Get details of a work item type."""
    return client.get(
        f"_apis/wit/workitemtypes/{type_name}",
        project=project,
    )


def my_work_items(
    project: str,
    *,
    type_filter: Optional[str] = None,
    top: Optional[int] = None,
    include_completed: bool = False,
) -> List[Dict[str, Any]]:
    """List work items assigned to the authenticated user via WIQL."""
    wiql = "SELECT [System.Id] FROM WorkItems WHERE [System.AssignedTo] = @Me"
    if type_filter:
        wiql += f" AND [System.WorkItemType] = '{type_filter}'"
    if not include_completed:
        wiql += " AND [System.State] <> 'Closed' AND [System.State] <> 'Done' AND [System.State] <> 'Removed'"
    wiql += " ORDER BY [System.ChangedDate] DESC"

    result = client.post(
        "_apis/wit/wiql",
        project=project,
        json_body={"query": wiql},
        params={"$top": top or 50},
    )
    items = result.get("workItems", [])
    if not items:
        return []
    ids = [it["id"] for it in items[: top or 50]]
    return get_work_items_batch(project, ids)


def run_wiql(
    project: str,
    query: str,
    *,
    top: Optional[int] = None,
    team: Optional[str] = None,
) -> Any:
    """Execute a WIQL query and return results."""
    params: Dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    if team:
        params["team"] = team
    return client.post(
        "_apis/wit/wiql",
        project=project,
        json_body={"query": query},
        params=params,
    )


def get_query(
    project: str,
    query_id_or_path: str,
    *,
    depth: Optional[int] = None,
    expand: Optional[str] = None,
) -> Dict[str, Any]:
    """Get a saved query by ID or path."""
    params: Dict[str, Any] = {}
    if depth is not None:
        params["$depth"] = depth
    if expand:
        params["$expand"] = expand
    return client.get(
        f"_apis/wit/queries/{query_id_or_path}",
        project=project,
        params=params,
    )


def get_query_results(
    query_id: str,
    *,
    project: Optional[str] = None,
    top: Optional[int] = None,
    team: Optional[str] = None,
) -> Any:
    """Execute a saved query by ID and return results."""
    params: Dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    if team:
        params["team"] = team
    return client.post(
        f"_apis/wit/wiql/{query_id}",
        project=project,
        json_body={},
        params=params,
    )


def get_work_items_for_iteration(
    project: str,
    iteration_id: str,
    *,
    team: Optional[str] = None,
) -> Any:
    """Get work items in a specific iteration."""
    team_segment = f"{project}/{team}" if team else project
    return client.get(
        f"_apis/work/teamsettings/iterations/{iteration_id}/workitems",
        project=team_segment,
    )


def list_backlogs(project: str, team: str) -> List[Dict[str, Any]]:
    """List backlogs for a team."""
    data = client.get(
        "_apis/work/backlogs",
        project=f"{project}/{team}",
    )
    return data.get("value", []) if isinstance(data, dict) else data


def list_backlog_work_items(
    project: str, team: str, backlog_id: str
) -> Any:
    """Get work items in a specific backlog."""
    return client.get(
        f"_apis/work/backlogs/{backlog_id}/workItems",
        project=f"{project}/{team}",
    )
