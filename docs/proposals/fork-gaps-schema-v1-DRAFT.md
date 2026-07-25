---
title: fork-gaps schema v1 (DRAFT — awaiting owner approval)
description: A typed entry schema for docs/fork-gaps.md that separates incident record, backlog item, and doctrine source; makes the header block mandatory and machine-checked; and fires the existing validators at write time instead of on a manual sweep.
---

# fork-gaps schema v1 — DRAFT

**Status: ACCEPTED and LANDED 2026-07-25 (`935395f8`).** Owner approved; the single-typed-ledger option was taken. 47 entries are migrated and the write-time gate is armed. This document is now the schema's reference description — the enforced definition lives in `tools/lib/fork_gap_lint.py`, and where the two disagree the code wins. Approve, amend, or reject before any bulk
migration. The one decision this proposal defers to Mason is at the bottom: **single typed ledger
vs split ledgers**.

**Problem this fixes** (evidence, 2026-07-25 fork-maintenance session): 5 of 6 entries opened were
already fixed and never closed; 1 entry claimed RESOLVED naming two artifacts that do not exist on
disk; the stale-open detector could see 15 of 48 entries because `Marker:` was documented optional;
6 `Target file:` pointers had rotted past a directory reorg; and closure state was living in
500-character backticked blobs welded to headings. None of that is entry-quality — the prose is the
best thing in the repo. It is a schema that is advisory, swept by hand, and unenforced at write time.

---

## 1. Entry shape — three blocks, three lifecycles

One entry, three named blocks. Physical file split is NOT required by this schema (see §6); the
roles are made explicit by block, and each block has its own mutability rule.

````markdown
## FG-2026-07-20-003 — the two most expensive workflows resolve a collision key in step-01 and never check it

```yaml
id: FG-2026-07-20-003
class: shared-state
scope: fork
target: custom/workflows/implement/design-ingest/steps/step-01-frame-inventory.md
marker: "5a. Concurrent-run check"
state: fork-fixed-distribution-owed
owner: fork-maintenance
distribution: "sync-bmad-workflows.sh (all 14 targets)"
```

### Incident            <!-- IMMUTABLE · append-only -->
What fought us, with evidence. Dates, numbers, quoted errors, what was ruled out.
Later observations are APPENDED as dated paragraphs. Nothing here is ever reworded,
summarized, or deleted — including corrections and retractions, which are themselves
evidence of how the understanding moved.

### Work                <!-- MUTABLE -->
**Status (2026-07-25):** one-line current truth. Replaces the heading blob.
Why it is structural. Candidate fixes. Enforcement tier, honestly labelled.

### Doctrine            <!-- OPTIONAL · collapses to a pointer once migrated -->
→ `docs/manifest-contract.md` §4a
````

**Why these three.** The reason entries accrete `CORRECTION` / `UPDATE` / `THIRD FIRING` /
`REOPENED` amendments forever is that one record is doing three jobs with three different
lifecycles — an incident that should never close, work that should, and reasoning that should
migrate out and leave a pointer. Separating them is what lets an entry finish.

**The Doctrine block is the only place deletion is allowed**, and only as replacement: when the
reasoning has been written into a real contract, the prose here is replaced by a pointer to it.
That is how the register stops being a second, drifting copy of the doctrine.

---

## 2. Header fields

| Field | Required | Type / allowed values | Notes |
|---|---|---|---|
| `id` | always | `FG-YYYY-MM-DD-NN` | Stable, never reused. The only thing other entries reference. |
| `class` | always | kebab slug, open vocabulary | Keep the current vocabulary (`shared-state`, `contract-dimension-gap`, `silent-partial-implementation`, `context-budget-overflow`, …). Open on purpose. |
| `scope` | always | `fork` · `project` · `machine-local` · `harness` | Where the fix LANDS, not what it is about. Drives filtering and distribution. |
| `target` | always | path, scope-prefixed when not `fork` | `custom/…` · `project:accounting-tools/CLAUDE.md` · `machine:~/.claude/settings.local.json` · `harness:EnterWorktree`. |
| `marker` | always¹ | string, ≥3 non-space chars | A string that WILL exist in `target` once fixed. **Must not already exist in `target` at log time.** |
| `state` | always | see §3 | |
| `owner` | always | `fork-maintenance` · `mason` · `project:<name>` · `harness-vendor` | Who moves it. Not who logged it. |
| `superseded_by` | iff `state: superseded` | an `id` | |
| `blocked_by` | iff `state: blocked` | one line, must name an **observable** condition | "PR #1118 merged", not "when we get to it". |
| `distribution` | iff `state: fork-fixed-distribution-owed` | the exact invocation owed | e.g. `sync-bmad-workflows.sh (all 14 targets)`. |
| `priority` | optional | free text | Existing habit; keep. Never load-bearing. |

¹ **The one marker exemption, by explicit rule:** `marker: n/a` is legal **only** when
`scope: harness` — there is no file we own to grep. The linter enforces the pairing, so the
exemption cannot spread by convention.

**Headings carry `id` + title only.** No state, no closure note, no backticked blob. Ever.

---

## 3. State model

| State | Meaning (one line) | Exit condition |
|---|---|---|
| `open` | Logged; nothing shipped; actionable now. | Someone does the work. |
| `blocked` | Owed, but not actionable until a named external condition clears. | `blocked_by` observably true. |
| `partly` | A named half shipped; another named half is still open. | The Status line must name BOTH halves. |
| `fork-fixed-distribution-owed` | Fix is on `myfork/custom` but has NOT reached the 13 synced projects. | The named `distribution` command runs. |
| `superseded` | No longer the right framing; a different entry now owns it. | `superseded_by` set. |
| `closed` | Fix VERIFIED by reading the implementing section — never a grep hit — and distribution done if it was a fork fix. | Terminal. Entry moves to the archive. |

**Justification for the sixth state (`blocked`) — the one addition beyond the five specified.**
`open` and `blocked` are both "not done", but they behave differently under triage: an `open` item
should be picked up, a `blocked` item should be *skipped without re-deriving why*. Without the
distinction, every sweep re-reads the same entries to rediscover that they cannot move. Two live
examples today: the accounting-tools canonical-home entry needs a PR in another repo, and the
collision-guard WARN→DENY promotion is blocked on a defined 14-day evidence window. Both would
otherwise sit in `open` and be re-examined every pass. The cost of the extra state is one enum
value; the cost of omitting it is a recurring re-derivation tax on every triage.

`fork-fixed-distribution-owed` is not cosmetic either — the register already contains an entry
complaining that "distribution owed has no OWNER" and that a deferred delivery step is shelved as
an open investigation. That entry is the missing state, described in prose.

---

## 4. Validation — three validators, fired at write time

Wire into `.githooks/pre-commit`: **when `docs/fork-gaps.md` is in the staged set**, run all three.
Cheap (only fires on commits touching the register) and it removes the manual-sweep dependency.
Keep the SessionStart surfacer for sweep mode.

### A. `check-fork-gap-schema.sh` — NEW. All ERROR (blocks the commit).

Everything it checks is mechanical and unambiguous, so nothing here is a judgement call:

- header block present and parses as YAML; `id` unique and well-formed
- every required field present; every enum value known
- conditional fields present (`superseded_by` / `blocked_by` / `distribution`)
- `marker` ≥3 non-space chars after trimming, or `n/a` with `scope: harness`
- heading contains no state blob (regex: a backticked `[…]` tail on a `## ` line)
- an `### Incident` block exists

### B. `check-fork-gap-targets.sh` — EXISTING. Mostly WARN.

- **ERROR** when `scope: fork` and the target does not resolve in the fork tree. That is rot, and
  it is exactly what six entries had.
- **WARN** for every other scope — a project or machine-local path legitimately does not resolve
  from here.

### C. `check-fork-gap-stale-open.sh` — EXISTING. Two modes, and this is the important one.

Same check, opposite meaning depending on when it runs:

- **At creation** (entry is new in this diff): the marker already exists in the target → **ERROR**.
  Either the marker is too generic to prove anything, or the gap is already fixed and should not be
  logged as open. *This single rule would have caught both bad markers I wrote today* —
  `.claude/worktrees/` (already in `onboard-project.sh`) and `inert-scope sweep` (already prose in
  a template).
- **On sweep** (pre-existing entry): the marker exists in the target → **WARN**, a stale-open
  candidate for human verification. Never auto-closes.

**How weak marker coverage is prevented, structurally:** `marker` is a required field, so the
schema linter blocks any entry without one — coverage cannot decay below 100%. The `n/a` escape is
pinned to `scope: harness`. And the creation-mode check above stops the *other* failure, a marker
that is present but proves nothing.

**Unchanged invariant:** the register never counts itself as evidence, and no detector ever mutates
the register or closes an entry. Closing stays a human call after reading the implementing section.

---

## 5. Migration contract (for later — not now)

**Preserve verbatim.** Every Incident sentence and evidence claim; all dates and numbers; every
`CORRECTION` / retraction / amendment block; every enforcement-tier statement; every author's
priority judgement and fix direction; the original title text after the em-dash; existing closure
notes — **relocated into `Status:`, not reworded**.

**May be normalized.** Heading state blob → `Status:` line in `### Work`. Existing
`**Class:** / **Fix scope:** / **Target file:** / **Marker:**` lines → header block fields.
Marker backtick and whitespace normalization. Adding a header field whose value is unambiguously
derivable from existing text.

**Must NOT be rewritten.** No summarizing, no merging two entries, no "tidying" prose, no dropping
a superseded observation because a later one contradicts it — the contradiction is the record.

**Unknowns are declared, never guessed.** A field that cannot be derived is written `unknown` and
listed in a migration report. Never infer an owner or a class.

**Mechanically checkable invariant:** for every entry, the post-migration body must contain every
pre-migration body line except the relocated heading blob. The migration script asserts this and
aborts on any loss — the same line-conservation check used for the archive moves this session.

**Delivery:** one commit, reviewable as a diff, revertible. The archive is not touched.

---

## 6. Scope discipline — recommendation: ONE typed ledger

**Recommend: a single ledger with mandatory `scope` typing, plus scope-filtered views.**

Reasons, strongest first:

1. **Cross-scope entries are real and their linkage is the valuable part.** The edit-guard gap
   spans project-local hooks, machine-local config, and fork doctrine; today it turned out that a
   2026-07-03 fork entry and a 2026-07-25 machine-local entry are *the same missing lane reached
   from a different tool*. A physical split forces an arbitrary home and severs exactly that
   observation.
2. **The pain is a query problem, not a storage problem.** "I read 45 to find the 20 that are
   actionable here" is solved by `--scope fork` on the surfacer, not by four files.
3. **Splitting multiplies the drift surface** — four files, four places for the schema and the
   How-this-works preamble to rot, and a scope field is still needed anyway (a `fork` entry can
   have a project-local half).
4. **Distribution is not an argument for splitting**: `fork-gaps.md` is fork-local and does not
   sync to any project today.

The honest counter-argument, so it is on the record: a single ledger keeps a fork-maintenance
session reading past ~25 entries it cannot act on, and if the project/machine-local population
keeps growing, that ratio gets worse. The trigger to revisit: **if non-`fork` entries exceed ~60%
of the open set, split then** — by which point the scope field makes the split mechanical.

---

## 7. Recommendation

**Schema first, migration later.** Approve or amend this document, then migrate in one reviewed,
line-conserving commit. Migrating before the schema is settled would mean touching all 45 entries
twice, and each touch of an immutable evidence block is a chance to lose the thing the register
exists to hold.

**Open decision for Mason:** single typed ledger (recommended above) vs split ledgers by scope or
lifecycle. Everything else in this proposal is independent of that choice.

---

## 8. Migration implementation — PREPARED, not run, not committed

One script, dry-run by default, held in the **session scratchpad** rather than the fork tree so it
cannot be executed by accident: `migrate_fork_gaps_PREPARED.py`. There is no implicit write path —
`--write` is inert in the prepared build and gets enabled only on approval.

**What it does, per entry:** split the state blob off the heading → assign `FG-<date>-NN` (date read
from the title, ordinal within that date) → normalize the existing `**Class/Fix scope/Target
file/Marker**` lines into the header block → derive `state` from the blob, `scope` from the target
path, `owner` from scope → emit heading / header / `### Incident` (body verbatim, minus only the
four relocated field lines) / `### Work` (leading `**Status (date):**` carrying the blob **quoted,
not reworded**).

**Handling of the three named hard cases:**

| Case | Behaviour |
|---|---|
| Unknown `owner` / `class` / `scope` | Written literally as `unknown` and appended to the migration report with its entry id. **Never inferred from prose.** Owner is derived *only* from an unambiguous scope (`fork`→fork-maintenance, `machine-local`→mason, `harness`→harness-vendor); a `project` scope always yields `unknown`, because which project owns it is a human call. |
| Existing superseded chains | `state: superseded` triggers a scan of the blob for a named successor; found → `superseded_by`, not found → `superseded_by: unknown` **plus** a `superseded-without-target` report line. The chain is never invented. |
| `scope: harness` | `marker: n/a` is written automatically — the one sanctioned exemption, applied by the script rather than left to a human to remember. |

**The invariant that makes it safe.** Per entry, every non-blank pre-migration line must appear in
the post-migration output, except the heading and the four relocated field lines. Any other loss
**raises and aborts the whole run** — no partial write. Same line-conservation check used for the
archive moves on 2026-07-25.

**One deliberate asymmetry, called out because it is the risky part.** `derive_state()` maps a
`RESOLVED` blob to `closed` — which is only legitimate *because* every such entry in the current
file was verified by reading its implementing section during the 2026-07-25 pass. A future run over
unverified closures must not trust the blob. That is precisely how the canonical-case-home entry
came to claim two delivered artifacts that do not exist on disk.

## 9. Hook activation plan — placement decided, wiring NOT done

`.githooks/pre-commit` already ends with a docs-conditional block:

```sh
if git diff --cached --name-only | grep -Eq '^docs/'; then
  npm run docs:validate-links
  npm run docs:validate-sidebar
fi
```

The register validators go **immediately after it**, in their own narrower conditional, so they fire
only on commits that actually touch the ledger:

```sh
# Register gate — only when the ledger itself is staged.
if git diff --cached --name-only | grep -qx 'docs/fork-gaps.md'; then
  bash tools/check-fork-gap-schema.sh      || exit 1   # ERRORs: schema + fields
  bash tools/check-fork-gap-targets.sh     || exit 1   # ERROR only on scope:fork rot
  bash tools/check-fork-gap-stale-open.sh --creation-mode || exit 1   # ERROR: marker already present on a NEW entry
fi
```

Placement rationale: after the existing docs block (so link/sidebar failures surface first and the
register gate never masks them), before the hook ends, and gated on an exact-match path so an
unrelated `docs/` edit pays nothing. Sweep mode (`--sweep`, warn-only) stays where it is today — on
the SessionStart surfacer, which is the right place for "these N entries look stale," a judgement
that must never block a commit.

**Once migration lands, these three become non-optional for any future edit to the file.** That is
the whole point: the schema is only real if it is checked at write time. Until then the block is
documented here and **not wired** — wiring it against unmigrated entries would fail every commit
that touches the register.
