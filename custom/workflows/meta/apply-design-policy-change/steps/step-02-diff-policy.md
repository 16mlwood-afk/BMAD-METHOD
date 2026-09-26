# Step 2: Diff the Policy

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Diff section-by-section, not line-by-line — the goal is semantic classification, not textual diff
- If `{policy_previous}` is empty (first version), treat every section as "major change" from nothing

## CONTEXT BOUNDARIES:

- `{policy_current}` and `{policy_previous}` are available from step 01
- `{policy_changelog}` provides the author's intent (advisory, not authoritative)

## YOUR TASK:

Compare old and new policy section-by-section. For each section, classify the change magnitude.

## DIFF SEQUENCE:

### Section-by-section comparison

Compare each of the 9 policy sections between `{policy_previous}` and `{policy_current}`:

| Section | What to compare | Minor = | Major = |
|---------|----------------|---------|---------|
| **1. Visual Direction** | Identity statement, register, density, anti-references | Tone adjustment, rewording | New identity, density flip (high↔low), new anti-references |
| **2. Reference Products** | Product list, borrow/avoid columns | Added/removed one product, adjusted borrow scope | New primary reference, removed all references |
| **3. Tone & Personality** | Voice, expertise, error/empty states | Wording refinement | Changed expertise level, new error personality |
| **4. Layout Principles** | Primary pattern, page structure, nav, responsive, whitespace | Spacing adjustment, responsive tweak | New primary pattern (table→card), nav restructure, page anatomy change |
| **5. Component Language** | Tables, cards, badges, buttons, filters, modals | Size/spacing tweak, added one component rule | New badge system, changed table convention, new filter pattern |
| **6. Status System** | Principle, palette, max colors | Added one status meaning | Changed max colors, added/removed status tier, palette swap |
| **7. Typography & Color** | Font, size philosophy, color restraint, monospace | Size adjustment, added one rule | New font, new accent color, changed restraint level |
| **8. Hard Failures** | List of non-negotiable anti-patterns | Reworded existing failure | Added new hard failure, removed one |
| **9. Page Mode Rules** | Operational, analytical, hybrid defaults | Clarification of existing rule | New default mode, changed hybrid behavior, new mode type |

### Classification output

Build `{section_diffs}`:

```
Section 1 (Visual Direction): unchanged | minor | major
Section 2 (Reference Products): unchanged | minor | major
...
Section 9 (Page Mode Rules): unchanged | minor | major
```

### Summary report

"**Policy diff (v{policy_version_previous} → v{policy_version_current}):**

| Section | Change Level | Summary |
|---------|-------------|---------|
| 1. Visual Direction | {level} | {one-line summary of what changed} |
| 2. Reference Products | {level} | {one-line summary} |
| ... | ... | ... |
| 9. Page Mode Rules | {level} | {one-line summary} |

**Changelog says:** {policy_changelog or 'no changelog entry'}

**Major changes in:** {list of sections with 'major'}
**Minor changes in:** {list of sections with 'minor'}
**Unchanged:** {list of sections with 'unchanged'}"

## NEXT STEP:

Proceed to `{project-root}/_bmad/bmm/workflows/meta/apply-design-policy-change/steps/step-03-classify-impact.md`.

In autonomous mode: proceed immediately.
