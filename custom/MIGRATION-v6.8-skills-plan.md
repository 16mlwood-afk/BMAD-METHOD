# Migration plan — custom corpus → v6.8.0 skills-native layout

**Status:** PROPOSAL with all design decisions resolved (not started). Authored 2026-06-19,
decisions locked 2026-06-19, from the cash-recovery onboarding session.
**Multi-session, touches the provenance layer — execute deliberately, not ad hoc.**

---

## Problem

Upstream BMAD moved to a **skills-based architecture** (v6.8.0). A fresh `bmad-cli install`
emits `.claude/skills/bmad-<name>/` dirs (hand-authored, copied verbatim — there is **no
workflow→skill compiler**), discovered by walking the local `core`/`bmm` module trees for
`SKILL.md`. Refs: `tools/installer/core/manifest-generator.js:110-184`,
`tools/installer/ide/_config-driven.js:408-468`, `tools/installer/project-root.js:64-72`.

The fork's entire custom layer still lives in the **old layout** (`custom/workflows/<group>/<wf>/`,
distributed by `sync-bmad-workflows.sh` into each project's `_bmad/bmm/workflows/`). None of it is
in the skills trees the installer ships from. So every new project installed on v6.8.0 gets vanilla
upstream skills with **none** of the fork's safety layer (grounding gate, brief provenance,
hardened quick-dev, design-*). Confirmed during cash-recovery onboarding. cash-recovery was worked
around by installing on the 6.0.4 base layout + sync overlay (same as all 14 projects).

## Goal

A fresh install + sync produces a project with the **full fork custom layer** as skills, with the
grounding gate / brief-provenance contract intact, fork-hardened workflows winning over upstream
namesakes, and all 14 projects migrated (or running a documented dual-layout transition).

---

## KEY DECISION: deliver via the sync, NOT the installer

The sync already copies `custom/skills/*` → a project's `.claude/skills/` (`sync_skills_for_project`,
`sync-bmad-workflows.sh:263`) — that is how the 4 existing custom skills land. We extend THAT path
rather than building an installer module. Why this beats the installer-module route:

| | Sync-delivered (CHOSEN) | Installer local module (`src/modules/mason/`) |
|---|---|---|
| Code change | 1 small sync edit | patch `findModuleSource` (official-modules.js) + module.yaml + picker |
| Rebase surface | none — all in `custom/` | new code in `tools/installer/` = upstream conflict risk |
| Runs relative to install | AFTER → overwrites upstream skills (last-writer-wins, `rsync -a --delete`) | positional precedence, fragile, duplicate CSV rows |
| Collision resolution | free (last-writer-wins on same dir name) | depends on `--modules` ordering; under-counts skills |
| Proven | yes (4 custom skills today) | no |

**The one required sync change:** `sync-bmad-workflows.sh:822` skips any target whose
`_bmad/bmm/workflows` dir is absent (`SKIP <target> (not found)`) — which gates skills, hooks, AND
CLAUDE.md. Decouple skills/hooks/CLAUDE.md delivery from that check: key per-project work off the
**project root** (derivable from the target path) and only gate the *workflow-overlay* step on the
old dir's existence. After this, a skills-layout project (no old workflows dir) still receives
skills + hooks + CLAUDE.md.

**Bootstrap gap to fix too:** CLAUDE.md section-sync requires the file to already exist
(`:908`, `:1130`). A fresh project has none. The sync (or a bootstrap step) must create CLAUDE.md
from `CLAUDE.md.template` before managing its sections.

---

## Phase 0 — Wire the delivery path (SMALL, do first)

1. Edit `sync-bmad-workflows.sh:822` per above so skills/hooks/CLAUDE.md deliver regardless of layout.
2. Add CLAUDE.md create-from-template when absent.
3. Verify on a throwaway v6.8.0 install: sync delivers the 4 existing custom skills + hooks + CLAUDE.md
   into a project that has NO `_bmad/bmm/workflows`. No corpus work yet — just prove the pipe.

## Phase 1 — Shared-policy home (HIGHEST RISK)

The 12 policies in `custom/workflows/shared/` (5) + `custom/workflows/design/shared/` (7) — incl.
`brief-revision-policy.md` (the provenance contract), `design-standards.md`, `analytics-archetypes.md`
— are referenced by many workflows via relative `shared/...` and old `{project-root}/_bmad/bmm/
workflows/.../shared/` paths.

**DECISION:** deliver them to a fork-owned **`{project-root}/_bmad/bmad-shared/`** dir via the sync
(NOT a fake "skill" — skills must be invocable; a policy bundle isn't). This follows the existing
`{project-root}/_bmad/style-guides/company-voice.md` precedent (already referenced by upstream skills).
Add a sync step that copies `custom/.../shared/*` → `_bmad/bmad-shared/`. All workflow refs rewrite to
`{project-root}/_bmad/bmad-shared/<policy>.md`.
**Gate:** after rewrite, re-verify the 6 intake checks resolve from a consumer skill (Mode-1 review).

## Phase 2 — Path-rewrite rules (mechanical, corpus-wide)

| Old-layout reference | Skills-native target |
|---|---|
| `{project-root}/_bmad/bmm/workflows/<wf>/steps/step-XX.md` (self) | `./step-XX.md` (skill-root relative) |
| `{project-root}/_bmad/bmm/workflows/<group>/<other-wf>/workflow.md` (cross) | sibling skill `bmad-<other-wf>` |
| `{project-root}/_bmad/core/workflows/party-mode/workflow.md` | `bmad-party-mode` skill |
| `{project-root}/_bmad/core/workflows/advanced-elicitation/workflow.xml` | `bmad-advanced-elicitation` skill |
| relative `shared/<policy>.md` | `{project-root}/_bmad/bmad-shared/<policy>.md` |

Genuine project paths stay literal: `{project-root}/_bmad/bmm/config.yaml`, `{implementation_artifacts}`,
`{project-root}/_bmad/scripts/resolve_customization.py` (installer leaves `{project-root}` unexpanded
for runtime — `_config-driven.js:94`). Build the rewrite as a script; don't hand-edit 28 workflows.

## Phase 3 — Port fork-only workflows (LOW RISK, do early)

No upstream name collision → net-new skills, unique names, safe first. Port each into
`custom/skills/bmad-<name>/` (workflow.md → SKILL.md with `name: bmad-<name>` matching the dir;
steps copied; Phase-2 rewrite applied):
- `design/*` (12), `verify/*` (7), `meta/*` (5), `implement/maintenance-triage`, `implement/quick-spec`.

Each: name==dir gate satisfied, Mode-1 self-review against durable principles.

## Phase 4 — Collisions: fork must beat upstream (MEDIUM RISK)

6 fork workflows share a name with an upstream skill: `quick-dev`, `code-review`, `spec`,
`review-adversarial-general`, `review-edge-case-hunter` (+ confirm any others after Phase-3 inventory).

**DECISION — two-tier, prefer the override seam:**
- **Additive hardening** (guardrail `persistent_facts`, pre-flight `activation_steps_prepend`,
  reminders) → ship `{project-root}/_bmad/custom/bmad-<name>.toml` via the sync. This is the
  architecture's intended override seam (`resolve_customization.py`, customize.toml shape) and
  survives upstream skill updates cleanly. Use it wherever the hardening is expressible this way.
- **Deep mid-step logic** the toml can't express (e.g. quick-dev's gated provenance PRE-FLIGHT
  inside step-03) → ship the full `custom/skills/bmad-<name>/` dir; the sync overwrites upstream's
  copy after install (last-writer-wins). **Keep the same dir name** (`bmad-quick-dev`) so it stays
  manifest-tracked by `bmm` and is NOT orphan-removed by installer cleanup (`installed-skills.js`).
- Per collision, pick the lighter tier. Do NOT use unique IDs (`mason-quick-dev`) for collisions —
  users invoke `bmad-quick-dev`; we want to replace it, not run a parallel one. (Unique IDs are only
  for net-new skills, which already have unique names.) Do NOT edit upstream `src/` skills in place.

## Phase 5 — Migrate the 14 projects (dual-layout, pilot-first)

**DECISION:** dual-layout transition, not a big-bang re-install. The sync can populate BOTH the old
`_bmad/bmm/workflows/` overlay AND `.claude/skills/` during transition, so no project is ever broken
mid-migration.
1. Pilot on ONE low-stakes project: sync delivers skills-native layer alongside the existing overlay.
2. Validate: invoke `bmad-quick-dev` + `bmad-design-handoff`, confirm grounding gate + provenance
   frontmatter fire, shared policies resolve.
3. Roll the rest via a bash-driven multi-repo pass (per CLAUDE.md cross-repo-edits guidance).
4. Keep the old overlay until every project is validated on skills; remove it only after cutover.

---

## Verification (every phase)

- Mode-1 self-review of each ported skill (provenance, grounding gate, autonomy scoping).
- Smoke test on a throwaway install (invoke quick-dev + design-handoff; gate + provenance fire).
- `STATUS.md` Now-block + dated Changelog entry; bump skill `last_verified_against_fork_commit`.

## Rollback

Old-layout `custom/workflows/` + sync overlay stay intact until Phase-5 cutover completes. If
skills-native validation fails, projects remain on the working 6.0.4-base + overlay. Nothing is
removed until the replacement is proven.

## Effort

Phase 0 (sync wiring): tiny, ~½ session. Phase 1 (shared rehome + ref rewrite, the careful part) +
Phase 2 (rewrite script): ~1 session. Phase 3 (port 25 fork-only via the script): mechanical,
parallelizable. Phase 4 (6 collisions): small, fiddly. Phase 5 (14 projects): scripted, gated by
pilot. Realistically **3–5 sessions**, front-loaded on the provenance-safe shared rehome.

## Decisions log (was: open questions)

1. **Delivery home** → extend the sync's `custom/skills/` path (NOT an installer module). One edit at
   `sync-bmad-workflows.sh:822` + CLAUDE.md create-from-template. Rebase-clean, proven, collisions free.
2. **Shared policies** → `{project-root}/_bmad/bmad-shared/` via sync (style-guides precedent), not a skill.
3. **Collisions** → customize.toml override seam for additive hardening; same-named full skill dir
   (sync last-writer-wins, stays manifest-tracked) for deep changes. Never edit upstream `src/`.
4. **14-project cutover** → dual-layout, pilot one then scripted rollout; old overlay stays until proven.
