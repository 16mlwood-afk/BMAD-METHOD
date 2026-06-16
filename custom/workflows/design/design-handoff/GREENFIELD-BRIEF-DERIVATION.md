<!--
  DRAFT working note — greenfield brief-derivation recipe.
  Status: v0.1, unproven. Authored 2026-06-16 to support the first greenfield
  project run. NOT yet a codified workflow mode and NOT yet synced to the 13
  targets — deliberately. Run it by hand once, let the first run reveal the
  real shape, THEN codify as design-handoff step-01 greenfield branch (see
  "Codification target" at the bottom). House style: mirrors design-handoff/
  steps/step-01-gather.md, which this substitutes the INPUT SOURCES of.
-->

# Greenfield Brief Derivation (design-handoff, executed from specs)

**What this is.** The bridge that lets the custom design lane
(`design-policy` → `design-synthesize` → `design-implement`) run on a
**greenfield** project, where `design-handoff` cannot read a built codebase.
It produces the **same canonical brief** design-handoff emits — identical
11-field Block-A provenance, Block-B content fields, and §1–§7 body — by
substituting the gather step's INPUT SOURCES: spec artifacts instead of code.

**The one-line principle.** *The brief shape is phase-agnostic; only where the
raw materials come from changes.* Brownfield reads code; greenfield reads the
PRD, the architecture, and the UX design.

---

## Where this sits in the canonical greenfield spine

The creators' intended order, with the **two fork insertions** marked:

```
product-brief
  → create-prd
  → ★ onboard-design-system        ← INSERTION 1 (creates docs/design-policy.md + tokens)
  → create-ux-design               (page inventory, flows, states)
  → create-architecture            (data model + routes — the "schema" before code)
  → create-epics-and-stories
  → ★ THIS recipe (design-handoff, greenfield) ← INSERTION 2 (derives the brief)
  → design-synthesize              (brief + policy → bundle)   [UNCHANGED]
  → dev-story                      (builds the first cut)
  → design-implement               (takes over on iteration 2, diffing built code) [UNCHANGED]
```

After the first cut ships, the project **is** brownfield: every later design
iteration uses the normal `design-handoff` (reads the now-built code) →
`design-synthesize` → `design-implement` chain, unmodified. Greenfield is a
one-time bootstrap per surface.

---

## Preconditions — HALT if any is unmet

1. **`docs/design-policy.md` exists.** This is non-negotiable: design-synthesize
   reads it, and this recipe quotes it verbatim into §4. Canonical greenfield
   never prompts for it (it is a fork concept), so it is the easiest thing to
   skip. **If absent, HALT** with:
   > Greenfield bootstrap blocked: no `docs/design-policy.md`. Run
   > `onboard-design-system` first — it creates the policy + token bundle the
   > brief and synthesize both depend on. (Insertion 1, after `create-prd`.)
2. **PRD exists** (feature purpose, FRs, personas).
3. **create-architecture output exists** (data model / entities + routes). This
   is the greenfield stand-in for the Drizzle schema.
4. **create-ux-design output exists** (page inventory, flows, states). This is
   the greenfield stand-in for the route table + current-surface grep.

---

## Source-substitution map (the whole adapter)

Every brownfield input in `step-01-gather.md` maps to a greenfield source. The
brief sections it feeds are unchanged.

| Gather step (brownfield) | Greenfield source | Feeds brief § |
|---|---|---|
| §1b Load design policy | **SAME** — `docs/design-policy.md` from onboard-design-system | §4 Visual Direction, §4 Tokens |
| §3 Map data surface — DB schema (Drizzle) | **create-architecture** data model (entities + fields, flattened FKs) | §2 Domain Data |
| §3a Linked records — schema FKs + `relational-edges.yaml` | **architecture entity relationships**. No `relational-edges.yaml` yet (fresh project) — derive edges from the architecture's relationships; where a foreign value is owned by a surface that exists in the UX page inventory, it is a §13 linked record | §2a Linked records & lookups |
| §3 capabilities — grep current surface for mutations | **PRD FRs + epics/stories**. design-handoff's own rule: *"For a new feature there is no current surface to grep, so this audit reduces to the ingest audit alone."* Enumerate capabilities from the FRs, not a grep | §6 Design Ask (capabilities) |
| §4 Feature purpose — from code | **PRD** feature statement + FRs | §1 Feature Purpose |
| §5–§5f Page mode / composition / analytics / topology / spawned-surfaces | **SAME reasoning**, fed by the data model + user job above + the **UX page inventory** (which names the surfaces). The §5f spawned-surface inventory derives the §7 frame list exactly as in brownfield | §4a, §4b, §4c, §7 |
| §6 User context — from code | **PRD personas + create-ux-design** flows | §3 Who Uses This |
| step-02 Audit current design | **SKIPPED** — nothing built yet (mode is fresh-design, first build) | — |

---

## Provenance — exact Block-A values for a greenfield original

Fill the 11 Block-A fields (`shared/brief-revision-policy.md §2`) as:

```yaml
target_slug: <kebab-feature-slug>      # doubles as active-uniqueness key
brief_status: active
revision_mode: workflow_generated      # see honesty note below
change_class: original                 # first brief for the feature, no predecessor
supersedes:                            # EMPTY (Invariant 4: original ⇒ no predecessor)
superseded_by:                         # EMPTY (freshly generated)
source_workflow: design-handoff
source_run_date: <ISO date you run this>
policy_version_required: <docs/design-policy.md frontmatter `version:`>  # NOT 0 — policy exists now
last_modified_by: workflow             # Invariant 8: must match revision_mode
last_modified_date: <same ISO date as source_run_date>   # Invariant 8: == source_run_date
```

**Honesty note on `revision_mode: workflow_generated`.** The provenance model
assumes briefs are workflow-produced, and the invariants leave no clean slot for
a free-hand original (Invariant 3 ties `manual_minor_revision` to `clarification`
only). The honest resolution: **this recipe *is* design-handoff's greenfield
path executed by hand.** When you follow the procedure faithfully, the output is
legitimately `workflow_generated / original` — the declaration is true because
the workflow's logic produced it, whoever moved the keys. Do **not** hand-wave
fields the procedure didn't actually decide; that is the dishonesty the contract
exists to catch. Once codified (below), the agent runs it and the declaration
needs no caveat.

**Block B** (always required): `mode: fresh-design`, `page_mode`, `route`,
`composition_provenance`, `band_provenance` (+ `analytics_archetype` iff the
band exists). Decide these from §5–§5f exactly as brownfield does.

---

## §7 Surface Inventory — the load-bearing section

`design-synthesize` step-01 §7a now populates `{screens}` **from the brief
body's §7 Surface Inventory table**, and **Gate 1f halts if any §7 frame would
go undrawn.** So §7 is not optional prose — it is the render contract.

Derive it via the §5f spawned-surface inventory:
- **Frame #1** — the primary surface (from the UX page inventory; `render_as`
  = the §5a composition).
- **The drilled detail drawer** — per the §5a composition, if the surface drills.
- **One lookup drawer per §2a linked record** — each §13 expand-in-context
  target is its own `{foreign-record}-lookup` frame, `render_as:
  drawer-over-{parent}`, `must_contain` = the foreign record's own fields PLUS
  what THIS relation needs (never a bare stub).

The UX page inventory maps almost 1:1 onto this table — that mapping is what
makes the greenfield adapter cheap.

---

## Procedure

1. Check the four **Preconditions**. HALT on the first unmet (especially #1).
2. Build the **source-substitution map** for this feature: open the PRD,
   architecture, and UX-design artifacts; note which file answers each row.
3. Run the gather logic §3 → §6 against those sources (skip step-02 audit).
4. Decide Block-B fields (§5–§5f).
5. Render the canonical brief from `brief-template.md` — same template,
   greenfield-sourced values. Stamp Block A per above.
6. Self-check against `brief-revision-policy.md` invariants 1, 1a, 2, 4, 8
   (the ones that bite a greenfield original).
7. Hand to `design-synthesize`. If its 6 intake checks halt, the brief lied
   about provenance or dropped a required field — fix the brief, not the check.

---

## Codification target (after the first run proves the shape)

The end-state is a **`project_phase` branch on `design-handoff` step-01**
(`project_phase` config already ships `greenfield | brownfield | mixed`,
`0dd2e1ca`): when greenfield, gather from PRD + architecture + UX per the map
above and skip step-02; when brownfield, the existing code-reading path. Every
downstream step (03 generate-brief, 04 deliver) and the whole brief shape stay
identical. Do NOT build that branch until this manual run reveals what the map
above gets wrong — same "ship v0.1, iterate after first run" ethos the lane was
built on.
