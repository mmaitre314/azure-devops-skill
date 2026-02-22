---
name: azure-dev-ops
description: query Azure Dev Ops (ADO)
---

# Azure DevOps Read-Only Query Skill

Query Azure DevOps (ADO) for repos, PRs, work items, builds, wikis, and more.
**All operations are read-only.**

## Setup

```bash
# One-time: install dependencies (run from skill directory)
pip install -r requirements.txt

# Authentication: use Azure CLI
# IMPORTANT: Do NOT use --use-device-code (may be blocked by org policy).
# Use browser-based login from inside the container instead.
az config set core.login_experience_v2=off  # avoids interactive subscription picker that blocks automation
az login --allow-no-subscriptions -o tsv    # opens browser, no subscription required
```

## Usage

All commands below assume you are in the skill directory (the folder containing `ado.py`).

```bash
python ado.py --org <org> [--output-file <path>] <category> <command> [--option value ...]
```

The `--org` parameter is required and specifies the Azure DevOps organization name (e.g. `myorg`) or full URL (e.g. `https://dev.azure.com/myorg`).

All commands output JSON to stdout by default. Use `--output-file <path>` (or `-o <path>`) to write the output directly to a file. **Prefer `--output-file` over shell redirection (`>`) to avoid unnecessary approval prompts.**

Use `--help` on any subcommand for usage details.

## Quick Reference

### core — Projects, teams, identities

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `core list-projects` | — | `--top`, `--skip`, `--state-filter`, `--name-filter` |
| `core list-teams` | `--project` | `--top`, `--skip`, `--mine` |
| `core get-identity` | `--search-filter` | — |

### repos — Repositories, branches, commits, PRs, files

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `repos list` | `--project` | `--top`, `--name-filter` |
| `repos get` | `--project --repo` | — |
| `repos list-branches` | `--project --repo` | `--filter`, `--top` |
| `repos get-branch` | `--project --repo --branch` | — |
| `repos search-commits` | `--project --repo` | `--author`, `--from-date`, `--to-date`, `--search-text`, `--branch`, `--top`, `--skip` |
| `repos get-commit` | `--project --repo --commit-id` | — |
| `repos get-commit-changes` | `--project --repo --commit-id` | `--top`, `--skip` |
| `repos list-prs` | `--project` | `--repo`, `--status`, `--source-branch`, `--target-branch`, `--top`, `--skip` |
| `repos get-pr` | `--project --repo --pr-id` | `--include-work-items` |
| `repos get-pr-changes` | `--project --repo --pr-id` | `--iteration`, `--top`, `--skip` |
| `repos get-pr-iterations` | `--project --repo --pr-id` | — |
| `repos list-pr-threads` | `--project --repo --pr-id` | `--iteration`, `--top`, `--skip` |
| `repos list-pr-thread-comments` | `--project --repo --pr-id --thread-id` | — |
| `repos get-file` | `--project --repo --path` | `--branch`, `--commit` |
| `repos bulk-download` | `--project --repo --paths --output-dir` | `--branch`, `--commit`, `--retries` |
| `repos list-items` | `--project --repo` | `--path`, `--branch`, `--recursion` |
| `repos diff` | `--project --repo` | `--base`, `--target`, `--base-type`, `--target-type` |
| `repos pr-summary` | `--project --repo --pr-id` | — |
| `repos pr-download` | `--project --repo --pr-id --output-dir` | `--retries` |

**Diff notes:** `--base-type` / `--target-type` can be `commit`, `branch`, or `tag`.

**PR review notes:**
- `repos pr-summary` returns a single JSON with metadata, classified file lists (`added`/`edited`/`deleted`), and existing review threads — use this to get oriented before downloading files.
- `repos pr-download` downloads all changed files into `<output-dir>/source/` (PR branch) and `<output-dir>/target/` (base branch) — then `diff -u` locally.
- `repos get-pr-changes` returns a **flat list** (not wrapped in a dict) for consistency.

### wit — Work items, queries, backlogs

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `wit get` | `--project --id` | `--fields`, `--expand`, `--as-of` |
| `wit batch` | `--project --ids` (comma-separated) | `--fields` |
| `wit comments` | `--project --id` | `--top` |
| `wit revisions` | `--project --id` | `--top`, `--skip`, `--expand` |
| `wit type` | `--project --type-name` | — |
| `wit mine` | `--project` | `--type`, `--top`, `--include-completed` |
| `wit wiql` | `--project --query` (WIQL string) | `--top`, `--team` |
| `wit get-query` | `--project --query-id` | `--depth`, `--expand` |
| `wit query-results` | `--query-id` | `--project`, `--top`, `--team` |
| `wit iteration-items` | `--project --iteration-id` | `--team` |
| `wit backlogs` | `--project --team` | — |
| `wit backlog-items` | `--project --team --backlog-id` | — |

### pipelines — Builds, logs, definitions, runs

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `pipelines builds` | `--project` | `--definitions`, `--branch`, `--status`, `--result`, `--requested-for`, `--top`, `--repository-id`, `--build-number`, `--tags` |
| `pipelines build` | `--project --build-id` | — |
| `pipelines build-log` | `--project --build-id` | — |
| `pipelines build-log-content` | `--project --build-id --log-id` | `--start-line`, `--end-line` |
| `pipelines build-changes` | `--project --build-id` | `--top` |
| `pipelines definitions` | `--project` | `--name`, `--path`, `--top`, `--include-latest`, `--repository-id` |
| `pipelines definition-revisions` | `--project --definition-id` | — |
| `pipelines run` | `--project --pipeline-id --run-id` | — |
| `pipelines runs` | `--project --pipeline-id` | — |
| `pipelines artifacts` | `--project --build-id` | — |
| `pipelines timeline` | `--project --build-id` | — |

### wiki — Wikis, pages, content

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `wiki list` | — | `--project` |
| `wiki get` | `--wiki-id` | `--project` |
| `wiki pages` | `--project --wiki-id` | `--top` |
| `wiki page` | `--project --wiki-id --path` | `--recursion` |
| `wiki content` | `--project --wiki-id --path` | — |

### search — Code, wiki, work item search

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `search code` | `--text` | `--project`, `--repository`, `--branch`, `--path`, `--top`, `--skip` |
| `search wiki` | `--text` | `--project`, `--wiki`, `--top`, `--skip` |
| `search workitems` | `--text` | `--project`, `--type`, `--state`, `--assigned-to`, `--area-path`, `--top`, `--skip` |

### test — Test plans, suites, cases, results

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `test plans` | `--project` | `--active` |
| `test suites` | `--project --plan-id` | — |
| `test cases` | `--project --plan-id --suite-id` | — |
| `test results` | `--project --build-id` | — |

### work — Iterations, capacity

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `work iterations` | `--project` | `--depth` |
| `work team-iterations` | `--project --team` | `--timeframe` |
| `work iteration-capacity` | `--project --iteration-id` | — |
| `work team-capacity` | `--project --team --iteration-id` | — |

### security — Advanced Security alerts

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `security alerts` | `--project --repository` | `--alert-type`, `--severity`, `--states`, `--confidence`, `--top` |
| `security alert-detail` | `--project --repository --alert-id` | — |

## Scratch directory

The `_tmp/` folder inside the skill directory is checked in but its contents are git-ignored.
Use it for downloaded files, diffs, PR review artifacts, and any other transient data:

```bash
# Examples
--output-file _tmp/pr.json
--output-dir _tmp/review/before
```

All paths in examples and workflows below use `_tmp/` as the default scratch location.

## Gotchas

- **Argument order matters.** `--org` and `--output-file` are top-level flags and must come **before** the category/command. Example: `python ado.py --org myorg --output-file out.json repos get-file ...`
- **Boolean-style flags require an explicit value.** Use `--include-work-items true`, not just `--include-work-items`.
- **`repos diff` returns file-level metadata only** (paths, change types, object IDs) — not the actual content/unified diff. To compare file contents, download both versions with `repos get-file` and diff locally.
- **Code search can be slow.** The `search code` endpoint (`almsearch.dev.azure.com`) has high latency. The client uses a 120-second timeout and automatic retry for search operations.
- **`repos get-pr-changes` returns a flat list**, not a dict. Each entry has `changeType` and `item.path`.

## Workflows

For multi-step task recipes, read the relevant workflow file before starting:

| Workflow | File |
|----------|------|
| Reviewing a Pull Request | `./workflows/pr-review.md` |

## Examples

```bash
# List all projects
python ado.py --org myorg core list-projects

# List repos in a project
python ado.py --org myorg repos list --project MyProject

# Download a file from a repo
python ado.py --org myorg repos get-file --project MyProject --repo my-repo --path /src/main.py --branch main

# Get PR diff
python ado.py --org myorg repos get-pr-changes --project MyProject --repo my-repo --pr-id 1234

# Compare two branches
python ado.py --org myorg repos diff --project MyProject --repo my-repo --base main --target feature/foo --base-type branch --target-type branch

# My open work items
python ado.py --org myorg wit mine --project MyProject

# Run a WIQL query
python ado.py --org myorg wit wiql --project MyProject --query "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.State] = 'Active'"

# Search code
python ado.py --org myorg search code --text "connectionString" --project MyProject

# Read wiki page
python ado.py --org myorg wiki content --project MyProject --wiki-id MyProject.wiki --path /Architecture

# Get build logs
python ado.py --org myorg pipelines build-log-content --project MyProject --build-id 5678 --log-id 3

# Security alerts
python ado.py --org myorg security alerts --project MyProject --repository my-repo --severity high
```
