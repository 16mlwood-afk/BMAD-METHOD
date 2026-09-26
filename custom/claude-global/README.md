# Global Claude assets (versioned backup)

`~/.claude/` is **not** git-tracked. These global assets live there at runtime but their
canonical, version-controlled copies live here so they have backup + rollback.

| Asset | Runtime location | Restore with |
|---|---|---|
| `skills/bmad-onboard/` | `~/.claude/skills/bmad-onboard/` | `~/bmad-method-v6/install-global-assets.sh` |
| `new-project-bootstrap.snippet.md` | the `### New project bootstrap` section of `~/.claude/CLAUDE.md` | paste by hand (the global CLAUDE.md is hand-maintained; not auto-merged) |

## Workflow

- **Source of truth is HERE.** Edit the skill in `custom/claude-global/skills/bmad-onboard/`, commit,
  then run `install-global-assets.sh` to push it to `~/.claude/`. (Editing only the `~/.claude/` copy
  leaves it unbacked-up and will drift.)
- `onboard-project.sh` calls `install-global-assets.sh` best-effort on every run, so a wiped or stale
  global skill self-heals the next time you onboard a project.
- After cloning the fork on a new machine, run `install-global-assets.sh` once.
