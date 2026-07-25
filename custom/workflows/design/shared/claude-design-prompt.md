# Claude Design Enhancement Prompt

Single source of truth for the **structure of a focused Claude Design paste prompt** — the artifact emitted when a *design-shaped* change to an existing surface should be authored in Claude Design rather than written as a code spec. Referenced by `design-elevation` (step-04 §3a) and `maintenance-triage` (step-03, design lane). Any future workflow that needs to hand a design-shaped change to Claude Design should reference this file rather than re-enumerate the structure.

## Why this file exists

Two `contract-dimension-gap` fixes (design-elevation `657913cd`, maintenance-triage `83c9355e`) added the same new route: *a design-shaped in-surface change goes to a Claude Design paste prompt, not to quick-spec/quick-dev.* The prompt's structure was duplicated as prose in both step files. This is the consolidation — one place defines what the prompt contains and how it is saved, so a fix to the format does not have to be made twice (and silently drift).

## What this prompt IS — and is NOT

A Claude Design enhancement prompt is a **focused, brief-descended** paste prompt that asks Claude Design to deepen ONE interaction on an existing surface, with everything else held constant.

- It is **NOT a full re-brief.** A change to *what the surface is for* (a new view, a reframed primary action, new data) is an intent-change → run `design-handoff`, which supersedes the brief per `brief-revision-policy.md`. This prompt is for changes where the brief's stated job is **unchanged**.
- It is **NOT a code spec.** The deliverable is a visual + interaction design authored in Claude Design. If the change is wiring/logic with no new pixels, it is code-shaped → quick-spec/quick-dev, not this.
- It is a **brief descendant, not a brief revision.** Because intent is unchanged, the prompt does NOT carry a Block A provenance header, is NOT subject to the 6 intake checks, and does NOT supersede anything. It *references* the surface's active brief (if one exists) so the lineage is traceable, but it does not modify it.

## Required structure (emit in this order)

1. **Connect line** — the repo + branch to connect to. Read the exact URL from the surface's design brief "For Claude Design" block when one exists.
2. **Files to read first** — the actual component(s)/route of the surface (its `built_surface_refs`), the relevant derivation/helper, the design brief (if any), and `docs/design-policy.md`.
3. **Keep-everything-else-as-is guard** — name explicitly what must NOT be redesigned, so the pass stays focused on the one enhancement.
4. **The change** — the precise interaction being deepened, grounded in the real surface (never an invented affordance), and the core-job facet it serves.
5. **Sibling pattern to borrow (optional, when one exists)** — name the sibling surface and the part to mirror (the coherence lens). Pair it with a **grounding caveat**: borrow the *layout / interaction grammar*, not mismatched *data semantics* — copying a sibling's content model when the data differs is the failure this caveat prevents.
6. **Policy constraints** — the hard constraints from `docs/design-policy.md` that apply (pill shape / 4-tone, drawer pattern, accent/mono rules, named anti-defaults), so Claude Design stays conformant.
7. **Artifact shape — REQUIRED when the surface's class is handheld-first / mobile-primary / phone-canonical.** Composition is not the generator's to choose; leaving it unspecified is what produces a **review board**. Carry these three verbatim in spirit (contract + golden cases: `operator-artifact-contract.md` B1–B6):
   - **Generate the canonical phone surface FIRST and structure the whole artifact around it** — first, largest, alone above the fold. It is the deliverable; everything else is subordinate.
   - **Do NOT default to a symmetric row of comps.** A phone/tablet/desktop board is the wrong shape here even when the phone is leftmost and correctly labelled. Additive renders go under one "Additive verification viewports" heading, after and smaller.
   - **Do NOT let variant states become separate mini-products.** Draw each as a degraded state OF the canonical surface — same skeleton, same chrome, same primary-action position, one changed region — in a strip beneath it.
   Plus: rationale and specs come LAST (never opening the artifact, never interleaved comp-by-comp), the primary action and next-step loop outrank every heading and caption inside the canonical render, and on-surface copy stays short and imperative with long-form explanation relocated to the notes block. On a desktop-only or ambition-OPEN surface, omit this item entirely — it does not apply.

8. **In-surface composition — REQUIRED when the surface is table-first (its primary content is a list, table, queue, or worklist).** Item 7 governs how the ARTIFACT is arranged; this governs how the SURFACE itself is composed, and it is a separate instruction because a bundle can satisfy every rule in item 7 and still open with a generic app hero (contract: `operator-artifact-contract.md` **B7**, checked at review as **C5**). Carry verbatim in spirit:
   - **Compose the canonical render as a COMPRESSED OPERATIONAL STACK — a compact header block, then data, immediately.** The header shares the worklist's grid and vertical rhythm and reads as the **top of the list, not a band above it**. Not a banner, hero, opener card, or summary card.
   - **The loud count and the primary action may dominate — but only INLINE within the worklist header.** No large empty half opposite them, no billboard CTA row of their own, no distinct background/border/elevation making the header its own card. Exactly ONE element carries display weight: the count and its action read as a single unit.
   - **Collapse secondary counts, caveats, filters and sort controls into the same vertical rhythm** at label weight. **No chip wall** — no wrapping grid of pills, status chips, or metric tiles as an opener band.
   - **At least one real data row must be visible at rest**, without scrolling, at the canonical viewport.
   **"Make the action loud" means loud WITHIN the header — never "give the action its own billboard."** The failure shape is named **DASHBOARD OPENER**, and it is rejected at review even when every required element is present. On a single-record cockpit with no list, or a desktop-only/ambition-OPEN surface, omit this item.

## Save + emit rules

- **Save** the prompt body to `{implementation_artifacts}/claude-design-prompt-{surface-slug}-{enhancement-slug}.md` so it is copy-pasteable, and surface it inline in the calling workflow's summary.
- **Always emit; never invoke.** Claude Design is a human-in-the-loop external tool. The workflow's deliverable is the prompt — emit and save it regardless of `autonomous_mode`. Do not attempt to run Claude Design from the workflow.
- **Settled surface that "should do more"** → prefer routing through `design-elevation`, which formalizes this prompt with leverage-ranking and provenance, rather than emitting a bare prompt.
