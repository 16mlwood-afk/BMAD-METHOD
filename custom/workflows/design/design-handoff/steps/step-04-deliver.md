---
name: 'step-04-deliver'
description: 'Deliver the brief to the repository default branch so external consumers (Claude Design, downstream synthesize, design-implement) can read it. Implements shared/delivery-to-main.md for design-handoff.'

workflow_path: '{project-root}/_bmad/bmm/workflows/design/design-handoff'
thisStepFile: './step-04-deliver.md'
---

# Step 4: Deliver

**Goal:** Commit the brief written in step-03, push the worktree branch, open a PR, and merge to `main` so external consumers can read the brief at its hand-off URL. Without this step, the brief lives only on the operator's local disk and the consumer cannot find it.

This step implements `shared/delivery-to-main.md` for `design-handoff`. The shared policy carries the full rationale; this step is the executable form.

**Voice — Rhea, Design Steward** (`shared/workflow-personas.md`): the close is a hand-off to the next consumer, not a recap of what you did. Emit the consumer-facing close-out shape in §10; **process narration is forbidden by default** (no "I did X then Y", no branch/PR choreography, no workflow-history or decision diary unless the user explicitly asks for the trace). A one-line re-orientation or a genuine implementation risk is allowed; a process essay is not. Governing standard: `shared/close-out-contract.md` (STD-CLOSEOUT-001); workflow.md § "OUTPUT CONTRACT & WORKFLOW-FEEDBACK ROUTING" points to it.

---

## AVAILABLE STATE

From step-03:
- `{output_path}` — absolute path to the brief on disk
- `{output_filename}` — basename of the brief
- `{output_path_relative_to_repo_root}` — for PR body / hand-off prompt
- `{github_repo_url}` — for verification
- `{feature_name}`, `{target_slug}`, `{handoff_mode}` — for commit / PR text

From step-03c (Gate 1 — brief-ready):
- `{gate1_artifact_path}` — the `brief-adversary-{target_slug}-{date}.md` written by the gate. Staged in the SAME commit as the brief (§3). Empty when the gate was skipped.
- `{brief_body_sha}` / `{brief_body_sha_after_repair}` — the review binding (brief body only, frontmatter excluded). Re-checked in §0a.
- `{gate1_paused}` / `{gate1_owner_decisions}` — the ONE Phase-1 condition that stops this step. See §0a.

From step-03b (only when `{has_analytics_band}` is `true`):
- `{rationale_output_path}` — absolute path to the analytics rationale on disk
- `{rationale_path_relative_to_repo_root}` — for the final surface
- If `{has_analytics_band}` is `false`, no rationale file exists — every "rationale" reference below is a no-op.

From config:
- `{delivery_mode}` — `auto` (default) or `skip` (from `_bmad/bmm/config.yaml`'s `delivery.design-handoff` field, if set)
- `{user_name}`

---

## EXECUTION SEQUENCE

### 0. Live-Apply Check — a brief regen during an active apply is a BLOCKED operation

**Before writing or delivering a brief for surface S, read `<main-checkout>/.claude/wip-register.yaml`
and check for an ACTIVE `design-implement` / `design-ingest` / apply claim on S.** If one exists and
is held by another `claimed_by_session_id`, **HALT** — do not write the brief, do not deliver it.

**Why this is a halt and not a caution.** Regenerating a brief mid-apply *forks the design*: the
applying session is implementing bundle A while the brief that justifies it silently becomes bundle
B's. The loss is real, already-built work, and it surfaces late. On **2026-07-20** this exact
collision binned **two full build → verify → PR cycles** in this project. On **2026-07-25** it was
caught only because the session happened to read the register first — judgment, not a system.

**Correct sequence:** let the apply land (merged or explicitly abandoned), confirm no active claim
remains on S *or its sibling surfaces*, then regenerate. Sequencing is the **owner's** call — a
handoff may not resolve it by proceeding.

**`status: active` is NOT the same as LIVE — run dead-claim detection before halting.** Nothing
releases an abandoned claim, so `active` rows accumulate indefinitely and a literal read of the
paragraph above deadlocks this workflow **permanently** on any surface that was ever claimed. That is
a stuck ladder, not a safety property, and it is what makes agents stop reading the register at all.
So the ACTIVE check above resolves through **`{project-root}/_bmad/bmm/workflows/shared/parallel-sessions.md` §C4
(Dead-claim detection — zombie vs genuine in-progress)**, which already owns this question for the
fork. Do not restate its test here and do not invent a second one; apply §C4's liveness signals to the
apply-claim shape:

| §C4 signal | Its apply-claim form |
|---|---|
| claiming worktree / branch still exists | the claimed branch or worktree exists **and has advanced since `claimed_at`** |
| holding process still running | a manifest **current-editor marker** is held on the surface's manifest (`.claude/manifest-locks/`) |
| recent `at` **AND** evidence of progress | within §C4's freshness window **and** the targeted manifest/artifact has not been superseded, nor its successor chain merged |

**Any signal live ⇒ the claim is LIVE ⇒ HALT exactly as above.** §C4's **conservatism rule** binds
here too: on genuine ambiguity, prefer to halt — refusing costs one re-run, proceeding past a live
apply costs somebody's build.

When you do proceed past a claim that is dead on every signal, that judgement is yours to own:
**name the row, its age, and each signal you checked in the close-out**, and recommend the owner
release it. Never proceed silently. Never rewrite or release another session's claim to clear your own
path — §C4 permits *reclaim* by the story-claim protocol, not unilateral release by a handoff.
An unparseable, missing, or future-dated `claimed_at` is UNKNOWN, never young: treat as LIVE and halt.

**What to do instead of halting silently:** report the conflicting claim (surface, `claimed_by`,
`claimed_by_session_id`), and message the holding session via the agent mailbox with anything that
changes their in-flight work — e.g. a policy version that moved under them. Then stop and let the
owner sequence it.

> **Enforcement honesty.** The deterministic tier is a `PreToolUse` **ASK** on `Edit|Write` of
> `design-brief-*.md` (`.claude/hooks/brief_regen_guard.py`, 12-case golden suite, fails OPEN on an
> unreadable register, conservative surface matching). It is **machine-local — it does NOT ship with
> the fork**, so in any project without it this section is the only tier. That is exactly the
> prose-consumer blind spot: a gate constrains a tool call, never the instruction that tells the model
> to make it. Treat this step as load-bearing, not as a restatement of the hook.

### 0a. Gate 1 Check — one pause condition, and a re-bound review

**Gate 1 (step-03c) is WARN-ONLY in Phase 1, and warn-only is NOT uniform.**

- **Instrument results never stop this step.** A fired probe, an adversary finding, an `open`
  disposition, an unavailable checker: recorded in `{gate1_artifact_path}`, surfaced in §10,
  and delivery proceeds. There is no finding count and no severity that blocks delivery.
- **`{gate1_paused}` is the ONE condition that does.** It is true iff Gate 1 found a genuine
  missing OWNER product/design decision. Then: **do not deliver this brief**, do not invent the
  value, and do not hand the contract to Claude Design with the decision unresolved. Surface
  the decision (it is the only thing the owner sees from the gate) and resume here when it is
  answered. Say plainly that **this is not the gate blocking on findings — it is the route
  refusing to guess a decision that is the owner's to make.** This holds in `autonomous_mode`.

**Re-bind the review before staging.** The review is only about the text it read:

```bash
python3 ~/bmad-method-v6/tools/check-brief-readiness.py "{output_path}" --body-sha
```

If it differs from `{brief_body_sha_after_repair}` (or `{brief_body_sha}` when no repair ran),
the brief body changed after the review — **the review is INVALID; re-run step-03c** before
delivering. A frontmatter-only edit cannot trigger this (the digest excludes frontmatter by
construction), so supersede bookkeeping and `last_modified_date` move freely.

If Gate 1 was skipped, `{gate1_artifact_path}` is empty; note the skip in §10 and continue.

Full contract: `shared/design-gate-artifacts.md`.

### 1. Delivery Skip Check

Determine whether to run the delivery sequence at all.

```bash
# Read delivery config from _bmad/bmm/config.yaml — look for:
#   delivery:
#     design-handoff: skip
```

Resolve `{delivery_mode}`:
- If the user's invocation contains `--no-deliver` → `{delivery_mode}` = `skip`
- Else if `_bmad/bmm/config.yaml` has `delivery.design-handoff: skip` → `{delivery_mode}` = `skip`
- Else → `{delivery_mode}` = `auto`

If `{delivery_mode}` = `skip`, emit the warning from `shared/delivery-to-main.md` §5 and exit step-04. The brief stays on disk in the worktree; the operator is on the hook for delivery later.

If `{delivery_mode}` = `auto`, proceed to step 2.

### 2. Verify Worktree Containment

Per `shared/worktree-portability.md` §2, the brief must be inside the current worktree before delivery — otherwise the PR will not include it.

```bash
project_root=$(git rev-parse --show-toplevel)
case "{output_path}" in
  "${project_root}"/*) : ;;  # ok — brief is inside the worktree
  *) halt with shared/worktree-portability.md §4 diagnostic ;;
esac
```

### 3. Stage and Commit the Brief

Stage the brief, and the rationale too when one was written (`{has_analytics_band}` is `true`) — both belong in the same commit so a brief on `main` always has its rationale beside it.

**Use `git add -f`.** Most projects gitignore `/_bmad-output/` (the `bmad-artifacts-untracked-main-only` posture), so a plain `git add` of a brief is silently rejected as ignored — it stages nothing, the commit reports "no changes", and the push ships an EMPTY branch that looks delivered. The `-f` flag is mandatory for delivery-bound artifacts under a gitignored path. (See `shared/delivery-to-main.md` §3.) Note: because existing briefs are **force-tracked despite the ignore**, a re-run's NEW files stay invisible to plain `git status` / `git add` while the superseded predecessor (already tracked) shows as modified — do not trust plain `git status` to reveal the new artifacts; always `-f`-add them by explicit path.

**Pre-stage wrong-tree guard (run BEFORE `git add`).** Catch the silent split where the brief was written to the MAIN checkout instead of this worktree (step-03 §1 "Bind every read AND every write to THIS tree"). Conservative — fires ONLY when we are inside a linked worktree AND the brief is present in the main checkout but absent here:

```bash
repo=$(git rev-parse --show-toplevel)
main_root=$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')   # main checkout = first entry
rel="{output_path_relative_to_repo_root}"
if [ "$repo" != "$main_root" ] && [ ! -e "$repo/$rel" ] && [ -e "$main_root/$rel" ]; then
  echo "HALT: brief was written to the MAIN checkout ($main_root), not this worktree ($repo)."
  echo "Fix — copy the new brief + rationale (and any superseded-predecessor flips) into the worktree, then restore main to pristine:"
  echo "  cp \"$main_root\"/_bmad-output/implementation-artifacts/*{target_slug}*.md \"$repo\"/_bmad-output/implementation-artifacts/"
  echo "  cd \"$main_root\" && git checkout -- _bmad-output/implementation-artifacts/   # revert the flip edits; rm any new-date files written to main"
  exit 1
fi
```

There is no legitimate "deliver from the wrong tree" case, so the recipe IS the resolution — no override path. This mirrors the post-`git add` stage assertion below; it turns the cryptic `pathspec did not match` into a fix recipe.

**Pre-stage brief-contract assertion (run BEFORE `git add`).** A deterministic internal-consistency gate on the just-written brief. The step-03 §3 self-review already has a "§7 Surface Inventory / structural-contract `frames`" checkbox, but that is **probabilistic** — the model self-attests — and the only hard gate today fires *downstream* (`design-synthesize` Gate 1f / `design-implement` §2f), so it never bites if those consumers don't run. This assertion mechanically verifies the **Block B `frames` contract** — the machine-readable frame list `design-implement` step-01 §SHARED.1b diffs the bundle against — is present, non-empty, unique, and mirrored in the §7 body, at the producer, regardless of self-attestation or any downstream run. **Scope (honest cede):** this checks *internal consistency* of the artifact only. It does NOT verify completeness-against-the-schema (whether every drawer that SHOULD exist was captured) — that needs the gather context and stays with step-01 §5f derivation + the step-03 §3 self-review + the downstream gates (see RULES).

```bash
brief="{output_path}"
# Extract the Block B `frames:` list (inline `[a, b]` or block `- a`) from the YAML frontmatter, one id per line.
frames=$(awk '
  NR==1 && $0=="---"{infm=1; next}
  infm && $0=="---"{exit}
  infm && /^frames:/{
    if ($0 ~ /\[/){ s=$0; sub(/^[^[]*\[/,"",s); sub(/\].*/,"",s); gsub(/,/," ",s); print s; next }
    blk=1; next }
  infm && blk && /^[[:space:]]*-[[:space:]]/{ s=$0; sub(/^[[:space:]]*-[[:space:]]*/,"",s); print s; next }
  infm && blk && /^[^[:space:]]/{ blk=0 }
' "$brief" | tr -d "\"'," | tr -s " " "\n" | sed '/^$/d')

n=$(printf '%s\n' "$frames" | sed '/^$/d' | wc -l | tr -d ' ')
if [ "$n" -eq 0 ]; then
  echo "HALT: brief frontmatter has no non-empty 'frames:' list (brief-revision-policy.md §2 invariant 1a)."
  echo "  Every brief declares >=1 frame (the primary surface). Without it the brief ships UNVERIFIED and design-implement's §SHARED.1b gate cannot bite."
  echo "  Fix: emit 'frames:' in Block B mirroring the §7 Surface Inventory rows (step-03 §2 structural-contract fields), then re-run delivery."
  exit 1
fi
dupes=$(printf '%s\n' "$frames" | sort | uniq -d)
if [ -n "$dupes" ]; then
  echo "HALT: duplicate frame id(s) in 'frames:': $dupes"
  echo "  Frame names must be unique — they key brief -> rendered frame -> design-implement grid row at every hop."
  exit 1
fi
# Body = brief minus frontmatter. Every declared frame id must appear in it (frames mirrors the §7 rows, never a divergent list).
# while-read + case (NOT `for f in $frames`): zsh does not word-split unquoted vars, so a for-loop would iterate once over the whole blob and silently miss everything. This form is correct in both bash and zsh.
body=$(awk 'NR==1 && $0=="---"{infm=1;next} infm && $0=="---"{infm=0;next} !infm{print}' "$brief")
missing=""
while IFS= read -r f; do
  [ -z "$f" ] && continue
  case "$body" in *"$f"*) : ;; *) missing="$missing $f" ;; esac
done <<EOF
$frames
EOF
if [ -n "$missing" ]; then
  echo "HALT: frame id(s) declared in 'frames:' but absent from the brief body / §7 Surface Inventory:$missing"
  echo "  Block B 'frames' must mirror the §7 rows exactly (identical ids). A frame in frontmatter that §7 never draws is the inconsistency design-implement §2f would later flag — cheaper here."
  exit 1
fi
# A §2a Linked Records section implies §7 lookup-drawer frames — linked records cannot have zero frames.
if printf '%s' "$body" | grep -qiE '^#+.*linked records'; then
  printf '%s' "$body" | grep -qiE 'surface inventory' || {
    echo "HALT: brief has a Linked Records (§2a) section but no §7 Surface Inventory."
    echo "  Each linked record requires one expand-in-context lookup-drawer frame (Deliverable-Completeness Principle). Add §7 + the matching 'frames:' rows."
    exit 1; }
fi
```

There is no legitimate "deliver a frames-inconsistent brief" case, so each recipe above IS the resolution — no override path (matching the wrong-tree guard). A brief that legitimately has a single frame still passes (n=1, the primary surface).

```bash
git add -f {output_path}
# Only when {has_analytics_band} is true:
git add -f {rationale_output_path}
# Only when Gate 1 ran ({gate1_artifact_path} non-empty) — the gate record belongs beside the
# brief it reviewed, in the same commit, for the same reason the rationale does.
git add -f {gate1_artifact_path}
```

**Assert the stage actually happened** — turn the silent no-op into a loud, self-correcting halt:

```bash
git diff --cached --name-only | grep -qF "$(basename {output_path})" || {
  echo "HALT: brief did not stage. The path is gitignored — re-run with: git add -f {output_path}"; exit 1;
}
```

Do not proceed to commit until the brief is confirmed staged.

Compose the commit message. Use this template (HEREDOC form to preserve formatting):

```bash
git commit -m "$(cat <<'EOF'
docs(design-handoff): {handoff_mode} brief for {feature_name}

{2-3 line description: what the brief is, what consumer will read it, what scope it covers.
For refine-screen briefs: cite the screen-review artifact this brief derives from.
For fresh-design briefs: cite the feature scope and target route.
If {has_analytics_band} is true: add a line noting the commit also includes the analytics presentation rationale (design-rationale-{target_slug}-{date}.md) — the record-of-decision behind the page-mode/band/archetype choices.}

Co-Authored-By: design-handoff workflow via Claude Code
EOF
)"
```

If a pre-commit hook fails on this commit, the brief itself is unlikely to have caused it (markdown in `_bmad-output/`). Read the hook output, fix the underlying issue, re-stage, and create a NEW commit per the project's commit guidance.

### 4. Rename the Worktree Branch (if auto-generated)

Worktrees created via `EnterWorktree` start on an auto-generated name like `worktree-<random>`. Rename before pushing so the PR carries a meaningful identifier.

```bash
current=$(git branch --show-current)
case "$current" in
  worktree-*)
    new_name="docs/design-brief-{target_slug}-$(date +%Y%m%d)"
    git branch -m "$new_name"
    ;;
esac
```

The date suffix is load-bearing, not cosmetic: material revisions re-run on the SAME slug by design (brief-revision-policy), and delivery branches leak on the remote (see §7 — `--delete-branch` doesn't work from worktrees), so an un-suffixed deterministic name collides with its own previous delivery.

If the branch is already conventionally named (`docs/...`, `feat/...`, etc.), skip the rename.

### 5. Push the Branch

Guard first — if the target branch name already exists on origin (a leftover from a previous same-slug delivery, possible even with the date suffix on a same-day re-run), check its PR state before pushing:

```bash
if git ls-remote --exit-code --heads origin "$(git branch --show-current)" >/dev/null 2>&1; then
  gh pr list --head "$(git branch --show-current)" --state all --json state --jq '.[0].state'
fi
```

- `MERGED` (or no PR) → the remote branch is a stale leak; safe to replace: push with `--force-with-lease`.
- `OPEN` → HALT. A genuinely in-flight delivery exists for this branch — surface it to the user instead of clobbering.

Then push:

```bash
git push -u origin "$(git branch --show-current)"
```

This sets the upstream tracking branch. Per project `CLAUDE.md` pre-push hook conventions: pushes to non-main branches skip the build check; pushes to `main` are blocked entirely (the delivery flow goes through PR).

### 6. Open the PR

Compose the PR body using this template (HEREDOC form):

```bash
gh pr create --title "docs(design-handoff): {handoff_mode} brief for {feature_name}" --body "$(cat <<'EOF'
## Summary

- {1-2 line description of what this brief is}
- {Consumer that will read it (Claude Design, design-synthesize, design-implement)}
- {Scope: refine-screen V1-V3 with edge-state variants, OR fresh-design with N open questions}
- {If {has_analytics_band} is true: "Includes an analytics presentation rationale (design-rationale-…) — a human-facing record of WHY the page-mode/band/archetype were chosen. Not a design input; Claude Design reads the brief only."}

## Why this is doc-only

Brief lives in `_bmad-output/implementation-artifacts/` — BMAD workflow artifact directory, not source, not build input. No code touched, no schema touched, no runtime impact. Safe to merge without deploy.

## Test plan

- [ ] Brief renders as readable Markdown on the PR diff
- [ ] Once merged, the consumer can read `{github_repo_url}/blob/main/{output_path_relative_to_repo_root}`
- [ ] No deploy needed — doc-only change, no runtime impact. The BMAD deploy contract (`./scripts/bmad-deploy.sh`) would also no-op on this PR

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Capture the PR number from the `gh pr create` output as `{pr_number}`.

### 7. Merge the PR

Prefer the standard squash-merge:

```bash
gh pr merge {pr_number} --squash
```

Do NOT pass `--delete-branch`: from inside a worktree it fails (`fatal: 'main' is already used by worktree...`) because the flag tries to check out `main` locally after deleting. The remote branch is deleted explicitly in §8 instead — never leave it to auto-cleanup that structurally can't run here.

If branch protection blocks the merge AND the failing check is structurally unavailable (GH Actions quota exhausted, zero-step CI failure — see project `CLAUDE.md` "CI Health Check"), retry with admin override:

```bash
gh pr merge {pr_number} --squash --admin
```

The `--admin` escape is acceptable here because the brief is doc-only — no runtime impact. **Never use `--admin` to bypass real CI signal.** The condition for `--admin` is:
- The brief is in `_bmad-output/` (doc-only), AND
- The failing check is structurally unavailable, not substantively failing.

If both conditions are not met, halt and surface to the user.

### 8. Verify Remote Merge State

`gh pr merge` may report a local error after a successful remote merge (when the parent worktree has `main` checked out). Confirm the merge via remote state:

```bash
gh pr view {pr_number} --json state,mergedAt,mergeCommit
```

Once `state` is `MERGED`, delete the remote delivery branch explicitly (this works fine from a worktree, unlike `--delete-branch`):

```bash
git push origin --delete "$(git branch --show-current)"
```

Skipping this is how stale `docs/design-brief-*` branches accumulate on origin and collide with future same-slug deliveries.

If `"state": "MERGED"`, the delivery succeeded. The local error from step 7 (if any) is non-blocking and unrelated to merge success.

If `"state": "OPEN"` and step 7 errored, the merge actually failed — surface the gh output and halt.

### 9. Fast-Forward Main from the Parent Worktree

The artifact is now on `origin/main`, but the local main checkout (outside this worktree) is one commit behind. Pull it forward so subsequent sessions see the artifact under tracked state.

```bash
# Run from the parent worktree (NOT the current worktree, which is on the now-deleted branch)
cd {parent_repo_root}
git fetch origin main
git pull --ff-only origin main
```

If `git pull` blocks on untracked files in `_bmad-output/` matching the brief's path, follow the project `CLAUDE.md` recipe — move blocking files to `.claude/orphaned-main-commits/<stamp>/`, then re-pull.

### 10. Surface Delivery Result to User — consumer-facing close-out

**The closing message is itself a handoff.** Write it for the NEXT consumer (`{consumer}` — Claude Design / `design-synthesize`), not as an account of the workflow you just ran. Do NOT narrate workflow history, provenance bookkeeping, or step mechanics — the consumer needs four things: which brief is active, what changed materially, what constraints matter, and what to do next. Lead with the active artifact and the delta; keep it short; ALWAYS append the tight "For {consumer}" block.

Emit this close-out (fill from recorded state — omit a line when its source is empty; never pad):

```
Done. The {feature_name} brief is delivered and is the active brief on `origin/main`.

Active artifact
- {output_path_filename}
{If {change_class} is `material_revision`:}
- Predecessor ({supersedes}) marked `superseded` with `superseded_by` set — one active brief for `{target_slug}`.

What changed
{If {change_class} is `material_revision`: one or two plain-language lines on the MATERIAL DELTA from step-03 — what this revision changes vs the predecessor (not the provenance mechanics).}
{If `original`: one line — new brief for `{route}`.}
- Page mode: {page_mode}. Composition: {composition_provenance} ({policy-default = the mode's standard composition; recommended-alt = a named alternative, say which in one phrase}).
- {If {has_analytics_band}: "Analytics rationale emitted beside the brief (why the presentation was chosen — for humans, not for {consumer})." else: "No analytics band, so no rationale artifact."}

{If there are substantive corrections (material_revision): a 1–3 bullet "Substantive correction" block — the real fixes a designer needs to know (e.g. a data-boundary or least-privilege correction). Skip the heading entirely if none.}

Delivery
- PR {pr_number} ({pr_url}) — MERGED. {If doc-only: "Artifact-only, no deploy." else note deploy status.}
- Completion: {completion_disposition — `pr_merged` once the brief PR is merged; `pr_open` with the reason if delivery skipped/blocked; `owner_gated_residue` naming any blocker} (STD-COMPLETION-001)
- Brief on main: {github_repo_url}/blob/main/{output_path_relative_to_repo_root}
{If {has_analytics_band}:}
- Rationale: {github_repo_url}/blob/main/{rationale_path_relative_to_repo_root} (read for context; do NOT hand to {consumer})
{If Gate 1 ran: ONE line — the artifact path, plus "Gate 1: WARN-ONLY (Phase 1) — findings recorded, delivery not blocked". Do NOT list the findings, the fired-probe count, or the dispositions table; the owner gets decisions, not evidence of work. If Gate 1 was skipped, say which skip condition fired. Never hand this artifact to {consumer}.}
{If {gate1_owner_decisions} is non-empty: this LEADS the whole close-out, above "Active artifact" — one sentence per decision, why the brief cannot answer it, what a generator will do unanswered, and the options where they exist. Say that delivery is PAUSED for this brief and that this is the route refusing to guess an owner decision, not the gate blocking on findings.}

For {consumer}
- Connect to {github_repo_url} and use `{output_path_filename}` on main as the SOLE active source brief for `{route}`.
- Interpret it as a {page_mode} {scope: redesign | new} of `{route}`.
{If scope is redesign / change_class material_revision:}
- Do NOT treat the prior implementation or any superseded brief as binding layout precedent — recompose freely.
- Preserve the brief's required frames (§ Surface Inventory), state semantics, and any data/least-privilege boundaries it names.
- {Composition guardrail from the brief: e.g. "It is a station, not a dashboard — avoid worklist/owner/analytics chrome." Derive this one line from {page_mode} + {composition_provenance} + the brief's hard constraints; do not invent constraints the brief doesn't carry.}

Outstanding (design backlog) — for the owner, not {consumer}
{Include this tail unless nothing is genuinely outstanding. Inspect the surface register if present: if `docs/surface-register.*` exists, derive the candidates from it; else derive an approximate list from existing `design-brief-*.md` + built routes. Omit a bullet whose bucket is empty.}
- Designed-not-built: {brief exists, no route yet — the cleanest build-next candidates}
- Built-no-brief (reconcile): {shipped route with no brief — flag "reconcile provenance, do NOT greenfield" when it looks like surface-identity drift}
- Unowned concept gaps: {present in briefs/PRD but no route — needs PRD/FR ownership triage}
```

**Voice (Rhea):** the prose above the code fence may carry a one-line re-orientation and any genuine implementation risk — but the emitted block stays in this consumer-facing shape. Compress; say each thing once. The goal is that `{consumer}` (or a human routing to it) knows the next step without parsing an internal-process essay.

**Completion disposition (STD-COMPLETION-001).** design-handoff is a completion workflow — its deliverable is the brief. The `Completion:` line in the Delivery block above IS its `completion_disposition` per `shared/completion-contract.md`: `pr_merged` when the brief PR merged, `pr_open` (with the reason) if `--no-deliver`/skip or a blocked merge left it undelivered, `owner_gated_residue` if something the owner must resolve remains. Ending step-04 with the brief written but no disposition declared is the invalid commentator exit (contract §3).

**Outstanding-backlog tail (register-optional, design-lane triage).** Never stop at only the surface just delivered. After the consumer-facing block, append the short owner-facing **Outstanding (design backlog)** triage above, in priority order: (1) designed-but-not-built, (2) built-but-unbriefed (reconcile — "do NOT greenfield" on surface-identity drift), (3) unowned concept gaps in briefs/PRD but not in routes. **Register-optional:** if a surface register exists (`docs/surface-register.*` — e.g. cash-recovery's `npm run surface-register`), triage from it; if none exists (most projects), derive an approximate list from existing `design-brief-*.md` + built routes — never reference a register file a project lacks. This is owner-facing, distinct from the `For {consumer}` block (STD-CLOSEOUT-001 §2 next-actor section). PROBABILISTIC guidance only — no hard gate (a Stop-hook backlog scan would be the indiscriminate-detector anti-pattern); the lever for drift is §4 of the contract. Keep it to the three bullets; omit an empty bucket.

### 11. Exit the Worktree

Per project `CLAUDE.md`, exit the worktree once the PR is merged. The squash-merge leaves the worktree's local commit orphaned (different hash from the merged squash on main) — this is normal, not a sign of unmerged work.

```
ExitWorktree action: "remove" discard_changes: true
```

`discard_changes: true` is required because the worktree's local commit is orphaned-by-squash; the content is on `main` under a different hash.

---

## RULES

- Step-04 only runs when `{delivery_mode}` = `auto`. Skip-mode emits the warning and exits at step 1.
- **The §3 pre-stage brief-contract assertion is deterministic and has no override.** It verifies only the artifact's *internal* `frames`↔§7 consistency (present / non-empty / unique / mirrored) — the Block B contract `design-implement` diffs against. It deliberately does NOT verify completeness-against-the-schema (every drawer that should exist); that dimension needs the gather context and is owned by step-01 §5f + the step-03 §3 self-review + the downstream `design-synthesize`/`design-implement` gates. Ceding it here, rather than faking a check the artifact can't support, is the design — an internal-consistency gate that bites is worth more than a completeness check that lies.
- **Fully-deterministic upgrade (not yet shipped):** the §3 assertion is a tier-3 in-flow gate — deterministic *logic*, but it only runs if the agent executes step-04. The tier-6 version is a **project pre-commit hook** on `design-brief-*.md` running the same checks, fully outside the agent. That ships on the hooks/onboarding distribution track (NOT workflow sync), so it must be added per-project and rolled out **warn-only first** before gating. Tracked as a follow-up; until then this in-flow assertion is the producer-side guard.
- Never push directly to `main`. Always via PR.
- `--admin` merge is allowed only for doc-only artifacts with structurally-unavailable CI. Document the override in the PR thread or session log.
- The merged-URL surfaced in step 10 MUST be the URL the consumer will actually read. If the operator chose `--no-deliver`, the warning says so — do not pretend the file is on main.
- **Output-shape feedback is a workflow patch, not a one-off.** If the user critiques the SHAPE of this close-out ("stop narrating history", "lead with the active artifact / material delta / next-consumer instructions", "fix this at the workflow root"), patch §10 (and/or workflow.md's output contract) in the fork FIRST so the fix propagates by sync, then regenerate this message from the updated template. Do NOT resolve it by rewriting only the current message or by writing a project memory — see `shared/close-out-contract.md` (STD-CLOSEOUT-001) §4.

---

## FAILURE MODES

- **Skipped step-04 entirely.** Brief on disk, consumer can't find it. The producer has not finished its job.
- **Pushed but did not merge.** Branch on origin, PR open. Consumer fails to find the file on `main`. Either complete the merge or update the hand-off prompt to reference the branch URL.
- **Used `--admin` for a non-doc-only PR.** Bypasses real CI signal. The escape exists for structurally-broken-CI + doc-only — not for "I want to skip review."
- **Forgot to fast-forward main.** Local main checkout is behind origin/main. Subsequent local-session reads of `{implementation_artifacts}` don't see the brief until pull. Always run step 9.
- **Reused a worktree-* branch name in the PR.** Reader of the PR list sees a meaningless identifier. Always rename per step 4.
- **Shipped a brief with an empty or §7-inconsistent `frames:` contract.** The brief reaches `main` `UNVERIFIED`, so `design-implement`'s structural diff has nothing to bite on and a dropped drawer renders un-spec'd. The §3 pre-stage assertion catches the internal-consistency half (empty / duplicate / not-mirrored-in-§7) before commit; the completeness half (a drawer that should exist but was never derived) is caught earlier by step-01 §5f + step-03 §3, not here.
