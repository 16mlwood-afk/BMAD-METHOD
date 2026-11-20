---
name: context-compaction
description: Shrink an over-budget, always-loaded context/instruction file to the reference-not-restate shape. Use when a file loaded on every turn exceeds its char/token budget or duplicates a doc it could point at — "instruction file over budget", "compact CLAUDE.md", "reduce the Space instructions", "reference not restate", "this file is too long / over char limit", "index this instruction file". Do not use for ordinary prose editing or a one-off doc with no reuse/budget pressure. Owns the OPERATION only; doctrine is STD-CLAUDE-001 (reference-not-restate), which it cites and never redefines. Applies to CLAUDE.md, SKILL.md, MEMORY.md-as-a-file, and external always-loaded surfaces (e.g. a Perplexity Space instruction field).
provenance:
  id: context-compaction
  version: 1.0.0
  created_at: 2026-07-24
  author: Claude (with Mason)
  source_research:
    - https://gist.github.com/badlogic/cd2ef65b0697c4dbe2d13fbecb0a0a5f  # "Context Compaction Research: Claude Code, Codex, OpenCode, Amp"
    - https://github.com/topics/prompt-compression  # LLMLingua-2 and runtime prompt-compression tools
    - https://github.com/Opencode-DCP/opencode-dynamic-context-pruning  # runtime context pruning plugin
  origin_type: original
  exemption_reason: "External tools compress RUNTIME prompts/conversation context (LLMLingua-2, DCP). This skill does author-time refactoring of an always-loaded INSTRUCTION FILE (CLAUDE.md/SKILL.md/MEMORY.md) to the reference-not-restate/pointer shape — a different problem with no external tool. Doctrine = STD-CLAUDE-001."
  last_reviewed_at: 2026-07-24
  review_notes: "Backfill under STD-SKILLPROV-001. The term is externally validated (badlogic gist); the file-refactoring operation is fork-original."
---

## External research checked
- Date: 2026-07-24 · Queries: "LLM context window compaction prompt compression technique open source GitHub"
- Sources: badlogic context-compaction gist · GitHub prompt-compression topic (LLMLingua-2) · OpenCode DCP
- Verdict: ORIGINAL — external tools compress runtime context, not author-time instruction files. Distinct problem.

# Context Compaction — the reference-not-restate operation

**Doctrine lives in STD-CLAUDE-001** (`_bmad/bmad-shared/claude-md-standard.md`, section "Reference-not-restate is surface-agnostic"). This skill does not restate the principle — it is the invocable procedure for shrinking one over-budget file to that shape. Sibling registries that already embody the same method: `STANDARDS.md` (STD IDs), `MEMORY.md` (`[[name]]` index).

## When to use
An always-loaded file — one pulled into context every turn, competing for a char/token budget — is over budget, or restates a body it could point at. Symptoms: "over the char limit", "instruction file too long", CLAUDE.md / SKILL.md / Space-instructions bloat, the same rule copied in two files.

**Do NOT use** for: ordinary prose editing, shortening a one-off document with no reuse/budget pressure, or deciding a file's *content* (that is the file's own authoring workflow). This skill only reshapes an existing over-budget file to the pointer form.

## The operation
1. **Measure against budget.** Get the hard ceiling (ask if unknown — never guess it) and the current size (`wc -m` for chars). Record the overage. Re-measure after every pass; counters differ, so leave ~40+ chars headroom at the end.
2. **Cut inline vs pointer.** For each block decide: is it a firing TRIGGER or GUARDRAIL that must act without the referenced doc loaded? → it stays inline, thinned to *trigger + key constraint*. Is it procedure, rationale, a golden case, or a repeated path? → it moves behind a pointer. Never demote a guardrail to a pointer (STD-CLAUDE-001: "don't hide guardrails behind pointers").
3. **Build or extend the registry.** One index block maps each `[[Name]]` → file/section (or `STD-<AREA>-NNN` / path), defined ONCE. Factor a repeated path into a shorthand (e.g. `board = claude-advisory-board.md`). The registry is the only place the physical location lives — that is what makes the file rename-safe.
4. **Convert references.** Replace every restated rule and every long-form "(see doc X, section Y)" with `[[Name]]`. Each doctrine section collapses to: *trigger sentence · key constraint · `Full: [[Name]]`*. If a section needs more than ~2 sentences to be safely actionable inline, split it into two named rules rather than cram.
5. **Verify.** Re-measure ≤ budget with headroom. Confirm every `[[Name]]` resolves to an index entry (no dangling pointers) and every always-on trigger survived inline. Point the registry at the *real current* heading names — rename-safety only holds if the registry matches reality.

## Golden example — Perplexity advisory instructions, 10,238 → 6,955 chars (7,000 budget)
- **One section, before → after.** Anti-stall went from ~800 chars of restated rule + a long-form pointer to:
  > "Never ratify a 'nothing to do' close. A blocker is real only if it names action → owner → why-not-now; a cheap decidable check is a to-do, not a park; on a 'we're all parked' paste, break the stall. Full: `[[Anti-Stall]]`."
  ~200 chars — firing trigger kept inline, elaboration + golden case pointed out.
- **Whole file.** Built an 18-entry `[[Name]]` registry (`board` = `claude-advisory-board.md` factored once), converted every "(Full → charter …)" tail to `[[Name]]`, kept all gate-triggers inline, verified all 18 pointers resolve and the file lands under budget with headroom. The 3,283-char cut came entirely from de-duplication (the referenced charter holds the detail) + factoring the repeated path — no rule was dropped.

## What to watch
- **Don't let this skill — or the compacted file — become a second copy of the doctrine.** Point at STD-CLAUDE-001 and the sibling registries; don't re-explain the method.
- **A dropped guardrail is worse than an over-budget file.** If the triggers won't fit, the budget or the file's scope is wrong — flag it, don't silently delete a gate.
- **Headroom, not exact fit.** Landing 4 chars under a hard ceiling is fragile across counters; leave a real margin.
