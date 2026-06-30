---
name: parallel-sessions
contract_version: 1
description: 'Shared protocol for implementation and review workflows that run while OTHER agent sessions edit the same repo concurrently. Covers (A) src-editing workflows — enter a worktree before editing, integrate an advancing main before delivery, and resolve the named collision classes instead of halting; (B) artifact workflows — race-safe sprint-status edits and lane claiming; and (C) story claim + reconcile — atomically claim a story before working it, refuse one already held by a live session, and reconcile the story-file Status vs sprint-status on entry (heals the "done-but-unchecked" and "claimed-but-zombie" drift classes). Composes with worktree-portability.md (path mechanics) and delivery-to-main.md (artifact/PR delivery). Referenced by quick-dev (step-03 execute, step-07 deliver), quick-spec, code-review, dev-story (step-01 claim, step-04 reconcile).'
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
- **§C** — any **sprint-driven implementer that picks a story from `sprint-status.yaml`**: `dev-story` (and any future workflow that auto-discovers "the next ready story"). §C runs at story selection (claim) and on entry (reconcile); it composes with §A's worktree (the claim's `session=` reuses the worktree branch slug — one identity, no double-warn).
- A workflow that does several of these applies all of them. `dev-story` applies §A (it edits `src/`) **and** §C (it claims a story); a `quick-dev` run driven straight from a tech-spec (not from sprint-status) applies §A only.

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

> **The same "`main` moves under you" hazard applies to the DEPLOY lane, not just the merge.** A `manual_cli` deploy (`railway up`) ships the working tree at invocation time while a parallel session can fast-forward local `main` mid-deploy — so a verify step that re-reads live `HEAD` mis-reads a just-shipped deploy as stale. A deploy is therefore a single-driver critical section through verification, and the verify must compare prod against the **SHA captured at deploy time**, never a re-read of `HEAD`. Owned in `shared/deployment-to-prod.md` §3f — the deploy-lane sibling of the "worktrees isolate code, not state" hazard (the shared `main` pointer + the single prod target are the shared state here).

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

### B1a. Multi-line story prose does NOT belong in `sprint-status.yaml`

§B1's "edit one line, leave every other byte-identical" assumes **one value per line**. It breaks down for a per-story **multi-line comment block** (a reopen-note / status-rationale paragraph attached to one story key) — you can't edit a paragraph "byte-identical to every other line", so two sessions touching adjacent stories collide on the block. Two rules:

- **Prefer: keep the board one-line-per-key.** Story-level prose (reopen reasons, review notes, rationale) belongs in the **per-story `.md`** — where §C0 already makes the story file authoritative — not in `sprint-status.yaml`. The board carries `development_status[<key>]: <value>` (+ the §C1 claim *comment*, which is a single trailing line) and nothing multi-line. This keeps every board edit a true §B1 per-key line edit.
- **If a comment block must stay on the board:** treat it as **owned by exactly one story key and edited as a unit** — read-modify-write the whole block for *your* story only, asserting its prior content before replacing, and never span two stories' blocks in one edit. This is the carve-out to §B1's line rule, scoped to a single owner so it stays race-minimal.

### B2. Claim your lane before generating

When two sessions generate stories/epics for the same plan, **split the work explicitly first** ("agent A: epics 1–3; agent B: epics 4+") and write to per-item files (`<id>.md`), never a single shared document both append to. State the split in your output so the other session — and the user — can see the boundary. (This is the parallel-coordination half of the cash-recovery friction: the worktree discipline is §A; this is what keeps two story-generators from colliding.)

---

## §C — Story claim + reconcile (dev-story / any sprint-driven implementer)

**Why this exists.** §A keeps two sessions' *edits* from colliding; §B keeps their *sprint-status writes* from clobbering. Neither stops two sessions from **picking the same story** in the first place, and neither reconciles the two places a story's state is recorded. Both failures were observed live (cash-recovery, 2026-06):

1. **Drift — "done-but-unchecked".** `sprint-status.yaml` said `done`; the story `.md` said `Status: review` with every task checkbox empty — yet the code was built, reviewed, and merged. The two ledgers disagreed and nothing reconciled them to reality.
2. **Zombie claim.** `sprint-status.yaml` said `ready-for-dev`; the story `.md` said `Status: in-progress` with a `baseline_commit` set and ZERO commits. A session set the claim, then vanished. The next session could not tell a dead claim from genuine in-progress work.

Root cause: story discovery is "read sprint-status top-to-bottom, take the first `ready-for-dev`," with **no atomic claim** (nothing records WHO holds a story or detects a dead hold) and **two un-reconciled sources of truth**.

### C0. Source-of-truth rule

- The **story file `Status:` line is authoritative for the story's lifecycle** (`ready-for-dev` → `in-progress` → `review` → `done`). It is the per-story record of record, versioned alongside the code in the same branch/PR.
- `sprint-status.yaml` is the **shared index + claim ledger** — the only place a parallel session can see, in one read, what every other session is working and what is free. Its `development_status[<key>]` value mirrors the story file's lifecycle; it additionally carries the **claim token** (below).
- **On any disagreement, reconcile per C3 before doing anything else.** When evidence exists (commits past `baseline_commit`, checked task boxes, a merged PR), the evidence wins and BOTH ledgers are healed to match it. When there is no evidence, the more-conservative state wins (treat as un-started/free, not done).

### C1. The claim token — what "claimed" looks like

Do **not** invent a new top-level status value (existing readers parse the five-word vocabulary). Instead keep the value as the existing `in-progress` and attach an inline **claim token** as a trailing YAML comment on that one key — a §B1 per-key edit, byte-identical to every other line:

```yaml
  2-8-resolve-by-lpn: in-progress  # claim: owner=<user_name> session=<sig> at=<iso8601> baseline=<sha>
```

- `owner` — `{user_name}` from config (the human the session acts for).
- `session` — a stable per-session signature. Use the worktree branch slug when in a worktree (`git rev-parse --abbrev-ref HEAD`), else the controlling `claude` PID (`echo $PPID`), else `unknown`. The branch slug is preferred: it survives across the session and is what a teammate can `git worktree list` to verify.
- `at` — ISO-8601 UTC claim time.
- `baseline` — the `baseline_commit` captured at claim (mirrors the story-file frontmatter).

The token lives ONLY in the comment, so `development_status[<key>]` stays a clean `in-progress` for every existing reader. A read-modify-write that rewrites only this line (asserting its prior value first, per §B1) is the safe shape.

### C2. CLAIM — atomic, before any work

Run this the moment a candidate story is selected in discovery, **before** loading deep context, writing `baseline_commit`, or touching code:

1. **Re-read `sprint-status.yaml` fresh** (do not trust an earlier in-context copy — a parallel session may have just claimed).
2. **Inspect the candidate key's value + claim token:**
   - `ready-for-dev`, no token → **free. Claim it:** flip the value to `in-progress` and write the claim token (one per-key edit). Re-read the line back to confirm your token landed (last-writer-wins detection: if a different `session=` is now present, you lost the race — go to step 4).
   - `in-progress` **with a token whose `session=` is YOURS** → you already hold it (resume). Proceed.
   - `in-progress` **with a token whose `session=` is ANOTHER live session** (C4 dead-claim check says live) → **REFUSE.** Do not work this story. Return to discovery and take the next `ready-for-dev`. Emit: `⛔ {key} is claimed by {owner}/{session} since {at} — skipping to the next free story.`
   - `in-progress` **with a token whose session is DEAD** (C4) → **reclaim** after reconcile (C3): take over the token (rewrite `session=` to yours, keep/refresh `baseline` per C3's evidence check).
   - `in-progress` with **no token** (legacy, or claimed before this protocol) → treat as a dead/ambiguous claim: run C4; if no live session and no evidence of in-flight work, reclaim; if evidence exists, reconcile per C3.
   - `review` / `done` → not claimable as fresh work; this is a reconcile case (C3) or a review-continuation (the workflow's own review-continuation path), not a claim.
3. **Worktree composition (no double-warn).** The claim is orthogonal to §A1's worktree. The `session=` signature *reuses* the worktree branch slug, so claiming inside the worktree you opened in §A1 is one identity, not two. Do NOT open a second worktree for the claim and do NOT re-emit the parallel-session warning — §A1 already entered the worktree; C2 just records who holds the story in the shared ledger. If `ps`-based detection says you are the only `claude` session, still write the token (a claim of one is free and makes the next arriving session safe).
4. **Lost the race** → return to discovery, pick the next free story, repeat C2. Never two sessions on one key.

### C3. RECONCILE — on entry, heal the two drift classes

Before claiming (or immediately after, for a `review`/`done` candidate), reconcile the candidate's story-file `Status:` against its `sprint-status` value. Gather evidence once:

- `git log {baseline}..HEAD --oneline -- <story's code paths>` (or, if delivered, `git log --all --oneline` for the merged PR) → are there commits past baseline?
- Story file task checkboxes → any `[x]`? all `[x]`?
- Is there a merged PR / a "Senior Developer Review (AI)" section?

Then:

- **Class 1 — "done-but-unchecked" (sprint says `done`/`review`, story says an earlier state, but evidence shows work landed).** The evidence is authoritative. Heal BOTH ledgers UP to the evidenced state: set the story-file `Status:` and `development_status[<key>]` to the highest justified value (`done` if a merged PR exists, else `review` if implementation is complete), and check the task boxes that the merged code satisfies (or, if you cannot verify each task individually, add a Dev Agent Record note: `Reconciled: status set to {x} from merge evidence {sha/PR}; task boxes not individually back-verified`). **Do NOT silently re-open** a story that is actually finished. Emit a reconcile note naming the evidence. This is NOT a claim — a reconciled-to-`done` story is removed from the candidate pool.
- **Class 2 — "zombie claim" (sprint or story says `in-progress`/claimed, `baseline == HEAD`, zero commits past baseline, no checked boxes).** There is no work to preserve. If C4 says the holding session is dead (or there is no token): **reset to free** — clear the claim token, set both ledgers back to `ready-for-dev`, and discard the stale `baseline_commit` from the story-file frontmatter (it will be re-captured at the next real claim). Then C2 may claim it cleanly. Emit: `🧟 {key} was a stale claim (baseline==HEAD, no commits, holder dead) — reset to ready-for-dev.`
- **No drift** (both ledgers agree, or the only difference is the lifecycle step this run is about to perform) → nothing to heal; proceed.

Reconcile edits to `sprint-status.yaml` are §B1 per-key edits. Reconcile edits to the story file touch only the permitted areas (Status, frontmatter `baseline_commit`, Tasks/Subtasks checkboxes, Dev Agent Record).

### C4. Dead-claim detection — zombie vs genuine in-progress

A claim is **live** if ANY of these hold; otherwise treat it as **dead**:

- Its `session=` is a worktree branch that still exists: `git worktree list --porcelain | grep -q <branch-slug>` → live. (A worktree present means a session is — or recently was — actively on it.)
- Its `session=` is a PID that is still a running `claude` process: `ps -p <pid> -o comm= 2>/dev/null | grep -q claude` → live.
- The claim `at` timestamp is **recent** (within a freshness window — default **2 hours**) AND there is evidence of progress (commits past `baseline`, or checked boxes) → live (an active session that simply hasn't updated the ledger this minute).

Dead signals (the zombie shape from incident 2): worktree branch gone AND PID not running (or `session=unknown`), `baseline == HEAD`, no commits, no checked boxes, `at` older than the freshness window. When dead, C2/C3 may reclaim or reset.

**Conservatism rule:** if liveness is genuinely ambiguous (e.g. `session=unknown`, no worktree, but `at` is 10 minutes old) prefer to **skip to the next story** rather than reclaim — refusing costs you one story; stealing a live claim corrupts a peer's run. Only reclaim on a clear dead signal.

## §D — Authoring a shared standard/workflow in the fork

Fork edits (`~/bmad-method-v6/`) are deliberately hook-allowlisted — no worktree is required — which is convenient but removes the *only* collision protection. Two cold sessions pointed at the same gap can both author the same new standard into `custom/workflows/shared/`, duplicate the ID space, and collide. This happened once (one session wrote `claude-md-charter.md`/`STD-CLAUDEMD-001`, another `claude-md-standard.md`/`STD-CLAUDE-001`), caught only by a lucky re-read.

### D1. Before authoring a NEW shared standard/workflow — claim it
1. **Check for an in-flight twin.** `grep` `STANDARDS.md` for the topic/ID, scan recent commits (`git log --oneline -10`), and check **uncommitted shared/ work**: `git -C ~/bmad-method-v6 status --porcelain -- custom/workflows/shared custom/skills-native/_shared`. A foreign untracked file there is another session mid-authoring.
2. **Claim up front.** Decide the ID (`STD-<AREA>-NNN`) and Home filename, and add the STANDARDS.md index block *first* (or a one-line "being authored" note) before writing the Home doc — so a second session greps and sees it.
3. The **`check-fork-authoring-collision`** hook (PreToolUse) surfaces this automatically: it nudges when you edit a shared/ file while another session has uncommitted shared/ work you haven't touched (a per-session ledger avoids flagging your own multi-file edit). Awareness only — it never blocks.

### D2. When a collision DID happen — dedupe convention
**Defer to the most-integrated, then fold in.** The version that is committed/pushed/synced is the keeper (reconciling around an integrated artifact is cheaper than re-integrating). Fold any genuinely-better content from the loser into the keeper, purge the duplicate everywhere (incl. synced project copies + the skills mirror), and keep the collision logged in `docs/fork-gaps.md`. Don't re-litigate the keeper choice each time.

### D3. Commit fork edits ATOMICALLY — never leave files staged across a tool boundary
Fork edits share **one working tree + one index** across all sessions (the worktree exemption that makes D1 necessary also means `git add` is global to the repo). So if you `git add` your files and a parallel session runs *its* `git commit` before you commit, that commit sweeps up **your** staged hunks under **its** message — wrong provenance, and a latent partial-commit/lost-work hazard. This happened once (a `docs(status)` commit absorbed another session's 6 staged standard files).

**Rule: stage and commit as one atomic step that names only your paths — never `git add` then commit in separate steps.**
- Use `git commit -o <path>...` (`-o`/`--only` commits *only* the named paths regardless of what else is staged), or `git commit <explicit paths>`. Both stage-and-commit the named files in one operation and ignore the rest of the index.
- If a pre-commit hook forces a message via stdin/heredoc, the message-bearing-VCS exemption in the bash edit-guard already lets `git commit -F - <<MSG` through — combine it: `git commit -o <path> -F - <<MSG … MSG`.
- **Before committing, if anything outside your paths is `M`/`A`/staged, that's another session's work** — confirm `-o`/explicit-path scoping caught only yours (`git show --stat HEAD` after) so you didn't commingle.

## §E — Ad-hoc quick-flow claim (quick-spec / quick-dev from a tech-spec, NOT a sprint story)

§C makes a session claim a **sprint story** before working it. But a `quick-dev` run driven straight from a tech-spec (and the `quick-spec` that authored it) is explicitly §A-only — it touches `src/` but claims *nothing*, because there is no sprint-status key to attach a token to. That is a real blind spot: two sessions can pick the same tech-spec-shaped feature and build it twice, and one build is thrown away (the incident that motivated this section — two independent implementations of the same listing failure-reason surface).

§E closes it with an **awareness register**, not a gate. "Same feature" is not deterministically detectable (two sessions name their branches differently), so this surfaces in-flight work and lets a human/agent judge overlap — it never blocks (a hard block here would be the indiscriminate-gate anti-pattern).

### E1. The register — shared, auto-written
- Ledger: **`<main-repo>/.claude/wip-register.yaml`** — anchored at the MAIN checkout (resolved via `git rev-parse --git-common-dir`) so a claim written from any worktree is visible to every other session. NOT per-worktree `_bmad-output` (gitignored + not shared → the exact blindness this fixes). Safe from sync (`rsync --delete` only touches `.claude/{skills,commands,worktrees}`).
- **Written deterministically by the `EnterWorktree` PostToolUse hook** (`wip-claim-on-worktree.sh` → `wip-register.sh claim`): worktree creation is the only reliable "feature work starting" signal, so the claim does not depend on a workflow step the agent might skip. One flow-map line per worktree path: `branch / worktree / session / baseline / started / description`.
- **Dead claims self-collect:** a claim whose worktree directory no longer exists is pruned on the next write and filtered at read time — so `ExitWorktree`/removal needs no extra hook.

### E2. Surfaced at SessionStart (awareness, tier 4)
The `check-wip-register.sh` SessionStart hook prints any LIVE foreign claim (worktree still on disk; your own is hidden) into the arriving session's context: branch + description + age. **This is DETERMINISTIC delivery of AWARENESS, not a gate** — acting on it is the model's choice. Enforcement honesty: there is no deterministic "same feature" test, so there is deliberately no PreToolUse block.

### E3. What quick-spec / quick-dev do (the probabilistic enrich + check layer)
- **quick-spec step-01 / quick-dev step-03**, after entering the worktree: (a) `wip-register.sh enrich <main_root> <worktree> "<one-line feature description>"` so the bare auto-claim gains human intent; (b) **read `.claude/wip-register.yaml` first** — if another live claim plausibly covers the same feature/area, surface it to the user before building, rather than duplicating it blind. This is the check that turns the SessionStart awareness into a decision.

### E4. Distribution (do not confuse the two tracks)
The **hooks** (`wip-register.sh`, `check-wip-register.sh`, `wip-claim-on-worktree.sh` + their `settings.json` entries) ship on the **global hooks track** (`install-global-assets.sh`), machine-local — they do NOT sync to the projects. The **prose** in this file + the quick-spec/quick-dev step edits ship on the **workflow-sync track** to the 13 projects. Both must land for the behavior to be whole.

## Costs

- A worktree per src-editing run — cheap, and the project `CLAUDE.md` already mandates it; §A1 just moves it from "the human remembered" into the workflow.
- One fresh `sprint-status.yaml` re-read + a single per-key claim edit at story start (§C2), plus an entry-time reconcile pass (§C3) — seconds. The alternative is two sessions on one story, or a zombie claim no one can clear.
- An integrate-and-re-gate pass before each delivery — seconds to minutes. The alternative is a stranded branch.
- A little more delivery logic in the workflow. Worth it: the failure it prevents — finished, tested work halted because `main` moved one commit — is the most demoralizing one in the implement loop, and it is fully mechanical to avoid.
