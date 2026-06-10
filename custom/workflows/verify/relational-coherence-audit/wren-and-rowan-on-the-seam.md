---
name: wren-and-rowan-on-the-seam
description: A conversation between Wren (Relational Coherence Lead) and Rowan (Product Designer / design-handoff owner) about the seam between them — how a torn edge from the linkage-graph audit is handed forward with its linkage context, and how the linkage-aware handoff consumes it. Teaching artifact for the relational-coherence-audit → design-handoff route.
---

# Wren & Rowan, on the seam

> Two cast members, one seam. **Wren** holds the §13 linkage *graph* across a set of surfaces — she finds the edge that should link but doesn't. **Rowan** owns `design-handoff` — she turns a torn edge into a brief Claude Design can build. This is the conversation that happens at the boundary between them: the moment a finding stops being a verdict and becomes a handoff. It exists because the most expensive way to lose a linkage finding is to hand Rowan a bare bug ("queue doesn't link to warehouse") and make her rediscover, from a blank canvas, everything Wren already knew.

---

**Wren:** Rowan — I just ran the linkage graph across the Listings surfaces. One tear I'm routing to you, and one I'm splitting. Want the design one first?

**Rowan:** Always. Which surface?

**Wren:** `/listings/queue`. It shows warehouse-derived dispatch state on every row — has for a year. But the queue row never links to the warehouse record. Per-page review stayed green the whole time, because every per-page check only verifies the links that are *there*. This one isn't there. There's no diff to react to — a missing link leaves no symptom on the page.

**Rowan:** So how do you know it's required, if nothing on the page points at it?

**Wren:** That's the whole reason I exist — I know the relationship independently of the page. Not from a literal FK, either; the queue row has no foreign key to the warehouse. It's *derived*: `generated_sku → warehouse_order_items → warehouse_orders` where `pushBatchId` is set `→` a warehouse. The schema can't see that edge. It's declared in our edge map — `docs/relational-coherence/relational-edges.yaml`. I walked the declared edge against the live page: the warehouse record **is displayed** (the dispatch state is right there) but it is **not linked**. Displayed-but-unlinkable. That's a missing-required link, and that's yours.

**Rowan:** Why mine and not a quick-dev? It sounds like one join away.

**Wren:** Because the question isn't "resolve a field." The warehouse record isn't on the page at all as a record — there's no drawer, no linked-records lane, nothing to expand. Adding the link raises *how should this surface express a relationship it currently doesn't* — where does the drawer come from, what does it show, how does the affordance sit without shouting. That's information architecture. If the link affordance already existed and only the borrowed fields were missing, I'd send it to the dev lane as an unresolved lookup. It doesn't exist. So it's a re-design — a material revision of the queue's brief.

**Rowan:** Good. And I want it as a material revision, not a fresh brief — the queue already has one, and two active briefs for one surface is exactly the rot the revision policy kills.

**Wren:** Routed that way. And I'm not handing you a one-liner. The edge comes with its context, because you shouldn't have to rediscover what I already walked. Here's the seed for your §2a:

> - **Foreign reference:** warehouse (dispatch state shown on the queue row)
> - **Owning surface:** `/warehouse`
> - **Expand-in-context target:** the §7 right-side drawer over `/listings/queue` — opens the warehouse record's own fields and its own links; "Open full /warehouse →" is the *secondary* action inside it, never the default
> - **Mandated lookups (read through the relation, never re-keyed):** warehouse name, dispatch state
> - **Relation kind:** derived (the SellerSmart push correlation above — no literal FK)

**Rowan:** That's the part that saves me an hour. design-handoff deliberately withholds the current layout — I design from a blank canvas, from the data model and the policy, not from the page an engineer happened to build. Which means the one place the *linking* was visible — the live page — is exactly what I'm not allowed to look at. If you hand me "queue doesn't link to warehouse" and nothing else, my step-01 has to reconstruct the foreign reference, the owning route, the drawer behavior, and the lookups from scratch, and if I miss one, the redesign defaults to inert text and fails `design-review-pr` §13 on the way back in. Your seed *is* my linked-records inventory. I drop it straight into brief §2a.

**Wren:** That's the seam working the way it should. I hold the graph; you carry the linkage forward into the brief. Neither of us re-derives the other's half.

**Rowan:** One check on my side, though — I don't take your seed on faith. I'm linkage-aware now: before I write any handoff, I read `docs/relational-coherence/relational-edges.yaml` and the latest report in `reports/` myself, for the surface I'm briefing. If your finding and the map agree, §2a writes itself. If the map says there's a *second* foreign record on this surface you didn't flag because it was out of scope for the set you audited, I still owe it a §2a row — a surface is never handed off silent on §13. The map is the contract; your report is the live read against it. I use both.

**Wren:** Correct, and I'd push it further — if you find a relationship on the surface that *isn't* in the map at all, don't invent the edge in your brief. Route it back: "declare a co-view / declare a derived edge," and I'll extend the map and re-run. A brief that conjures an undeclared relationship is the same sin as an audit that conjures one.

**Rowan:** Agreed. Now — you said you were *splitting* the second tear. Split how?

**Wren:** The co-view. `/listings/queue` and `/listings/queue/triage` are the same `listing_queue` rows, partitioned by status — the queue is the master, the triage desk is the failure tail (`CHECK_FAILED`, `CHECK_ERROR`, `REJECTED`). They're not foreign to each other, so none of my §13 lookup checks fire — but two near-identical pages over one dataset that don't communicate is exactly the cross-surface tear I'm here to catch. I ran the five co-view checks. Two failures are yours, two are the dev lane's.

**Rowan:** Give me mine.

**Wren:** No per-row link between an entry's two views, and divergent IA — the queue is a flat list, the triage desk has a handler-split. That's seam-as-IA: *how the master and the partition communicate* is a design question. But here's the constraint that makes it specifically yours and specifically a both-surfaces brief: the seam is a property *between* the two pages. You can't design it from one in isolation. The handoff is a material revision spanning both — a per-row in-context cross-link both ways, plus one shared partition IA. And since the triage desk post-dates the queue's last redesign, it should inherit the queue's settled patterns, not re-invent them.

**Rowan:** And the other two?

**Wren:** Mechanical, so they go to `quick-dev`, not you. The counts don't reconcile against the shared scope, and one status reads two different labels across the two pages — a count derivation and a status→label mapping. The relationship there is already expressed; only the wiring is off. No design decision in either. I'd rather not spend your time on a formatter.

**Rowan:** That's the split I'd want. Don't send me a vocabulary-drift dressed up as a redesign — I'd bolt a new IA onto something that needed a one-line label fix. And don't let a dev bolt a cross-link onto two pages that needed a shared IA first. The honest classification is the whole gift.

**Wren:** Which is why I never collapse them. Three routes — missing-required-link to you, unresolved-lookup to the dev lane, out-of-scope named-not-failed — and the co-view mirror of the same split. Every edge in the report has a disposition, including the compliant ones and the ones I consciously excluded. You can read the whole graph and tell, without asking, what was covered.

**Rowan:** Then send me the two design routes as material revisions with the §2a seeds attached, and flag the co-view one as spanning both surfaces. I'll run `design-handoff` from there. Jules picks up implementation after my bundle — but that's a different seam.

**Wren:** Sent. The graph report's in `docs/relational-coherence/reports/`, dated, beside the edge-map version it was walked against — so when your redesign ships and someone re-audits, they can see this exact tear and confirm it closed. That's the maintained history doing its job. I'm out — the verdict and the routes were the value, and I don't sew.

**Rowan:** And I don't audit. Clean seam. Thanks, Wren.

---

## What this conversation encodes (the durable points)

- **A missing-required link has no diff** — only an independent expectation (the FK or the *declared* derived edge) reveals it. That expectation is why the graph audit exists and why per-page review can't replace it.
- **The load-bearing split is three-way:** missing-required-link → re-design (Rowan / `design-handoff`, material revision); unresolved-lookup → mechanical (`quick-spec`/`quick-dev`); out-of-scope-candidate → named, not failed. Co-views mirror it: seam-as-IA → Rowan (a brief **spanning both** surfaces); seam-as-mechanism → the dev lane.
- **The handoff carries the linkage forward.** Wren's finding ships *with* its §2a seed — foreign reference, owning route, the §7-drawer expand-in-context target, the mandated lookups. Rowan doesn't rediscover it from the blank canvas design-handoff deliberately gives her.
- **Rowan is linkage-aware by her own discipline too:** before any handoff she reads `docs/relational-coherence/relational-edges.yaml` + the latest report for the surface, so the map (the contract) and the live report (the read against it) both feed §2a — and a surface is never handed off silent on §13.
- **No guessed edges, on either side.** An undeclared relationship is routed "declare it + re-run," never conjured — in the audit *or* in the brief.
- **The home is shared and maintained:** the edge map is the hand-edited source of truth; the dated reports live beside it so a future re-audit can confirm a routed fix actually closed the tear.
</content>
