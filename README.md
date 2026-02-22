# Azure DevOps Skill

A read-only Python CLI for querying Azure DevOps — repos, PRs, work items, builds, wikis, search, and more. Designed as a [GitHub Copilot skill](https://code.visualstudio.com/docs/copilot/chat/chat-agent-mode#_custom-instructions) so an AI agent can interact with ADO programmatically.

## Quick start

1. **Open in the dev container** (Python 3.13 + Azure CLI pre-installed).

2. **Install dependencies:**
   ```bash
   cd .github/skills/azure-dev-ops
   pip install -r requirements.txt
   ```

3. **Authenticate:**
   ```bash
   az config set core.login_experience_v2=off
   az login --allow-no-subscriptions -o tsv
   ```

4. **Run a command:**
   ```bash
   python ado.py --org <org> <category> <command> [options]
   ```
   Example:
   ```bash
   python ado.py --org myorg repos list --project MyProject
   ```

## Project layout

```
.github/skills/azure-dev-ops/
  ado.py              # CLI entry point
  ado/                # API modules (repos, work_items, pipelines, …)
  workflows/          # Multi-step task recipes (e.g. PR review)
  SKILL.md            # Full reference — commands, options, gotchas, examples
  requirements.txt    # Python dependencies
```

## Key concepts

- **All operations are read-only.** Nothing is created, updated, or deleted in ADO.
- Output is JSON. Use `--output-file <path>` (or `-o`) to write to a file instead of stdout.
- `--org` and `-o` are **top-level** flags — they go *before* the category/command.
- Use `--help` on any subcommand to see its options.

## Categories

| Category | What it covers |
|----------|---------------|
| `core` | Projects, teams, identities |
| `repos` | Repositories, branches, commits, PRs, file downloads |
| `wit` | Work items, WIQL queries, backlogs |
| `pipelines` | Builds, logs, definitions, runs |
| `wiki` | Wiki pages and content |
| `search` | Code, wiki, and work-item search |
| `test` | Test plans, suites, cases, results |
| `work` | Iterations, capacity |
| `security` | Advanced Security alerts |

## Workflows

| Workflow | File | Description |
|----------|------|-------------|
| PR Review | `workflows/pr-review.md` | Step-by-step guide to reviewing a pull request |

## Running tests

```bash
cd .github/skills/azure-dev-ops
python -m unittest discover -s tests -v
```

No extra dependencies needed — tests use Python's built-in `unittest` module with `unittest.mock` to avoid network calls.

## Further reading

See [SKILL.md](.github/skills/azure-dev-ops/SKILL.md) for the full command reference, examples, and gotchas.
