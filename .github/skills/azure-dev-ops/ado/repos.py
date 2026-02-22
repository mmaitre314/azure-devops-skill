"""Repository operations – repos, branches, commits, PRs, file content, diffs."""

from __future__ import annotations

import os
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from . import client


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------


def list_repos(project: str, *, top: Optional[int] = None, name_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all Git repositories in a project."""
    params: Dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    if name_filter:
        params["$filter"] = f"contains(name, '{name_filter}')"
    return client.get_all("_apis/git/repositories", project=project, params=params)


def get_repo(project: str, repo: str) -> Dict[str, Any]:
    """Get repository details by name or ID."""
    return client.get(f"_apis/git/repositories/{quote(repo, safe='')}", project=project)


# ---------------------------------------------------------------------------
# Branches
# ---------------------------------------------------------------------------


def list_branches(
    project: str,
    repo: str,
    *,
    filter_contains: Optional[str] = None,
    top: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """List branches in a repository."""
    params: Dict[str, Any] = {}
    if filter_contains:
        params["filterContains"] = filter_contains
    if top is not None:
        params["$top"] = top
    data = client.get(f"_apis/git/repositories/{quote(repo, safe='')}/refs", project=project, params={**params, "filter": "heads/"})
    return data.get("value", []) if isinstance(data, dict) else data


def get_branch(project: str, repo: str, branch_name: str) -> Any:
    """Get details for a specific branch."""
    # The refs endpoint with an exact filter
    name = branch_name.removeprefix("refs/heads/")
    data = client.get(
        f"_apis/git/repositories/{quote(repo, safe='')}/refs",
        project=project,
        params={"filter": f"heads/{name}", "filterContains": name},
    )
    values = data.get("value", []) if isinstance(data, dict) else []
    return values[0] if values else None


# ---------------------------------------------------------------------------
# Commits
# ---------------------------------------------------------------------------


def search_commits(
    project: str,
    repo: str,
    *,
    author: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    search_text: Optional[str] = None,
    top: Optional[int] = None,
    skip: Optional[int] = None,
    branch: Optional[str] = None,
    include_work_items: Optional[bool] = None,
) -> Any:
    """Search commits with filters."""
    body: Dict[str, Any] = {}
    if author:
        body["author"] = author
    if from_date:
        body["fromDate"] = from_date
    if to_date:
        body["toDate"] = to_date
    if search_text:
        body["searchText"] = search_text
    if branch:
        body["itemVersion"] = {"version": branch.removeprefix("refs/heads/")}
    if include_work_items is not None:
        body["includeWorkItems"] = include_work_items

    params: Dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    if skip is not None:
        params["$skip"] = skip

    return client.post(
        f"_apis/git/repositories/{quote(repo, safe='')}/commitsbatch",
        project=project,
        json_body=body,
        params=params,
    )


def get_commit(project: str, repo: str, commit_id: str) -> Dict[str, Any]:
    """Get a single commit by ID."""
    return client.get(
        f"_apis/git/repositories/{quote(repo, safe='')}/commits/{commit_id}",
        project=project,
    )


def get_commit_changes(project: str, repo: str, commit_id: str, *, top: Optional[int] = None, skip: Optional[int] = None) -> Any:
    """Get changes (diffs) introduced by a commit."""
    params: Dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    if skip is not None:
        params["$skip"] = skip
    return client.get(
        f"_apis/git/repositories/{quote(repo, safe='')}/commits/{commit_id}/changes",
        project=project,
        params=params,
    )


# ---------------------------------------------------------------------------
# Pull Requests
# ---------------------------------------------------------------------------


def list_pull_requests(
    project: str,
    *,
    repo: Optional[str] = None,
    status: Optional[str] = None,
    source_branch: Optional[str] = None,
    target_branch: Optional[str] = None,
    creator_id: Optional[str] = None,
    reviewer_id: Optional[str] = None,
    top: Optional[int] = None,
    skip: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """List pull requests (by repo or project-wide)."""
    params: Dict[str, Any] = {}
    if status:
        params["searchCriteria.status"] = status
    if source_branch:
        params["searchCriteria.sourceRefName"] = source_branch
    if target_branch:
        params["searchCriteria.targetRefName"] = target_branch
    if creator_id:
        params["searchCriteria.creatorId"] = creator_id
    if reviewer_id:
        params["searchCriteria.reviewerId"] = reviewer_id
    if top is not None:
        params["$top"] = top
    if skip is not None:
        params["$skip"] = skip

    if repo:
        path = f"_apis/git/repositories/{quote(repo, safe='')}/pullrequests"
    else:
        path = "_apis/git/pullrequests"
    return client.get_all(path, project=project, params=params)


def get_pull_request(project: str, repo: str, pr_id: int, *, include_work_items: bool = False) -> Dict[str, Any]:
    """Get a pull request by ID."""
    pr = client.get(
        f"_apis/git/repositories/{quote(repo, safe='')}/pullrequests/{pr_id}",
        project=project,
    )
    if include_work_items:
        wi = client.get(
            f"_apis/git/repositories/{quote(repo, safe='')}/pullrequests/{pr_id}/workitems",
            project=project,
        )
        pr["workItemRefs"] = wi.get("value", []) if isinstance(wi, dict) else wi
    return pr


def get_pull_request_iterations(project: str, repo: str, pr_id: int) -> List[Dict[str, Any]]:
    """Get iterations (push sets) of a pull request."""
    data = client.get(
        f"_apis/git/repositories/{quote(repo, safe='')}/pullrequests/{pr_id}/iterations",
        project=project,
    )
    return data.get("value", []) if isinstance(data, dict) else data


def get_pull_request_changes(
    project: str, repo: str, pr_id: int, *, iteration_id: Optional[int] = None, top: Optional[int] = None, skip: Optional[int] = None
) -> Any:
    """Get file changes (diff) for a pull request or a specific iteration.

    Returns a list of change entries. Each entry has ``changeType``
    (``add``, ``edit``, ``delete``, …) and ``item.path``.

    The raw API wraps this in a ``changeEntries`` key; this function
    unwraps it for consistency with other list-returning commands.
    """
    if iteration_id:
        path = f"_apis/git/repositories/{quote(repo, safe='')}/pullrequests/{pr_id}/iterations/{iteration_id}/changes"
    else:
        # Use the last iteration by default
        iters = get_pull_request_iterations(project, repo, pr_id)
        if iters:
            last = iters[-1]["id"]
            path = f"_apis/git/repositories/{quote(repo, safe='')}/pullrequests/{pr_id}/iterations/{last}/changes"
        else:
            path = f"_apis/git/repositories/{quote(repo, safe='')}/pullrequests/{pr_id}/iterations/1/changes"
    params: Dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    if skip is not None:
        params["$skip"] = skip
    data = client.get(path, project=project, params=params)
    # Normalize: raw API uses "changeEntries"; unwrap for consistency
    if isinstance(data, dict):
        return data.get("changeEntries", data.get("value", []))
    return data


def list_pr_threads(
    project: str,
    repo: str,
    pr_id: int,
    *,
    iteration: Optional[int] = None,
    top: Optional[int] = None,
    skip: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """List comment threads on a pull request."""
    params: Dict[str, Any] = {}
    if iteration is not None:
        params["$iteration"] = iteration
    if top is not None:
        params["$top"] = top
    if skip is not None:
        params["$skip"] = skip
    data = client.get(
        f"_apis/git/repositories/{quote(repo, safe='')}/pullrequests/{pr_id}/threads",
        project=project,
        params=params,
    )
    return data.get("value", []) if isinstance(data, dict) else data


def list_pr_thread_comments(
    project: str, repo: str, pr_id: int, thread_id: int
) -> List[Dict[str, Any]]:
    """List comments in a specific PR thread."""
    data = client.get(
        f"_apis/git/repositories/{quote(repo, safe='')}/pullrequests/{pr_id}/threads/{thread_id}/comments",
        project=project,
    )
    return data.get("value", []) if isinstance(data, dict) else data


# ---------------------------------------------------------------------------
# File content & diffs
# ---------------------------------------------------------------------------


def get_file_content(
    project: str,
    repo: str,
    path: str,
    *,
    branch: Optional[str] = None,
    commit: Optional[str] = None,
) -> str:
    """Download raw file content from a repository."""
    params: Dict[str, Any] = {"path": path}
    if branch:
        params["versionDescriptor.version"] = branch.removeprefix("refs/heads/")
        params["versionDescriptor.versionType"] = "branch"
    elif commit:
        params["versionDescriptor.version"] = commit
        params["versionDescriptor.versionType"] = "commit"
    return client.get_text(
        f"_apis/git/repositories/{quote(repo, safe='')}/items",
        project=project,
        params=params,
    )


def list_items(
    project: str,
    repo: str,
    *,
    path: str = "/",
    branch: Optional[str] = None,
    recursion: str = "oneLevel",
) -> Any:
    """List items (files/folders) in a repo path."""
    params: Dict[str, Any] = {
        "scopePath": path,
        "recursionLevel": recursion,
    }
    if branch:
        params["versionDescriptor.version"] = branch.removeprefix("refs/heads/")
        params["versionDescriptor.versionType"] = "branch"
    return client.get(
        f"_apis/git/repositories/{quote(repo, safe='')}/items",
        project=project,
        params=params,
    )


def bulk_download_files(
    project: str,
    repo: str,
    paths: List[str],
    output_dir: str,
    *,
    branch: Optional[str] = None,
    commit: Optional[str] = None,
    retries: int = 2,
) -> List[Dict[str, Any]]:
    """Download multiple files from a repository into a local directory tree.

    Each file at ``/src/Foo/Bar.cs`` is written to ``<output_dir>/src/Foo/Bar.cs``.
    Returns a JSON-serialisable list of {path, status, output, error?} dicts.
    """
    results: List[Dict[str, Any]] = []
    total = len(paths)
    for idx, file_path in enumerate(paths, 1):
        out_path = os.path.join(output_dir, file_path.lstrip("/"))
        pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        last_err: Optional[str] = None
        ok = False
        for attempt in range(1, retries + 2):  # retries + 1 total attempts
            try:
                content = get_file_content(
                    project, repo, file_path,
                    branch=branch, commit=commit,
                )
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(content)
                ok = True
                break
            except Exception as exc:  # noqa: BLE001
                last_err = f"{type(exc).__name__}: {exc}"
                if attempt <= retries:
                    time.sleep(1 * attempt)  # simple back-off
        status = "ok" if ok else "failed"
        entry: Dict[str, Any] = {
            "path": file_path,
            "status": status,
            "output": out_path if ok else None,
        }
        if last_err and not ok:
            entry["error"] = last_err
        results.append(entry)
        # Progress to stderr so it doesn't pollute JSON stdout
        print(f"[{idx}/{total}] {status}: {file_path}", file=sys.stderr)
    return results


def get_diff(
    project: str,
    repo: str,
    *,
    base_version: Optional[str] = None,
    target_version: Optional[str] = None,
    base_version_type: str = "commit",
    target_version_type: str = "commit",
) -> Any:
    """Get diff between two versions (commits, branches, tags)."""
    params: Dict[str, Any] = {}
    if base_version:
        params["baseVersionDescriptor.version"] = base_version.removeprefix("refs/heads/")
        params["baseVersionDescriptor.versionType"] = base_version_type
    if target_version:
        params["targetVersionDescriptor.version"] = target_version.removeprefix("refs/heads/")
        params["targetVersionDescriptor.versionType"] = target_version_type
    return client.get(
        f"_apis/git/repositories/{quote(repo, safe='')}/diffs/commits",
        project=project,
        params=params,
    )


# ---------------------------------------------------------------------------
# High-level helpers
# ---------------------------------------------------------------------------


def pr_summary(
    project: str,
    repo: str,
    pr_id: int,
) -> Dict[str, Any]:
    """Return a structured overview of a PR suitable for code review.

    Combines metadata, changed-file list, and existing review threads
    into a single response.  This saves several round trips compared to
    calling each API individually.
    """
    # 1. PR metadata
    pr = get_pull_request(project, repo, pr_id, include_work_items=True)

    # 2. Changed files (normalised to a flat list)
    changes = get_pull_request_changes(project, repo, pr_id)

    # Classify files
    added, edited, deleted = [], [], []
    for c in (changes if isinstance(changes, list) else []):
        ct = c.get("changeType", "")
        p = c.get("item", {}).get("path", "")
        if ct == "add":
            added.append(p)
        elif ct == "edit":
            edited.append(p)
        elif ct == "delete":
            deleted.append(p)

    # 3. Review threads — only human-authored text threads
    all_threads = list_pr_threads(project, repo, pr_id)
    review_comments = []
    for t in all_threads:
        comments = t.get("comments", [])
        text_comments = [c for c in comments if c.get("commentType") == "text"]
        if not text_comments:
            continue
        first = text_comments[0]
        review_comments.append({
            "status": t.get("status", "unknown"),
            "author": first.get("author", {}).get("displayName", "?"),
            "filePath": (t.get("threadContext") or {}).get("filePath", ""),
            "content": first.get("content", "")[:200],
        })

    return {
        "title": pr.get("title"),
        "description": (pr.get("description") or "")[:500],
        "status": pr.get("status"),
        "createdBy": pr.get("createdBy", {}).get("displayName"),
        "sourceBranch": pr.get("sourceRefName"),
        "targetBranch": pr.get("targetRefName"),
        "sourceCommit": (pr.get("lastMergeSourceCommit") or {}).get("commitId"),
        "targetCommit": (pr.get("lastMergeTargetCommit") or {}).get("commitId"),
        "workItemRefs": pr.get("workItemRefs", []),
        "files": {
            "added": added,
            "edited": edited,
            "deleted": deleted,
        },
        "reviewComments": review_comments,
    }


def pr_download(
    project: str,
    repo: str,
    pr_id: int,
    output_dir: str,
    *,
    retries: int = 2,
) -> Dict[str, Any]:
    """Download all changed files for a PR into ``output_dir/source`` and
    ``output_dir/target`` sub-directories, ready for local diffing.

    Returns a dict with metadata (commits used) and download results.
    """
    import os

    # 1. Get PR metadata for commit SHAs
    pr = get_pull_request(project, repo, pr_id)
    source_commit = (pr.get("lastMergeSourceCommit") or {}).get("commitId")
    target_commit = (pr.get("lastMergeTargetCommit") or {}).get("commitId")
    if not source_commit or not target_commit:
        raise ValueError("PR does not have merge commit information yet")

    # 2. Get changed files
    changes = get_pull_request_changes(project, repo, pr_id)
    change_list = changes if isinstance(changes, list) else []

    added, edited, deleted = [], [], []
    for c in change_list:
        ct = c.get("changeType", "")
        p = c.get("item", {}).get("path", "")
        if not p:
            continue
        if ct == "add":
            added.append(p)
        elif ct == "edit":
            edited.append(p)
        elif ct == "delete":
            deleted.append(p)

    # 3. Download target (before) versions for edited + deleted files
    before_paths = edited + deleted
    before_results = []
    if before_paths:
        before_results = bulk_download_files(
            project, repo,
            before_paths,
            os.path.join(output_dir, "target"),
            commit=target_commit,
            retries=retries,
        )

    # 4. Download source (after) versions for edited + added files
    after_paths = edited + added
    after_results = []
    if after_paths:
        after_results = bulk_download_files(
            project, repo,
            after_paths,
            os.path.join(output_dir, "source"),
            commit=source_commit,
            retries=retries,
        )

    return {
        "sourceCommit": source_commit,
        "targetCommit": target_commit,
        "files": {"added": added, "edited": edited, "deleted": deleted},
        "downloads": {
            "target": before_results,
            "source": after_results,
        },
    }
