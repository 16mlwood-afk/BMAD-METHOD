---
title: Fork Gaps — method & infra backlog
description: A running, Claude-noticed backlog of structural gaps in the Mason-BMAD fork and surrounding infra — method-level friction (deploy, hooks, sync, workflow steps, shared state) logged proactively for later investigation.
---

# Fork Gaps — method & infra backlog

A running, **Claude-noticed** backlog of STRUCTURAL gaps in the Mason-BMAD fork and the infra around it — places where the way things are wired makes normal agent work painful. This is *not* a bug tracker: it's for method-level friction (deploy, hooks, sync, workflow steps, shared state), not one-off task bugs.

This doc is **fork-local** (like `global-bmad-workflow.md` / `parallel-work-and-bmad-state.md`): it is not synced into the 13 projects. It is consumed by the fork-maintenance lane — `maintenance-triage` (sibling, production-driven), `orchestrate-workflows`, and the `mason-bmad-workflow-expert` skill.

## How this works
- **Claude logs here proactively** when the method / fork / infra fights an agent — per the global `workflow-friction-and-process-issues` policy. The user shouldn't have to notice the gap or drag it out; catching yourself working *around* the method is the signal to log.
- **No fixed schema.** Each entry is free-form prose: *what fought us · the specific target file/workflow it points at · why it's structural · proposed investigation · rough priority in words.* No severity/category enums — infer the flavour and urgency in prose.
- **Point at a specific target**, never "the fork is awkward." Name the file/workflow/hook that should change.
- Newest at top. Close an entry by marking it `[resolved: <how>]` in place — don't delete it (the history of what got rediscovered is the point).

---

## Open

### Deploy method is under-specified for agents → `deployment-to-prod.md` + project CLAUDE.md deploy notes
**Noticed:** 2026-06-26 (inbound-flow). **Priority: high** — deploy is the last mile of *every* task, so this friction recurs constantly and every agent pays it.

**What fought us:** an agent deployed with `railway up` directly, leaving prod *ahead of `main`* with the commit stranded on an unmerged local branch; it never considered the git-push-auto-deploy path, weighed no fallback ladder, and followed a CLAUDE.md note ("run `railway up` from `inventory-manager/`") that was wrong and cost failed deploys to rediscover. It also didn't connect that this is a *fork* gap — it treated a structural deploy-legibility problem as a one-off session annoyance.

**Why structural:** there is no canonical, agent-legible deploy method + **fallback ladder**, and no "what to do when GitHub auth breaks mid-deliver" branch. So agents reinvent the deploy path each session and sometimes pick a method that diverges prod from `main`.

**Proposed investigation:**
- Define the canonical deploy path per project and a fallback ladder (e.g. git-push auto-deploy → `railway up` from the correct dir → manual), encoded so an agent picks the right one without guessing. Note: inbound-flow is `deploy.bmad_contract: skip` (Railway auto-deploys on push) — yet the agent reached for `railway up`, which is the tell that the method isn't legible from where the agent looks.
- Add an **auth-failure branch**: if GitHub auth breaks, the commit must still reach `main` (the durable target), not just prod via a side-channel `railway up` — otherwise the next git-based deploy reverts the fix.
- Correct the wrong "run `railway up` from `inventory-manager/`" guidance wherever it's copied (likely several project CLAUDE.mds seeded from the fork template).
- Decide whether the deploy method belongs codified **once** in `deployment-to-prod.md` (so it syncs to all ~13 projects) rather than restated — and drifting — per project CLAUDE.md.
