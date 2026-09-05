---
name: 'step-02-cluster-and-prioritize'
description: 'Group related signals into clusters, score by severity × frequency × effort, produce a ranked list'

nextStepFile: './step-03-emit-tech-specs.md'
---

# Step 2: Cluster and Prioritize

**Goal:** Turn raw signals into a small ranked list of triagables. The output of this step is a prioritized array of clusters, each of which becomes (or doesn't become) a tech-spec in step-03.

---

## AVAILABLE STATE

- `{signals}` — from step-01

## STATE VARIABLES (set in this step)

- `{clusters}` — array of cluster records: `{ id, theme, signal_ids, severity, frequency_estimate, effort_estimate, score }`
- `{prioritized}` — `{clusters}` sorted by score, descending

---

## SEQUENCE OF INSTRUCTIONS

### 1. Cluster Related Signals

Two signals belong to the same cluster if they share *at least one of*:

- The same affected file/module (e.g., both mention `src/routes/queries/+page.svelte`)
- The same user-facing symptom (e.g., "slow", "wrong number", "filter resets")
- The same root cause (e.g., both stem from "supplier matching returns stale results")

Don't over-cluster. If two reports could be the same bug but the evidence is thin, keep them separate and let step-03 decide whether to merge.

Each cluster gets:
- **id**: short slug (e.g., `queries-filter-persistence`)
- **theme**: one-sentence summary
- **signal_ids**: which `{signals}` belong to it

### 2. Score Each Cluster

For each cluster, assign three values:

**Severity** (1–4): impact on a user if unfixed for a week
- 4: data corruption, security risk, blocking workflow
- 3: visible incorrect behavior, performance regression users notice
- 2: minor UX friction, cosmetic
- 1: housekeeping, only-internal-noticeable

**Frequency** (1–4): how often the symptom is encountered
- 4: every session for most users
- 3: weekly per user
- 2: occasional, narrow audience
- 1: edge case, rare combination

**Effort** (1–4): rough implementation cost
- 4: large refactor, schema change, multi-file
- 3: moderate, 1–2 days
- 2: small, half-day
- 1: trivial, <1 hour

**Score = (Severity × Frequency) / Effort**, rounded to 1 decimal. Higher = do sooner.

These are estimates — not measurements. If you genuinely don't know one of the three, write down what you'd need to find out and score conservatively.

### 3. Build {prioritized}

Sort `{clusters}` by score, descending. Apply two filters:

- **Drop score < 0.5.** Below this threshold the work isn't worth even a quick-spec — note it for the user but don't emit a tech-spec in step-03.
- **Top-N cap: 5.** This workflow is for triage, not exhaustive backlog grooming. If there are more than 5 high-scoring clusters, output the top 5 and tell the user there are N more below the cut.

### 4. Present Triage Summary

Display to user (always, regardless of `autonomous_mode` — they should see what's about to become work):

```
**Maintenance Triage — {date}**

{n_signals} signals → {n_clusters} clusters → {n_emitted} ready for tech-spec.

**Ready for tech-spec (top {n_emitted}):**

1. [score X.X] {theme}
   sev={s} freq={f} effort={e}  •  signals: {signal_ids}
2. ...

**Below threshold (logged, no tech-spec):**

- {theme} — score {X.X}
- ...

**Past the top-N cap:**

- {n} additional clusters above threshold but past the 5-item cap — re-run triage after the first batch ships.
```

If autonomous mode, proceed automatically. Otherwise wait for user to confirm or override priorities.

### 5. Proceed

**NEXT:** Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/maintenance-triage/steps/step-03-emit-tech-specs.md`

---

## SUCCESS METRICS

- Every signal assigned to a cluster
- Every cluster scored on all three axes
- `{prioritized}` produced, capped at top-5
- Triage summary presented

## FAILURE MODES

- Inventing causation between unrelated signals (over-clustering)
- Scoring on gut feel without documenting reasoning
- Emitting all clusters to tech-spec without filtering low-scorers (defeats the point)
