---
name: 'step-03-emit-tech-specs'
description: 'For each prioritized cluster, emit a small tech-spec artifact and route to quick-spec or quick-dev'
---

# Step 3: Emit Tech-Specs

**Goal:** Convert prioritized clusters into actionable tech-spec artifacts. Each cluster becomes one short markdown file that can be picked up by quick-spec (for further investigation) or quick-dev directly (when the change is already clear).

---

## AVAILABLE STATE

- `{signals}`, `{clusters}`, `{prioritized}` — from prior steps

## STATE VARIABLES (set in this step)

- `{emitted_spec_paths}` — list of paths written

---

## SEQUENCE OF INSTRUCTIONS

### 1. Route Each Cluster

For each cluster in `{prioritized}`, decide the downstream workflow:

- **Direct quick-dev** — if the cluster is concrete enough that step-02 of the gathering already named the file + the change in plain English (e.g., "queries page filter resets on refresh — `src/routes/queries/+page.svelte` line 88 doesn't read URL state on mount"). The signal IS the verb-target pair quick-dev's GROUNDING GATE asks for.

- **quick-spec first** — if the cluster names a symptom but not a concrete fix (e.g., "expense import feels slow"). It needs investigation. Quick-spec will produce a proper tech-spec; quick-dev runs against that.

When in doubt, route to quick-spec. It's the safer brownfield path — investigation is cheap, fabricated solutions are expensive.

### 2. Write Triage-Spec Artifacts

For each cluster, write a short markdown file to `{implementation_artifacts}/triage-{cluster_id}-{YYYY-MM-DD}.md`:

```markdown
---
name: triage-{cluster_id}
theme: {theme}
score: {score}
severity: {s}
frequency: {f}
effort: {e}
route: quick-spec | quick-dev
emitted_at: {YYYY-MM-DD}
source_signals: {signal_ids}
---

# {theme}

**Score:** {score} (severity {s} × frequency {f} ÷ effort {e})

## Raw signals

{quoted user reports / telemetry excerpts / etc., one per bullet, with source}

## Hypothesis

{1–3 sentences. What you currently believe is happening, based on the signals
and any quick grep you did. Be honest about confidence level — "I think X
because Y" beats stating Y as fact.}

## Suggested next workflow

{
  If route=quick-dev:
    Run `quick-dev` with: "{the verb-target instruction quick-dev needs}"

  If route=quick-spec:
    Run `quick-spec` with: "{the problem statement quick-spec investigates}"
}

## Rollback note

{If quick-dev: one sentence on how to revert.
 If quick-spec: leave blank; quick-spec will fill it during §4b.}
```

Keep these files short. They're triage artifacts, not full specs. The full spec (if needed) comes out of quick-spec downstream.

### 3. Hand Off

Display to user:

```
**Emitted {n} triage-spec(s):**

1. {path} → run: /bmad:bmm:workflows:{quick-spec|quick-dev} {path}
2. ...

These are ordered by score. Work the highest first unless something
external (e.g., user pinged you about a specific one) reorders the list.

Below-threshold clusters were logged in step-02 but did NOT get artifacts.
If any of them turn out to matter, drop them in again next triage.
```

If autonomous mode, do NOT auto-invoke the downstream workflows from here. Triage emits the queue; the user (or a separate invocation) drives the queue. This boundary is intentional — it prevents one triage run from cascading into N hours of unattended implementation.

### 4. Done

This workflow ends here. No further steps. The triage-spec artifacts are the handoff.

---

## SUCCESS METRICS

- Every cluster in `{prioritized}` (above threshold) has a written triage-spec
- Each triage-spec has a clear next-workflow recommendation
- User sees a ranked list of paths to act on
- No downstream workflows auto-invoked

## FAILURE MODES

- Bundling multiple clusters into one mega-spec (defeats the small-units design)
- Auto-invoking quick-dev for all clusters under autonomous_mode (intent autonomy violation; user must drive the queue)
- Writing speculative "Hypothesis" content that goes beyond what the signals support
- Forgetting the rollback note on direct-to-quick-dev routes
