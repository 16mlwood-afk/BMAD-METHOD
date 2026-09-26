# Sync plan — depth-pass provenance gates (`c7a6917e`)

**Status: PLAN ONLY. No sync has been run. Do not run one from this document.**
This is the prepared brief for a *dedicated* fleet re-sync thread. It stops at the
boundary deliberately: the ACT step is withheld until the owner gives an explicit
**"go" on fleet sync**. Opening a competing sync from a routine session is the exact
thing the `## Now` ⛔ STOP item forbids.

- **Fork commit:** `c7a6917e` (+ `STATUS.md` record), pushed to `myfork/custom`.
- **Owner decision behind it:** disclosure + proof marker (2026-07-20).
- **Prerequisite that is NOT satisfied:** the `## Now` ⛔ fleet re-sync STOP item is
  still open — 11 projects blocked, quiet low-contention window required, never
  `--force` into live sessions.

---

## 1. Blast radius

**13 consuming projects** (14 sync targets less the fork itself). Every one of them
loads these files from `_bmad/bmm/workflows/` (or the v6.8 skills layout in
`cash-recovery`, the lone pilot), so the change lands in all of them at once.

Two of the touched surfaces are **cross-cutting doctrine**, not single-workflow text —
this is what makes the radius wider than the file count suggests:

| Surface | Why it reaches beyond design-handoff |
|---|---|
| `shared/analytics-archetypes.md` | A **shared standard**, read by every workflow and human that reasons about analytics shape. The wording change (removing the "mandatory pass … enforced by `C-RIGOR-01`" overclaim) alters how the whole corpus describes its own enforcement. |
| `design-review-pr/steps/step-01-scope.md` | The **review-time** consumer. After sync, PR review reads `rigor_source` and escalates its human-judgment prompt on `inline-fallback` — so reviewer behaviour changes in every project, not just ones running design-handoff. |

**Interaction with in-flight state:** the fleet is already behind on the cockpit wave
(`265cd6a1`) and STD-SCOPEROUTE-001. A sync carrying *this* change carries those too.
That is an argument for one deliberate combined sync, **not** for a narrow `--only`
run — but it also means the diff each project sees is much larger than these 7 files.
Size the review window accordingly.

## 2. Exact files touched

| File | Change | Reaches projects via |
|---|---|---|
| `custom/workflows/design/design-handoff/steps/step-01b-decide.md` | §5c-2/§5c-3: `{rigor_source}` / `{decision_source}` mandatory on both paths, reason recorded on the fallback | workflow sync |
| `custom/workflows/design/design-handoff/brief-template.md` | Required `rigor_source:` / `decision_source:` line in §4d/§4e | workflow sync |
| `custom/workflows/design/design-review-pr/steps/step-01-scope.md` | Capture `rigor_source`; escalate the human-judgment prompt on `inline-fallback`; never treat an undeclared §4d as skill-produced | workflow sync |
| `custom/workflows/design/shared/analytics-archetypes.md` | Corrected the enforcement overclaim; documented that both producer skills are unauthored | workflow sync |
| `custom/githooks/check-design-brief-completeness.sh` | Tier-6 warn on a §4d/§4e with no declaration + tier-7 marker cross-check | **githooks track** (`gates.d/`) |
| `src/modules/bmm/_module-installer/assets/hooks.json` | Tier-7 `PostToolUse:Skill` invocation marker | **hooks/onboarding track — NOT workflow sync** |
| `docs/fork-gaps.md` | Sweep result recorded | fork-only, no fan-out |

**Two different distribution tracks — do not conflate them.** The four workflow/standard
files ride `sync-bmad-workflows.sh`. The gate script rides the githooks rail. **The
`hooks.json` marker does NOT ship via BMAD sync at all** — it lands only through
onboarding / a hooks-track update. Consequence: a project can receive the *declaration
requirement* while never receiving the *marker*, which is precisely the degraded state
§4 describes. Plan the hooks track explicitly or the proof layer silently never arrives.

## 3. Expected user-facing change

**Headline: "rigor provenance disclosed." No new hard fails.**

- **No commit is blocked.** `check-design-brief-completeness.sh` is Phase-1 **WARN-only**
  (`exit 0` unconditionally). A brief missing `rigor_source` prints a stderr finding and
  commits normally. Promotion to a hard gate is a separate, later decision made only
  after the warn phase proves quiet.
- **No existing brief is invalidated.** Briefs written before this change have no
  `rigor_source`; they warn on next commit-touch and are otherwise untouched. There is
  no migration and no back-fill requirement.
- **design-handoff runs gain one required line** in §4d/§4e. On projects where the
  producer skills are absent (all of them today), the honest value is
  `inline-fallback` + a reason.
- **design-review-pr runs get a sharper prompt**, not a new failure: on
  `inline-fallback` the reviewer is asked to sanity-check *the spec itself* (is the base
  rate the right denominator? is the named deciding field the real one?) rather than only
  the surface's conformance to it.
- **Net behavioural delta for an author:** one extra honest line. For a reviewer: one
  extra thing to look at, on the subset of briefs that admit a hand-derived spec.

## 4. What this does NOT do — state plainly, do not let it drift

1. **Rigor QUALITY stays PROBABILISTIC. Permanently.** Whether a base rate is the apt
   denominator, or a named deciding field is genuinely the deciding one, has no
   machine-decidable form. No gate in this plan — or any future one — settles it. The only
   oracle is a competent reader. **The accurate label is "rigor provenance disclosed."
   Never "rigor enforced."**
2. **Marker absence = UNVERIFIABLE, not clean.** The tier-7 cross-check only runs when
   `.claude/.depth-pass-invocations.jsonl` exists. Where the hook is not installed the
   file is absent and the gate **stays deliberately quiet** — warning on every brief in
   every un-hooked project would noise-poison the gate into being ignored. That silence is
   a known hole, named in-script. **Do not read a quiet gate as proof the pass ran.**
3. **`rigor_source` alone is SELF-REPORTED.** Without the marker it is an assertion, not
   evidence. An agent that skips the pass can still write `rigor_source: skill`. Only the
   marker makes the claim unfakeable — and even then it proves *invocation*, never quality.
4. **The two producer skills remain unauthored.** `analytics-rigor` and `decision-analysis`
   exist in no resolution root (`tool-discovery` sweep, 2026-07-20; both confirmed genuine
   uncovered gaps with nothing adaptable). This sync does **not** create them and must not
   be described as completing them. Authoring is a separate owner decision; when requested,
   it is a **Mode 2 AUTHOR** job against the already-written consumer contract in
   §5c-2/§5c-3.
5. **`C-RIGOR-01` / `C-DECISION-01` are not demoted and never were phantom.** They are real
   conformance checks (rendered surface vs the brief's §4d/§4e). They simply take those
   sections as ground truth and therefore cannot audit them — which is the whole reason
   provenance had to move to the producer.

## 5. Pre-flight for the sync thread (checks, not actions)

Run these *inside* the dedicated thread, before any sync command:

- `sync-bmad-workflows.sh --check` — preview; confirm which targets are dirty/blocked.
- Confirm the window is genuinely low-contention (no live sessions mid-merge in the
  targets). The `bmad_managed_dirty()` guard refuses dirty targets — **let it refuse;
  do not `--force`.**
- Decide the hooks-track action for the `hooks.json` marker **explicitly** — it will not
  ride this sync. Skipping this decision ships the requirement without the proof layer.
- Expect a large per-project diff: this sync also carries the cockpit wave and
  STD-SCOPEROUTE-001.

## 6. Gate

**Do not proceed past §5 without an explicit owner "go" on fleet sync.**
Until then the correct description of fleet state is:
*authored on fork, inert in all 13 projects.*
