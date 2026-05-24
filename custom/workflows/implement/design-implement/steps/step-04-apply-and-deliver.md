---
name: 'step-04-apply-and-deliver'
description: 'Apply all deltas from the comparison grid to the implementation, run build, commit, push, create PR, merge, and deploy'
---

# Step 4: Apply and Deliver

**Progress: Step 4 of 4** — Final step

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- Fix EVERY delta from Step 3's grid — Tier 1, Tier 2, and Tier 3. No "good enough."
- After applying fixes, re-verify by re-reading the modified files. Do not trust that the edit was correct without checking.
- Follow the project's CLAUDE.md for commit, PR, merge, and deploy procedures.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`

## CONTEXT

From Step 3 you have:
- `{comparison_grid}` — the full delta table with severity tiers
- `{delta_count}` — number of properties to fix
- `{impl_components}` — paths to all implementation files
- `{impl_config}` — Tailwind config and class resolution table
- `{baseline_commit}` — Git SHA before changes

## SEQUENCE OF INSTRUCTIONS

### 1. Plan Fix Strategy

For each delta, determine the correct fix approach:

| Fix Type | When | Example |
|----------|------|---------|
| Tailwind class swap | A Tailwind class maps to the wrong value | `rounded-lg` → `rounded` (when config maps `rounded` to `4px`) |
| Tailwind arbitrary value | No Tailwind class matches the design value | `rounded-[3px]`, `text-[22px]`, `tracking-[-0.015em]` |
| Inline style change | Property is set via `style` attribute | `width="20"` → `width="24"` |
| Grid template edit | Column widths differ | `grid-cols-[28px_1fr_auto]` → `grid-cols-[32px_1fr_auto]` |
| Content text change | Label or sub-text differs | `{count} invoices scored` → `vs previous batch` |
| New component | Design has a component the implementation lacks | Create the component file |

### 2. Apply Fixes Component by Component

Process one component at a time. For each:

1. Read the current implementation file
2. Apply all fixes for that component
3. Re-read the file to verify the edits landed correctly
4. Check that no adjacent code was broken by the edit

**Order:** Fix Tier 1 (structural) first, then Tier 2 (visual), then Tier 3 (micro). Within a component, apply all tiers together — the ordering is for prioritization if something goes wrong, not for separate passes.

### 3. Handle Tailwind Config Conflicts

If the design requires a value that conflicts with the project's Tailwind config:

- **Prefer arbitrary values** (`rounded-[4px]`) over changing the Tailwind config
- **Never modify `tailwind.config.js`** unless the user explicitly requested it — the config affects the entire project, not just this page
- If a Tailwind utility class happens to resolve correctly through the existing config, use the class (e.g., `rounded` if it maps to `4px`)

### 4. Run Build Check

```bash
npm run build
```

If the build fails:
1. Read the error output
2. Fix the issue (likely a template nesting error from edits)
3. Re-run `npm run build`
4. If it fails again, diagnose more carefully — read the affected file region

### 5. Update the Grid Artifact

Re-read each modified file. Update the comparison grid artifact from Step 3:
- Change every fixed delta from its previous value to `✓ FIXED`
- Leave any unfixed deltas (if any) clearly marked
- Add a summary line at the bottom: `Fixed: {X}/{delta_count} deltas`

### 6. Commit and Push

Follow the project's CLAUDE.md commit procedures:

```bash
git add {list of modified files}
git commit -m "$(cat <<'EOF'
fix: align data-quality page with Meridian design spec

Resolves {delta_count} design deltas identified by component × property
comparison grid. Key changes: border-radius (tokens.radius → Tailwind
arbitrary values), font sizes, grid column widths, SVG dimensions,
and content text.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

Push and create a PR:

```bash
git push -u origin {branch-name}
gh pr create --title "fix: align {page-name} with Meridian design spec" --body "$(cat <<'EOF'
## Summary
- Resolves {delta_count} design deltas found by exhaustive comparison grid
- Key areas: border-radius, font sizes, grid column widths, icon dimensions
- Comparison grid artifact: {artifact_path}

## Changes
{list of files changed with one-line summary each}

## Test plan
- [ ] Visual comparison against design artifact
- [ ] Build passes (`npm run build`)
- [ ] No regressions on adjacent pages

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 7. Merge and Deploy

```bash
gh pr merge --squash --admin
```

Then deploy per the project's CLAUDE.md instructions.

### 8. Report Completion

Output:

```
Design implementation complete.

Baseline: {baseline_commit}
Deltas fixed: {X}/{delta_count}
PR: {pr_url}
Deploy: {deploy_url}

Comparison grid: {artifact_path}
```

---

## SUCCESS METRICS

- Every delta from the comparison grid is fixed
- Build passes
- PR created, merged, and deployed
- Grid artifact updated with fix status
- No regressions introduced

## FAILURE MODES

- Fixing some deltas but not all ("the rest are minor" — fix them all)
- Editing without re-reading to verify (edits can silently fail or land in the wrong location)
- Changing `tailwind.config.js` when an arbitrary value would work
- Committing without running `npm run build`
- Forgetting to deploy after merge
