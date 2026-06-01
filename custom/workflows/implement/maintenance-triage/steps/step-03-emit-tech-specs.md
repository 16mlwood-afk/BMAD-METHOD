---
name: 'step-03-emit-tech-specs'
description: 'For each prioritized cluster, decide its shape (code-shaped vs design-shaped), emit a small triage-spec artifact, and route it — code-shaped to quick-spec/quick-dev, design-shaped to a Claude Design paste prompt or design-review/design-elevation'
---

# Step 3: Emit Tech-Specs

**Goal:** Convert prioritized clusters into actionable triage artifacts. Each cluster becomes one short markdown file routed by its **shape**: code-shaped clusters go to quick-spec (for investigation) or quick-dev (when the change is already clear); design-shaped clusters go to a Claude Design paste prompt (when the surface + change are clear) or design-review/design-elevation (when the surface needs design investigation first).

---

## AVAILABLE STATE

- `{signals}`, `{clusters}`, `{prioritized}` — from prior steps

## STATE VARIABLES (set in this step)

- `{emitted_spec_paths}` — list of paths written

---

## SEQUENCE OF INSTRUCTIONS

### 1. Route Each Cluster

For each cluster in `{prioritized}`, first decide its **shape**, then its downstream workflow. The shape gate matters because triage's default instinct is to frame everything as a code change — but a cluster whose real problem is the surface's layout or interaction needs the design family, not a code spec.

**Shape gate (decide first):**

- **Code-shaped** — the fix is logic, wiring, data, or performance; no new visual or interaction design is needed (a filter that resets, a slow import, a null field, a dead handler). Route within the **code lane** below.
- **Design-shaped** — the problem *is* the surface: it's confusing, cluttered, missing an affordance the job needs, or the layout fights the task. Fixing it means (re)designing, not just coding. Route within the **design lane** below. A design-shaped cluster forced into quick-spec/quick-dev produces a *code* spec for work the *design tool* should author — the gap this gate closes.
- **Straddle** — a complaint that's part UX, part bug (e.g. "the recon drawer is read-only AND the variance number is wrong"). Split it into a design-shaped part and a code-shaped part and route each; don't force the whole cluster down one lane.

**Code lane → quick-dev or quick-spec:**

- **Direct quick-dev** — if the cluster is concrete enough that step-02 of the gathering already named the file + the change in plain English (e.g., "queries page filter resets on refresh — `src/routes/queries/+page.svelte` line 88 doesn't read URL state on mount"). The signal IS the verb-target pair quick-dev's GROUNDING GATE asks for.

- **quick-spec first** — if the cluster names a symptom but not a concrete fix (e.g., "expense import feels slow"). It needs investigation. Quick-spec will produce a proper tech-spec; quick-dev runs against that.

When in doubt between these two, route to quick-spec. It's the safer brownfield path — investigation is cheap, fabricated solutions are expensive.

**Design lane → a Claude Design paste prompt, or design-review/design-elevation** (the same concrete-vs-investigate split, one lane over):

- **Concrete → a focused Claude Design paste prompt.** If the surface and the visual/interaction change are clear (e.g. "the orders drawer shows the discrepancy but has no action to resolve it"), emit a paste-ready Claude Design enhancement prompt instead of a code spec. **Build and save it per `{project-root}/_bmad/bmm/workflows/design/shared/claude-design-prompt.md`** (the SoT for its structure, save path, and always-emit-never-invoke rule). This is the design analog of "direct quick-dev" — the signal already names the surface + the change. (If the surface is *settled* and the signal is "it should do more," prefer routing through `design-elevation`, which formalizes this prompt with provenance.)

- **Needs design investigation → design-review or design-elevation.** If the surface "feels wrong" but the fix is unclear, route to **design-review** (a live audit of the surface) for a quality/regression complaint, or **design-elevation** (the "what would make THIS better" pass) when the surface is settled and the signal is "it should do more." This is the design analog of "quick-spec first" — don't fabricate a redesign; investigate first.

When in doubt on a design-shaped cluster, route to design-review — an audit is cheap, a fabricated redesign is expensive.

**Data-quality clusters are root-cause work, not data-patch work.** When a cluster is a data-quality defect — bad, missing, or inconsistent *stored* values (null fields, mislabeled records, format drift, double-counted rows) — the spec's primary deliverable is the fix to the *producing* pipeline (extractor, ingest, importer, sync, migration), NOT a production-data amendment. A one-time backfill of the existing bad rows is a secondary, adjunct task within the same spec — name it as such, never as the spec's sole content. A spec that proposes only "correct the data" will recur the moment the producer writes again. If the producing code isn't yet identified, route to **quick-spec** to find it before any backfill is specified.

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
shape: code | design
route: quick-spec | quick-dev | claude-design-prompt | design-review | design-elevation
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

  If route=claude-design-prompt:
    Paste into Claude Design (no code workflow): "{the paste-ready enhancement
    prompt — connect line, files to read, keep-as-is guard, the change, policy
    constraints}". Save the prompt body below this section so it is copy-pasteable.

  If route=design-review:
    Run `design-review` on: "{the surface/route to audit}"

  If route=design-elevation:
    Run `design-elevation` on: "{the settled surface to deepen}"
}

## Rollback note

{If quick-dev: one sentence on how to revert.
 If quick-spec: leave blank; quick-spec will fill it during §4b.
 If a design route: leave blank — no code changes yet; rollback applies when the
 design returns as code via design-implement/quick-dev.}
```

Keep these files short. They're triage artifacts, not full specs. The full spec (if needed) comes out of quick-spec downstream.

### 3. Hand Off

Display to user:

```
**Emitted {n} triage-spec(s):**

1. {path} → {next-action by route}
     • quick-spec / quick-dev / design-review / design-elevation → run: /bmad:bmm:workflows:{route} {path}
     • claude-design-prompt → paste the prompt in {path} into Claude Design (no workflow to run)
2. ...

These are ordered by score. Work the highest first unless something
external (e.g., user pinged you about a specific one) reorders the list.
Lead each line with the plain next action ("paste into Claude Design" /
"run quick-dev") so the queue is actionable at a glance, not just a list of paths.

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

- Routing a design-shaped cluster to quick-spec/quick-dev (forces a code spec for a design problem — run the shape gate first; design-shaped goes to Claude Design / design-review / design-elevation)
- Bundling multiple clusters into one mega-spec (defeats the small-units design)
- Auto-invoking quick-dev for all clusters under autonomous_mode (intent autonomy violation; user must drive the queue)
- Writing speculative "Hypothesis" content that goes beyond what the signals support
- Forgetting the rollback note on direct-to-quick-dev routes
