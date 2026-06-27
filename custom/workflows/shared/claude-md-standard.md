---
name: claude-md-standard
contract_version: 1
description: 'STD-CLAUDE-001 — the structure and discipline standard for CLAUDE.md files. Defines the split between the GLOBAL CLAUDE.md (cross-cutting doctrine, machine-local at ~/.claude/CLAUDE.md) and a PROJECT CLAUDE.md (repo-specific details only), the canonical project layout, the pointer-not-restate rule, and the edit discipline. Governs both. Referenced by STANDARDS.md (STD-CLAUDE-001), the new-project spec, and the CLAUDE.md lint/drift nudges.'
---

# STD-CLAUDE-001 — CLAUDE.md Structure & Discipline

CLAUDE.md is governed like any other standard: there is a canonical division of responsibility, a recommended shape, and an edit discipline. The goal is **thin, pointer-based project CLAUDE.md files** that defer to the shared canon, and **one** authoritative global doctrine file — not N copies of the same doctrine drifting apart.

## The two CLAUDE.md layers

### Global CLAUDE.md — `~/.claude/CLAUDE.md` (machine-local doctrine)
Owns **cross-cutting doctrine** that applies everywhere:
- Precedence rules (system/CLAUDE.md/current-request beats stored memory), the executive-summary rules, answer-shape & autonomy.
- "BMAD fork is shared infra," the discovery gate, the enforcement gate (→ `enforcement-expert`), the memory doctrine pointer (→ `memory-library-discipline` / `memory-hygiene`).
- Always-on reactive guardrails.

**Must NOT contain:** project-specific commands, URLs, DB layout, secrets, or any per-repo nuance. Those belong in a project CLAUDE.md. It is machine-local (like memory) and is **not** synced through the fork; keep a backup copy in the fork if you want history.

### Project CLAUDE.md — `<repo>/CLAUDE.md` (repo-specific only)
Owns **only** what is true for this one repo:
- Dev (how to run it locally), Deploy (env names, URLs, platform quirks), CI specifics, DB layout, worktree policy, genuinely-local gotchas.

**Must NOT restate shared standards.** Where a project follows a shared standard, **point at it by ID/path** — never paste its body. A long generic memory-doctrine block or a copied deploy contract in a project CLAUDE.md is drift; replace it with a pointer (e.g. "Deploy follows **STD-DEPLOY-001** — see `_bmad/bmm/workflows/shared/deployment-to-prod.md`").

## Canonical project CLAUDE.md shape

A good project CLAUDE.md is short and pointer-based. Recommended sections:

```
# <repo> — Overview        one-liner: what this repo is
# Dev                      how to run it locally (ports, commands, local-stack notes)
# Deploy                   project-specific bits (env names, URLs); canon via STD-DEPLOY-001
# Memory                   where this project's memory lives; STD-MEMORY-001 + MEMORY.md
# Notes                    truly local quirks only
```

`cash-recovery` is the **reference project** for this shape: a thin pointer-style CLAUDE.md with the deploy manual factored into `docs/deployment.md`, citing `_bmad/bmad-shared/` standards by path.

## Edit discipline

- **Global** CLAUDE.md is edited in ONE place: `~/.claude/CLAUDE.md`. Doctrine changes land there (and, if you keep a fork backup, mirror it).
- **Project** CLAUDE.md is edited in the project repo, stays thin, and uses pointers. When you find yourself pasting a shared standard's body into a project CLAUDE.md, stop and write a pointer instead.
- A `PreToolUse(Edit|Write)` nudge (`check-claude-md-lint.sh`) flags CLAUDE.md edits that look like full restatements of a shared standard and suggests a pointer — message only, never a block.

## Governance

Reviewed quarterly by the **Standards Governance Review** routine (the global CLAUDE.md by the local half of that review, since it is machine-local; project CLAUDE.md shape by the per-project nudges). Changes are logged via STATUS entries, same as any standard. A `SessionStart` nudge (`check-claude-md-drift.sh`) soft-warns when a project has no CLAUDE.md or one that looks thick/restating.
