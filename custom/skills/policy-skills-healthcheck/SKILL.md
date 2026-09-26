---
name: policy-skills-healthcheck
description: >
  Audit the skill corpus for long-term health of POLICY-SKILLS — skills that encode necessity
  (materiality / domain ownership / safety / correctness), e.g. finance-domain-pass,
  analytics-surface-architect. Load when the user says "sanity-check our skills", "are our skills
  healthy / well-routed", "audit the skills for dormant modes", or after creating/editing a
  policy-skill. Checks for dormant modes (declared but uncalled), missing plain-language invocation
  policies, duplicated/conflicting responsibility, and undocumented routing — and reports gaps as
  system-health findings. Read-only: it diagnoses and proposes; it does not modify skills.
metadata:
  short-description: Audit policy-skills for dormant modes / missing invocation policy / routing gaps
provenance:
  id: policy-skills-healthcheck
  version: 1.0.0
  created_at: 2026-07-24
  author: Claude (with Mason)
  source_research:
    - https://smithery.ai/skills/majesticlabs-dev/skill-linter  # closest analog: audits skills on a Trigger/Structure/Steering/Pruning framework incl. empirical dormant-trigger testing
    - https://mcpmarket.com/tools/skills/skill-specification-linter  # adjacent: lints Claude Code skill frontmatter/structure/content quality against the agentskills.io standard
    - https://dev.to/avifenesh/your-ai-agent-configs-are-probably-broken-and-you-dont-know-it-16n1  # adjacent: agnix, a linter for AI agent configs catching silent skill-invocation failures
  origin_type: adapted
  exemption_reason: ""
  predecessor_id:
  superseded_by:
  last_reviewed_at: 2026-07-24
  review_notes: "Backfill under STD-SKILLPROV-001. Core method (audit a skill corpus for trigger/invocation health and dormant capabilities) mirrors external skill-linter tooling; this fork reworks it around a fork-specific 'policy-skill' necessity taxonomy, cross-skill symmetry, and PR-severity routing (S1/S2/S3 tied to STATUS.md), so it is adapted rather than adopted."
---

## External research checked
- Date: 2026-07-24 · Queries: "AI agent skill audit dormant modes invocation policy linter tool" · "Claude Code skills governance audit tool GitHub open source" · "BMAD-METHOD bmad-code-org workflow health check skill audit routing"
- Sources: <https://smithery.ai/skills/majesticlabs-dev/skill-linter> · <https://mcpmarket.com/tools/skills/skill-specification-linter> · <https://dev.to/avifenesh/your-ai-agent-configs-are-probably-broken-and-you-dont-know-it-16n1>
- Verdict: ADAPTED — external skill-linter tools already audit skills for trigger health / dormant capabilities via a generic Trigger/Structure/Steering/Pruning framework; this skill takes that core idea but reworks it around this fork's policy-skill necessity taxonomy, sister-skill symmetry, and severity-based PR routing tied to STATUS.md, with no upstream BMAD-METHOD equivalent found.

# Policy-skills Health Check

A **policy-skill** encodes *what must or must not happen* — materiality (when it should engage at
all), domain ownership (who owns a decision), safety, or correctness. Examples in this fork:
`finance-domain-pass` (when is presentation domain logic?), `analytics-surface-architect` (what shape
answers the question?). Contrast a *utility* skill, which just performs a mechanical transform.

Policy-skills rot in a specific way: they stay correct in the core but get **under-routed** — invoked
from one narrow branch, with dormant modes and a jargon-coded trigger nothing reaches. This skill
audits for that. It is **read-only**: it produces findings + proposed fixes; the user applies them.

## When to invoke

- The user asks to "sanity-check / audit our skills" or "are our skills healthy / well-routed".
- Proactively, right after creating or editing any policy-skill (per the mason-bmad-workflow-expert
  "Policy-skills" doctrine) — a single-skill audit, not the whole corpus.

Do **not** use for: ordinary skill *content* review (that's mason-bmad Mode 1), or for utility skills
that encode no necessity.

## The four checks (run per policy-skill)

1. **Invocation policy present?** Does the skill carry a plain-language *When to invoke* block —
   **use / don't use / if-uncertain** — in language a human would actually trigger, not internal
   jargon? A skill whose only trigger is domain vocabulary (`archetype`, `evidence layer`) is
   effectively invisible to auto-activation.
2. **Every mode has a real caller?** For each declared mode, name at least one actual invocation site
   (a workflow step, another skill, or a documented human entry). A mode with no caller is **dormant**
   — flag it (this is the `analytics-surface-architect` `critique`/`explain` case).
3. **Symmetry with sister skills?** Skills in the same domain family should get the same treatment —
   plain invocation policy, wired at the same lifecycle points (e.g. a handoff-time enrich AND a
   review-time audit). Flag asymmetry (one domain has a PR-time check, its sister doesn't).
4. **Routing documented both ways?** The skill names where it's called from; each caller names the
   skill (not a re-derived inline copy of its logic). Flag a caller that re-implements the skill's
   judgment instead of deferring to it (undocumented / bypassed routing).

## Procedure

1. **Enumerate policy-skills.** Walk `custom/skills/` (and any project `.claude/skills/`); classify each
   as policy (encodes necessity) or utility. Audit only policy-skills.
2. **Per skill, run the four checks.** For mode→caller, grep the workflow corpus
   (`custom/workflows/`) for the skill name and for inline re-derivations of its decision.
3. **Cross-skill symmetry pass.** Group by domain; compare invocation policy + lifecycle wiring across
   the group.
4. **Report** (see output contract). Order by severity. Propose the concrete fix for each (the
   mason-bmad playbook: add the invocation block / wire the dormant mode at its intended caller /
   restore symmetry), but **do not apply** — hand findings back.

## Output contract

```
audited:        [ <skill>, ... ]              # policy-skills examined
findings:
  - skill:      <name>
    check:      <invocation-policy | dormant-mode | symmetry | routing>
    severity:   <S1 | S2 | S3>
    reason:     "<what's wrong, concretely + the evidence: caller/grep/asymmetry>"
    suggested_fix: "<the concrete proposed change — NOT applied>"
healthy:        [ <skill that passed all four>, ... ]
```

## Severity (three levels — enough to route, not a second rating system)

**S1 — Contract breaker (block PR; fix before merge or explicitly waive with a comment).** The change
is unsafe as-is:
- a NEW or materially-changed policy-skill with **no** plain-language invocation block;
- a mode **removed or repurposed without updating its callers** (runtime behavior mismatch);
- a caller that **re-derives policy logic** instead of deferring to the skill (duplicated truth);
- a change that **breaks symmetry in a way that contradicts existing policy** (e.g. finance has a
  materiality rule, analytics hardcodes a different one).

**S2 — Structural debt (safe to merge; log + schedule).** Track it; clear it soon — do NOT silently
ship-and-forget:
- an existing policy-skill with a **dormant mode that never had a caller** (design oversight, not breakage);
- **asymmetry with a sister skill that is "just behind"** (not contradicting policy) — e.g. analytics
  missing an invoke-block that finance has;
- **routing documented only one way** (callers know the skill, but the skill text doesn't name its
  callers, or vice versa).

**S3 — Hygiene / style (opportunistic; fix when you're in the file anyway).**
- technically-correct but inconsistent wording (slightly different "use when" phrasing across skills);
- missing examples / edge-case notes in an otherwise-sound skill;
- minor duplication between a README/comment and the SKILL.md.

## Routing (how the severities are used)

- **S1** → block the PR / skill change; must be fixed, or explicitly waived with a comment saying why.
- **S2** → allowed to merge, but requires EITHER a follow-up task/issue OR an entry in the
  **"Policy-skill debt"** section of `STATUS.md`. Never merge an S2 with no trace.
- **S3** → optional; fix opportunistically.

If nothing is wrong, say so plainly.
