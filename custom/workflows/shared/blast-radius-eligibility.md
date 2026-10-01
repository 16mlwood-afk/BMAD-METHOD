# Blast-Radius Eligibility — quick-dev's scope ceiling

**What this is:** a shared classification fragment that quick-dev runs **once, before any edits**, to confirm the task still fits quick-dev's contract — *small, decided work shipped end-to-end*. A run that silently outgrows that contract is a workflow-integrity failure, not just a big change. This fragment halts/reroutes before that happens.

**Where it runs:** step-03 §0, the single funnel both modes pass through (Mode A: step-01→03; Mode B: step-01→02→03). By step-03 both modes have their context — Mode A from the tech-spec, Mode B from step-02 — so the classification is based on the *actual intended change surface*, not the wording of the prompt.

**Relationship to the other gates:**

- The step-01 **grounding gate** decides *whether intent exists*. This fragment decides *whether the work fits the workflow*. They are orthogonal — grounding can pass while eligibility fails.
- The step-01 **escalation threshold** (Mode B, linguistic) is a cheap *early* reroute on prompt wording. This fragment is the **authoritative** check on real surface. Keep both; this one wins on conflict.
- This fragment is the PROBABILISTIC awareness/early-exit tier. The **deterministic guarantee** is the `quick-dev-blast-radius-check` script invoked at step-07 (and, where wired, at pre-push) against the observed diff. Prose cannot guarantee the model classifies honestly; the script enforces on truth. Do not treat this fragment as the ceiling — it is the *legibility and early-exit* layer in front of the ceiling.

---

## CLASSIFY (state this explicitly before proceeding)

Classify the task into exactly one band, and **state the band + the one-line reason** so step-07 can echo it:

- **`tiny-patch`** — a handful of files, no structural surface. Proceed.
- **`contained-feature`** — a cohesive feature in one area, within quick-dev's reach but at the edge. Proceed, but the regression surface check (step-04 §6) is non-negotiable.
- **`not-quick-dev`** — crosses a HARD trigger below, OR carries 2+ soft signals with genuine uncertainty about scope. **Do NOT execute.** Reroute.

### HARD triggers — ANY one → `not-quick-dev`

The change is intended to touch:

1. **Database schema or a migration** — new/renamed/dropped columns or tables, a migration file, a Drizzle/Prisma/SQL DDL change. *(One recognized exception: the Mode-A gated-migration carve-out below. It does NOT loosen triggers 2–5.)*
2. **Auth / permissions / access control** — login, session, role/scope checks, middleware that gates access, API-key handling.
3. **Payments / billing / money** — charge, invoice-total, ledger-writing, or pricing logic.
4. **Shared infrastructure / platform boot** — worker/queue registration, instrumentation/bootstrap, env/secret wiring, deploy config, anything in the cross-boundary schema registry.
5. **File-count / diff size over the project threshold** — more files or lines than `quick_dev.max_files` / `quick_dev.max_diff_lines` in `_bmad/bmm/config.yaml` (defaults: 15 files / 600 lines).

### SOFT signals — 2+ with real scope uncertainty → `not-quick-dev`

Multiple subsystems at once (UI + API + data); "how should I" / "best way to" framing; multi-day framing; a tech-spec (Mode A) that enumerates many affected callers across areas.

> **Recognized blind spot — stringly-typed registries.** This classification (and the §6 regression-surface trace it feeds) reasons about *symbol* dependencies. A change that ADDS a member to a source-of-truth set (report types, feature flags, status vocabularies, columns) can silently drift a hand-maintained registry that mirrors that set by **bare string** — e.g. a `raw-records/data.ts` catalog whose `reportType` is a plain string, not an import of the enum. A symbol grep finds nothing, so it does not raise scope here. This is NOT a `not-quick-dev` trigger; it is a completeness check the §6 regression surface must run by VALUE (grep the literal), not by symbol. Named so a stringly-typed mirror is not mistaken for "no blast radius."

---

## ON `not-quick-dev` — reroute (this OVERRIDES `autonomous_mode`)

> **Mirrors the grounding gate.** `autonomous_mode` grants *decision* autonomy (which file, which pattern), not *scope* autonomy (turning a schema/auth/payments/infra change into a "quick" one). If a HARD trigger fires, halt and reroute **regardless of `autonomous_mode`** — exactly as the grounding gate does. Honesty caveat: this override is prose, so it is probabilistic; the deterministic backstop at step-07 is what actually fences an autonomous run that ignores this.

1. State plainly which trigger/signals fired and the band: *"This is `not-quick-dev`: it touches a database migration (HARD trigger 1). Quick-dev ships small, decided work; a schema change needs planning."*
2. Reroute:
   - HARD trigger or "needs a plan" → **`quick-spec`** (`{project-root}/_bmad/bmm/workflows/implement/quick-spec/workflow.md`).
   - Genuinely platform/system-scale → the full BMad PRD flow.
3. **Do NOT proceed to the execution loop.** **EXIT quick-dev.**

**Override-with-logging.** If the user explicitly says proceed anyway, continue — but log the override (which trigger, the user's confirmation) into your summary so it lands in the PR. Never silently override.

---

## Mode-A gated-migration carve-out — the one recognized exception to HARD trigger 1

A Mode-A run is handed a complete tech-spec. When that spec **already contains the migration plan** the reroute would force you to go produce, HARD trigger 1 firing `not-quick-dev` sends you to `quick-spec` to generate a plan you are already holding — a deterministic mis-fire on a legitimately quick-dev-shaped input. This carve-out names that exact shape so it doesn't require an ad-hoc override every run.

**Reclassify as `contained-feature` (NOT `not-quick-dev`) only when ALL of these hold:**

1. The run is **Mode A** (a tech-spec drove it — never a Mode B free-text prompt; a free-text "add a column" has no plan and stays `not-quick-dev`).
2. **Schema/migration (trigger 1) is the ONLY HARD trigger that fired.** If auth, payments, shared-infra, or the file/diff threshold *also* fire, the carve-out does NOT apply — reroute.
3. The spec specifies the migration as **gated: generate-not-apply** — this run writes the migration file but applies **no** DDL to any database; the apply is an explicit, separate, later, gated step — **and sequenced, and carrying a rollback.** If the run would *apply* schema in-band, the carve-out does NOT apply — an applied/unplanned migration is the real hazard trigger 1 exists for, and it stays fenced.
4. The change otherwise fits `contained-feature` (cohesive, one area, within the file/diff thresholds).

**This is the edge band, not a free pass:** the step-04 §6 regression-surface check is non-negotiable, and **you MUST still satisfy the deterministic backstop honestly.** The step-07 `quick-dev-blast-radius-check` script sees the migration file in the diff and will fire trigger 1 against truth regardless of this prose. Do not silently bypass it — proceed under its existing override path by setting `QUICK_DEV_OVERRIDE` to the carve-out reason, e.g. `QUICK_DEV_OVERRIDE="Mode-A gated-migration carve-out: spec §<n> pre-plans generate-not-apply + sequenced + rollback; no DDL applied this run"`. The gate then still fires-and-records (the reason lands in the run record), rather than being defeated. The carve-out makes this override the **documented default for this shape**, not a thing the agent must remember to reach for — but it never removes the deterministic check or its logging.

State it explicitly, same as any band: *"`contained-feature` via the Mode-A gated-migration carve-out — spec §<n> pre-plans the migration generate-not-apply, sequenced, rollback present; trigger 1 only; backstop override reason recorded."*

---

## ON `tiny-patch` / `contained-feature` — proceed

Record the band + reason (one line) for step-07's eligibility echo, then continue with step-03's execution loop.
