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

**URL path:** download and extract exactly as `design-implement` step-01 URL.1 (gzip/tar/HTML handling), then `find … -name "*.html"` to locate the project directory. Store as `{design_dir}`.

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

## 5. Tell the user what you found, then hand to step-02

Say it conversationally — lead with a sentence a colleague would say, not a table. Name the screens plainly (the worklist, the order drawer, the lookups), how many there are, and which are actually drawn vs. only referenced. If a screen that should be there looks missing, or something seems off, say so and tell them you'll keep an eye on it. Then say you're about to go through each screen in turn to list its sections.

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
- NO section enumeration attempted in this step (that is step-02's fan-out — keeping the whole bundle out of one context is the point).
