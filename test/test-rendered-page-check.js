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

/* ── Gate 1, completeness: the gaps Claude Design found in the v4 brief (brief-gap-ledger.md G1–G9) ── */

const V4 = fs.readFileSync(path.join(__dirname, 'fixtures', 'rendered-page', 'brief-v4-pre-review.md'), 'utf8');
const codesOf = (md) => validateBrief(md).findings.map((f) => f.code);
const detailsOf = (md, code) =>
  validateBrief(md)
    .findings.filter((f) => f.code === code)
    .map((f) => f.detail);
const withFloor = (md, edit) =>
  md.replace(/```json presentation-floor\n([\s\S]*?)```/, (_, j) => {
    const floor = JSON.parse(j);
    edit(floor);
    return '```json presentation-floor\n' + JSON.stringify(floor, null, 2) + '\n```';
  });

it('GOLDEN v4 — passes B1–B11, as the real brief did', () => {
  const old = codesOf(V4).filter((c) => Number(c.slice(1)) <= 11);
  assert.deepStrictEqual(old, []);
});
it('GOLDEN v4 — fails every one of B12–B20', () => {
  const got = new Set(codesOf(V4));
  for (const c of ['B12', 'B13', 'B14', 'B15', 'B16', 'B17', 'B18', 'B19', 'B20'])
    assert.ok(got.has(c), `${c} missing: ${[...got].join(',')}`);
});
it('G1 ranked by magnitude alone — fails B12 until evidence tiers lead', () => {
  assert.ok(codesOf(V4).includes('B12'));
  const oneTier = withFloor(GOLDEN_BRIEF, (f) => (f.ordering[0].tiers = ['all lines']));
  assert.ok(codesOf(oneTier).includes('B12'));
});
it('G1 silent — a brief with no ranked list needs no ordering', () => {
  const b = withFloor(GOLDEN_BRIEF.replace('Cards are ranked by', 'Cards come by'), (f) => delete f.ordering);
  assert.ok(!codesOf(b.replace('highest first', 'in the list order')).includes('B12'), detailsOf(b, 'B12').join('; '));
});
it('G2 truncation — fails B13 without what must survive, and without the near-duplicates', () => {
  assert.ok(codesOf(V4).includes('B13'));
  const noSurvive = withFloor(GOLDEN_BRIEF, (f) => (f.truncation[0].mustSurvive = ''));
  assert.ok(detailsOf(noSurvive, 'B13').some((d) => d.includes('mustSurvive')));
  const noDupes = withFloor(GOLDEN_BRIEF, (f) => delete f.truncation[0].nearDuplicates);
  assert.ok(detailsOf(noDupes, 'B13').some((d) => d.includes('nearDuplicates')));
});
it('G2 silent — "none: <how checked>" is a legitimate near-duplicates answer', () => {
  const b = withFloor(GOLDEN_BRIEF, (f) => (f.truncation[0].nearDuplicates = 'none: all 61 names differ in their first 40 characters'));
  assert.ok(!codesOf(b).includes('B13'));
});
it('G3 say-once — the v4 deck says "before freight and prep" in three strings', () => {
  assert.ok(detailsOf(V4, 'B14').some((d) => d.includes('before freight and prep') && d.includes('11, 63, 72')));
});
it('G3 silent — alternatives in one slot, toasts and controls are not repeats', () => {
  const b = GOLDEN_BRIEF.replace(
    '| 9 | Footer |',
    '| 10 | Page answer, some to buy | {n} of these {n} lines could make money once freight is priced, and {n} are buys. | new | a✓ b✓ c✓ d✓ |\n| 11 | Toast after copying twice | Copied a link to row {n} again | new | a✓ b✓ c✓ d✓ |\n| 9 | Footer |',
  );
  assert.deepStrictEqual(detailsOf(b, 'B14'), []);
});
it('G3 silent — a string shown only inside a closed disclosure ("on open") is not at rest', () => {
  const rep = GOLDEN_BRIEF.replace(
    '| 9 | Footer |',
    '| 12 | Held questions, on open | Up to £{n} a unit once at the warehouse, from Keepa. | new | a✓ b✓ c✓ d✓ |\n| 9 | Footer |',
  );
  assert.ok(!codesOf(rep).includes('B14'), detailsOf(rep, 'B14').join('; '));
});
it('G3 — a declared, argued exception passes; an undeclared one does not', () => {
  const rep = GOLDEN_BRIEF.replace('Prices as Keepa read them on {date}.', 'Up to £{n} a unit once at the warehouse, from Keepa.');
  assert.ok(codesOf(rep).includes('B14'));
  const ok = withFloor(rep, (f) => (f.sayOnceExceptions = [{ phrase: 'a unit once at the warehouse', why: 'test' }]));
  assert.ok(!codesOf(ok).includes('B14'));
});
it('G3 — a brief with no Copy deck is not screened, and that is a finding', () => {
  const b = GOLDEN_BRIEF.slice(0, GOLDEN_BRIEF.indexOf('## Copy deck'));
  assert.ok(detailsOf(b, 'B14').some((d) => d.includes('no Copy deck')));
});
it('G4 self-contained — placeholder deck row, "as it is" and a pointer to another brief all fail', () => {
  const d = detailsOf(V4, 'B15');
  assert.ok(
    d.some((x) => x.includes('row 165')),
    d.join('; '),
  );
  assert.ok(
    d.some((x) => x.includes('"as they are"')),
    d.join('; '),
  );
  assert.ok(
    d.some((x) => x.includes('"as it is"')),
    d.join('; '),
  );
  assert.ok(
    d.some((x) => x.includes('points at another brief')),
    d.join('; '),
  );
});
it('G4 silent — "do not design from the earlier brief" and "the price as it is listed" are not pointers', () => {
  const b = GOLDEN_BRIEF.replace(
    '### 4b. Notation',
    'Do not design from the earlier brief for this page. The name is shown as it is listed by the supplier.\n\n### 4b. Notation',
  );
  assert.deepStrictEqual(detailsOf(b, 'B15'), []);
});
it('G5 states × views — a missing cell (skipped × drawer) fails', () => {
  assert.ok(codesOf(V4).includes('B16'));
  const b = withFloor(GOLDEN_BRIEF, (f) => (f.states = f.states.filter((s) => !(s.state === 'skipped' && s.view === 'drawer'))));
  assert.ok(detailsOf(b, 'B16').some((d) => d.includes('"skipped" in view "drawer"')));
});
it('G5 — a matrix without a loading state fails', () => {
  const b = withFloor(GOLDEN_BRIEF, (f) => (f.states = f.states.filter((s) => s.state !== 'loading')));
  assert.ok(detailsOf(b, 'B16').some((d) => d.includes('"loading"')));
});
it('G6 responsive — 1280 missing fails, and a drawer needs overlay or push', () => {
  assert.ok(codesOf(V4).includes('B17'));
  const no1280 = withFloor(GOLDEN_BRIEF, (f) => (f.responsive = f.responsive.filter((r) => r.width !== 1280)));
  assert.ok(detailsOf(no1280, 'B17').some((d) => d.includes('1280')));
  const noMode = withFloor(GOLDEN_BRIEF, (f) => delete f.responsive[2].drawer);
  assert.ok(detailsOf(noMode, 'B17').some((d) => d.includes('overlays or pushes')));
});
it('G7 feedback — actions without a feedback spec fail; one without a duration fails', () => {
  assert.ok(codesOf(V4).includes('B18'));
  const b = withFloor(GOLDEN_BRIEF, (f) => delete f.feedback.durationMs);
  assert.ok(detailsOf(b, 'B18').some((d) => d.includes('duration')));
});
it('G8 headroom — 56 of 60 words fails; 51 passes', () => {
  const at56 = withFloor(GOLDEN_BRIEF, (f) => (f.attention.wordsAboveFirstItem = 56));
  assert.ok(detailsOf(at56, 'B19').some((d) => d.includes('no headroom')));
  const at51 = withFloor(GOLDEN_BRIEF, (f) => (f.attention.wordsAboveFirstItem = 51));
  assert.ok(!codesOf(at51).includes('B19'));
});
it('G9 notation — without a notation line the brief fails B20', () => {
  assert.ok(codesOf(V4).includes('B20'));
  const b = withFloor(GOLDEN_BRIEF, (f) => delete f.notation.separators);
  assert.ok(codesOf(b).includes('B20'));
});
it('the gap ledger is seeded with G1–G9 and each names its check', () => {
  const ledger = fs.readFileSync(path.join(__dirname, '..', 'custom', 'workflows', 'design', 'shared', 'brief-gap-ledger.md'), 'utf8');
  for (let i = 1; i <= 9; i++) assert.match(ledger, new RegExp(`\\| G${i} \\|[^\\n]*\\bB${11 + i}\\b`));
});

/* ── below the fold: the v6 prose wall (presentation-floor.md §9, brief-gap-ledger G10) ── */

const statusW = (snap, id) => status(snap, id, F.floorWithSections);
it('GOLDEN v6 lower half — fails the prose wall, the section forms and the footer', () => {
  const f = failed(F.v6LowerHalf(), F.floorWithSections);
  for (const id of ['R12', 'R13', 'R14']) assert.ok(f.includes(id), `${id} missing: ${f.join(',')}`);
});
it('GOLDEN v6 — R12 names the six-paragraph run under Before you order', () => {
  const r = run(F.v6LowerHalf(), F.floorWithSections).find((x) => x.id === 'R12');
  assert.ok(
    r.evidence.some((e) => e.startsWith('6 paragraphs in a row in "before-you-order"')),
    r.evidence.join('; '),
  );
});
it('GOLDEN v6 — R13 says the held questions are open at rest and Before you order is not rows', () => {
  const ev = run(F.v6LowerHalf(), F.floorWithSections)
    .find((x) => x.id === 'R13')
    .evidence.join('; ');
  assert.match(ev, /"held-questions" \(held\) is open at rest/);
  assert.match(ev, /"before-you-order" is declared as rows but carries no \[data-row\]/);
});
it('GOLDEN v6 — R14 fails a six-line footer with no disclosure', () => {
  assert.strictEqual(statusW(F.v6LowerHalf(), 'R14'), 'fail');
});
it('GOLDEN structured lower half — the same content in rows, disclosures and a two-line footer passes everything', () => {
  assert.deepStrictEqual(failed(F.structuredLowerHalf(), F.floorWithSections), []);
  for (const id of ['R12', 'R13', 'R14']) assert.strictEqual(statusW(F.structuredLowerHalf(), id), 'pass', id);
});
it('R12 silent — two paragraphs side by side are fine', () => {
  const s = F.structuredLowerHalf();
  s.paragraphRuns = [{ length: 2, section: null, sample: 'x' }];
  assert.strictEqual(statusW(s, 'R12'), 'pass');
});
it('R12 — one paragraph over 40 words fails on its own', () => {
  const s = F.structuredLowerHalf();
  s.paragraphs.push({ text: F.FREIGHT_Q, words: 54, section: 'x' });
  assert.strictEqual(statusW(s, 'R12'), 'fail');
});
it('R13 — a row over 12 words after its label fails', () => {
  const s = F.structuredLowerHalf();
  s.sections[2].rows[0].words = 15;
  assert.strictEqual(statusW(s, 'R13'), 'fail');
});
it('R13 — a sixth caveat row fails the five-row cap', () => {
  const s = F.structuredLowerHalf();
  s.sections[2].rows.push({ label: 'Stand-in', text: 'Stand-in wording', words: 1 });
  assert.strictEqual(statusW(s, 'R13'), 'fail');
});
it('R13 — the message block open at rest fails', () => {
  const s = F.structuredLowerHalf();
  s.sections[3].collapsed = false;
  assert.strictEqual(statusW(s, 'R13'), 'fail');
});
it('R13 — a section on the page that the brief never declared fails', () => {
  const s = F.structuredLowerHalf();
  s.sections.push({ name: 'stand-in-note', kind: null, form: null, wordsAtRest: 14, collapsed: false, rows: [] });
  assert.strictEqual(statusW(s, 'R13'), 'fail');
});
it('R13 unchecked — a declared section the page does not mark is not a pass', () => {
  const s = F.structuredLowerHalf();
  s.sections = s.sections.filter((x) => x.name !== 'held-questions');
  assert.strictEqual(statusW(s, 'R13'), 'unchecked');
});
it('R12–R14 unchecked on an old-probe snapshot, never a pass', () => {
  for (const id of ['R12', 'R13', 'R14']) assert.strictEqual(statusW(F.cleanPage(), id), 'unchecked', id);
});
it('R14 — a two-line footer with no disclosure fails: the rest was dropped or printed', () => {
  const s = F.structuredLowerHalf();
  s.footer.hasDisclosure = false;
  assert.strictEqual(statusW(s, 'R14'), 'fail');
});

/* ── Gate 1, B21: every section declares its form ── */

it('B21 — the golden brief declares its sections and passes', () => {
  assert.ok(!codesOf(GOLDEN_BRIEF).includes('B21'));
});
it('GOLDEN v4 — the v4 brief, which let v6 draw the prose wall, fails B21', () => {
  assert.ok(codesOf(V4).includes('B21'));
});
it('B21 — caveats as running prose fail; caveats must be rows', () => {
  const b = withFloor(GOLDEN_BRIEF, (f) => (f.sections[1].form = 'cards'));
  assert.ok(detailsOf(b, 'B21').some((d) => d.includes('must be "rows"')));
});
it('B21 — held questions open at rest fail; they must be a disclosure with a one-line summary', () => {
  const open = withFloor(GOLDEN_BRIEF, (f) => (f.sections[2].form = 'rows'));
  assert.ok(detailsOf(open, 'B21').some((d) => d.includes('must be "disclosure"')));
  const noSummary = withFloor(GOLDEN_BRIEF, (f) => delete f.sections[2].summary);
  assert.ok(detailsOf(noSummary, 'B21').some((d) => d.includes('"summary"')));
});
it('B21 — a message block names its controls', () => {
  const b = withFloor(GOLDEN_BRIEF, (f) => delete f.sections[3].controls);
  assert.ok(detailsOf(b, 'B21').some((d) => d.includes('"controls"')));
});
it('B21 — a footer of six lines at rest fails', () => {
  const b = withFloor(GOLDEN_BRIEF, (f) => (f.sections[4].linesAtRest = 6));
  assert.ok(detailsOf(b, 'B21').some((d) => d.includes('linesAtRest')));
});
it('B21 — a non-item section budget over 60 words fails', () => {
  const b = withFloor(GOLDEN_BRIEF, (f) => (f.sections[1].wordBudget = 180));
  assert.ok(detailsOf(b, 'B21').some((d) => d.includes('at most 60')));
});
it('the gap ledger carries G10 with its checks', () => {
  const ledger = fs.readFileSync(path.join(__dirname, '..', 'custom', 'workflows', 'design', 'shared', 'brief-gap-ledger.md'), 'utf8');
  assert.match(ledger, /\| G10 \|[^\n]*\bB21\b[^\n]*\bR12\b/);
});

/* ── label/value row groups: the bundle 6 journey (presentation-floor.md §10, brief-gap-ledger G11) ── */

const RG = F.floorWithRowGroups;
const rgRun = (snap) => run(snap, RG);
const rg = (snap, id) => rgRun(snap).find((r) => r.id === id);
it('GOLDEN bundle 6 drawer — fails the row cells, the grid, the internal words and the total', () => {
  const f = failed(F.bundle6Drawer(), RG);
  for (const id of ['R15', 'R16', 'R17', 'R18']) assert.ok(f.includes(id), `${id} missing: ${f.join(',')}`);
});
it('GOLDEN bundle 6 — R15 names the status that repeats the value, the sentence in the value column and the long notes', () => {
  const ev = rg(F.bundle6Drawer(), 'R15').evidence.join('; ');
  assert.match(ev, /the value repeats the status \("not priced"\)/);
  assert.match(ev, /the value "in the export; not in this handoff" is 7 words; at most 4/);
  assert.match(ev, /the explanation is \d+ words; at most 12/);
});
it('GOLDEN bundle 6 — R16 finds the ragged status column, the ragged value edge, the proportional figures and the rows spaced like lines', () => {
  const ev = rg(F.bundle6Drawer(), 'R16').evidence.join('; ');
  assert.match(ev, /status text starts at \d+px of different x/);
  assert.match(ev, /value cells end at \d+px of different x/);
  assert.match(ev, /not in tabular numerals/);
  assert.match(ev, /rows are 8px apart and lines inside a row 8px/);
});
it('GOLDEN bundle 6 — R17 catches "export", "handoff" and "record"', () => {
  const ev = rg(F.bundle6Drawer(), 'R17').evidence.join('; ');
  for (const w of ['export', 'handoff', 'record']) assert.ok(ev.includes(`"${w}"`), ev);
});
it('GOLDEN bundle 6 — R18: unpriced legs and no total', () => {
  assert.match(rg(F.bundle6Drawer(), 'R18').evidence.join('; '), /has an unpriced row and shows no total/);
});
it('GOLDEN corrected drawer — the same legs as a grid pass R15–R18, and nothing fails', () => {
  assert.deepStrictEqual(failed(F.correctedDrawer(), RG), []);
  for (const id of ['R15', 'R16', 'R17', 'R18']) assert.strictEqual(rg(F.correctedDrawer(), id).status, 'pass', id);
});
it('R18 — a total over an unpriced leg that does not say partial fails', () => {
  const s = F.correctedDrawer();
  s.rowGroups[0].total = { text: 'Total £1.23', label: 'Total', partial: false };
  assert.strictEqual(rg(s, 'R18').status, 'fail');
});
it('R15 silent — "£0.27" is one value, and money is never counted as words', () => {
  const s = F.correctedDrawer();
  s.rowGroups[0].rows[2].cells[1].text = '£1,234.56 a unit';
  assert.strictEqual(rg(s, 'R15').status, 'pass');
});
it('R15 — two value cells in one row fail', () => {
  const s = F.correctedDrawer();
  s.rowGroups[0].rows[2].cells.push({ ...s.rowGroups[0].rows[2].cells[1], text: '£0.30' });
  assert.strictEqual(rg(s, 'R15').status, 'fail');
});
it('R16 — a status column one row 10px out fails; within 2px passes', () => {
  const s = F.correctedDrawer();
  s.rowGroups[0].rows[4].cells[3].left += 10;
  assert.strictEqual(rg(s, 'R16').status, 'fail');
  const ok = F.correctedDrawer();
  ok.rowGroups[0].rows[4].cells[3].left += 2;
  assert.strictEqual(rg(ok, 'R16').status, 'pass');
});
it('R17 silent — "running", "exported" and "recorded" are not the banned words themselves', () => {
  const s = F.correctedDrawer();
  s.rowGroups[0].rows[2].cells[2].text = 'Recorded on the running tally we exported.';
  assert.strictEqual(rg(s, 'R17').status, 'pass');
});
it('R15–R18 unchecked on an old-probe snapshot; pass on a page that has no row group and declares none here', () => {
  for (const id of ['R15', 'R16', 'R17', 'R18']) assert.strictEqual(rg(F.cleanPage(), id).status, 'unchecked', id);
  const page = { ...F.structuredLowerHalf(), page: 'price-list', rowGroups: [] };
  for (const id of ['R15', 'R16', 'R17', 'R18']) assert.strictEqual(rg(page, id).status, 'pass', id);
});
it('R15–R18 unchecked when the brief declares a row group for this view and the page marks none', () => {
  const s = { page: 'line-drawer', sections: [], rowGroups: [] };
  assert.strictEqual(rg(s, 'R15').status, 'unchecked');
});
it('R13 does not look for a drawer section on the page snapshot', () => {
  const page = { ...F.structuredLowerHalf(), page: 'price-list' };
  assert.strictEqual(status(page, 'R13', RG), 'pass');
});

/* ── Gate 1, B22: a row group is specified as one ── */

const withJourney = (edit) =>
  withFloor(GOLDEN_BRIEF, (f) => {
    const j = structuredClone(F.JOURNEY_SPEC);
    f.internalWords = ['export', 'handoff', 'pipeline', 'record', 'run'];
    f.sections.push(j);
    if (edit) edit(j, f);
  });
it('B22 — a fully specified row group passes', () => {
  assert.deepStrictEqual(detailsOf(withJourney(), 'B22'), []);
});
it('GOLDEN v4 — the v4 brief fails B22 once its journey is declared as facts (the form bundle 6 drew)', () => {
  const b = withFloor(V4, (f) => {
    f.sections = [{ name: 'journey', kind: 'facts', form: 'rows', wordBudget: 200 }];
  });
  assert.ok(codesOf(b).includes('B22'));
});
it('B22 — a status value that says "not priced" repeats the value and fails', () => {
  const b = withJourney((j) => (j.statusValues = ['not priced', 'assumed']));
  assert.ok(detailsOf(b, 'B22').some((d) => d.includes('repeats the value cell')));
});
it('B22 — rows no further apart than the lines in a row fail', () => {
  const b = withJourney((j) => (j.rowGap = 4));
  assert.ok(detailsOf(b, 'B22').some((d) => d.includes('"rowGap" larger than "innerGap"')));
});
it('B22 — a partial total whose label does not say so fails; no total needs a reason', () => {
  const b = withJourney((j) => (j.total = { label: 'Total', partial: true }));
  assert.ok(detailsOf(b, 'B22').some((d) => d.includes('does not say so')));
  const none = withJourney((j) => (j.total = 'none'));
  assert.ok(detailsOf(none, 'B22').some((d) => d.includes('none: <why>')));
});
it('B22 — a value cap over 4 words, a note cap over 12 and left-aligned values each fail', () => {
  assert.ok(
    detailsOf(
      withJourney((j) => (j.valueMaxWords = 8)),
      'B22',
    ).some((d) => d.includes('valueMaxWords')),
  );
  assert.ok(
    detailsOf(
      withJourney((j) => (j.noteMaxWords = 30)),
      'B22',
    ).some((d) => d.includes('noteMaxWords')),
  );
  assert.ok(
    detailsOf(
      withJourney((j) => (j.valueAlign = 'left')),
      'B22',
    ).some((d) => d.includes('"valueAlign"')),
  );
});
it('B22 — a row group needs the internal-word list', () => {
  const b = withJourney((j, f) => (f.internalWords = ['export']));
  assert.ok(detailsOf(b, 'B22').some((d) => d.includes('"handoff"')));
});
it('the gap ledger carries G11 with its checks', () => {
  const ledger = fs.readFileSync(path.join(__dirname, '..', 'custom', 'workflows', 'design', 'shared', 'brief-gap-ledger.md'), 'utf8');
  assert.match(ledger, /\| G11 \|[^\n]*\bB22\b[^\n]*\bR15\b/);
});

/* ── declared exemptions (presentation-floor.md §11, brief-gap-ledger G12) ── */

// The live price list of 2026-09-28 (brand-source-finder /product/190), reduced to the strings the
// build agent reported: two real products that share a name and a basis, a supplier code, a listing
// title in its seller's capitals, and the supplier drawer whose answer has no figure by design.
const EX = {
  ...F.floorWithRowGroups,
  quotedSources: [
    { source: 'supplier', what: "the supplier's codes and titles, verbatim", exempts: ['R8', 'R10', 'R17'] },
    { source: 'amazon-listing', what: "a UK listing's title as its seller wrote it", exempts: ['R8', 'R10'] },
  ],
  exemptions: [
    { check: 'R6', view: 'supplier-lookup', why: 'the supplier drawer answers yes, no or not known; no figure by design' },
    { check: 'R8', scope: 'across-items', max: 2, why: 'rows 7 and 9 are two real lines that share a name and a basis' },
  ],
  internalWordExceptions: [{ phrase: 'invoice it as an export', why: 'the customs term for goods leaving Spain' }],
};
const TWIN = 'Oral-B Pro Kids Electric Toothbrush, Spider-Man, Blue and Red';
const BASIS = 'sells at £37.99, lowest offer';
function livePage() {
  const s = F.cleanPage();
  const add = (t, top, extra) => s.texts.push(F.text(t, 14, 400, top, 20, extra));
  for (const [i, top] of [
    [0, 520],
    [1, 620],
  ].map(([k, y]) => [k, y])) {
    s.blocks.push(
      F.block('item', `${TWIN} ${BASIS}`, top, 80, {
        item: true,
        border: F.allRound({ width: 1, style: 'solid', color: 'rgb(229, 229, 229)' }),
      }),
    );
    add(TWIN, top + 8, { quoted: i === 0 ? 'amazon-listing' : 'amazon-listing' });
    add(BASIS, top + 40, {});
  }
  add('IO2/BK+TC', 720, { quoted: 'supplier' });
  add('DENTAL Braun ORAL-B IO-3 CEPILLO', 750, { quoted: 'amazon-listing' });
  return { ...s, page: 'price-list' };
}
const exRun = (snap, floor = EX) => checkSnapshot(snap, floor);
const exSt = (snap, id, floor = EX) => exRun(snap, floor).find((r) => r.id === id).status;

it('BEFORE — with no exemption declared, the live strings fail R8 and R10 as they did on the live page', () => {
  assert.strictEqual(exSt(livePage(), 'R8', F.floorWithRowGroups), 'fail');
  assert.strictEqual(exSt(livePage(), 'R10', F.floorWithRowGroups), 'fail');
});
it('AFTER — with the brief declaring them, the same strings are exempt, and the report says so', () => {
  const r8 = exRun(livePage()).find((r) => r.id === 'R8');
  assert.strictEqual(r8.status, 'exempt');
  assert.match(r8.detail, /exempt by the brief: rows 7 and 9/);
  assert.strictEqual(exSt(livePage(), 'R10'), 'exempt');
  assert.ok(failed(livePage(), EX).length === 0, failed(livePage(), EX).join(','));
});
it('R10 — an undeclared data-source exempts nothing', () => {
  const s = livePage();
  s.texts.find((t) => t.text === 'IO2/BK+TC').quoted = 'someone-else';
  assert.strictEqual(exSt(s, 'R10'), 'fail');
});
it('R10 — quoted text inside the answer is never exempt', () => {
  const s = livePage();
  s.texts.push(F.text('CHECK THIS', 28, 600, 130, 30, { inAnswer: true, quoted: 'supplier' }));
  assert.strictEqual(exSt(s, 'R10'), 'fail');
});
it('R10 — our own capitals are still caught beside exempt supplier text', () => {
  const s = livePage();
  s.texts.push(F.text('SKIP', 12, 400, 800, 16));
  assert.strictEqual(exSt(s, 'R10'), 'fail');
});
it('R8 across-items — a sentence three times across three items fails a cap of 2', () => {
  const s = livePage();
  s.blocks.push(F.block('item', BASIS, 900, 80, { item: true }));
  s.texts.push(F.text(BASIS, 14, 400, 940, 20));
  assert.strictEqual(exSt(s, 'R8'), 'fail');
});
it('R8 across-items — the same sentence twice inside ONE item still fails', () => {
  const s = livePage();
  s.texts.push(F.text(BASIS, 14, 400, 580, 20));
  assert.strictEqual(exSt(s, 'R8'), 'fail');
});
it("R8 — the owner's ledger pattern (a clause down more than 4 rows) is never exempted", () => {
  const s = livePage();
  for (let i = 0; i < 6; i++) s.texts.push(F.text(`${40 + i} reads not made`, 12, 400, 1000 + i * 20, 16));
  assert.strictEqual(exSt(s, 'R8'), 'fail');
});
it('R6 — exempt on the declared view only', () => {
  const answer = (page) => ({
    ...F.cleanPage(),
    page,
    texts: [F.text('Whether Media Electrónics will invoice us is not known. This is not a no.', 24, 600, 100, 32, { inAnswer: true })],
  });
  assert.strictEqual(exSt(answer('supplier-lookup'), 'R6'), 'exempt');
  assert.strictEqual(exSt(answer('line-drawer'), 'R6'), 'fail');
});
it('R17 — "invoice it as an export" passes by declared phrase; the tooling sense still fails', () => {
  const s = F.correctedDrawer();
  s.rowGroups[0].rows[1].cells[2].text = '0% while they invoice it as an export from Spain.';
  assert.strictEqual(exSt(s, 'R17'), 'pass');
  s.rowGroups[0].rows[2].cells[2].text = 'in the export; not in this handoff';
  assert.strictEqual(exSt(s, 'R17'), 'fail');
});
it('R18 — "Open WhatsApp" is a control, not an unpriced value', () => {
  const s = F.correctedDrawer();
  s.rowGroups[0].rows[2].cells[1].text = 'Open WhatsApp ↗';
  assert.ok(!/unpriced/.test(rg(s, 'R18').evidence.join(' ')));
});
it('NOT LOOSENED — bundle 6 still fails R15–R18 and the v6 lower half R12–R14 under the exemption floor', () => {
  const f6 = failed(F.bundle6Drawer(), EX);
  for (const id of ['R15', 'R16', 'R17', 'R18']) assert.ok(f6.includes(id), `${id}: ${f6.join(',')}`);
  const exSec = { ...EX, sections: F.floorWithSections.sections };
  const fv = failed(F.v6LowerHalf(), exSec);
  for (const id of ['R12', 'R13', 'R14']) assert.ok(fv.includes(id), `${id}: ${fv.join(',')}`);
});

/* ── R19: provenance written into the body (G12) ── */

function liveDrawerProvenance() {
  const s = { ...F.correctedDrawer(), ...F.cleanPage(), page: 'line-drawer' };
  s.texts.push(
    F.text('Named from the supplier’s price-list line.', 12, 400, 300, 16),
    F.text('Known because the price-list run matched this line to its amazon.co.uk listing .', 12, 400, 320, 16),
    F.text('· the supplier’s list', 12, 400, 340, 16),
    F.text('Supplier stock: 20, as listed by the supplier.', 14, 400, 360, 20),
    F.text(', found by Keepa’s code lookup', 12, 400, 380, 16),
  );
  return s;
}
it('GOLDEN live drawer — R19 fails the five provenance captions the owner rejected', () => {
  const r = exRun(liveDrawerProvenance()).find((x) => x.id === 'R19');
  assert.strictEqual(r.status, 'fail');
  assert.match(r.detail, /^5 provenance caption/);
});
it('R19 silent — the same captions in the footer or an open disclosure pass', () => {
  const s = liveDrawerProvenance();
  for (const t of s.texts) if (/named from|known because|supplier’s list|as listed|found by/i.test(t.text)) t.inDisclosure = true;
  assert.strictEqual(exSt(s, 'R19'), 'pass');
});
it('R19 silent — a heading "where the price comes from" and a basis date are not provenance captions', () => {
  const s = F.cleanPage();
  s.texts.push(
    F.text('The product, and where the price comes from', 18, 600, 400, 24),
    F.text('lowest offer, read 26 Sep 2026', 12, 400, 430, 16),
  );
  assert.strictEqual(exSt(s, 'R19'), 'pass');
});

/* ── Gate 1: B23 exemptions are narrow, B24 the brief keeps its own budgets ── */

it('B23 — the exemptions this brief needs pass', () => {
  const b = withFloor(GOLDEN_BRIEF, (f) =>
    Object.assign(f, {
      quotedSources: EX.quotedSources,
      exemptions: EX.exemptions,
      internalWords: EX.internalWords,
      internalWordExceptions: EX.internalWordExceptions,
    }),
  );
  assert.deepStrictEqual(detailsOf(b, 'B23'), []);
});
it('B23 — an exemption from a floor check (R3, the tinted box) is refused', () => {
  const b = withFloor(GOLDEN_BRIEF, (f) => (f.exemptions = [{ check: 'R3', why: 'we like the yellow box very much' }]));
  assert.ok(detailsOf(b, 'B23').some((d) => d.includes('"R3" is not allowed')));
});
it('B23 — R8 across more than 3 items, R6 with no view, a quoted source exempting R1, and an empty reason are refused', () => {
  const d = (e) => detailsOf(withFloor(GOLDEN_BRIEF, e), 'B23');
  assert.ok(d((f) => (f.exemptions = [{ check: 'R8', scope: 'across-items', max: 10, why: 'many cards share it' }])).length > 0);
  assert.ok(d((f) => (f.exemptions = [{ check: 'R6', why: 'no figure here by design at all' }])).some((x) => x.includes('"view"')));
  assert.ok(d((f) => (f.quotedSources = [{ source: 'supplier', what: 'their words verbatim', exempts: ['R1'] }])).length > 0);
  assert.ok(d((f) => (f.exemptions = [{ check: 'R6', view: 'x', why: '' }])).some((x) => x.includes('"why"')));
});
it('B23 — an internal-word exception that is just the word, or holds none, is refused', () => {
  const d = (ph) =>
    detailsOf(
      withFloor(GOLDEN_BRIEF, (f) => (f.internalWordExceptions = [{ phrase: ph, why: 'the customs sense of the word' }])),
      'B23',
    );
  assert.ok(d('export').length > 0);
  assert.ok(d('leaving the EU today').some((x) => x.includes('contains no internal word')));
});
it('G13 GOLDEN — the journey counted with its heading and caption (96 words) fails a budget of 90', () => {
  const j = [
    'The journey to Amazon UK, cost by cost',
    'Spain → Great Blakenham → Amazon UK, Bison as importer',
    'Spain → Great Blakenham freight',
    'not priced',
    "The supplier's freight quote to Great Blakenham fills it.",
    'UK import VAT',
    '£0',
    'if terms hold',
    'Our VAT return covers it; their forwarder needs our EORI in writing.',
    'UK import duty',
    '£0.27',
    '2%, the base case.',
    'Prep at Great Blakenham',
    'not priced',
    'Box handling £0.18 (10 a box, assumed); labels and cartons unknown.',
    'Great Blakenham → Amazon UK parcel',
    '£0.96',
    'assumed',
    'Parcelforce via Parcel2Go at that box count; not measured.',
    'Priced so far, partial',
    '£1.23',
  ];
  const md = GOLDEN_BRIEF.replace(
    '### 4b. Notation in this brief',
    `${j.map((x) => `*${x}*`).join(' ')}\n\n### 4b. Notation in this brief`,
  );
  const b = withFloor(md, (f) => f.sections.push({ ...F.JOURNEY_SPEC, sample: j }));
  assert.ok(
    detailsOf(b, 'B24').some((d) => /journey": the brief's own content is 96 words at rest, over its wordBudget of 90/.test(d)),
    detailsOf(b, 'B24').join('; '),
  );
  const listOnly = withFloor(md, (f) => f.sections.push({ ...F.JOURNEY_SPEC, sample: j.slice(2) }));
  assert.deepStrictEqual(detailsOf(listOnly, 'B24'), []);
});
it('B24 — a sample the brief never writes is refused, and a section with none is flagged', () => {
  const b = withFloor(GOLDEN_BRIEF, (f) => (f.sections[1].sample = ['Words that appear nowhere in this brief']));
  assert.ok(detailsOf(b, 'B24').some((d) => d.includes('is not written anywhere')));
  const none = withFloor(GOLDEN_BRIEF, (f) => delete f.sections[1].sample);
  assert.ok(detailsOf(none, 'B24').some((d) => d.includes('needs "sample"')));
});
it('the gap ledger carries G12 and G13 with their checks', () => {
  const ledger = fs.readFileSync(path.join(__dirname, '..', 'custom', 'workflows', 'design', 'shared', 'brief-gap-ledger.md'), 'utf8');
  assert.match(ledger, /\| G12 \|[^\n]*\bB23\b[^\n]*\bR19\b/);
  assert.match(ledger, /\| G13 \|[^\n]*\bB24\b/);
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
