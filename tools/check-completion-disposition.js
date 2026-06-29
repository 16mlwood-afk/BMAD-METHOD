/**
 * check-completion-disposition.js  —  WARN-ONLY (Phase 1)
 *
 * Soak detector for STD-COMPLETION-001 (custom/workflows/shared/completion-contract.md).
 *
 * The contract says a COMPLETION-oriented workflow's terminal step must declare a
 * `completion_disposition` (pr_merged / pr_open / owner_gated_residue / advisory) —
 * diagnosis with no disposition is the invalid "commentator" exit.
 *
 * What is and ISN'T deterministically enforceable (per the enforcement-expert
 * DETERMINISTIC vs PROBABILISTIC axis):
 *   - Whether the agent ACTUALLY drove the work to completion vs. stopped at
 *     commentary is a JUDGMENT — not a file-checkable state. A Stop-hook "did it
 *     really finish?" scan would be the indiscriminate-detector anti-pattern.
 *     Runtime conformance stays PROBABILISTIC; its lever is the close-out
 *     feedback-patch rule (STD-CLOSEOUT-001 §4). NOT checked here.
 *   - Template COVERAGE is checkable: a terminal close-out step (a STD-CLOSEOUT-001
 *     adopter) that ALSO delivers code/an artifact should reference STD-COMPLETION-001.
 *     This detector reports those gaps.
 *
 * WHY WARN-ONLY: this is Phase 1. The detector exits 0 by default and is deliberately
 * NOT in the pre-commit gate or `npm test`. The point of the soak is to observe its
 * precision — which "gaps" are real (a completion deliver-step missing the disposition)
 * vs. expected (an advisory audit/router/review close-out that legitimately has no PR).
 *
 * PHASE-2 PROMOTION (pre-staged, NOT yet armed): pass `--strict` to make a likely gap
 * exit 1 (the escape hatch is unchanged — a delivering close-out adopts the contract by
 * referencing STD-COMPLETION-001, including `advisory` for a genuine no-deliver case).
 * `--strict` exists so the flip is a one-line change and so soak can observe what a gate
 * WOULD block (`npm run check:completion -- --strict`) without arming it. To ARM the gate
 * in Phase 2: add `check:completion -- --strict` to the `test` script / pre-commit — only
 * after the default (warn) output has been proven quiet across an elapsed soak window of
 * real completion-workflow runs and corpus edits, per the warn-then-gate pattern. Today
 * the static scan is quiet (0 likely gaps); that is the PRECONDITION, not the soak itself.
 *
 * Run: `npm run check:completion`            (warn-only, exit 0)
 *      `npm run check:completion -- --strict`  (Phase-2 preview: exit 1 on a likely gap)
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const WF_DIR = path.join(ROOT, 'custom', 'workflows');

// Phase-2 promotion flag (pre-staged, NOT armed in the gate). With --strict a likely
// gap exits 1; without it the detector is warn-only (exit 0). See the header.
const STRICT = process.argv.includes('--strict');

// Adopts the terminal-message shape (so it has a close-out worth dispositioning).
const CLOSEOUT_REF = /close-out-contract\.md|STD-CLOSEOUT-001/;
// Declares its completion disposition — the thing we want coverage on.
const COMPLETION_REF = /completion-contract\.md|STD-COMPLETION-001/;
// Signals a DELIVERY (code/artifact reaches main) — i.e. a completion workflow,
// the close-outs that SHOULD carry a disposition (vs advisory audits/routers).
const DELIVERY_SIGNAL = /delivery-to-main\.md|STD-DELIVERY-001/;
const DELIVERY_FILENAME = /(deliver|handoff|apply-and-deliver)/i;

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
  console.error(`check:completion: workflow dir not found: ${rel(WF_DIR)}`);
  process.exit(0); // warn-only: never block, even on a missing dir
}

const files = walk(WF_DIR);

let adopters = 0; // close-out adopters
let withDisposition = 0; // close-out adopters that also declare the disposition
const likelyGaps = []; // close-out + delivery signal, but NO disposition  → the gap we care about
const advisoryNoDisp = []; // close-out, no delivery signal, no disposition → expected (advisory)

for (const file of files) {
  const text = fs.readFileSync(file, 'utf8');
  const base = path.basename(file);

  // The contract/standard docs themselves reference everything — skip them.
  if (base === 'completion-contract.md' || base === 'close-out-contract.md' || base === 'STANDARDS.md') {
    if (COMPLETION_REF.test(text)) withDisposition++;
    continue;
  }

  const isCloseout = CLOSEOUT_REF.test(text);
  const hasDisposition = COMPLETION_REF.test(text);
  if (!isCloseout && !hasDisposition) continue; // not a terminal close-out — out of scope

  if (isCloseout) adopters++;
  if (hasDisposition) {
    withDisposition++;
    continue;
  }

  // close-out adopter WITHOUT a disposition — classify the gap
  const looksLikeDelivery = DELIVERY_SIGNAL.test(text) || DELIVERY_FILENAME.test(base);
  (looksLikeDelivery ? likelyGaps : advisoryNoDisp).push(rel(file));
}

// --- report (warn-only) ------------------------------------------------------
console.log(
  `\ncheck:completion (WARN-ONLY, Phase 1 — never blocks): ` +
    `${files.length} workflow files · ${adopters} close-out adopters · ${withDisposition} declare a completion_disposition.`,
);

if (likelyGaps.length > 0) {
  console.log(
    `\n  ⚠ ${likelyGaps.length} likely coverage gap(s) — a delivering close-out step (STD-CLOSEOUT-001 + a delivery signal) with NO STD-COMPLETION-001 disposition:`,
  );
  for (const f of likelyGaps) console.log(`      • ${f}`);
  console.log(`    These are the candidates to wire (add a one-line completion_disposition per shared/completion-contract.md §6).`);
}

if (advisoryNoDisp.length > 0) {
  console.log(
    `\n  · ${advisoryNoDisp.length} close-out(s) with no disposition and no delivery signal — likely ADVISORY (audit/router/review); expected to have none. Listed for soak visibility, not flagged:`,
  );
  for (const f of advisoryNoDisp) console.log(`      · ${f}`);
}

if (likelyGaps.length === 0) {
  console.log(`\n  ✓ No delivering close-out is missing a completion_disposition.`);
}

console.log(
  `\n  NOTE: ${STRICT ? '--strict (Phase-2 preview)' : 'warn-only by design (contract §5)'}.` +
    ` Runtime "did it actually finish?" is PROBABILISTIC and not checked here.` +
    ` Arming the gate (adding --strict to the test/pre-commit) is Phase 2, after an elapsed soak proves this quiet.\n`,
);

// Default (warn-only) ALWAYS exits 0. --strict (Phase-2 preview / future gate) exits 1
// on a likely gap so the flip is a one-line change — it is NOT wired into the gate yet.
if (STRICT && likelyGaps.length > 0) {
  console.error(
    `check:completion --strict: ${likelyGaps.length} delivering close-out(s) missing a completion_disposition (would BLOCK once armed).`,
  );
  process.exit(1);
}
process.exit(0);
