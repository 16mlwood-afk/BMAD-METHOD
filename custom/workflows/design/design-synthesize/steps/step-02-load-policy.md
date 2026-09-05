---
name: 'step-02-load-policy'
description: 'Resolve the project design policy, compute its version hash, and extract the hard-failure list and contract-critical positive-assertion allowlist. Halt on Gate 2 if the policy is missing or lacks required sections.'
---

# Step 2: Load Policy

**Goal:** Load `docs/design-policy.md` (or the legacy `brand-identity.md` slot) and extract the two enforcement inputs step 6 needs: the hard-failure list (Sub-check a) and the contract-critical positive-assertion allowlist (Sub-check b). Compute a hash of the policy file so the manifest can record exactly which version of the policy this bundle was synthesized against.

**Gate owned:** Gate 2 — policy presence (workflow.md §APPROVAL GATES).

---

## RULES

- **The policy is the floor, not a suggestion.** It overrides the brief on hard failures and the positive-allowlist (see workflow.md §SOURCE-OF-TRUTH PRECEDENCE, D0).
- **Allowlist items must be policy-ratified positive assertions** (e.g., "status indicators use status tokens, not raw colors"). They are NOT workflow invariants (those are unconditional, checked in step 7). `design-synthesize` does NOT invent allowlist items — if the policy doesn't ratify it, it doesn't enter the allowlist.
- **Specific-value positive assertions** (row heights, font sizes, exact spacing values) stay OUT of the allowlist. Those belong to `design-review`, which runs against the rendered DOM with real data. Including them here causes false failures in step 6 because the synthesized HTML may legitimately differ from the prior implementation on a value the brief doesn't specify.
- **An empty allowlist is acceptable IF the policy declares it explicitly** (`positive_allowlist: []` or equivalent). A missing allowlist is NOT acceptable — silence is ambiguous between "no positive assertions" and "this policy hasn't been ratified yet". Halt on missing; pass on empty-but-declared.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

---

## EXECUTION SEQUENCE

### 1. Resolve the policy path

Check both possible locations in order. Prefer the canonical path:

```bash
ls {project-root}/docs/design-policy.md 2>/dev/null
ls {planning_artifacts}/brand-identity.md 2>/dev/null
```

- If `docs/design-policy.md` exists → set `{policy_path}` to it.
- Else if `{planning_artifacts}/brand-identity.md` exists → set `{policy_path}` to it.
- Else → sweep sibling worktrees before halting (a policy authored via `create-design-policy`/`onboard-design-system` is commonly in a feature worktree, not yet merged): `ls {project-root}/.claude/worktrees/*/docs/design-policy.md 2>/dev/null`. If found, set `{policy_path}` to the worktree path and note it is worktree-resident (not yet on main). Only if that is also empty → halt with: `policy not found. Tried: docs/design-policy.md, {planning_artifacts}/brand-identity.md, .claude/worktrees/*/docs/design-policy.md. Run create-design-policy or modify-design-policy to author one, or place a policy at one of these paths.`

### 2. Load the policy contents

Read the file fully into `{policy_content}`. Use the Read tool.

### 3. Compute the policy version hash

```bash
shasum -a 256 {policy_path} | awk '{print $1}'
```

Store as `{policy_version_hash}`. This is copied into `manifest.synthesis.policy_version_hash` in step 7. Two bundles produced against the same policy text will share the same hash — useful when the user is asking "did this bundle's policy match the current policy?".

### 4. Extract the hard-failure list

The policy's hard-failure section is the floor. Synthesized HTML that commits any of these is a step-6 failure that returns to step 4.

**Discovery rules** (tolerant of section heading style):

- Look for a heading matching `(?i)^#{1,3}\s*(hard\s*failures?|anti-patterns?|never\s+do|forbidden)`.
- The section continues until the next same-or-higher-level heading.
- Extract each bullet/numbered item as a separate failure rule. Strip leading bullets and numbering; preserve the rule text as-is so step 6's diagnostic text quotes the policy verbatim.

Populate `{hard_failures}` as a list of `{rule: <text>, source_line: <int>}` records. Source line is the line number in `{policy_path}` where the rule appears — used in step 6 diagnostics so the user can navigate from a violation to the originating policy line.

**If no hard-failure section is found:** halt with `policy at {policy_path} contains no hard-failure section. Synthesis without enforced floors is unsafe. Add a "## Hard Failures" section listing the anti-patterns this project forbids.`

### 4b. Load the canonical AI-fingerprint taxonomy

READ `{project-root}/_bmad/bmm/workflows/design/shared/design-standards.md` § AI Fingerprint Detection (all six category tables + the composite test) and append its rows to `{hard_failures}` tagged `source: design-standards`, so step-6's self-critique evaluates the synthesized HTML against the FULL taxonomy — not the brief's §5b copy and not a remembered list (the brief's embed is a convenience mirror; the standards file is the source, and a generator that never opens it is how a left-border-accent container shipped on 2026-08-24). A brand-identity-declared exception (named construction + scope) suppresses the matching row for its declared scope only. If the standards file is unreadable, HALT — synthesizing without the taxonomy floor is the same unsafe state as a missing hard-failure section.

### 5. Extract the contract-critical positive-assertion allowlist

Positive assertions are rules the policy ratifies as contract-critical — things synthesis MUST do, not just things it must avoid.

**Discovery rules:**

- Look for a heading matching `(?i)^#{1,3}\s*(positive\s+assert(ion)?s?|contract-critical|must\s+do|always)`.
- OR a YAML/list block tagged `positive_allowlist:` (e.g., at the bottom of the policy as machine-readable enforcement metadata).
- The section continues until the next same-or-higher-level heading.

Populate `{positive_allowlist}` as a list of `{assertion: <text>, source_line: <int>}` records.

**Empty-but-declared is acceptable:**

- A section heading with no items below it, OR a `positive_allowlist: []` block → `{positive_allowlist} = []`. Step 6 sub-check (b) is a no-op when the allowlist is empty. Log: `policy declares empty positive allowlist — sub-check (b) will be skipped.`

**Missing is NOT acceptable:**

- No section heading AND no `positive_allowlist:` block → halt with: `policy at {policy_path} does not declare a positive-assertion allowlist (not even an empty one). Add a "## Positive Assertions" section or a "positive_allowlist:" block — an empty allowlist is fine, but the declaration must be explicit.`

### 6. Sanity-check the allowlist for invariant contamination

The allowlist must contain policy-ratified positive assertions, not workflow invariants. Workflow invariants are unconditional structural rules of the bundle format itself — they live in step 7's validation pass, never in step 6's policy check.

Reject items that match the **workflow-invariant pattern** (these are bugs in the policy authoring, not in this workflow):

- `(?i)every var\(--\*\) resolves`
- `(?i)no config-dependent tailwind`
- `(?i)manifest.*disagree.*html`
- `(?i)bundle (must be )?self-contained`

If any allowlist item matches one of these patterns, halt with: `policy allowlist item "<text>" at line N is a workflow invariant, not a policy-ratified positive assertion. Workflow invariants are enforced unconditionally in step 7. Move this item out of the allowlist and into a separate "Workflow Contracts" section (informational, not enforcement). See workflow.md §D3 for the boundary explanation.`

This guard prevents a recurring authoring mistake: confusing what the workflow guarantees structurally with what the policy ratifies semantically.

### 7. Print the policy summary and proceed

Print to the user:

```
✓ Policy loaded:
  path:              {policy_path}
  version hash:      {policy_version_hash}  (first 12 chars)
  hard failures:     {len(hard_failures)} rules
  positive allowlist: {len(positive_allowlist)} assertions

Proceeding to step 3: load frontend context.
```

Then load `step-03-load-frontend-context.md` and follow it.

---

## STATE CHECKPOINT

After this step, the following state variables MUST be populated:

- `{policy_path}`, `{policy_content}`, `{policy_version_hash}`
- `{hard_failures}` (non-empty list)
- `{positive_allowlist}` (may be empty list, but the variable is set)

Any unset required variable is a workflow bug — halt before step 3.
