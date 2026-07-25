---
title: Manifest Multi-Writer Contract
description: Who may write a design-ingest / design-implement manifest, when, and what a second writer must do. Governs pass identity, append-only structure, concurrency detection, and commit hygiene for the shared write-back ledgers.
---

# Manifest Multi-Writer Contract

**Applies to:** `design-ingest-<slug>.md` (the ingest manifest and its apply ledger) and
`design-implement-grid-<slug>*.md` (the URL-path apply ledger). Schema of the artifact itself
lives in `custom/workflows/implement/design-ingest/manifest-schema.md`; this document governs
**concurrent authorship** of it.

## The gap this closes

A manifest is a **shared, hand-versioned write-back ledger** and multi-writer is its *designed*
operating mode — the whole reason the manifest path exists is that a large surface needs many
passes across many sessions. It was also the one mode the artifact contract never specified.

Recorded twice inside ~90 minutes on 2026-07-20 (`design-ingest-clerk-receive.md`, cash-recovery),
across four concurrent sessions:

- **Pass numbers were derived by read-and-add-one** — read the file, find the highest `Pass N`,
  write `N+1`. That is a read-modify-write race with no lock. Two sessions doing legitimately
  *different* work both computed `Pass 4`; an hour later two more both computed `Pass 5`.
- **Both writes survived the merge** — both sections appended at EOF in the same region, so git
  saw no conflict. The ledger ended up reading **Pass 5 → Pass 4 → Pass 5**: textually clean,
  semantically incoherent, because sections land in **merge order, not run order**.
- **Uncommitted edits were swept into another session's commit.** One session's pass sat staged
  in the shared main checkout, where it also blocked `git merge --ff-only origin/main` — local
  `main` could not advance without touching another session's in-flight work.
- **The authors were not even distinguishable.** Both sessions carried a
  `claude-session-20260720-1711…`-shaped header — a timestamp, not an identity, and provably
  non-unique under concurrency.

The expensive symptom is not the duplicate number. It is that **a lost or misordered ledger entry
is indistinguishable from a pass that was never run**, and the resume contract trusts exactly that
signal. A surface claim does not help: it gates the *surface*, and these sessions had every right
to be working on it. What was missing was a contract for the *artifact*.

## The contract

### 1. Per-pass identity is stamped, never derived

Every pass record carries an identity block immediately under its heading:

```markdown
### Pass 4 — 2026-07-20 · frame `process-station--scan-matched` (5 rows) · CHECKPOINTED
<!-- pass_id: 6ab32aad-20260720T171114Z | session_id: 6ab32aad
     author: claude-session-20260720-171114 | started_at: 2026-07-20T17:11:14Z
     frames: process-station--scan-matched | branch: feat/clerk-receive-scan-matched
     pr: 357 | seq: 4 | concurrent_with: a5d818bf-20260720T171100Z -->
```

| Field | Authority | Rule |
|---|---|---|
| `pass_id` | **identity** | `<session_id>-<UTC compact>`. Unique by construction. **Never** derived from the file's current contents. |
| `session_id` | **authoritative** | The harness-supplied `session_id`. The ONLY field any gate or reader compares. |
| `author` | display only | The `claude-session-<timestamp>` header. **Non-authoritative** — it is a timestamp, and concurrent sessions collide on it. Never key anything on it. |
| `started_at` | ordering | UTC ISO-8601 with `Z`, from the harness clock (`date -u`). Never local time, never naive. |
| `frames` | scope | The frame/section scope this pass claims. |
| `seq` | **derived** | The pass's position when records are sorted by `started_at`. Regenerable output, not identity. See rule 2. |
| `concurrent_with` | honesty | `pass_id`s whose scope overlapped in time. Present means run order between them is genuinely unknown — say so, do not invent one. |

The lesson is the WIP register's, one artifact later: `claimed_by` looked like identity and wasn't;
`claimed_at` looked like a comparable instant and wasn't. **A field an agent computes from shared
state will eventually collide, and anything a gate keys on must be stamped by the harness.**

### 2. Append-only; pass numbers are computed, not written

- **New passes append. Existing pass records are never renumbered, reordered in place, or
  re-identified.** Renumbering is what produced `Pass 5 → Pass 4 → Pass 5`.
- **A pass number, if kept, is a rendered index — `seq`, derived from `started_at` ordering.**
  It is regenerable and carries no meaning beyond position. Identity is `pass_id`.
- **File order should equal run order.** When it cannot (a record lands after a later-started one
  because of merge order), the out-of-order record carries an explicit `run order ≠ file order`
  note naming the pass it followed. Silence here is the failure — a future session resuming from
  this ledger must be able to tell what happened when.
- **Legacy `### Pass N` headings are grandfathered and frozen.** Do not retro-fix them; migrate
  once, deliberately, recording `legacy_heading:` in the identity block (see the worked migration
  in `design-ingest-clerk-receive.md`).
- **Per-row grid dispositions are NOT pass records.** The `(frame, section)` scaffold rows stay
  mutable — that is the resume state, owned by whichever pass applies the section. Only the pass
  narrative is append-only. Keeping the two roles separate is what stops a benign concurrent
  append from becoming data loss.

### 3. Concurrency: detect, then reconcile explicitly

A **current-editor marker** — one lock file per manifest:

```text
<main-checkout>/.claude/manifest-locks/<manifest-basename>.lock.json
{ "manifest": "...", "session_id": "<harness id>", "acquired_at": "<UTC Z>", "intent": "frames=..." }
```

- **Location is deliberate.** Resolved via `git rev-parse --git-common-dir`, exactly like the WIP
  register — so a lock taken inside a worktree is visible to every other session *immediately*,
  with no commit and no push. The manifest itself carries only durable pass records; the lock is
  ephemeral coordination and is **not committed**. Keeping them separate means the coordination
  channel can never itself become a merge conflict.
- **Acquire before the first write; release at handoff.**

  ```bash
  python3 ~/.claude/hooks/manifest-contract-gate.py --acquire <manifest> --intent "frames=a,b"
  python3 ~/.claude/hooks/manifest-contract-gate.py --release <manifest>
  python3 ~/.claude/hooks/manifest-contract-gate.py --status
  ```

- **A live lock held by another session forces explicit reconciliation — never a silent merge.**
  Coordinate scope, pick a non-overlapping frame, or wait. (The mitigation that actually worked on
  2026-07-20 was exactly this, performed by hand: a session read the register, saw three live
  claims, and deliberately took the one frame outside every declared scope. This makes that
  systematic.)
- **No session may clear another session's marker.** The CLI refuses it. A gate the governed agent
  can unlock is not a gate.
- **Stale is not free.** A lock older than 90 minutes is *stale*, not absent: record a takeover in
  `takeover_of` rather than deleting it silently.
- **Unparseable or future-dated is UNKNOWN, never young.** A naive/local timestamp written with a
  `Z`, or a clock beyond ~2 minutes of skew, is a FORMAT ERROR — warn and treat the manifest as
  possibly held. The forbidden failure mode, by name: **"youngest claim wins."**

### 4. Shared-checkout hygiene: the index and the tree, not just the manifest

The manifest is the loudest instance, not the boundary. **One working checkout has ONE index and
ONE tree, shared by every session in it** — so the same three rules protect workflow files,
`docs/fork-gaps.md`, `STATUS.md`, and anything else under contention. Rules 4a–4c are general;
the manifest is simply the file where getting them wrong is most expensive.

**4a. Stage and commit by explicit path.**

- **A manifest is committed or explicitly left out — never swept.** Before any broad
  `git add -A` / `git add .` / `git commit -a` / `git stash` / `sync-bmad-workflows.sh`, a dirty
  manifest must be either staged **explicitly by path** (`git add -f <manifest>` — it lives under
  gitignored `_bmad-output/`) if this session owns it, or left out of the commit entirely.
- **The same applies to every file, not only manifests.** Never `-A`, never `.`, never a bare
  directory.
- **Commit in ONE step: `git commit -- <explicit paths> -m …`. Do not `git add` and then commit.**
  The gap between the two commands *is* the sweep window: your files sit in the shared index, and
  any session that runs a bare `git commit` in that interval carries them under its own message.
  A path-scoped commit ignores the rest of the index entirely, so it is safe in both directions —
  it cannot scoop a foreign staged file, and a foreign bare commit cannot scoop yours after it.
- **Caveat, same day: the path-scoped form is currently UNRELIABLE in the fork repo.** `git commit -m … -- <paths>` failed **four consecutive times** with the intermittent `invalid object … Error building trees` naming an unrelated untracked path (`.claude/skills/bmad-example/SKILL.md`), including after a `git read-tree HEAD` ruled out a stale index cache-tree — the object is absent from HEAD, the index, the working tree and the stash list, and `git fsck --connectivity-only` reports no missing reachable object. The plain staged form (`git add <explicit paths>` then `git commit`) succeeded immediately. So in THIS repo, until that failure is root-caused (fork-gaps 2026-07-20, explicitly not root-caused), the working order is: **`git add <explicit paths>` and commit in the very next command, with nothing else staged.** That keeps the sweep window to a second or two instead of eliminating it. Still never `-A`, never `.`, never a bare directory — the narrowing is what matters most, and the one-step form remains correct wherever it works.

  **Evidence (2026-07-25, third firing):** the commit that introduced *this very rule* was written
  as `git add … && git commit …` and was swept mid-window into another session's
  `docs(status): record the viewport artifact-labeling wave`. Nothing was lost — both files are
  intact on HEAD — but the fix for index-sweeping is recorded in the history as somebody else's
  STATUS.md update. Two-step staging is the whole of the exposure.
- **Never `git reset --soft` in this checkout.** It deliberately *leaves* changes staged, widening
  the window where another session's bare commit sweeps them. Use `git restore --staged <path>`
  (or `git reset --mixed <path>`) and re-add by path. Observed 2026-07-25: an un-scoop via
  `reset --soft` was itself swept, twice, inside one window — every change survived on HEAD, but
  under two unrelated sessions' commit messages.
- **Un-ID'd dirty pass records block nothing but must be surfaced**: if the working tree holds
  manifest changes whose authorship cannot be established, a sweep that includes them is a scoop.
  Establish authorship (stamp the identity block) or exclude the file.
- **The sync's skip-if-dirty guard is not this guard.** It protects the *sync target*; this
  protects the *other writer*.

**4b. Do not diagnose from a file you did not stage while your own commit is in flight.**

A commit in this checkout runs the pre-commit chain, and hook tooling may rewrite the tree
underneath every other session (this is why the fork now runs `lint-staged --no-stash`). Inside
such a window a foreign file can read as an *earlier* version of itself: syntactically valid, at
the right path, with a plausible bug — and nothing signals that you are reading a restored backup.
Observed 2026-07-25: a source file and the gate that requires it both read as broken for ~40s
during the reading session's own commit, and the conclusion "the armed gates do not parse" was one
step from being reported. **Retry the read before forming any claim about a file you did not
stage**, and never close or open a gap on a single such observation.

**4c. Expect the tree to be dirty with work that is not yours.**

The fork's pre-commit prints a `foreign-dirty` line naming how many paths are dirty outside the
staged set. It is warn-only and never blocks — its whole job is to make the shared-tree assumption
visible at the moment it matters. A non-zero count is normal, not an error; it means *those paths
belong to someone else right now*.

## Enforcement — honest tiers

| Layer | Mechanism | Class |
|---|---|---|
| Structural rules R1/R2 (identity present, append-only) | `manifest-contract-gate.py` PreToolUse(Edit\|Write) pattern check | **DETERMINISTIC detection**, WARN-only action |
| R3 concurrency (lock held / conflict / stale / format) | same hook, reads the main-checkout lock | **DETERMINISTIC detection**, WARN-only action |
| Commit hygiene | same hook, PreToolUse(Bash) on sweep-shaped commands | **DETERMINISTIC detection**, WARN-only action |
| No session clears another's marker | CLI `--release` refusal | **DETERMINISTIC** |
| At-rest lint | CLI `--check <manifest>` (un-ID'd records, duplicate ids, seq out of order) | **DETERMINISTIC** |
| Taking the lock at all; reconciling a real concurrent edit; deciding run-order semantics between genuinely concurrent passes | workflow prose + this document | **PROBABILISTIC** |

**What is guaranteed and what is not.** The hook *fires* deterministically on every violating
tool call — that part cannot be skipped. It *warns*; it does not deny, so the model can still
proceed. And it can detect the *shape* of a violation, never the *judgment*: whether two
overlapping passes should have run in the order they did, and how to reconcile them, is human and
model work that no matcher replaces. Distribution note: the hook lives in `~/.claude/hooks/` and
is wired in `~/.claude/settings.json` — **machine-local, and it does NOT ride the fork sync.**
Authoring this document does not ship the gate.

### Promotion criteria — WARN to DENY

Same ladder as the collision guard, and for the same reason: a gate that false-fires gets switched
off, permanently, usually along with everything else in the file.

Promotion of R1/R2 (identity + append-only, the two purely structural checks) to
`permissionDecision: "deny"` requires **both**:

1. **A false-positive rate indistinguishable from zero** over ≥14 consecutive days AND ≥20 sessions
   that actually edited a manifest, across ≥3 distinct `session_id`s. Any confirmed misfire resets
   the window to zero.
2. **No lock-file corruption events** in that window — no lost markers, no overwritten owners, no
   cross-session release.

**R3 (lock) and the Bash sweep matcher stay permanently WARN-only.** R3 depends on a marker a
session must choose to take, so denying on its absence would punish the honest path and make the
bootstrap deadlock the collision guard already hit. The Bash matcher is a documented heuristic —
it matches a command *shape*, and correct classification needs real shell parsing.

Promotion is a one-line change in the hook's `warn()` — deliberately small, so the *decision*
carries the weight rather than the diff.

## Golden cases

`~/.claude/hooks/manifest-contract-gate.test.sh` — 12 cases, all green as of 2026-07-25.

| # | Case | Expected |
|---|---|---|
| 1 | Two sessions both reach for the same pass slot: A holds the lock, B appends anyway | **WARN** R3 concurrent editor — name A's session + intent, require explicit reconciliation, never a silent merge |
| 2 | A session hand-renumbers an older pass (`Pass 5` → `Pass 4`) | **WARN** R2 append-only violation — cite the 2026-07-20 recurrence; append instead, `seq` is derived |
| 3 | A new pass appended with no identity block | **WARN** R1 un-ID'd record — show the stamp form; identity is never "highest N + 1" |
| 4 | A sweep (`git add -A`, or `sync-bmad-workflows.sh`) over a dirty manifest carrying un-ID'd records or a foreign lock | **WARN** commit hygiene — stage explicitly by path or exclude the file |
| 5 | Well-formed append, lock held by this session | **SILENT** |
| 6 | Grid-scaffold row flipped `UNVERIFIED` → `✓ applied` | **SILENT** — resume state is mutable by design |
| 7 | Any non-manifest file | **SILENT** |
| 8 | Narrow explicit staging (`git add -f <manifest>`) | **SILENT** — this is the prescribed behaviour |
| 9 | Malformed stdin | **SILENT** (fails open) |
| 10 | Session B tries to `--release` session A's lock | **REFUSED** |
| 11 | `--check` on a `Pass 5 → Pass 4 → Pass 5` file | **DETECTED** (out-of-order derived seq) |

Cases 5–9 are the ones that keep the gate alive: a manifest gate that fires on normal ledger work
gets disabled, and it takes the real signal with it.

## Override

`MANIFEST_CONTRACT_OFF=1` silences the hook. The override is **logged** to
`~/.claude/logs/manifest-contract-gate.jsonl` (metadata only — event, tool, timestamp; never
manifest content), alongside every warn. A hard gate with no override gets ripped out; a silent
override defeats the audit.
