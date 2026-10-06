# Mason-BMAD Fork — STATUS

> Update this file whenever you ship a change to the fork, absorb upstream, or change the shipped/designed status of a feature. The `mason-bmad-workflow-expert` skill reads this file on every invocation as ground truth for volatile state.

**Last updated:** YYYY-MM-DD by <name>

---

## Now

The compact, always-current state — the skill reads THIS block + the top of `## Changelog` on every invocation. Keep it short.

- **Latest wave:** <one line + commit>
- **Fork vs upstream:** see `## Versioning`.
- **Owed / in-flight:** see `## In-Flight Work`. Skill `last_verified_against_fork_commit` = <commit>.

## Changelog

Newest first. **One discrete entry per wave** — never a single run-on line (that is the anti-pattern this section exists to prevent):

```
### YYYY-MM-DD — <title> (`commit`)

<bounded paragraph: what · why · scope · delivery (pushed/synced) · self-review verdict>
```

Keep ~12 entries here; when it grows past that, move the oldest (newest-first order preserved) into `STATUS-archive.md`. The archive is read on demand only, never on the skill's hot path.

---

## Versioning

- **Upstream BMAD version tracked:** v6.x.x
- **Fork base snapshot:** v6.x.x (date)
- **Commits behind upstream:** N
- **Commits ahead of upstream:** N
- **Last upstream sync attempted:** YYYY-MM-DD (result: absorbed / deferred / blocked-by-X)

## Shipped Features

Mark each as ✅ shipped, 🟡 partial, 🔴 not started.

> **Status-integrity rule (fork-gap #7 — checked, not asserted).** A feature is ✅ only if a COMMIT implements it — cite it inline as `built: <commit>`. "Designed", "machinery complete", "ready", or "scaffolded" without a commit is 🟡/🔴 + `built: NO (designed only)`, never ✅. Phrase capability/migration status as *"built: <commit|NO>"*, never a bare "complete". Before writing ✅ or "complete", confirm the code path actually exists. This prevents the two failures this gap was logged for: a STATUS "machinery complete" that overstated an unbuilt delivery path, and stale "X is unsupported/orphaned" narrative that nearly drove a *destructive* revert because the code had already moved past it.

- [ ] Brief provenance contract (11-field frontmatter, 6 intake checks)
- [ ] design-handoff predecessor + supersession logic
- [ ] design-artifact-loop, design-synthesize, design-tuning intake checks
- [ ] Quick-dev grounding gate (Mode B)
- [ ] Quick-dev autonomy scoping (decision vs intent)
- [ ] sync-bmad-workflows.sh
- [ ] Worktree creation hook → auto-sync
- [ ] .gitignore entries for synced directories in consuming projects

## Designed but Not Yet Shipped

- [ ] `project_phase: greenfield | brownfield | mixed` config flag
- [ ] Quick-dev split into `spec-dev` and `direct-dev` entry points
- [ ] Maintenance pipeline: `maintenance-triage → tech-spec → spec-dev`

## In-Flight Work

Track PRs or branches currently being worked on so the skill knows what's mid-change.

- (none) / branch-name → short description → status

**Parked cross-repo decisions.** A deferred cross-repo decision MUST name the exact file(s) in each repo whose current state its premise depends on. A resuming session opens those files from the canonical branch (`origin/main`, or the fork's `myfork/custom`) before proceeding — never from thread memory or STATUS prose. If the premise moved, close the item as SUPERSEDED; do not execute the deferred action. Record shape + resume-time re-check: `parallel-sessions.md` §E6.

- (none) / decision → repos-involved → load-bearing premise (file[s]) → owner → parked-at

## Known Drift Across the 13 Projects

If any consuming project is out of sync with the current fork, note it here so workflows aren't authored against assumptions that don't hold everywhere.

- project-a: synced from commit abcdef, behind by N commits, reason: ___
- project-b: in sync

## Upstream Items Under Evaluation

Upstream changes you're considering absorbing. Each line: change → reconciliation difficulty → decision.

- v6.x feature X → low / medium / high → absorb / adapt / skip / undecided

## Recent Decisions Worth Remembering

Short bullet log of policy-level decisions made recently. Helps future-you and the skill stay coherent.

- YYYY-MM-DD: decided to {what} because {why}
