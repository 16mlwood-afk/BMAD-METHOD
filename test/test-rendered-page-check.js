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
