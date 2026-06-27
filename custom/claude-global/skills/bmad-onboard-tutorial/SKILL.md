---
name: bmad-onboard-tutorial
description: >
  Guided "first lived-in operations" walkthrough for a freshly onboarded project, run right after
  onboard-project.sh completes. Load when the user says "walk me through the new project", "teach me
  the gates", "do the onboarding tutorial", "run the first guided tasks", or when onboard-project.sh's
  closing output points here. Demonstrates the safety gates by DOING — a safe sync dry-run and a first
  feature-branch + tests + commit — so the repo is not just configured but exercised once under the rails.
---

# Onboarding tutorial — teach by doing

`onboard-project.sh` is the deterministic spine: it wires the BMAD layer and stamps the marker. This
skill is the **probabilistic teaching layer** that runs *after* it — it does not re-onboard anything.
Its job: make the project feel lived-in by walking the user through two canonical operations under the
real gates, narrating what each gate does and where the override is.

Run this only against a repo that is already onboarded (a `_bmad/bmm/config.yaml` with an
`onboarding:` stamp exists). If there's no stamp, stop and point at `bmad-onboard` first.

## Task 1 — a safe sync under the gates (read-only demonstration)

Goal: show the user how the fork's sync classifies files and protects local work, **without changing
anything**.

1. State the target: `~/bmad-method-v6/sync-bmad-workflows.sh --only <this-project>`.
2. Explain the protection before running: the sync keeps a per-project manifest
   (`_bmad/_config/sync-manifest.txt`) and only ever removes a target-only file if it is in the
   manifest AND its bytes still match the recorded hash — every other state fails closed to BLOCKING
   to protect local work. (This is the content-hash hardening that fixed the sync-deadlock fork-gap.)
3. Run the scoped sync for this project and read back what it reports — workflows/skills/hooks/commands
   refreshed, anything blocked-and-why. Narrate the classification on real output.
4. If anything is blocked as "local-only content," DO NOT force past it — surface it as the gate
   working as intended and explain the manual reconciliation path. This is the lesson, not a failure.

## Task 2 — first feature branch + tests + commit (the delivery rails)

Goal: walk the standard change loop once so the branch/test/commit discipline is muscle memory.

1. **Worktree first** if the project's CLAUDE.md requires it (most do) — `EnterWorktree`. State why:
   collisions silently overwrite; the worktree cost is near zero.
2. **Branch name**: propose a descriptive `<type>/<desc>` (e.g. `chore/onboarding-smoke`). Rename any
   auto-generated branch before committing.
3. **A tiny, real change with a test.** Pick something genuinely small and verifiable (a constant, a
   pure helper) so the loop — not the feature — is the point. Write the test next to the source.
4. **Show the diff, run the tests**, report pass/fail honestly. If the project has a pre-flight
   build/type-check, run it and surface any pre-existing errors rather than absorbing them.
5. **Commit** on the branch (do not push/PR/merge unless the user asks — those are the side-effecting
   steps that always stay the owner's call). Then explain the rest of the path the project uses
   (rebase → push → PR → merge → deploy) per its CLAUDE.md, without taking those steps.
6. **Clean up** the worktree when done if nothing is left in flight.

## Posture

- This is a demonstration, not autonomous execution — narrate each gate as you hit it, name the
  override path, and let the user drive the decision points (what the change is, whether to push).
- Keep it to these two operations. Deeper feature work is the normal build loop (`quick-spec` /
  `dev-story` / the design-* workflows), not this tutorial.
- If the project is a `fork-of-upstream` topology, also point out the upstream guard: deliver to your
  own origin; `git push upstream` / force-push / hard-reset-onto-upstream are blocked (override
  `BMAD_ALLOW_UPSTREAM_PUSH=1`).
