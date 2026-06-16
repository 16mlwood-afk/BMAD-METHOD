<!--
  DRAFT working note — greenfield bootstrap runbook (end-to-end).
  Status: v0.1, unproven. Authored 2026-06-16 alongside
  design-handoff/GREENFIELD-BRIEF-DERIVATION.md. Project-AGNOSTIC by design:
  every project-specific value is a <placeholder>. NOT synced — run once by
  hand, then codify. House style mirrors a workflow.md orchestration shell.
-->

# Greenfield Bootstrap Runbook

The end-to-end sequence to take a **brand-new** project from nothing to a first
built, policy-conformant UI — running BMAD's canonical greenfield order with the
custom design lane attached. Project-agnostic: fill every `<placeholder>` when
you instantiate it for a real project.

**Companion:** the brief-derivation step (Phase 4 below) is detailed in
`design-handoff/GREENFIELD-BRIEF-DERIVATION.md`. This runbook is the spine; that
is the zoom-in on the one new step.

---

## The spine (★ = fork insertion, not upstream canonical)

```
1  product-brief            → <project>-brief
2  create-prd               → PRD (FRs, NFRs, personas)
3 ★ onboard-design-system   → docs/design-policy.md + token bundle   (INSERTION 1)
4  create-ux-design         → page inventory, flows, states
4b ★ policy→schema-reqs     → required-fields contract                (INSERTION 3)
5  create-architecture      → data model (entities + routes)  ← consumes 4b's contract
6  create-epics-and-stories → epics/stories
7 ★ design-handoff (greenfield) → canonical design brief             (INSERTION 2)
8  design-synthesize        → design bundle (HTML + tokens.css + manifest)
9  dev-story                → first built cut
10 design-implement         → iteration 2+ (diffs the now-built code)
```

After step 9 the project **is brownfield** — every later surface uses the normal
`design-handoff` (reads code) → `design-synthesize` → `design-implement` chain.
This runbook is a one-time-per-surface bootstrap.

---

## Phase-by-phase

### 1. product-brief
Run `create-product-brief`. Output: `<project>-brief`. This is the only step
that needs raw human intent; everything downstream derives from artifacts.

### 2. create-prd
Run `create-prd` from the brief. Capture FRs (→ capabilities later), NFRs, and
personas (→ §3 Who Uses This later). **Gate:** the PRD must name the data
entities at least loosely — `create-architecture` (step 5) sharpens them, but
the brief-derivation needs them.

### 3. ★ onboard-design-system — DO NOT SKIP
Run `onboard-design-system`. It orchestrates `create-design-policy` (strategic
visual direction) + brand-identity (tactical) + a code-shaped token bundle, and
delivers `docs/design-policy.md` to main.

**Why here:** you now know the product's character (from the brief + PRD) — the
minimum to set visual direction — and every step from 7 onward depends on the
policy existing. Canonical greenfield never prompts for this; it is the single
easiest thing to skip and the most expensive to skip (step 7 halts without it).

**Gate:** confirm `docs/design-policy.md` exists with a frontmatter `version:`.
Record that version — it becomes `policy_version_required` in the brief.

### 4. create-ux-design
Run `create-ux-design`. Output: page inventory, user flows, screen states. This
is greenfield's substitute for the route table + current-surface grep that
brownfield `design-handoff` reads from code. **The page inventory maps ~1:1 onto
the brief's §7 Surface Inventory** — keep it concrete (name every surface,
drawer, and lookup).

### 4b. ★ Policy → schema-requirements contract — the gap-closer
Follow `design/GREENFIELD-SCHEMA-REQUIREMENTS.md`. Read `docs/design-policy.md`,
extract the **data-bearing** rules (provenance/raw-exchange, relational FKs, money
basis/currency/lane), and emit a **Schema Requirements (policy-derived)** doc —
required columns per entity, each traced to the policy rule it satisfies.

**Why here:** the greenfield dry-run proved the policy otherwise first enters at
step 7 (design-handoff), two steps *after* the schema is decided — so the schema
gets built blind and the design lane catches the violation late, forcing an
architecture + stories redo. This step carries the constraints forward to step 5.
It keeps `create-architecture` **unforked** — it produces an *input*, not a patch.

**Gate:** `docs/design-policy.md` must exist (→ INSERTION 1). Every data-bearing
rule maps to ≥1 required column or is explicitly marked N/A for this feature.

### 5. create-architecture
Run `create-architecture` **with the step-4b Schema Requirements doc as an input
alongside the PRD.** Output: the data model (entities, fields, foreign keys) +
intended routes — now built to satisfy the policy's data-bearing rules from the
start, not retrofitted. This is greenfield's substitute for the Drizzle schema
that brownfield `design-handoff §3` reads. Flatten FKs the same way (a
`supplier_country` FK is a flat field, not a grouping dimension).

### 6. create-epics-and-stories
Run `create-epics-and-stories`. The FRs/epics enumerate **capabilities** —
greenfield's substitute for the mutation-grep (design-handoff already special-
cases this: "new feature → no surface to grep → ingest audit alone").

### 7. ★ design-handoff (greenfield) — derive the brief
Follow `design-handoff/GREENFIELD-BRIEF-DERIVATION.md`. In short:
- Check its 4 preconditions (esp. design-policy.md present → else HALT to step 3).
- Build the source-substitution map (PRD + architecture + UX → brief sections).
- Render the canonical brief from `brief-template.md`; stamp 11-field Block A as
  a greenfield original (`workflow_generated / original`, `policy_version_required`
  = step 3's version), Block B from §5–§5f.
- Skip step-02 (no current design to audit).
- Self-check against `brief-revision-policy.md` invariants 1, 1a, 2, 4, 8.

**Gate:** one `active` brief per `target_slug`; §7 Surface Inventory complete
(synthesize Gate 1f halts on an undrawn frame).

### 8. design-synthesize — UNCHANGED
Run `design-synthesize` on the brief. Its 6 intake checks validate the brief's
provenance; if they halt, fix the brief, never the check. Output: the design
bundle (HTML + tokens.css + screenshot + manifest), §7-frame-complete.

### 9. dev-story — first build
Build from the bundle via `dev-story` (per epic/story). Use dev-story rather than
design-implement for the FIRST cut: design-implement diffs against existing code,
and on a first build there is none — its grid would be all-missing.

### 10. design-implement — iteration 2+
From the second design pass onward, the project is brownfield: `design-implement`
diffs the bundle against the now-built code and fixes deltas. This is its sweet
spot.

---

## Instantiation checklist (when a real project exists)

- [ ] Replace every `<project>` / `<placeholder>` with real values.
- [ ] Decide repo location + `project_phase: greenfield` in `_bmad/bmm/config.yaml`.
- [ ] Run the spine 1→10, honouring each **Gate**.
- [ ] After step 9 ships, flip `project_phase` to `brownfield` (or `mixed`).
- [ ] Capture what the brief-derivation map (step 7) got wrong → feed the
      codification of the `design-handoff` greenfield branch.

---

## Codification target

Once a real project validates this spine, the three insertions become first-class:
INSERTION 1 stays a workflow call (`onboard-design-system` already exists);
INSERTION 3 (policy→schema-requirements) folds into the `design-handoff` greenfield
branch as a pre-architecture sub-step, or stays a standalone runbook step;
INSERTION 2 becomes the `project_phase: greenfield` branch on `design-handoff`
step-01 (see the derivation recipe's "Codification target"). The runbook itself
can then graduate from a draft note to a `maintenance-triage`-style front-door
doc for greenfield starts.
