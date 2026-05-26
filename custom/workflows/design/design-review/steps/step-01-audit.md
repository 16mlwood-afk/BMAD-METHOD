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

### 2. Read the Page

- Call `mcp__claude-in-chrome__read_page` on `{tab_id}`. This returns visible text + DOM structure — both are inputs to the compare step.

### 3. Measure (evidence, not impressions)

Call `mcp__claude-in-chrome__javascript_tool` to collect concrete measurements. At minimum capture:

- **Top 3 visual elements:** `fontSize`, `fontWeight`, `color` (computed styles) of the three visually heaviest elements on the page (largest headings, primary CTAs, big numbers).
- **Scroll containers:** `scrollWidth` vs `clientWidth` and `scrollHeight` vs `clientHeight` for every element with `overflow: auto|scroll`. Flag any where scroll dimension exceeds client dimension — that's horizontal or vertical overflow.
- **Counts:** cards, sections, KPI tiles, table rows visible.
- **Duplicated data:** any field/value that appears in 2+ distinct regions on the page (e.g., the order ID rendered in both the header and a context card).

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
- `{implementation_artifacts}` — resolve from `{main_config}`. Common value: `{project-root}/_bmad-output/implementation-artifacts/`. If the directory doesn't exist, create it.

**Compute output path:**

```
{artifact_path} = {implementation_artifacts}/screen-review-{target_slug}-{date}.md
```

If a file at this exact path already exists, append `-v{N}` (starting at v2) so the prior artifact isn't overwritten — downstream consumers pick the most recent timestamp regardless.

**Write the artifact** exactly in the format specified in `workflow.md` under "Artifact output". The body uses the artifact's stable headings — `## Violations`, `## Keepers`, `## Edge States to Test`, `## Peer Steals`, `## Measurement Evidence` — with YAML frontmatter populated from state. Severity per violation must be one of `hard failure | major | minor` (not invented levels, not the chat review's looser language). Violations carry stable V1, V2, … IDs and are ordered by severity (hard failure → major → minor). The interactive chat review's "Top 3" maps to the artifact's first three violations; the artifact emits every violation you'd act on — do not truncate to 3.

**Rule-citation precedence (artifact mode).** Every violation's `Rule violated:` field must cite the policy section directly — never just a brief or peer page — so downstream consumers can re-resolve it against the canonical source. The acceptable forms, in order of preference:

1. **Policy citation:** `{brand_identity_path} §<N> (<section name>): "<verbatim rule text>"`. Example: `docs/design-policy.md §5 (Hard Failures): "Emoji as UI icons. Use Lucide icons or no icon at all."`
2. **Shared design-standards citation** when the policy is silent on a category the standards cover: `_bmad/bmm/workflows/design/shared/design-standards.md: "<rule>"`.
3. **Brief-only citation** as a last resort when no policy or standards rule exists: `Brief §<N>: "<rule>"`. Use sparingly — if the rule is brief-only, mark severity as `minor` unless the brief is the only source the project has.

Do not cite a peer page as the rule violated; peer pages may inform peer-steals but are not authority. If a peer page demonstrates the policy's intended pattern, cite the policy and reference the peer in the `Required correction:` field.

**Edge states — special rule for artifact mode.** The interactive review doesn't require an explicit edge-states section; the artifact does. In artifact mode you MUST list at least 2 edge states the design needs explicit variants for. Derive them from real data conditions visible on the page (e.g., "country with 0 rows", "country fully filed", "row with missing buyer VAT"), not from generic "loading / error / empty" templates. If you can't name 2 from the data, that's a sign you didn't measure enough in step 3 — go back and look.

**Confirm the file is on disk** by listing it back to the user along with the chat-rendered interactive review:

> Artifact written to `{artifact_path}` — `design-handoff` (refine-screen) will pick this up automatically.

---

## RULES (enforced every time)

- Cite real class names and real file paths — no "the heading feels heavy", say `text-2xl font-bold` at `foo.tsx:128`.
- Measurements are evidence — include the actual numbers from step 3.
- Don't flag dark-mode issues.
- Don't propose new tokens — use what's in the design system (`--status-*`, `text-muted-foreground`, `bg-secondary`, etc.).
- Don't implement. Produce the review document only.

---

## FAILURE MODES

- Reviewing from screenshots alone without step-3 measurements.
- Skipping peer reads — "compare" with only one view in your head.
- Listing 10 issues instead of the top 3 — the ranking is the value.
- Vague class citations (`"the card"`) instead of the exact class on the exact element.
- Drifting into implementation ("I'll change this to...") — stop at the before/after table.
- Flagging density issues without the scrollWidth numbers to back them up.
