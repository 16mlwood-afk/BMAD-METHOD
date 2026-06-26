---
name: diagnostics-gate
contract_version: 1
description: 'Prove-don''t-assert rule for the implementation verification gate. New diagnostics (type errors, "cannot find module", lint/compile failures) after an edit, merge, or worktree teardown mean the gate is RED until a re-run in the CURRENT checkout proves zero errors. Referenced by dev-story (step 8 validation gates), quick-dev (step-04-self-check §2), design-implement (step-04-apply-and-deliver).'
---

# Diagnostics Gate — Prove, Don't Assert

**Why this exists.** "All tests pass / build green / type-check clean" is a *claim about a result*, and a claim is only worth what backs it. Two failure modes this gate prevents:

1. **Rationalized-away diagnostics.** New diagnostics appear after an edit or merge, and the agent reasons them away — "they reference a path I just removed," "the build passed earlier," "those are stale." Sometimes that's true. But *deciding* it's true instead of *proving* it is how a genuinely red gate gets reported as green. The reasoning is a hypothesis; only a re-run is a result.

2. **Stale-checkout drift.** Diagnostics surface against a working tree that no longer matches what's about to ship — an IDE language server still holding a deleted worktree path after teardown, a check last run two commits ago, a build artifact from before the final edit. The fix is the same in every case: re-run in the *current* checkout.

This gate is the rule every implementation workflow applies before it may say "verified."

---

## 1. The rule

When **any** new diagnostic surfaces after an edit, a merge, or a worktree/checkout change, the verification gate is **RED until proven green**. Resolution is **binary** — there is no "probably fine" state:

- **(a) Prove green.** Re-run the relevant check *in the current working directory* and show zero errors. Quote the result — exit code, pass count, the empty error list. Only then is the gate green.
- **(b) Treat as failure.** If it still errors, fix it or escalate. Do not proceed.

The relevant check is the one that emits the diagnostic class:

| Diagnostic class | Re-run to prove it |
|---|---|
| Type errors / "cannot find module" | the project's type-check (`tsc --noEmit`, `npm run typecheck`, equiv.) |
| Test failures | the affected test file, then the suite |
| Lint / format | the project's lint command |
| Build / compile | the project's build command |

> Use the project's own configured commands (see `detect-stack.md`) — never a hand-invented invocation.

---

## 2. What does NOT satisfy the gate

- **"It refers to a removed path / worktree, so it's stale."** A plausible cause, not a result. Re-run; a true-stale diagnostic disappears on re-run in the live checkout, and *that disappearance* is the proof — not the explanation for why it should disappear.
- **"The build passed earlier / before the last edit."** Earlier is not now. The gate is about the tree that ships.
- **"Only my unrelated change is red."** Then prove the relevant check is green *after* your change, in this checkout.
- **Silence.** "Gate green" with no quoted re-run is an unbacked claim. If diagnostics surfaced at any point in the run, the closing statement must point at the re-run that cleared them.

---

## 3. Where this binds

Every implementation workflow's "done/verified" step is gated by this rule. A step may only emit a "verified / gate green / tests pass" status when, for every diagnostic that surfaced during the run, either (a) a current-checkout re-run proved it clear, or (b) it was fixed/escalated as a failure. Disclose which — don't let a cleared-by-reasoning diagnostic pass silently.

Pairs with each project's own pre-flight/build expectations (project `CLAUDE.md`) and with `delivery-to-main.md` (a gate that isn't green doesn't get delivered).
