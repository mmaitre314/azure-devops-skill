"""Work / iteration operations – read-only."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import client


def list_iterations(
    project: str,
    *,
    depth: Optional[int] = None,
) -> Any:
    """List all iterations (sprints) in a project."""
    params: Dict[str, Any] = {}
    if depth is not None:
        params["$depth"] = depth
    return client.get(
        "_apis/wit/classificationnodes/iterations",
        project=project,
        params=params,
    )


def list_team_iterations(
    project: str,
    team: str,
    *,
    timeframe: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List iterations assigned to a team."""
    params: Dict[str, Any] = {}
    if timeframe:
        params["$timeframe"] = timeframe
    data = client.get(
        "_apis/work/teamsettings/iterations",
        project=f"{project}/{team}",
        params=params,
    )
    return data.get("value", []) if isinstance(data, dict) else data


def get_iteration_capacities(
    project: str, iteration_id: str
) -> Any:
    """Get capacity for all teams in an iteration."""
    return client.get(
        f"_apis/work/teamsettings/iterations/{iteration_id}/capacities",
        project=project,
    )


def get_team_capacity(
    project: str, team: str, iteration_id: str
) -> Any:
    """Get capacity for a specific team in an iteration."""
    return client.get(
        f"_apis/work/teamsettings/iterations/{iteration_id}/capacities",
        project=f"{project}/{team}",
    )
