# Research-First Skill Standard — DRAFT (not yet enforced)

**Status:** DRAFT for Mason's review. Nothing here is live enforcement.
**Author:** Claude (session claude-session-20260724-140148)
**Created:** 2026-07-24
**Origin:** Mason flagged that skill discovery is inward-only and skills lack research provenance, after "no Outlook connection" was reported without any external search — when an official Anthropic M365 connector and several GitHub Outlook MCP servers exist.
**Scope:** UNDECIDED — global doctrine vs fork-wide contract is Mason's call (see §7).
**Models on:** the brief-provenance contract in this fork (this standard is deliberately its sibling for skills).

---

## 1. The defect, framed precisely (two parts)

This is a systemic gap, not a one-off mistake.

**Part 1 — Discovery is inward-only.**
- "I searched the tool registry" means **"I only checked tools already installed in this session."**
- It does **NOT** mean "this integration does not exist on the web / marketplace / GitHub."
- Conflating the two misleads whenever an Outlook / M365 / GitHub / MCP / plugin option exists but simply isn't wired in. It is how the assistant ends up saying "there's nothing, let's build our own" when a researched solution is one search away.

**Part 2 — Skills lack research-first provenance.**
- No mandatory external search before building a skill.
- No origin URLs or research references recorded.
- No version / lineage frontmatter (unlike briefs, which carry provenance).
- No drift-review schedule and no per-skill changelog.

The fix is a standard with a mandatory external-discovery gate, an adopt-over-build default, provenance frontmatter, drift discipline, and a *designed* (not yet switched-on) enforcement tier.

---

## 2. (A) External Discovery Gate — MANDATORY BEFORE BUILD

Before authoring or materially editing a skill, run **both**:

1. **A web search** — docs, marketplace, blog posts — for existing solutions.
2. **A GitHub / MCP / extension search** — code-level connectors or skills.

Record, and surface it **inside the skill's own doc** as a visible block (not implied):

```
## External research checked
- Date: YYYY-MM-DD
- Queries:
  - "<query 1>"
  - "<query 2>"
- Relevant sources considered:
  - <url> — <one-line why it's relevant / connector repo / research writeup>
  - <url> — ...
- Verdict: adopting <x> / adapting <x> / building original (see exemption §3)
```

A skill whose doc has no "External research checked" block has **not** satisfied the gate.

---

## 3. (B) Adopt-Over-Build Rule — DEFAULT

**Default:** reuse or adapt an evidence-based existing solution when all three hold:
- License permits the use,
- Security/privacy constraints are met,
- Fit to the domain (BMAD workflows / Mason's stack) is adequate.

**"Build our own" is an exemption**, allowed ONLY with a concrete named reason:
- License incompatibility,
- Security / privacy risk,
- Quality issues in the existing repo (unmaintained, buggy, untested),
- Poor fit to BMAD workflows.

The exemption reason is **encoded in the skill frontmatter** (`origin_type: original` + `exemption_reason:`). No reason = not a valid original build.

---

## 4. (C) Skill Provenance Frontmatter — REQUIRED (mirrors the brief contract)

Every skill carries a provenance block. A skill without it is treated as **UNVERIFIED** in advisory terms.

```yaml
---
id: <stable-kebab-slug>
name: <display name>
version: <semver, e.g. 1.0.0>
created_at: <YYYY-MM-DD>
author: <who authored it>
source_research:            # URLs / repos that informed it — REQUIRED, >=1 entry
  - <url>
origin_type: adopted | adapted | original
exemption_reason: <required only when origin_type: original>
predecessor_id: <id, if this revises an earlier skill>
superseded_by: <id, if this is no longer the active version>
last_reviewed_at: <YYYY-MM-DD>
review_notes: <short note from the last review>
---
```

Notes:
- `source_research` must have at least one real URL. An empty list fails the gate.
- `origin_type: original` requires `exemption_reason`.
- `predecessor_id` / `superseded_by` give lineage, exactly like brief revisions.

---

## 5. (D) Drift & History Discipline

**Per-skill changelog** (in the skill doc or a sibling `CHANGELOG`):

```
## Changelog
- v1.1.0 — 2026-08-01 — <change summary> — <reviewer>
- v1.0.0 — 2026-07-24 — initial — Claude
```

**Review cadence** — periodic (annually, or on a major infra shift), mirroring brief-intake checks:
- Verify the origin/source URLs still resolve,
- Confirm the assumptions the skill rests on still hold,
- Update `last_reviewed_at` / `review_notes`, or **supersede** the skill when drift is found (set `superseded_by`).

---

## 6. (E) Enforcement Tier — DESIGN ONLY (not claimed live)

No deterministic enforcement is asserted yet. What HARD enforcement *would* look like:

- **Provenance linter** — refuses to treat a skill as "live" unless its frontmatter is complete AND `source_research` has ≥1 URL. Runnable locally and in CI.
- **New-skill gate** — a pre-commit / CI check (and/or a PreToolUse marker in the fork) that blocks adding a skill file without a provenance block and an "External research checked" section.
- **Retrofit sweep** — a one-time pass that backfills provenance on existing skills, flagging any that can't cite external research as "original — exemption needed."

Per the enforcement-expert doctrine: prose alone is PROBABILISTIC. If Mason wants this guaranteed, the linter + CI/marker is the DETERMINISTIC tier, and I should run `enforcement-expert` to place it before claiming it's enforced. This section is the design, not a switch that's been flipped.

---

## 7. Rollout options — Mason's decision

**Soft (advisory, forward-looking):**
- Applies to *new* skills going forward, as a guideline.
- I follow it by habit; no linter, no CI, no retrofit.
- Zero blast radius; also zero guarantee (probabilistic).

**Hard (fork-wide enforced contract, like briefs):**
- A formal fork standard, enforced via linter + CI/hook.
- Existing skills retrofitted with provenance over time.
- Propagates to the 13 projects on sync — real blast radius, real teeth.

**Scope question for Mason:**
> Do you want this as a fork-wide, enforced skills-provenance contract (like briefs), or as a forward-looking guideline for new skills only?

And, orthogonally: does the doctrine live in **global CLAUDE.md** (applies to everything I do for you), in the **BMAD fork** (propagates to 13 projects), or **both, layered**?

---

## 8. Behaviour I have already adopted (regardless of the teeth decision)

Effective now, without waiting for the enforcement decision:

1. **No more inward-only "doesn't exist" claims.** When I say there's no X integration, I will always qualify: *"There is no X tool installed in this session; I have NOT searched the wider web/marketplace"* — and then offer to search, or search first.
2. **Proposing a new skill triggers a real external search first** — web + GitHub — with a findings summary and an explicit adopt-vs-build call and reason.
3. **New skills get a minimal provenance note** in the paste-back, even before the full contract is ratified.

---

## 9. Rollout note (Step 4 — phased plan)

**Pilot repo:** the **fork itself** (`~/bmad-method-v6`) — it is the most skills-heavy repo (`custom/skills`, `custom/claude-global/skills`) and is where skills are *authored*, so a linter here catches drift at the source before it ever syncs. cash-recovery (first skills-layout project) is the natural second pilot.

**Phasing (warn → gate), mirroring how `check:completion` / `check:digest` were staged:**
1. **Warn-only linter — SHIPPED 2026-07-24.** `tools/check-skill-provenance.js` (npm `check:skillprov`), wired warn-only into `npm test`. Flags any skill missing the provenance block, a required field, or a `source_research` URL (a logged `origin_type: original` + `exemption_reason` passes). Exits 0 always; `--added` scopes to newly-staged skills, `--strict` is the future gate (unwired). **Baseline measured: 15/15 fork skills UNVERIFIED** (all predate the standard) — that is the retrofit backlog, item 2. Enforcement classified with `enforcement-expert`: the provenance frontmatter is DETERMINISTIC (checked); the external-discovery *act* stays PROBABILISTIC (no artifact — a fabricated URL passes; the CLAUDE.md honesty rule is its only lever).
2. **Retrofit sweep — COMPLETE 2026-07-24.** All 15 fork skills provenanced (0 gaps, linter + structural validator both green). 4 done manually (incl. the catch that `frontend-design` is Anthropic's OFFICIAL skill vendored in — origin_type `adopted`), 11 via the `skillprov-retrofit` parallel workflow (1 agent/skill, external discovery + provenance). Origin breakdown: **1 adopted** (frontend-design = Anthropic's vendored skill), **8 adapted** (mostly from upstream bmad-code-org/BMAD-METHOD: bmad-correct-course, bmad-onboard, bmad-onboard-tutorial, design-policy-canonical, operational-finance-ui, policy-skills-healthcheck, mason-bmad-workflow-expert; plus enforcement-expert from industry guardrail practice), **6 original** (analytics-surface-architect, context-compaction, finance-domain-pass, operational-analytics-band, operational-cockpit, operator-domain-pass — each with a concrete exemption_reason naming the closest rejected adjacents). `property-appraisal` (global) is the worked exemplar.
3. **Arm on new skills only — ARMED 2026-07-24.** `check:skillprov -- --added --strict` is chained into BOTH pre-commit paths (fast + full), scoped by `git --diff-filter=A` to SKILL.md files this commit ADDS — a no-op unless a new skill is being committed. A newly-added skill without valid provenance (or a logged `origin_type: original` + `exemption_reason`) exits 1 and BLOCKS the commit, with an actionable message naming the missing fields + the exemption escape hatch. Proven both directions before arming (bad new skill blocks / provenanced new skill passes / nothing-added is a clean no-op). Existing skills stay warn-only (full-corpus `check:skillprov` in `npm test`, non-blocking). Escape hatch: add provenance, add a logged exemption, or `--no-verify`. Honest caveat: quiet-at-arming, not an elapsed soak (same as the fork's `check:completion` arming).
4. **Fork-wide hard gate — NOT YET ARMED (explicit later decision).** Only after the new-skill phase shows low friction: extend `--strict` from `--added` to the full corpus, add a CI gate, and promote STD-SKILLPROV-001 into the machine-parsable STANDARDS index with a synced `Home: shared/...`. This step is deliberately held as a separate owner decision, per Mason 2026-07-24.

**Retrofit order beyond the pilot:** fork skills → cash-recovery → the other 12 projects on the existing deliberate sync thread (never a `--force` fan-out into live sessions).

**Costs / friction seen up front:**
- Retrofit is manual per-skill (the external search is the real cost, ~5 min each) — the warn-only phase quantifies the backlog before committing.
- `source_research` on a genuinely-original skill needs an honest exemption, not a fabricated URL — the linter checks presence, not that the URL is load-bearing; that judgment stays with the author.
- The deterministic tier (linter + hook) must be authored via `enforcement-expert` before being called "enforced" — that is the Step-2 next action, not done here.

**Promotion trigger:** warn-only quiet on new skills + pilot retrofit complete on the fork → then, and only then, arm the fork-wide gate.

## Changelog
- v0.2.0 — 2026-07-24 — added §9 rollout note (pilot = fork, warn→gate phasing, retrofit order, friction); recorded scope decision (global hard / fork soft-but-committed, both layered); property-appraisal retrofitted as exemplar — Claude (session claude-session-20260724-140512)
- v0.1.0 — 2026-07-24 — initial DRAFT for review — Claude (session claude-session-20260724-140148)
