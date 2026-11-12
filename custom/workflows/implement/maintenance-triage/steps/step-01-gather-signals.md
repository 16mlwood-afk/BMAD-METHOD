---
name: 'step-01-gather-signals'
description: 'Collect production-driven signals from user input and (where available) project-specific signal sources'

nextStepFile: './step-02-cluster-and-prioritize.md'
---

# Step 1: Gather Signals

**Goal:** Build a list of raw production signals that may deserve a tech-spec. Anchor on real inputs — do not invent.

---

## STATE VARIABLES (set in this step)

- `{signals}` — array of raw signal records: `{ source, raw_text, observed_at, suggested_severity }`

---

## SEQUENCE OF INSTRUCTIONS

### 1. Accept User-Provided Signals (always)

Whatever the user provided when invoking the workflow — paste, list, prose — is the primary input. Parse it into one signal per distinguishable concern.

Common shapes the user may drop:

- **User reports** — "Daisy says the queries page filter resets on refresh"
- **Telemetry observations** — "Error logs show 12 timeouts on /api/invoices/match yesterday"
- **Dependency alerts** — "Dependabot opened a high-severity drizzle-orm advisory"
- **Self-observations** — "The expense import feels slow when batch > 50"
- **Recent git churn** — "We touched src/lib/server/amazon/* twice this week with bandaid commits"

Don't dismiss anything as too vague at this stage. Capture it. Filtering happens in step-02.

### 2. Query Project-Specific Signal Sources (where wired up)

Look for documented signal endpoints in this project. Check:

- `CLAUDE.md` for an admin API URL pattern (e.g., the `system-status` action)
- `docs/infrastructure.md` or `docs/PROJECT.md` for dashboards, log search URLs
- `_bmad-output/analysis/` for recent audits with named pain points

If a low-cost read endpoint is documented (one that requires no credentials beyond what's already in env), query it for a snapshot. Add findings to `{signals}` with `source: "<endpoint-name>"`.

**Do NOT** invent a query against an undocumented endpoint. If no signal source is wired up for this project, skip this section silently.

### 3. Tag Each Signal

For each signal, attach:

- **source**: where it came from ("user-input", "admin-api:system-status", "dependabot", "git-log")
- **raw_text**: the original wording
- **observed_at**: when, if known (`null` is fine)
- **suggested_severity**: `critical | high | medium | low` based on your initial read — refine in step-02

### 4. Halt Condition

If `{signals}` is empty after both sections — no user input and no wired-up source — HALT.

Display:
```
No signals to triage. Paste any of: user reports, recent error log excerpts,
dependency alerts, observations like "the queries page feels slow." I'll
cluster and produce small tech-specs.
```

Do NOT invent signals to keep the workflow moving. This halt overrides `autonomous_mode` (intent autonomy is never granted — see workflow.md).

### 5. Proceed

Print a one-line summary: `Gathered N signals from M sources.`

**NEXT:** Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/maintenance-triage/steps/step-02-cluster-and-prioritize.md`

---

## SUCCESS METRICS

- `{signals}` populated with ≥1 record
- Each signal tagged with source, raw_text, suggested_severity
- No fabricated signals

## FAILURE MODES

- Inventing signals when user provided none and no signal source is wired up (halt instead)
- Treating optimization wishlists as signals (they're not — they're features, route them through quick-spec directly)
- Skipping the tag step (downstream clustering needs the metadata)
