---
name: 'step-01-frame-inventory'
description: 'Download/locate the design source, extract tokens + layout constraints, and build the frame inventory. No section enumeration yet — that is step-02''s fan-out.'
---

# Step 1: Frame Inventory

**Progress: Step 1 of 3** — Next: Fan-out section enumeration (autonomous), then a manifest + handoff pause.

**Kickoff — say hello in your own words (2–3 plain sentences, not a status line).** Tell the user what you're about to do, the way you'd explain it to a colleague: you'll open the design and go through it screen by screen, list out every section so nothing slips through the cracks, and then stop and show them the list before a single line of code gets applied. Mention that the heavy reading happens off to the side (one pass per screen) so it stays thorough. Don't recite step numbers or variable names — just talk. Then carry on.

## RULES

- Autonomous. No user interaction in steps 01–02.
- Branch on `{input_kind}` (set by workflow Input Resolution): `claude_design_url` → download+extract; `synthesize_bundle` → read the bundle dir. Never mix.
- If download fails (URL path), retry once, then report and stop.
- This step builds the FRAME inventory only. Do NOT enumerate sections here — that is step-02, where each frame gets its own isolated context so the whole bundle never sits in one.

---

## 1. Locate the design source → `{design_dir}`

**URL path:** download and extract exactly as `design-implement` step-01 URL.1 (gzip/tar/HTML handling), then `find … -name "*.html"` to locate the project directory. Store as `{design_dir}`. **On the DesignSync (`claude_design`) MCP path (`claude.ai/design/p/<uuid>`), mirror each `get_file` to disk via the context-free persist mechanism in `design-implement` step-01 URL.1b step 3 — never paste `get_file`'s return value through context, or a large bundle blows the very context budget this fan-out exists to protect.**

**Bundle path:** `{design_dir} = {bundle_dir}`; verify `manifest.yaml` + `tokens.css` + at least one `<screen>.html` exist (halt with the malformed-bundle diagnostic if any is missing).

## 2. Layout constraints → `{design_layout_constraints}`

Source the page-shell framing rule in precedence order, authoritative from the project `docs/design-policy.md` (root or `inventory-manager/docs/`), corroborated by the bundle README / wrapper — identical to `design-implement` URL.2. Record `{ source, assertion, resolved:{width,centered,padding}, authoritative }`. This carries into the manifest and downstream into `design-implement` step-03 §2d. If the policy is unreadable, fall back to README/wrapper and mark `authoritative: false`.

## 3. Tokens → `{design_tokens}`

Extract radii / type scale / colors / spacing from the token source (`theme/tokens.jsx` on the URL path; `tokens.css` on the bundle path). Resolve token references to numeric values. Same as `design-implement` URL.4 / BUNDLE.3.

## 4. Frame inventory → `{design_frame_inventory}`

Build the complete frame set the target surface delivers or consumes — the primary frame plus every drilled detail drawer and §13 expand-in-context lookup. Derive exactly as `design-implement` URL.3a:

1. **`<script src>` frame modules + their comments** ("… frames/lookups consumed").
2. **Per-frame banners inside the traced modules** (`/* ===== warehouse-lookup ===== */`).
3. **Lookup→target maps in the bundle data** (`app.jsx` lookup→`<frame>.html` maps).
4. **Sibling standalone `<frame>.html` the target links to.**

Each entry: `{ frame, role: primary|drilled-detail|§13-lookup, parent, declared_in, drawn }`. The primary frame (the target file) is row 0, `role: primary`. A frame declared in a comment/map but with NO module and NO standalone HTML is `drawn: false` (it carries into the manifest and downstream §2f as FRAME NOT DRAWN — routed, never inferred).

On the bundle path, the frame inventory comes from `{bundle_manifest}.screens` + the `data-region` roots; same `{ frame, role, drawn }` shape.

## 5. Derive `{target_slug}` + supersede awareness → `{handoff_supersede_status}`

The surface identity is known once the primary frame is in hand. Derive `{target_slug}` by kebab-casing the surface the design targets (primary frame, row 0). **Prefer an exact match to an existing brief's `target_slug`** when the surface clearly corresponds — the slug is the join key to the brief, so matching the brief's slug (not inventing a near-miss) is what makes the supersede check work. This slug names the manifest (`design-ingest-<target_slug>.md`) AND keys the supersede check below.

Then resolve the handoff's supersede status against the briefs on disk — the "cope with a superseded handoff" contract (workflow Critical Rules; `brief-revision-policy.md` §8). This is autonomous and silent; the *reporting* happens at the step-03 pause.

1. List briefs in `{implementation_artifacts}` whose Block-A `target_slug` matches `{target_slug}` (read frontmatter per `brief-revision-policy.md` Block A). If the surface does not confidently correspond to any brief's `target_slug`/`route`, do NOT force a match.
2. Set `{handoff_supersede_status}`:
   - **No confident match** → `no_brief`. A raw-URL/bundle run with no brief on disk: supersede CANNOT be known. Record it; do NOT infer `active`.
   - **Exactly one match, `brief_status: active`** → `active`. Normal flow. `{source_brief}` = that file.
   - **The matched brief is `brief_status: superseded`** → `superseded`. Set `{superseded_by}` = the matched brief's `superseded_by` (the active successor it names). `{source_brief}` = the superseded file.
   - **More than one `active` for the slug** → `ambiguous`. The active-uniqueness invariant (`brief-revision-policy.md` §2.6) is already broken upstream. Record it and carry the list; do NOT block — ingest is non-destructive and surfacing it at the pause is enough.
3. Capture `{source_brief}` provenance (`brief_status`, `change_class`, `last_modified_by` / `last_modified_date`) for the manifest receipt stamp (step-03 §1).

**Do NOT refuse on any value.** This step records the status; step-03 stamps it into the manifest and leads the pause with it. Tolerance is the whole point — the hard refuse belongs to brief *consumers*, not to this non-destructive cataloguer.

## 5a. Concurrent-run check — fail BEFORE the fan-out, never after it

`{target_slug}` is a **canonical collision key**: two sessions ingesting the same surface provably compute the same slug and therefore the same output path (`{implementation_artifacts}/design-ingest-<target_slug>.md`). The slug is in hand HERE, one step before the most expensive phase in the workflow. Run the check now — the entire point is to fail *before* the spend, not to discover the duplicate at the manifest write.

**Why this exists (2026-07-20, cash-recovery).** Two sessions ran a full ~13-frame fan-out on the same design in parallel, ~1M output tokens each, to produce two versions of one manifest. The duplicate surfaced ONLY because the Write tool happened to refuse ("File has not been read yet") after the other session had already written and staged the identical path. That was an accidental save, not a designed one — without it the later write silently clobbers another session's staged, in-flight work. The cost curve is inverted against the operator: this workflow is deliberately routed the LARGEST surfaces (the size preflight sends anything >=5 frames / >=60KB here), so the bigger the job, the wider the collision window and the larger the loss.

Two probes, cheapest first. Neither writes shared state; neither blocks on failure.

**1. Output-path probe (no shared state, always run).** Record `{run_started_at}` (UTC, from the harness clock) at the top of this step. Then:

```bash
test -e "{implementation_artifacts}/design-ingest-{target_slug}.md" && \
  stat -f '%m %N' "{implementation_artifacts}/design-ingest-{target_slug}.md"
```

- **Absent** → no concurrent run detectable by this probe. Continue.
- **Present and OLDER than `{run_started_at}`** → a prior completed ingest, not a concurrent one. This is a **re-ingest**, which is legitimate. Note it for the step-03 pause ("this supersedes an earlier manifest from `<date>`") and continue. **If you ARCHIVE the prior manifest under a new filename rather than overwriting it, you owe it a restamp — see below.**

**Restamp the archived manifest (re-ingest only).** A re-ingest that PRESERVES the prior manifest — renaming it to `design-ingest-{target_slug}-<discriminator>.md` because it carries an apply ledger worth keeping — MUST re-resolve **that archived file's own** `supersede_status` / `superseded_by` before continuing. This is not bookkeeping:

- `supersede_status` is the field `design-implement` branches on to refuse a stale apply (`manifest-schema.md` § Supersede stamp: `superseded` → no silent apply; HALT if deltas remain). It is resolved **only here, and only for the manifest this run is writing.** Nothing in the workflow ever revisits an existing one.
- So an archived manifest keeps `supersede_status: active` **permanently**, while the brief it was built from is now superseded. A later session that opens the archived file — by filename, by a resume, or by following an inbound reference — reads `active` and proceeds normally. That is exactly the silent apply of a superseded design the stamp exists to prevent, reached through the one path that never restamps.

Set on the archived file: `supersede_status: superseded`; `superseded_by: <successor BRIEF filename>` (a brief — per the schema table, NOT the successor manifest); `successor_manifest: <the re-ingest that archived it>`; and a one-line note stating whether its applied rows transfer (they do not when `bundle_shape` differs). Take the manifest marker before writing, as for any ledger edit.

**Then report inbound references.** The rename silently retargets every pointer that cited `design-ingest-{target_slug}.md` — reachability allowlists, story files, briefs, code comments — because the un-discriminated name now resolves to the NEW manifest, so the reference keeps resolving while meaning something else. Grep the project for the un-discriminated filename and list the hits in the step-03 pause. Do **not** rewrite them from here: some sit outside this workflow's blast radius (application source, other workflows' artifacts), and naming them is the deliverable.
- **Present and NEWER than `{run_started_at}`** → the file appeared *during* this run. That is proof of a concurrent session on the same slug. **STOP before step-02.** Surface it plainly: another session is ingesting this same surface and has already written `design-ingest-{target_slug}.md`; running the fan-out now would spend a full multi-agent pass to produce a duplicate and then race that session's write. Ask whether to abandon this run (default), or to continue deliberately under a distinct slug.

**2. Register probe (advisory, run when the register exists).** Resolve the canonical register at `$(git rev-parse --git-common-dir)/../.claude/wip-register.yaml` — the **main checkout** copy, never the worktree copy, so a claim takes effect with no commit/push. If it exists and parses, look for a **live** claim on surface `design-ingest:{target_slug}` held by a different `claimed_by_session_id`. If found, SURFACE it and stop, same as probe 1.

**Fail OPEN on every ambiguity.** An unreadable register, an unparseable claim, a missing `git rev-parse`, or an ambiguous own-identity is **UNKNOWN, not clear** — warn in one line and continue. Never auto-release another session's claim, and never treat a future-dated or malformed `claimed_at` as young (the "youngest claim wins" failure mode named in the register's own design v3). This probe adds awareness; it is not a gate, and it must never become the reason a legitimate solo run cannot start.

**Do NOT hand-write a claim into the register from here.** Claim writes are harness-stamped by contract (`claimed_by_session_id` and `claimed_at` are written by the mediating writer, never self-reported) — an agent appending a claim by hand produces exactly the unattributable claim the register cannot honour. Read-only here is deliberate.

## 5b. Net-new existence probe — is there anything to implement against at all?

`design-implement` already runs this probe and **soft-exits on it before reading a single row**. Running it only there means the *cheap* consumer refuses what the *expensive* producer has already paid for in full. This workflow is deliberately routed the LARGEST surfaces (the size preflight sends anything >=5 frames / >=60KB here), so the ordering is inverted against the operator exactly as it is for §5a — same cost curve, same fix. The slug is already in hand; probe here, one step before the fan-out.

**Why this exists (2026-07-28 `/stock`; again 2026-07-31 `intake-pilot-console`).** Both completed a full ingest — 8 frames / 70 sections, then 9 frames / 65 sections — and both were soft-exited by `design-implement` at its existence gate before it read a row. The second cost *more* than a normal ingest: its per-frame fan-out could not run (sub-agents cannot reach the design MCP — `FG-2026-07-26-01` / `-06`), so every source module came through a single orchestrator context. And it had already computed the answer — the manifest carried a hand-written `F-NET-NEW` flag saying *"design-implement would be NET-NEW CREATION, not a delta apply"* — while still handing off as ready to implement. **The fact was in the artifact; nothing made it terminal.** That is the half this section fixes, and it is smaller than "teach ingest to detect net-new."

Three probes, `ls`-class, **run against `origin/main`, not the working tree** (`FG-2026-07-28-06`). A long-lived branch reports a false ABSENCE, and false-absence is the direction that fires this gate — so probing the checkout would make the gate fire on surfaces that exist.

1. **Route** — no route / nav entry matches `{target_slug}` or its route in the app's router or nav config.
2. **Page component** — no page / screen component file exists for the surface.
3. **Backing object** — no schema table and no shared type exists for the surface's primary object.

**Verdict — probes 1–2 decide it; probe 3 never vetoes.** A backing object alone is not a surface, and this section's own recommended path CREATES the schema-present / route-absent state — so an all-three-absent trigger would disarm the gate for precisely the operator who followed the advice.

- **Probes 1–2 both absent** → `{surface_existence} = net-new-surface`. Record what probe 3 found: it scopes the *recommendation* (the backend step may already be done), never the *verdict*.
- **Probes 1–2 present** → `{surface_existence} = brownfield`. Continue normally.
- **Probe unresolvable** → `{surface_existence} = unknown (probe failed, failed open)`. Warn in one line and continue. Unreadable is UNKNOWN, not clear — same discipline as §5a.

Do **not** re-run `design-implement`'s capability-granularity probes (4–6) here. Those classify a capability layered on an *existing* surface and need the brief/spec pair the consumer resolves; duplicating them would let the two gates drift apart, which is the failure this repair closes.

**On `net-new-surface`, STOP before step-02 — soft, never a hard refuse.** Ingest is the tolerant half (workflow Critical Rules) and the operator keeps the wheel, exactly as in `design-implement`'s early-exit. Say it plainly: this surface has no route and no page component, so a full enumeration would catalogue against something that cannot be applied yet. Name the onboarding path (build the minimal backend → brownfield `design-handoff` → `design-synthesize` → `design-implement`), name whichever of those steps probe 3 shows is already done, and offer to continue deliberately.

**If the operator continues anyway, the determination is TERMINAL for how the manifest PRESENTS ITSELF.** Carry `{surface_existence}` into the receipt (`ingest.surface_existence`, `manifest-schema.md`) and into the step-03 pause. A manifest built over a net-new surface may be handed off as a **catalogue**; it may **not** be handed off as ready to implement. Writing the fact into a flag while the handoff still reads READY is precisely what happened on 2026-07-31 — a determination the artifact records but the handoff contradicts is not a gate.

## 6. Tell the user what you found, then hand to step-02

Say it conversationally — lead with a sentence a colleague would say, not a table. Name the screens plainly (the worklist, the order drawer, the lookups), how many there are, and which are actually drawn vs. only referenced. If a screen that should be there looks missing, or something seems off, say so and tell them you'll keep an eye on it. **If `{handoff_supersede_status} == superseded`, flag it here too** — a quick "heads up, this handoff looks superseded by `{superseded_by}`; I'll still build the manifest but I'll walk you through that at the end" — so it isn't a surprise at the pause. Then say you're about to go through each screen in turn to list its sections.

Keep it brief and human. A compact line or two is plenty — for example: *"Pulled the design — it's got the Supply Orders worklist, the order drawer, and six linked-record lookups (eight screens, all drawn). Layout reads full-width. Going through each one now to list its sections."* The figures below are what you're conveying, not a format to print verbatim:

- source + primary frame: `{design_dir}` / `{target_file}`
- frames: `{N}` declared, `{M}` drawn, `{N-M}` referenced-but-not-drawn (these carry as FRAME NOT DRAWN)
- layout: `{resolved.width}`{, centered if so} (authoritative: `{bool}`)
- tokens cataloged: `{len}`
- sections: not enumerated yet — step-02 fans out one agent per drawn frame

---

## COMPLETION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-ingest/steps/step-02-fanout-enumerate.md`

## SUCCESS METRICS

- `{design_dir}` resolves to the design source on disk.
- `{design_frame_inventory}` non-empty, with the primary frame as row 0 and `drawn` set on every entry.
- `{design_layout_constraints}` populated (authoritative from policy where readable).
- `{design_tokens}` non-empty with resolved values.
- `{target_slug}` derived and `{handoff_supersede_status}` resolved to one of `active | superseded | no_brief | ambiguous` (with `{superseded_by}` / `{source_brief}` captured) — never left unset, never refused.
- The §5a concurrent-run check RAN before handing to step-02, and its verdict is recorded (`no-collision | prior-manifest (re-ingest) | concurrent-detected | unknown (probe failed, failed open)`). A `concurrent-detected` verdict STOPPED the run before the fan-out — the spend is the thing being protected, so detecting the collision after step-02 is a failure even if the manifest is later correct.
- The §5b net-new existence probe RAN before handing to step-02, against `origin/main`, and `{surface_existence}` is set to one of `net-new-surface | brownfield | unknown (probe failed, failed open)` — never left unset. A `net-new-surface` verdict STOPPED the run before the fan-out unless the operator explicitly continued; if they continued, the verdict is carried into the receipt and the step-03 pause, and the handoff does NOT read as ready to implement.
- NO section enumeration attempted in this step (that is step-02's fan-out — keeping the whole bundle out of one context is the point).
