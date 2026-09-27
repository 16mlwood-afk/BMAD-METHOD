/**
 * test-rendered-page-check.js — golden suite for tools/check-rendered-page.js (STD-PRESENTATION-FLOOR-001).
 *
 * The two failing goldens the owner named on 2026-09-27 lead: the yellow `.plr-next` box, and the 288
 * words above the first row. Both are rebuilt from the measured audit (test/fixtures/rendered-page/).
 * The rest pin each check in both directions, and a good share assert SILENCE — a neutral item card,
 * a tab underline, an acronym, one plain bordered block inside its budget — because a rendered-page
 * check that fires on ordinary pages gets switched off.
 *
 * Run: node test/test-rendered-page-check.js   (wired as `npm run test:rendered-page`)
 */

'use strict';
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const {
  checkSnapshot,
  validateBrief,
  floorFromBrief,
  parseColour,
  contrastRatio,
  compositeStack,
  probe,
} = require('../tools/check-rendered-page.js');
const F = require('./fixtures/rendered-page/fixtures.js');

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
const run = (snap, floor = F.floor) => checkSnapshot(snap, floor);
const status = (snap, id, floor) => run(snap, floor).find((r) => r.id === id).status;
const failed = (snap, floor) =>
  run(snap, floor)
    .filter((r) => r.status === 'fail')
    .map((r) => r.id);

/* ── the owner's two named failing goldens ── */

it('GOLDEN yellow box — the .plr-next box fails as a tinted callout', () => {
  assert.strictEqual(status(F.cleanWithYellowBox(), 'R3'), 'fail');
});
it('GOLDEN yellow box — it also spends the bordered-block budget', () => {
  assert.strictEqual(status(F.cleanWithYellowBox(), 'R4'), 'fail');
});
it('GOLDEN yellow box — without it the same page is clean', () => {
  assert.deepStrictEqual(failed(F.cleanPage()), []);
});
it('GOLDEN 288 words — the fixture carries exactly the measured 288 words above the first row', () => {
  const s = F.clean288();
  const n = s.texts.filter((t) => t.bottom <= s.firstItem.top && !t.control).reduce((a, t) => a + t.text.split(/\s+/).length, 0);
  assert.strictEqual(n, 288);
});
it('GOLDEN 288 words — fails the prose budget and the fold', () => {
  const f = failed(F.clean288());
  assert.ok(f.includes('R7'), f.join(','));
  assert.ok(f.includes('R11'), f.join(','));
});

/* ── the live page as the audit measured it ── */

it('LIVE light — fails every check the audit says it should, and no other', () => {
  assert.deepStrictEqual(failed(F.livePriceList('light')).sort(), ['R1', 'R11', 'R2', 'R3', 'R4', 'R6', 'R7', 'R8'].sort());
});
it('LIVE light — the 288 words are counted', () => {
  const r = run(F.livePriceList('light')).find((x) => x.id === 'R7');
  assert.match(r.detail, /^288 word/);
});
it('LIVE light — the headline reaches no figure within 12 words', () => {
  const r = run(F.livePriceList('light')).find((x) => x.id === 'R6');
  assert.strictEqual(r.status, 'fail');
  assert.ok(Number.parseInt(r.detail, 10) > 30, r.detail);
});
it('LIVE light — the 17 row profits at the headline size are what R2 names', () => {
  const r = run(F.livePriceList('light')).find((x) => x.id === 'R2');
  assert.match(r.detail, /^17 element/);
});
it('LIVE light — "over the £30 floor" down 17 rows is a repeated fact', () => {
  const r = run(F.livePriceList('light')).find((x) => x.id === 'R8');
  assert.ok(
    r.evidence.some((e) => e.includes('×17') && e.includes('over the # floor')),
    r.evidence.join(' | '),
  );
});
it('LIVE dark — adds the 4.1:1 footer grey the audit measured', () => {
  const r = run(F.livePriceList('dark')).find((x) => x.id === 'R9');
  assert.strictEqual(r.status, 'fail');
  assert.ok(
    r.evidence.some((e) => e.startsWith('4.08:1')),
    r.evidence.join(' | '),
  );
});

/* ── colour maths ── */

it('oklch(0.55) on oklch(0.145) is 4.08:1, as the audit computed', () => {
  assert.strictEqual(contrastRatio(parseColour('oklch(0.55 0 0)'), compositeStack(['oklch(0.145 0 0)'])).toFixed(2), '4.08');
});
it('black on white is 21:1', () => {
  assert.strictEqual(contrastRatio(parseColour('#000'), compositeStack(['#fff'])).toFixed(0), '21');
});
it('rgb, rgba, hex, color(srgb) and oklch with alpha all parse', () => {
  for (const c of [
    'rgb(1, 2, 3)',
    'rgba(1,2,3,0.5)',
    '#abcdef',
    '#abc',
    'color(srgb 0.1 0.2 0.3)',
    'oklch(0.62 0.13 70 / 0.7)',
    'oklch(62% 0.13 70)',
  ])
    assert.ok(parseColour(c), c);
});
it('an unparseable text colour makes contrast UNCHECKED, never a pass', () => {
  const s = F.cleanPage();
  s.texts[0].color = 'lab(50 20 30)';
  assert.strictEqual(status(s, 'R9'), 'unchecked');
});

/* ── R1 / R2 type ── */

it('R1 — a size off the declared scale fails', () => {
  const s = F.cleanPage();
  s.texts[2].fontSize = 13;
  assert.strictEqual(status(s, 'R1'), 'fail');
});
it('R1 — a figure set at the answer size fails (one size, one job)', () => {
  const s = F.cleanPage();
  s.texts[6].fontSize = 28;
  assert.strictEqual(status(s, 'R1'), 'fail');
});
it('R1 — an answer set below the answer role fails', () => {
  const s = F.cleanPage();
  s.texts[1].fontSize = 18;
  assert.strictEqual(status(s, 'R1'), 'fail');
});
it('R2 — no [data-answer] is UNCHECKED, not a pass', () => {
  const s = F.cleanPage();
  s.answer = null;
  for (const t of s.texts) t.inAnswer = false;
  assert.strictEqual(status(s, 'R2'), 'unchecked');
  assert.strictEqual(status(s, 'R6'), 'unchecked');
});

/* ── R3 / R4 / R5 blocks — mostly silence ── */

it('R3 silent — a neutral grey panel is not a tint', () => {
  const s = F.cleanPage();
  s.blocks.push(F.block('panel', 'Some neutral panel with enough words', 180, 40, { background: 'oklch(0.97 0 0)' }));
  assert.strictEqual(status(s, 'R3'), 'pass');
});
it('R3 silent — a tinted item card (a selected row) is not a notice box', () => {
  const s = F.cleanPage();
  s.blocks[0].background = 'oklch(0.96 0.03 250)';
  assert.strictEqual(status(s, 'R3'), 'pass');
});
it('R3 silent — a tinted status label of two words is a label, not a box', () => {
  const s = F.cleanPage();
  s.blocks.push(F.block('pill', 'not priced', 300, 18, { background: 'oklch(0.95 0.05 70)', width: 70 }));
  assert.strictEqual(status(s, 'R3'), 'pass');
});
it('R3 — the dark-mode box (amber at 10%) still fails', () => {
  assert.strictEqual(status(F.livePriceList('dark'), 'R3'), 'fail');
});
it('R4 silent — ONE plain bordered block passes when the brief allows one (an owed action nobody is chasing)', () => {
  const s = F.cleanPage();
  s.blocks.push(
    F.block('owed', 'Freight from Spain is owed and nobody is chasing it', 196, 40, {
      border: F.allRound({ width: 1, style: 'solid', color: 'rgb(60,60,60)' }),
    }),
  );
  const floor = { ...F.floor, budgets: { ...F.floor.budgets, borderedAllowed: 1 } };
  assert.strictEqual(status(s, 'R4', floor), 'pass');
  assert.strictEqual(status(s, 'R3', floor), 'pass');
});
it('R4 silent — bordered item cards are the layout, not a budget spend', () => {
  assert.strictEqual(status(F.cleanPage(), 'R4'), 'pass');
});
it('R5 — a 3px coloured left stripe fails', () => {
  const s = F.cleanPage();
  s.blocks.push(
    F.block('note', 'A note with a stripe on the left side', 180, 40, {
      border: {
        ...F.allRound({ width: 0, style: 'none', color: 'rgb(0,0,0)' }),
        left: { width: 3, style: 'solid', color: 'oklch(0.6 0.15 250)' },
      },
    }),
  );
  assert.strictEqual(status(s, 'R5'), 'fail');
});
it('R5 — a card with a coloured top edge over a hairline fails', () => {
  const s = F.cleanPage();
  s.blocks[0].border = {
    ...F.allRound({ width: 1, style: 'solid', color: 'rgb(229,229,229)' }),
    top: { width: 4, style: 'solid', color: 'oklch(0.55 0.2 25)' },
  };
  assert.strictEqual(status(s, 'R5'), 'fail');
});
it('R5 silent — a bottom divider is a rule, not a stripe', () => {
  const s = F.cleanPage();
  s.blocks.push(
    F.block('head', 'Worth a look and more words here', 220, 24, {
      border: {
        ...F.allRound({ width: 0, style: 'none', color: 'rgb(0,0,0)' }),
        bottom: { width: 2, style: 'solid', color: 'oklch(0.3 0 0)' },
      },
    }),
  );
  assert.strictEqual(status(s, 'R5'), 'pass');
});
it('R5 silent — an active tab underline is a control', () => {
  const s = F.cleanPage();
  s.blocks.push(
    F.block('tab', 'Worth a look tab label here', 220, 24, {
      control: true,
      border: {
        ...F.allRound({ width: 0, style: 'none', color: 'rgb(0,0,0)' }),
        left: { width: 3, style: 'solid', color: 'oklch(0.5 0.15 255)' },
      },
    }),
  );
  assert.strictEqual(status(s, 'R5'), 'pass');
});

/* ── R6 / R7 / R8 words ── */

it('R6 — a figure at word 12 passes, at word 13 fails', () => {
  const s = F.cleanPage();
  s.texts[1].text = 'one two three four five six seven eight nine ten eleven twelve 3 lines';
  assert.strictEqual(status(s, 'R6'), 'pass');
  s.texts[1].text = 'one two three four five six seven eight nine ten eleven twelve thirteen 3 lines';
  assert.strictEqual(status(s, 'R6'), 'fail');
});
it('R7 — control labels do not count as prose', () => {
  const s = F.cleanPage();
  s.texts.push(F.text(Array.from({ length: 80 }, () => 'word').join(' '), 14, 500, 170, 20, { control: true }));
  assert.strictEqual(status(s, 'R7'), 'pass');
});
it('R7 — no [data-first-item] is UNCHECKED', () => {
  const s = F.cleanPage();
  s.firstItem = null;
  assert.strictEqual(status(s, 'R7'), 'unchecked');
  assert.strictEqual(status(s, 'R11'), 'unchecked');
});
it('R8 — the same sentence twice fails', () => {
  const s = F.cleanPage();
  s.texts.push(F.text('FX €1 = £0.86045, ECB reference rate of 25 Sep 2026. Imported 26 Sep 13:38.', 12, 400, 1500, 16));
  assert.strictEqual(status(s, 'R8'), 'fail');
});
it('R8 silent — the same shape with a different number is a different fact (30-day vs 90-day basis)', () => {
  const s = F.cleanPage();
  s.texts.push(F.text('FX €1 = £0.86, ECB reference rate of 24 Sep 2026. Imported 25 Sep 12:00.', 12, 400, 1500, 16));
  assert.strictEqual(status(s, 'R8'), 'pass');
});
it('R8 — one label clause on every one of 17 rows fails, whatever the numbers', () => {
  const s = F.cleanPage();
  for (let i = 0; i < 17; i += 1) s.texts.push(F.text(`most it could make a unit, ${i}-day average`, 12, 400, 1600 + i * 20, 16));
  assert.strictEqual(status(s, 'R8'), 'fail');
});
it('R8 silent — a clause down four items is within the default', () => {
  const s = F.cleanPage();
  for (let i = 0; i < 4; i += 1) s.texts.push(F.text(`£${i} over the £30 floor`, 12, 400, 1600 + i * 20, 16));
  assert.strictEqual(status(s, 'R8'), 'pass');
});

/* ── R10 caps ── */

it('R10 — text-transform:uppercase fails', () => {
  const s = F.cleanPage();
  s.texts[4].textTransform = 'uppercase';
  assert.strictEqual(status(s, 'R10'), 'fail');
});
it('R10 — a BUY / CHECK pill fails', () => {
  const s = F.cleanPage();
  s.texts.push(F.text('CHECK', 12, 600, 300, 14));
  assert.strictEqual(status(s, 'R10'), 'fail');
});
it('R10 silent — VAT, UK, FBA, ECB and a model code are not shouting', () => {
  const s = F.cleanPage();
  s.texts.push(F.text('No VAT on UK FBA stock; ECB rate; model EN267 and iO9.', 14, 400, 1700, 16));
  assert.strictEqual(status(s, 'R10'), 'pass');
});

/* ── R11 fold ── */

it('R11 — a snapshot not taken at 1440×900 is UNCHECKED', () => {
  const s = F.cleanPage();
  s.viewport = { width: 1280, height: 800 };
  assert.strictEqual(status(s, 'R11'), 'unchecked');
});
it('R11 — a first item cut by the fold fails', () => {
  const s = F.cleanPage();
  s.firstItem = { ...s.firstItem, top: 300, bottom: 950 };
  assert.strictEqual(status(s, 'R11'), 'fail');
});

/* ── a snapshot over nothing ── */

it('an empty snapshot passes nothing', () => {
  const r = run({ viewport: { width: 1440, height: 900 }, texts: [], blocks: [] });
  assert.ok(r.filter((x) => ['R1', 'R2', 'R6', 'R7', 'R9', 'R10', 'R11'].includes(x.id)).every((x) => x.status === 'unchecked'));
});

/* ── Gate 1: the brief ── */

const GOLDEN_BRIEF = fs.readFileSync(path.join(__dirname, 'fixtures', 'rendered-page', 'brief-golden.md'), 'utf8');

it('the golden brief validates clean', () => {
  assert.deepStrictEqual(validateBrief(GOLDEN_BRIEF).findings, []);
});
it('the golden brief floor is the fixture floor the page checks run against', () => {
  const { floor } = floorFromBrief(GOLDEN_BRIEF);
  assert.deepStrictEqual(Object.keys(floor.typeScale).sort(), Object.keys(F.floor.typeScale).sort());
  assert.deepStrictEqual(failed(F.cleanPage(), floor), []);
  assert.ok(failed(F.livePriceList('light'), floor).includes('R3'));
});
it('a brief without Part 2b fails Gate 1', () => {
  const codes = validateBrief('# Design Brief\n## Part 2 · What must be true\n').findings.map((f) => f.code);
  assert.ok(codes.includes('B1') && codes.includes('B2'), codes.join(','));
});
it('a brief whose roles share a size fails (one size, two jobs)', () => {
  const b = GOLDEN_BRIEF.replace('"figure": { "size": 16', '"figure": { "size": 18');
  assert.ok(validateBrief(b).findings.some((f) => f.code === 'B3'));
});
it('a brief whose answer is not the largest role fails', () => {
  const b = GOLDEN_BRIEF.replace('"answer": { "size": 28', '"answer": { "size": 17');
  assert.ok(validateBrief(b).findings.some((f) => f.code === 'B3'));
});
it('a brief missing the tinted-callout ban fails', () => {
  const b = GOLDEN_BRIEF.replace('"tinted-callout", ', '');
  assert.ok(validateBrief(b).findings.some((f) => f.code === 'B8' && f.detail.includes('tinted-callout')));
});
it('a brief missing a policy citation fails', () => {
  const b = GOLDEN_BRIEF.replaceAll('docs/supplier-buyer-profile.md', 'somewhere');
  assert.ok(validateBrief(b).findings.some((f) => f.code === 'B10' && f.detail.includes('supplier-relationship')));
});
it('a brief whose provenance goes to the top fails', () => {
  const b = GOLDEN_BRIEF.replace('"provenanceTo": "footer"', '"provenanceTo": "top"');
  assert.ok(validateBrief(b).findings.some((f) => f.code === 'B6'));
});
it('an unrendered {placeholder} in Part 2b fails', () => {
  const b = GOLDEN_BRIEF.replace('the sentence that answers the page', '{answer_use}');
  assert.ok(validateBrief(b).findings.some((f) => f.code === 'B11'));
});

/* ── the template and the probe stay wired ── */

it('brief-template.md carries Part 2b and a presentation-floor block', () => {
  const t = fs.readFileSync(path.join(__dirname, '..', 'custom', 'workflows', 'design', 'design-handoff', 'brief-template.md'), 'utf8');
  assert.match(t, /## Part 2b · The presentation floor/);
  assert.match(t, /```json presentation-floor/);
});
it('the probe serialises to a self-contained function', () => {
  const src = `(${probe.toString()})`;
  assert.ok(src.includes('getComputedStyle') && !src.includes('require('));
});

console.log(`rendered-page check: ${pass} passed, ${failures.length} failed`);
for (const f of failures) console.log(`  ✗ ${f}`);
process.exit(failures.length > 0 ? 1 : 0);
