---
name: 'step-01-audit'
description: 'Audit the live page — read DOM, measure, find source + peers, compare, deliver the review.'

workflow_path: '{project-root}/_bmad/bmm/workflows/design/design-review'
thisStepFile: './step-01-audit.md'
---

# Step 1: Audit

**Goal:** Produce the design review deliverable described in `workflow.md`. No implementation.

---

## AVAILABLE STATE

- `{target_url}` — URL under review
- `{tab_id}` — Chrome tab ID
- `{brand_identity}` — Project brand identity (if loaded). When present, evaluate against its specific typography, colors, component patterns, and hard failures instead of generic design-standards.md.
- `{output_mode}` — `"interactive"` (default) or `"artifact"`. When `"artifact"`, step 7 below writes a structured screen-review file in addition to the chat output.

---

## EXECUTION SEQUENCE

### 1. Resolve Target

- If the user specified a URL: store as `{target_url}`.
- Otherwise: call `mcp__claude-in-chrome__tabs_context_mcp` and use the URL of the active tab. Store the tab ID as `{tab_id}`.

### 1.5. Source-vs-Deployed Drift Gate (pre-flight)

Before reading the page in §2, check whether the source tree the audit will compare against is ahead of what's deployed. If the live page (Chrome) shows the deployed version but the source on disk has uncommitted or unmerged work, the audit will flag violations against the deployed version that may already be fixed in unshipped code.

**Peek-ahead source locate.** Pick the most distinctive visible string you can identify from the user's input — the target slug, the page title from `{target_url}`'s path, a feature name in the user's prompt. `grep -l` that string under `src/` to find the candidate component file. Capture as `{candidate_component_path}` (formalized in §4).

**Drift checks** (run all three; surface anything that fires):

```bash
# 1. Is the candidate component modified or untracked locally?
git status --porcelain {candidate_component_path}

# 2. Recent commits on the component vs the current production deploy:
git log --oneline -5 {candidate_component_path}

# 3. Local main vs remote main (does origin/main have newer commits the local dev hasn't pulled, or vice versa?):
git fetch origin main 2>/dev/null
git rev-list --left-right --count HEAD...origin/main
```

**Interpretation:**

- **Check 1 non-empty** → the source has uncommitted changes. The live page may not reflect these. Surface: *"`{candidate_component_path}` has uncommitted changes locally — Chrome may be showing a different state than the source the audit will read."*
- **Check 2 most-recent commit timestamp is < 48h old AND `git log origin/main` shows it not yet pushed** → recent unshipped work. Surface: *"`{candidate_component_path}` was last modified locally at `<timestamp>` and is not yet pushed to origin/main. The live page may show pre-edit state."*
- **Check 3 shows local ahead of origin/main** → the live deployed prod is behind local main. Surface: *"Local `main` is `<N>` commits ahead of `origin/main`. If the live page being audited is deployed prod, some violations may already be resolved in unshipped commits."*

**What to do on drift:**

- If `autonomous_mode: true` AND any drift is detected: proceed with the audit BUT add a `source_state_caveat` line to the artifact's `measurement_caveat` block (see §3 / `measurement_method`) naming the drift. The audit still emits — downstream consumers see the caveat and can decide whether to defer the brief until shipped state stabilises.
- If `autonomous_mode: false` AND any drift is detected: halt and surface the diagnostic. Ask the user: "Audit deployed live state, audit local source, or wait for the local changes to ship?" Do NOT silently pick one.
- If no drift fires: proceed to §2 with no caveat addition.

This gate does NOT block the audit when the user is auditing a known dev-only state (e.g., "review this WIP page on my branch") — drift is the expected condition there. The gate's job is to surface drift, not to refuse to run.

### 1.6. Brief structural-contract check (frame coverage, shell/role, station-vs-dashboard)

The independent live-page net for the bundle→implement seam: even when `design-synthesize` and `design-implement` both passed a non-conformant design through, the live page is audited against the brief's STRUCTURAL contract here, and a structural miss is a **blocking** finding (it gates PR approval), not a nit.

**Resolve the brief.** Match `{target_url}`'s route / slug against the briefs in `{implementation_artifacts}` (same `target_slug` resolution `design-implement` uses). If **no brief** matches, record `brief_contract: none — structural conformance unaudited (UNVERIFIED — no captured contract)` and continue — never infer a contract. If a brief matches, read its Block B `frames`, `shell_role`, and `composition` (`brief-revision-policy.md` §2) and check the LIVE page (same dimension order as the `design-implement` step-01 §SHARED.1b gate):

1. **Frame coverage** — every `frames` id must be reachable / discoverable on the live surface (a present region in default state, or reachable in-session for an in-flow frame). A frame the live page never exposes → **blocking** (designed-but-unbuilt).
2. **Shell / role** — when `shell_role` is present: the live page must render `required_chrome` and must NOT render `forbidden_chrome` (e.g. the owner global nav on a `(clerk)` surface). Forbidden chrome present → **blocking**; the fix is scoping the ancestor shell to its role, not a component tweak.
3. **Station vs dashboard** — when `composition` is a non-default key (a `recommended-alt` station/stream/verify, e.g. `scanner-terminal`): the live page must express that **job loop** (e.g. scan → feedback → tally → close) as the dominant structure — NOT a centered hero card in dead space, NOT a generic dashboard/landing surface. "A dashboard where the brief said station" is a **Tier-1 / blocking** violation: cite `Brief §<N> composition: {composition}` and the policy composition rule. This is the exact receive-station failure — its whole point is to be caught here if it slipped the upstream gates.
4. **Live-process behavioral contract** — ONLY when the matched brief carries a **§2c Runtime behavior contract** (equivalently: `frames` contains `{primary}--{state}` state-variant ids). This is the RECEIVER for the runtime cede: design-handoff captures the contract and design-implement compares static frames, but behavior verification was explicitly ceded here (`design-implement` step-03 §2e pattern) — a cede with no receiver silently drops. Three sub-checks against the LIVE surface:
   - **States render.** Drive the surface into each operator-distinct lifecycle state named by the state-variant frames (start a run, pause it, let items complete/fail as the session allows). A state that cannot be reached in-session (e.g. `partial-failure` needs a real failing item) is recorded `UNVERIFIED(state: <name> — <why unreachable>)` — disclosed, never skipped silently, never marked pass.
   - **Verbs reachable where legal.** Every §2c control verb (pause / resume / cancel / retry / …) is reachable in exactly the states the §2c table marks it legal. A verb missing in a legal state, or offered in a state where §2c says it is illegal, is **blocking** — cite `Brief §2c control verbs`.
   - **Staleness within budget.** While the surface is in a running state, observe its actual update cadence and compare against the §2c staleness budget. Observed staleness beyond budget is **blocking** (the design's liveness claim is broken) — cite `Brief §2c staleness budget: <value>`.

   When the brief has no §2c section, this dimension is `n/a` — the contract genuinely doesn't exist, which is distinct from `unaudited`.

Record results into the audit's findings with `blocking` severity for any miss; on `no_brief` mark dimensions 1–3 `unaudited` (UNVERIFIED) rather than `pass` (dimension 4 is `n/a` without a §2c brief). This dimension is what makes "looks fine" insufficient — a page can be visually clean and still be the wrong surface for the job the brief specified, or a process console whose paused state, cancel verb, or liveness claim was never actually exercised.

### 2. Read the Page

- Call `mcp__claude-in-chrome__read_page` on `{tab_id}`. This returns visible text + DOM structure — both are inputs to the compare step.

### 3. Measure (evidence, not impressions)

**Mode A — `chrome-live` (preferred).** Call `mcp__claude-in-chrome__javascript_tool` to collect concrete measurements. At minimum capture:

- **Top 3 visual elements:** `fontSize`, `fontWeight`, `color` (computed styles) of the three visually heaviest elements on the page (largest headings, primary CTAs, big numbers).
- **Scroll containers:** `scrollWidth` vs `clientWidth` and `scrollHeight` vs `clientHeight` for every element with `overflow: auto|scroll`. Flag any where scroll dimension exceeds client dimension — that's horizontal or vertical overflow.
- **Counts:** cards, sections, KPI tiles, table rows visible.
- **Duplicated data:** any field/value that appears in 2+ distinct regions on the page (e.g., the order ID rendered in both the header and a context card).

**Mode B — `source-derived` (fallback when Chrome MCP unavailable).** Derive the same shape of evidence from source + screenshots:

- **Top 3 visual elements:** identify the three heaviest from the screenshot, then `grep` source for the matching component(s) and read the Tailwind classes directly. Record the class string in place of computed style (e.g., `text-[22px] font-semibold tracking-[-0.015em]` instead of `fontSize: "22px", fontWeight: "600"`).
- **Scroll containers:** `grep` source for `overflow-auto`, `overflow-x-auto`, `overflow-y-auto`, `overflow-scroll`. Flag any container holding a wide grid (`grid-cols-[...]` summing > 1200px) or a long list. No live `scrollWidth` available — note that under `measurement_caveat`.
- **Counts:** count from source — `<th>` elements, `.map(...)` row templates, conditional sections — and cross-check against the screenshot. Sprint-mode `grep` patterns: `'<th'`, `'<section'`, `'rounded-(lg|xl).*border'`.
- **Duplicated data:** scan the screenshot for repeated values (the same order ID, the same supplier name) and the source for repeated field references in distinct regions.

**Mode C — `screenshot-only` (weakest).** No source-grep. Measurements collapse to "what can be observed in the image":
- Top 3 visual elements: described by relative size and position, not by class. Use the words "title", "primary CTA", "biggest number on the page" rather than `text-[22px]`.
- Scroll containers: not assessable — note "not measurable in screenshot-only mode" under `measurement_caveat`.
- Counts: counted from the screenshot directly.
- Duplicated data: visible-text comparison only.

**For Modes B and C:** the artifact's `measurement_method` field records which mode was used; the `measurement_caveat` field records what specifically was NOT measured live. Downstream consumers (notably `design-handoff` refine-screen) read both fields and may treat the artifact's edge-state list and peer-steal list as advisory rather than authoritative when the mode is not `chrome-live`.

Example harvest script:

```javascript
(() => {
  const topVisuals = [
    ...document.querySelectorAll('h1, h2, [class*="text-3xl"], [class*="text-2xl"], [class*="text-xl"], button[class*="primary"]'),
  ]
    .slice(0, 3)
    .map((el) => {
      const s = getComputedStyle(el);
      return {
        tag: el.tagName,
        text: el.textContent.trim().slice(0, 60),
        fontSize: s.fontSize,
        fontWeight: s.fontWeight,
        color: s.color,
      };
    });

  const scrollers = [...document.querySelectorAll('*')]
    .filter((el) => {
      const s = getComputedStyle(el);
      return /auto|scroll/.test(`${s.overflow} ${s.overflowX} ${s.overflowY}`);
    })
    .filter((el) => el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight)
    .slice(0, 8)
    .map((el) => ({
      cls: (el.className.toString() || el.tagName).slice(0, 80),
      scrollW: el.scrollWidth,
      clientW: el.clientWidth,
      scrollH: el.scrollHeight,
      clientH: el.clientHeight,
    }));

  const cards = document.querySelectorAll('[class*="rounded-lg"][class*="border"], [class*="rounded-xl"][class*="border"]').length;
  const sections = document.querySelectorAll('section, [role="region"]').length;
  const tableRows = document.querySelectorAll('tbody tr, [role="row"]').length;

  return JSON.stringify({ topVisuals, scrollers, cards, sections, tableRows }, null, 2);
})();
```

Scan the rendered text (from step 2) for repeated values — note which ones appear in multiple regions. Duplicated data is a density red flag.

**Identifier rendering (all modes — feeds the §13a check in §5).** Separately from duplicated-data, capture *how each canonical-identifier class is formatted* wherever it appears. For each class present — supplier, buy/sell marketplace, ASIN / SKU / product code, order / shipment / batch number, currency, date — record the literal rendered string(s) from the visible text: e.g. supplier `amazon` in the table but `Amazon` in a header; `marketplaceBuy` rendered `AMAZON_ES` (raw enum) while `marketplaceSell` renders `Amazon UK`. This is plain rendered text, so it is capturable in every mode (`chrome-live`, `source-derived`, `screenshot-only`) — there is no degraded-mode excuse to skip it. Store the per-class rendered forms for the §5 consistency compare.

### 4. Locate Source + Peers

- Pick a distinctive visible string from the page (a unique heading, an uncommon label, a specific button label).
- `grep` that string in the project's `src/` directory to find the component that owns the page. Store the absolute path as `{component_path}` and read the file fully.
- Identify 2–3 peer detail/summary views to use as the quality bar. Good candidates:
  - Other detail pages in the same folder (e.g., `order-detail.tsx`, `staged-order-review-detail.tsx`).
  - Summary strips referenced as the visual benchmark (e.g., `pipeline-summary-strip.tsx`).
  - Sibling pages the user has previously praised or used as the "ship this kind of thing" example.
- Store paths as `{peer_paths}` and read each fully.

### 5. Compare

With measurements + source in hand, compare the page under review against the peers AND the brand identity (if loaded). Focus on:

- **Hierarchy:** Do the top 3 visually heaviest elements match the page's primary decision? Or is weight spent on low-value chrome (breadcrumbs, meta, labels)?
- **Information architecture:** Are related concepts grouped? Is any data duplicated across regions (from step 3)? Is there a region that answers no user question?
- **Identifier & value formatting (§13a — canonical identifier):** Using the per-class rendered forms captured in step 3, does each canonical-identifier class render in ONE consistent casing / label form everywhere it appears — across cells, columns, and the page↔drawer boundary? Policy §13 ("Canonical identifier") requires a record to *"read, format … the same way everywhere … do not relabel, reformat, or re-key the same record per surface."* Flag (a) **inconsistency** — the same class rendered two ways (`amazon` vs `Amazon`; `AMAZON_ES` vs `Amazon UK`); and (b) **raw-enum / code leakage** — a SCREAMING_SNAKE or internal code (`AMAZON_ES`) rendered verbatim where a human label is expected. This is plain rendered text (works in every measurement mode); cite policy §13 (and §4 for casing). A systemic inconsistency in a canonical-identifier class is a `hard failure`; an isolated one-off label slip is `minor`.
- **Multi-handler split (§6 topology — project-policy-gated):** If the project `design-policy.md` defines a multi-handler split rule (a surface whose records span two or more **operational handlers** — a route/dispatch warehouse, a shipping lane, a fulfilment provider, or the project's analogue — must not be presented as one merged list), audit the live surface for it. Do the visible rows resolve to **two or more** such handlers, and are they **interleaved in one undifferentiated list** rather than split by view — per-handler tabs/segments, or sibling routes? An interleaved multi-handler list is a `hard failure` (cite policy §6 Multi-handler surfaces + its §5 hard failure); a surface already split by tabs, a per-handler segmenting lens, or sibling routes passes. **Consult the project policy for whether such a rule exists and what counts as a "handler" — skip entirely in projects whose policy defines no such rule** (this keeps the audit design-agnostic; the handler concept is the project's to define).
- **Density:** `scrollWidth` vs `clientWidth` — is the page leaking horizontal overflow? Are cards nested (card-in-card)? Is a 12-col grid rendered with only 2–3 fields per row (dead space)? Are KPI tiles showing values that are mostly `0` or `null`?
- **Peer gaps:** What pattern does each peer use — sticky header, two-column split, inline meta row, pill nav — that this page doesn't? Name the pattern and the peer.
- **Brand identity alignment (when `{brand_identity}` exists):** Does the page match the brand's stated visual language? Check:
  - Typography: body text size matches the brand scale (e.g., 13px not 14px), heading tracking matches, monospace used only where specified
  - Colors: background, badge pattern, semantic colors match the brand's exact values
  - Components: cards, buttons, badges match the brand's exact patterns (Tailwind classes)
  - Hard failures: none of the brand identity's section 8 items are present
  - Reference page alignment: would this page look at home alongside the brand's listed gold-standard pages?

### 6. Deliver (interactive)

Produce the review in exactly the structure defined in `workflow.md`. Template:

---

## Top 3 things that feel wrong

For each (no more, no less than 3):

- **{Short name}** — `{exact Tailwind class or token}` at `{file_path:line}`
- **Why:** {the question the user can't answer at a glance}
- **Before/after:**

| Element                | Before                  | After                                                               |
| ---------------------- | ----------------------- | ------------------------------------------------------------------- |
| `<h2>` in Context card | `text-xl font-semibold` | `text-sm font-medium uppercase tracking-wide text-muted-foreground` |

## Regional fixes

Only include regions that have actual fixes. Each bullet: `file_path:line` + class swap + one-line reason.

### Header

- ...

### Summary / KPI strip

- ...

### Context card(s)

- ...

### Table / list shell

- ...

### Expanded row / detail surface

- ...

### Color + density tokens

- ...

## Steal from peers

- **From `{peer_path}`:** {specific pattern — e.g., "inline meta row above the table instead of a second context card"} — port by {concrete action}.
- (repeat per peer if applicable)

## What's already fine

- ...
- ...

## Get radical (optional)

One paragraph. Omit entirely if the current layout is the right shape.

---

### 7. Emit Artifact (only when `{output_mode}` = "artifact")

If `{output_mode}` is not `"artifact"`, skip this step entirely.

Otherwise, write a structured screen-review file that downstream workflows (specifically `design-handoff` in refine-screen mode) will consume.

**Derive filename inputs:**

- `{target_slug}` — kebab-case slug from `{target_url}`'s pathname. Strip leading/trailing slashes, replace `/` with `-`, lowercase. Example: `https://app.example.com/reclaim/avask` → `reclaim-avask`. If the path is empty or `/`, fall back to the page's `<title>` slugified.
- `{date}` — current date in `YYYY-MM-DD` format from the project config / system time.
- `{project-root}` — **resolve via `git rev-parse --show-toplevel` from the session's current working directory.** Per `shared/worktree-portability.md` §1, this returns the worktree root when inside a worktree and the main checkout root otherwise. Do NOT use a cached resolution from earlier session state, and do NOT use an absolute path from `{main_config}` if it points outside the current working tree.
- `{implementation_artifacts}` = `{project-root}/_bmad-output/implementation-artifacts/`. If the directory doesn't exist, create it.

**Compute output path:**

```
{artifact_path} = {implementation_artifacts}/screen-review-{target_slug}-{date}.md
```

**Worktree refusal.** Before writing, verify `{artifact_path}` is a descendant of `{project-root}`. If not, halt with the diagnostic in `shared/worktree-portability.md` §4 — this catches the case where a stale absolute path leaked into state from an earlier session.

If a file at this exact path already exists, append `-v{N}` (starting at v2) so the prior artifact isn't overwritten — downstream consumers pick the most recent timestamp regardless.

**Write the artifact** exactly in the format specified in `workflow.md` under "Artifact output". The body uses the artifact's stable headings — `## Violations`, `## Keepers`, `## Edge States to Test`, `## Peer Steals`, `## Measurement Evidence` — with YAML frontmatter populated from state. Severity per violation must be one of `hard failure | major | minor` (not invented levels, not the chat review's looser language). Violations carry stable V1, V2, … IDs and are ordered by severity (hard failure → major → minor). The interactive chat review's "Top 3" maps to the artifact's first three violations; the artifact emits every violation you'd act on — do not truncate to 3.

**Rule-citation precedence (artifact mode).** Every violation's `Rule violated:` field must cite the policy section directly — never just a brief or peer page — so downstream consumers can re-resolve it against the canonical source. The acceptable forms, in order of preference:

1. **Policy citation:** `{brand_identity_path} §<N> (<section name>): "<verbatim rule text>"`. Example: `docs/design-policy.md §5 (Hard Failures): "Emoji as UI icons. Use Lucide icons or no icon at all."`
2. **Shared design-standards citation** when the policy is silent on a category the standards cover: `_bmad/bmm/workflows/design/shared/design-standards.md: "<rule>"`.
3. **Brief-only citation** as a last resort when no policy or standards rule exists: `Brief §<N>: "<rule>"`. Use sparingly — if the rule is brief-only, mark severity as `minor` unless the brief is the only source the project has.

Do not cite a peer page as the rule violated; peer pages may inform peer-steals but are not authority. If a peer page demonstrates the policy's intended pattern, cite the policy and reference the peer in the `Required correction:` field.

**Edge states — special rule for artifact mode.** The interactive review doesn't require an explicit edge-states section; the artifact does. In artifact mode you MUST list at least 2 edge states the design needs explicit variants for. Derive them from real data conditions visible on the page (e.g., "country with 0 rows", "country fully filed", "row with missing buyer VAT"), not from generic "loading / error / empty" templates. If you can't name 2 from the data, that's a sign you didn't measure enough in step 3 — go back and look.

**Anti-AI checklist — required in artifact mode.** Before emitting the artifact, evaluate the three checks defined in `workflow.md` § Artifact output → Anti-AI Checklist. Each check is binary AND requires a one-line rationale on the same line; an unchecked box without a written failure violation is invalid output.

1. **No generic card row layout.** Does the page lean on a row of identical (or near-identical) cards as its primary structure? Use measurement counts from step 3 (`counts.cards`) as evidence — if multiple cards share the same width / padding / framing / hierarchy and sit in a row above or instead of the working surface, the check fails. Card-shaped components used for genuine content surfaces (e.g., a single context card next to a table) do NOT fail this check; the test is "row of look-alikes as primary structure".
2. **Domain-authored hierarchy.** Walk the top 3 visually heaviest elements from step 3 (`top_visuals`) and the major region order. Is the ordering driven by domain logic specific to this product (risk, urgency, lifecycle, workflow state, value-at-stake) or by a generic template default (alphabetical, creation date, "summary cards first then table")? Name the specific domain rule in the rationale. If you can't name one, the check fails — that's evidence the page is using a template default.
3. **Recognizably this product.** Compare the page's accent color, type scale, badge shape, row density, and chrome against the policy's reference pages (or, if none, the peer paths from step 4). Would a user familiar with the rest of this product immediately recognize the page as belonging here, or would it pass as "any AI-generated admin UI"? Cite the specific shared signal in the rationale (e.g., "slate-navy accent + 13px dense rows + monospace IDs match `/avask` and `/queries` exactly"). If the page reads as generic, the check fails.

**Failure → violation rule.** If any check fails, you MUST also emit a matching block in `## Violations` with severity `hard failure`. The checklist is a summary cross-check, not a parallel track — every failing check has a corresponding violation. If you find yourself wanting to fail a check without a corresponding violation, the violation list is incomplete; go back and add it.

**Confirm the file is on disk** by listing it back to the user along with the chat-rendered interactive review:

> Artifact written to `{artifact_path}` — `design-handoff` (refine-screen) will pick this up automatically.

---

## TERMINAL — Behavior Update Digest (STD-DIGEST-001)

design-review is an audit-lane workflow: its output is a *finding*, so it must not stop at the written artifact. After delivering the review, emit the **Behavior Update Digest** and auto-execute the safe stages per `shared/behavior-update-digest.md` (STD-DIGEST-001): `doctrine_delta` (record any rule change via memory/policy) · `handoff_delta` (the review already routes to `design-handoff` refine-screen — name it) · `story_candidate` (draft the scoped unit + acceptance criteria from the top findings) · `owner_gated` · `completion_disposition` (STD-COMPLETION-001 `advisory`, enumerating the four deltas' real state). Recording doctrine, drafting a story, and re-issuing a brief are **registration/routing, not implementation** — the "Don't implement" rule below still holds. Findings with no digest is an invalid exit.

---

## RULES (enforced every time)

- Cite real class names and real file paths — no "the heading feels heavy", say `text-2xl font-bold` at `foo.tsx:128`.
- Measurements are evidence — include the actual numbers from step 3.
- Don't flag dark-mode issues.
- Don't propose new tokens — use what's in the design system (`--status-*`, `text-muted-foreground`, `bg-secondary`, etc.).
- Don't implement. Produce the review document only.

---

## FAILURE MODES

- **Silent mode degradation.** Starting in `chrome-live`, hitting a Chrome MCP failure, and proceeding without re-recording `measurement_method` + writing `measurement_caveat`. If the live tool stops working mid-run, halt, switch modes, and document.
- **Screenshot-only with no caveat.** Producing an artifact with `measurement_method: screenshot-only` and an empty `measurement_caveat` — that combination is invalid output. Downstream consumers cannot judge what to trust without the caveat.
- Skipping peer reads — "compare" with only one view in your head.
- Listing 10 issues instead of the top 3 — the ranking is the value.
- Vague class citations (`"the card"`) instead of the exact class on the exact element.
- Drifting into implementation ("I'll change this to...") — stop at the before/after table.
- Flagging density issues without the scrollWidth numbers to back them up (only applies in `chrome-live`; in `source-derived` and `screenshot-only` modes density claims must be flagged as inferred, not measured).
