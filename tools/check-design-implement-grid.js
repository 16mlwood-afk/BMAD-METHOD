/**
 * check-design-implement-grid.js  —  deterministic verifier for a design-implement grid
 *                                    artifact's own delta arithmetic.
 *
 * Home of the rule: custom/workflows/implement/design-implement/steps/step-03-build-grid.md §3
 *                   ("Count Deltas — DERIVE the figure from the tables") + step-04 §5 (apply ledger).
 *
 * WHY THIS EXISTS (FG-2026-08-03-16).
 * step-03 §3 said only "count the rows where the Delta column is NOT ✓". Both the count and the
 * tables it summarises were produced by the same agent, in the same pass, with no mechanism to
 * compare them — so "count" meant "add it up again and hope". On 2026-08-03 a real run wrote
 * `delta_count: 41` against ten per-section tables carrying 74 non-✓ rows: a 45% under-count in
 * the one field every later reader treats as the denominator.
 *
 * It is not merely a misreport, and that is the whole reason this tool exists. step-04 §5's
 * `A + D + X == {delta_count}` is the apply's own integrity check — so an UNDER-counted
 * denominator does not FAIL that check, it SATISFIES IT EARLY. The run then reports
 * "41/41 applied" over a 74-row grid: green, complete-looking, and a third of the work missing.
 * step-04 §16 names that exact shape ("shipping a count like 47/47 while the grid
 * under-enumerated") and places its guard on the apply, where it is structurally blind to the
 * cause: the denominator was already wrong when the apply began.
 *
 * Same through-line as its sibling check-ingest-manifest.js, and as the collision guard's
 * actor / claimed_by / claimed_at family: "a field an agent self-reports will eventually be
 * wrong; the harness must derive anything a gate keys on." `delta_count` looks like a fact, is
 * self-reported, and step-04's gate is keyed on it.
 *
 * DELIBERATELY NOT DONE: this tool does not WRITE `delta_count`. The agent still declares it and
 * the checker still disagrees — two independent derivations that must match. A self-stamping
 * counter would erase the disagreement that catches the error.
 *
 * ── What IS and ISN'T deterministically checkable (enforcement-expert axis) ──
 *
 *  CHECKED (pure arithmetic and token matching over the emitted file — no judgement):
 *    G1  frontmatter delta_count == (non-✓ rows in Delta-columned tables) + declared deviations
 *    G2  the Delta-summary tier table (Tier 1 + 2 + 3) == the derived non-✓ row count
 *    G3  the apply ledger closes: Applied + Deferred + Dropped == delta_count
 *    G4  frontmatter fixed_count == the ledger's Applied figure
 *    G5  every ⊘ deferred / ✗ dropped disposition names a reason in parentheses
 *
 *  NOT CHECKED (needs judgement — ceded, exactly as the workflow cedes them):
 *    · whether a row's Delta verdict is CORRECT (is 10px really ≠ 4px here?)
 *    · whether the tables ENUMERATE everything the design contains — an under-enumerated grid
 *      is internally consistent and passes every check below. That is step-03 §2f/§2f-bis's
 *      job (frame + section coverage), not arithmetic's.
 *    · whether an applied row was actually applied. Only re-reading the impl proves that.
 *
 *  So a green run means "this artifact does not contradict itself", never "this grid is right".
 *
 * ROUTED ROWS ARE NOT DELTAS and are excluded from the derivation by their own named tokens —
 * the workflow says so in §2c/§2e/§2f/§2g/§2i, and each carries a machine-findable marker.
 *
 * usage: node tools/check-design-implement-grid.js --grid <path> [--strict] [--json]
 *        exit 0 = no findings (or non-strict); 1 = findings under --strict, or bad usage.
 */

'use strict';

const fs = require('node:fs');

/* A Delta cell that is a ROUTED disposition, not a delta to apply. Each token is the literal
   the workflow prescribes, so this list is a transcription, not a heuristic. */
const ROUTED_TOKENS = [
  'CONTENT-LANE-UNVERIFIED',
  'CEDED',
  'NON-CANONICAL TOKEN',
  'FOUNDATION-TOKEN DRIFT',
  'DEAD-FALLBACK',
  'FRAME NOT DRAWN',
  'LOOKUP UNDER-ENUMERATED',
  'needs human confirmation',
];

/* A Delta cell meaning "no delta". `—`/`-`/empty are used for note rows that carry no verdict. */
const NO_DELTA = /^(✓|—|-|n\/a|na)?$/i;

function splitRow(line) {
  const t = line.trim().replace(/^\|/, '').replace(/\|$/, '');
  return t.split('|').map((c) => c.trim());
}

function isSeparatorRow(cells) {
  return cells.length > 0 && cells.every((c) => /^:?-{2,}:?$/.test(c));
}

/**
 * Walk every markdown table that has a column literally headed `Delta`, and count the data rows
 * whose Delta cell is neither empty/✓ nor a routed token. Returns the rows so a caller can
 * report WHERE, not just how many — a bare number is the thing this tool exists to distrust.
 */
function deriveDeltaRows(lines) {
  const rows = [];
  const routed = [];
  let deltaCol = -1;

  for (const [i, line] of lines.entries()) {
    if (!line.includes('|')) {
      deltaCol = -1;
      continue;
    }
    const cells = splitRow(line);
    if (isSeparatorRow(cells)) continue;

    const headerIdx = cells.findIndex((c) => /^delta$/i.test(c));
    if (headerIdx !== -1 && deltaCol === -1) {
      // A header row for a Delta-columned table. The next non-separator row starts the data.
      deltaCol = headerIdx;
      continue;
    }
    if (deltaCol === -1) continue;
    if (cells.length <= deltaCol) continue;

    const verdict = cells[deltaCol];
    const entry = { line: i + 1, label: cells[0], verdict };
    if (ROUTED_TOKENS.some((tok) => verdict.includes(tok))) routed.push(entry);
    else if (!NO_DELTA.test(verdict)) rows.push(entry);
  }
  return { rows, routed };
}

/** Deviations logged under §5b — real ledger rows that are not grid rows. */
function countDeviations(lines) {
  let inSection = false;
  let n = 0;
  for (const line of lines) {
    if (/^#{2,4}\s/.test(line)) inSection = /logged deviation/i.test(line);
    if (!inSection) continue;
    if (!line.trim().startsWith('|')) continue;
    const cells = splitRow(line);
    if (isSeparatorRow(cells)) continue;
    if (/^#?\s*$/.test(cells[0]) || /^#$/i.test(cells[0])) continue; // header row
    if (/^D\d+$/i.test(cells[0])) n++;
  }
  return n;
}

function num(re, text) {
  const m = text.match(re);
  return m ? Number(m[1].replaceAll(',', '')) : null;
}

const argv = process.argv.slice(2);
function flag(name) {
  const i = argv.indexOf(name);
  return i === -1 ? null : argv[i + 1];
}

const gridPath = flag('--grid');
const STRICT = argv.includes('--strict');
const JSON_OUT = argv.includes('--json');

if (!gridPath) {
  console.error('usage: check-design-implement-grid.js --grid <path> [--strict] [--json]');
  process.exit(1);
}
if (!fs.existsSync(gridPath)) {
  console.error(`check-design-implement-grid: no such file: ${gridPath}`);
  process.exit(1);
}

const text = fs.readFileSync(gridPath, 'utf8');
const lines = text.split('\n');
const findings = [];

const { rows: deltaRows, routed } = deriveDeltaRows(lines);
const derived = deltaRows.length;
const deviations = countDeviations(lines);
const expected = derived + deviations;

const declared = num(/^delta_count:\s*'?(\d[\d,]*)'?/m, text);
const fixed = num(/^fixed_count:\s*'?(\d[\d,]*)'?/m, text);

/* G1 — the headline figure against the tables it summarises. */
if (declared === null) {
  findings.push({ id: 'G1', msg: 'frontmatter has no `delta_count` — step-03 §3 requires it' });
} else if (declared !== expected) {
  findings.push({
    id: 'G1',
    msg:
      `delta_count declares ${declared}, tables derive ${expected} ` +
      `(${derived} non-✓ Delta rows + ${deviations} logged deviation(s)). ` +
      'The TABLES WIN (step-03 §3): correct the summary and record the correction. ' +
      (declared < expected
        ? `An under-count LICENSES A SHORT APPLY LEDGER — step-04 §5's A+D+X check would be satisfied ${expected - declared} row(s) early.`
        : 'An over-count will make step-04 §5 unsatisfiable.'),
  });
}

/* G2 — the tier breakdown against the same derivation. */
const tiers = ['Tier 1', 'Tier 2', 'Tier 3'].map((t) => {
  const re = new RegExp(`\\|\\s*\\*{0,2}${t}[^|]*\\|\\s*\\*{0,2}(\\d[\\d,]*)`, 'm');
  return num(re, text);
});
if (tiers.every((t) => t !== null)) {
  const sum = tiers.reduce((a, b) => a + b, 0);
  if (sum !== derived) {
    findings.push({
      id: 'G2',
      msg: `Delta-summary tiers sum to ${sum} (${tiers.join(' + ')}) but the tables derive ${derived} non-✓ rows`,
    });
  }
}

/* G3 — the apply ledger closes against the declared denominator (step-04 §5). */
const applied = num(/Applied:\s*\*{0,2}(\d[\d,]*)\s*\//i, text);
const deferred = num(/Deferred:\s*\*{0,2}(\d[\d,]*)/i, text);
const dropped = num(/Dropped:\s*\*{0,2}(\d[\d,]*)/i, text);
const ledgerPresent = applied !== null && deferred !== null && dropped !== null;

if (ledgerPresent && declared !== null) {
  const total = applied + deferred + dropped;
  if (total !== declared) {
    findings.push({
      id: 'G3',
      msg: `apply ledger closes at ${total} (applied ${applied} + deferred ${deferred} + dropped ${dropped}) but delta_count is ${declared} — step-04 §5 requires A + D + X == delta_count`,
    });
  }
  /* G4 — fixed_count is the ledger's Applied figure, not a second opinion. */
  if (fixed !== null && fixed !== applied) {
    findings.push({ id: 'G4', msg: `frontmatter fixed_count is ${fixed} but the ledger reports ${applied} applied` });
  }
}

/* G5 — a bare `deferred`/`dropped` is the silent drop wearing a label (step-04 §5). */
for (const [i, line] of lines.entries()) {
  const m = line.match(/[⊘✗]\s*(deferred|dropped)(?!\s*\()/i);
  if (m && !/[⊘✗]\s*(deferred|dropped)\s*\(/i.test(line)) {
    findings.push({ id: 'G5', msg: `line ${i + 1}: bare \`${m[1]}\` with no reason in parentheses` });
  }
}

if (JSON_OUT) {
  console.log(
    JSON.stringify(
      { grid: gridPath, declared, derived, deviations, expected, routed: routed.length, applied, deferred, dropped, findings },
      null,
      2,
    ),
  );
} else {
  for (const f of findings) console.log(`  ✗ ${f.id}: ${f.msg}`);
  const verdict = findings.length === 0 ? 'consistent' : `${findings.length} finding(s)`;
  console.log(
    `check-design-implement-grid: ${verdict} · ${derived} non-✓ row(s) + ${deviations} deviation(s) = ${expected} · declared ${declared === null ? 'MISSING' : declared} · ${routed.length} routed row(s) excluded`,
  );
  if (findings.length === 0) {
    console.log('  note: consistency is NOT coverage — this proves the artifact agrees with itself,');
    console.log('        never that the grid enumerated everything the design contains (§2f/§2f-bis).');
  }
}

process.exit(STRICT && findings.length > 0 ? 1 : 0);
