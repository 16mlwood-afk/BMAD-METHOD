/**
 * test-ingest-manifest-check.js — regression suite for tools/check-ingest-manifest.js
 *
 * The checker exists because a design-ingest manifest's completeness gate used to be keyed on a
 * number the agent hand-summed (FG-2026-07-27-06: a real run declared `sections_total: 66`
 * against a 73-row grid). This suite pins BOTH directions — a consistent manifest must pass, and
 * each defect class must fire with its own code — because a checker that has only ever been seen
 * to pass is a checker nobody has proven fires.
 *
 * Fixtures are built inline in a temp dir rather than committed: they are small, and the
 * defect under test is the RELATIONSHIP between three counts, which is clearer to read as a
 * mutation of one good manifest than as eight near-identical files on disk.
 *
 * Run: node test/test-ingest-manifest-check.js   (wired as `npm run test:ingest-manifest`)
 */

'use strict';
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const CHECKER = path.join(__dirname, '..', 'tools', 'check-ingest-manifest.js');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'ingest-manifest-check-'));

let pass = 0;
const failures = [];

/** A minimal but STRUCTURALLY REAL manifest: 2 frames, 3 sections, consistent everywhere. */
function goodManifest() {
  return `---
ingest:
  workflow: design-ingest
  version: 1
  target_slug: fixture-surface
  supersede_status: active
  manifest_grain: value-exact
  completeness:
    frames_total: 2
    frames_drawn: 2
    sections_total: 3
    sections_per_frame:
      alpha: 2
      beta: 1
    frames_with_empty_section_list: []
    sections_missing_property_rows: []
---

# Fixture manifest

## Frame inventory

| frame | role | parent | declared_in | drawn |
|---|---|---|---|---|
| alpha | primary | — | target html | true |
| beta | §13-lookup | alpha | jsx banner | true |

## Section inventory  (THE COMPLETENESS GATE)

### Frame: alpha  (2 sections)
1. header — "Alpha"
2. body — "Alpha body"

### Frame: beta  (1 section)
1. panel — "Beta"

## Grid scaffold  (pre-seeded)

| frame | section | design copy/structure (verbatim) | data fields read | component×property rows | status |
|---|---|---|---|---|---|
| alpha | header | "Alpha" | a.id | .h{16px,600} | UNVERIFIED |
| alpha | body | "Alpha body" | a.body | .b{13px,400} | UNVERIFIED |
| beta | panel | "Beta" | b.id | .p{12px,400} | UNVERIFIED |

## Data-availability notes
- none
`;
}

/** Run the checker; return { exit, codes[] }. */
function run(manifestText, name, extraArgs = ['--strict']) {
  const file = path.join(TMP, `${name}.md`);
  fs.writeFileSync(file, manifestText);
  let out = '';
  let exit = 0;
  try {
    out = execFileSync('node', [CHECKER, '--manifest', file, '--json', ...extraArgs], {
      encoding: 'utf8',
    });
  } catch (error) {
    exit = error.status;
    out = error.stdout || '';
  }
  const codes = out.trim()
    ? JSON.parse(out)
        .findings.map((f) => f.code)
        .sort()
    : [];
  return { exit, codes };
}

function check(name, manifestText, expectedExit, expectedCodes) {
  const { exit, codes } = run(manifestText, name);
  try {
    assert.strictEqual(exit, expectedExit, `exit ${exit} !== ${expectedExit}`);
    assert.deepStrictEqual(codes, [...expectedCodes].sort(), `codes ${codes} !== ${expectedCodes}`);
    console.log(`  PASS  ${name}  (exit=${exit}, codes=[${codes}])`);
    pass++;
  } catch (error) {
    console.log(`  FAIL  ${name}  ${error.message}`);
    failures.push(name);
  }
}

console.log('test-ingest-manifest-check: pinning both directions\n');

/* ── The positive case. If this ever fails, every negative below is meaningless. ── */
check('consistent-manifest', goodManifest(), 0, []);

/* ── C1/C9: the exact defect that motivated the tool — a hand-summed total. ── */
check('wrong-sections-total', goodManifest().replace('sections_total: 3', 'sections_total: 2'), 1, ['C1-TOTAL', 'C9-SUM']);

/* ── C2: a section enumerated but never scaffolded → design-implement is blind to it. ── */
check('grid-row-missing', goodManifest().replace('| alpha | body | "Alpha body" | a.body | .b{13px,400} | UNVERIFIED |\n', ''), 1, [
  'C1-TOTAL',
  'C2-PER-FRAME',
]);

/* ── C3: frontmatter per-frame map disagrees with the section-inventory heading. ── */
check('per-frame-map-disagrees', goodManifest().replace('      alpha: 2', '      alpha: 3'), 1, ['C3-FRONTMATTER', 'C9-SUM']);

/* ── C4: a drawn frame with no section-inventory entry and no grid rows at all. ── */
check(
  'drawn-frame-absent',
  goodManifest().replace(
    '| beta | §13-lookup | alpha | jsx banner | true |',
    '| beta | §13-lookup | alpha | jsx banner | true |\n| gamma | §13-lookup | alpha | jsx banner | true |',
  ),
  1,
  ['C4-MISSING-INV', 'C4-MISSING-GRID'],
);

/* ── C5: a grid row for a frame the inventory never declared.
 * `beta` had exactly ONE grid row, so renaming it leaves beta with ZERO — which is
 * C4-NO-GRID-ROWS, not a count mismatch. And that defect must be reported ONCE, from the
 * section-inventory side only: the drawn-frame sweep must not re-report it as C4-MISSING-GRID. ── */
check('undeclared-frame-in-grid', goodManifest().replace('| beta | panel |', '| ghost | panel |'), 1, ['C4-NO-GRID-ROWS', 'C5-UNDECLARED']);

/* ── C6: step-02's gate should have halted; a delivered manifest must never carry this. ── */
check(
  'empty-section-list-declared',
  goodManifest().replace('frames_with_empty_section_list: []', 'frames_with_empty_section_list: [beta]'),
  1,
  ['C6-EMPTY-LIST'],
);

/* ── C7: the grain lie — value-exact while admitting missing property rows. ── */
check('grain-lie', goodManifest().replace('sections_missing_property_rows: []', 'sections_missing_property_rows: ["alpha / body"]'), 1, [
  'C7-GRAIN',
]);

/* ── C8: a duplicated frame-inventory row. ── */
check(
  'duplicate-frame-row',
  goodManifest().replace(
    '| beta | §13-lookup | alpha | jsx banner | true |',
    '| beta | §13-lookup | alpha | jsx banner | true |\n| alpha | primary | — | target html | true |',
  ),
  1,
  ['DUP-FRAME'],
);

/* ── Warn-only default must NOT exit non-zero, so the tool is safe to run anywhere. ── */
{
  const { exit } = run(goodManifest().replace('sections_total: 3', 'sections_total: 2'), 'warn-only', []);
  try {
    assert.strictEqual(exit, 0, `warn-only exited ${exit}, expected 0`);
    console.log('  PASS  warn-only-does-not-exit-nonzero');
    pass++;
  } catch (error) {
    console.log(`  FAIL  warn-only-does-not-exit-nonzero  ${error.message}`);
    failures.push('warn-only-does-not-exit-nonzero');
  }
}

fs.rmSync(TMP, { recursive: true, force: true });

console.log(`\n${pass} passed, ${failures.length} failed`);
if (failures.length > 0) {
  console.error(`FAILED: ${failures.join(', ')}`);
  process.exit(1);
}
console.log('check-ingest-manifest: both directions pinned.');
