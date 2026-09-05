---
name: scope-register-routing
contract_version: 1
description: 'Shared policy for what a scope-register ROW must carry so registered scope cannot sit inert. Every row declares a `route` from a closed enum (R1 capability / R2 bounded-local / R3 design / R4 operational-milestone / R5 parked), and each route names the ONE artifact that makes the scope actionable — a story file, a quick-spec, an active design brief, an owned milestone block, or (for R5) an owner + activation trigger + why-not-now. Carries the ACTIONABILITY LADDER that separates registered / proposed / described from shaped: a scope-register row, a sprint-change-proposal, an epic in `epics.md`, and a `backlog` story line are all DESCRIBED, never ACTIONED — the first actionable artifact in every route is the one a different workflow can consume without a human re-deciding scope. The write-side counterpart of STD-SCOPEROUTE-001 (which routes the ASK at intake; this makes the resulting ROW carry that route as a field). Unlike its sibling, this standard gates an ARTIFACT, not a prose answer, so it has a real deterministic tier: `tools/check-scope-register.js`. Produced by correct-course; consumed by create-story / quick-spec / design-handoff / sprint-planning; audited by the inert-scope sweep.'
---

# Scope-Register Routing — a registered row is not a plan until it names its route

**Why this exists.** Greenfield work in this fork has a fully-owned shaping chain: brief → PRD →
architecture → `epics.md` → `create-story` → story file → `dev-story` → PR. Every hop has a
*producing* workflow, a *consuming* workflow, and a machine-readable state with a defined enum
(`sprint-status.yaml`).

Brownfield scope change has no equivalent. `correct-course` produces a sprint-change-proposal; the
proposal names impacted artifacts in prose; a human appends a row to the project's scope register —
and there the chain **ends**. The row has a `disposition` (is it approved?) but no `route` (what
kind of work is it?) and no required `next_artifact` (what makes it real?). So an `accepted` row
with an empty linked-artifact is indistinguishable, by inspection, from a delivered one. That is
**registered-but-inert** scope: agreed, recorded, owned by nobody, consumed by nothing.

This standard closes it by making the row itself carry the route and the next artifact, in fields a
checker can read.

**Relationship to its sibling (reference, do not duplicate).** `scope-extension-routing.md`
(STD-SCOPEROUTE-001) fires **at intake**, on the natural-language ask — it decides which BMAD
mechanism owns "let's add / deepen / extend X" and mandates a 4-part *answer*. Its enforcement is
honestly PROBABILISTIC because a prose answer has no artifact to gate on. **This standard fires at
the write** — it governs the row that the routed work leaves behind. Because a row IS an artifact,
this one has a deterministic tier. Same lane vocabulary, two different moments; when the two appear
to disagree on a lane, STD-SCOPEROUTE-001 is the source of truth for the lane and this standard
governs how that lane is recorded.

**Relationship to the completion family.** `completion-contract.md` (STD-COMPLETION-001) forbids the
commentator exit at a *workflow's* terminal step. This forbids the same failure one layer up, at the
*scope* level: writing a row down and calling the shaping work finished. §5 is the scope-level
instantiation of that contract's "name the residue, never drop it silently".

---

## 0. Appending a row (read this FIRST — it is the whole compliance cost)

This standard MANDATES an append from every shaping session, and the session it reaches is a cold
one at the END of other work, with the least context to spend. So the append affordance comes before
the rules. **Do not reverse-engineer the format from existing rows** — they are 400–2000 characters
wide, the header sits ~70 lines above them, and the newest rows are the longest.

```bash
node tools/check-scope-register.js --register {planning_artifacts}/scope-register.md --new-row
```

It prints a correctly-columned skeleton for **both** tables plus the next free `SR-nn`, derived from
the register's LIVE header — so a register that grows a column still gets a correct skeleton.

**The pairing nothing else tells you: there are TWO tables and a row belongs in BOTH.** A short
routing table (`id | route | next_artifact | state`) and a wide intake table
(`id | item | category | discovery-source | trigger | evidence | disposition | …`). They are joined
by `SR-nn` and by nothing else — appending to one and not the other is the single most common way a
row is born inert. Minimal well-formed pair:

```markdown
| SR-36 | R2-bounded-local | implementation-artifacts/quick-spec-thing.md | SHAPED |

| SR-36 | One-line item | design | audit 2026-07-26 | — | link/quote | pending | — | — | — | — |
```

Then check what you wrote (`--audit`). Three rules the skeleton cannot enforce: `route: TBD` is legal
only while `disposition: pending` and owes the named unblocking decision (§2); `R5-parked` owes all
three activation parts (§3); and "recorded in the register" is REGISTERED, not done (§4).

---

## 1. Scope

Applies to every write to a project's scope register (canonically
`{planning_artifacts}/scope-register.md`) — whether the writer is `correct-course` (the primary
producer, §6), an audit/review workflow appending a `pending` candidate, or a human.

Applies to the workflows that CONSUME registered scope: `create-story`, `quick-spec`,
`design-handoff`, `design-elevation`, `sprint-planning`, `maintenance-triage`.

Does NOT apply to: work that never touches project scope (a bug fix inside already-shaped scope, a
refactor, a doc edit). Registering those is noise — the register is for scope *provenance*, not a
task list.

---

## 2. Required row fields

Every row carries the existing provenance fields (`id`, `item`, `category`, `discovery-source`,
`trigger`, `evidence`, `disposition`, `owner-decision`, `decided`, `brief-link`) **plus these
three**, which are what this standard adds:

| Field | Values | Rule |
|---|---|---|
| `route` | `R1-capability` · `R2-bounded-local` · `R3-design` · `R4-operational-milestone` · `R5-parked` | Closed enum. Mandatory on any row not `disposition: pending`. A `pending` row MAY carry `route: TBD` — that is the ONLY legal absence, and it expires when the owner dispositions the row. |
| `next_artifact` | a path, or a named artifact + its state | The ONE artifact that makes this scope actionable, per §3. Mandatory on `accepted`. Must be route-appropriate (§3) — an epic name does not satisfy R1; a proposal does not satisfy anything. |
| `activation` | `owner: <who>` · `trigger: <observable condition>` · `why-not-now: <reason>` | Mandatory **and only** on `route: R5-parked`. All three parts, or the row is not legally parked. |

**`disposition` still means "is this approved?" and is unchanged.** `route` means "what kind of work
is this?" and `next_artifact` means "what makes it real?" Three orthogonal questions that were
previously collapsed into one column and a paragraph of prose.

---

## 3. The routing rule (a decision procedure, not advice)

Apply in order. The first matching clause wins.

**R0 — does this change an existing direction, policy, or already-accepted decision?**
Then `correct-course` **LEADS**, regardless of what the work turns out to be. Run it *first*; its
proposal supersedes the prior decision on the record. Then re-enter this procedure to route the
work itself — correct-course is a **gateway, not a terminal** (§4). A row whose only artifact is a
sprint-change-proposal is NOT routed; it is awaiting routing.

**R1 — capability.** Any ONE of: a new table · a new external source · a schema-level or structural
model change · a new PRD FR · an epic-level capability spanning multiple stories.
→ `correct-course` → `prd` (FR) + `architecture` (AD) → `create-epics-and-stories` → **`create-story`
on at least one story.**
**`next_artifact` = the path of the first STORY FILE, at `ready-for-dev`.** Not the epic. Not the
epic's story list. See §4 — an epic in `backlog` is described, not actioned.

*Guardrail (MATERIALITY, inherited from STD-SCOPEROUTE-001 §3):* a small clerk-writable field or a
single new enum value is **R2**, not R1. R1 fires on a new table, a new external source, or a
schema-level/structural change.
*Guardrail (PREMISE-CHECK, inherited from §4 of the same):* before routing R1 on "a new source",
verify we do not already ingest it. A dimension already sitting in a table we pull is **R3**.

**R2 — bounded-local.** A change confined to an existing surface/module: no new table, no new
external source, no schema-level change. Materiality-clause items land here.
→ `quick-spec` → `quick-dev`.
**`next_artifact` = the quick-spec tech-spec file path**, in a ready-for-dev state.

**R3 — design.** The system already has the data and the capability; what changes is what the
operator sees, in what order, at what depth.
→ `design-elevation` (if the surface is settled and this is a deepening pass) or `design-handoff`
(if the intent changes) → `design-synthesize`/`design-implement`.
**`next_artifact` = the ACTIVE design brief path** — provenance-valid per `brief-revision-policy`.
A material revision is produced by `design-handoff`, never hand-edited; a row whose next artifact is
"hand-edit the brief" is invalid by construction.

**R4 — operational milestone.** There is **nothing to build**: the work is running, verifying,
proving, or physically executing something with already-shipped code. Proving runs, credential
provisioning, prod verifications, backfill executions, pilot measurements.
→ **NOT stories.** A **milestone block** in `sprint-status.yaml` per §7, whose items are
preconditions/verifications, each carrying an owner (`owner: operator` | `owner: agent` |
`owner: external`).
**`next_artifact` = the milestone block key**, e.g. `sprint-status.yaml#proving-run-resale`.
An R4 item that is silently converted into build stories is a mis-route: it manufactures code for a
problem that is a config check or a physical action.

**R5 — parked.** Genuinely deferred: right call, wrong time.
→ No downstream workflow. **`activation` is mandatory and complete** — `owner` (a named human or
role who will re-evaluate), `trigger` (an *observable* condition, not "when we get to it"), and
`why-not-now` (the actual blocker or the cheaper alternative that won a comparison).
**`next_artifact` = `—` is legal here and ONLY here**, because `activation` carries the obligation
instead.

**Mixed.** Say it is mixed, name BOTH routes, and set `route` to the one that **LEADS**. Record the
follower as a second row with its own `next_artifact`, cross-referenced. Do not fold two routes into
one row — a row with two routes has no checkable next artifact.

---

## 4. Actionability — what "actioned" actually means

The failure this standard exists to kill is the conflation of **written down** with **ready to
happen**. Four states, and only the last is actionable:

| State | Artifacts in this state | Actionable for |
|---|---|---|
| **REGISTERED** | a scope-register row | *nothing* — it is a record of intent |
| **PROPOSED** | a `sprint-change-proposal-*.md` | **owner decision only** — never build, never design |
| **DESCRIBED** | an epic in `epics.md` · `epic-N: backlog` · a story line at `backlog` in `sprint-status.yaml` (which the enum itself defines as "story only exists in epic file") · a bullet in a proposal's impact analysis | *nothing* — no consumer can start |
| **SHAPED** | **a story file at `ready-for-dev`** (→ `dev-story`) · **a quick-spec** (→ `quick-dev`) · **an active, provenance-valid design brief** (→ `design-synthesize`/`design-implement`) · **a milestone block with owned preconditions** (→ operator execution) | **the named consumer, with no further scope decision** |

**The test for SHAPED, stated once:** *can a different workflow, in a cold session, consume this
artifact and start work without a human re-deciding what the scope is?* If a human must still choose
between options, pick a grain, or approve a direction, the item is DESCRIBED, not SHAPED.

**Corollaries a cold session gets wrong:**

- An epic with seven `backlog` story lines is **one described item, not seven actionable ones.** It
  reads like delivery on a board and is zero shaped units.
- `correct-course` finishing successfully means a **decision is ready to be made**, not that work is
  ready to start. Its own contract is read-only on tracker state — it deliberately produces no
  shaped artifact.
- An `accepted` disposition means the owner said yes. It says nothing about whether anything is
  actionable. `disposition: accepted` + `next_artifact: —` is the exact inert state this standard
  detects.
- An R4 milestone is **fully actionable** even though it produces no code. "Not a build" is not "not
  ready" — do not downgrade an operational milestone to a backlog item because it has no story file.

---

## 5. The close-out rule — no "done" without a route

At the terminal step of any workflow that **added or dispositioned** a scope-register row, before
declaring the shaping work complete:

> For **each** row you added or changed, state its `route`, its `next_artifact`, and — if `R5-parked`
> — its owner, trigger, and why-not-now. A row you cannot route is not finished work; say
> `route: TBD` and name what decision unblocks it. **"Recorded in the scope register" is not a
> completion.** It is the REGISTERED state (§4), and reporting it as done is the scope-level form of
> the commentator exit that STD-COMPLETION-001 §3 forbids.

This composes with, and does not replace, the `completion_disposition` field. A run that registered
scope and shaped none of it is `owner_gated_residue` **with each unrouted row named**, or `advisory`
with a why — never a bare success.

---

## 6. Producer contract — `correct-course` owns the row

`correct-course` is the fork's scope-change front door and is therefore the **primary producer** of
scope-register rows. Its Step 4.5 (§ "Record Scope Provenance") MUST, for every scope item the
proposal introduces or re-dispositions:

1. Append (or update) a row in `{planning_artifacts}/scope-register.md` with the §2 fields.
2. Set `route` per §3 — and where the proposal is only a gateway (R0), set `route: TBD` with the
   named decision that unblocks it, never leave the field absent.
3. Set `next_artifact` to the route-appropriate SHAPED artifact from §4 — **the artifact that will
   exist, with its intended path** — not the workflow name, not the epic.
4. On `R5-parked`, write all three `activation` parts.
5. Rows are **append-only**; a superseded row is re-dispositioned in place with a dated note, never
   deleted or renumbered. (Same discipline as `manifest-contract.md` — a renumber is a
   read-modify-write race, and scope ids are cited from stories, briefs, and PRs.)

Consumers (`create-story`, `quick-spec`, `design-handoff`) write their produced artifact's path back
into `next_artifact` when they consume a row — that write-back is what moves a row from *promised*
to *shaped* and is what the audit in §8 measures.

---

## 7. R4 — the milestone block (tracker vocabulary)

`sprint-status.yaml`'s status enums cover epics, stories, retrospectives, and action items. They have
no vocabulary for an operational milestone, so R4 work has historically been encoded ad-hoc with
undefined statuses. The sanctioned shape, added to the sprint-planning template:

```yaml
  # ---- MILESTONE: <name> ----
  # <what real-world observable proves this milestone>
  # Source: scope-register <SR-id>
  <milestone-key>: blocked          # milestone status: blocked | in-progress | done
  <item-key>: blocked               # owner: operator  — a physical/manual action
  <item-key-2>: blocked             # owner: agent     — the system can drive this
  <item-key-3>: blocked             # owner: external  — waits on a third party
```

**Milestone status enum:** `blocked` (a precondition is unmet) · `in-progress` · `done`.
**Every item carries an `owner:`** — `operator` (a human does it), `agent` (the system drives it),
`external` (a third party gates it). An item with no owner is the inert state again, one level down.

A milestone is NOT an epic: it has no stories, no retrospective, and never enters `create-story`.
`sprint-status` reports it separately from epic progress so a blocked milestone cannot be read as
build progress.

---

## 8. Enforcement (honest tier)

Classified via `enforcement-expert`. **The load-bearing difference from STD-SCOPEROUTE-001: this
standard governs a FILE, so a deterministic tier is available and is taken.**

**DETERMINISTIC — the artifact check.** `tools/check-scope-register.js`:

- `--register <path>` lints a project's register: every non-`pending` row has a `route` from the
  enum; every `accepted` row has a route-appropriate `next_artifact`; every `R5-parked` row has all
  three `activation` parts. Exit 1 under `--strict`.
- `--audit` is the **inert-scope sweep** (§9): rows that are `accepted` with no `next_artifact`,
  rows parked with no trigger, and rows whose `next_artifact` names a path that does not exist on
  disk (a *promised* artifact that was never produced — the most common real failure).
- With no `--register`, it scans the fork's own `custom/workflows/` corpus for **adoption**: a
  workflow that writes or consumes scope-register rows but does not reference STD-SCOPEREG-001.
  Same shape as `check:completion` / `check:digest`.

**Ships WARN-ONLY (`npm run check:scoperegister`, exit 0).** Per the warn-then-gate pattern it is NOT
armed in `npm test` or the pre-commit fast-path at v1: the row-shape heuristic is unproven against
hand-maintained registers written before this standard existed, and a linter that false-blocks a
commit on a legacy row is the anti-pattern that gets gates ripped out. Promotion to `--strict` in
the gate requires the fork scan quiet AND at least one project's register passing clean after
backfill.

**DETERMINISTIC DELIVERY, PROBABILISTIC ACTION — the write-moment detector.** A `PostToolUse`
`Edit|Write` matcher on a `scope-register.md` path re-lints the file and returns
`{"decision":"block","reason":"<the failing rows>"}`, which feeds the violation back for immediate
correction. `PostToolUse` is the correct primitive here rather than `PreToolUse`: an `Edit` gate
cannot see the resulting file, and the check needs the whole row. It cannot un-write the row — it
forces the fix before the session moves on.

**PROBABILISTIC — awareness.** §5's close-out rule and §6's producer contract are prose the model
must choose to follow. The convergence lever is STD-CLOSEOUT-001 §4: a shape failure patches the
correct-course step in the fork so it propagates by sync, rather than being absorbed as a memory.

**NOT enforceable, stated plainly:** whether a declared `route` is the *correct* one. A linter can
prove a row has `route: R2-bounded-local` and a quick-spec path; it cannot prove the item was not
really R1. That axis is ceded to the golden suite (§9) and to human review — measured, not gated.

**Distribution.** The standard rides `sync-bmad-workflows.sh` into every project (authoring ≠
shipping). The linter is fork tooling; it reaches projects as a `_bmad` script on the sync track. The
`PostToolUse` detector ships on the hooks track (`hooks.json` template), NOT with this doc — writing
this section did not deploy that hook.

---

## 9. Monitoring

**The inert-scope sweep (recurring).** `check-scope-register.js --register <path> --audit` returns
the registered-but-inert population. Run it: at `sprint-status`, at `maintenance-triage` intake, and
on the project's SessionStart surfacer as a one-line count (`INERT SCOPE: N rows`) so a cold session
sees it without asking. A non-zero count is not automatically wrong — it is the backlog of scope
that has been agreed and not shaped, which is exactly the number that was previously invisible.

**A trigger with nothing that fires it is a note, not a mechanism.** This section named three
trigger points for ~4 weeks while **none of the three invoked the sweep**, so it only ran when
somebody already suspected a problem — the exact failure this standard exists to kill, reproduced one
level up. Now wired for real at `sprint-planning` step 5 (report-only, right before the completion
summary); `maintenance-triage` intake and the SessionStart surfacer are still prose-only and
therefore still unfired — treat them as owed, not as covered.

**The reverse signature — DELIVERED-BUT-PENDING.** The sweep also reports a row still `pending`
whose `next_artifact` (or the story id its prose names) ALREADY EXISTS on disk. This is the more
expensive direction, because it is invisible: rows move ONTO `pending` automatically and off it only
by a human remembering, so `pending` is a one-way ratchet and delivered-but-unclosed rows accumulate
monotonically. Nobody notices, because a stale `pending` row is indistinguishable **by inspection**
from a real open decision — the owner reads four blockers on their desk that are actually one.
Measured on the first real register: 3 fires, all three genuine (SR-07 answered by a story merged
~4 weeks earlier, SR-08 by its fixture retirement, SR-12 by a decision resolved the same day), 0
false positives across 35 rows. **The detector deliberately fires only on a parsed `pending`** — an
UNPARSED disposition is not a pending one, and the first cut, which treated null as pending, produced
11 false blockers to catch those 3. **It never flips a disposition**: the flip stays human because
owner-only-off-`pending` is the audit anchor. The gap was detection, not authority.

**Golden suite.** `evals/scope-register-routing.md` — cases drawn from real registered rows that
must route *differently*, scored on `route` + `next_artifact` + (for R5) the three activation parts.
This measures the axis the linter cedes: route correctness. Replay on any change to §3.

---

## §10 `why_not_now` — a registered row must say why it isn't happening

**Registering scope is not a way to make work go away.** Every accepted row carries
`why_not_now:` from the closed set below. It is the field that distinguishes a row registered
because it is BLOCKED from a row registered because it was AVOIDED — which were, until
2026-07-28, byte-identical in the file.

| value | means |
|---|---|
| `owner-decision` | needs a ruling only the owner can give |
| `blocked-by-data` | the data or source does not exist yet |
| `blocked-by-artifact` | an upstream artifact or workflow must land first |
| `other-session` | another session's surface, or an active claim |
| `too-large-for-now` | a genuine multi-pass build, not a same-session change |
| `NOT-BLOCKED` | nothing prevents it — **so do it; do not file this row** |

**`NOT-BLOCKED` is in the enum on purpose, and it FAILS the linter.** There is deliberately no
silent option: either you name a real blocker, or you write down that there isn't one — and
writing that down is the moment you notice you should just do the work. A row that cannot name
a blocker is not registrable scope; it is undone work with paperwork attached.

**The failure this closes (2026-07-28, cash-recovery, SR-49 split A + SR-50).** A session
diagnosed two small changes — attach an identity already held in memory, expose a boolean
already computed, select a column that already existed — wrote *"nobody is doing it / ready to
be picked up"*, registered both rows, and stopped. Nothing blocked either. The owner asked
three times before the work happened; it then took one pass, no schema change, no migration,
no new query. Both rows had a route, a `next_artifact` and an owner, so **every existing check
passed them**. Only `R5-parked` had ever been required to say why-not-now.

**Scope of the rule:**

- Asked of `accepted` rows only. A `pending` row is by definition awaiting a decision — that
  is its own why-not-now.
- `R5-parked` is EXEMPT: it already owes the three-part activation block (§3 R5) whose
  why-not-now is legitimately free text. One contract per row.
- Legacy rows are grandfathered and reported as ONE aggregate line, never one warning each —
  50 individual warnings would bury the finding that matters.

**Enforcement, honestly.** `tools/check-scope-register.js` decides two things
DETERMINISTICALLY: whether the field exists, and whether its value is in the enum. It **cannot
judge whether the stated reason is TRUE** — `owner-decision` on a row nothing is waiting for
passes the linter. That axis stays PROBABILISTIC, and the mitigation is visibility: the
sentence is now in the row, in the diff, and in front of the next reader. The checker is
**WARN-ONLY** and runs only when invoked (`sprint-status`, `maintenance-triage`, before closing
shaping work) — a pre-commit gate on the register would make it unavoidable and is the
available upgrade, not something claimed here.
