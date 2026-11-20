# Quick-Dev Safety: Grounding Gate and Autonomy Scoping

`quick-dev` is the fork's primary "small change" AI coding workflow. It's the workflow most likely to ship a regression across 13 projects, so it carries the strictest safety layer in the system.

## Two Modes

- **Mode A — spec-driven.** A light dev-story drives the change. Spec exists, scope is bounded.
- **Mode B — direct instructions.** User describes the change inline. No spec. **This is where the grounding gate lives.**

## The Grounding Gate (Mode B)

Before quick-dev does anything in Mode B, it must answer two questions from the user's input alone:

1. **Verb** — what action is being requested? (add, remove, refactor, rename, fix, etc.)
2. **Target** — where in the code? (file path, function name, component, or a string that `grep` can locate)

If either is missing, the workflow **halts** with a message indicating which piece is absent.

### What fails the gate (concrete examples)

- Single-word prompts: `"fix"`, `"refactor"`, `"clean up"` — no target.
- Vague asks: `"make the button nicer"` — verb is mushy, target depends on inference.
- Untraceable references: `"update the thing in checkout"` if "the thing" doesn't grep to a unique location.
- Pure intent statements: `"the UX feels off"` — no verb, no target, only feeling.

### What passes the gate

- `"Add an aria-label to the close button in <ModalHeader>"` — verb (add), target (specific component + element).
- `"Remove the unused useDebounce import from src/hooks/useSearch.ts"` — verb (remove), target (specific file + symbol).
- `"Rename handleSubmit to handleFormSubmit in CheckoutForm"` — verb + target.

## Autonomy Scoping

`autonomous_mode` in the fork has been redefined to draw a hard line between two kinds of autonomy.

### Decision autonomy — ALLOWED

The workflow may make these decisions on its own:
- **File choice** — picking which file to edit when the user named a symbol, not a path.
- **Pattern/library selection** — choosing how to implement (e.g., `useMemo` vs derived state, regex vs parser).
- **Implementation detail** — naming locals, structuring a function, choosing iteration style.

These are decisions about **how** to execute a clearly-stated intent.

### Intent autonomy — FORBIDDEN

The workflow may **not** make these decisions:
- Deciding what the user "must have meant" from underspecified input.
- Expanding scope ("while I'm here, I'll also...") without explicit instruction.
- Choosing between two reasonable interpretations of an ambiguous request.
- Inferring a target when the user didn't name one.

These are decisions about **what** to do. The user must own them.

## The Failure Chain This Closes

Before the gate and autonomy scoping:
1. User issues a fuzzy ask (e.g., "tidy up the checkout flow").
2. quick-dev runs autonomously, infers a scope, picks a target.
3. Workflow ships a change the user didn't actually request.
4. Change propagates through PR to one of 13 projects.

After:
1. User issues a fuzzy ask.
2. Grounding gate halts: "Can't proceed — verb is unclear (what does 'tidy up' mean?) and target is unbounded (which files in checkout?)."
3. User clarifies or aborts. No invented work ships.

## Review Checklist for Quick-Dev Changes

When reviewing a change to quick-dev or any workflow that adopts its safety pattern:

- [ ] Mode B path enters the grounding gate before any action
- [ ] Gate explicitly checks for both verb and target
- [ ] Halt diagnostics name which piece is missing
- [ ] Autonomy scope is explicit somewhere in the workflow config (decision-only)
- [ ] No silent fallback that bypasses the gate when input is empty/short
- [ ] Tests or examples cover at least one gate-failing input

## Applying the Pattern Elsewhere

The grounding gate is a general pattern, not just a quick-dev feature. Any workflow that:
- Accepts free-form user input, AND
- Takes consequential action (file edits, ships output downstream)

...should adopt the verb-and-target gate. When authoring new workflows in this category, bake it in from the first draft. When reviewing existing workflows that don't have it, flag the gap as a Concern (not a blocking issue unless the workflow operates on production code).
