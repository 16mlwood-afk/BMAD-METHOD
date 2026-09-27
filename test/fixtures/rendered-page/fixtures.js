/**
 * Rendered-page snapshots for test/test-rendered-page-check.js.
 *
 * Two of these are the price-list page the owner rejected on 2026-09-27, rebuilt from the measured
 * values in the audit (price-list-ui-audit-2026-09-27.md, §§1, 4, 5, 6): the live strings are quoted
 * from it, the sizes, colours and positions are the ones it measured at 1440×900. Where the audit
 * quotes only part of the text above the first row, `filler()` stands in for the unquoted remainder so
 * the total matches the measured 288 words. The filler is labelled as filler; it is not page copy.
 *
 * The snapshot shape is what tools/check-rendered-page.js `probe()` returns from a live page.
 */

'use strict';

const INK = 'oklch(0.2 0 0)';
const MUTED = 'oklch(0.45 0 0)';
const WHITE = 'rgb(255, 255, 255)';
const HAIRLINE = { width: 1, style: 'solid', color: 'rgb(229, 229, 229)' };
const NONE = { width: 0, style: 'none', color: 'rgb(0, 0, 0)' };

const floor = {
  standard: 'STD-PRESENTATION-FLOOR-001',
  viewport: { width: 1440, height: 900 },
  typeScale: {
    answer: { size: 28, weight: 600, use: 'the one sentence that answers the page' },
    sectionHeading: { size: 18, weight: 600, use: 'the name of a group of items' },
    figure: { size: 16, weight: 500, use: 'the deciding figure on each item' },
    body: { size: 14, weight: 400, use: 'item names and sentences' },
    caption: { size: 12, weight: 400, use: 'the basis beside a figure, and the footer' },
  },
  spacing: [4, 8, 12, 16, 24, 32, 48],
  colours: [
    { name: 'ink', value: INK, means: 'text and figures' },
    { name: 'muted', value: MUTED, means: 'captions and the footer; the one secondary grey' },
    { name: 'ground', value: 'oklch(1 0 0)', means: 'the page' },
    { name: 'rule', value: 'oklch(0.9 0 0)', means: 'hairlines between items' },
    { name: 'act', value: 'oklch(0.5 0.15 255)', means: 'someone must act and nobody is acting yet; links' },
  ],
  attention: {
    top: 'the answer',
    firstItem: 'the first line worth a look',
    provenance: ['FX rate', 'data dates', 'import stamp'],
    provenanceTo: 'footer',
  },
  layout: { summaryFirst: true, items: 'cards', atRestFields: 3, detailOnOpen: true },
  banned: ['tinted-callout', 'edge-stripe', 'stacked-badges', 'all-caps-labels', 'repeated-fact'],
  budgets: { wordsToFigure: 12, proseAboveFirstItem: 60, borderedAllowed: 0, headerMaxFraction: 0.4, repeatedClauseMax: 4 },
};

let ORDER = 0;
function text(t, size, weight, top, height, extra = {}) {
  return {
    order: ORDER++,
    tag: 'p',
    text: t,
    fontSize: size,
    fontWeight: weight,
    fontFamily: 'Inter',
    color: INK,
    textTransform: 'none',
    bgStack: [WHITE],
    inAnswer: false,
    control: false,
    top,
    bottom: top + height,
    left: 240,
    width: 900,
    height,
    ...extra,
  };
}
function block(cls, t, top, height, extra = {}) {
  return {
    tag: 'div',
    cls,
    text: t,
    words: t.split(/\s+/).filter(Boolean).length,
    background: 'rgba(0, 0, 0, 0)',
    border: { top: NONE, right: NONE, bottom: NONE, left: NONE },
    item: false,
    control: false,
    top,
    bottom: top + height,
    left: 240,
    width: 900,
    height,
    ...extra,
  };
}
const allRound = (b) => ({ top: b, right: b, bottom: b, left: b });

/** A page that follows the floor: answer with a figure first, one line of next action, then items. */
function cleanPage() {
  ORDER = 0;
  const items = [
    ['Oral-B iO9 Magnetic, white', '£65.34', 'most it could make a unit, 90-day average'],
    ['Oral-B iO7, black onyx', '£41.10', 'most it could make a unit, 30-day average'],
    ['Oral-B Pro 3 3500, pink', '£12.80', 'most it could make a unit, spot price'],
  ];
  const texts = [
    text("Media Electrónics' Oral-B price list, 23 September", 12, 400, 96, 16, { color: MUTED }),
    text('3 of 17 lines could make money once freight is priced; none is a buy yet.', 28, 600, 120, 36, { inAnswer: true, tag: 'h1' }),
    text('Ask the supplier what freight from Spain to Leipzig costs.', 14, 400, 168, 20),
    text('Ask on WhatsApp', 14, 500, 168, 20, { control: true, tag: 'a' }),
    text('Worth a look', 18, 600, 220, 24, { tag: 'h2' }),
  ];
  const blocks = [];
  items.forEach(([name, fig, cap], i) => {
    const top = 256 + i * 88;
    texts.push(text(name, 14, 400, top + 12, 20), text(fig, 16, 500, top + 36, 20), text(cap, 12, 400, top + 58, 16, { color: MUTED }));
    blocks.push(block('item', `${name} ${fig} ${cap}`, top, 80, { item: true, border: allRound(HAIRLINE) }));
  });
  texts.push(
    text('FX €1 = £0.86045, ECB reference rate of 25 Sep 2026. Imported 26 Sep 13:38.', 12, 400, 1400, 16, { color: MUTED }),
  );
  return {
    schema: 'rendered-page-snapshot/1',
    url: 'fixture://clean',
    theme: 'light',
    viewport: { width: 1440, height: 900 },
    pageBackground: WHITE,
    answer: { text: texts[1].text, top: 120, bottom: 156 },
    firstItem: { text: items[0].join(' '), top: 256, bottom: 336 },
    texts,
    blocks,
  };
}

/** Words that stand in for the part of the measured 288 the audit does not quote. Labelled filler. */
function filler(n) {
  return Array.from({ length: n }, (_, i) => `filler${i}`).join(' ');
}

/** The `.plr-next` box exactly as bundle (3) drew it and the page shipped it (audit §5). */
const YELLOW_BOX_TEXT =
  'Next: get Spain → Leipzig priced. It is question 1 on the right. Until it is priced, no line can be worth buying. WhatsApp ↗';
function yellowBox(top) {
  return block('plr-next', YELLOW_BOX_TEXT, top, 44, {
    background: 'oklch(0.98 0.02 85)',
    border: allRound({ width: 1, style: 'solid', color: 'oklch(0.62 0.13 70)' }),
  });
}

/** Clean page with the yellow box added above the list. */
function cleanWithYellowBox() {
  const s = cleanPage();
  s.blocks.push(yellowBox(196));
  s.texts.push(text(YELLOW_BOX_TEXT, 14, 400, 208, 20, { bgStack: ['oklch(0.98 0.02 85)', WHITE] }));
  return s;
}

/** The live page, light theme (audit §§1, 4, 6): 288 words above the first row, which starts at y=739. */
function livePriceList(theme = 'light') {
  ORDER = 0;
  const ground = theme === 'dark' ? 'oklch(0.145 0 0)' : WHITE;
  const ink = theme === 'dark' ? 'oklch(0.95 0 0)' : 'oklch(0.15 0 0)';
  const grey = theme === 'dark' ? 'oklch(0.72 0 0)' : 'oklch(0.48 0 0)';
  const subtle = theme === 'dark' ? 'oklch(0.55 0 0)' : 'oklch(0.52 0 0)';
  const t = (s, size, weight, top, h, extra = {}) => text(s, size, weight, top, h, { color: ink, bgStack: [ground], ...extra });
  const quoted = [
    t(
      'sent 2026-09-23-price-list-of-oral-b-23-09.xlsx on 23 Sep 2026, checked 26 Sep 13:29 UTC (SR-20260926-005) · an earlier check of this list exists',
      12,
      400,
      100,
      18,
      { color: grey, fontFamily: 'JetBrains Mono' },
    ),
    t(
      'Nothing on this list is worth buying yet. Every profit once delivered to Amazon UK is before Spain → Leipzig, which nobody has priced yet, so each is the most the line could make.',
      18,
      600,
      137,
      48,
      { inAnswer: true, tag: 'h1' },
    ),
    t('17 lines checked; 0 worth buying until freight is priced.', 14, 400, 196, 20),
    t(YELLOW_BOX_TEXT, 14, 600, 230, 20, { bgStack: [theme === 'dark' ? 'oklch(0.62 0.13 70 / 0.1)' : 'oklch(0.98 0.02 85)', ground] }),
    t(
      'Profit once delivered takes every priced cost… The profit at the supplier’s price leaves out freight, prep, customs and duty.',
      12,
      400,
      290,
      34,
      { color: grey },
    ),
    t('No Spanish VAT is added… Ask them before ordering.', 12, 400, 330, 17, { color: grey }),
    t('€1 = £0.86045, ECB reference rate of 25 Sep 2026.', 12, 400, 350, 17, { color: grey }),
    t('Lines selling for under £30 on Amazon UK are skipped.', 12, 400, 370, 17, { color: grey }),
    t('UK prices and sales as Keepa read them on 25–26 Sep, not live.', 12, 400, 390, 17, { color: grey }),
    t('Buy, check and skip calls made by amazon-removal-assistant; imported 26 Sep 13:38.', 12, 400, 410, 17, { color: grey }),
    t('1 question for the supplier, not yet answered', 14, 500, 140, 20, { left: 1100, width: 300 }),
    t('What would freight cost from you to Leipzig?', 14, 400, 170, 20, { left: 1100, width: 300 }),
  ];
  quoted.push(t('Profit once delivered, before Spain → Leipzig: the most it can cost a unit', 12, 600, 617, 52));
  const quotedWords = quoted.reduce((n, x) => n + x.text.split(/\s+/).filter((w) => /[\p{L}\p{N}]/u.test(w)).length, 0);
  const texts = [...quoted, t(filler(288 - quotedWords), 12, 400, 440, 160, { color: grey })];
  const blocks = [
    block('plr-next', YELLOW_BOX_TEXT, 220, 44, {
      background: theme === 'dark' ? 'oklch(0.62 0.13 70 / 0.1)' : 'oklch(0.98 0.02 85)',
      border: allRound({ width: 1, style: 'solid', color: theme === 'dark' ? 'oklch(0.62 0.13 70 / 0.7)' : 'oklch(0.62 0.13 70)' }),
    }),
  ];
  for (let i = 0; i < 17; i += 1) {
    const top = 739 + i * 106;
    const floorMargin = 35 - i;
    texts.push(
      t(`Row ${String(i + 7).padStart(2, '0')} · IO${i}MAG`, 12, 400, top, 17, { color: grey, fontFamily: 'JetBrains Mono' }),
      t(`Oral-B line ${i + 1}`, 14, 500, top + 20, 20),
      t(`£${(65.34 - i).toFixed(2)}`, 18, 600, top + 44, 26),
      t(`£${floorMargin} over the £30 floor`, 12, 400, top + 74, 17, { color: grey }),
    );
  }
  texts.push(
    t('imported 2026-09-26 13:38:09', 12, 400, 2600, 17, { color: subtle }),
    t('FX: ECB, fetched 2026-09-26 11:00', 12, 400, 2620, 17, { color: subtle }),
  );
  return {
    schema: 'rendered-page-snapshot/1',
    url: 'fixture://live-price-list-190',
    theme,
    viewport: { width: 1440, height: 900 },
    pageBackground: ground,
    answer: { text: quoted[1].text, top: 137, bottom: 185 },
    firstItem: { text: 'Row 07 Oral-B line 1', top: 739, bottom: 820 },
    texts,
    blocks,
  };
}

/** The clean page, but with 288 words between the answer and the list, pushing the list to y=739. */
function clean288() {
  const s = cleanPage();
  const shift = 739 - 256;
  for (const x of s.texts) if (x.top >= 220) Object.assign(x, { top: x.top + shift, bottom: x.bottom + shift });
  for (const b of s.blocks) Object.assign(b, { top: b.top + shift, bottom: b.bottom + shift });
  const above = s.texts.filter((x) => x.bottom <= 739 && !x.control);
  const have = above.reduce((n, x) => n + x.text.split(/\s+/).filter(Boolean).length, 0);
  s.texts.push(text(filler(288 - have), 12, 400, 200, 400, { color: MUTED }));
  s.firstItem = { ...s.firstItem, top: 739, bottom: 819 };
  return s;
}

module.exports = { floor, cleanPage, cleanWithYellowBox, livePriceList, clean288, yellowBox, text, block, allRound, YELLOW_BOX_TEXT, WHITE, MUTED };
