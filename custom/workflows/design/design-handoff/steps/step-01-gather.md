---
name: 'step-01-gather'
description: 'Gather feature purpose, data model, API surface, and user context — without capturing current layout or component structure'
---

# Step 1: Gather Feature Context (Bias-Free)

**Goal:** Extract the raw materials a designer needs — data model, user purpose, API surface, constraints — without describing the current UI's layout, information grouping, or visual hierarchy.

---

## RULES

- **NEVER describe the current page layout, component structure, or information grouping.** The current UI was built by a developer. Describing it anchors the designer to implementation choices.
- Read component files ONLY to extract data types, API calls, and route paths — NOT to summarize what sections the page shows.
- Focus on WHAT DATA is available and WHO needs it — not HOW it is currently presented.
- Present all data fields neutrally. Do NOT rank fields as "prominent" or "secondary."
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- **Voice — Rhea, Design Steward** (`shared/workflow-personas.md`): open with a one-line re-orientation that echoes the intent + hard constraints back ("I'll turn this into a dev-ready spec without losing the intent: …"). Presentation only — opening line + risk flags, never the gather logic; the bias-free RULES above still bind.

---

## EXECUTION SEQUENCE

### 0. Surface class — chrome short-circuit

Before anything else, classify the target: is it a content PAGE (a route's primary surface or a sub-surface within one), or app-shell CHROME — the global navigation, sidebar, top-bar, mobile nav drawer, or the shell frame itself? Set `{surface_class}` = `page` (the default; everything below runs as written) or `chrome`.

**When `{surface_class}` = `chrome`** (contract: `brief-revision-policy.md` Block B `surface_class` row):

- Set `page_mode: n/a`. SKIP §3–§3b (data-shape walk, linked-records §13 pass, finance pass), §5–§5g (band gate, archetype, drawer spawning, list-rendering) and step-01b's page-mode selection — chrome has no page_mode, no data table, no analytics band, no lookup drawers. Project design policies scope their page-layout rules to pages for exactly this reason (e.g. policy §5 "app-shell navigation is out of scope").
- Still run: §1/§1b (repo + policy — the visual system and anti-AI hard failures apply to chrome VERBATIM), §2 (user context), §4 (constraints), and the runtime §3c check if the chrome carries live indicators (e.g. a sync badge).
- Capture INSTEAD, as the chrome equivalent of the data walk: (a) the **route inventory** the nav must express (every top-level destination, grouping, and ordering — from the router/nav config, not invented); (b) **states** per item (active, hover, collapsed, disabled-by-role); (c) **role visibility** (`shell_role` — which items each role sees, when the app is multi-role); (d) **breakpoints** (desktop rail vs mobile drawer trigger).
- `frames` = the chrome variants + operator-distinct states (e.g. `nav-desktop`, `nav-mobile-drawer`, `nav-desktop--collapsed`), never empty. `route` = the shell's scope anchor (normally `/`), `surface_part` = the chrome piece (`primary-nav`, `top-bar`).

### 1. Resolve Repository URL

Capture `{github_repo_url}`:

```bash
git remote get-url origin
```

Convert SSH URLs to HTTPS. Strip trailing `.git`.

### 1b. Load Project Design Policy

Check both possible locations for a project-level design system declaration. `docs/design-policy.md` is the canonical location; `planning-artifacts/brand-identity.md` is the legacy slot. Prefer the first if both exist.

```bash
ls {project-root}/docs/design-policy.md 2>/dev/null
ls {planning_artifacts}/brand-identity.md 2>/dev/null
```

**If either is found:**
- Read the entire file → `{brand_identity}` (variable name retained for backward compatibility)
- Set `{brand_identity_path}` to the absolute path of whichever file was loaded
- Set `{design_system}` = "branded"
- Parse the frontmatter `version:` field of the loaded file → `{policy_version}` (integer). If no version field exists, default to `1`. This value is stamped into the generated brief's `policy_version_required` field in step-03 so downstream consumers can detect when the policy has moved past the brief's pinned version.
- **FRESHNESS GATE — verify the tree is current BEFORE stamping (required).** `{policy_version}` is read from whatever tree this run happens to occupy. A stale checkout therefore makes the stamp **a claim the drift detector then trusts**:

  ```bash
  # FOUR outcomes, each separately reachable. Substitute the path resolved above.
  if git fetch -q origin 2>/dev/null; then
    if ! git rev-parse --verify -q origin/HEAD >/dev/null 2>&1; then
      echo UNVERIFIED-NO-REF         # no origin/HEAD; try the repo's default remote branch first
    elif git diff --quiet origin/HEAD -- <resolved policy path> 2>/dev/null; then
      echo CLEAN                     # verified against a FRESH remote read
    else
      echo STALE                     # the check RAN against a fresh read and found divergence
    fi
  else
    # OFFLINE. A last-known ref may still be on disk from an earlier fetch. It is weaker
    # evidence than a fresh read, but it is not nothing — use it, and say what it is.
    if ! git rev-parse --verify -q origin/HEAD >/dev/null 2>&1; then
      echo OFFLINE-NO-REF
    elif git diff --quiet origin/HEAD -- <resolved policy path> 2>/dev/null; then
      echo OFFLINE-MATCHES-LAST-KNOWN
    else
      echo OFFLINE-STALE             # differs from the last ref we DID fetch — real evidence of drift
    fi
  fi
  ```

  - **`CLEAN` →** stamp `{policy_version}` as read.
  - **`STALE` → HALT**, naming BOTH numbers: *"design-handoff — policy version unverifiable. `docs/design-policy.md` in this tree is v{local}; `origin/<default>` is v{remote}. Stamping v{local} would certify this brief against a policy that has since moved. Re-run from a current tree, or rebase this one, then retry."* Do **not** stamp a guessed value, and do **not** stamp the remote's number against locally-read content — a brief must be authored against the policy text it actually read.
  - **`OFFLINE-STALE` → HALT.** The tree differs from the last remote state this machine actually saw. That is positive evidence of drift, not an absence of evidence, so it earns the same stop as `STALE` — name both numbers and add *"(compared against the last fetched ref; the live remote may have moved further)"*.
  - **`OFFLINE-MATCHES-LAST-KNOWN` / `OFFLINE-NO-REF` / `UNVERIFIED-NO-REF` → PROCEED (never halt)**, and record an Open Question in the brief: *"policy freshness unverified — no fresh remote read; `policy_version_required: {n}` is this tree's local value."* A halt here would freeze every disconnected run.

  **`OFFLINE-MATCHES-LAST-KNOWN` is NOT `CLEAN`, and the distinction is load-bearing.** Matching the last ref you fetched proves only *no drift since your last fetch* — it cannot see anything that landed after it. The two states are **byte-identical from offline**: measured with a tree at v21 matching its last-known ref, the verdict is the same whether the remote is still v21 or has since moved to v22. Labelling that `CLEAN` would let the run stamp `policy_version_required` with full confidence and **skip the Open Question** — which is precisely the original defect this gate exists to prevent, re-created through a label. Report what the evidence supports: *no drift since the last fetch*, not *current*.

  **The `||`-shorthand this replaces was WRONG, and measurably so (fixed 2026-07-29).** The first cut of this gate was `git fetch -q origin 2>/dev/null` followed by `git diff --quiet origin/HEAD -- <path> || echo STALE`. Two defects, both proven against a real git remote across four cases:

  1. **`git fetch`'s exit code was never consulted**, so the `UNVERIFIED` branch above was **unreachable by construction** — the prose offered an offline path the commands could not produce.
  2. **`|| echo STALE` fires on ANY non-zero exit**, so *"the check could not run"* was reported as *"the check ran and found divergence."* Measured: offline with no `origin/HEAD`, `git diff` exits `fatal: bad revision 'origin/HEAD'` and the shorthand printed **STALE for a tree that was actually CURRENT** — a false HALT on a fresh checkout. Offline-but-genuinely-behind also halted, freezing a disconnected session.

  **A gate whose failure mode is indistinguishable from its trigger is not a gate.** Branch on the three outcomes separately; never collapse "couldn't check" into "check failed."

  **Why this is a gate, not a nicety.** The failure is not "a wrong answer" — it is a brief that **certifies its own correctness against a version nobody checked**. `brief-revision-policy.md` §2 makes consumers *"halt or warn when the current policy version exceeds this"*, so a stale stamp makes that detector report **no drift in exactly the case it exists to catch**. And it is invisible at every existing gate: the brief is internally consistent, the commit-time completeness check tests presence not currency, and `design-implement` compares against the number the brief supplied — nothing re-reads the policy. **Observed 2026-07-28 (cash-recovery):** the main checkout carried policy **v18** while `origin/main` was **v21** (three versions merged by parallel sessions); the run was one incidental grep away from stamping v18 into a brief authored against v21. Structurally likely to recur wherever `_bmad-output/` artifacts live in the main checkout while a worktree mandate keeps *code* out of it — the tree workflows are told to run in is the tree most likely to be behind.

**If neither is found:**
- Set `{brand_identity}` = empty, `{brand_identity_path}` = empty
- Set `{design_system}` = "existing" (may be overridden to "external" by user input)
- Set `{policy_version}` = `0` (sentinel meaning "no policy in effect at brief time"; downstream consumers treat this as "no drift check possible — surface to user").

### 1c. Project-phase source binding (greenfield)

Read `{project_phase}` (loaded from config). **If `{is_greenfield}` is false (brownfield/mixed — the default), SKIP this whole section** and gather from code as written in §2–§4 below.

**If `{is_greenfield}` is true**, there is no built code to read. The brief shape is unchanged — only where the raw materials come from changes (this codifies `GREENFIELD-BRIEF-DERIVATION.md`). Bind sources and rules for the rest of step-01:

**Source-substitution map — every "read from code/DB/grep" instruction in §2–§4 resolves to its greenfield source per this table** (read those sections *through* this binding; do not also try to read non-existent code):

| §2–§4 instruction (brownfield) | Greenfield source |
|---|---|
| §3 DB schema (Drizzle/Prisma/…) | `create-architecture` data model (entities + fields), OR a schema doc the policy names (e.g. `docs/report-formats.md`) |
| §3 capability grep of current surface | PRD FRs + epics/stories (there is no surface to grep — the mutation-derivation audit reduces to the ingest audit) |
| §3a `relational-edges.yaml` / FK walk | architecture entity relationships; `relational-edges.yaml` may be absent on a fresh project — derive edges from the architecture |
| §4 feature purpose from code | PRD feature statement + FRs |
| §6 user context from code | PRD personas + `create-ux-design` flows |
| §7 surface inventory | the `create-ux-design` page inventory (maps ~1:1 onto §5f frames) |

**Gap rules (do NOT fabricate what the spec sources don't contain):**

1. **§2 type/nullability degrade — never invent.** A schema doc (e.g. `report-formats.md`) yields column **names + notes only**; it has no SQL types and only implicit nullability. Set `Type`/`Nullable` to `n/a` rather than guessing. Use a column dictionary (e.g. `docs/data-sources-reference.md`) for types **only if it exists**.
2. **§3 capabilities are floor-only.** With no surface to grep, derive only the capabilities the PRD FRs + ingest audit name. Collect everything a capable operator would plausibly need but no spec fixes (export, scoped search, column-visibility, sticky header, raw-vs-derived split, …) into a `{capabilities_need_human}` stub list and surface it as Open Questions — do NOT ship a thin capability set silently.
3. **§4 residue/inheriting policy.** When `docs/design-policy.md` is residue-only or inherits a family overlay (defers concrete tokens to a future `brand-identity.md`), §4/§5 quote the policy **residue + the named overlay** — NOT a 9-section brand-identity copy (there is none).
4. **No-guessed-edges still holds (§3a).** Derive linked records from architecture relationships; if an edge isn't in the architecture, route "declare it" — never invent it in the brief. (The §5a `source-mirror` archetype already suppresses §13 expand-in-context for a faithful-mirror surface — §5f draws the single frame.)

**Then:** set `{skip_step_02} = true` (nothing built to audit — step-02 is skipped) and proceed. Step-03 stamps this brief `revision_mode: spec_derived`, `last_modified_by: human`, `last_modified_date == source_run_date` (`brief-revision-policy.md` §4); predecessor lookup / `change_class` are unchanged (zero active matches → `original`, one → `material_revision`).

### 2. Identify the Feature

Determine `{feature_name}` and `{feature_scope}` from user input or recent git history:

```bash
git log --oneline -10
git diff --name-only HEAD~3..HEAD
```

Set `{feature_scope}`:
- **"new"** — component file was created (not modified) in recent commits
- **"redesign"** — component exists and user wants it redesigned

#### 2-pre. Prerequisite gate — is the target's basis built or settled? (grounding; overrides autonomous_mode)

design-handoff produces a brief from a basis that **already exists**: a `redesign` extracts `{data_shape}` + `{user_context}` from an implementation; a `new` (from-scratch) brief designs against a **settled spec / data-model + intent**. It must NOT *decide* an unbuilt feature's architecture — a brief invented over an open question silently fabricates the very decision (credential type, role split, field set) an upstream PRD/architecture step owns. (design-router's intake grounds that the target can be *named*; this grounds that its *basis exists* — a distinct check.)

Before §3 capture, confirm the target resolves to ONE of: **an existing implementation** (a matching route/component on disk → `redesign`) OR **a settled spec** (a PRD/architecture artifact fixing the data-model + intent → `new`).

**HALT-and-reroute (fires even under `autonomous_mode`)** when **neither** holds — deterministic signal: `feature_scope=new` AND no matching route/component on disk for the target AND the feature is named in the PRD Open-Questions / unmet-FR list (or has no PRD coverage). Do NOT enter capture; emit and halt (a grounding reroute, not a failure — like the §2a redirect, the flag does not license fabricating the missing model):

> design-handoff — target not grounded (no implementation AND no settled spec).
>
> "{target}" has no implementation on disk and its data-model/intent is an open upstream decision (cite the PRD Open-Question / unmet FR if known). A brief here would invent that decision (credential / field / role model), which the PRD/architecture step owns — not a design brief.
>
> Route: `bmad-prd` (settle the requirement) → `bmad-architecture` (settle data-model/intent), then return for `new` — or `bmad-ux` / `design-artifact-loop` (design-from-brief) once a spec exists.

When the target IS grounded (an implementation exists, or a settled spec does), proceed.

**Greenfield (`{is_greenfield}`) — on-disk absence is EXPECTED, not an ungrounding.** A greenfield project has no implementation by definition, so "no matching route/component on disk" must NOT trigger the HALT on its own. The greenfield grounding basis is a **settled spec** (a `create-architecture` data-model + a PRD/UX intent) **OR a design-policy surface declaration** (the surface named as an archetype in `docs/design-policy.md` §3, with its data sourced from a schema doc per §1c). HALT-and-reroute only when **none** of those exist — i.e. the surface is neither in the architecture/PRD/UX nor declared in the policy, so its data-model/intent is genuinely an open upstream decision. (Same reroute target: settle it in `bmad-architecture` / `bmad-prd` first.) The §1c source binding presumes this gate passed on a spec/policy basis.

#### 2a. Lookup-drawer target redirect — route, never bounce (destination vs relationship)

A §13 expand-in-context **lookup drawer** (the small drawer that opens *over* a surface when you act on a foreign reference — a `catalog-lookup` over an order, a `warehouse-lookup`, a `supply-source-lookup`) is **owned by the relation, not by a page** (Deliverable-Completeness Principle; brief-template §2a). It is drawn as a **frame in its parent surface's §7 Surface Inventory**, never as its own brief — a separate brief for it would be a duplicate of an already-owned frame and trip the brief-revision-policy multiple-active-brief invariant. So **`design-handoff` does not accept a lookup drawer as a standalone target** — but it must **route**, not reject opaquely (the user targeted it because the drawer is shipping thin; bouncing them with no path is the friction this gate kills).

**Detect.** The resolved target is a lookup drawer when it is a §13 expand-in-context drawer over another surface — signals: the component is a `*-record-drawer` / `*-lookup` that renders a foreign record keyed by an FK/derived edge (an ASIN, warehouse, supply source, batch) opened from a parent surface; the user describes it as "the X drawer/link when I click Y on Z"; it has no route of its own. (When ambiguous between a lookup drawer and a real drilled detail drawer that owns a page/route, treat it as a normal target — only the relation-owned lookup redirects.)

**Redirect (do NOT produce a standalone brief).** Identify the parent surface (the one the drawer opens *over*) and emit:

```
design-handoff — lookup-drawer target redirected (not rejected).

"{target}" is a §13 expand-in-context lookup drawer. It is owned by the
RELATION, so it is drawn as a frame in its parent surface's §7 Surface
Inventory — never its own brief (that would duplicate an owned frame and
break the multiple-active-brief invariant). Destination vs relationship:
a destination (a real page / deep /[id] route) gets a handoff; a
relationship (a lookup over a parent) rides its parent's brief.

It is shipping thin because of WHERE in the pipeline it was missed — pick
the matching fix:

  • Its parent brief's §7 already lists it as a frame, but it was never
    DRAWN → re-run design-synthesize on the PARENT brief (now §7-aware:
    every Surface Inventory frame becomes a rendered screen), then
    design-implement to build the drawn frame. ← most common; this is the
    render gap, not a design gap.

  • Its parent brief has NO §7 frame for it (older brief) → re-run
    design-handoff on the PARENT surface "{parent}" (material revision) so
    step-01 §5f enumerates the lookup drawer into §7, then synthesize +
    implement.

  • You want the foreign RECORD itself redesigned everywhere it expands →
    run design-handoff on that record's OWNING surface "{owner_route}"
    (material revision), not on this one drawer instance.

Parent surface: {parent}   ·   Foreign record / owner: {record} / {owner_route}
```

Then **halt this run** (no brief produced). This is a routing redirect, not a failure — state the chosen next command so the user can run it directly. (Autonomous mode does not override this: producing the duplicate brief is an *intent* violation, not a decision the flag licenses.)

### 3. Map the Data Surface

**Route:**
- What URL path does this feature live at?
- Note the route path — NOT the component that renders at it

**Data Model — Procedural Capture (anti-bias):**

Follow these steps in order. The goal is to capture domain entities from the source of truth (DB schema), not from the page server's UI-shaped response.

1. **Open the DB schema** at the project's source of truth. Common locations: `src/lib/server/db/schema.ts` (Drizzle), `prisma/schema.prisma` (Prisma), `app/models/` (Rails), `models.py` (Django), `migrations/*.sql` (raw SQL), or equivalent. Find the tables this feature reads from. **Greenfield (`{is_greenfield}`):** there is no schema file — read the `create-architecture` data-model (or the schema doc the policy names, e.g. `docs/report-formats.md`) per §1c, and apply the §1c gap rule 1 (Type/Nullable degrade to `n/a`, never invent).
2. **For each entity**, list its columns: name, type, nullability. These are the primitive fields.
3. **Stop. Do NOT open the page-shaped server response file to get the data shape.** Examples: `+page.server.ts` (SvelteKit), `getServerSideProps` or route `loader` (Next.js), controller action (Rails), view function (Django/Flask), GraphQL resolver, etc. These denormalize, group, pre-compute, and add rendering hints — all of which bias the designer. If you need to know which entities the feature uses, check the file's imports or queries, but do NOT copy its return type.
4. **Flatten any nested structures.** If the schema has a foreign key (e.g., `supplier_country` on an invoice), that's a flat field on the row — not a grouping dimension. Record it as a field.
5. **Drop anything not in the schema:**
   - Pre-computed derivations (`daysLeft`, `totalNet`, `filingProgress`, etc.) — keep only the inputs (deadline date, money amount, status enum)
   - Rendering hints (`flag`, `badgeColor`, emoji fields) — keep only the underlying data (`countryCode`, status enum)
   - UI-control enums (`'all' | 'not_filed' | 'ready'`) — "all" is a filter affordance, not data. Keep only the row-level status enum.
   - Precomputed rollups (`domesticCount`, `countryTotal`, `validCount`) — the designer decides which aggregations matter.
6. **Note which primitive fields are nullable** — these need empty-state treatment.

Capture `{data_shape}` in **domain-entity table form** (see step-03 template). If you find yourself copy-pasting `interface PageData { ... }`, you've gone off track.

**API Surface:**
- What endpoints does the frontend call? → `{api_surface}`
- What does each response look like? (reference the data shape)
- What mutations are available? (POST/PUT/DELETE endpoints)
- **Ingest / entry-point audit:** For each entity type the feature displays, ask: *how does a new record enter the system?* Is there an upload, import, manual-create, webhook, or scraper that populates it? A production page-level affordance that seeds the pipeline (e.g. a "Upload wholesale price list" button) is a **capability**, not just a technical endpoint — capture it in `{must_support_capabilities}` (as an outcome) AND in `{api_surface}` (as the mutation). Miss it and the redesign can browse records but never create them. This is the most common single-capability loss in redesign-scope briefs.
- **Mutation-derivation audit (anti-recall — DERIVE capabilities, don't remember them):** The data shape is *derived* from the schema (above), so no field can be silently missed. Capabilities must be derived the **same mechanical way**, not recalled — recall is where they leak. For a **redesign**, `grep` the *current* surface's implementing component files for every server action / mutation they import and call (this reads the **verbs the screen exposes**, NOT its layout — so it stays inside the anti-bias rule; you are cataloguing what the operator can *do*, never how it's arranged). Then account for **every** action found — each must resolve to exactly one of:
  - a **primary user goal** or a **`{must_support_capabilities}`** entry — the capability is carried forward (name it as an outcome), OR
  - a **deliberate drop** — recorded in `{dropped_capabilities}` as `{ capability (outcome phrasing) · backing_action · reason }`, where `reason` is one of: `relocated` (to a named sibling surface), `obsolete`, or `out-of-scope-by-design`.
  No action may be left unaccounted for. The **ingest audit** above catches mutations that *create* records; **this** audit catches mutations on *existing* records — resolve / remap / override / re-run / reprice / reconcile / approve / dismiss — the subclass a blank-canvas redesign sheds most easily because each is neither a primary goal nor an entry-point, and the anti-bias rule discourages the very UI-reading that would surface it. An action that lands in **neither** bucket is the silent capability loss this audit exists to make impossible (the EAN→ASIN remap dropped from the EOS batch-detail redesign — `overrideWholesaleAsinAction` left with zero callers — is the canonical case). For a **new** feature there is no current surface to grep, so this audit reduces to the ingest audit alone.

**Implementation Files:**
- List relevant file paths → `{implementation_files}`
- Include: type definitions, API route handlers, the main page component path, CSS/style files
- These are for technical reference, NOT layout reference
- **DO-NOT-READ list (redesign scope only):** for `{feature_scope}` = "redesign", also list every file that renders the target surface's CURRENT markup/structure — the view entry point (page/HTML/component file), its section components, and any layout-owning module (state→DOM rendering, template builders) → `{do_not_read_files}`, one line each with a short "what it renders" note. You already touched these in the mutation-derivation audit above (grepping verbs, not layout) — record their paths now so brief §8 can name them as off-limits to the designer. This list feeds the §8 🚫 DO-NOT-READ block; a redesign brief without it leaves the current layout one innocent file-open away (the anchoring hole). For "new" scope, leave `{do_not_read_files}` unset.

### 3a. Linked-records inventory — every on-screen value that IS a foreign record

Project design-policy **§13 (Cross-surface relational coherence — linked records & lookups)** is a **contract-critical §12 assertion that `design-review-pr` enforces as a hard failure**: any on-screen value that IS a record *owned by another surface* (ASIN, SKU, order number, batch, shipment, supplier, customs entry, listing, …) must **resolve and expand that foreign record in context** — never inert duplicated text, and **never a link that merely navigates away** to the sibling page. The §13 function is **expand-in-context, not navigate-away**: acting on the reference opens the foreign record in the project's §7 right-side drawer *over* the current surface, showing that record's own fields and its own linked references (recursively), with related fields surfaced as lookups read through the relation. Because this brief withholds the current layout (blank canvas), the one place that linking was visible is gone; if the brief is silent on it, the redesign defaults to inert text and **fails review on the way back in**. So derive the inventory here — mechanically, the same anti-recall way as the data surface (§3) and the mutation audit — never leave it for the designer to rediscover.

**Seed from the maintained linkage map first (don't rediscover).** The project keeps a maintained relational-coherence home at `docs/relational-coherence/` — `relational-edges.yaml` (the hand-maintained edge + co-view map: which on-screen value IS a record another surface owns, including the *derived* relationships the schema can't express, like the SellerSmart warehouse push) and `reports/relational-coherence-audit-*.md` (the latest §13 graph audit, already walked against the live surface by Wren / the relational-coherence-audit). **Read both for this surface before deriving anything.** They are the authoritative, already-resolved source — every edge whose `to` is owned by another surface and whose `from` is this surface seeds a `{linked_records_inventory}` entry with its `owner_route`, expand-in-context target, and `mandated_lookups` carried straight through. If a relational-coherence-audit routed this handoff (a missing-required link or a co-view seam), its §2a seed is already attached — use it verbatim, don't re-derive. If the map exists but omits a foreign reference you find below, that's a gap — note it and route "declare it" back to the audit (no-guessed-edges), never invent the edge in the brief. The derivation below is the cross-check (and the fallback when the home is absent), not the primary source.

**Derive (don't recall).** From the `{data_shape}` and route just mapped — cross-checked against the maintained edge map above — for **each** field that resolves to a record another surface owns (start from the foreign keys / natural keys flattened in §3 step 4 — `supplier`, `asin`, `order_number`, `batch_id`, …):
1. **Foreign reference** — the field/identifier as it appears on this surface.
2. **Owning surface** — which surface owns that record, and its route (`/suppliers/[id]`, `/catalog/[asin]`, …). If no surface owns it yet, say so — it is a plain value, not a link, and does not belong in the inventory.
3. **Expand-in-context target (§7 drawer, NOT navigate-away)** — acting on the reference opens **the foreign record** in the right-side **detail drawer** (§7) *over the current surface*, showing that record's own fields and its own linked references (recursive). Name the foreign record that expands and the §7 drawer as the expand surface. Crossing to the sibling's full page ("Open full {sibling} →") is a **secondary** action *inside* the expanded record — note it as secondary, never as the primary drill. A reference whose only behavior is to navigate to the sibling page is a §13 hard failure.
4. **Inline lookups** — any *related field* this surface needs from that foreign record to make its decision (a supplier's lead-time, a catalog product's image/title on an order line, an order's marketplace/currency on a batch). These render as **read-only** lookups read *through the relation* from the canonical record — never re-keyed per surface.

Set `{linked_records_inventory}` — one entry per foreign reference, each with the four facts above. **Empty only when nothing on the surface resolves to a foreign record** (a true leaf surface); empty-by-omission is the silent failure this step exists to prevent — the §13 mandate is invisible to the designer unless this inventory carries it into the brief. The §13 *form* guardrail (the affordance is the quiet demoted-blue §4 link + the §7 drawer, **never** a button, CTA, colored pill, chip, or Airtable modal chrome) travels with the inventory into brief §2a — Airtable's **relation** imported (expand-in-context + lookups), Airtable's **form** rejected.

### 3b. Finance-domain pass — semantics a blank-canvas redesign must preserve (conditional)

Fires **only when finance presentation is material** to the surface — money is a primary data type
(not an incidental field); the operator reviews/reconciles quantities, values, balances, costs, taxes,
landed costs, or variances; the data is inventory/ledger/payout/statement/VAT/reconciliation/accounting
export; or mispresenting missing/estimated/anomalous/duplicate-grouped values could distort financial
truth. **Skip** (`{is_finance_surface}` = `false`) when money is a minor field on a general CRUD page,
the task is pure styling/layout, or another domain owns the semantics; if uncertain, fire only when bad
presentation could distort operational or financial truth, else proceed without it and note the
ambiguity. (Full gate: `finance-domain-pass` "When to invoke".) Finance surfaces hide load-bearing semantics inside the layout this
brief withholds (lifecycle states, quantity/value separation, reconciliation, exceptions); without this
pass a blank-canvas redesign silently drops them or guesses them as taste. This pass captures the
finance **meaning** — never the layout.

**Invoke the skill (mode: extract).** Load `finance-domain-pass` via the Skill tool and pass it:
- the **source artifact** (the data file / page / export the handoff is about),
- the **`{data_shape}`** and **`{linked_records_inventory}`** just derived (§3, §3a),
- read-only awareness of `docs/design-policy.md` (so it surfaces collisions as open questions, never overrides).

The skill runs its procedure (detect type → column semantics → capabilities-as-outcomes → shed-capability
flags → exception expectations → implied surfaces → unresolved assumptions → terminology → must-not-infer)
and returns its **appendix object**. It governs finance meaning, NOT layout — it never names a bar, card,
drawer, or composition. Capture it and route each field into the existing machinery:

| Appendix field | Captured / routed into |
| --- | --- |
| `report_type_detected` | `{finance_report_type}` — a §1 context signal; does **not** set `{page_mode}` or composition |
| `source_column_semantics` | `{finance_column_semantics}` — enriches `{data_shape}` (Domain Data); never blends qty + value |
| `must_preserve_capabilities` | **merge into** `{must_support_capabilities}` (§4) — as outcomes |
| `dropped_capability_flags` | **cross-check into** `{dropped_capabilities}` (§3 mutation audit) — confirm each, don't auto-drop |
| `exception_expectations` | `{finance_exception_expectations}` — representability requirements (NOT a panel design) |
| `implied_surfaces` | **feed §5f** `{spawned_surfaces}` as candidates (frame-name keyed, depth-1; §5f reconciles + owns the final inventory) |
| `unresolved_assumptions` | `{finance_unresolved_assumptions}` — rendered as brief Open Questions; **never resolved here** |
| `terminology` | `{finance_terminology}` — canonical terms for brief labeling |
| `must_not_infer` | `{finance_must_not_infer}` — acceptance constraints preserving accounting truth |
| `policy_collisions` | surface to the user as `modify-design-policy` candidates — do **not** patch the brief around policy |

**Outcomes, never mechanics.** If any captured capability or surface can't be stated without naming a
component, it was a layout leak — drop it. **Never resolve an unknown:** a flagged `unresolved_assumption`
(status source-of-truth, valuation/costing basis, block/line semantics, FX basis) goes to the brief's
Open Questions verbatim; the pass never decides it and the brief never invents it.

**Fallback (skill not synced).** If `finance-domain-pass` is absent (older sync), apply the same
procedure inline using `{project-root}/_bmad/bmm/workflows/shared/` finance conventions + the
`finance-presentation` standard, and populate the same capture fields by hand. The skill is preferred
(it makes the must-not-infer and capability outputs mandatory rather than skippable prose), but handoff
must not hard-fail when it is absent.

### 3c. Live-process pass — runtime behavior a blank-canvas redesign must preserve (conditional)

Fires **only when the surface's primary job is watching or controlling a long-running in-flight process** — a scrape/download run, an import/ingestion job, a sweep, a sync, a batch reconciliation: the page's content changes over time while the operator watches, and the process can partially fail mid-flight. Set `{is_live_process_surface}` = `true` and run the capture below. **Skip** (`false`) for request/response CRUD surfaces where data changes only on user action, and for surfaces that merely *display* a job's finished output; if uncertain, fire only when the operator's core anxiety is "is it still working, and what went wrong?" — else proceed without it and note the ambiguity. A live-process surface hides its load-bearing semantics in *time*, which a brief's static data tables cannot carry: without this pass a blank-canvas redesign depicts one moment of a process whose whole job is change, and the temporal contract (states, staleness, control) never reaches the designer. This pass captures the runtime **meaning** — never widgets, never layout.

**Capture `{runtime_behavior_contract}` — derive from the code that drives the process (its status enums, message types, storage writes), never from memory and never invented.** Greenfield (`{is_greenfield}`): derive from the PRD/architecture's process description per §1c, degrading unknown fields to Open Questions rather than guessing. Five facts:

1. **Run lifecycle** — the state machine of one run: every state, every transition, and what triggers it (operator action, item completion, throttle, fatal error). Read it from the actual state enum/handling; a state the code doesn't have may not be invented, and a state it has may not be dropped.
2. **Per-item states** — the states one work item passes through, **including every failure/partial lane** (throttled, held, load-error, retrying, skipped, missing-at-source). Partial failure is the normal case on a live process, not an edge case.
3. **Update transport & staleness** — how this surface learns the process changed (pushed message, storage listener, poll — and at what cadence), and how stale the display can legitimately be. Staleness is a **designed property** the brief must state, not an accident the designer discovers; if the current transport makes honest liveness impossible (e.g. slow polling), record that as a constraint/open question — do NOT silently spec a liveness the plumbing can't deliver.
4. **Control verbs** — what the operator can do to a run in flight (pause / resume / cancel / retry / reprioritize) with their **real** semantics: immediate or drains in-flight items, resumable or restart-from-zero, per-item or whole-run. As outcomes ("stop the run without losing completed work"), never as buttons.
5. **Progress signals available** — the raw signals the design may derive progress from: counts by state, per-item/per-marketplace telemetry, timing data usable for pacing reads, run-report/history data. Signals only — never prescribe a progress bar, spinner, or log panel; the derivation is the designer's.

**Route into the existing machinery:** each lifecycle state that changes what the operator sees or can do becomes a **state-variant frame candidate** for the primary surface, fed to §5f (which owns the final inventory) — the film-strip is how a static brief communicates a dynamic mechanism. Control verbs that invoke server/extension actions also cross-check against the §3 mutation-derivation audit (a pause/cancel/retry action is a mutation — it must land in `{must_support_capabilities}` or `{dropped_capabilities}` like any other). Unresolvable semantics (what "cancel" really does to in-flight items, whether a run is resumable) go to the brief's Open Questions verbatim — never resolved here. Actual motion/transition/animation verification stays ceded downstream (`design-review` / `verify`); the brief carries states and cadence, not animations.

### 3d. Interaction-model pass — how the operator DRIVES a processing cockpit (conditional)

Fires **only when the surface is a processing cockpit**: `{page_mode}` = `operational` AND the §2 user context is **expert, high-frequency, keyboard-first** — a queue/worklist the operator clears one item at a time at speed (mapping-queue, a reconciliation lane, a review queue). Set `{is_processing_cockpit}` = `true` and run the capture below. **Skip** (`false`) for occasional/low-frequency operational surfaces, read-mostly dashboards, chrome, and any surface where the operator is not repeatedly committing per-item decisions. If uncertain, fire only when §2 already says keyboard-first / high-frequency AND §1's success metrics reward *speed* (time-to-decision, fewer stuck defers) — else proceed without it and note the ambiguity.

**Why this pass exists (the gap it closes):** a static brief captures *what to show* (composition, data, evidence, contracts) but never *how the surface is operated* — keyboard flow, per-item commit→advance momentum, seeing a consequence before an irreversible commit. Those requirements are derivable from signals the brief ALREADY carries (§2 keyboard-first/high-frequency user, §1 speed metrics), but without this pass nothing converts them into requirements, so a blank-canvas redesign ships a beautiful click-only form and the speed goals fail silently — discovered only when a human drives a prototype. This pass captures the interaction **meaning** — never key maps, never widgets.

**Capture `{interaction_model_contract}` — derive from §1 (`{must_support_capabilities}` verbs), §2 (user context), the §3 mutation audit, and §2b basis where a figure is written; never invented.** Five facts:

1. **Operation surface** — keyboard-first vs pointer-first. For an expert high-frequency cockpit it is keyboard-first: every per-item verb reachable + committable without the mouse, plus a persistent shortcut affordance. State as an outcome, not a key map.
2. **Per-item action set & commit weight** — each per-item verb from `{must_support_capabilities}`, classed **reversible** (skip / defer / claim) vs **irreversible / high-stakes** (immutable key, money, partner write). The irreversible set is what requires a consequence-preview (fact 4).
3. **Momentum after commit** — what happens on decide: auto-advance vs manual, to the next *actionable* item (skip claimed-by-other / read-only), with an undo/safety window. Derived from §1 speed metrics.
4. **Consequence-preview** — which irreversible verbs must show WHAT the commit writes (resulting record + derived figure per §2b basis) BEFORE committing. The correctness lever for hard-to-undo writes.
5. **Confidence-scaled effort** — where the machine is confident/unambiguous → a one-action fast path; where ambiguous/detectors disagree → the full decision is FORCED (no rubber-stamp). Derived from §1 "fewer stuck defers".

**Route into the existing machinery:** the per-item verbs cross-check the §3 mutation-derivation audit exactly like §3c control verbs (a commit that invokes a server action must be in `{must_support_capabilities}` / `{dropped_capabilities}`). A consequence-preview that shows a cost/KPI figure inherits the §2b/§4d **DERIVED-vs-PERSISTED** basis rule (never present a derived number as stored). This pass produces **no new frames** — it is a cross-cutting behavior contract rendered into brief §4f (like §2c), NOT a Surface-Inventory entry. Unresolved semantics go to the brief's Open Questions verbatim. Actual keyboard-focus/animation verification stays ceded downstream (`design-review` / `verify`); the brief carries the operation model, not the bindings.

### 3e. Operator-domain pass — who the operator is and what the surface must SHOW before it ASKS (conditional)

Fires when **`{is_processing_cockpit}` = true** (the same flag §3d sets — §3d and §3e **co-fire** on a decide-one operator cockpit). §3d captures how the operator DRIVES the surface; §3e captures **who the operator is and what they must know**. **Skip** (`{operator_domain_present}` = `false`) whenever §3d skipped.

**Why this pass exists (the gap it closes):** `design-handoff` already detects the cockpit, applies the `operational-cockpit` M1–M6 floor (into §4f), and captures the interaction model (§3d) — but nothing injects the operator's ROLE semantics (who they are, the trust boundary, what the system already knows before each ask, what they must decide, the evidence required BEFORE input, the forbidden asks). So M6 ("surface the evidence the decision requires") ships **domain-blind** — the surface asks the operator for input the system could have resolved and shown first (the clerk-works-blind defect). This pass captures operator **meaning** — never layout. It is the twin of §3b `finance-domain-pass` for MONEY, applied to OPERATOR ROLE.

**Invoke the skill (mode: extract).** Load `operator-domain-pass` via the Skill tool and pass it:
- the resolved **operator-domain profile** — `docs/<operator>-operational-profile.md` (e.g. `docs/clerk-operational-profile.md`); resolving this is §3e's first action,
- read-only extraction context: `{is_processing_cockpit}`, `{page_mode}`, `{must_support_capabilities}` (§4), `{interaction_model_contract}` (§3d), the §3 mutation/ask audit, and §2 user context — never layout,
- read-only awareness of `docs/design-policy.md` (so a policy collision is surfaced as an open question, never overridden).

**HALT-on-missing-profile (hard stop).** If `{is_processing_cockpit}` = true and no `docs/<operator>-operational-profile.md` resolves, **do NOT emit an operator appendix and do NOT proceed on generic cockpit doctrine** — surface the blocking diagnostic (see the `operator-domain-pass` skill § Enforcement: "missing operator-domain profile for cockpit handoff / why this blocks … / next step: supply or select `docs/<operator>-operational-profile.md`, then rerun design-handoff"). `semantically_incomplete` is permitted only if a safe downstream consumer behavior is named that keeps the warning visible and prevents silent best-effort use; absent that, HALT.

The skill runs its procedure (resolve profile → per-decision extract → operator header → must-not-infer → ordering-invariants → policy-collision detect → **internal-consistency validation gate**) and returns its **appendix object**. Capture each field into the `{operator_*}` state variables:

| Appendix field | Captured into |
| --- | --- |
| `operator_detected` | `{operator_detected}` — a §1 context signal; does **not** set `{page_mode}`/composition |
| `operator_role` | `{operator_role}` |
| `trust_boundary` | `{operator_trust_boundary}` (`may_decide` / `may_not_decide` / `write_trust`) |
| `decision_points[].operator_decides` | `{operator_decides}` (per decision) |
| `decision_points[].known_before_each_ask` | `{operator_known_before_ask}` (per decision) |
| `decision_points[].evidence_required` | `{operator_evidence_required}` (per decision) |
| `decision_points[].forbidden_asks` | `{operator_forbidden_asks}` (per decision) |
| `must_not_infer` | `{operator_must_not_infer}` — top-level operator-truth constraints |
| `ordering_invariants` | `{operator_ordering_invariants}` — top-level |
| `policy_collisions` | `{operator_policy_collisions}` — open questions to the brief; **never resolved here** |

Set `{operator_domain_present}` = `true` once the profile resolved AND the validation gate passed. The per-item verbs cross-check the §3 mutation audit exactly like §3d (a commit that invokes a server action must be in `{must_support_capabilities}` / `{dropped_capabilities}`). This pass produces **no new frames** — it is a cross-cutting operator-meaning contract rendered into brief §4f alongside the interaction model, NOT a Surface-Inventory entry. A `{operator_policy_collision}` is an open question a human must resolve in the brief; the pass never bends policy to fit the profile or vice versa.

**Fallback (skill not synced).** If `operator-domain-pass` is absent (older sync), produce the same appendix **by hand** from `docs/<operator>-operational-profile.md` against the skill's manual checklist — **the same internal-consistency validation gate runs on this path**, so skipping the skill does not skip the gate, and HALT-on-missing-profile still applies (the profile, not the skill, is the load-bearing input). `{is_processing_cockpit}` may not be marked fully captured until the checklist passes.

### 3f. Viewport & responsive pass — the per-surface viewport CONTRACT (every page)

Fires on **every `{surface_class} == page` run** (skip for `chrome` — step-01 §0 already captures `nav-desktop` vs `nav-mobile-drawer` breakpoints; `{viewport_present}` stays unset there). Unlike §3d/§3e (cockpit-only), this is UNIVERSAL for content pages: a page brief that never states its viewport posture ships desktop-blind, and the non-interpretive downstream pipeline then guesses one.

**Why this pass exists (the gap it closes):** owner content surfaces had no responsive doctrine and the gather ran no structured viewport pass — the only mobile signal was the freeform §5 `constraints — responsive breakpoints` field, routinely left empty. This pass makes viewport a first-class, policy-sourced contract. It captures viewport MEANING from policy — never invents a posture. Twin of §3b `finance-domain-pass` (money) / §3e `operator-domain-pass` (operator role), for VIEWPORT.

**Source of truth: the project `docs/design-policy.md §8` (surface-class → viewport policy). Never invent a breakpoint, tap target, or phone-support decision.** (If the project has no §8 viewport policy, record an Open Question — "no viewport policy in docs/design-policy.md; author §8 first" — and do not fabricate one.)

1. **Resolve `{viewport_surface_class}`** — match `{route}` against policy §8.1's class→route table (e.g. `clerk_bench` | `owner_dashboards_worklists` | `owner_approvals_recovery_reimbursements` | `owner_listings_catalog`). Unmappable ⇒ record an Open Question ("route not mapped to a viewport surface-class in policy §8.1"), do NOT guess a class.

   **Membership is QUOTED, never asserted (added 2026-07-29 — `FG-2026-07-29-01`).** Resolving a class means finding `{route}` **literally present** in that class's Members cell, and **copying the matched member text verbatim** into `{viewport_class_evidence}`, which §4g renders beside the class name. A class name with no quoted member string is **not a resolution** — it is an assertion, and gate (a) cannot tell the two apart: (a) fails an *unresolved* class, never a *wrongly resolved* one. **A near-miss is a MISS.** A sibling route in the class (`/foo` present, `/foo/[id]` absent), a route that "obviously belongs", a predecessor brief that already carried the class, or a changelog entry that mapped a *different* route — none of these is membership. Each resolves to **unmappable** ⇒ the step-1 Open Question, exactly as if no class existed. **Do not repair the policy from inside this workflow:** adding the missing member is a policy edit with its own owner-ruling discipline (posture is decided per class, on each class's own job), and doing it here launders a guess into a citation.

   *Observed 2026-07-28: a brief recorded `viewport_surface_class: owner_dashboards_worklists` "resolved from §8.1 (mapped in policy v17)". v17 mapped a different route and nothing else — neither ingestion route had ever been in §8.1. Gate (a) passed (a class WAS named), the brief shipped `pending-policy` — which reads as correctly-following-policy, not as unverified — and every downstream consumer inherited a guessed posture. The route was later mapped by a genuine owner ruling, which is what makes the original citation checkable at all.*
2. **Decided class → AUTO-FILL from policy §8.2 (whatever posture it decided — do NOT assume desktop-only).** If the resolved class is DECIDED in policy §8.2, fill all six fields from THAT class's §8.2 block **verbatim**. A decided class can be any posture, e.g.:
   - a **desktop-only** bench class (e.g. grading/scanning/reconciliation): `{primary_viewport_class}` = `desktop-only`, `{viewport_breakpoints}` = `desktop-only ≥1280px, landscape`, keyboard + hardware scanner, `{viewport_min_tap_target}` = n/a, `{viewport_device_exclusions}` = `phone, tablet — a mobile/faux-mobile UI here is a policy VIOLATION` (cite the project's clerk-web-mode hard-failure);
   - a **handheld-first / mobile-primary** class (e.g. a roaming receiving clerk): `{primary_viewport_class}` = `mobile-first`, phone viewport / portrait / one-handed, mobile scanner, offline-capable if the policy says so, desktop **additive-only** (a desktop-only mouse-dependent layout is the VIOLATION here), `{viewport_min_tap_target}` from policy.
   **Never hardcode desktop-only — read the class's actual §8.2 decision** (a class can be decided desktop-only OR decided mobile-first). Then run the validation gate (step 5).
3. **Owner class + ambition OPEN → WARN-ONLY (do not freeze owner work).** If the resolved class is an owner class and policy §8.3's mobile ambition is still OPEN (the ⚠ OPEN ITEM marker present, ambition unset): **render §4g with the six owner fields marked `pending — awaiting the owner's §8.3 mobile-ambition decision`, set `{viewport_pending_policy}` = true, mark the brief `unverified` / `pending-policy`, and LET THE HANDOFF CONTINUE.** Never invent breakpoints, tap targets, or phone support. Surface the loud diagnostic verbatim:
   > **Viewport policy not set for this owner surface-class. Mason must choose the mobile ambition (tablet-down desktop-primary · mobile-first · desktop-only) in `docs/design-policy.md §8.3`. This brief is marked pending-policy and unverified until that decision — proceeding without freezing owner work.**
   This is **warn-then-gate**: a small follow-up flips this to a hard HALT once the ambition is set. (PROBABILISTIC workflow warn — see § Enforcement tier below; the deterministic companion is the per-project brief-artifact validator.)
4. **Owner class + ambition SET → read from policy §8.3.** Once the owner has set the ambition, populate all six fields from policy per class; never soften or reinterpret. (A missing/partial field HERE — ambition set but a field blank — is a HARD fail, not a warn; see step 5.)
4b. **DECIDED class → derive `{canonical_viewport}` + `{additive_viewports}` (the ARTIFACT-LABELING half).** Steps 1–4 capture which viewport the surface is DESIGNED FOR; they do NOT control how the rendered artifact MARKS it. An unlabelled phone/tablet/desktop comp set contradicts **none** of the six fields, so the gate below passed it while the artifact read desktop-first to every cold reader — and the §7 deliverable line then told the designer "desktop width" regardless of posture. Close that here. **DERIVE, never choose** — if the project policy carries a canonical-vs-additive subsection (e.g. cash-recovery `docs/design-policy.md` §8.2c), read its values verbatim instead:
   - `{canonical_viewport}` — the ONE viewport the interaction model is designed at and judged against, read off `{primary_viewport_class}`: `mobile-first`/handheld-first ⇒ **phone portrait, 375×812 reference**; `desktop-only`/`desktop-primary` ⇒ **desktop ≥1280 landscape, 1440×900 reference**; `tablet-down` ⇒ the policy's named tablet reference. Exactly one — a surface with two canonical viewports has none.
   - `{additive_viewports}` — every other `{viewport_breakpoints}` entry, each an **additive verification render**: a CHECK that the canonical model survives a different container, never a second design. Anything in `{viewport_device_exclusions}` is in NEITHER list and is **not rendered at all**.
   - **Owner class with an OPEN ambition ⇒ leave both unset, skip this derivation, and gate class (e) does not apply.** There is no decided posture to mark; do not invent one.
4c. **Handheld-first DECIDED class → assemble `{handheld_declaration}` (the ARTIFACT-COMPOSITION half).** (e) makes the deliverable be *drawn at* the right viewport; it does not stop the artifact being a **review board** — co-equal comps, rationale competing with the surface, state variants as peer mini-products. Contract + failure shape + golden cases: **`shared/operator-artifact-contract.md`** (rules B1–B7) — read it, do not restate it. **On a table-first surface, also carry rule B7 into §7** — the canonical render must be specified as a **compressed operational stack** (compact header reading as the top of the list; count + primary action loud but inline in the worklist header; secondary counts/filters collapsed at label weight, no chip wall; ≥1 real data row visible at rest), because the artifact-level rules alone will pass a **DASHBOARD OPENER**. Assemble the five declaration fields it requires: surface class · canonical viewport · additive viewports (`none` legal) · **scan/next-step loop** (stated as a loop: trigger → feedback → next, from `{core_job}` / the §3c contract — never a feature list) · **offline/degraded state treatment** (which degraded states are first-class + the B3 statement that they are drawn as states OF this surface, sourced from the class's offline policy and the §5f state-variant frames). `TBD`/`responsive`/`see policy` are non-answers. **Skip entirely on a desktop-only class and on any OPEN owner ambition.**
5. **Validation gate (runs on both paths) — three classes, don't conflate them:** **HARD FAIL** (set `{viewport_present}` = false, brief NOT deliverable, revise naming the failing check): (a) `{viewport_surface_class}` unresolved; (b) **missing/partial** — a field blank on a clerk surface, or on an owner surface whose ambition is SET; (c) **policy contradiction** — a field contradicts the class's OWN declared §8.2 posture (not a blanket "clerk = desktop"): a **desktop-only-decided** class marked mobile/tablet-supported FAILS, **and** a **mobile-first/handheld-first-decided** class forced into a desktop-only, mouse-dependent layout (dropping the mobile/offline premise) FAILS. Contradiction is measured against the class's declared posture, never a hardcoded assumption; it fails, it never warns. **WARN-ONLY** (set `{viewport_present}` = false + `{viewport_pending_policy}` = true, brief `unverified` / `pending-policy` but STILL DELIVERABLE and the handoff CONTINUES): (d) owner ambition OPEN (step 3). **HARD FAIL, cont. — (e) canonical viewport undeclared (DECIDED classes only).** A DECIDED-class `page` run fails when `{canonical_viewport}` is unset, when more than one viewport is marked canonical, or when the brief's §7 "Per-frame outputs" does not name the canonical viewport as the render target with the others explicitly marked additive. This is the artifact-labeling half of the contract: (b) asks *"is the posture recorded?"*, (e) asks *"will the deliverable actually be DRAWN and READ at that posture?"* — a brief can pass (b) with a perfect §4g table and still instruct the designer to render desktop-first, which is exactly what a hardcoded §7 line used to do. **(e) never fires on an owner class with an OPEN ambition** (no decided posture ⇒ nothing to declare) — it is not a back door around the warn-only (d) treatment. **HARD FAIL, cont. — (f) handheld-first declaration incomplete (handheld-first DECIDED classes only).** A `mobile-first`/handheld-first `page` run fails when any of the five §4c declaration fields is missing, blank, or hand-waved (`TBD` · `responsive` · `see policy`), or when §7 does not carry the B1–B4 composition instruction, **or — on a table-first surface (primary content is a list/table/queue/worklist) — when §7 does not carry the B7 IN-SURFACE composition spec** (compact header block reading as the top of the list · count + primary action loud but **inline in the worklist header**, no hero/banner/billboard-CTA/large-empty-half/separate-summary-card · secondary counts, caveats, filters and sorts collapsed into the same vertical rhythm at label weight, no chip wall · **at least one real data row visible at rest**). **The B7 clause is a distinct failure, not a restatement:** a brief can carry a flawless artifact-composition sequence and still commission a **DASHBOARD OPENER**, because every artifact-level rule is satisfied and B5 is satisfied *by construction* by a billboard CTA — the action really is the loudest element. Loudness was never the question; shape is. **B7 binds by CONTENT SHAPE, not viewport class** — it does not fire on a single-record cockpit with no list. **(e) asks *will the deliverable be drawn at the canonical viewport?*; (f) asks *does the brief specify the SHAPE of the artifact at that viewport, and of the surface inside it?*** A brief passes (e) with a flawless canonical label and still commissions a review board. **"Responsive" is not a canonical viewport** — it names a technique, and it is the phrasing that lets a generator pick desktop as the design. **(f) never fires on a desktop-only class or an OPEN owner ambition** (same false-positive guard as (e)). Contract: `shared/operator-artifact-contract.md` § Layer A. A `page` run is *fully captured* only when the gate passes clean (none of a–f); it is deliverable on (d)-only, but never on a/b/c/e/f.

This pass produces **no new frames** — it is a cross-cutting page-shell viewport contract rendered into brief §4g (like §2c / §4f), NOT a Surface-Inventory entry. Set `{viewport_present}` = true once the class resolved, the contract is complete, AND the gate passed.

**§ Enforcement tier (honest — do not overclaim).** Mechanisms 1–5 here are **PROBABILISTIC** (workflow prose the model executes; they ship via the fork sync). The **DETERMINISTIC** companion is a per-project CI/pre-commit validator on the emitted brief artifact (surface_class present · six fields complete · consistent with `design-policy.md §8` · bench-class not mobile-marked) — it is code, distributed on the separate per-project hooks/CI track, and does NOT ship via the workflow sync. Authoring this pass does not deploy a hard gate; the validator is the hard gate.

### 3g. Ledger-archetype pass — is this a LEDGER, and which view (conditional pre-filter, every page)

**Ask on any surface where `{is_finance_surface}` is true, OR whose rows are quantity/stock MOVEMENTS
(inventory in/out, receipts/issues, adjustments) even with no money on the page.** Finance-shaped is the
PRE-FILTER for asking the question — it is **not** the answer: a ledger need not carry money (quantity
movements accumulate the same way), and most finance surfaces are plain worklists. Skip entirely on a
surface with neither.

**The archetype test (the ONLY test — apply it to what the rows ARE, never to the route's name):** a
surface is a ledger when its rows are **movements over time on an account** AND a column is **meant to be
summed or accumulated**. A table that merely sorts by a date is a worklist. A route called `/lineage`,
`/ledger` or `/register` is *naming*, not evidence — cash-recovery's `/lineage` is called a ledger in its
own code header and in its policy class name, and is not one (identity links, nothing accumulates).

**1. Set `{is_ledger_surface}` and `{ledger_view}` as a STRUCTURED VALUE, never a yes/no.** Emit exactly
one of three:

| `{ledger_view}` | When | Sort |
|---|---|---|
| `not-a-ledger` | rows are not movements, or no column accumulates | per the project's default (§F most-recent-first) |
| `register` | movements over time, **no** running balance shown | most-recent-first — the default; no exception applies |
| `running-balance` | movements over time **with** a cumulative column | **oldest-first (date-ascending)** — the cumulative only builds correctly reading DOWN |

`not-a-ledger` is a **first-class, legal, common answer** — it is the expected value on most finance
surfaces and is never a failure. Do NOT phrase this to yourself as *"is this a ledger?"* and answer yes/no:
a challenge-shaped self-question produces capitulation rather than judgement. Apply the test, emit the value.

**2. Resolve whether a ledger ARCHETYPE exists in this project's policy chain — two reads, no project list.**
Set `{ledger_archetype_policy_source}` to the file that defines it, or empty:

```
# i. the project policy itself (you have already read it at §1)
grep -nE '^(##+ )?.*(Ledger (&|and) register|Ledger surfaces)' {project-root}/docs/design-policy.md
# ii. the overlay it NAMES as its parent — read the `Inherits`/`inherits:` line, follow it, and check
#     that file's frontmatter for `declares_archetypes:` (authoritative) or its own ledger section
grep -nE 'declares_archetypes|^## §M\.' <the-overlay-path-the-policy-names>
```

**Key on what the policy DECLARES, never on a hardcoded family or project list** — a third project that
starts inheriting the overlay is then picked up the day it does, with no edit here. Prefer the frontmatter
`declares_archetypes:` marker over heading-text matching; heading text drifts and a project's own section
name is project-specific (cash-recovery's is `§3a`, not `§M`).

**3. Branch on what resolved:**
- **An archetype resolved AND `{ledger_view}` ≠ `not-a-ledger`** → the view declaration is **REQUIRED** in
  the brief (rendered at §2d; gate class **(g)** in step-03). Read that policy section and carry its
  concrete rules into §2d verbatim — do not paraphrase them from memory.
- **An archetype resolved AND `{ledger_view}` = `not-a-ledger`** → render §2d with the classification only.
  One line. This is the common case and it is cheap on purpose.
- **NO archetype resolved** → set `{ledger_view}` anyway (the classification is true regardless of which
  policy a project inherits) and **record an Open Question** — *"no ledger archetype in this project's
  design-policy chain; the view is classified but no archetype rules exist to apply"* — then proceed. **Do
  NOT fabricate ledger rules, and do NOT import another project's §M text.** Same discipline as the missing
  §8 viewport policy at §3f: record it, never invent it. A brief field whose rules no consumer defines is a
  reader with no writer — the exact shape the invisibility policy exists to catch.

**§ Enforcement tier (honest — do not overclaim).** This pass is **PROBABILISTIC**: it is workflow prose
the model executes, and it ships via the fork sync. Gate class (g) in step-03 is a workflow halt (tier 3),
the same tier as classes (e)/(f). **What cannot be enforced at all: whether the rendered comp obeys the
archetype's rules — a comp is not a tool call, so no hook can block one**, the identical ceiling to the
canonical-viewport passes. The strongest additional tier is the `design-review-pr` brief check, which reads
TEXT and can only ever confirm the brief SAID the right thing. A commit-time validator on the emitted brief
is **deliberately NOT proposed here** — the existing brief gate documents its own blindness to NEW briefs
in a repo whose artifacts dir is gitignored, and duplicating that placement would ship a check that reports
green from seeing nothing.

### 4. Capture Feature Purpose

Write `{feature_purpose}`:

```
Feature: {feature_name}
Route: /path
Scope: new | redesign
Purpose: [1-2 sentences: what problem does this solve for the user?]
Data source: GET /api/endpoint → domain entities (see {data_shape})
User goals: [domain outcomes, NOT UI clicks.
  GOOD: "spot countries near deadline", "answer 'what's blocking filing today?'"
  BAD:  "click bulk-mark filed", "switch the active quarter"]
Must-support capabilities: [the jobs the operator must be able to ACCOMPLISH on this
  surface beyond the primary goals above — as outcomes, NOT UI mechanics. These are
  requirements the design must satisfy even though this brief withholds the current
  layout; name the secondary capabilities a blank-canvas redesign most easily drops.
  Set `{must_support_capabilities}` (empty only if there genuinely are none).
  GOOD: "attach the source receipt to the order", "verify each AI-extracted field
        against the source it came from", "bypass staging review for a trusted record"
  BAD:  "drag-drop zone in the right rail", "a skip-staging checkbox", "a two-pane split"]
Data volume: [typical count — "usually 10-50 items", "1,400+ records per quarter"]
```

Do NOT include "Main component", "Child components", "Current sections", "Current tabs", or "Key interactions." Do NOT phrase user goals or capabilities as UI actions. **The line between a forbidden interaction and a required capability is the arrangement, not the verb:** strip *how the current UI does it* (the control, the layout, the mechanic — "a skip-staging checkbox in the toolbar"), but keep *what the operator must be able to accomplish* (the job — "bypass staging for a trusted record"). The blank-canvas mandate forbids inheriting the *arrangement*; it does not license dropping a *capability*. A capability the brief never names is silently dropped from the redesign — the design tool cannot reinstate what it was never told to support, which is exactly how a redesign comes back "more basic" than the screen it replaced.


---

**Next — the gather continues in two focused sub-steps (split out of this file for context budget; same content, no behaviour change):**

Read fully and follow: `{project-root}/_bmad/bmm/workflows/design/design-handoff/steps/step-01b-decide.md` (§5 page mode → §5a composition → the §5b–§5c-3 analytics decision stack), then it chains to `step-01c-topology.md` (§5d topology → §6 user context → COMPLETION) and on to step-02.
