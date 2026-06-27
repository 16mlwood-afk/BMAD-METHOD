/**
 * validate-close-out-contract.js
 *
 * Deterministic guard for STD-CLOSEOUT-001 (custom/workflows/shared/close-out-contract.md).
 *
 * The contract says a workflow's terminal close-out message must be audience-first
 * (a hand-off to the next actor), never a process recap of what the agent did.
 *
 * What is and ISN'T deterministically enforceable here (per the enforcement-expert
 * DETERMINISTIC vs PROBABILISTIC axis):
 *   - The agent's RUNTIME close-out MESSAGE cannot be linted from a file — it's
 *     conversational output. A heuristic Stop-hook scan for "first-person recap"
 *     would be the indiscriminate-detector anti-pattern (high false positives).
 *     Runtime conformance stays PROBABILISTIC; its convergence lever is contract §4
 *     (output-shape feedback routes to a workflow patch). NOT linted here.
 *   - The workflow DEFINITION FILES are deterministically lintable — and template
 *     drift in the fork is the durable failure (it propagates to every project).
 *     This linter guards the templates.
 *
 * The signal is NOT "every close-out references the contract" — most close-outs
 * (routers, triage, verify audits) are consumer-aware by their own design and
 * legitimately never reference it; demanding a reference would false-positive the
 * whole corpus (the indiscriminate-gate anti-pattern). The signal is the inverse:
 * a file that INSTRUCTS narration while NOT having adopted the contract.
 *
 * GATE (exit 1, low false-positive):
 *   A custom/workflows file contains a banned narration-INSTRUCTION phrase
 *   (high-precision list below) AND does NOT reference the contract
 *   (close-out-contract.md / STD-CLOSEOUT-001).
 *   Fix: reshape the phrase to audience-first, OR — if the file is contract-aware
 *   (it quotes the phrase as a thing to AVOID, like the contract/standard docs and
 *   the wired pointers do) — reference the contract, which exempts the file.
 *
 * The contract-reference escape hatch is the logged, in-file override: a file that
 * cites the contract has consciously adopted it, so its phrase mentions are
 * understood to be negative examples, not instructions to narrate.
 *
 * Conservative: narration-specific multi-word phrases + the escape hatch ⇒ the
 * check is silent on the current (post-cleanup) corpus and only fires on a genuine
 * regression or a newly-authored unwired narration-prone close-out.
 *
 * --strict reserved for parity with the other validators (no soft tier today).
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const WF_DIR = path.join(ROOT, 'custom', 'workflows');

// A file that mentions the contract has adopted it — exempt from the phrase gate.
const CONTRACT_REF = /close-out-contract\.md|STD-CLOSEOUT-001/;

// High-precision narration-INSTRUCTION phrases. Each is multi-word and specific to
// "tell the agent to recap its own work" — deliberately NOT bare words like
// "summary"/"summarize" (which appear in legitimate consumer-facing close-outs).
const BANNED_NARRATION = [
  /recap of what you did/i,
  /recap of what'?s? locked/i,
  /a tight recap of (the|your)/i,
  /summari[sz]e key accomplishments/i,
  /summari[sz]e (the steps|what you did|the work you did|how you built)/i,
  /narrate (the |your )?(workflow|process)( history| you (just )?ran)?/i,
  /step-by-step (recap|account|replay) of (the|your)/i,
  /(report|tell the user) (the|each) step (you|the agent) (took|ran)/i,
];

// --- helpers ----------------------------------------------------------------
function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p, out);
    else if (entry.isFile() && entry.name.endsWith('.md')) out.push(p);
  }
  return out;
}
const rel = (p) => path.relative(ROOT, p);

// --- gather -----------------------------------------------------------------
if (!fs.existsSync(WF_DIR)) {
  console.error(`close-out: workflow dir not found: ${rel(WF_DIR)}`);
  process.exit(2);
}
const files = walk(WF_DIR);

const failures = [];
let adopters = 0;

for (const file of files) {
  const text = fs.readFileSync(file, 'utf8');

  // Escape hatch: a contract-aware file is exempt (its phrase mentions are
  // negative examples — "do NOT narrate X" — not instructions to narrate).
  if (CONTRACT_REF.test(text)) {
    adopters++;
    continue;
  }

  for (const [i, line] of text.split('\n').entries()) {
    if (BANNED_NARRATION.some((rx) => rx.test(line))) {
      failures.push({ file: rel(file), line: i + 1, text: line.trim().slice(0, 140) });
    }
  }
}

// --- report -----------------------------------------------------------------
if (failures.length > 0) {
  console.error(`\nclose-out: ${failures.length} BLOCKING failure(s) — narration-prone close-out not adopting STD-CLOSEOUT-001:`);
  for (const f of failures) {
    console.error(`  ✗ ${f.file}:${f.line}`);
    console.error(`      ${f.text}`);
  }
  console.error(
    `\nFix each: reshape the close-out to be audience-first (active artifact → what changed → status → next-actor instructions),\n` +
      `OR — if this file describes the rule rather than instructing narration — reference shared/close-out-contract.md (STD-CLOSEOUT-001) to adopt it.\n` +
      `Contract: custom/workflows/shared/close-out-contract.md. NOTE: runtime message conformance is probabilistic (contract §5) — this linter guards the templates only.`,
  );
  process.exit(1);
}

console.log(
  `close-out: OK — ${files.length} workflow files scanned, ${adopters} adopt STD-CLOSEOUT-001; ` +
    `no unwired narration-prone close-out found.`,
);
