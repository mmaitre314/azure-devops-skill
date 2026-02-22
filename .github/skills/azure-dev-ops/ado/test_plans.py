"""Test plan operations – read-only."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import client


def list_test_plans(
    project: str,
    *,
    filter_active: Optional[bool] = None,
    include_plan_details: Optional[bool] = None,
    continuation_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List test plans in a project."""
    params: Dict[str, Any] = {}
    if filter_active is not None:
        params["filterActivePlans"] = str(filter_active).lower()
    if include_plan_details is not None:
        params["includePlanDetails"] = str(include_plan_details).lower()
    if continuation_token:
        params["continuationToken"] = continuation_token
    data = client.get("_apis/testplan/plans", project=project, params=params)
    return data.get("value", []) if isinstance(data, dict) else data


def list_test_suites(
    project: str,
    plan_id: int,
    *,
    continuation_token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List test suites in a test plan."""
    params: Dict[str, Any] = {}
    if continuation_token:
        params["continuationToken"] = continuation_token
    data = client.get(
        f"_apis/testplan/plans/{plan_id}/suites",
        project=project,
        params=params,
    )
    return data.get("value", []) if isinstance(data, dict) else data


def list_test_cases(
    project: str, plan_id: int, suite_id: int
) -> List[Dict[str, Any]]:
    """List test cases in a test suite."""
    data = client.get(
        f"_apis/testplan/plans/{plan_id}/suites/{suite_id}/testcase",
        project=project,
    )
    return data.get("value", []) if isinstance(data, dict) else data


def get_test_results_by_build(
    project: str, build_id: int
) -> List[Dict[str, Any]]:
    """Get test results for a specific build."""
    data = client.get(
        "_apis/test/runs",
        project=project,
        params={"buildUri": f"vstfs:///Build/Build/{build_id}"},
    )
    runs = data.get("value", []) if isinstance(data, dict) else data
    all_results: List[Dict[str, Any]] = []
    for run in runs:
        results = client.get(
            f"_apis/test/runs/{run['id']}/results",
            project=project,
        )
        run_results = results.get("value", []) if isinstance(results, dict) else results
        for r in run_results:
            r["runName"] = run.get("name")
        all_results.extend(run_results)
    return all_results
