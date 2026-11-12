---
name: 'step-04-route'
description: 'Map the assessment to a placement verdict, write the decision artifact, surface the net-new-scope veto, and emit the exact design-handoff invocation (carrying --placement) — without auto-invoking it'
---

# Step 4: Route to a Placement Verdict

**Progress: Step 4 of 4** — Final step

## RULES — read before acting

- **DO NOT auto-invoke `design-handoff`.** This workflow emits the decision + the exact next command; the user (or a separate invocation) runs it. This boundary mirrors `maintenance-triage` — it prevents one triage from cascading into unattended design work.
- **Net-new scope is veto-surfaced, not silently committed.** A `tab` or `sibling-page` verdict adds surface area. In interactive mode, surface it for veto before finalizing. Under `autonomous_mode`, *surface-and-proceed* (the veto concept is design-handoff §5b `recommended-new`; the surface-and-proceed behavior mirrors §5d) — recommend the home, record `is_net_new_scope: true`, and let the user veto after the fact.
- The verdict comes from the assessment in steps 02–03 — do not re-open the brains here.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

## AVAILABLE STATE

From steps 02–03: `{band_belongs}`, `{topology_verdict}`, `{surface_hierarchy}`, `{analytics_shape}`, and any short-circuit `{placement_verdict}` (`no-surface`/`remove-band`). From step-01: `{target_route}`, `{analytics_question}`, `{existing_band}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Decide the placement verdict

If a short-circuit already set `{placement_verdict}` in step-02 (`no-surface` or `remove-band`), keep it. Otherwise map the assessment:

| Condition | `{placement_verdict}` |
|---|---|
| `{band_belongs}` = `none` (step-02 short-circuit) | `no-surface` |
| `{band_belongs}` = `recommended-drop` (step-02 short-circuit) | `remove-band` |
| band belongs AND `{topology_verdict}` = `single-page-appropriate` | `band` |
| band belongs AND `{topology_verdict}` = `needs-tab-views` | `tab` |
| band belongs AND `{topology_verdict}` = `needs-sibling-route` | `sibling-page` |
| `{topology_verdict}` = `unresolved` | *do not decide* → go to §1a |

Set `{is_net_new_scope}` = `true` when the verdict is `tab` or `sibling-page`, else `false`.

#### 1a. Unresolved topology — surface the fork, do not guess

If `{topology_verdict}` = `unresolved`, do NOT pick a home. Surface the two co-equal jobs to the user. Resolve per the §5d ground-or-flag rule (which §5e's hierarchy routing also points back to): a deliberate mode-switch → `tab`; two distinct sub-features → `sibling-page`. In autonomous mode, recommend the more conservative (`tab`) and flag it as unresolved in the artifact. This is the workflow's abstain path — an asked placement beats a guessed one.

### 2. Build the exact design-handoff invocation (carrying --placement)

Set `{handoff_invocation}` to the precise next command the verdict implies. **Always pass `--placement <verdict>`** — and, when a shape was chosen, **`--archetype {analytics_shape}`** — so both the decided home AND the shape are *consumable* by design-handoff (its step-01 §5b/§5d honor the placement and §5c honors the archetype, skipping re-derivation) rather than advisory prose it might silently re-decide:

- **`band`** → `/bmad:bmm:workflows:design-handoff {target_route} --placement band --archetype {analytics_shape}` — the band lands on the operational page; the `operational-analytics-band` skill governs its build. If `{existing_band}` ≠ `none`, note "upgrade the existing band," not "add one."
- **`tab`** → `/bmad:bmm:workflows:design-handoff {target_route} --placement tab --archetype {analytics_shape}` — a distinct analytics tab/mode on the same route.
- **`sibling-page`** → `/bmad:bmm:workflows:design-handoff {target_route}/analytics --placement sibling-page --archetype {analytics_shape}` — a **new analytical surface** (`page_mode: analytical`, NOT operational). This is the net-new-scope case.
- **`remove-band`** → `/bmad:bmm:workflows:design-handoff {target_route} --placement remove-band` — redesign the operational page WITHOUT the ornamental band (a real design task, not a no-op). No `--archetype` (no surface to shape).
- **`no-surface`** → no handoff. State plainly: the data + job do not justify an analytics surface here; stop.

`{analytics_shape}` now rides the command as `--archetype` — design-handoff §5c honors it and skips re-selection (the shape was chosen here via the same `analytics-surface-architect` skill — honored upstream-first, not re-derived). Carry `{surface_hierarchy}` into the invocation note as context for a multi-surface page.

### 3. Write the placement-decision artifact

Render `../template.md` to `{decision_artifact_dir}/analytics-placement-{target_slug}-{date}.md` (derive `{target_slug}` from `{target_route}`: strip slashes, lowercase, `/`→`-`). Substitute every `{{variable}}` from state. Store the path as `{decision_artifact_path}`. This artifact is a triage record — NOT a brief; it carries no brief provenance block and is not consumed by the provenance contract.

### 4. Hand off (do not auto-invoke)

Display to the user:

```
**Placement verdict: {placement_verdict}** for analytics on {target_route}.
Why: band-belongs={band_belongs} · topology={topology_verdict} · shape={analytics_shape}.

{If is_net_new_scope: "⚠️ Net-new scope — this adds a {tab|sibling page}. Veto now if the band-on-page option is preferable."}

Next: run
  {handoff_invocation}

Decision artifact: {decision_artifact_path}
```

Do not run `{handoff_invocation}` yourself. This workflow ends at the recommendation.

### 5. Done

No further steps. The placement-decision artifact + the surfaced verdict are the handoff.

---

## SUCCESS METRICS

- `{placement_verdict}` set from the steps 02–03 assessment (or carried short-circuit), with `{is_net_new_scope}` correct
- `{handoff_invocation}` is a runnable, target-correct `design-handoff` command **carrying `--placement <verdict>`** (or "no handoff" for `no-surface`)
- Net-new scope was veto-surfaced (interactive) or surfaced-and-proceeded (autonomous) — never silently committed
- Decision artifact written; `design-handoff` NOT auto-invoked
- Unresolved topology was surfaced/asked, not guessed

## FAILURE MODES

- Auto-invoking `design-handoff` (cascade boundary violation — mirror maintenance-triage)
- Omitting `--placement` so the verdict degrades to advisory prose design-handoff re-decides (the consumability gap this workflow exists to close)
- Silently committing a `sibling-page`/`tab` without surfacing the net-new scope
- Emitting a `sibling-page` invocation with `page_mode: operational` (the home and the mode must agree)
- Writing a brief-style provenance block into the decision artifact (it is a triage record, not a brief)
