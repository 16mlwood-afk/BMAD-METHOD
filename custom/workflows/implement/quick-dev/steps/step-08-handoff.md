---
name: 'step-08-handoff'
description: 'Proactive developer handoff — document gaps, observations, and follow-up recommendations discovered during implementation'
---

# Step 8: Developer Handoff

**Goal:** Before closing the session, document what you noticed. Every implementation reveals things the spec didn't anticipate — inconsistencies, missing data, fragile patterns, opportunities. Capture them now while context is fresh.

**Why this step exists:** Developers discover gaps during implementation that are invisible from the spec. Without a structured handoff, these observations evaporate when the session ends. The next developer (or the same one, next week) starts from zero. This step makes institutional knowledge compound instead of decay.

---

## AVAILABLE STATE

From previous steps:

- `{baseline_commit}` - Git HEAD at workflow start
- `{execution_mode}` - "tech-spec" or "direct"
- `{tech_spec_path}` - Tech-spec file (if Mode A)
- Implementation delivered and merged

---

## WHEN TO PRODUCE A HANDOFF

**Always.** Even if everything went cleanly, say so — a "nothing to report" handoff is still valuable because it confirms the spec was complete.

The handoff is not optional and not gated behind a menu. It runs automatically after delivery.

---

## WHAT TO CAPTURE

Reflect on the full implementation cycle and identify items in these categories. Be concrete — cite file paths, line numbers, field names, API responses. Vague observations ("the code could be cleaner") are worthless.

### 1. Gaps Found & Fixed

Things the spec didn't cover that you handled during implementation. These are already shipped — document them so the requester knows what was added beyond the original ask.

Examples:
- "Detail page was missing estimatedDeliveryWindow — sidebar had it but detail page didn't. Added for parity."
- "Spec said to add a column but didn't mention the filter config. Added a filter option for consistency."

### 2. Gaps Found & NOT Fixed

Things you noticed but intentionally left alone — either out of scope, blocked, or requiring a product decision.

Examples:
- "carrierAppointmentDetails is in the DB and API but not shown anywhere. Probably useful for LTL shipments."
- "The weight formatting assumes only KILOGRAMS and POUNDS but the schema allows freetext — could break if Amazon adds a new unit."

### 3. Code Quality Observations

Patterns, duplication, or structural issues you encountered that aren't bugs but create friction or risk.

Examples:
- "Three components had identical format helpers copy-pasted. Extracted to shared util but there may be more."
- "The shipment detail sidebar casts `shipment` to `Record<string, unknown>` because the TypeScript type from the API response is too loose. Should type the getShipmentDetail return properly."

### 4. Recommendations

Specific follow-up work you'd suggest. Each should be actionable enough to hand to another dev.

Examples:
- "Add estimatedShippingCost column to the main table — data is already fetched, just needs a column def."
- "The transportation-progress.tsx component also formats shipping costs independently — should use the shared transport-format.ts util."

**DO NOT include post-deploy commands the user is expected to run.** Recommendations describe future work in prose; they are not a checklist of shell commands. If a script needs to run after deploy (backfill, rearm, dry-run + apply, etc.), the rule from step-07 applies: run it yourself in-session, or describe the follow-up here in plain language without a copy-pasteable command block. Never queue the user with `source ~/.secrets && npx tsx scripts/...` style instructions.

### 5. Strategic & Operational Insights

**This is the highest-value section.** Step back from the code you just wrote and think about the system holistically. Implementation gives you context that no spec or review can — use it.

Ask yourself these questions based on what you touched, read, or debugged during implementation:

- **Resource & cost:** Are there capacity limits, rate limits, API quotas, or plan tiers that the current usage pattern is outgrowing? Would upgrading a service tier be cheaper than the engineering time spent working around limits?
- **Operational efficiency:** Are there recurring processes (sweeps, syncs, enrichments) that run blind — without checking whether they'll succeed or whether resources are available? Could a pre-flight check (query a status endpoint, check a budget) prevent wasted cycles?
- **Hidden multipliers:** Does the code path you touched trigger secondary costs that aren't obvious? Cache misses that cascade into extra API calls, N+1 patterns against external services, retry storms on rate-limited endpoints?
- **Architecture friction:** Did you encounter a pattern that made this change harder than it should have been? A missing abstraction, a coupling that forced changes in multiple places, a type that doesn't match reality?
- **Data pipeline gaps:** Is there data flowing through the system that's collected but not surfaced, or surfaced but not acted on? Monitoring blind spots?

**Format each insight as:**
1. **Observation** — what you noticed (be specific: name the service, endpoint, config, metric)
2. **Impact** — why it matters (cost, reliability, developer velocity, user experience)
3. **Suggested action** — what to do about it, with a rough effort estimate

**Examples:**
- "The API rate limit is 20 req/min shared across two services with continuous pipelines. The budget math doesn't close — upgrading the plan doubles headroom and likely costs less than the engineering time spent on rate-limit workarounds."
- "The scheduled sweep fires hourly regardless of API quota pressure. Checking available quota before processing and skipping the tick if quota is low would prevent the sweep from burning requests and getting rate-limited. ~15 lines in the sweep processor."
- "Each cache miss triggers a secondary API lookup. The cache TTL and hit rate are worth auditing — if the cache is cold after deploys, it's a significant cost multiplier that doesn't show up in the per-request count."

**If you have no strategic insights, say "None — the implementation was self-contained with no system-level observations." But try. The implementation context you have right now is perishable — these observations are often more valuable than the code itself.**

---

## OUTPUT FORMAT

Write a handoff file to `{implementation_artifacts}/` using this structure:

```markdown
---
title: 'Handoff: {brief description of what was implemented}'
created: '{date}'
source_pr: '{pr_url}'
type: handoff
completion_disposition: '{pr_merged | pr_open | owner_gated_residue | advisory}'  # STD-COMPLETION-001 — pr_* carries the PR; owner_gated_residue names each blocker below; advisory only if the owner scoped this run to analysis
---

# Handoff: {brief description}

**PR:** {pr_url}
**Spec:** {tech_spec_path or "direct instructions"}
**Date:** {date}

## Delivered Beyond Spec

{List items from "Gaps Found & Fixed", or "None — spec was complete."}

## Known Gaps

{List items from "Gaps Found & NOT Fixed", or "None identified."}

## Code Observations

{List items from "Code Quality Observations", or "None."}

## Recommended Follow-ups

{Numbered list of concrete next actions. Each should include:}
{- What to do}
{- Why it matters}
{- Files involved}
{- Rough size estimate: trivial / small / medium}

{Or "None — implementation is self-contained."}

## Strategic & Operational Insights

{Numbered list from section 5. Each should include:}
{- Observation: what you noticed}
{- Impact: why it matters}
{- Suggested action with rough effort estimate}

{Or "None — the implementation was self-contained with no system-level observations."}

## Constraints Persisted

{List memories saved by the "Persist Discovered Constraints" step, or omit this section entirely if none were saved.}
{- **{memory-name}** — {one-line description}}
```

**File naming:** `handoff-{slug}-{date}.md` where `{slug}` matches the PR branch name or tech-spec slug.

---

## PRESENT TO USER

After writing the handoff file, present a brief summary to the user. Emit it per `shared/close-out-contract.md` (STD-CLOSEOUT-001): audience-first for the next developer — what's filed and what they act on next, NOT a process recap of how you built it (process narration is forbidden by default; trace on request). If the user critiques the SHAPE of this summary, patch this step in the fork (contract §4), don't just rewrite the message or write a memory.

**Declare the completion disposition.** Emit a `completion_disposition` per `shared/completion-contract.md` (STD-COMPLETION-001) — both in the handoff-file frontmatter (above) and as a one-line tail on the summary: `pr_merged` / `pr_open` with the PR, `owner_gated_residue` with each remaining blocker NAMED and why it is owner-gated (e.g. "needs a credential provisioned", "destructive migration — owner-gated"), or `advisory` with a why if the owner scoped this run to analysis only. Ending the handoff with only observations and no disposition is the invalid commentator exit (contract §3) — quick-dev is a completion workflow, so a clean run is `pr_merged`, not a list of things you noticed.

```
**Handoff filed:** {file_path}

{If there are recommended follow-ups:}
**Follow-ups identified:** {count}
{One-line summary of each, numbered}

{If there are strategic insights:}
**Strategic insights:** {count}
{One-line summary of each, numbered — prioritized by impact}

{If no follow-ups and no strategic insights:}
Clean implementation — no follow-ups or strategic insights identified.
```

---

## AUTONOMOUS MODE BEHAVIOR

In autonomous mode, write the handoff file and present the summary. Do not halt or wait for input. The handoff is informational — it does not require approval.

---

## WIRE-CHECK CHAIN

After presenting the handoff summary, trigger a wire-check on the handoff artifact you just wrote. The wire-check traces every data field end-to-end and catches loose wires before the next developer encounters them.

**In autonomous mode:** Run the wire-check immediately — do not ask.

**In interactive mode:** Present the option:
```
Wire-check available — trace data wires from this handoff?
→ /bmad:bmm:workflows:wire-check {handoff_file_path}
```

The wire-check workflow handles its own worktree, commit, and delivery. It will enter a fresh worktree if fixes are needed, so the current worktree can be cleaned up first.

**Ordering:** Write handoff → present summary → clean up worktree → chain wire-check. The wire-check runs after worktree cleanup because it manages its own worktree independently.

---

## PERSIST DISCOVERED CONSTRAINTS

Implementation often reveals hard platform limits, service ceilings, and infrastructure gotchas that aren't documented anywhere. These constraints are invisible from specs and code reviews — they only surface when you hit them. **Save them to project memory so future sessions don't rediscover them the hard way.**

### What qualifies as a constraint

- **Platform limits:** column counts, row sizes, query variable caps, payload size ceilings, rate limits discovered empirically (not just documented ones)
- **Service ceilings:** plan-tier restrictions, API quota walls, storage limits, concurrent connection caps
- **Infrastructure gotchas:** operations that silently fail, features that don't work as documented, version-specific behaviors, deployment sequencing requirements
- **Workaround patterns:** if you had to work around a constraint, document both the constraint and the pattern — future sessions may need the same workaround

### What does NOT qualify

- Code patterns or architecture (derivable from the codebase)
- Bug fixes (the fix is in the code; the commit message has context)
- Anything already in CLAUDE.md or existing memory

### How to save

For each discovered constraint, write a `project`-type memory:

```markdown
---
name: {constraint-slug}
description: {one-line summary — specific enough to match future searches}
metadata:
  type: project
---

{What the constraint is — be specific: name the service, limit, threshold, error message.}

**Why:** {How you discovered it — what failed, what error, what workaround was needed.}
**How to apply:** {When future sessions should check for this — e.g., "before adding columns to invoices table", "when designing batch queries against D1".}
```

Add an index entry to the project's `MEMORY.md` under `## Project`.

### When to skip

If the implementation was routine and hit no platform/infrastructure limits, skip this section. Don't manufacture constraints that aren't there.

### In the handoff file

If you saved any constraint memories, add a `## Constraints Persisted` section to the handoff file listing what was saved:

```markdown
## Constraints Persisted

- **{memory-name}** — {one-line description}
```

This creates an audit trail connecting the handoff to the memories it produced.

---

## WORKTREE CLEANUP

**Only after** the handoff file is written and the summary has been presented, clean up the worktree.

If NOT in a worktree, skip this section.

### Copy handoff to the main repo BEFORE removing the worktree

The handoff file is untracked (not committed). It lives inside the worktree directory tree. **Removing the worktree deletes all untracked files inside it**, including the handoff. You MUST copy it out first:

```bash
cp <worktree-path>/_bmad-output/implementation-artifacts/handoff-*.md \
   <main-repo-root>/_bmad-output/implementation-artifacts/
```

Verify the copy landed:

```bash
ls -la <main-repo-root>/_bmad-output/implementation-artifacts/handoff-<slug>-<date>.md
```

### Remove the worktree

Call `ExitWorktree` with `action: "remove"`:

- All commits have been pushed and merged in step-07 — the worktree branch is no longer needed.
- `ExitWorktree` returns the session to the original working directory.
- If `ExitWorktree` refuses because of uncommitted changes or unmerged commits, something went wrong in step-07 — investigate before forcing. Use `discard_changes: true` only after confirming the handoff was copied.

**Critical ordering:** the sequence is always (1) write handoff file → (2) present summary → (3) copy handoff to main repo → (4) `ExitWorktree`. Reversing (1)/(2) and (4) trips the parallel-sessions hook on `Edit|Write` and blocks the handoff write. Skipping (3) loses the handoff when the worktree is removed. Both are bugs the workflow has hit in production.

After `ExitWorktree` succeeds, append one line to the user-facing summary: `**Worktree cleaned up.**`

### Rebuild dist after worktree cleanup

Worktree builds compile into the **worktree's** `dist/` directory, which is destroyed on removal. The main repo's `dist/` is now stale — it still contains pre-change code. For projects that build to a `dist/` directory (Chrome extensions, bundled apps), this means the user is testing against old code without knowing it.

**After `ExitWorktree` returns you to the main repo:**

1. Pull latest main: `git pull origin main`
2. Rebuild: run the project's build command (e.g., `npm run build`)
3. Confirm the build succeeded

This is **not optional** — skipping it means the user's local app/extension runs stale code and will report bugs that are already fixed. The agent must never tell the user "just rebuild" as a response to a test failure.

---

## SUCCESS METRICS

- Handoff file written to implementation artifacts directory
- All five categories addressed (even if "None")
- Observations are concrete (file paths, field names, line numbers) not vague
- Follow-ups are actionable — another dev could pick one up without asking questions
- Summary presented to user
- Worktree removed via `ExitWorktree` (if applicable) — and only after the handoff was written

## FAILURE MODES

- Skipping the handoff because "everything went fine"
- Writing vague observations without concrete references
- Listing follow-ups that are too broad to act on ("improve the codebase")
- Not writing the file (just presenting verbally — context is lost when session ends)
- Not presenting the summary to the user
- **Listing follow-ups as command blocks the user is supposed to execute after the deploy lands.** Run the commands yourself in-session, or describe the follow-up in prose. The handoff file is documentation, not a chore queue.
- **Calling `ExitWorktree` before the handoff file is written.** The parallel-sessions `PreToolUse` hook will block the write and the handoff is lost. Always: write handoff → present summary → copy to main repo → exit worktree.
- **Removing the worktree without copying the handoff file to the main repo first.** The handoff is untracked — it lives inside the worktree directory and is destroyed on removal. This has happened in production.
- Not calling `ExitWorktree` at all (leaves stale worktrees on disk — see `git worktree list`).
- **Not rebuilding `dist/` after worktree cleanup.** The worktree's build output is destroyed on removal. The main repo's `dist/` still contains pre-change code. The user tests against stale code, reports bugs that are already fixed, and the agent wastes time saying "just rebuild." This has happened in production.
- Skipping section 5 (Strategic & Operational Insights) — this is the highest-value section. Implementation context is perishable; if you don't surface system-level observations now, they're lost.
