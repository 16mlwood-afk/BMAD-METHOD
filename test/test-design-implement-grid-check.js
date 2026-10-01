/**
 * test-design-implement-grid-check.js — regression suite for tools/check-design-implement-grid.js
 *
 * The checker exists because a design-implement grid's `delta_count` used to be a number the
 * agent hand-summed (FG-2026-08-03-16: a real run declared 41 against ten tables carrying 74
 * non-✓ rows — and the hand-correction to 74 was ALSO wrong, by 16, because it skipped two whole
 * section-coverage blocks). This suite pins BOTH directions — a consistent grid must pass, and
 * each defect class must fire — because a checker that has only ever been seen to pass is a
 * checker nobody has proven fires.
 *
 * The negative cases matter more than usual here. The defect this tool guards is one that
 * SATISFIES the downstream invariant rather than failing it (an under-counted denominator makes
 * step-04 §5's `A + D + X == delta_count` close early), so "it didn't complain" was never
 * evidence of anything and must not become evidence about the checker either.
 *
 * Fixtures are built inline rather than committed: the thing under test is a RELATIONSHIP between
 * a frontmatter figure and the tables below it, which reads more clearly as a mutation of one
 * good grid than as six near-identical files on disk.
 *
 * Run: node test/test-design-implement-grid-check.js   (wired as `npm run test:di-grid`)
 */

'use strict';
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const CHECKER = path.join(__dirname, '..', 'tools', 'check-design-implement-grid.js');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'di-grid-check-'));

let pass = 0;
const failures = [];

/**
 * A minimal but STRUCTURALLY REAL grid: 4 non-✓ delta rows across two tables, 1 routed row that
 * must NOT be counted, 1 logged deviation, a tier table that sums to 4, and a ledger that closes.
 * delta_count = 4 + 1 deviation = 5.
 */
function goodGrid() {
  return `---
status: complete
delta_count: 5
fixed_count: 4
---

# Fixture grid

## Page shell

| Property | Design | Implementation | Delta |
|---|---|---|---|
| container width | full-bleed | 1180px | capped → Tier-1 |
| centering | false | true | Tier-1 |
| padding | 32px | 32px | ✓ |

## Component × property

| Property | Design | Implementation | Delta |
|---|---|---|---|
| radius | 4px | 10px | -6px |
| font-size | 13px | 13px | ✓ |
| label | "Ledger" | "Ledgers" | COPY-DELTA |

## Content lane

| Component | State | Property | Design | Implementation | Delta |
|---|---|---|---|---|---|
| money cell | — | content-lane: identifier value | mock £1.00 | fmtMoney | CONTENT-LANE-UNVERIFIED → route to design-review |

## Delta summary

| Tier | Count | Description |
|---|---|---|
| Tier 1 — Structural | 2 | page shell |
| Tier 2 — Visual | 1 | radius |
| Tier 3 — Micro | 1 | copy |
| **Sub-total (grid rows)** | **4** | |

## Apply ledger

**Applied: 4/5 · Deferred: 1 · Dropped: 0**

### Logged deviations

| # | Deviation | Disposition |
|---|---|---|
| D1 | negative money renders (£x) | ⊘ deferred(judgment: shared money path) |
`;
}

function run(body, name, { strict = true } = {}) {
  const file = path.join(TMP, `${name}.md`);
  fs.writeFileSync(file, body);
  const args = ['--grid', file, '--json'];
  if (strict) args.push('--strict');
  try {
    const out = execFileSync('node', [CHECKER, ...args], { encoding: 'utf8' });
    return { exit: 0, report: JSON.parse(out) };
  } catch (error) {
    return { exit: error.status, report: JSON.parse(error.stdout || '{}') };
  }
}

function check(name, fn) {
  try {
    fn();
    pass++;
    console.log(`  PASS  ${name}`);
  } catch (error) {
    failures.push(`${name}: ${error.message}`);
    console.log(`  FAIL  ${name} — ${error.message}`);
  }
}

const ids = (r) => (r.report.findings || []).map((f) => f.id);

/* ── the positive direction ───────────────────────────────────────────────── */

check('consistent grid passes, exit 0', () => {
  const r = run(goodGrid(), 'good');
  assert.strictEqual(r.exit, 0, `expected exit 0, got ${r.exit} (${ids(r)})`);
  assert.deepStrictEqual(ids(r), []);
});

check('a routed row is EXCLUDED from the derivation, not counted as a delta', () => {
  const r = run(goodGrid(), 'routed');
  assert.strictEqual(r.report.derived, 4, 'the CONTENT-LANE row must not be a delta');
  assert.strictEqual(r.report.routed, 1, 'but it must still be reported as routed');
});

check('a logged deviation counts toward delta_count but not toward derived', () => {
  const r = run(goodGrid(), 'deviation');
  assert.strictEqual(r.report.deviations, 1);
  assert.strictEqual(r.report.expected, 5);
});

/* ── the negative direction — each defect class must FIRE ─────────────────── */

check('G1 fires on an UNDER-counted delta_count (the motivating defect)', () => {
  const r = run(goodGrid().replace('delta_count: 5', 'delta_count: 3'), 'g1-under');
  assert.strictEqual(r.exit, 1);
  assert.ok(ids(r).includes('G1'), `expected G1, got ${ids(r)}`);
  const msg = r.report.findings.find((f) => f.id === 'G1').msg;
  assert.ok(/LICENSES A SHORT APPLY LEDGER/.test(msg), 'must name the downstream consequence');
});

check('G1 fires on an OVER-counted delta_count too', () => {
  const r = run(goodGrid().replace('delta_count: 5', 'delta_count: 9'), 'g1-over');
  assert.strictEqual(r.exit, 1);
  assert.ok(ids(r).includes('G1'));
});

check('G1 fires when a whole table block is omitted from the count (the SECOND defect)', () => {
  // Adds a section-coverage block — exactly the shape the hand re-count skipped.
  const withBlock = goodGrid().replace(
    '## Delta summary',
    `## Section coverage

| Section | Design | Implementation | Delta |
|---|---|---|---|
| S1 header | renders | duplicated | STRUCTURE-DELTA |
| S2 body | renders | absent | SECTION MISSING in impl |

## Delta summary`,
  );
  const r = run(withBlock, 'g1-skipped-block');
  assert.strictEqual(r.exit, 1, 'a grid that grew two rows but kept its old count must fail');
  assert.ok(ids(r).includes('G1'));
  assert.strictEqual(r.report.derived, 6);
});

check('G2 fires when the tier table disagrees with the tables', () => {
  const r = run(goodGrid().replace('| Tier 1 — Structural | 2 |', '| Tier 1 — Structural | 7 |'), 'g2');
  assert.strictEqual(r.exit, 1);
  assert.ok(ids(r).includes('G2'), `expected G2, got ${ids(r)}`);
});

check('G3 fires when the apply ledger does not close against delta_count', () => {
  const r = run(goodGrid().replace('**Applied: 4/5 · Deferred: 1 · Dropped: 0**', '**Applied: 4/5 · Deferred: 0 · Dropped: 0**'), 'g3');
  assert.strictEqual(r.exit, 1);
  assert.ok(ids(r).includes('G3'), `expected G3, got ${ids(r)}`);
});

check('G4 fires when fixed_count is a second opinion rather than the ledger figure', () => {
  const r = run(goodGrid().replace('fixed_count: 4', 'fixed_count: 5'), 'g4');
  assert.strictEqual(r.exit, 1);
  assert.ok(ids(r).includes('G4'), `expected G4, got ${ids(r)}`);
});

check('G5 fires on a bare deferred with no reason', () => {
  const r = run(goodGrid().replace('⊘ deferred(judgment: shared money path)', '⊘ deferred'), 'g5');
  assert.strictEqual(r.exit, 1);
  assert.ok(ids(r).includes('G5'), `expected G5, got ${ids(r)}`);
});

check('G1 fires when delta_count is missing entirely', () => {
  const r = run(goodGrid().replace('delta_count: 5\n', ''), 'g1-missing');
  assert.strictEqual(r.exit, 1);
  assert.ok(ids(r).includes('G1'));
});

/* ── parser robustness — a false FIRE is as bad as a false pass ───────────── */

check('a table with no Delta column is ignored entirely', () => {
  const withForeign = goodGrid().replace(
    '## Delta summary',
    `## Capability inventory

| # | Capability | Class | Evidence |
|---|---|---|---|
| P1 | global nav | chrome | layout.tsx |
| P2 | headline | economics | app.tsx |

## Delta summary`,
  );
  const r = run(withForeign, 'foreign-table');
  assert.strictEqual(r.exit, 0, `a Delta-less table must not add rows (${ids(r)})`);
  assert.strictEqual(r.report.derived, 4);
});

check('prose in a Delta cell counts as an OPEN delta — notation is read literally', () => {
  const r = run(goodGrid().replace('| padding | 32px | 32px | ✓ |', '| padding | 32px | 32px | fine once S1 lands — ✓ |'), 'prose-verdict');
  assert.strictEqual(r.exit, 1, 'a resolved row written as prose must not silently read as closed');
  assert.ok(ids(r).includes('G1'));
});

check('non-strict mode reports without exiting non-zero', () => {
  const r = run(goodGrid().replace('delta_count: 5', 'delta_count: 3'), 'nonstrict', { strict: false });
  assert.strictEqual(r.exit, 0);
  assert.ok(ids(r).includes('G1'), 'still reports the finding');
});

fs.rmSync(TMP, { recursive: true, force: true });

console.log(`\n${pass} passed, ${failures.length} failed`);
if (failures.length > 0) {
  for (const f of failures) console.error(`  ✗ ${f}`);
  process.exit(1);
}
console.log('check-design-implement-grid: both directions pinned.');
