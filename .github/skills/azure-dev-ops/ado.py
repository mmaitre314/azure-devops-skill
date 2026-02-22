#!/usr/bin/env python3
"""
Azure DevOps read-only query CLI.

Usage:  python ado.py --org <org> <category> <command> [options]

The --org parameter is required and specifies the Azure DevOps organization
(e.g. "myorg" or "https://dev.azure.com/myorg").
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from ado import client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _int_or_none(v: str | None) -> int | None:
    return int(v) if v is not None else None


def _bool_flag(v: str | None) -> bool | None:
    if v is None:
        return None
    return v.lower() in ("true", "1", "yes")


def _list_of_ints(v: str) -> list[int]:
    return [int(x.strip()) for x in v.split(",")]


def _output(data: Any) -> None:
    client.output(data)


# ===================================================================
# CORE
# ===================================================================

def cmd_core_list_projects(args: argparse.Namespace) -> None:
    from ado.core import list_projects
    _output(list_projects(
        top=_int_or_none(args.top),
        skip=_int_or_none(args.skip),
        state_filter=args.state_filter,
        name_filter=args.name_filter,
    ))


def cmd_core_list_teams(args: argparse.Namespace) -> None:
    from ado.core import list_project_teams
    _output(list_project_teams(
        args.project,
        top=_int_or_none(args.top),
        skip=_int_or_none(args.skip),
        mine=_bool_flag(args.mine),
    ))


def cmd_core_get_identity(args: argparse.Namespace) -> None:
    from ado.core import get_identity_ids
    _output(get_identity_ids(args.search_filter))


# ===================================================================
# REPOS
# ===================================================================

def cmd_repos_list(args: argparse.Namespace) -> None:
    from ado.repos import list_repos
    _output(list_repos(args.project, top=_int_or_none(args.top), name_filter=args.name_filter))


def cmd_repos_get(args: argparse.Namespace) -> None:
    from ado.repos import get_repo
    _output(get_repo(args.project, args.repo))


def cmd_repos_list_branches(args: argparse.Namespace) -> None:
    from ado.repos import list_branches
    _output(list_branches(args.project, args.repo, filter_contains=args.filter, top=_int_or_none(args.top)))


def cmd_repos_get_branch(args: argparse.Namespace) -> None:
    from ado.repos import get_branch
    _output(get_branch(args.project, args.repo, args.branch))


def cmd_repos_search_commits(args: argparse.Namespace) -> None:
    from ado.repos import search_commits
    _output(search_commits(
        args.project, args.repo,
        author=args.author, from_date=args.from_date, to_date=args.to_date,
        search_text=args.search_text, top=_int_or_none(args.top),
        skip=_int_or_none(args.skip), branch=args.branch,
    ))


def cmd_repos_get_commit(args: argparse.Namespace) -> None:
    from ado.repos import get_commit
    _output(get_commit(args.project, args.repo, args.commit_id))


def cmd_repos_get_commit_changes(args: argparse.Namespace) -> None:
    from ado.repos import get_commit_changes
    _output(get_commit_changes(
        args.project, args.repo, args.commit_id,
        top=_int_or_none(args.top), skip=_int_or_none(args.skip),
    ))


def cmd_repos_list_prs(args: argparse.Namespace) -> None:
    from ado.repos import list_pull_requests
    _output(list_pull_requests(
        args.project, repo=args.repo, status=args.status,
        source_branch=args.source_branch, target_branch=args.target_branch,
        top=_int_or_none(args.top), skip=_int_or_none(args.skip),
    ))


def cmd_repos_get_pr(args: argparse.Namespace) -> None:
    from ado.repos import get_pull_request
    _output(get_pull_request(
        args.project, args.repo, int(args.pr_id),
        include_work_items=_bool_flag(args.include_work_items) or False,
    ))


def cmd_repos_get_pr_changes(args: argparse.Namespace) -> None:
    from ado.repos import get_pull_request_changes
    _output(get_pull_request_changes(
        args.project, args.repo, int(args.pr_id),
        iteration_id=_int_or_none(args.iteration),
        top=_int_or_none(args.top), skip=_int_or_none(args.skip),
    ))


def cmd_repos_get_pr_iterations(args: argparse.Namespace) -> None:
    from ado.repos import get_pull_request_iterations
    _output(get_pull_request_iterations(args.project, args.repo, int(args.pr_id)))


def cmd_repos_list_pr_threads(args: argparse.Namespace) -> None:
    from ado.repos import list_pr_threads
    _output(list_pr_threads(
        args.project, args.repo, int(args.pr_id),
        iteration=_int_or_none(args.iteration),
        top=_int_or_none(args.top), skip=_int_or_none(args.skip),
    ))


def cmd_repos_list_pr_thread_comments(args: argparse.Namespace) -> None:
    from ado.repos import list_pr_thread_comments
    _output(list_pr_thread_comments(
        args.project, args.repo, int(args.pr_id), int(args.thread_id),
    ))


def cmd_repos_get_file(args: argparse.Namespace) -> None:
    from ado.repos import get_file_content
    client.output_text(get_file_content(
        args.project, args.repo, args.path,
        branch=args.branch, commit=args.commit,
    ))


def cmd_repos_bulk_download(args: argparse.Namespace) -> None:
    from ado.repos import bulk_download_files
    paths = [p.strip() for p in args.paths.split(",") if p.strip()]
    _output(bulk_download_files(
        args.project, args.repo, paths, args.output_dir,
        branch=args.branch, commit=args.commit,
        retries=int(args.retries) if args.retries else 2,
    ))


def cmd_repos_list_items(args: argparse.Namespace) -> None:
    from ado.repos import list_items
    _output(list_items(
        args.project, args.repo,
        path=args.path or "/", branch=args.branch,
        recursion=args.recursion or "oneLevel",
    ))


def cmd_repos_diff(args: argparse.Namespace) -> None:
    from ado.repos import get_diff
    _output(get_diff(
        args.project, args.repo,
        base_version=args.base, target_version=args.target,
        base_version_type=args.base_type or "commit",
        target_version_type=args.target_type or "commit",
    ))


def cmd_repos_pr_summary(args: argparse.Namespace) -> None:
    from ado.repos import pr_summary
    _output(pr_summary(args.project, args.repo, int(args.pr_id)))


def cmd_repos_pr_download(args: argparse.Namespace) -> None:
    from ado.repos import pr_download
    _output(pr_download(
        args.project, args.repo, int(args.pr_id),
        args.output_dir,
        retries=int(args.retries),
    ))


# ===================================================================
# WORK ITEMS
# ===================================================================

def cmd_wit_get(args: argparse.Namespace) -> None:
    from ado.work_items import get_work_item
    _output(get_work_item(
        args.project, int(args.id),
        fields=args.fields, expand=args.expand, as_of=args.as_of,
    ))


def cmd_wit_batch(args: argparse.Namespace) -> None:
    from ado.work_items import get_work_items_batch
    ids = _list_of_ints(args.ids)
    fields = args.fields.split(",") if args.fields else None
    _output(get_work_items_batch(args.project, ids, fields=fields))


def cmd_wit_comments(args: argparse.Namespace) -> None:
    from ado.work_items import list_comments
    _output(list_comments(args.project, int(args.id), top=_int_or_none(args.top)))


def cmd_wit_revisions(args: argparse.Namespace) -> None:
    from ado.work_items import list_revisions
    _output(list_revisions(
        args.project, int(args.id),
        top=_int_or_none(args.top), skip=_int_or_none(args.skip),
        expand=args.expand,
    ))


def cmd_wit_type(args: argparse.Namespace) -> None:
    from ado.work_items import get_work_item_type
    _output(get_work_item_type(args.project, args.type_name))


def cmd_wit_mine(args: argparse.Namespace) -> None:
    from ado.work_items import my_work_items
    _output(my_work_items(
        args.project, type_filter=args.type,
        top=_int_or_none(args.top),
        include_completed=_bool_flag(args.include_completed) or False,
    ))


def cmd_wit_wiql(args: argparse.Namespace) -> None:
    from ado.work_items import run_wiql
    _output(run_wiql(
        args.project, args.query,
        top=_int_or_none(args.top), team=args.team,
    ))


def cmd_wit_get_query(args: argparse.Namespace) -> None:
    from ado.work_items import get_query
    _output(get_query(
        args.project, args.query_id,
        depth=_int_or_none(args.depth), expand=args.expand,
    ))


def cmd_wit_query_results(args: argparse.Namespace) -> None:
    from ado.work_items import get_query_results
    _output(get_query_results(
        args.query_id, project=args.project,
        top=_int_or_none(args.top), team=args.team,
    ))


def cmd_wit_iteration_items(args: argparse.Namespace) -> None:
    from ado.work_items import get_work_items_for_iteration
    _output(get_work_items_for_iteration(
        args.project, args.iteration_id, team=args.team,
    ))


def cmd_wit_backlogs(args: argparse.Namespace) -> None:
    from ado.work_items import list_backlogs
    _output(list_backlogs(args.project, args.team))


def cmd_wit_backlog_items(args: argparse.Namespace) -> None:
    from ado.work_items import list_backlog_work_items
    _output(list_backlog_work_items(args.project, args.team, args.backlog_id))


# ===================================================================
# PIPELINES
# ===================================================================

def cmd_pipelines_builds(args: argparse.Namespace) -> None:
    from ado.pipelines import get_builds
    _output(get_builds(
        args.project,
        definitions=args.definitions, branch_name=args.branch,
        status_filter=args.status, result_filter=args.result,
        requested_for=args.requested_for, top=_int_or_none(args.top),
        repository_id=args.repository_id, build_number=args.build_number,
        tag_filters=args.tags,
    ))


def cmd_pipelines_build(args: argparse.Namespace) -> None:
    from ado.pipelines import get_build
    _output(get_build(args.project, int(args.build_id)))


def cmd_pipelines_build_log(args: argparse.Namespace) -> None:
    from ado.pipelines import get_build_log
    _output(get_build_log(args.project, int(args.build_id)))


def cmd_pipelines_build_log_content(args: argparse.Namespace) -> None:
    from ado.pipelines import get_build_log_by_id
    print(get_build_log_by_id(
        args.project, int(args.build_id), int(args.log_id),
        start_line=_int_or_none(args.start_line),
        end_line=_int_or_none(args.end_line),
    ))


def cmd_pipelines_build_changes(args: argparse.Namespace) -> None:
    from ado.pipelines import get_build_changes
    _output(get_build_changes(args.project, int(args.build_id), top=_int_or_none(args.top)))


def cmd_pipelines_definitions(args: argparse.Namespace) -> None:
    from ado.pipelines import get_build_definitions
    _output(get_build_definitions(
        args.project, name=args.name, path=args.path,
        top=_int_or_none(args.top),
        include_latest_builds=_bool_flag(args.include_latest),
        repository_id=args.repository_id,
    ))


def cmd_pipelines_definition_revisions(args: argparse.Namespace) -> None:
    from ado.pipelines import get_build_definition_revisions
    _output(get_build_definition_revisions(args.project, int(args.definition_id)))


def cmd_pipelines_run(args: argparse.Namespace) -> None:
    from ado.pipelines import get_pipeline_run
    _output(get_pipeline_run(args.project, int(args.pipeline_id), int(args.run_id)))


def cmd_pipelines_runs(args: argparse.Namespace) -> None:
    from ado.pipelines import list_pipeline_runs
    _output(list_pipeline_runs(args.project, int(args.pipeline_id)))


def cmd_pipelines_artifacts(args: argparse.Namespace) -> None:
    from ado.pipelines import list_artifacts
    _output(list_artifacts(args.project, int(args.build_id)))


def cmd_pipelines_timeline(args: argparse.Namespace) -> None:
    from ado.pipelines import get_build_timeline
    _output(get_build_timeline(args.project, int(args.build_id)))


# ===================================================================
# WIKI
# ===================================================================

def cmd_wiki_list(args: argparse.Namespace) -> None:
    from ado.wiki import list_wikis
    _output(list_wikis(project=args.project))


def cmd_wiki_get(args: argparse.Namespace) -> None:
    from ado.wiki import get_wiki
    _output(get_wiki(args.wiki_id, project=args.project))


def cmd_wiki_pages(args: argparse.Namespace) -> None:
    from ado.wiki import list_pages
    _output(list_pages(args.project, args.wiki_id, top=_int_or_none(args.top)))


def cmd_wiki_page(args: argparse.Namespace) -> None:
    from ado.wiki import get_page
    _output(get_page(args.project, args.wiki_id, args.path, recursion_level=args.recursion))


def cmd_wiki_content(args: argparse.Namespace) -> None:
    from ado.wiki import get_page_content
    print(get_page_content(args.project, args.wiki_id, args.path))


# ===================================================================
# SEARCH
# ===================================================================

def cmd_search_code(args: argparse.Namespace) -> None:
    from ado.search import search_code
    _output(search_code(
        args.text, project=args.project, repository=args.repository,
        branch=args.branch, path=args.path,
        top=_int_or_none(args.top), skip=_int_or_none(args.skip),
    ))


def cmd_search_wiki(args: argparse.Namespace) -> None:
    from ado.search import search_wiki
    _output(search_wiki(
        args.text, project=args.project, wiki=args.wiki,
        top=_int_or_none(args.top), skip=_int_or_none(args.skip),
    ))


def cmd_search_workitems(args: argparse.Namespace) -> None:
    from ado.search import search_work_items
    _output(search_work_items(
        args.text, project=args.project, work_item_type=args.type,
        state=args.state, assigned_to=args.assigned_to,
        area_path=args.area_path,
        top=_int_or_none(args.top), skip=_int_or_none(args.skip),
    ))


# ===================================================================
# TEST PLANS
# ===================================================================

def cmd_test_plans(args: argparse.Namespace) -> None:
    from ado.test_plans import list_test_plans
    _output(list_test_plans(args.project, filter_active=_bool_flag(args.active)))


def cmd_test_suites(args: argparse.Namespace) -> None:
    from ado.test_plans import list_test_suites
    _output(list_test_suites(args.project, int(args.plan_id)))


def cmd_test_cases(args: argparse.Namespace) -> None:
    from ado.test_plans import list_test_cases
    _output(list_test_cases(args.project, int(args.plan_id), int(args.suite_id)))


def cmd_test_results(args: argparse.Namespace) -> None:
    from ado.test_plans import get_test_results_by_build
    _output(get_test_results_by_build(args.project, int(args.build_id)))


# ===================================================================
# WORK (iterations)
# ===================================================================

def cmd_work_iterations(args: argparse.Namespace) -> None:
    from ado.work import list_iterations
    _output(list_iterations(args.project, depth=_int_or_none(args.depth)))


def cmd_work_team_iterations(args: argparse.Namespace) -> None:
    from ado.work import list_team_iterations
    _output(list_team_iterations(args.project, args.team, timeframe=args.timeframe))


def cmd_work_iteration_capacity(args: argparse.Namespace) -> None:
    from ado.work import get_iteration_capacities
    _output(get_iteration_capacities(args.project, args.iteration_id))


def cmd_work_team_capacity(args: argparse.Namespace) -> None:
    from ado.work import get_team_capacity
    _output(get_team_capacity(args.project, args.team, args.iteration_id))


# ===================================================================
# SECURITY
# ===================================================================

def cmd_security_alerts(args: argparse.Namespace) -> None:
    from ado.security import get_alerts
    _output(get_alerts(
        args.project, args.repository,
        alert_type=args.alert_type, severity=args.severity,
        states=args.states, confidence_levels=args.confidence or "high",
        top=_int_or_none(args.top),
    ))


def cmd_security_alert_detail(args: argparse.Namespace) -> None:
    from ado.security import get_alert_details
    _output(get_alert_details(args.project, args.repository, int(args.alert_id)))


# ===================================================================
# ARGUMENT PARSER
# ===================================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ado",
        description="Azure DevOps read-only query tool",
    )
    p.add_argument("--org", required=True,
                   help="Azure DevOps organization name or URL (e.g. 'myorg' or 'https://dev.azure.com/myorg')")
    p.add_argument("--output-file", "-o", default=None,
                   help="Write JSON output to this file instead of stdout")
    sub = p.add_subparsers(dest="category", required=True)

    # ---- core ----
    core = sub.add_parser("core", help="Projects, teams, identities")
    core_sub = core.add_subparsers(dest="command", required=True)

    lp = core_sub.add_parser("list-projects")
    lp.add_argument("--top"); lp.add_argument("--skip")
    lp.add_argument("--state-filter"); lp.add_argument("--name-filter")
    lp.set_defaults(func=cmd_core_list_projects)

    lt = core_sub.add_parser("list-teams")
    lt.add_argument("--project", required=True)
    lt.add_argument("--top"); lt.add_argument("--skip"); lt.add_argument("--mine")
    lt.set_defaults(func=cmd_core_list_teams)

    gi = core_sub.add_parser("get-identity")
    gi.add_argument("--search-filter", required=True)
    gi.set_defaults(func=cmd_core_get_identity)

    # ---- repos ----
    repos = sub.add_parser("repos", help="Repositories, branches, PRs, files")
    repos_sub = repos.add_subparsers(dest="command", required=True)

    rl = repos_sub.add_parser("list")
    rl.add_argument("--project", required=True); rl.add_argument("--top"); rl.add_argument("--name-filter")
    rl.set_defaults(func=cmd_repos_list)

    rg = repos_sub.add_parser("get")
    rg.add_argument("--project", required=True); rg.add_argument("--repo", required=True)
    rg.set_defaults(func=cmd_repos_get)

    rb = repos_sub.add_parser("list-branches")
    rb.add_argument("--project", required=True); rb.add_argument("--repo", required=True)
    rb.add_argument("--filter"); rb.add_argument("--top")
    rb.set_defaults(func=cmd_repos_list_branches)

    rbg = repos_sub.add_parser("get-branch")
    rbg.add_argument("--project", required=True); rbg.add_argument("--repo", required=True); rbg.add_argument("--branch", required=True)
    rbg.set_defaults(func=cmd_repos_get_branch)

    sc = repos_sub.add_parser("search-commits")
    sc.add_argument("--project", required=True); sc.add_argument("--repo", required=True)
    sc.add_argument("--author"); sc.add_argument("--from-date"); sc.add_argument("--to-date")
    sc.add_argument("--search-text"); sc.add_argument("--top"); sc.add_argument("--skip"); sc.add_argument("--branch")
    sc.set_defaults(func=cmd_repos_search_commits)

    gc = repos_sub.add_parser("get-commit")
    gc.add_argument("--project", required=True); gc.add_argument("--repo", required=True); gc.add_argument("--commit-id", required=True)
    gc.set_defaults(func=cmd_repos_get_commit)

    gcc = repos_sub.add_parser("get-commit-changes")
    gcc.add_argument("--project", required=True); gcc.add_argument("--repo", required=True); gcc.add_argument("--commit-id", required=True)
    gcc.add_argument("--top"); gcc.add_argument("--skip")
    gcc.set_defaults(func=cmd_repos_get_commit_changes)

    lpr = repos_sub.add_parser("list-prs")
    lpr.add_argument("--project", required=True); lpr.add_argument("--repo")
    lpr.add_argument("--status"); lpr.add_argument("--source-branch"); lpr.add_argument("--target-branch")
    lpr.add_argument("--top"); lpr.add_argument("--skip")
    lpr.set_defaults(func=cmd_repos_list_prs)

    gpr = repos_sub.add_parser("get-pr")
    gpr.add_argument("--project", required=True); gpr.add_argument("--repo", required=True); gpr.add_argument("--pr-id", required=True)
    gpr.add_argument("--include-work-items")
    gpr.set_defaults(func=cmd_repos_get_pr)

    gprc = repos_sub.add_parser("get-pr-changes")
    gprc.add_argument("--project", required=True); gprc.add_argument("--repo", required=True); gprc.add_argument("--pr-id", required=True)
    gprc.add_argument("--iteration"); gprc.add_argument("--top"); gprc.add_argument("--skip")
    gprc.set_defaults(func=cmd_repos_get_pr_changes)

    gpri = repos_sub.add_parser("get-pr-iterations")
    gpri.add_argument("--project", required=True); gpri.add_argument("--repo", required=True); gpri.add_argument("--pr-id", required=True)
    gpri.set_defaults(func=cmd_repos_get_pr_iterations)

    lprt = repos_sub.add_parser("list-pr-threads")
    lprt.add_argument("--project", required=True); lprt.add_argument("--repo", required=True); lprt.add_argument("--pr-id", required=True)
    lprt.add_argument("--iteration"); lprt.add_argument("--top"); lprt.add_argument("--skip")
    lprt.set_defaults(func=cmd_repos_list_pr_threads)

    lprtc = repos_sub.add_parser("list-pr-thread-comments")
    lprtc.add_argument("--project", required=True); lprtc.add_argument("--repo", required=True)
    lprtc.add_argument("--pr-id", required=True); lprtc.add_argument("--thread-id", required=True)
    lprtc.set_defaults(func=cmd_repos_list_pr_thread_comments)

    gf = repos_sub.add_parser("get-file")
    gf.add_argument("--project", required=True); gf.add_argument("--repo", required=True); gf.add_argument("--path", required=True)
    gf.add_argument("--branch"); gf.add_argument("--commit")
    gf.set_defaults(func=cmd_repos_get_file)

    bd = repos_sub.add_parser("bulk-download")
    bd.add_argument("--project", required=True); bd.add_argument("--repo", required=True)
    bd.add_argument("--paths", required=True, help="Comma-separated repo paths (e.g. /src/A.cs,/src/B.cs)")
    bd.add_argument("--output-dir", required=True, help="Local directory to write files into")
    bd.add_argument("--branch"); bd.add_argument("--commit")
    bd.add_argument("--retries", default="2", help="Number of retries per file (default: 2)")
    bd.set_defaults(func=cmd_repos_bulk_download)

    li = repos_sub.add_parser("list-items")
    li.add_argument("--project", required=True); li.add_argument("--repo", required=True)
    li.add_argument("--path"); li.add_argument("--branch"); li.add_argument("--recursion")
    li.set_defaults(func=cmd_repos_list_items)

    rd = repos_sub.add_parser("diff")
    rd.add_argument("--project", required=True); rd.add_argument("--repo", required=True)
    rd.add_argument("--base"); rd.add_argument("--target")
    rd.add_argument("--base-type"); rd.add_argument("--target-type")
    rd.set_defaults(func=cmd_repos_diff)

    prs = repos_sub.add_parser("pr-summary", help="Get a structured PR overview for code review (metadata + files + threads)")
    prs.add_argument("--project", required=True); prs.add_argument("--repo", required=True); prs.add_argument("--pr-id", required=True)
    prs.set_defaults(func=cmd_repos_pr_summary)

    prd = repos_sub.add_parser("pr-download", help="Download all changed files (source + target versions) for a PR")
    prd.add_argument("--project", required=True); prd.add_argument("--repo", required=True); prd.add_argument("--pr-id", required=True)
    prd.add_argument("--output-dir", required=True, help="Base directory; files go into source/ and target/ subdirs")
    prd.add_argument("--retries", default="2", help="Number of retries per file (default: 2)")
    prd.set_defaults(func=cmd_repos_pr_download)

    # ---- wit (work items) ----
    wit = sub.add_parser("wit", help="Work items, queries, backlogs")
    wit_sub = wit.add_subparsers(dest="command", required=True)

    wg = wit_sub.add_parser("get")
    wg.add_argument("--project", required=True); wg.add_argument("--id", required=True)
    wg.add_argument("--fields"); wg.add_argument("--expand"); wg.add_argument("--as-of")
    wg.set_defaults(func=cmd_wit_get)

    wb = wit_sub.add_parser("batch")
    wb.add_argument("--project", required=True); wb.add_argument("--ids", required=True, help="comma-separated IDs")
    wb.add_argument("--fields")
    wb.set_defaults(func=cmd_wit_batch)

    wc = wit_sub.add_parser("comments")
    wc.add_argument("--project", required=True); wc.add_argument("--id", required=True); wc.add_argument("--top")
    wc.set_defaults(func=cmd_wit_comments)

    wr = wit_sub.add_parser("revisions")
    wr.add_argument("--project", required=True); wr.add_argument("--id", required=True)
    wr.add_argument("--top"); wr.add_argument("--skip"); wr.add_argument("--expand")
    wr.set_defaults(func=cmd_wit_revisions)

    wt = wit_sub.add_parser("type")
    wt.add_argument("--project", required=True); wt.add_argument("--type-name", required=True)
    wt.set_defaults(func=cmd_wit_type)

    wm = wit_sub.add_parser("mine")
    wm.add_argument("--project", required=True); wm.add_argument("--type"); wm.add_argument("--top")
    wm.add_argument("--include-completed")
    wm.set_defaults(func=cmd_wit_mine)

    wq = wit_sub.add_parser("wiql")
    wq.add_argument("--project", required=True); wq.add_argument("--query", required=True)
    wq.add_argument("--top"); wq.add_argument("--team")
    wq.set_defaults(func=cmd_wit_wiql)

    wgq = wit_sub.add_parser("get-query")
    wgq.add_argument("--project", required=True); wgq.add_argument("--query-id", required=True)
    wgq.add_argument("--depth"); wgq.add_argument("--expand")
    wgq.set_defaults(func=cmd_wit_get_query)

    wqr = wit_sub.add_parser("query-results")
    wqr.add_argument("--query-id", required=True); wqr.add_argument("--project")
    wqr.add_argument("--top"); wqr.add_argument("--team")
    wqr.set_defaults(func=cmd_wit_query_results)

    wii = wit_sub.add_parser("iteration-items")
    wii.add_argument("--project", required=True); wii.add_argument("--iteration-id", required=True); wii.add_argument("--team")
    wii.set_defaults(func=cmd_wit_iteration_items)

    wbl = wit_sub.add_parser("backlogs")
    wbl.add_argument("--project", required=True); wbl.add_argument("--team", required=True)
    wbl.set_defaults(func=cmd_wit_backlogs)

    wbli = wit_sub.add_parser("backlog-items")
    wbli.add_argument("--project", required=True); wbli.add_argument("--team", required=True); wbli.add_argument("--backlog-id", required=True)
    wbli.set_defaults(func=cmd_wit_backlog_items)

    # ---- pipelines ----
    pipes = sub.add_parser("pipelines", help="Builds, logs, definitions, runs")
    pipes_sub = pipes.add_subparsers(dest="command", required=True)

    pb = pipes_sub.add_parser("builds")
    pb.add_argument("--project", required=True); pb.add_argument("--definitions"); pb.add_argument("--branch")
    pb.add_argument("--status"); pb.add_argument("--result"); pb.add_argument("--requested-for")
    pb.add_argument("--top"); pb.add_argument("--repository-id"); pb.add_argument("--build-number")
    pb.add_argument("--tags")
    pb.set_defaults(func=cmd_pipelines_builds)

    pbg = pipes_sub.add_parser("build")
    pbg.add_argument("--project", required=True); pbg.add_argument("--build-id", required=True)
    pbg.set_defaults(func=cmd_pipelines_build)

    pbl = pipes_sub.add_parser("build-log")
    pbl.add_argument("--project", required=True); pbl.add_argument("--build-id", required=True)
    pbl.set_defaults(func=cmd_pipelines_build_log)

    pblc = pipes_sub.add_parser("build-log-content")
    pblc.add_argument("--project", required=True); pblc.add_argument("--build-id", required=True); pblc.add_argument("--log-id", required=True)
    pblc.add_argument("--start-line"); pblc.add_argument("--end-line")
    pblc.set_defaults(func=cmd_pipelines_build_log_content)

    pbc = pipes_sub.add_parser("build-changes")
    pbc.add_argument("--project", required=True); pbc.add_argument("--build-id", required=True); pbc.add_argument("--top")
    pbc.set_defaults(func=cmd_pipelines_build_changes)

    pd = pipes_sub.add_parser("definitions")
    pd.add_argument("--project", required=True); pd.add_argument("--name"); pd.add_argument("--path")
    pd.add_argument("--top"); pd.add_argument("--include-latest"); pd.add_argument("--repository-id")
    pd.set_defaults(func=cmd_pipelines_definitions)

    pdr = pipes_sub.add_parser("definition-revisions")
    pdr.add_argument("--project", required=True); pdr.add_argument("--definition-id", required=True)
    pdr.set_defaults(func=cmd_pipelines_definition_revisions)

    prn = pipes_sub.add_parser("run")
    prn.add_argument("--project", required=True); prn.add_argument("--pipeline-id", required=True); prn.add_argument("--run-id", required=True)
    prn.set_defaults(func=cmd_pipelines_run)

    prns = pipes_sub.add_parser("runs")
    prns.add_argument("--project", required=True); prns.add_argument("--pipeline-id", required=True)
    prns.set_defaults(func=cmd_pipelines_runs)

    pa = pipes_sub.add_parser("artifacts")
    pa.add_argument("--project", required=True); pa.add_argument("--build-id", required=True)
    pa.set_defaults(func=cmd_pipelines_artifacts)

    pt = pipes_sub.add_parser("timeline")
    pt.add_argument("--project", required=True); pt.add_argument("--build-id", required=True)
    pt.set_defaults(func=cmd_pipelines_timeline)

    # ---- wiki ----
    wiki = sub.add_parser("wiki", help="Wikis, pages, content")
    wiki_sub = wiki.add_subparsers(dest="command", required=True)

    wl = wiki_sub.add_parser("list")
    wl.add_argument("--project")
    wl.set_defaults(func=cmd_wiki_list)

    wge = wiki_sub.add_parser("get")
    wge.add_argument("--wiki-id", required=True); wge.add_argument("--project")
    wge.set_defaults(func=cmd_wiki_get)

    wp = wiki_sub.add_parser("pages")
    wp.add_argument("--project", required=True); wp.add_argument("--wiki-id", required=True); wp.add_argument("--top")
    wp.set_defaults(func=cmd_wiki_pages)

    wpg = wiki_sub.add_parser("page")
    wpg.add_argument("--project", required=True); wpg.add_argument("--wiki-id", required=True); wpg.add_argument("--path", required=True)
    wpg.add_argument("--recursion")
    wpg.set_defaults(func=cmd_wiki_page)

    wpc = wiki_sub.add_parser("content")
    wpc.add_argument("--project", required=True); wpc.add_argument("--wiki-id", required=True); wpc.add_argument("--path", required=True)
    wpc.set_defaults(func=cmd_wiki_content)

    # ---- search ----
    srch = sub.add_parser("search", help="Code, wiki, work item search")
    srch_sub = srch.add_subparsers(dest="command", required=True)

    sco = srch_sub.add_parser("code")
    sco.add_argument("--text", required=True); sco.add_argument("--project"); sco.add_argument("--repository")
    sco.add_argument("--branch"); sco.add_argument("--path"); sco.add_argument("--top"); sco.add_argument("--skip")
    sco.set_defaults(func=cmd_search_code)

    swi = srch_sub.add_parser("wiki")
    swi.add_argument("--text", required=True); swi.add_argument("--project"); swi.add_argument("--wiki")
    swi.add_argument("--top"); swi.add_argument("--skip")
    swi.set_defaults(func=cmd_search_wiki)

    swit = srch_sub.add_parser("workitems")
    swit.add_argument("--text", required=True); swit.add_argument("--project"); swit.add_argument("--type")
    swit.add_argument("--state"); swit.add_argument("--assigned-to"); swit.add_argument("--area-path")
    swit.add_argument("--top"); swit.add_argument("--skip")
    swit.set_defaults(func=cmd_search_workitems)

    # ---- test ----
    test = sub.add_parser("test", help="Test plans, suites, cases, results")
    test_sub = test.add_subparsers(dest="command", required=True)

    tp = test_sub.add_parser("plans")
    tp.add_argument("--project", required=True); tp.add_argument("--active")
    tp.set_defaults(func=cmd_test_plans)

    ts = test_sub.add_parser("suites")
    ts.add_argument("--project", required=True); ts.add_argument("--plan-id", required=True)
    ts.set_defaults(func=cmd_test_suites)

    tc = test_sub.add_parser("cases")
    tc.add_argument("--project", required=True); tc.add_argument("--plan-id", required=True); tc.add_argument("--suite-id", required=True)
    tc.set_defaults(func=cmd_test_cases)

    tr = test_sub.add_parser("results")
    tr.add_argument("--project", required=True); tr.add_argument("--build-id", required=True)
    tr.set_defaults(func=cmd_test_results)

    # ---- work (iterations) ----
    work = sub.add_parser("work", help="Iterations, capacity")
    work_sub = work.add_subparsers(dest="command", required=True)

    wki = work_sub.add_parser("iterations")
    wki.add_argument("--project", required=True); wki.add_argument("--depth")
    wki.set_defaults(func=cmd_work_iterations)

    wkti = work_sub.add_parser("team-iterations")
    wkti.add_argument("--project", required=True); wkti.add_argument("--team", required=True); wkti.add_argument("--timeframe")
    wkti.set_defaults(func=cmd_work_team_iterations)

    wkic = work_sub.add_parser("iteration-capacity")
    wkic.add_argument("--project", required=True); wkic.add_argument("--iteration-id", required=True)
    wkic.set_defaults(func=cmd_work_iteration_capacity)

    wktc = work_sub.add_parser("team-capacity")
    wktc.add_argument("--project", required=True); wktc.add_argument("--team", required=True); wktc.add_argument("--iteration-id", required=True)
    wktc.set_defaults(func=cmd_work_team_capacity)

    # ---- security ----
    sec = sub.add_parser("security", help="Advanced Security alerts")
    sec_sub = sec.add_subparsers(dest="command", required=True)

    sa = sec_sub.add_parser("alerts")
    sa.add_argument("--project", required=True); sa.add_argument("--repository", required=True)
    sa.add_argument("--alert-type"); sa.add_argument("--severity"); sa.add_argument("--states")
    sa.add_argument("--confidence"); sa.add_argument("--top")
    sa.set_defaults(func=cmd_security_alerts)

    sad = sec_sub.add_parser("alert-detail")
    sad.add_argument("--project", required=True); sad.add_argument("--repository", required=True); sad.add_argument("--alert-id", required=True)
    sad.set_defaults(func=cmd_security_alert_detail)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    client.set_org(args.org)
    client.set_output_file(args.output_file)
    try:
        args.func(args)
    except Exception as exc:
        error_detail = json.dumps({"error": str(exc)})
        print(error_detail, file=sys.stderr)
        # When --output-file is set, also report on stdout so the failure
        # is visible even when stderr is not displayed (e.g. truncated
        # terminal output, run_in_terminal timeout).
        out_path = getattr(args, "output_file", None)
        if out_path:
            print(f"ERROR: failed to write {out_path} — {exc}")
        sys.stdout.flush()
        sys.stderr.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
