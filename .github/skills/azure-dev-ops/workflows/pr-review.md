# Workflow: Reviewing a Pull Request

PR reviews require multiple steps. Two high-level commands can short-circuit most of them:

> **All commands assume you are in the skill directory** (the folder containing `ado.py`).
> Downloaded artifacts go into `_tmp/`, which is git-ignored.

## Quick path (recommended)

### Step A: Get a structured PR overview

```bash
python ado.py --org myorg -o _tmp/pr-summary.json repos pr-summary \
  --project MyProject --repo my-repo --pr-id 1234
```

Returns a single JSON object with:
- PR title, description, status, author, branches, commit SHAs
- Changed files classified as `added`, `edited`, `deleted`
- Existing review threads (status, author, file, first 200 chars of content)

### Step B: Download all changed files (source + target)

```bash
python ado.py --org myorg repos pr-download \
  --project MyProject --repo my-repo --pr-id 1234 \
  --output-dir _tmp/review
```

Creates `_tmp/review/source/` (PR branch) and `_tmp/review/target/` (base branch) with the correct file versions. Then diff locally:

```bash
diff -u _tmp/review/target/src/File.cs _tmp/review/source/src/File.cs
```

---

## Manual path (step-by-step)

Use this when you need finer control (e.g. downloading a specific iteration).

> **All commands assume you are in the skill directory** (the folder containing `ado.py`).
> Downloaded artifacts go into `_tmp/`, which is git-ignored.

## Step 1: Get PR metadata

```bash
python ado.py --org myorg --output-file _tmp/pr.json repos get-pr \
  --project MyProject --repo my-repo --pr-id 1234 --include-work-items true
```

Key fields in the response:
- `sourceRefName` / `targetRefName` — branch names
- `lastMergeSourceCommit.commitId` — the PR branch tip at merge time
- `lastMergeTargetCommit.commitId` — the target branch state **before** merge
- `status` — `active` or `completed` (i.e., merged)

## Step 2: Get changed file list

```bash
python ado.py --org myorg -o _tmp/changes.json repos get-pr-changes \
  --project MyProject --repo my-repo --pr-id 1234
```

Returns a flat JSON list. Each entry has `changeType` (`add`, `edit`, `delete`) and `item.path`.

## Step 3: Download source and target file versions

**Critical:** If the PR is already merged, `--branch main` gives the **post-merge** state. Use the commit hashes from Step 1 instead:

```bash
# Pre-merge baseline (target branch before merge)
python ado.py --org myorg --output-file _tmp/before.cs repos get-file \
  --project MyProject --repo my-repo --path /src/File.cs \
  --commit <lastMergeTargetCommit.commitId>

# PR version (source branch at merge time)
python ado.py --org myorg --output-file _tmp/after.cs repos get-file \
  --project MyProject --repo my-repo --path /src/File.cs \
  --commit <lastMergeSourceCommit.commitId>
```

For **active (unmerged) PRs**, you can use `--branch` directly:

```bash
# Baseline
python ado.py --org myorg --output-file _tmp/before.cs repos get-file \
  --project MyProject --repo my-repo --path /src/File.cs --branch main

# PR version
python ado.py --org myorg --output-file _tmp/after.cs repos get-file \
  --project MyProject --repo my-repo --path /src/File.cs \
  --branch feature/my-change
```

## Step 4: Bulk download files

Use the `repos bulk-download` command to download all changed files in one invocation. It handles retries and directory creation automatically.

```bash
# Download pre-merge baseline (all edited/deleted files)
python ado.py --org myorg repos bulk-download \
  --project MyProject --repo my-repo \
  --paths "/src/File1.cs,/src/File2.cs,/src/File3.cs" \
  --commit <lastMergeTargetCommit.commitId> \
  --output-dir _tmp/review/before

# Download PR version (all edited/added files)
python ado.py --org myorg repos bulk-download \
  --project MyProject --repo my-repo \
  --paths "/src/File1.cs,/src/File2.cs,/src/File3.cs" \
  --commit <lastMergeSourceCommit.commitId> \
  --output-dir _tmp/review/after
```

Tip: Build the `--paths` list from Step 2 — include `edit` files in both commands, `delete` files only in `before`, and `add` files only in `after`.

## Step 5: Compare locally

```bash
diff -u _tmp/review/before/src/File.cs _tmp/review/after/src/File.cs
```

## Step 6: Check existing review threads

```bash
python ado.py --org myorg --output-file _tmp/threads.json repos list-pr-threads \
  --project MyProject --repo my-repo --pr-id 1234
```

Filter for `commentType == "text"` entries; system-generated threads have other types. Check thread `status` for `active`, `fixed`, `closed`, etc.
