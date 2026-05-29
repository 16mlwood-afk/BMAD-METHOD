# Step 06 — Deliver to Main & Guide the User

**Goal:** Make the design-system artifacts reachable on `origin/main` (so Claude Design's GitHub ingest can read them), then walk the user through the claude.ai/design form. This step closes the "file written but not on main" gap per `delivery_to_main`.

---

## 1. Delivery gate

If `{delivery_mode}` = `skip` (config `delivery.onboard-design-system: skip` or `--no-deliver`): emit the `delivery_to_main` §5 skip warning, leave the GitHub link in the card marked `LOCAL ONLY` with the local-folder attach instructions, and jump to §3.

Otherwise run the **`delivery_to_main` §3 sequence** for the artifacts produced:

- `{planning_artifacts}/design-system/` (tokens.css, sample.html, README.md)
- `{planning_artifacts}/brand-identity.md`
- `docs/design-policy.md` (if created/changed this run)
- `{intake_card_path}`
- any approved real-token-surface changes from step 04 §2 (these are app code → still go through the same PR)

## 2. Run the sequence (summary — authority is delivery_to_main §3)

1. Verify artifacts are inside the active worktree (`worktree-portability` §2).
2. Commit. Type = `feat(onboard-design-system)` for the bundle + docs (design-system is new project capability, not a doc-only brief). Cite this workflow and name Claude Design as the consumer in the body.
3. Rename any `worktree-*` branch to `feat/onboard-design-system` (or `docs/` if doc-only and no app code changed).
4. `git push -u origin <branch>`.
5. Open a PR to `main`. Body: what the design system is, that Claude Design will ingest the bundle via GitHub, and the post-merge test plan (paste link → form → generation).
6. Merge (`--squash --delete-branch`; `--admin` only per the project CLAUDE.md quota-exhausted escape, and only if no `src/` changes).
7. Verify merge: `gh pr view <num> --json state,mergedAt,mergeCommit` → `MERGED` is authoritative (the local checkout error when `main` is held by the parent worktree is expected).
8. Fast-forward main from the parent worktree so subsequent sessions see the artifacts.
9. Capture the **live `origin/main` URL** of `{frontend_subfolder}` / the bundle.
10. Exit the worktree (`action: remove`, `discard_changes: true` is normal after squash).

## 3. Finalize the intake card

Flip the card's "Link code on GitHub" field from `PENDING DELIVERY` to the live `origin/main` URL captured in §2.9 (or the `LOCAL ONLY` attach path if delivery was skipped). Re-write `{intake_card_path}`.

## 4. Guide the user through the form

Present the final walkthrough:

```
✅ Design system delivered to origin/main. Configure Claude Design now:

1. Go to claude.ai/design → "Set up your design system"
2. Company name + blurb:   <paste from card>
3. Link code on GitHub:    <live repo URL>  (attach subfolder: <frontend_subfolder>)
4. .fig file:              <path | none — optional>
5. Fonts/logos/assets:     <list | none — optional>
6. Any other notes:        <paste from card>
7. Click "Continue to generation"

Claude Design will now treat THIS system as the priority source that outranks
individual design-handoff briefs. Re-run this workflow's step 04-06 (or
modify-design-policy → here) whenever the system changes, so the GitHub source
Claude Design reads stays current.
```

## 5. Done

The workflow is complete only when: artifacts are on `origin/main` (or explicitly local-only), the intake card has a live link, and the user has the field-by-field walkthrough. Surface the merged PR URL and the card path.
