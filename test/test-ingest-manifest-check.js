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
  /* EXIT 2, not 1, since 2026-08-21: a `drawn: true` frame with no section-inventory entry is
   * an EMIT REFUSAL, not a finding among findings. The frame inventory contradicts the section
   * inventory, so every count below has a denominator the manifest itself says is incomplete.
   * `drawn: false` is untouched and still routes downstream as FRAME NOT DRAWN. */
  2,
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

/* ── C12 · the scaffold's own arithmetic. ─────────────────────────────────────
 *
 * THE CASE THIS ENCODES, verbatim from the field: cash-recovery's handheld manifest
 * printed a per-frame scaffold whose 19 rows sum to 75, under a footer rule declaring
 * 70, with the same 70 repeated in two more places. It carried no `sections_total`, so
 * C1 was skipped; six design-implement passes then reported progress against a
 * denominator the file did not support.
 *
 * C1 could not have caught it, and this is the whole reason C12 exists: that scaffold is
 * a FENCED BLOCK, so the markdown-table row parser reads nothing from it and the frame
 * arithmetic is correctly CEDED. C12 scans the printed TEXT instead — layout-independent
 * like C10/C11 — so it fires exactly where C1 must stay silent.
 *
 * These fixtures are STANDALONE rather than `goodManifest()` + an appended block. An
 * earlier draft appended, which put two grids in one file: C12's text scan summed the
 * fenced rows while the frontmatter described the table's, and every case reported a
 * disagreement the fixture had manufactured. A fixture that layers two contradictory
 * scaffolds cannot pin a check about scaffold arithmetic. */
function fencedManifest({ declaredTotal, printedTotal }) {
  return `---
ingest:
  workflow: design-ingest
  version: 1
  target_slug: fenced-fixture-surface
  supersede_status: active
  manifest_grain: value-exact
  completeness:
    frames_total: 2
    frames_drawn: 2
    sections_total: ${declaredTotal}
    sections_per_frame:
      alpha: 3
      beta: 4
    frames_with_empty_section_list: []
    sections_missing_property_rows: []
---

# Fenced-scaffold fixture

## Frame inventory

| frame | role | parent | declared_in | drawn |
|---|---|---|---|---|
| alpha | primary | — | target html | true |
| beta | §13-lookup | alpha | jsx banner | true |

## Section inventory  (THE COMPLETENESS GATE)

### Frame: alpha  (3 sections)
1. header — "Alpha"
2. body — "Alpha body"
3. footer — "Alpha footer"

### Frame: beta  (4 sections)
1. panel — "Beta"
2. list — "Beta list"
3. detail — "Beta detail"
4. actions — "Beta actions"

## Grid scaffold  (pre-seeded)

\`\`\`
frame                sections  status
alpha                       3  UNVERIFIED
beta                        4  UNVERIFIED
                     ─────────
                            ${printedTotal}
\`\`\`

## Data-availability notes
- none
`;
}

/* C13 is the EXPECTED companion on every one of these: the grid is present and this
 * parser reads zero rows from it. That is a real, disclosed limit — the manifest's frame
 * arithmetic is unverified here, not verified-clean — so it belongs in the expected set
 * rather than being suppressed. What must NOT appear is C1-TOTAL and the C2/C4/C5 family:
 * those are derived from grid rows that were never read, and reporting them accuses the
 * manifest of defects the parser invented. */
const CEDED = ['C13-GRID-UNPARSED'];

/* The defect the field case had: the rule prints 9, the rows above it sum to 7. */
check('c12-scaffold-arithmetic-disagrees', fencedManifest({ declaredTotal: 7, printedTotal: 9 }), 1, [...CEDED, 'C12-SCAFFOLD-ARITHMETIC']);

/* THE OTHER DIRECTION, and the one that matters most: when the printed total matches its
 * own rows and the frontmatter agrees with both, C12 says NOTHING. A checker that fires on
 * a correct manifest is one nobody runs twice. */
check('c12-scaffold-arithmetic-agrees', fencedManifest({ declaredTotal: 7, printedTotal: 7 }), 1, CEDED);

/* The third disagreement C12 covers: the scaffold is internally consistent (7 and 7) but
 * the machine-readable frontmatter says something else. This is the shape the fix to the
 * cash-recovery manifest had to avoid re-introducing — a declared total that agrees with
 * nothing. C9-SUM co-fires legitimately, from the other side of the same arithmetic. */
check('c12-declared-total-disagrees-with-rows', fencedManifest({ declaredTotal: 5, printedTotal: 7 }), 1, [
  ...CEDED,
  'C12-TOTAL-VS-ROWS',
  'C9-SUM',
]);

/* ── C1 must NOT accuse a CORRECT total when the grid is merely unreadable. ──
 *
 * Before the `gridEvaluable` guard, this exact manifest reported `sections_total is 7 but
 * the grid scaffold has 0 data rows` — blaming the number that was right, at precisely the
 * moment someone had done the right thing by declaring it, and adding a C4-NO-GRID-ROWS
 * for every frame on top. Four findings, all invented by the parser's own blindness.
 * Pinned as an explicit absence, because a cry-wolf regression is silent otherwise. */
{
  const { codes } = run(fencedManifest({ declaredTotal: 7, printedTotal: 7 }), 'c1-must-not-accuse', ['--strict']);
  const invented = codes.filter((c) => /^C[1245]-/.test(c));
  try {
    assert.deepStrictEqual(invented, [], `parser-invented findings on an unreadable grid: ${invented}`);
    console.log(`  PASS  c1-must-not-accuse-an-unreadable-grid  (codes=[${codes}])`);
    pass++;
  } catch (error) {
    console.log(`  FAIL  c1-must-not-accuse-an-unreadable-grid  ${error.message}`);
    failures.push('c1-must-not-accuse-an-unreadable-grid');
  }
}

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

/* ── Robustness: a legitimate NARROWER table in a NEW section after the grid must not be read as
 * grid rows. This is the defect the tool hit on its own first real use — a 3-column retraction
 * table of commit SHAs, added in a section between the grid and Data-availability, had its SHAs
 * reported as undeclared frames. Section scoping is by heading level + column count now. ── */
check(
  'foreign-narrow-table-after-grid',
  goodManifest().replace(
    '## Data-availability notes',
    `## Retraction

| commit | PR | what it shipped |
|---|---|---|
| 26a7e82 | #430 | phase 1 |
| c3986ee | #448 | all 9 frames |

## Data-availability notes`,
  ),
  0,
  [],
);

/* ── Robustness: an h3 subsection INSIDE the grid section must not end it early. ── */
check(
  'h3-subsection-inside-grid-does-not-truncate',
  goodManifest().replace(
    '| beta | panel | "Beta" | b.id | .p{12px,400} | UNVERIFIED |',
    `| beta | panel | "Beta" | b.id | .p{12px,400} | UNVERIFIED |

### A note about the grid

Prose that happens to sit inside the grid section.`,
  ),
  0,
  [],
);

/* ── A 5-column grid (copy + properties merged into one locator, values carried per-section via
 * `property_rows_location`) is legitimate and must parse. The 6-column schema example is not the
 * only lawful shape, and enforcing the column count would fail a conformant manifest. ── */
check(
  'five-column-grid-parses',
  goodManifest()
    .replace(
      '| frame | section | design copy/structure (verbatim) | data fields read | component×property rows | status |\n|---|---|---|---|---|---|',
      '| frame | section | structure / values | data fields read | status |\n|---|---|---|---|---|',
    )
    .replace('| alpha | header | "Alpha" | a.id | .h{16px,600} | UNVERIFIED |', '| alpha | header | "Alpha" | a.id | UNVERIFIED |')
    .replace(
      '| alpha | body | "Alpha body" | a.body | .b{13px,400} | UNVERIFIED |',
      '| alpha | body | "Alpha body" | a.body | UNVERIFIED |',
    )
    .replace('| beta | panel | "Beta" | b.id | .p{12px,400} | UNVERIFIED |', '| beta | panel | "Beta" | b.id | UNVERIFIED |'),
  0,
  [],
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

/* ══ 2026-08-21 additions ══════════════════════════════════════════════════════
 * C14 enum validation and the consumer trust ceiling. Most assert SILENCE: a checker that
 * fires on a legitimate manifest is one that gets switched off, taking every real finding
 * with it. ── */

for (const g of ['value-exact', 'partial', 'summary']) {
  check(`c14-silent-on-legal-grain-${g}`, goodManifest().replace(/manifest_grain:\s*\S+/, `manifest_grain: ${g}`), 0, []);
}

/* Out-of-enum is REPORTED, never coerced — found in the wild as `full`. */
check('c14-fires-on-out-of-enum-grain', goodManifest().replace(/manifest_grain:\s*\S+/, 'manifest_grain: full'), 1, ['C14-GRAIN-ENUM']);

/* ABSENT is the schema's own conservative default, NOT an invalid value. Conflating the two
 * would fire on every manifest written before the field existed — which is most of them. */
check('c14-silent-when-grain-absent', goodManifest().replace(/^\s*manifest_grain:.*$/m, ''), 0, []);

fs.rmSync(TMP, { recursive: true, force: true });

console.log(`\n${pass} passed, ${failures.length} failed`);
if (failures.length > 0) {
  console.error(`FAILED: ${failures.join(', ')}`);
  process.exit(1);
}
console.log('check-ingest-manifest: both directions pinned.');
