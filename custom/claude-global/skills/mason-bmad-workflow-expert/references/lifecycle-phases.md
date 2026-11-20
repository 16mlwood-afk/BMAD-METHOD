# Greenfield vs Brownfield Lifecycle

Upstream BMAD is heavily greenfield-biased. It assumes a project flows from PRD → epics → stories → code. That works well for new projects; it breaks down for ongoing maintenance, where there's no fresh PRD and the "story" is often a single-line bug report or refactor request.

The Mason-BMAD fork acknowledges this asymmetry. Some pieces are shipped; some are designed but not yet built. Always check STATUS.md to confirm what's live.

## The Two Modes

### Greenfield
- Project starts from scratch or from a major new initiative.
- Artifacts exist: PRD, epics, stories.
- Workflows can assume those artifacts are present and grounded.
- Quick-dev Mode A (spec-driven) is the natural fit.

### Brownfield
- Project exists, has real users, has accumulated decisions.
- No fresh PRD. Maintenance work arrives as bug reports, small features, refactors, polish.
- Workflows must operate from sparse input (a sentence, a Linear ticket, a Slack message).
- Quick-dev Mode B (direct instructions) is the natural fit — but only behind the grounding gate.

Most of the 13 projects live in brownfield. The fork's safety changes are explicitly designed for this.

## What's Shipped

These are live in the fork (subject to STATUS.md confirmation):

- **Grounding gate** in quick-dev Mode B — closes the "fuzzy ask → invented work" failure chain.
- **Autonomy scoping** (decision vs intent) — explicit in `autonomous_mode`.
- **Brief provenance contract** — applies to design pipeline regardless of phase, but especially valuable in brownfield where briefs accumulate over time.

## What's Designed (Not Yet Built)

These are described in design notes but not coded — verify against STATUS.md.

### `project_phase` config flag

Idea: add `project_phase: greenfield | brownfield | mixed` to `_bmad/bmm/config.yaml`. Workflows branch behavior based on phase. Examples:
- Greenfield: assume PRD/epics/stories exist; fail loudly if missing.
- Brownfield: do not assume those artifacts; route through maintenance-oriented entry points.
- Mixed: support both, infer from context per workflow invocation.

### Quick-dev split: `spec-dev` vs `direct-dev`

Idea: replace the single quick-dev entry with two explicit entry points.
- `spec-dev` — artifact-first. Requires a spec/story. The current Mode A path, made explicit.
- `direct-dev` — direct instructions. The current Mode B path with grounding gate, made explicit.

Benefit: removes the ambiguity of "which mode am I in?" and makes the safety boundary visible at the entry point.

### Maintenance pipeline

Idea: `maintenance-triage → tech-spec → spec-dev` as the brownfield equivalent of `quick-spec → quick-dev`.
- `maintenance-triage` — accepts sparse input (ticket, bug report, Slack message), classifies it, decides whether it needs a tech-spec.
- `tech-spec` — produces a lightweight artifact suitable for `spec-dev` to consume. Not a full PRD.
- `spec-dev` — executes against the tech-spec.

This gives brownfield work a first-class surface instead of routing everything through `direct-dev` and relying on the grounding gate to catch issues.

## Authoring Implications

When writing or reviewing a workflow, ask:

- **Which phase is this workflow for?** If it assumes PRD/epics/stories, it's greenfield-only. Say so in its description.
- **Does it accept sparse input?** If yes, it needs the grounding gate.
- **Does it propagate phase awareness downstream?** If a workflow produces output that another consumes, the consumer should know what phase produced it.

## Diagnostic Implications

When diagnosing a workflow failure, ask:

- **Was this a brownfield invocation of a greenfield-biased workflow?** Common root cause. Symptom: workflow halts looking for an artifact that doesn't exist, or invents one.
- **Was the grounding gate bypassed?** Possible if the workflow is older than the gate or has a code path that skips it.
- **Are we in the gap between designed and shipped?** Some maintenance scenarios are designed but not built. The user may be hitting the unshipped surface.
