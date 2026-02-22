"""Advanced Security operations – alerts (read-only)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import client


def get_alerts(
    project: str,
    repository: str,
    *,
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    states: Optional[str] = None,
    confidence_levels: str = "high",
    ref: Optional[str] = None,
    top: Optional[int] = None,
    only_default_branch: Optional[bool] = None,
) -> Any:
    """Retrieve Advanced Security alerts for a repository."""
    params: Dict[str, Any] = {"criteria.confidenceLevels": confidence_levels}
    if alert_type:
        params["criteria.alertType"] = alert_type
    if severity:
        params["criteria.severities"] = severity
    if states:
        params["criteria.states"] = states
    if ref:
        params["criteria.ref"] = ref
    if top is not None:
        params["$top"] = top
    if only_default_branch is not None:
        params["criteria.onlyDefaultBranch"] = str(only_default_branch).lower()
    return client.get(
        f"_apis/alert/repositories/{repository}/alerts",
        project=project,
        params=params,
    )


def get_alert_details(
    project: str,
    repository: str,
    alert_id: int,
    *,
    ref: Optional[str] = None,
) -> Dict[str, Any]:
    """Get detailed information about a specific security alert."""
    params: Dict[str, Any] = {}
    if ref:
        params["ref"] = ref
    return client.get(
        f"_apis/alert/repositories/{repository}/alerts/{alert_id}",
        project=project,
        params=params,
    )
