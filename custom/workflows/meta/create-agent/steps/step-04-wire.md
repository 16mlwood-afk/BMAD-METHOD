---
name: 'step-04-wire'
description: 'Sync the custom/agents/ lane to distribute the persona and auto-generate its command wrapper, then verify the slash command resolves in the current project'
---

# Step 4: Sync the Lane & Verify Invocable

**Progress: Step 4 of 4** — Final step

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- **The sync generates the wrapper — do NOT hand-write it.** As of the `custom/agents/` lane, `sync_agents_for_project` mirrors the persona into every project's `_bmad/bmm/agents/` AND emits the `.claude/commands/bmad/bmm/agents/{agent_slug}.md` wrapper. Running the sync IS the wiring step.
- Verify the slash command resolves in the current project before reporting success. A persona in the lane that was never synced is NOT invokable.

## CONTEXT

From step 3 the persona exists at `{agent_file}` = `{bmad_root}/custom/agents/{agent_slug}.md` (the fork lane). It is in the lane but not yet in any project. This step runs the sync to distribute it + generate its wrapper, then confirms `/bmad:bmm:agents:{agent_slug}` resolves in `{project_root}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Run the Sync

Distribute the persona and auto-generate its wrapper across all targeted projects:

```bash
"{bmad_root}/sync-bmad-workflows.sh"
```

Read the output:

- Look for `OK    agents (N agent(s) synced)` lines — those projects received the new persona + a generated wrapper.
- Some projects may report `blocked` due to **pre-existing local-only content** in their workflow dirs (unrelated to this agent — the block check only scans workflow `SYNC_DIRS`, never `_bmad/bmm/agents/`). That does NOT stop the agent reaching the unblocked projects, and it does NOT mean the agent failed. Note the blocked count for the report; the agent reaches those projects on the next clean broad-sync.
- If the **current project** (`{project_root}`) is among the blocked, the agent's files may not have landed there yet — section 2 will catch it; if so, materialize the two files directly into the current project (persona via the lane copy, wrapper via the shape below) so it is invokable now, and note the broad-sync will reconcile the rest.

The wrapper the sync writes has this exact shape (for reference / the fallback case only):

```
---
name: '{agent_slug}'
description: '{agent_slug} agent'
---

You must fully embody this agent's persona and follow all activation instructions exactly as specified. NEVER break character until given an exit command.

<agent-activation CRITICAL="TRUE">
1. LOAD the FULL agent file from @_bmad/bmm/agents/{agent_slug}.md
2. READ its entire contents - this contains the complete agent persona, menu, and instructions
3. Execute ALL activation steps exactly as written in the agent file
4. Follow the agent's persona and menu system precisely
5. Stay in character throughout the session
</agent-activation>
```

### 2. Verify the Slash Command Will Resolve in the Current Project

Confirm both files landed in `{project_root}` and point at each other:

```bash
ls -la "{project_root}/_bmad/bmm/agents/{agent_slug}.md"
ls -la "{project_root}/.claude/commands/bmad/bmm/agents/{agent_slug}.md"
grep -n "@_bmad/bmm/agents/{agent_slug}.md" "{project_root}/.claude/commands/bmad/bmm/agents/{agent_slug}.md"
```

Confirm:

- [ ] The persona landed at `{project_root}/_bmad/bmm/agents/{agent_slug}.md` (the sync mirrored it from the lane).
- [ ] The wrapper exists at `{project_root}/.claude/commands/bmad/bmm/agents/{agent_slug}.md` (the sync generated it).
- [ ] The wrapper's `@_bmad/...` path matches the persona filename exactly.

If the current project was blocked and the files are missing, materialize them now (copy the lane persona to `{project_root}/_bmad/bmm/agents/` and write the wrapper above) so the agent is invokable, then proceed.

### 3. Finalize in the Fork

The persona is in the lane and distributed locally, but it is **untracked in the fork** until committed. Surface the exact finalization command for the completion report (commit + push so the persona is durable and reaches other machines/clones):

```bash
git -C "{bmad_root}" add "custom/agents/{agent_slug}.md"
git -C "{bmad_root}" commit -m "feat(agents): add {agent_name} ({agent_slug})"
git -C "{bmad_root}" push myfork custom
```

(Surface it; do not auto-run if other fork work is in flight — the user finalizes when ready.)

### 4. Report Completion

Present a concise summary:

```
Agent "{agent_name}" ({agent_title}) built and INVOKABLE.

Files:
- {bmad_root}/custom/agents/{agent_slug}.md   (persona — the fork lane, source of truth)
- synced → {project_root}/_bmad/bmm/agents/{agent_slug}.md   (persona, this project)
- synced → {project_root}/.claude/commands/bmad/bmm/agents/{agent_slug}.md   (wrapper, auto-generated)

Invoke it now:
  /bmad:bmm:agents:{agent_slug}

Routes/owns: {one-line summary of the lane, or "advisor — answers {domain} questions"}

Distribution: {N} project(s) synced{, M blocked on pre-existing local-only drift — reach on next clean broad-sync}.
Finalize in the fork (durable + pushed):
  git -C {bmad_root} add custom/agents/{agent_slug}.md && git -C {bmad_root} commit -m "..." && git -C {bmad_root} push myfork custom
```

---

## SUCCESS METRICS

- Sync run; `OK agents` line confirms the persona + wrapper were emitted
- `/bmad:bmm:agents:{agent_slug}` resolves in `{project_root}` (both files present, wrapper points at persona)
- Persona is in the lane (`custom/agents/`), distributed (not project-local), and wipe-safe (sync_agents re-writes after the upstream `--delete`)
- Distribution status (synced / blocked counts) reported honestly
- Fork commit+push command surfaced for finalization

## FAILURE MODES

- **Hand-writing the wrapper instead of running the sync** — redundant now; the sync generates it. (Only materialize a wrapper directly if the current project was blocked and you need the agent invokable immediately.)
- **Reporting success without running the sync** — the persona in the lane is not invokable in any project until the sync distributes it.
- Slug mismatch between the persona filename and the wrapper's `@_bmad/...` reference — wrapper resolves but loads nothing (the sync keeps these in lock-step; only a risk in the manual fallback).
- Treating a `blocked` project as a hard failure — blocks are pre-existing workflow-dir drift, unrelated to the agent; report and move on.
