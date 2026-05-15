---
name: 'step-01-gather-context'
description: 'Detect what just happened — read handoff artifacts, git state, and categorize changed files'
---

# Step 1: Gather Context

**Progress: Step 1 of 4** — Next: Index Workflows (autonomous)

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Cast a wide net — gather everything, filter later.
- If a data source is unavailable (no handoff file, no recent commits), skip it and note its absence.

## SEQUENCE OF INSTRUCTIONS

### 1. Detect Trigger Source

Determine how this workflow was triggered. Check in order:

| Source | Signal | How to extract |
|--------|--------|---------------|
| **Handoff artifact** | User provided a path, or a handoff file was written in the last 30 minutes | Read the handoff file — it contains PR URL, spec path, gaps, follow-ups |
| **PR / branch** | User provided a PR number or branch name | `gh pr view {number} --json title,body,files` or `git diff main...{branch} --stat` |
| **Workflow name** | User said "I just finished quick-dev" | Check `{implementation_artifacts}` for the most recent handoff matching that workflow |
| **Git state** | Nothing explicit provided | `git log --oneline -10`, find the most recent merge or feature branch commits |

Store the trigger source type and raw data as `{trigger_context}`.

### 2. Identify Recent Handoff Artifacts

Scan `{implementation_artifacts}` for handoff files created in the last 24 hours:

```bash
find {implementation_artifacts} -name 'handoff-*.md' -mtime -1 -exec ls -lt {} + 2>/dev/null | head -5
```

If any exist, read the most recent one. Extract:

- **Source workflow** — which workflow produced this handoff (quick-dev, wire-check, etc.)
- **PR URL** — link to the merged PR
- **Gaps found & not fixed** — these are prime candidates for follow-up workflows
- **Recommended follow-ups** — the previous workflow's own suggestions
- **Strategic insights** — system-level observations that may warrant deeper investigation

Store as `{recent_handoffs}`.

### 3. Catalog Changed Files

Get the list of files changed in the most recent work:

**If a PR/branch is available:**
```bash
git diff main...HEAD --name-only
```

**If only recent commits are available:**
```bash
git log --oneline -1 --format=%H | xargs git diff HEAD~1 --name-only
```

**If a handoff references a PR:**
```bash
gh pr view {pr_number} --json files --jq '.files[].path'
```

Store the file list as `{changed_files}`.

### 4. Categorize Changed Files

Classify each changed file into categories using path patterns:

| Category | Path patterns | Significance |
|----------|--------------|-------------|
| **Backend API** | `src/routes/api/`, `server/`, `src/lib/server/` | Data shape changes — wire-check territory |
| **Frontend UI** | `src/routes/**/+page.svelte`, `src/lib/components/`, `client/src/` | Visual changes — design-review, trace-flow territory |
| **Database** | `migrations/`, `schema.ts`, `schema.prisma`, `drizzle/` | Schema changes — broad impact, many workflows relevant |
| **Shared types** | `src/lib/types/`, `shared/`, `*.d.ts` | Interface changes — wire-check for contract alignment |
| **Styles** | `*.css`, `tailwind.config.*`, `globals.css` | Visual-only — design-review territory |
| **Scripts/tooling** | `scripts/`, `*.config.*`, `.github/` | Infrastructure — rarely needs workflow follow-up |
| **Tests** | `*.test.*`, `*.spec.*`, `__tests__/` | Test changes — may indicate coverage gaps elsewhere |
| **Config/constants** | `constants.ts`, `config.ts`, `*.env*` | Shared state — check downstream consumers |

Count files per category. Store as `{file_categories}` — a map of category → file count + file list.

### 5. Assess Work Scope

From `{file_categories}`, determine the work's footprint:

- **Narrow:** 1-2 categories touched, under 5 files total — targeted change
- **Medium:** 2-3 categories, 5-15 files — feature work
- **Wide:** 4+ categories, 15+ files — large feature or refactor
- **Full-stack:** Both backend API and frontend UI categories have files — end-to-end wiring is likely

Store as `{work_scope}`.

### 6. Proceed to Index

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/orchestrate-workflows/steps/step-02-index-workflows.md`

---

## SUCCESS METRICS

- Trigger source identified and raw data captured
- Recent handoff artifacts scanned (last 24h)
- Changed files cataloged and categorized
- Work scope assessed (narrow/medium/wide/full-stack)
- All state variables populated: `{trigger_context}`, `{recent_handoffs}`, `{changed_files}`, `{file_categories}`, `{work_scope}`
