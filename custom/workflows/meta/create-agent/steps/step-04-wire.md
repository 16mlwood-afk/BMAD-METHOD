---
name: 'step-04-wire'
description: 'Sync the custom/agents/ lane into THIS project only (--only), auto-generating the command wrapper, then verify the slash command resolves here'
---

# Step 4: Sync the Lane & Verify Invocable

**Progress: Step 4 of 4** — Final step

## RULES:

- FULLY AUTONOMOUS. No user interaction. No menus. No halting.
- **Scope the sync to this project: `--only "{project_root}"`. Never a bare fleet fan-out.** Authoring an agent is not authorisation to distribute it to 14 projects — see §1.
- **The sync generates the wrapper — do NOT hand-write it.** `sync_agents_for_project` mirrors the persona into the project's `_bmad/bmm/agents/` AND emits the `.claude/commands/bmad/bmm/agents/{agent_slug}.md` wrapper. Running the sync IS the wiring step.
- Verify the slash command resolves in the current project before reporting success. A persona in the lane that was never synced is NOT invokable.

## CONTEXT

From step 3 the persona exists at `{agent_file}` = `{bmad_root}/custom/agents/{agent_slug}.md` (the fork lane). It is in the lane but not yet in any project. This step syncs it into **this project** + generates its wrapper, then confirms `/bmad:bmm:agents:{agent_slug}` resolves in `{project_root}`. Fleet distribution is deliberately out of scope here and rides the batched window per `STATUS.md`.

## SEQUENCE OF INSTRUCTIONS

### 1. Run the Sync

Deliver the persona and auto-generate its wrapper **into this project only**:

```bash
"{bmad_root}/sync-bmad-workflows.sh" --only "{project_root}"
```

**`--only` is mandatory, and the reason is not stylistic.** A bare invocation is a **14-project
fan-out** — a fleet distribution, run autonomously, for one persona. `STATUS.md`'s ⛔ fleet re-sync
STOP forbids exactly that: *"no `custom/` change gets its own sync window."* Authoring an agent is
not authorisation to distribute it. So this step syncs the project the user is standing in — where
the "is it actually invokable?" guarantee is checkable in section 2 — and **fleet distribution rides
the batched window**, like every other `custom/` change.

Do NOT add a second sync command, a project list, or a filter of your own. `--only PATH` is existing
`sync-bmad-workflows.sh` support; reuse it so "what gets synced" stays single-sourced in the script.

Read the output:

- Look for the `OK    agents (N agent(s) synced)` line — this project received the new persona + a
  generated wrapper. Section 2 verifies it landed; do not infer success from the line alone.
- A `blocked` result for this project means **pre-existing local-only content** in its workflow dirs,
  unrelated to this agent (the block check scans workflow `SYNC_DIRS`, never `_bmad/bmm/agents/`).
  Report it plainly and stop — the agent is authored and in the lane, but **not yet invokable here**.
  Do not hand-materialize the files to work around it: the persona's home is the lane, the sync owns
  the project copies, and writing into `{project_root}/_bmad/` is forbidden by `workflow.md`.

The wrapper the sync writes has this exact shape — **reference only**, so you can recognise a correct
wrapper in section 2. It is never hand-written:

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

If either file is missing, the sync did not deliver — **report that, do not paper over it.** Say the
agent is authored and in the lane but NOT invokable in this project yet, name the reason from the
sync output, and leave the fix to a deliberate re-sync. Writing the two files by hand would put the
persona in `{project_root}/_bmad/bmm/agents/`, which `workflow.md` forbids: that path is
upstream-mirrored with `rsync --delete`, so a hand-placed copy is wipe-exposed and diverges from the
lane the moment either changes.

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
Agent "{agent_name}" ({agent_title}) built and INVOKABLE in this project.

Files:
- {bmad_root}/custom/agents/{agent_slug}.md   (persona — the fork lane, source of truth)
- synced → {project_root}/_bmad/bmm/agents/{agent_slug}.md   (persona, this project)
- synced → {project_root}/.claude/commands/bmad/bmm/agents/{agent_slug}.md   (wrapper, auto-generated)

Invoke it now:
  /bmad:bmm:agents:{agent_slug}

Routes/owns: {one-line summary of the lane, or "advisor — answers {domain} questions"}

Distribution: this project synced; fleet distribution rides the batched window per STATUS.md.
Finalize in the fork (durable + pushed):
  git -C {bmad_root} add custom/agents/{agent_slug}.md && git -C {bmad_root} commit -m "..." && git -C {bmad_root} push myfork custom
```

---

## SUCCESS METRICS

- Sync run **scoped with `--only "{project_root}"`** — never a bare fleet fan-out
- `/bmad:bmm:agents:{agent_slug}` resolves in `{project_root}` (both files present, wrapper points at persona)
- Persona is lane-homed (`custom/agents/`), not project-local, and wipe-safe (sync_agents re-writes after the upstream `--delete`)
- Reach reported honestly — **this project**, with fleet distribution named as pending the batched window, never implied as done
- Fork commit+push command surfaced for finalization

## FAILURE MODES

- **Running a bare `sync-bmad-workflows.sh`** — a 14-project fan-out for one persona, autonomously, against `STATUS.md`'s ⛔ fleet re-sync STOP. Authoring is not authorisation to distribute. Always `--only "{project_root}"`.
- **Claiming the agent is "distributed everywhere"** — it is invokable HERE. The other projects get it on the batched window, and saying otherwise reports a fan-out that was never authorised.
- **Hand-writing the wrapper, or hand-placing the persona into `{project_root}/_bmad/bmm/agents/`** — the sync owns both files, and that path is upstream-mirrored with `rsync --delete` (wipe-exposed, and forbidden by `workflow.md`). A failed sync is reported, not worked around.
- **Reporting success without running the sync** — the persona in the lane is not invokable in any project until the sync delivers it.
- Slug mismatch between the persona filename and the wrapper's `@_bmad/...` reference — wrapper resolves but loads nothing (the sync keeps these in lock-step).
- Treating a `blocked` result as the agent having failed — the block is pre-existing workflow-dir drift, unrelated to the agent. The persona is fine; it is just not invokable here yet. Say exactly that.
