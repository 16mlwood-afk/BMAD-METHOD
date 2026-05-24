---
name: design-implement
description: 'Implement a Claude Design artifact with pixel-level precision. Fetches the design bundle, reads every CSS value, builds a component-by-component comparison grid against the existing implementation, then fixes all deltas.'
main_config: '{project-root}/_bmad/bmm/config.yaml'
---

# Design Implement Workflow

**Goal:** Take a Claude Design artifact URL and bring the codebase into pixel-perfect alignment with the design — measured by an exhaustive component × property comparison grid, not by eyeballing.

**Your Role:** You are a pixel-precision engineer. You do not design — you enforce. The Claude Design artifact is the authoritative specification. Your job is to extract every CSS value from the design source, compare it against the implementation, enumerate every delta, and fix all of them. A delta that slips through is a failure.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture** for focused execution:

- All 4 steps are FULLY AUTONOMOUS — no user interaction after invocation
- State persists via variables (see below)
- Sequential progression: ingest design → map implementation → build grid → apply and deliver

### State Variables

- `{design_url}` — Claude Design artifact URL provided by the user
- `{design_file}` — Target design file name (e.g., `Data Quality Dashboard.html`)
- `{design_dir}` — Extracted bundle directory on disk
- `{design_components}` — Map of component name → file path within the extracted bundle
- `{design_tokens}` — Design system tokens (radii, type scale, colors, spacing)
- `{impl_page}` — Path to the SvelteKit/React/Vue page component in the codebase
- `{impl_components}` — Map of component name → file path in the project
- `{impl_config}` — Tailwind/CSS config path and key overrides (border-radius, colors, etc.)
- `{comparison_grid}` — The full component × property delta table
- `{delta_count}` — Number of properties with non-zero deltas
- `{baseline_commit}` — Git SHA before any changes

### Step Processing Rules

1. **READ COMPLETELY**: Always read the entire step file before taking any action
2. **FOLLOW SEQUENCE**: Execute all numbered sections in order — no skipping, no optimizing
3. **ALL STEPS ARE AUTONOMOUS**: Never halt, never present menus, never wait for input
4. **SAVE STATE**: Carry variables between steps
5. **LOAD NEXT**: When directed, read fully and follow the next step file

### Critical Rules

- **The design artifact is the single source of truth.** If the design says `border-radius: 4px` and the implementation says `rounded-lg` (which maps to `10px`), the implementation is wrong — full stop.
- **Read the design source code, not screenshots.** JSX inline styles and token files contain exact values. Screenshots lose precision.
- **Check Tailwind config overrides.** A class like `rounded-sm` doesn't mean 2px — it means whatever the project's `tailwind.config.js` maps it to. Always resolve through the config.
- **Enumerate exhaustively.** Every CSS property on every component. The value of this workflow is that nothing slips through. Sampling is failure.
- **N/A is a valid cell.** If a property exists in the design but the implementation doesn't have that component, or vice versa — mark it, don't skip it.

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`
- `autonomous_mode`, `autonomous_rules`
- `implementation_artifacts` path
- `date` as system-generated current datetime
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

### Input Resolution

The user provides:

- **Claude Design artifact URL** — required. Format: `https://api.anthropic.com/v1/design/h/...`
- **Target file name** — optional. If not specified, the workflow reads the bundle's README to identify the primary design file.

Store as `{design_url}` and `{design_file}`.

### Paths

- `installed_path` = `{project-root}/_bmad/bmm/workflows/implement/design-implement`

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/implement/design-implement/steps/step-01-ingest-design.md` to begin.
