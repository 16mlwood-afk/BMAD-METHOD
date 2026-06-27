---
name: relational-coherence-audit
description: 'Read-only audit of §13 cross-surface relational coherence across a SET of pages — the linkage GRAPH, not one page in isolation. Derives the EXPECTED edges from the app''s own schema (Drizzle FKs) plus a declared relational-edges.yaml for the derived/correlated relationships the schema doesn''t encode, then walks each edge against the live surface: is the foreign record displayed, is it a navigable §13 lookup (expand-in-context, quiet), are the mandated inline lookups resolved, does it round-trip both ways, is the identifier canonical. Separates a MISSING-REQUIRED LINK (the surface doesn''t express the relationship at all → re-design) from an UNRESOLVED LOOKUP (the link is there, the inline fields aren''t → mechanical fix) from an OUT-OF-SCOPE CANDIDATE (a schema edge the surface never displays → named, not failed). Also audits CO-VIEW siblings — two surfaces over the SAME record type, partitioned (a master view + a status-filtered partition view) — for whether they actually communicate: a per-row link between an entry''s two views (both ways), reconciling counts, a consistent handler-split IA, and one shared status vocabulary. Detect + route only — never edits.'
---

# Relational Coherence Audit Workflow

**Goal:** Given a set of related surfaces, verify that the §13 linkage *graph* between them holds — every on-screen value that **is** a record owned by another surface is a navigable lookup to that record, the inline fields it borrows are resolved (not re-keyed), the drill round-trips both ways, and the identifier reads the same everywhere. The defining move is that this workflow holds the **whole graph at once**: it derives the *expected* edges from the app's own schema and a declared edge map, so it can catch the one thing no single-page workflow ever can — a link that is **absent but required**.

**Your Role:** You are a relationship auditor, not a wiring crew. Per-page §13 enforcement already exists — `design-review-pr` fails a PR whose diff renders a foreign record as inert text; `design-handoff` now seeds a linked-records inventory into each brief. But all of that is *local*: each workflow sees one surface's own view of its relations. The policy's hardest §13 clauses are not local — "no relationship visible from one side only," "a page passes only if it coheres with **and links to** its sibling records." Those need the graph. Your job is to stand above the surface set, derive what the relationships *should* be from the schema, and report — edge by edge — where the product's relational fabric is torn. You never sew it back; you route each tear to the lane that owns the needle.

**Key Insight — a missing link leaves no diff.** Every other §13 check is triggered by something *present*: a rendered value, a changed line, a DOM node. A link that *should* exist but doesn't produces nothing to react to — no failing assertion, no diff, no symptom on the page. The Listing Queue can show warehouse-derived dispatch state for a year and never link to the warehouse record, and every per-page check stays green, because each one only verifies the links that *are* there. The only way to see the absence is to know the relationship independently — from the schema FK, or from a declared semantic edge — and then look at the surface and find the link missing. That independent expectation is the entire reason this workflow exists. Without it, "all links resolve" and "all required links exist" are silently treated as the same claim, and they are not.

**The load-bearing distinction — missing-required-link vs unresolved-lookup vs out-of-scope-candidate.** Three findings look adjacent and route to opposite places; conflating them is the whole failure mode:

- **Missing-required link** — the surface *displays* a foreign record but expresses the relationship as inert text, or doesn't express it at all (no drawer, no linked-records lane). The fix is an **information-architecture** question — *how should this surface link to that record* — so it routes to **re-design** (`design-handoff` material revision).
- **Unresolved lookup** — the link is there and works, but the inline fields §13 says it should borrow (a supplier's name, an order's buy-cost) aren't resolved from the canonical record. The relationship is expressed; only the data pull is missing. That's **mechanical** → `quick-spec` / `quick-dev`.
- **Out-of-scope candidate** — the schema says an edge *could* exist, but the surface never puts that foreign value on screen. §13 only governs records that **appear** on a surface. This is **not a failure** — it's named so the reader knows it was considered and consciously excluded, never silently dropped.

Mislabel a missing-required link as an unresolved lookup and you hand a designer's problem to a `quick-dev` that can only bolt a link onto a value the page was never meant to show. Mislabel an out-of-scope candidate as a missing link and you flood the report with false failures for every internal FK the operator never sees. Producing those three verdicts honestly is the value.

**The second relation kind — co-view (same record, two surfaces).** Everything above is about **foreign-record** edges: record A on a surface should link to record B *owned by another surface*. There is a second relation the FK graph cannot see and §13's foreign-record clause does not reach: **two surfaces that render the SAME record type**, partitioned (usually by status) into a **master** view (the whole set) and one or more **partition** views (a filtered slice of the same rows). The Listing Queue (all statuses) and the Listing Upload Triage desk (the `CHECK_FAILED`/`CHECK_ERROR`/`REJECTED` failure tail) are the canonical pair — the same `listing_queue` rows, split. They are not *foreign* to each other, so none of the §13 lookup checks fire — yet two near-identical pages over one dataset that **don't communicate** is exactly the cross-surface tear this workflow exists to catch. The failure shape: no per-row link between an entry's two views, counts that don't reconcile, a handler-split IA on one and a flat list on the other, two names for one status. A co-view, like a derived edge, is **schema-invisible** — it must be **declared** in `relational-edges.yaml` (a `co_views:` entry, not an `edges:` entry) or the audit can't check it. Its checks are the five **CO-VIEW CHECKS (CV1–CV5)** in step-03, not the §13 lookup checks.

---

## Two evidence sources — and why neither alone is enough

This is the cross-surface analogue of `webhook-contract-check`: a contract verified across a boundary, from two sides that must agree. Here the "boundary" is each relational **edge** between two surfaces, and the two sides are:

| Side | Source | Answers |
|---|---|---|
| **Expected** | Drizzle schema FKs + the declared `relational-edges.yaml` | *Which records relate to which?* — the edges that COULD require a §13 link |
| **Actual** | Live source scan + DOM render of each surface (the `design-review-pr` source/DOM machinery) | *Does the surface DISPLAY this foreign record, and if so, is it a working §13 lookup?* |

The schema alone over-claims: not every FK is a relationship the operator ever sees — plenty are internal plumbing. The page alone under-claims: it can only show you the links it already has, never the one it's missing. **The finding lives in the join** — a schema/declared edge whose foreign record the surface *displays* but does not *link*. Decide "displayed?" from the page, "required?" from the schema, and only a value that is both is in scope. This is the same honesty the content-lane cede teaches: name the dimension you cannot settle from one evidence source, and go get the other — never assert a violation from the schema when only the DOM can confirm the value is even on screen.

---

## Sibling workflows — what relational-coherence-audit is NOT

| | This workflow | The sibling it's confused with |
|---|---|---|
| **vs `design-review-pr`** | Standing/periodic audit over a SET of surfaces; evidence = schema + edge map + N rendered pages; catches **absent** links | PR-time, single-diff §13 lane; evidence = the diff; verifies the links **present** in the change resolve. It cannot see a surface that isn't in the diff, nor a link that was never added. |
| **vs `design-handoff`** | Consumes many surfaces, emits findings + routes (one of which is *back into* design-handoff) | Produces ONE brief for ONE surface from a blank canvas. Opposite direction. This workflow is a *producer* of handoff work, not a peer. |
| **vs `data-quality-audit`** | Audits the relational **graph** between surfaces — are records linked and lookups resolved | Audits the **values** of one controlled-vocabulary dimension — are they canonical. Same posture (read-only, derive-from-the-app's-own-source, classify + route), different object. |
| **vs `trace-flow`** | Breadth across surfaces — the edge set and its §13 status | Depth down one pipeline — does *this* field flow from DB to one UI. trace-flow proves a wire exists; this proves the right wires exist across the product. |
| **vs `wire-check`** | Detects, never repairs | Repairs intra-app wires. A missing lookup this workflow finds may route *to* `wire-check`/`quick-dev`; the repair is theirs. |

If you want one page's links checked at PR time, that's `design-review-pr`. If you want the *graph* across the Listings/Orders/Catalog/Warehouse surfaces checked for holes, that's this workflow — and it hands you routed findings, not edits.

---

## CRITICAL RULES

- **Read-only. Never edits source or data.** The audit reads the schema, an edge map, and rendered surfaces. Every repair — a new link, a resolved lookup, an aligned formatter, a re-designed surface — belongs to the routed lane, in its own worktree, under its own rules. A run that "just added the obvious link while I was there" is not this workflow.
- **Expectation comes from the app's own sources — never an invented relationship list.** The expected graph is the Drizzle FKs plus the project's declared `relational-edges.yaml`. Do not hand-author edges in your head: an FK is authoritative; a *derived* edge (a correlated `EXISTS`, a join through a link table — e.g. the SellerSmart push that ties a listing to a warehouse with no literal FK) is real but invisible to the schema, so it must be **declared** in the edge map. If a derived relationship has no entry, it cannot be audited — say so and route the gap to "add it to `relational-edges.yaml`," don't guess it into existence.
- **"Displayed?" is decided from the page, not the schema.** A schema edge is a *candidate*. It enters scope only when the foreign record actually appears on the surface (source scan / DOM). Asserting a missing-link failure from the schema alone — without confirming the value is even on screen — is the false-positive flood this workflow is built to avoid.
- **The link mechanism is expand-in-context, not navigate-away (§13 / policy v6).** The §13 affordance opens the foreign record in the project's §7 right-side drawer *over* the current surface, carrying its fields as lookups; the full sibling page is a *secondary* "Open full {sibling} →" action, not the primary drill. Test the drawer-expand affordance and its quiet styling (§4 — never a button, CTA, or colored pill). A reference that navigates straight away, or that's styled as a CTA, fails even if it "links."
- **Bidirectional or it's a finding.** §13 forbids a relationship traversable from one side only. Every in-scope edge is checked both ways with a round-trip back; a dead-end drill or a B-from-A-but-not-A-from-B link is a defect, not a nicety.
- **Every edge gets an explicit disposition — including the benign and the out-of-scope.** Output a per-edge table where each row is classified AND routed (or explicitly marked `compliant` / `out-of-scope-candidate` with the reason). Nothing is silently dropped. An edge that appears in the report on neither the compliant nor the failing list is a silent-partial-implementation defect.
- **Missing-required-link vs unresolved-lookup vs out-of-scope-candidate is the load-bearing classification.** Resolve every non-compliant edge to exactly one. They route to opposite lanes (re-design vs mechanical vs nowhere).
- **Detect and route — do not fix.** This workflow stops at "here is the edge, its §13 verdict, and where the fix goes." Re-design routes to `design-handoff`; mechanical fixes route to `quick-spec`/`quick-dev`; a missing declared edge routes to "extend `relational-edges.yaml`."
- **Co-views are a declared relation, never inferred — and never mis-flagged as a dual-owner defect.** A `co_views:` entry is the only thing that puts a same-record sibling pair in scope (no FK produces it). The single-owner premise of the ownership map (step-01) has an explicit carve-out for it: a co-viewed record legitimately has 2+ surfaces — the declared `master` owns it, the `partition` views are co-viewers, NOT rival owners. An undeclared same-record sibling you happen to notice is routed "declare a `co_view`," never conjured into a finding from a guess. Co-view findings get their own disposition rows alongside the edge rows — never folded away.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- Each step loads fresh to combat "lost in the middle"
- State persists via variables: `{surface_set}`, `{ownership_map}`, `{schema_edges}`, `{declared_edges}`, `{co_views}`, `{expected_graph}`, `{walked}`, `{dispositions}`, `{db_access}`, `{server_live}`, `{baseline_commit}`
- Sequential progression through 4 phases: resolve the surface set + ownership map → derive the expected graph (foreign-record edges + co-view siblings) → walk each edge/co-view against the live surface → classify + route

---

## INITIALIZATION

### Configuration Loading

Load config from `{project-root}/_bmad/bmm/config.yaml` and resolve:

- `user_name`, `communication_language`
- `implementation_artifacts`
- `project_knowledge` (the project's `docs/` — where the design policy lives)
- `relational_coherence_home` = `{project_knowledge}/relational-coherence` — the **dedicated, maintained home** for this audit's two long-lived files: the declared edge map (`relational-edges.yaml`, hand-maintained source of truth) and the dated reports (`reports/`). Both are git-tracked project knowledge, not transient artifacts. (See "Declared Edge Map" below.)
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime

### Autonomous Mode Override

If `autonomous_mode` is `true` in config, the following rules apply to ALL steps:

- **Never halt, pause, or wait for user input** for *decision* questions — which surface to walk first, which rendered value resolves to which record, how to phrase a routing slip. Choose the most productive option and proceed.
- **Complete the full workflow end-to-end** — derive every expected edge, walk every in-scope edge, classify every edge, and emit a routing slip for every finding.

> **Scope — three things `autonomous_mode` does NOT cover:** the **grounding gate** below, the **no-edit** rule, and the **no-guessed-edges** rule. Autonomous mode buys decision autonomy (which surface, which value, which phrasing), not intent autonomy (inventing the surface set, or fabricating a derived relationship that isn't in the schema or the edge map). If the input can't be grounded to a surface set, halt regardless of the flag. If a derived edge isn't declared, route "declare it," don't conjure it. If a fix is needed, route it — don't apply it.

### Input & Grounding Gate

**The input is plain English — routes are an optional shorthand, never a requirement.** Ask it the way you'd ask a colleague: *"is the listing queue properly linked to its records?"*, *"check the linking between listings and the warehouse"*, *"audit the inbound supply-chain pages"*, *"does /orders link everything it should?"*. Step-01 pulls the verbs and nouns out of that sentence and resolves them — a page label, a domain area, a record type, or a raw route are all valid handles. The user is **not** expected to type a command form or hand over two routes.

What the sentence resolves to (step-01 §0–§1):

- **A surface set** — routes named outright, or a domain area / nav label ("the Listings surfaces") resolved via `nav-config` / the App Router tree. The default for the on-demand "evaluate these pages together" use.
- **A single anchor** — one page or one record named ("the listing queue", "warehouse"). Expanded to the surface set of every record it relates to (its schema neighbours), because a single page's §13 coherence is only judgeable against its siblings.
- **A full sweep** — "audit the whole product's relational coherence." Every operational route in `nav-config` that the schema says owns or references a shared record.

**Under-specified ≠ ungroundable.** If the ask is friendly but vague ("check our linking", "is this page linked right?"), step-01 §1a does **not** halt — it derives 2–4 candidate scopes from the schema neighbours / nav clusters and **offers them as a recommendation menu** (interactive) or picks the highest-leverage default and states it (autonomous). Offering grounded candidates is not intent autonomy; guessing one and running it silently would be.

**Before exiting INITIALIZATION you must be able to state, in plain English: "audit the §13 linkage graph among {named surfaces}" — reached either from the ask or from the user's pick off the §1a offer.**

**Hard HALT — last resort only:** when the input is genuinely ungroundable *and* the offer can't help — nothing in the sentence names or implies any surface and the nav tree yields no candidate to even offer, or the only target is a true leaf that shares no records with anything (auth, settings, a standalone upload — no graph to audit). A vague-but-anchorable ask is handled by the §1a offer, never by a halt.

**HALT response** (same shape as the `data-quality-audit` / `webhook-contract-check` halt — what's wrong, which gate, what clears it):

1. State plainly: "I can't ground or even offer a surface set — nothing here names or implies a surface that shares records with another, and the graph is the unit of audit."
2. Name what you *can* see (e.g., "the nav tree is unreadable" / "the only thing named is a leaf settings page").
3. Ask for the smallest unblock: any page name, area, or record to anchor from — *not* a route list or command form.

This last-resort halt fires regardless of `autonomous_mode`; the §1a offer (interactive) / stated-default (autonomous) handles everything short of it.

### No Worktree — Read-Only Across the Graph

**This workflow enters no worktree and edits no code or data.** It reads the schema, the edge map, and rendered surfaces, then reports and routes. The repairs happen later, per finding, when the routed lane (`design-handoff` → design build, or `quick-spec` → `quick-dev`) runs in its own worktree under its own rules. The deliverable is a graph report and routing slips, not edits.

### Read-Only Data / Render Access

The "actual" side needs each surface rendered with real data to decide *displayed?* and *linked?*. Resolve the project's render path from its `CLAUDE.md` — the local isolated stack where one exists, or the read-only production proxy for source/DOM inspection — without hardcoding credentials. **Also check the project's `docs/deployment.md` for a read-only DB-access note** — a public read-only proxy / `DATABASE_PUBLIC_URL`-style connection an agent may `SELECT` against for the actual-side counts, **distinct from the internal `DATABASE_URL` (often a `*.railway.internal` host that only resolves inside the platform) and explicitly OUTSIDE the `railway up` / deploy footgun**. Use it only for read-only audit queries. Where a project forbids running the app AND documents no reachable read-only path, fall back to **static source scan** (the same machinery `design-review-pr` step-02 uses) and record `{server_live} = false`. Store the resolved access as `{db_access}`. **When `{server_live} = false`, the actual side did not run — step-04's report MUST open with the loud structural-only banner: a decision-grade count the user asked for is NOT a verdict in a structural-only run, it ships as a hand-off query.**

### Declared Edge Map — and its maintained home

This audit produces and consumes two long-lived files. They get a **dedicated home** at `{relational_coherence_home}` (`docs/relational-coherence/`) so the thing you *maintain* (the edge map) and the thing you *accumulate* (the reports) live together, version-controlled, and never rot loose in `implementation-artifacts`:

```
docs/relational-coherence/
  README.md                 # what this home is + the maintenance discipline
  relational-edges.yaml     # THE maintained edge + co-view map — hand-edited source of truth
  reports/
    relational-coherence-audit-{scope-slug}-{date}.md   # dated audit history
```

- **`relational-edges.yaml`** is the hand-maintained source of truth for the derived/correlated relationships the schema can't express (the SellerSmart warehouse push, link-table joins) **and** the same-record `co_views:`. It is **maintained**, not generated: when a new shared record or sibling view ships, the operator extends this file (the audit routes "declare it," never conjures it). If it's absent, step-02 proceeds with FK-only edges and raises a P1 "no declared edge map" finding, because an FK-only audit silently misses exactly the decision-relevant relationships. The template and field schema live beside this workflow at `relational-edges.template.yaml`.
- **`reports/`** holds the dated audit reports — a maintained history beside the map version they were generated against, so a reader can see "as of this edge map, here is what cohered and what was torn." `docs/` is deploy-irrelevant under the BMAD deploy contract, so storing reports here never triggers a deploy.

**Legacy location:** earlier runs read the flat `{project_knowledge}/relational-edges.yaml`. Step-02 still falls back to it if the home is empty, and routes "move it into `relational-coherence/`." New work uses the home.

**Front door:** the human-facing way to run this audit is **Wren — Relational Coherence Lead** (`/bmad:bmm:agents:relational-coherence-lead`), the cast member who owns the linkage graph (sibling to Vera, the data-integrity lead). Wren runs this workflow, maintains the home above, and routes torn edges — re-design ones to **Rowan** (the design-handoff owner), mechanical ones to `quick-spec`/`quick-dev`. A power user can still invoke `/bmad:bmm:workflows:relational-coherence-audit` directly.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/verify/relational-coherence-audit`
- `relational_coherence_home` = `{project_knowledge}/relational-coherence` — maintained edge map + `reports/` (see "Declared Edge Map — and its maintained home")

### Baseline Commit

Capture `{baseline_commit}` = `git rev-parse HEAD` at workflow start — for reference in the report only. Nothing in this workflow commits.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/verify/relational-coherence-audit/steps/step-01-resolve-surfaces.md` to begin the workflow.
