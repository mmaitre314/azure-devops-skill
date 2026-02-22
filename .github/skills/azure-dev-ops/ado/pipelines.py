"""Pipeline / build operations – read-only."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import client


def get_builds(
    project: str,
    *,
    definitions: Optional[str] = None,
    branch_name: Optional[str] = None,
    status_filter: Optional[str] = None,
    result_filter: Optional[str] = None,
    requested_for: Optional[str] = None,
    top: Optional[int] = None,
    max_time: Optional[str] = None,
    min_time: Optional[str] = None,
    repository_id: Optional[str] = None,
    build_number: Optional[str] = None,
    tag_filters: Optional[str] = None,
    query_order: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List builds with optional filters."""
    params: Dict[str, Any] = {}
    if definitions:
        params["definitions"] = definitions
    if branch_name:
        params["branchName"] = branch_name
    if status_filter:
        params["statusFilter"] = status_filter
    if result_filter:
        params["resultFilter"] = result_filter
    if requested_for:
        params["requestedFor"] = requested_for
    if top is not None:
        params["$top"] = top
    if max_time:
        params["maxTime"] = max_time
    if min_time:
        params["minTime"] = min_time
    if repository_id:
        params["repositoryId"] = repository_id
    if build_number:
        params["buildNumber"] = build_number
    if tag_filters:
        params["tagFilters"] = tag_filters
    if query_order:
        params["queryOrder"] = query_order
    return client.get_all("_apis/build/builds", project=project, params=params)


def get_build(project: str, build_id: int) -> Dict[str, Any]:
    """Get build status / details."""
    return client.get(f"_apis/build/builds/{build_id}", project=project)


def get_build_log(project: str, build_id: int) -> Any:
    """Get list of log files for a build."""
    return client.get(f"_apis/build/builds/{build_id}/logs", project=project)


def get_build_log_by_id(
    project: str,
    build_id: int,
    log_id: int,
    *,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> str:
    """Get a specific build log content."""
    params: Dict[str, Any] = {}
    if start_line is not None:
        params["startLine"] = start_line
    if end_line is not None:
        params["endLine"] = end_line
    return client.get_text(
        f"_apis/build/builds/{build_id}/logs/{log_id}",
        project=project,
        params=params,
    )


def get_build_changes(
    project: str, build_id: int, *, top: Optional[int] = None
) -> Any:
    """Get commits/changes associated with a build."""
    params: Dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    return client.get(
        f"_apis/build/builds/{build_id}/changes",
        project=project,
        params=params,
    )


def get_build_definitions(
    project: str,
    *,
    name: Optional[str] = None,
    path: Optional[str] = None,
    top: Optional[int] = None,
    include_latest_builds: Optional[bool] = None,
    repository_id: Optional[str] = None,
    repository_type: Optional[str] = None,
    yaml_filename: Optional[str] = None,
    query_order: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List build/pipeline definitions."""
    params: Dict[str, Any] = {}
    if name:
        params["name"] = name
    if path:
        params["path"] = path
    if top is not None:
        params["$top"] = top
    if include_latest_builds is not None:
        params["includeLatestBuilds"] = str(include_latest_builds).lower()
    if repository_id:
        params["repositoryId"] = repository_id
    if repository_type:
        params["repositoryType"] = repository_type
    if yaml_filename:
        params["yamlFilename"] = yaml_filename
    if query_order:
        params["queryOrder"] = query_order
    return client.get_all("_apis/build/definitions", project=project, params=params)


def get_build_definition_revisions(
    project: str, definition_id: int
) -> Any:
    """Get revision history of a build definition."""
    return client.get(
        f"_apis/build/definitions/{definition_id}/revisions",
        project=project,
    )


def get_pipeline_run(
    project: str, pipeline_id: int, run_id: int
) -> Dict[str, Any]:
    """Get details of a specific pipeline run."""
    return client.get(
        f"_apis/pipelines/{pipeline_id}/runs/{run_id}",
        project=project,
    )


def list_pipeline_runs(
    project: str, pipeline_id: int
) -> List[Dict[str, Any]]:
    """List recent runs for a pipeline."""
    data = client.get(
        f"_apis/pipelines/{pipeline_id}/runs",
        project=project,
    )
    return data.get("value", []) if isinstance(data, dict) else data


def list_artifacts(project: str, build_id: int) -> List[Dict[str, Any]]:
    """List artifacts produced by a build."""
    data = client.get(
        f"_apis/build/builds/{build_id}/artifacts",
        project=project,
    )
    return data.get("value", []) if isinstance(data, dict) else data


def get_build_timeline(project: str, build_id: int) -> Any:
    """Get the timeline (stages, jobs, tasks) for a build."""
    return client.get(
        f"_apis/build/builds/{build_id}/timeline",
        project=project,
    )
