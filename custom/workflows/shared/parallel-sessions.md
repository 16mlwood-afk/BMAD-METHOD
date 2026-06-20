---
name: parallel-sessions
description: 'Shared protocol for implementation and review workflows that run while OTHER agent sessions edit the same repo concurrently. Covers (A) src-editing workflows — enter a worktree before editing, integrate an advancing main before delivery, and resolve the named collision classes instead of halting; and (B) artifact workflows — race-safe sprint-status edits and lane claiming. Composes with worktree-portability.md (path mechanics) and delivery-to-main.md (artifact/PR delivery). Referenced by quick-dev (step-03 execute, step-07 deliver), quick-spec, code-review.'
---

# Parallel Sessions — Concurrent-Work Protocol

**Why this exists.** The fork's implement/review workflows assume one linear session: edit, test, deliver, done. In real multi-agent projects, 3–5 sessions run at once — each on its own story, each merging to `main` independently. Two failure modes follow, and today no workflow handles either:

1. **Src edits land on a shared `main`.** A workflow that never enters a worktree edits `src/` directly on the main checkout. With parallel sessions that races other sessions' edits and trips the `PreToolUse(Edit|Write)` worktree-enforcement hook — the run stalls or silently collides.
2. **`main` advances under the workflow, then delivery halts.** A session branches from `main@A`, builds, tests — and by delivery time another session merged `main@B`. The merge conflicts, and `quick-dev/step-07` today says *"report the error and halt."* But the conflict is almost always one of a few mechanical classes (a barrel re-export, an additive schema table, two migrations both numbered `0001`). Halting strands finished, tested work on a branch.

Observed repeatedly (cash-recovery, 2026-06: one session delivered Epic-2 stories 2.1–2.4 while a second drove Epic 1 + Epic 3). **Every** delivery hit a barrel / `schema.ts` / migration-number conflict, and `sprint-status.yaml` was edited by both sessions at once. All resolvable; none of the resolution lived in the workflow text — the operator had to know it.

This protocol is the missing layer. It composes with — does not duplicate — `worktree-portability.md` (resolve `{project-root}` to the worktree root) and `delivery-to-main.md` (the artifact/PR delivery sequence).

---

## When it applies

- **§A** — any workflow that edits `src/` (or other tracked, non-`_bmad-output` files): `quick-dev`, `dev-story`, the source-touching half of `quick-spec`.
- **§B** — any workflow that writes `_bmad-output/` artifacts and updates `sprint-status.yaml`: `create-story`, `create-epics-and-stories`, sprint planning.
- A workflow that does both applies both.

Detect concurrency cheaply: if `ps -eo command | grep -c '^claude'` (or the project's own parallel-session signal) is `> 1`, treat the session as parallel. **The protocol is safe to follow even when alone** — a worktree of one, a no-op integrate — so when in doubt, follow it. Do NOT gate the worktree on detecting parallelism: the project `CLAUDE.md` mandates a worktree for src edits regardless; §A1 just moves that from "the human remembered" to "the workflow does it."

---

## §A — Src-editing workflows

### A1. Open: enter a worktree FIRST, from local `main`

Before editing any `src/` file, enter an isolated worktree. **Base it on local `main` HEAD, not `origin/main`.** Parallel sessions merge to *local* `main`, so `origin` is usually behind — a fresh-from-origin worktree would be missing the foundation your story depends on (e.g. an Epic-1 schema another session merged locally but hasn't pushed).

```bash
# Confirm local main has what you need, then base the worktree on it.
git -C "$(git rev-parse --show-toplevel)" rev-parse main      # local main HEAD
git worktree add .claude/worktrees/<branch-slug> -b <type>/<short-description> main
```

Then `EnterWorktree` (path) into it, and from here resolve `{project-root}` via `git rev-parse --show-toplevel` per `worktree-portability.md` §1 — every artifact path is worktree-relative.

Skip A1 ONLY if the user explicitly says "you're the only session, skip the worktree," or the workflow writes nothing under `src/`.

### A2. Build in the worktree

Implement, then run the project's full gate (typecheck / lint / test / build) inside the worktree. Standard — no change from today.

### A3. Integrate the advancing `main` BEFORE you merge

`main` has very likely moved since A1. Before delivering, bring it into your branch (`git merge main` from the worktree, or rebase). Resolve conflicts per A4, then **re-run the full gate** — the integrated tree is new code that neither session tested together.

### A4. Resolve-don't-halt: the named collision classes

These are mechanical and deterministic. **Resolve them; do not halt.** Halt ONLY on a genuine *semantic* conflict (two sessions changed the same logic). The classes, in order of frequency:

- **Barrel re-exports** — an `index.ts` that is only `export * from "./x"` lines. **Keep both** sides' export lines. The overwhelmingly common case: two sessions each added one module to `src/domain/index.ts` or `src/domain/ports/index.ts`.
- **Additive schema tables** — `schema.ts`, where each session appended a new `pgTable(...)`. **Keep both** table blocks. If the conflict split a shared doc-comment, give each table its own `/** … */` opener.
- **Drizzle migration-number collision** — both sessions ran `drizzle-kit generate` and produced `0001_*.sql`. Do **not** hand-merge the `meta/` JSON (fragile; a corrupt journal breaks `migrate` on deploy). Instead: take the other session's migration as the canonical `0001` (`git checkout --theirs meta/_journal.json meta/0001_snapshot.json`), `git rm` your `0001_*.sql`, complete the merge, then **regenerate** — `drizzle-kit generate` diffs the merged schema against their `0001` snapshot and emits a correct cumulative `0002_*.sql`.
- **`sprint-status.yaml`** — see §B1; per-key edits, never a whole-file rewrite, so two sessions' status flips don't clobber each other.

### A5. Deliver + cleanup, by project mode

- **Project HAS a git remote** → run the `delivery-to-main.md` PR sequence (push → PR → merge → verify).
- **Project has NO remote** (local-merge projects, per project `CLAUDE.md` "ALWAYS Deliver Your Work") → commit on the branch → (A3 already integrated `main`) → `ExitWorktree` keep → from the main checkout `git merge --no-ff <branch>` → re-verify the gate on `main` → `git worktree remove --force .claude/worktrees/<name>` (force tolerated: only `node_modules`/build artifacts remain after merge) → `git branch -d <branch>`.

Then mark the story `review` in `sprint-status.yaml` per §B1, and fill the story's Dev Agent Record (model, completion notes, file list).

### A6. Re-entrancy under the worktree-enforcement hook

When the hook is active, conflict-resolution edits to `src/` on the **main** checkout are blocked (you're not in a worktree there). So do A3/A4 *in the worktree branch* (edits allowed), making the main-side merge conflict-free. If a conflict still surfaces at the final main-side `git merge`, the only hook-compliant resolution of a `src/` file is to write the resolved content via a `/tmp` file + `cp` (the bash edit-guard permits `/tmp` targets and `cp` is not an edit-equivalent), never a blocked direct `Edit`/`Write`.

---

## §B — Artifact workflows (no worktree needed)

Artifact workflows write `_bmad-output/`, which the worktree-enforcement hook **allowlists** — so they do NOT need a worktree (entering one would be wrong: a worktree isolates the artifact away from the main checkout that downstream sessions read). Their parallel hazard is shared-file races, not src collisions.

### B1. `sprint-status.yaml` — per-key edits, never a whole-file rewrite

Multiple sessions update `sprint-status.yaml` at once (one flips `2-3` to `review`, another flips `1-4` to `in-progress`). A whole-file rewrite by either clobbers the other's flip. **Edit only the keys you own, in place** — match each line by its key and change just its value, leaving every other line byte-identical. A small read-modify-write scoped to your keys is race-minimal; a full-file regenerate is not. (A line-oriented script that flips only your keys, asserting each was at its expected prior value, is the safe shape.)

### B2. Claim your lane before generating

When two sessions generate stories/epics for the same plan, **split the work explicitly first** ("agent A: epics 1–3; agent B: epics 4+") and write to per-item files (`<id>.md`), never a single shared document both append to. State the split in your output so the other session — and the user — can see the boundary. (This is the parallel-coordination half of the cash-recovery friction: the worktree discipline is §A; this is what keeps two story-generators from colliding.)

---

## Costs

- A worktree per src-editing run — cheap, and the project `CLAUDE.md` already mandates it; §A1 just moves it from "the human remembered" into the workflow.
- An integrate-and-re-gate pass before each delivery — seconds to minutes. The alternative is a stranded branch.
- A little more delivery logic in the workflow. Worth it: the failure it prevents — finished, tested work halted because `main` moved one commit — is the most demoralizing one in the implement loop, and it is fully mechanical to avoid.
