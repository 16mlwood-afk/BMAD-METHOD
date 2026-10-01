---
name: create-agent
description: 'Create a new BMAD agent persona from a short brainstorm AND auto-wire its slash-command wrapper. Autonomously builds the persona file and the command wrapper so the agent is invokable the moment the workflow finishes. Use when the user says "create an agent" or "I want a named agent that fronts X"'
main_config: '{project-root}/_bmad/bmm/config.yaml'
metadata:
  # Backfilled 2026-07-31. These workflows predate provenance stamping; `unknown` is the honest
  # value, not a placeholder to fill in later. Anything authored from now on is stamped by
  # create-workflow at build time (STD-SKILLPROV-001 §3).
  created_at: 'unknown'
  authored_by: 'unknown'
  discovery_performed: false
  source_research: []
  override_reason: 'backfilled — authored before create-workflow stamped provenance'
---

# Create Agent

**Goal:** From a brief brainstorming conversation, autonomously build a complete, **invokable** BMAD agent — the persona `.md` AND its command wrapper — without further user input after the brainstorm. The agent must resolve as a slash command the moment this workflow finishes.

**Your Role:** You are an agent architect who has deep knowledge of BMAD's persona XML format, the activation/persona/routing/menu structure, and — critically — the command-wrapper indirection that makes a persona invokable. The user describes the persona they want (a named human like Devon or Vera who fronts a lane of workflows); you deliver a working, callable agent.

---

## WHY THIS WORKFLOW EXISTS

`create-workflow` auto-scaffolds a workflow into the fork's `custom/workflows/` lane, and the sync (`generate_command_content()`) emits its `.claude/commands/` wrapper from frontmatter. **Custom agents now have the exact equivalent.** As of the `custom/agents/` sync lane (commit `0cd582d4`), authoring an invokable, distributed agent is a clean three-move flow: render the persona, drop it in the lane, sync.

The lane closes the three gotchas that used to make this a manual dance:

1. **A persona `.md` alone is NOT invokable** — it needs a wrapper at `.claude/commands/bmad/bmm/agents/<name>.md`, or the slash command resolves to "Unknown command." **The sync now generates that wrapper** for every file in `custom/agents/` (`sync_agents_for_project`), the same way it does for workflows. You no longer hand-write it.
2. **Custom agents are now fork-distributed** — a persona in `custom/agents/<slug>.md` is mirrored to every project's `_bmad/bmm/agents/` on sync, not stranded in one project.
3. **Lane-distributed agents are wipe-SAFE.** `sync-bmad-workflows.sh` does mirror `_bmad/bmm/agents/` from the upstream reference with `rsync -a --delete`, BUT `sync_agents_for_project` runs *after* that mirror and re-writes every `custom/agents/` persona — so the upstream `--delete` can't strip a lane agent. (A persona written straight into a single project's `_bmad/bmm/agents/` — the old pattern — is still wipe-exposed; that is exactly why this workflow writes to the lane instead.)

So `create-agent` writes the persona to the fork lane and runs the sync **scoped to this project**
(`--only "{project_root}"`); the agent is invokable here the moment that finishes, and reaches the
other projects on the next batched broad-sync. The narrow scope is deliberate: a bare sync is a
14-project fan-out, and `STATUS.md`'s ⛔ fleet re-sync STOP rules that no single `custom/` change
gets its own distribution window. Authoring an agent is not authorisation to distribute it.

---

## WORKFLOW ARCHITECTURE

This uses **step-file architecture**:

- Step 1 is the only interactive step — a short brainstorm to define the agent's identity and lane
- Steps 2-4 are fully autonomous — no user input, no menus, no halting
- State persists via variables: `{agent_name}`, `{agent_slug}`, `{agent_title}`, `{agent_icon}`, `{agent_role}`, `{agent_description}`, `{agent_lane}`, `{agent_routes}`, `{agent_escalation}` (optional, contract §4), `{agent_style_example}` (optional, contract §6), `{agent_persona}`, `{agent_file}`, `{wrapper_file}`, `{bmad_root}`, `{project_root}`

### Step Processing Rules

1. **READ COMPLETELY**: Always read the entire step file before taking any action
2. **FOLLOW SEQUENCE**: Execute all numbered sections in order
3. **Steps 2-4 are AUTONOMOUS**: Never halt, never present menus, never wait for input. Make expert decisions and proceed.
4. **SAVE STATE**: Carry variables between steps
5. **LOAD NEXT**: When directed, read fully and follow the next step file

### Critical Rules

- **Step 1 only**: interact with the user
- **Steps 2-4**: fully autonomous, no exceptions
- **The persona in the lane is not the whole deliverable** — the agent must end up *invokable*. The sync generates the wrapper, so step-04 runs the sync and verifies the slash command resolves in the current project. A persona sitting in `custom/agents/` that was never synced is an incomplete run.
- **ALWAYS** follow the established persona XML format from sibling agents (`design-pm`/Devon, `data-integrity-lead`/Vera) — same `<activation>` / `<persona>` / routing / `<menu>` shape. Do NOT invent a new agent format.
- **ALWAYS** cover the **persona content contract** (`custom/workflows/meta/create-agent/persona-content-contract.md`) — the 8 persona sections mapped onto that XML, plus the human-tone behavior floor (acknowledge → clarify → close-loops). It is a SOFT gate, enforced by how step-03 *scaffolds* the file: real content where inferable, an obvious `TODO(persona)` marker only where genuinely un-inferable. The build stays fully autonomous and the agent is invokable on finish — the contract never adds an interactive halt.
- **The persona lives in the fork's `custom/agents/` lane, exactly like `create-workflow` writes to `custom/workflows/`.** This workflow writes the persona to `{bmad_root}/custom/agents/{agent_slug}.md`; the sync (`sync_agents_for_project`) mirrors it into every project's `_bmad/bmm/agents/` AND generates the `.claude/commands/bmad/bmm/agents/` wrapper. Do NOT write the persona straight into a project's `_bmad/` — that path is upstream-mirrored with `rsync --delete` and the agent would be wipe-exposed and undistributed.

---

## INITIALIZATION

### Configuration Loading

Load config from `{main_config}` and resolve:

- `user_name`, `communication_language`
- `autonomous_mode`, `autonomous_rules`
- `date` as system-generated current datetime

### Path Resolution

- `{bmad_root}` = the BMAD fork root directory — **where the persona is written** (`{bmad_root}/custom/agents/{agent_slug}.md`). Resolution order:
  1. Check if `~/bmad-method-v6/sync-bmad-workflows.sh` exists → use `~/bmad-method-v6/`
  2. Search upward from the installed workflow path for `sync-bmad-workflows.sh`
  3. Ask the user (non-autonomous only)
  If it can't be resolved, HALT — without the fork root there is no lane to write to and no sync to run. (Fall back to reading sibling-agent voice references from `{project_root}/_bmad/bmm/agents/`, but the persona itself must go to the fork.)
- `{agent_file}` = `{bmad_root}/custom/agents/{agent_slug}.md` (the persona — the one file this workflow authors).
- `{project_root}` = the current project's repo root. NOT a write target — the sync writes `_bmad/bmm/agents/` and `.claude/commands/` here; the workflow only *reads* it to verify the agent landed and resolves.
- `{installed_path}` = `{project-root}/_bmad/bmm/workflows/meta/create-agent`

### Write-Guard Awareness

The persona is written to `{bmad_root}/custom/agents/` — **fork paths are allowlisted by the PreToolUse edit-guard**, so a normal `Write` works (no heredoc-bypass needed). Do NOT write into `{project_root}/_bmad/` — that path *is* guarded, and it's the wrong home anyway (the sync owns it). The project's `_bmad/bmm/agents/` persona and `.claude/commands/` wrapper are both produced by the sync in step-04, not by direct writes here.

---

## EXECUTION

Read fully and follow: `{project-root}/_bmad/bmm/workflows/meta/create-agent/steps/step-01-brainstorm.md` to begin.
