/**
 * test-copy-screen-check.js — regression suite for tools/check-copy-screen.js (STD-COPY-SCREEN-001).
 *
 * G1 is the owner's own example (2026-09-26): "Check · 13 — boxes compared, something else to
 * settle". It must fail, and its fixed form must pass. Most of the rest assert SILENCE, because this
 * checker scans copy a person wrote on purpose and a false fire there is how a screen gets ignored.
 *
 * Run: node test/test-copy-screen-check.js   (wired as `npm run test:copy-screen`)
 */

'use strict';
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const { screenString, checkDeck } = require('../tools/check-copy-screen.js');

let pass = 0;
const failures = [];
function it(name, fn) {
  try {
    fn();
    pass += 1;
  } catch (error) {
    failures.push(`${name}\n      ${error.message}`);
  }
}
const hard = (s) =>
  screenString(s)
    .filter((f) => f.severity === 'hard')
    .map((f) => f.code);
const all = (s) => screenString(s).map((f) => f.code);

/* ── the golden matrix, read from the file so the two cannot drift ── */

const MATRIX = fs.readFileSync(
  path.join(__dirname, '..', 'custom', 'workflows', 'design', 'shared', 'copy-screen-golden-matrix.md'),
  'utf8',
);
const golden = MATRIX.split('\n')
  .filter((l) => /^\| G\d /.test(l))
  .map((l) => {
    const c = l.split('|').map((x) => x.trim());
    const unq = (x) => x.replaceAll(/^`|`$/g, '');
    return { id: c[1], current: unq(c[2]), ships: unq(c[4]) };
  });

it('the matrix carries five rows', () => assert.strictEqual(golden.length, 5));

it('G1 — the owner example fails on the label code and on "settle"', () => {
  const g = golden.find((x) => x.id === 'G1');
  assert.ok(g.current.includes('something else to settle'));
  assert.deepStrictEqual(hard(g.current).sort(), ['V1', 'V2']);
  assert.ok(all(g.current).includes('P2'));
});
it('G1 — the fixed form is silent', () => {
  const g = golden.find((x) => x.id === 'G1');
  assert.deepStrictEqual(all(g.ships), []);
});
for (const id of ['G2', 'G3', 'G4']) {
  it(`${id} — current fails hard, fixed form has no hard finding`, () => {
    const g = golden.find((x) => x.id === id);
    assert.ok(hard(g.current).length > 0, `expected a hard finding on ${g.current}`);
    assert.deepStrictEqual(hard(g.ships), []);
  });
}
it('G4 — an ASIN as the first word is a proxy, not a hard finding', () => {
  const g = golden.find((x) => x.id === 'G4');
  assert.ok(all(g.current).includes('P1'));
});
it('G5 — plain copy is silent', () => {
  assert.deepStrictEqual(all(golden.find((x) => x.id === 'G5').current), []);
});

/* ── vocabulary, each banned word in an inflection ── */

for (const s of [
  'Two verdicts differ',
  'Disposition every row',
  'Pallet lane',
  'Gated until Monday',
  'Routed by title',
  'Show provenance and audit',
  'The identity-test failed',
  'Figure listing',
  'Three preconditions hold',
  'Nothing settled yet',
  'The figure rests on none',
]) {
  it(`V1 fires on "${s}"`, () => assert.ok(hard(s).includes('V1')));
}
it('V2 fires on a bare SKIP code', () => assert.ok(hard('Row is SKIP').includes('V2')));
it('V2 fires on "Skip · 38 lines"', () => assert.ok(hard('Skip · 38 lines').includes('V2')));

/* ── silence: ordinary copy, lookalike words and template variables ── */

for (const s of [
  'Copy all',
  'Buy · 3 lines',
  '3 lines worth buying',
  'Close ✕',
  'Every figure is before freight, prep, duty and customs.',
  'No ECB rate was read, so every sterling cost is blank.',
  'Check the two pictures below, or open both listings.',
  'Cost per unit, with 21% Spanish VAT',
  'Delegate the translation',
  'Navigate to the supplier',
  'A setting that is off',
  'Planes and trains',
  '{n} lines need a look before buying',
  'Show all ${count} with their reasons',
]) {
  it(`silent on "${s}"`, () => assert.deepStrictEqual(hard(s), []));
}
it('a known acronym is not a P3 look', () => assert.deepStrictEqual(all('Price with VAT from the EAN on amazon.co.uk'), []));
it('an unknown upper-case code is a P3 look', () => assert.ok(all('Contents UNCLEAR').includes('P3')));

/* ── deck mode ── */

const deck = (rows, header = '| # | Where | Current | What it means | Ships as | Screen |') =>
  `# Brief\n\n## Copy deck\n\n${header}\n|---|---|---|---|---|---|\n${rows.join('\n')}\n\n## Next\n`;

it('R1 — a brief with no Copy deck fails', () => {
  assert.ok(checkDeck('# Brief\n\nno deck here\n').findings.some((f) => f.code === 'R1'));
});
it('a well-formed deck is clean', () => {
  const r = checkDeck(deck(['| 1 | head | — | the lines to buy | 3 lines worth buying | a✓ b✓ c✓ d✓ |']));
  assert.strictEqual(r.rows, 1);
  assert.deepStrictEqual(r.findings, []);
});
it('R2 — a row missing part (d) fails', () => {
  const r = checkDeck(deck(['| 1 | head | — | x | 3 lines worth buying | a✓ b✓ c✓ |']));
  assert.ok(r.findings.some((f) => f.code === 'R2' && /\(d\)/.test(f.detail)));
});
it('R3 — a row recording a failed part fails', () => {
  const r = checkDeck(deck(['| 1 | head | — | x | 3 lines worth buying | a✓ b✗ needs a noun c✓ d✓ |']));
  assert.ok(r.findings.some((f) => f.code === 'R3'));
});
it('R4 — an empty Ships-as fails', () => {
  const r = checkDeck(deck(['| 1 | head | — | x |  | a✓ b✓ c✓ d✓ |']));
  assert.ok(r.findings.some((f) => f.code === 'R4'));
});
it('a banned word in Ships as fails even with all four marks', () => {
  const r = checkDeck(deck([`| 1 | head | — | x | ${golden[0].current} | a✓ b✓ c✓ d✓ |`]));
  assert.ok(r.findings.some((f) => f.code === 'V1'));
});
it('a banned word in the Current column alone is silent (it is being replaced)', () => {
  const r = checkDeck(deck([`| 1 | head | ${golden[0].current} | x | ${golden[0].ships} | a✓ b✓ c✓ d✓ |`]));
  assert.deepStrictEqual(r.findings, []);
});
it('the section ends at the next heading of the same level', () => {
  const md = deck(['| 1 | h | — | x | 3 lines worth buying | a✓ b✓ c✓ d✓ |']) + '| stray | table | settle |\n';
  assert.strictEqual(checkDeck(md).rows, 1);
});

console.log(`copy-screen: ${pass} passed, ${failures.length} failed`);
if (failures.length > 0) {
  for (const f of failures) console.log(`  ✗ ${f}`);
  process.exit(1);
}
