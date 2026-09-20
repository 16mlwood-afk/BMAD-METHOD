# Getting a bespoke UI page built for an existing app — what exists today

**This tracked file is the record.** A reading copy also sits at
`~/Downloads/ui-generation-tools-2026-09-20.md` because that is what the owner opens; Downloads is
a scratch surface that gets wiped, so quote this one. Read-only survey — nothing was signed up
for, installed, configured or paid for, and no vendor was run.

**Read date for every source below: 2026-09-20.** Prices are as shown on the vendor's own page
on that date unless the row says otherwise.

**Question asked:** *"are there any web tools or integrations or anything out there in the AI
world where you can get a bespoke UI page built for your app, subscription costs or something, or
even just a Claude skill, something that simple."*

**Target surface:** `inbound-flow` — Next.js 14, App Router, TypeScript, Tailwind v4, shadcn/ui,
with its own design tokens and a versioned design policy (`docs/design-policy.md`, at v14).

---

## 1. The one-line answer

The category exists and is crowded, but the thing Mason is describing is **already installed,
already paid for inside his Claude subscription, and already wired into this repo** — the
`design-handoff → Claude Design → design-implement` chain — and no product found in this survey
does the part that actually matters here, which is holding a generated page to a written design
policy and a set of pass/fail truth tests before it lands on main.

**Calibrated label: Established (high confidence)** for the incumbent's existence and shape —
inspected directly on disk. **Likely (moderate)** for the claim that no surveyed vendor enforces a
policy/truth gate — that rests on vendor marketing copy and two pricing pages I could not render.

---

## 2. What I checked — by layer

Per the `tool-discovery` skill's proof-of-search requirement.

### Layer 1–2: local primitives and connected MCP servers

| Checked | Method | Finding |
|---|---|---|
| `~/bmad-method-v6/custom/workflows/design/` | `ls` + read | 17 design workflows present (list below) |
| `~/.claude/skills/` | `ls` | 20 global skills; none is a UI generator |
| `/Users/masonwood/code/inbound-flow/.claude/skills/` | `ls` | 46 project skills, incl. `frontend-design`, `design-policy-canonical`, `operational-cockpit`, `operational-analytics-band`, `operational-finance-ui`, `analytics-surface-architect`, and 20 `bmad-design-*` wrappers |
| `inbound-flow/.mcp.json` | read | two MCP servers, both domain (`inbound-flow-schemas`, `inbound-flow-us-route`). **No UI/design MCP server wired.** |
| `~/.claude/plugins/installed_plugins.json` | read | `frontend-design@claude-plugins-official` **is installed** (user scope, updated 2026-09-19) |
| `~/.claude/plugins/plugin-catalog-cache.json` | scripted regex sweep over all names + descriptions | UI-relevant entries: `frontend-design`, `figma`, `vercel`, `expo`, `design-mirror`, `ui-development`. **No general "generate a page for my existing app" plugin in the cached catalogue.** |
| `inbound-flow/docs/design-policy.md` | read (head) | v14, dated 2026-06-18, ported from accounting-tools v11. Carries §5 six-category audit, §6/§7 composition modes, §9 propagation, §12 positive assertions, §15 financial/money rules |
| `design-synthesize/manifest-schema.md` | read | see §5 below — this is the strongest incumbent asset |
| `design-handoff/workflow.md` | read (head) | carries the **2026-09-19 owner directive**, verbatim: *"the biggest takeaway is claude design should do the heavy lifting everything else is mostly advisory"* |
| `onboard-design-system/workflow.md` | grep | confirms Claude Design's **"Set up your design system"** form is a one-time seeding event creating a persistent workspace; strongest input is a **GitHub repo link** |

**The 17 installed design workflows:** `analytics-placement-triage`, `create-design-policy`,
`design-agent`, `design-artifact-loop`, `design-elevation`, `design-handoff`, `design-implement`
(project-level), `design-ingest`, `design-review`, `design-review-pr`, `design-router`,
`design-synthesize`, `design-tuning`, `modify-design-policy`, `onboard-design-system`, plus
`brand-identity-template.md` and two greenfield runbooks.

### Layer 6: marketplaces and the open web

Searched and/or fetched: v0.app, subframe.com, builder.io, onlook.com, magicpatterns.com,
polymet.ai, ui.shadcn.com, lovable.dev, bolt.new, locofy.ai, plus comparison coverage from
banani.co, sixtythirtyten.co, uibakery.io, g2, capterra, dev.to.

### Access failures — recorded separately from findings

These are **failures to see**, not evidence of absence:

| Source | Failure class | Consequence |
|---|---|---|
| `subframe.com/pricing` | **HTTP 404** — path moved | Subframe price taken from its own homepage instead |
| `magicpatterns.com/pricing` | **script-rendered** — page returned a heading and no table | Magic Patterns pricing is **UNVERIFIED** below |
| `polymet.ai` pricing | **gated** — "Get Started" / "Book a Demo", no public table | Polymet pricing is **UNVERIFIED** below |
| Claude Code in-app `/plugin marketplace` catalogue | **not web-indexed**; I read the on-disk cache instead | The cache may lag the live catalogue |
| Every vendor's actual behaviour | **not exercised** — the brief was read-only, nothing was signed up for | Every vendor row below is at most `Inspected`, never `Verified` |

**Absence classification:** my claim that no surveyed product enforces a design-policy/truth gate
is an **observed absence at the vendor-marketing layer** — it would be upgraded or refuted only by
actually running two of them against this repo. It does not license building anything.

---

## 3. The candidates

### 3a. Already here — the incumbent chain

| Component | What it takes in | What it outputs | Works on an existing repo? | Cost | Leaves the machine? |
|---|---|---|---|---|---|
| **`design-handoff`** | a finished/partial implementation + the design policy + tokens | an outcome-first markdown brief: the moment · pass/fail tests (T0…Tn) · what must dominate · the data and its defects · open questions | Yes — it is *built for* an existing repo, and deliberately withholds the current layout so the designer starts blank | included | no |
| **Claude Design** (claude.ai/design) | the brief + a **GitHub repo link** + a seeded design system | a designed page in a persistent workspace (`src/`, `ui_kits/`, `preview/`, generated `.html`, `SKILL.md`) | Yes — repo-linked | inside the Claude subscription | yes — repo is linked to claude.ai |
| **`design-synthesize`** | the same brief, terminal-native | a code-shaped bundle: HTML + `tokens.css` + screenshot + `manifest.yaml` | Yes | included | **no — fully local** |
| **`design-ingest` → `design-implement`** | the bundle | a component×property comparison grid, then the actual code change | Yes | included | no |
| **`design-review-pr`** | the diff | policy findings sorted into source-grep / dom-render / human-judgment lanes | Yes | included | no |

This is the exact shape Mason described — brief in, designed page out, implemented into the real
repo under policy. It is not a thing to go and find.

### 3b. The three external candidates that are genuinely worth his time

**Subframe** — <https://www.subframe.com/> (read 2026-09-20)
- **What it is:** a macOS app combining a design canvas, a coding agent and a browser, working
  directly in the codebase. Outputs React + Tailwind + TypeScript + Radix.
- **Existing codebase:** yes, explicitly — *"You can also import components & design tokens
  directly from code when designing"*, and it syncs with the design system in the codebase.
- **Price:** Free ($0, one project, limited AI credits) · **Pro $20 per editor/month** (unlimited
  projects, 5× credits). **Both tiers require you to bring your own Claude Code or Codex
  subscription** — which Mason already has.
- **Fit:** the strongest external fit found. It is the only surveyed product whose pitch is *a
  canvas over your real code and tokens* rather than *a generator that emits code*.
- **Against him:** macOS app, so it is a second place where design decisions get made; nothing in
  it reads `design-policy.md` or the T0…Tn tests. It would sit **beside** the chain, not inside it.
- **Grade: Inspected** (vendor homepage; not run).

**Onlook** — <https://www.onlook.com/for/nextjs> and <https://github.com/onlook-dev/onlook>
- **What it is:** open-source, local-first visual editor for React/Next.js. Edits real components
  on an infinite canvas; *"your changes are real code in your real Next.js repo with Storybook,
  Tailwind, and the App Router all respected"*.
- **Existing codebase:** yes — it is the explicit design goal. CI, hosting and git workflow unchanged.
- **Price:** **free and self-hostable**; a hosted cloud tier exists on a contact-us basis
  (price **UNVERIFIED** — no public figure found in the sources searched).
- **Fit:** zero subscription risk, nothing leaves the machine on the self-hosted path, and it is
  the cheapest way to answer *"what would this page look like if I nudged it"* without a round trip.
- **Against him:** it is a **visual editor**, not a designer. It will not produce a bespoke page
  from a brief; it gives you hands on the page you already have. Different job.
- **Grade: Inspected** (vendor page + GitHub listing; not installed).

**The official shadcn MCP server** — <https://ui.shadcn.com/docs/mcp>
- **What it is:** an MCP server that lets Claude Code browse, search and install components from
  shadcn registries conversationally — **including private and company-internal registries**,
  configured in `components.json` with `@namespace` syntax.
- **Install:** three lines in `.mcp.json` — `npx shadcn@latest mcp`.
- **Price:** no charge stated; distributed through npx in the shadcn package ecosystem.
- **Fit:** this is the one real **gap** the survey found. `inbound-flow/.mcp.json` has two domain
  servers and **no UI server at all**, so every shadcn component decision in this repo is currently
  made from model memory rather than the live registry. It complements the chain instead of
  competing with it.
- **Against him:** it installs and documents components; it designs nothing.
- **Grade: Inspected** (official docs page).

### 3c. Everything else, and why it loses

| Product | Price (read 2026-09-20) | Why it is a poor fit here |
|---|---|---|
| **v0 by Vercel** — <https://v0.app/pricing> | Free $0 ($5 credits) · **Plus $30/user/mo** (listed as reduced from $90) · Business $100/user/mo · Enterprise custom | Does now import GitHub repos, and its native stack *is* Next/TS/Tailwind/shadcn. But it is a hosted generator that wants to own the project; the repo and its tokens would leave the machine, and it enforces no policy. Note the secondary blogs said "$20 Premium" — **the vendor's own page says $30 Plus**, so the blogs are stale. |
| **Builder.io / Fusion** — <https://www.builder.io/pricing> | Free $0 (60 credits) · **Pro $24/user/mo** (500 credits) · Team $40/user/mo · Enterprise custom; overage $25 per 500 credits | Genuinely design-system-aware and codebase-aware, but its centre of gravity is **Figma → code**. There is no Figma file in Mason's loop. Credit-metered, and "Design System Intelligence" is Enterprise-gated. |
| **Lovable** | Pro ~$25/mo, ~100 message credits + 5/day *(secondary sources; vendor page not fetched — **UNVERIFIED**)* | Greenfield full-stack MVP builder. Pushes to a GitHub repo you own, but it is for standing up a new app, not designing one page inside a mature one. **Poor fit, and should be said to be.** |
| **Bolt.new** | Free (1M tokens/mo) · Pro ~$20–25/mo · Teams $30/member *(secondary sources — **UNVERIFIED**)* | Same class as Lovable: browser IDE for building an app from scratch. **Poor fit.** |
| **Magic Patterns** | **UNVERIFIED** — pricing page script-rendered. Moved to usage-scaled credits with pay-as-you-go from 2026-03-20 | Exports to React or Figma. Component-level ideation tool; no evidence found that it reads an existing repo's tokens. |
| **Polymet** | **UNVERIFIED** — gated behind Get Started / Book a Demo | Claims bring-your-own design system plus GitHub, private npm and Storybook integration. Worth a second look *only* if the demo wall is opened; nothing checkable today. |
| **tempo.new** | not fetched | Described as compatible with existing React codebases, imports components from Storybook. Drag-and-drop over React code — same class as Onlook, with a subscription attached. |
| **Locofy / Anima / Superflex / UX Pilot / Figma Make** | not individually fetched | All are **Figma-first**. Locofy converts Figma Styles and Variables into CSS custom properties; Anima and Superflex sit in the same lane. They solve *"I have a Figma file and need code"*. Mason has a written brief and a token file, not a Figma file. **Wrong input format — the whole class is a poor fit.** |
| **Claude Agent SDK** | API metered | Could build a bespoke generator. This is the *build* layer, layer 7, and it is not reachable from here: the chain that would be built already exists. |

---

## 4. The call — **keep what we have, plus one free bolt-on**

**KEEP** the `design-handoff → Claude Design → design-implement` chain. **ADOPT**, at zero cost,
the official shadcn MCP server into `inbound-flow/.mcp.json`. **DO NOT ADOPT** any subscription
product today.

Three reasons, in order of weight:

1. **The owner already decided this.** `design-handoff/workflow.md` carries a directive dated
   **2026-09-19 — yesterday** — in Mason's own words: *"the biggest takeaway is claude design
   should do the heavy lifting everything else is mostly advisory"*. Buying a second designer
   twenty-four hours after settling on the first would reopen a closed decision, not answer a
   question.
2. **No surveyed product holds a page to a policy.** v0, Builder.io, Subframe, Lovable and Bolt
   all generate; none of them refuses. The chain here refuses in about eight distinct ways.
3. **The cheapest real gap is not a designer at all.** It is that this repo talks to the shadcn
   registry from memory. That is three lines of config and no money.

**Strongest rejected alternative:** Subframe at $20/editor/month. It loses on a contract field
rather than on quality — a canvas app on a second surface cannot carry `compliance_state`,
`visual_quality_axes` or the T0…Tn tests, so anything it produced would enter the repo through the
side door that `design-review-pr` exists to close.

---

## 5. What we already have that a newcomer would duplicate

**`design-synthesize`'s manifest contract** — and it is not close.

Its `bundle/manifest.yaml` is **split-authority**: authoritative for the synthesis receipt,
interaction semantics, region declarations and flow invariants; **never** authoritative for visual
properties. Inside one generated page it records:

- `policy_version_hash` (sha256) and `baseline_commit` — so a page knows which policy version it
  was designed against;
- `compliance_state`, one of `pass | under_grounded | hard_failed | positive_failed | drift_failed |
  lift_failed | exemplar_failed | dev_only`;
- `skills_invoked` **versus** `skills_unloaded`, with the rule stated in the schema itself —
  *"Operating 'in the spirit of' a skill without loading it does NOT qualify"* — and an unloaded
  mandatory skill **forces** `compliance_state: under_grounded`;
- `evidence_basis` — whether the synthesizer actually read its own screenshot, actually compared
  against an exemplar, actually compared against a baseline. `unverified-strong` exists as an
  honest downgrade from `excellent` when no comparison happened;
- `visual_quality_axes` across five mandatory axes with evidence strings, and `macro_hierarchy`
  per screen with an above-the-fold allocation that **must sum to 100**;
- `visual_lift_over_baseline`, which may be `null`, with the instruction *"do NOT assert true
  without comparison"*;
- `dev_no_render: true`, which `design-implement` **refuses**.

That is a generated artefact that reports honestly on how well-grounded it is. No product in this
survey ships anything of the kind, and a newcomer brought in to "design a page" would quietly
route around all of it.

---

## 6. What would change the recommendation

**One fact:** if Claude Design turns out not to accept `inbound-flow`'s repo link and design-system
seed — so the designed page cannot see the real tokens and has to be re-typed by hand — then the
brief-to-page step is broken at its most important joint, and Subframe's $20/editor/month becomes
the cheapest way to design against the real token file. That is checkable in one sitting at the
claude.ai/design "Set up your design system" form, and `onboard-design-system` already produces the
exact paste-ready intake it asks for.

A weaker second: if Polymet's demo wall opens and it genuinely reads a private npm design system
and a Storybook, it moves from UNVERIFIED into the same row as Subframe and should be re-judged.

---

## 7. Retrieval report

- **modalities_used:** local filesystem inspection (`ls`, `cat`, `grep`, a scripted JSON sweep of
  the plugin catalogue cache), `WebSearch`, `WebFetch`.
- **coverage_scope:** vendor primary pages for v0, Subframe, Builder.io, Polymet, shadcn and
  Onlook; secondary comparison coverage for Lovable, Bolt, Magic Patterns, tempo, Locofy, Anima,
  Superflex, UX Pilot and Figma Make; the full on-disk Claude plugin catalogue cache and both
  skill directories; the fork's 17 design workflows.
- **time_window:** all reads 2026-09-20. Vendor pricing is a spot reading and these vendors
  reprice frequently — v0 was showing a strikethrough sale price at the time of reading.
- **access_failures:** `subframe.com/pricing` 404 · `magicpatterns.com/pricing` script-rendered ·
  `polymet.ai` pricing gated behind signup/demo · the in-app plugin marketplace is not
  web-indexed (on-disk cache read instead, may lag) · **no vendor was signed up for, run, or
  exercised** — nothing here is graded `Verified`.
- **negative_findings:** no UI-generating MCP server is wired into `inbound-flow/.mcp.json`; no
  general "design a page for my existing app" plugin appears in the cached Claude plugin catalogue;
  no evidence found, **in the sources searched**, that any surveyed vendor enforces a written design
  policy or pass/fail truth tests over its generated output. None of these is evidence that such a
  thing does not exist.

### Sources

- v0 pricing — <https://v0.app/pricing>
- v0 docs FAQ — <https://v0.app/docs/faqs>
- Subframe — <https://www.subframe.com/>
- Subframe GitHub — <https://github.com/SubframeApp/subframe>
- Builder.io pricing — <https://www.builder.io/pricing>
- Builder.io Fusion — <https://www.builder.io/fusion>
- Onlook for Next.js — <https://www.onlook.com/for/nextjs>
- Onlook GitHub — <https://github.com/onlook-dev/onlook>
- shadcn MCP docs — <https://ui.shadcn.com/docs/mcp>
- Magic Patterns pricing changes — <https://www.magicpatterns.com/blog/new-plans-and-pricing>
- Polymet — <https://polymet.ai/>
- Locofy — <https://www.locofy.ai/>
- Figma-to-code comparison — <https://www.sixtythirtyten.co/blog/from-figma-to-code-ai-design-to-dev-workflows-in-2026>
- Lovable/Bolt comparison — <https://www.nxcode.io/resources/news/lovable-vs-bolt-new-2026-ai-app-builder-comparison>
- Bolt pricing analysis — <https://justinmckelvey.com/blog/bolt-pricing>
- v0 pricing secondary (superseded by the vendor page) — <https://uibakery.io/blog/vercel-v0-pricing-explained-what-you-get-and-how-it-compares>

**Local artefacts inspected:** `~/bmad-method-v6/custom/workflows/design/` (17 workflows),
`design-synthesize/manifest-schema.md`, `design-handoff/workflow.md`,
`onboard-design-system/workflow.md`, `inbound-flow/docs/design-policy.md` (v14),
`inbound-flow/.mcp.json`, `inbound-flow/.claude/skills/` (46), `~/.claude/skills/` (20),
`~/.claude/plugins/installed_plugins.json`, `~/.claude/plugins/plugin-catalog-cache.json`,
`~/.claude/plugins/known_marketplaces.json`.
