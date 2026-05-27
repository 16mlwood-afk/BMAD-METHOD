---
name: 'step-03-load-frontend-context'
description: 'Detect frontend framework, parse Tailwind config, build the project tokens map, locate prior implementation paths for refine-screen drift baseline.'
---

# Step 3: Load Frontend Context

**Goal:** Discover the project's frontend conventions so step 4 can distinguish real tokens (the project already has them) from invented values (proposed tokens that count against the 5-cap). Without this, synthesis silently invents `var(--*)` names that don't exist anywhere, which breaks `design-implement`'s value resolution.

**Gate owned:** None directly. This step feeds Gate 3 (token cap) in step 4 and the drift baseline in step 6c.

---

## RULES

- **Discovery, not prescription.** This step reads what the project already has. It does NOT decide whether the project SHOULD have Tailwind / token files / a particular framework — those decisions belong to the project, not to this workflow.
- **A missing token file is not an error.** Some projects don't have one. Synthesis falls back to inline `style="..."` values in step 4. The 5-cap on proposed tokens still applies (an inline literal counts as 0 proposed tokens; a `var(--*)` whose name doesn't exist in any project token file counts as 1 proposed token).
- **`bundle/<screen>.html` is always emitted.** Framework-specific scaffolds (`.svelte`, `.tsx`) are *additional* convenience outputs, never replacements. The HTML is what `design-implement` reads.
- **Prior implementation lookup is refine-screen only.** In `fresh-design` mode, skip the prior-impl steps — there is no baseline.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

---

## EXECUTION SEQUENCE

### 1. Detect the framework

Read `package.json`:

```bash
cat {project-root}/package.json | jq '.dependencies + .devDependencies | keys'
```

Classification rules (first match wins):

| Indicator | `{framework}` |
|---|---|
| `@sveltejs/kit` or `svelte` in deps | `svelte` |
| `next` or `react` in deps | `react` |
| `vue` or `nuxt` in deps | `vue` |
| none of the above (or no `package.json`) | `none` |

Store the framework version too (e.g., `svelte: "5.x"`) as `{framework_version}` — informational, not authoritative. Recorded in `manifest.synthesis` for debugging.

**Output file extensions per framework** (used when emitting optional scaffolds in step 4):

- `svelte` → `.svelte`
- `react` → `.tsx`
- `vue` → `.vue`
- `none` → no scaffold; HTML only

### 2. Locate the Tailwind config

```bash
ls {project-root}/tailwind.config.{js,ts,cjs,mjs} 2>/dev/null | head -1
```

If found, set `{tailwind_config_path}` to the absolute path. If not, set to `null`.

When present, read the config (use Read, not `cat`) and extract the `theme.extend` and `theme.colors` blocks. The goal is to identify config-dependent class names whose values come from this file — these are the classes step 4 must NOT emit (workflow.md §Critical Rules).

Build `{tailwind_config_classes}` — a set of class-name prefixes that resolve through the config:

- Color utilities: `bg-{name}`, `text-{name}`, `border-{name}`, `ring-{name}` for every key in `theme.colors` and `theme.extend.colors`.
- Spacing utilities: `p-{n}`, `m-{n}`, `gap-{n}` etc. for every key in `theme.spacing` and `theme.extend.spacing`.
- Radius utilities: `rounded-{name}` for every key in `theme.borderRadius` and `theme.extend.borderRadius`.
- Font utilities: `font-{name}`, `text-{name}` for every key in `theme.fontSize`, `theme.fontWeight`, `theme.fontFamily` extensions.

This set is fed to step 6's hard-failure check (one of the unconditional invariants verified in step 7 is "no config-dependent Tailwind classes appear" — this set is how we know which classes ARE config-dependent in this project).

**If no Tailwind config is found:** `{tailwind_config_classes} = ∅`. The workflow-invariant check in step 7 still runs but only against universally-config-dependent class patterns (e.g., `text-primary`, `bg-status-*` heuristics).

### 3. Locate the project token file

The project may declare its design tokens in a CSS file, a TypeScript module, or a JSON file. Common locations:

```bash
# CSS — most common for SvelteKit/shadcn projects
ls {project-root}/src/app.css 2>/dev/null
ls {project-root}/src/styles/tokens.css 2>/dev/null
ls {project-root}/src/lib/styles/tokens.css 2>/dev/null

# TypeScript modules
ls {project-root}/src/lib/tokens.ts 2>/dev/null
ls {project-root}/src/lib/design-tokens.ts 2>/dev/null

# JSON
ls {project-root}/tokens.json 2>/dev/null
ls {project-root}/design-tokens.json 2>/dev/null
```

Set `{project_token_paths}` to the list of paths that exist. There may be more than one (e.g., `app.css` for shadcn vars plus a separate `tokens.ts` for typed access).

**If none are found:** `{project_tokens} = {}`. Synthesis still proceeds; every `var(--*)` it emits will count as a proposed token (against the 5-cap), and inline literals become the safer fallback.

### 4. Build the project tokens map

For each path in `{project_token_paths}`, extract the `var(--*)` definitions and their values into `{project_tokens}` — a map of `--name` → `value`.

**Discovery patterns:**

- **CSS:** Scan for `--<name>: <value>;` declarations inside any block (`:root`, `[data-theme="dark"]`, `.dark`, etc.). Record both the value AND the scope (`:root` is "default"; others are "scoped"). The map records the default scope's value; scoped overrides are noted as `{dark: <value>}` etc. and used in step 4 for synthesizing dark-mode-aware output if the brief requests it.
- **TypeScript:** Scan for `export const tokens = { ... }` and similar shapes. Flatten nested objects to dotted-kebab keys (e.g., `tokens.color.primary` → `--color-primary`).
- **JSON:** Same flattening, treating nested objects as dotted-kebab.

For each discovered token, record:

```
{name: "--status-warning", value: "#f59e0b", source_file: "src/app.css", source_line: 142}
```

The `source_line` lets step 4 cite the project's own token file when the synthesizer chooses a token, and lets step 6 produce diagnostics like "this token already exists at src/app.css:142 — do not propose it as new".

### 5. Locate the prior implementation (refine-screen only)

Skip this section if `{mode} != "refine-screen"`.

For each route in `{target_route}` or `{routes}`, locate the project's source file(s) that render at that route. Discovery depends on framework:

| Framework | Discovery |
|---|---|
| `svelte` (SvelteKit) | Route `/foo/bar` → `src/routes/foo/bar/+page.svelte` (and `+layout.svelte` if it owns visible structure). Dynamic segments: `/foo/[id]` → `src/routes/foo/[id]/+page.svelte`. |
| `react` (Next.js App Router) | Route `/foo/bar` → `app/foo/bar/page.tsx` or `app/foo/bar/page.jsx`. |
| `react` (Next.js Pages Router) | Route `/foo/bar` → `pages/foo/bar.tsx`. |
| `vue` (Nuxt) | Route `/foo/bar` → `pages/foo/bar.vue`. |

Verify each path exists. If a route's source file is missing, halt with: `refine-screen mode: prior implementation not found for route <route>. Expected at <path>. Either the route doesn't exist in this project or the discovery rule needs updating.`

Populate `{prior_impl_paths}` as `{route: <absolute path>}`.

### 6. Read prior implementation contents (refine-screen only)

For each path in `{prior_impl_paths}`, read the file fully into `{prior_impl_content[route]}`. This content feeds step 6c's drift check — the synthesizer needs to know what the bundle MUST match in `{unchanged_regions}`.

For large files (>1000 lines), still read fully — drift check works on the entire file by region. Truncation here causes false positives in step 6c.

### 7. Detect existing component library

Some projects ship a curated component library (e.g., shadcn/svelte at `src/lib/components/ui/`). When present, step 4 should prefer reusing component visual treatments rather than inventing parallel styling.

Discovery (best-effort, not required):

```bash
ls {project-root}/src/lib/components/ui 2>/dev/null
ls {project-root}/components/ui 2>/dev/null
ls {project-root}/src/components 2>/dev/null
```

If a `ui/` directory is found, scan filenames into `{component_library}` (e.g., `["button", "badge", "card", "dialog", ...]`). Step 4 uses this to choose component patterns that align with the project's existing visual language. Not finding one is fine; step 4 falls back to first-principles synthesis from the policy.

### 8. Print the context summary and proceed

```
✓ Frontend context loaded:
  framework:           {framework} {framework_version}
  tailwind config:     {tailwind_config_path or "none"}
  config-bound classes: {len(tailwind_config_classes)}
  token files:         {len(project_token_paths)} ({comma-separated basenames})
  project tokens:      {len(project_tokens)}
  component library:   {len(component_library) or "none"}
  prior impl files:    {len(prior_impl_paths) or "n/a (fresh-design)"}

Proceeding to step 4: synthesize.
```

Then load `step-04-synthesize.md` and follow it.

---

## STATE CHECKPOINT

After this step, the following state variables MUST be populated:

- `{framework}`, `{framework_version}`
- `{tailwind_config_path}` (may be null), `{tailwind_config_classes}` (may be empty set)
- `{project_token_paths}` (may be empty list), `{project_tokens}` (may be empty map)
- `{component_library}` (may be empty list)
- In `refine-screen` mode only: `{prior_impl_paths}` (non-empty), `{prior_impl_content}` (non-empty)

Any unset required variable is a workflow bug — halt before step 4.
