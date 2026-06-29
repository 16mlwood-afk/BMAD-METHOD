/**
 * check-digest-adoption.js  —  default WARN-ONLY · --strict is a PREVIEW (NOT wired into the gate)
 *
 * Coverage check for STD-DIGEST-001 (custom/workflows/shared/behavior-update-digest.md).
 *
 * The contract says an AUDIT / OBSERVATION / behavioral-review workflow's terminal step
 * must not stop at findings — it emits a Behavior Update Digest (doctrine_delta ·
 * handoff_delta · story_candidate · owner_gated · completion_disposition) and auto-executes
 * the safe stages. Findings with no digest is an invalid exit.
 *
 * What is and ISN'T deterministically enforceable (enforcement-expert DETERMINISTIC vs
 * PROBABILISTIC axis):
 *   - Whether the agent ACTUALLY emitted + executed the digest this turn is a JUDGMENT over
 *     a conversational message — not a file-checkable state, and there is no harness
 *     "an audit finished" event to hang a hook on. A Stop-hook scan would be the
 *     indiscriminate-detector anti-pattern. Runtime conformance stays PROBABILISTIC; its
 *     levers are the in-flow named-caller references + STD-CLOSEOUT-001 §4 feedback-patch.
 *     NOT checked here.
 *   - Template COVERAGE is checkable: an audit-lane TERMINAL step (audit/route/classify/
 *     diagnostic signals) that does NOT reference STD-DIGEST-001 is a likely gap. This
 *     detector reports those.
 *
 * TWO MODES:
 *   - default (no flag): WARN-ONLY, exit 0 always — soak-style visibility of coverage.
 *   - `--strict`: a likely gap exits 1. PREVIEW ONLY — deliberately NOT wired into
 *     `npm test` / the pre-commit. STD-DIGEST-001 was authored 2026-06-29 and is DEFERRED
 *     under the fork's own warn-then-gate discipline until adoption is proven quiet by an
 *     elapsed soak (not just quiet-at-arming). Arm later by adding
 *     `&& npm run check:digest -- --strict` to `test` + the pre-commit, exactly as
 *     check:completion was armed.
 *
 * Run: `npm run check:digest`             (warn-only, exit 0)
 *      `npm run check:digest -- --strict`  (preview: exit 1 on a likely gap)
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const WF_DIR = path.join(ROOT, 'custom', 'workflows');

const STRICT = process.argv.includes('--strict');

// Adopts the audit-lane terminal contract — the thing we want coverage on.
const DIGEST_REF = /behavior-update-digest\.md|STD-DIGEST-001/;
// Signals an AUDIT / OBSERVATION terminal step (detect-and-route / diagnostic / audit-only)
// — the close-outs that SHOULD carry the digest. Conservative phrase list (high precision).
const AUDIT_SIGNAL =
  /it does not fix|does not fix\b|No fixes applied|No implementation\.|diagnostic, not implementation|detects?\b[^.\n]{0,18}\broutes?\b|detect (?:\+|and) route|audit-lane|per-finding (?:route|disposition)/i;
// Restrict to plausible TERMINAL steps (the last-mile close-out), so we don't flag a mid-flow
// step that merely mentions "no fixes". Terminal = a route/classify/audit/diagnostic-suggest
// /emit step, or a single-step workflow's only step.
const TERMINAL_FILENAME = /(route|classify|audit|suggest-ui|emit-tech-specs|generate-prompts|step-0?1-audit)/i;

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p, out);
    else if (entry.isFile() && entry.name.endsWith('.md')) out.push(p);
  }
  return out;
}
const rel = (p) => path.relative(ROOT, p);

if (!fs.existsSync(WF_DIR)) {
  console.error(`check:digest: workflow dir not found: ${rel(WF_DIR)}`);
  process.exit(0); // warn-only: never block, even on a missing dir
}

const files = walk(WF_DIR);

let adopters = 0; // files referencing STD-DIGEST-001
const likelyGaps = []; // audit-lane terminal signals, but NO digest reference → the gap we care about

for (const file of files) {
  const text = fs.readFileSync(file, 'utf8');
  const base = path.basename(file);

  // The contract/standard docs themselves reference everything — skip them.
  if (
    base === 'behavior-update-digest.md' ||
    base === 'close-out-contract.md' ||
    base === 'completion-contract.md' ||
    base === 'STANDARDS.md'
  ) {
    if (DIGEST_REF.test(text)) adopters++;
    continue;
  }

  if (DIGEST_REF.test(text)) {
    adopters++;
    continue;
  }

  // No digest reference — is it an audit-lane terminal that SHOULD have one?
  if (AUDIT_SIGNAL.test(text) && TERMINAL_FILENAME.test(base)) {
    likelyGaps.push(rel(file));
  }
}

// --- report (warn-only) ------------------------------------------------------
console.log(
  `\ncheck:digest (${STRICT ? 'STRICT — preview, exit 1 on a likely gap' : 'WARN-ONLY — exit 0'}): ` +
    `${files.length} workflow files · ${adopters} STD-DIGEST-001 adopters.`,
);

if (likelyGaps.length > 0) {
  console.log(
    `\n  ⚠ ${likelyGaps.length} likely coverage gap(s) — an audit-lane terminal step (detect/route/diagnostic signals) with NO STD-DIGEST-001 reference:`,
  );
  for (const f of likelyGaps) console.log(`      • ${f}`);
  console.log(`    Candidates to wire (add the one-line digest reference per shared/behavior-update-digest.md §5).`);
} else {
  console.log(`\n  ✓ No audit-lane terminal step is missing the Behavior Update Digest reference.`);
}

console.log(
  `\n  NOTE: ${STRICT ? '--strict is a PREVIEW (NOT wired into the gate; arming deferred under warn-then-gate)' : 'warn-only mode (exit 0)'}.` +
    ` Runtime "did the agent emit + execute the digest?" stays PROBABILISTIC and is not checked here (contract §4).\n`,
);

if (STRICT && likelyGaps.length > 0) {
  console.error(
    `check:digest --strict: ${likelyGaps.length} audit-lane terminal(s) missing the STD-DIGEST-001 reference (would BLOCK once armed).`,
  );
  process.exit(1);
}
process.exit(0);
