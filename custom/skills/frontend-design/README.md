# frontend-design — installed verbatim from the Anthropic marketplace

`SKILL.md` is a verbatim copy of:

`~/.claude/plugins/marketplaces/claude-code-plugins/plugins/frontend-design/skills/frontend-design/SKILL.md`

Original authors: Prithvi Rajasekaran, Alexander Bricken (Anthropic). Plugin v1.0.0.

## Why it's installed here

The `design-artifact-loop` workflow (`_bmad/bmm/workflows/design/design-artifact-loop/workflow.md` lines 227, 239, 388) requires a "frontend / webapp design skill (`website-building` or project-equivalent)" for UI-fix guidance. Without one, the workflow's step 2 pre-flight records `"frontend skill missing — UI fix guidance falls back to policy + design-standards.md"` in `evidence_gaps` and outputs degrade silently. Installing this skill makes the workflow resolvable end-to-end.

## Tonal precedence — important

The skill's body encourages picking a "BOLD aesthetic direction" — brutally minimal, maximalist chaos, retro-futuristic, brutalist/raw, playful/toy-like, etc. **Those framings directly contradict `docs/design-policy.md`**, which mandates "serious, precise, trustworthy — calm fintech, never marketing or playful SaaS."

The conflict is resolved at the workflow level. Per `_bmad/bmm/workflows/design/design-artifact-loop/workflow.md` → "Source-of-truth precedence":

> 2. Project design policy — `docs/design-policy.md` ... Hard failures, status rules, layout principles, palette, typography.
> 3. Canonical sister skills — `design-policy-canonical`, `operational-analytics-band`, `operational-finance-ui`. Invoked within their scope; their rules are not restated here.
> ...
> If a sister skill's answer contradicts the brief, the policy wins.

In practice that means: when `frontend-design` and `design-policy-canonical` disagree on tone, layout, color, or typography, `design-policy-canonical` wins. `frontend-design` is consulted only for the slice of UI-craft guidance the project policy doesn't speak to (component refinement detail, anti-AI-slop tactics, code-quality patterns).

If `frontend-design`'s framing starts leaking into outputs, the corrective is to re-cite the policy more aggressively in the affected `screen-review` / `design-handoff` — not to uninstall the skill.

## Update policy

If the marketplace skill is updated, re-run the install by copying the new `SKILL.md` over the project copy. Do not edit `SKILL.md` in place — keep it a verbatim mirror so the diff against any future marketplace version is meaningful.
