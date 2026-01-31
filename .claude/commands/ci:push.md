---
description: Run CI gates, auto-fix failures, commit, push, and create PR if needed
argument-hint: "[commit message]"
---

Run the full CI-gated push workflow. If `$ARGUMENTS` is provided, use it as the commit message. Otherwise, auto-generate a commit message from the staged/unstaged changes.

## Workflow

### Step 1: CI loop (max 3 cycles)

For up to 3 cycles:

1. Run `pixi run ci` and capture output.
2. If all gates pass, proceed to Step 2.
3. If failures exist, classify each failure:
   - **AUTO-FIX**: Run `pixi run fix`, then restart the cycle.
   - **CONFIG-FIX**: Edit `pyproject.toml` or `pixi.toml` to resolve, then restart the cycle.
   - **MANUAL**: Read the failing file(s), understand the error, edit code to fix it, then restart the cycle.
4. After fixing, re-run `pixi run ci` (counts as next cycle).

If after 3 full cycles `pixi run ci` still fails, stop and report the remaining failures to the user. Do not commit or push.

### Failure classification reference

| Category | Action | Examples |
|----------|--------|---------|
| AUTO-FIX | `pixi run fix` | Unused import, unsorted imports, formatting, unused noqa |
| CONFIG-FIX | Edit `pyproject.toml` / `pixi.toml` | Add mypy override for untyped dep, adjust ruff ignores |
| MANUAL | Read error, edit code | Wrong type annotation, missing protocol impl, test failure |

### Step 2: Commit and push

1. Stage all changed files with `git add` (use specific file names, not `-A`).
2. Determine the commit message:
   - If `$ARGUMENTS` is non-empty, use it verbatim as the commit message.
   - Otherwise, run `git diff --cached --stat` and `git diff --cached` to understand the changes, then write a short (1-2 sentence) commit message summarizing the "why". No emojis.
3. Commit with the Co-Authored-By trailer:
   ```
   Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
   ```
4. Run `git push`. If the upstream is not set, use `git push -u origin HEAD`.

### Step 3: PR auto-detection

1. Get the current branch: `git branch --show-current`.
2. If the branch is `main` or `develop`, skip PR creation (just push).
3. Otherwise, check for an existing PR:
   ```bash
   gh pr list --head <current-branch> --json number --jq length
   ```
4. If no existing PR (length is 0), create one:
   - Generate a title (<70 chars) and body from `git log develop...HEAD --oneline` and `git diff develop...HEAD --stat`.
   - Create the PR:
     ```bash
     gh pr create --base develop --title "<title>" --body "<body>"
     ```
   - The body should follow this format:
     ```
     ## Summary
     <1-3 bullet points>

     ## Test plan
     - [ ] `pixi run ci` passes

     Generated with [Claude Code](https://claude.com/claude-code)
     ```
5. If a PR already exists, do nothing (the push already updated it).

Report the final result: commit SHA, branch name, and PR URL (if created).
