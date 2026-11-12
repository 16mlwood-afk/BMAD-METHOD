### New project bootstrap
To onboard a new project to the fork, run **one command** — it is idempotent and self-verifying:

```
~/bmad-method-v6/onboard-project.sh [<project-dir>] [--name <name>] [--phase greenfield|brownfield|mixed]
```

Defaults: `<project-dir>` = cwd, `--name` = dir basename, `--phase` = greenfield. The script does
git init, clones the reference project's `_bmad/` base (per `~/.bmad-reference`), sanitizes
project-specific config, creates `CLAUDE.md` from the template, registers the project in
`~/.bmad-targets`, and runs the sync (custom workflows, skills, hooks, commands). The `bmad-onboard`
skill wraps this for natural-language invocation ("install the BMAD fork", "set up BMAD here").

**Do NOT run `bmad-cli install` / `npx bmad-method install`.** The installer now produces the
upstream v6.8.0 skills layout (`.claude/skills/bmad-*`), which the fork's custom layer and
`sync-bmad-workflows.sh` do not support — a fresh install yields vanilla BMAD with none of the fork's
safety layer. All projects run the 6.0.4 base + custom overlay layout, which `onboard-project.sh`
reproduces. (Migrating the fork to the v6.8.0 skills layout is planned in
`~/bmad-method-v6/custom/MIGRATION-v6.8-skills-plan.md`.)

