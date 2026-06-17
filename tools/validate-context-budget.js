/**
 * validate-context-budget.js
 *
 * Deterministic guard for the context-budget durable principle
 * (see the mason-bmad-workflow-expert skill's references/context-budget.md).
 *
 * Workflows are dense instruction documents executed step-by-step by a model
 * with a finite usable context. Steps that are too long / too dense get
 * silently compressed and detail gets dropped. This linter is the COUNTABLE
 * backstop for that principle; it runs in `npm test` (the pre-commit gate).
 *
 * HARD failures (exit 1) — low false-positive, do not fight the existing corpus:
 *   1. RUNAWAY CEILING — any step file past an absolute size ceiling.
 *   2. STEP-3B GATE-GUARD — create-workflow must keep its adversarial review
 *      gate (step-03b-review.md present AND referenced by step-03-build.md).
 *
 * WARN only (exit 0) — surfaced, not blocked, because the fork's house style
 * routinely writes 400-900-line steps; hard-gating the real budget would block
 * legitimate in-progress work. Run with --strict to escalate warnings to
 * failures (intended for AFTER the corpus is shrunk to the real budget).
 *   - a step over the REAL per-step budget (lines / bytes)
 *   - a step with high apparent instruction density (must-do proxy)
 *
 * NOT enforceable here (irreducibly judgment — they live in step-03b as an
 * adversarial instruction): is a constraint buried, is a step truly one job,
 * did the adversarial review actually happen and was it adversarial.
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const WF_DIR = path.join(ROOT, 'custom', 'workflows');

// --- thresholds (tunable) ---------------------------------------------------
const RUNAWAY_MAX_LINES = 1100; // absolute ceiling — catches a ballooning step; current corpus max ~974
const RUNAWAY_MAX_BYTES = 95_000;
const BUDGET_LINES = 350; // soft per-step budget (warn)
const BUDGET_BYTES = 28_000; // ~7k tokens (warn)
const DENSITY_MUSTDO = 14; // soft must-do-count ceiling per step (warn); principle says ~10

const STRICT = process.argv.includes('--strict');

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

// "must-do" proxy: numbered instruction items + strong directive markers.
// Deliberately a heuristic — used for WARN only, never a hard gate.
function mustDoCount(text) {
  const numbered = (text.match(/^\s*\d+\.\s+\S/gm) || []).length;
  const directives = (text.match(/\b(MUST|NEVER|ALWAYS|REQUIRED|DO NOT)\b/g) || []).length;
  return numbered + directives;
}

// --- gather -----------------------------------------------------------------
if (!fs.existsSync(WF_DIR)) {
  console.error(`context-budget: workflow dir not found: ${rel(WF_DIR)}`);
  process.exit(2);
}
const stepFiles = walk(WF_DIR).filter((p) => /[/\\]steps[/\\][^/\\]+\.md$/.test(p));

const failures = [];
const warnings = [];

// --- check 1: runaway ceiling (HARD) + budget/density (WARN) -----------------
for (const file of stepFiles) {
  const text = fs.readFileSync(file, 'utf8');
  const lines = text.split('\n').length;
  const bytes = Buffer.byteLength(text, 'utf8');
  const mustDos = mustDoCount(text);

  if (lines > RUNAWAY_MAX_LINES || bytes > RUNAWAY_MAX_BYTES) {
    failures.push(
      `RUNAWAY  ${rel(file)} — ${lines} lines / ${bytes} bytes exceeds the ceiling ` +
        `(${RUNAWAY_MAX_LINES} lines / ${RUNAWAY_MAX_BYTES} bytes). Split this step into one-job-per-step.`,
    );
    continue;
  }
  if (lines > BUDGET_LINES || bytes > BUDGET_BYTES) {
    warnings.push(`over-budget  ${rel(file)} — ${lines} lines / ${bytes} bytes (budget ${BUDGET_LINES} lines / ${BUDGET_BYTES} bytes)`);
  }
  if (mustDos > DENSITY_MUSTDO) {
    warnings.push(`dense        ${rel(file)} — ~${mustDos} must-do markers (soft ceiling ${DENSITY_MUSTDO})`);
  }
}

// --- check 2: create-workflow step-3b adversarial gate-guard (HARD) ---------
const cwSteps = path.join(WF_DIR, 'meta', 'create-workflow', 'steps');
if (fs.existsSync(cwSteps)) {
  const gate = path.join(cwSteps, 'step-03b-review.md');
  const build = path.join(cwSteps, 'step-03-build.md');
  if (!fs.existsSync(gate)) {
    failures.push(
      `GATE     create-workflow is missing step-03b-review.md — the mandatory adversarial review gate. ` +
        `It must run between build (step-03) and wire (step-04). Do not remove it.`,
    );
  }
  if (fs.existsSync(build) && !/step-03b/.test(fs.readFileSync(build, 'utf8'))) {
    failures.push(
      `GATE     create-workflow/steps/step-03-build.md no longer routes to step-03b — the adversarial ` +
        `review gate is orphaned. step-03 must point at step-03b before wiring.`,
    );
  }
}

// --- report -----------------------------------------------------------------
if (STRICT) {
  failures.push(...warnings.map((w) => `STRICT   ${w}`));
  warnings.length = 0;
}

if (warnings.length > 0) {
  console.log(`context-budget: ${warnings.length} warning(s) (non-blocking):`);
  for (const w of warnings.slice(0, 8)) console.log(`  ⚠ ${w}`);
  if (warnings.length > 8) console.log(`  … and ${warnings.length - 8} more`);
}

if (failures.length > 0) {
  console.error(`\ncontext-budget: ${failures.length} BLOCKING failure(s):`);
  for (const f of failures) console.error(`  ✗ ${f}`);
  console.error(`\nSee the context-budget durable principle (mason-bmad-workflow-expert/references/context-budget.md).`);
  process.exit(1);
}

console.log(
  `context-budget: OK — ${stepFiles.length} step files within the runaway ceiling; ` +
    `create-workflow adversarial gate intact${warnings.length > 0 ? `; ${warnings.length} soft warning(s)` : ''}.`,
);
