/**
 * check-rendered-page.js — the deterministic half of the presentation floor (STD-PRESENTATION-FLOOR-001).
 *
 * Home of the rule: custom/workflows/design/shared/presentation-floor.md
 * Consumers:        design-handoff   steps/step-03c-gate1-brief-ready.md §1c  (--validate-brief)
 *                   design-implement steps/step-04b-rendered-page-checks.md   (--snapshot / --url)
 * Suite:            test/test-rendered-page-check.js  (`npm run test:rendered-page`)
 *
 * WHY THIS EXISTS. Owner, 2026-09-27, on the brand-source-finder price-list page: "it's reading like a
 * ledger printed on a screen... no font size enforcement... that yellow thing at the top, the most AI
 * pattern I've ever seen, which hasn't been caught by our anti-AI patterns... audit text at the top".
 * The audit (price-list-ui-audit-2026-09-27.md) found every rule that would have caught it was either
 * advisory in the brief or tested only against amazon-removal-assistant's own generated pages
 * (src/artifact-policy-check.ts). This carries that repository's checks to ANY rendered page, reading
 * the rendered DOM rather than source, because a stylesheet can be clean and the page still wrong.
 *
 * ── What it checks (each is pass | fail | unchecked; unchecked is never a pass) ──
 *   R1  type-tokens        every computed font-size is one of the brief's declared role sizes, and the
 *                          answer size is used by the answer alone (one size, one job)
 *   R2  answer-heaviest    the answer is set larger than every other piece of text on the surface
 *   R3  tinted-callout     no block of prose sits on a tinted (chromatic) fill — the `.plr-next` box
 *   R4  bordered-budget    all-round bordered blocks carrying prose, outside declared items, ≤ budget
 *   R5  edge-stripe        no block carries a coloured stripe on one edge
 *   R6  headline-figure    the answer reaches a figure within N words (default 12)
 *   R7  prose-above-item   words above the first actionable item ≤ budget (default 60)
 *   R8  repeated-sentence  no sentence twice (literal); no clause, numbers ignored, down more than N items
 *   R9  contrast           every text colour meets WCAG AA against the ground it sits on
 *   R10 all-caps           no text-transform:uppercase, no shouted run outside a known acronym
 *   R11 above-the-fold     at the declared viewport (1440×900) the first item is fully visible and
 *                          starts in the top part of the screen (header ≤ headerMaxFraction)
 *
 * ── What it CANNOT check, on purpose ──
 *   Whether the page reads well, whether the answer is the RIGHT answer, and whether a reader gets it
 *   in five seconds (T0/TD0). Those stay a reader's judgement. A green run proves counts and presence,
 *   never quality; a page can pass every budget and still bury the answer.
 *
 * Usage:
 *   node tools/check-rendered-page.js --snapshot <snap.json> --brief <brief.md>   [--json]
 *   node tools/check-rendered-page.js --snapshot <snap.json> --floor <floor.json> [--json]
 *   node tools/check-rendered-page.js --url <url> --brief <brief.md> [--theme dark] [--json]
 *        (needs `playwright` resolvable from the current directory; otherwise exit 2 and says so)
 *   node tools/check-rendered-page.js --validate-brief <brief.md> [--json]        (Gate 1)
 *   node tools/check-rendered-page.js --print-probe                                (browser-side probe)
 *
 * Exit: 0 every check passed · 1 a check failed · 2 bad usage, or a check could not run (unchecked).
 */

'use strict';

const fs = require('node:fs');

/* ─────────────────────────── contract constants ─────────────────────────── */

const STANDARD = 'STD-PRESENTATION-FLOOR-001';
const ROLES = ['answer', 'sectionHeading', 'body', 'figure', 'caption'];
const BANNED_KEYS = ['tinted-callout', 'edge-stripe', 'stacked-badges', 'all-caps-labels', 'repeated-fact'];
/** The ten policies the audit's §7 table found absent or second-hand. Gate 1 requires every one, by path. */
const REQUIRED_CITATIONS = [
  { id: 'artifact-policy', path: 'docs/artifact-policy.md' },
  { id: 'artifact-brief-policy', path: 'docs/artifact-brief-policy.md' },
  { id: 'document-design-format', path: 'docs/document-design-format.md' },
  { id: 'anti-ai-research', path: 'anti-ai-ui-patterns-2026-09-26.md' },
  { id: 'copy-screen', path: 'on-screen-copy-screen.md' },
  { id: 'presented-figures-basis', path: 'presented-figures-declare-their-basis' },
  { id: 'reference-policy', path: 'docs/transcript-policy.md' },
  { id: 'supplier-relationship', path: 'docs/supplier-buyer-profile.md' },
  { id: 'human-facing-documents', path: 'docs/human-facing-documents.md' },
  { id: 'provenance-to-footer', path: 'artifact-policy.md' },
];
const DEFAULT_BUDGETS = {
  wordsToFigure: 12, // artifact-policy.md §5; the audit's live headline: 33
  proseAboveFirstItem: 60, // the audit's live page: 288
  borderedAllowed: 0, // artifact-policy.md §3/§5: 0, or 1 when an owed action nobody is chasing exists
  headerMaxFraction: 0.4, // brief-template B7 "about a third of the viewport"; the audit's live page: 0.82
  repeatedClauseMax: 4, // a clause down more items than this is the same fact restated per row
  contrastMin: 4.5,
  contrastLargeMin: 3,
};
const SIZE_TOLERANCE_PX = 0.5;
const CHROMA_TINT = 0.015; // oklch chroma above which a fill reads as a colour, not a grey
const MIN_BLOCK_WORDS = 4; // a block with fewer words is a label or a control, not a notice
const MIN_SENTENCE_CHARS = 25; // artifact-policy-check.ts repeatedSentences()
const ACRONYMS = new Set(
  (
    'VAT UK GB EU DE FR ES IT NL US USA FBA FBM ASIN SKU MSKU FNSKU EAN UPC GTIN FX ECB GBP EUR USD PDF CSV ' +
    'XLSX ID URL API OK AM PM UTC GMT BST CET HMRC EORI PVA DHL UPS DPD TNT KN LTL FTL SPD ATS RXO AVASK IPR ' +
    'IOSS OSS ISO CE WEEE RRP MOQ ETA PO QTY NB AI UI'
  ).split(' '),
);

/* ─────────────────────────────── colour maths ─────────────────────────────── */

function clamp01(x) {
  return Math.min(1, Math.max(0, x));
}

/** Parse a computed CSS colour. Returns { r, g, b (linear 0..1), a, chroma } or null. */
function parseColour(input) {
  if (!input || typeof input !== 'string') return null;
  const s = input.trim().toLowerCase();
  if (s === 'transparent') return { r: 0, g: 0, b: 0, a: 0, chroma: 0 };
  const toLin = (c) => (c <= 0.040_45 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  const fromSrgb = (r, g, b, a) => {
    const lr = toLin(r),
      lg = toLin(g),
      lb = toLin(b);
    return { r: lr, g: lg, b: lb, a, chroma: oklchChroma(lr, lg, lb) };
  };
  let m = /^#([\da-f]{3,8})$/.exec(s);
  if (m) {
    let h = m[1];
    if (h.length === 3 || h.length === 4) h = [...h].map((c) => c + c).join('');
    const n = (i) => Number.parseInt(h.slice(i, i + 2), 16) / 255;
    return fromSrgb(n(0), n(2), n(4), h.length === 8 ? n(6) : 1);
  }
  m = /^rgba?\(([^)]+)\)$/.exec(s);
  if (m) {
    const parts = m[1].split(/[\s,/]+/).filter(Boolean);
    const ch = (v) => (v.endsWith('%') ? Number.parseFloat(v) / 100 : Number.parseFloat(v) / 255);
    const a = parts[3] === undefined ? 1 : parts[3].endsWith('%') ? Number.parseFloat(parts[3]) / 100 : Number.parseFloat(parts[3]);
    return fromSrgb(ch(parts[0]), ch(parts[1]), ch(parts[2]), a);
  }
  m = /^color\(srgb\s+([^)]+)\)$/.exec(s);
  if (m) {
    const parts = m[1]
      .split(/[\s/]+/)
      .filter(Boolean)
      .map(Number.parseFloat);
    return fromSrgb(parts[0], parts[1], parts[2], parts[3] ?? 1);
  }
  m = /^oklch\(([^)]+)\)$/.exec(s);
  if (m) {
    const parts = m[1].split(/[\s/]+/).filter(Boolean);
    let L = Number.parseFloat(parts[0]);
    if (parts[0].endsWith('%')) L /= 100;
    const C = parts[1] === 'none' ? 0 : Number.parseFloat(parts[1]);
    const H = parts[2] === 'none' ? 0 : (Number.parseFloat(parts[2]) * Math.PI) / 180;
    let a = 1;
    if (parts[3] !== undefined) a = parts[3].endsWith('%') ? Number.parseFloat(parts[3]) / 100 : Number.parseFloat(parts[3]);
    const lab = oklabToLinear(L, C * Math.cos(H), C * Math.sin(H));
    return { ...lab, a, chroma: C };
  }
  return null;
}

function oklabToLinear(L, A, B) {
  const l_ = L + 0.396_337_777_4 * A + 0.215_803_757_3 * B;
  const m_ = L - 0.105_561_345_8 * A - 0.063_854_172_8 * B;
  const s_ = L - 0.089_484_177_5 * A - 1.291_485_548 * B;
  const l = l_ ** 3,
    m = m_ ** 3,
    s2 = s_ ** 3;
  return {
    r: clamp01(4.076_741_662_1 * l - 3.307_711_591_3 * m + 0.230_969_929_2 * s2),
    g: clamp01(-1.268_438_004_6 * l + 2.609_757_401_1 * m - 0.341_319_396_5 * s2),
    b: clamp01(-0.004_196_086_3 * l - 0.703_418_614_7 * m + 1.707_614_701 * s2),
  };
}

function oklchChroma(r, g, b) {
  const l = Math.cbrt(0.412_221_470_8 * r + 0.536_332_536_3 * g + 0.051_445_992_9 * b);
  const m = Math.cbrt(0.211_903_498_2 * r + 0.680_699_545_1 * g + 0.107_396_956_6 * b);
  const s = Math.cbrt(0.088_302_461_9 * r + 0.281_718_837_6 * g + 0.629_978_700_5 * b);
  const A = 1.977_998_495_1 * l - 2.428_592_205 * m + 0.450_593_709_9 * s;
  const B = 0.025_904_037_1 * l + 0.782_771_766_2 * m - 0.808_675_766 * s;
  return Math.hypot(A, B);
}

/** Composite a stack of fills (innermost first) over opaque white. */
function compositeStack(stack) {
  let out = { r: 1, g: 1, b: 1 };
  const layers = (stack || []).map(parseColour).filter(Boolean).toReversed();
  for (const c of layers) out = { r: c.r * c.a + out.r * (1 - c.a), g: c.g * c.a + out.g * (1 - c.a), b: c.b * c.a + out.b * (1 - c.a) };
  return out;
}

function luminance(c) {
  return 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
}

function contrastRatio(fg, ground) {
  const f = { r: fg.r * fg.a + ground.r * (1 - fg.a), g: fg.g * fg.a + ground.g * (1 - fg.a), b: fg.b * fg.a + ground.b * (1 - fg.a) };
  const [hi, lo] = [luminance(f), luminance(ground)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

/* ─────────────────────────────── text helpers ─────────────────────────────── */

const words = (s) => (s || '').split(/\s+/).filter((w) => /[\p{L}\p{N}]/u.test(w));
const normalise = (s) =>
  s
    .toLowerCase()
    .replaceAll(/\d[\d.,]*/g, '#')
    .replaceAll(/[^\p{L}#\s]/gu, ' ')
    .replaceAll(/\s+/g, ' ')
    .trim();
const sentencesOf = (s) =>
  (s || '')
    .split(/(?<=[.!?])\s+/)
    .map((x) => x.trim())
    .filter(Boolean);
const clausesOf = (s) =>
  (s || '')
    .split(/[.!?;·•|—–]|,\s/)
    .map((x) => x.trim())
    .filter(Boolean);

/* ─────────────────────────────── brief parsing ─────────────────────────────── */

/** Pull the ```json presentation-floor block out of a brief. Returns { floor } or { error }. */
function floorFromBrief(markdown) {
  const m = /```json\s+presentation-floor\s*\n([\s\S]*?)```/.exec(markdown || '');
  if (!m) return { error: 'the brief has no ```json presentation-floor block (Part 2b)' };
  try {
    return { floor: JSON.parse(m[1]) };
  } catch (error) {
    return { error: `the presentation-floor block is not valid JSON: ${error.message}` };
  }
}

/** Gate 1: is the brief's presentation floor complete enough to bind a designer and a checker? */
function validateBrief(markdown) {
  const findings = [];
  const add = (code, detail) => findings.push({ code, severity: 'hard', detail });
  if (!/##\s*Part 2b\b/.test(markdown || '')) add('B1', 'no "## Part 2b · The presentation floor" section');
  const { floor, error } = floorFromBrief(markdown);
  if (error) {
    add('B2', error);
    return { findings, floor: null };
  }
  if (floor.standard !== STANDARD) add('B2', `standard must be "${STANDARD}"`);
  const ts = floor.typeScale || {};
  const sizes = [];
  for (const r of ROLES) {
    const role = ts[r];
    if (!role || typeof role.size !== 'number' || typeof role.weight !== 'number' || !role.use) {
      add('B3', `type role "${r}" needs a numeric size, a numeric weight and a "use" sentence`);
    } else sizes.push([r, role.size]);
  }
  const seen = new Map();
  for (const [r, s] of sizes) {
    if (seen.has(s)) add('B3', `roles "${seen.get(s)}" and "${r}" share ${s}px — one size, one job`);
    else seen.set(s, r);
  }
  if (ts.answer && sizes.length === ROLES.length && sizes.some(([r, s]) => r !== 'answer' && s >= ts.answer.size))
    add('B3', 'the answer size must be larger than every other role size');
  if (ts.answer && ts.figure && ts.answer.weight < ts.figure.weight) add('B3', 'the answer must be at least as heavy as a figure');
  const sp = floor.spacing;
  if (!Array.isArray(sp) || sp.length < 3 || sp.some((v) => typeof v !== 'number' || v % 2 !== 0))
    add('B4', 'spacing must be a scale of at least three even pixel values');
  const colours = floor.colours;
  if (!Array.isArray(colours) || colours.length < 3 || colours.some((c) => !c.name || !c.value || !c.means || !parseColour(c.value)))
    add('B5', 'colours must be a list of at least three { name, value, means } with parseable values');
  const at = floor.attention || {};
  if (!at.top || !at.firstItem || !Array.isArray(at.provenance) || !['footer', 'disclosure'].includes(at.provenanceTo))
    add('B6', 'attention needs "top", "firstItem", a "provenance" list and provenanceTo footer|disclosure');
  const lp = floor.layout || {};
  if (
    lp.summaryFirst !== true ||
    !['cards', 'groups'].includes(lp.items) ||
    typeof lp.atRestFields !== 'number' ||
    lp.detailOnOpen !== true
  )
    add('B7', 'layout needs summaryFirst:true, items cards|groups, a numeric atRestFields and detailOnOpen:true');
  const banned = floor.banned || [];
  for (const k of BANNED_KEYS) if (!banned.includes(k)) add('B8', `banned list is missing "${k}"`);
  const vp = floor.viewport || {};
  if (vp.width !== 1440 || vp.height !== 900) add('B9', 'viewport must be 1440×900');
  const cites = floor.citations || [];
  for (const c of REQUIRED_CITATIONS) {
    const hit = cites.find((x) => x.id === c.id);
    if (!hit || !String(hit.path || '').includes(c.path) || !hit.rule)
      add('B10', `citation "${c.id}" missing, or its path does not name ${c.path}, or it carries no rule`);
  }
  // A {placeholder} left anywhere in Part 2b is an unrendered template, not a specification.
  const part = /##\s*Part 2b\b[\s\S]*?(?=\n## (?!#))/.exec(markdown || '');
  if (part && /\{[a-z_]+[^}]*\}/i.test(part[0].replaceAll(/```json[\s\S]*?```/g, '')))
    add('B11', 'Part 2b still carries an unrendered {placeholder}');
  return { findings, floor };
}

/* ─────────────────────────────── page checks ─────────────────────────────── */

function checkSnapshot(snapshot, floor) {
  const results = [];
  const budgets = { ...DEFAULT_BUDGETS, ...floor.budgets };
  const put = (id, name, status, detail, evidence = []) => results.push({ id, name, status, detail, evidence });
  const texts = (snapshot && snapshot.texts) || [];
  const blocks = (snapshot && snapshot.blocks) || [];
  const answer = snapshot && snapshot.answer;
  const first = snapshot && snapshot.firstItem;
  const ts = floor.typeScale || {};
  const visible = texts.filter((t) => words(t.text).length > 0);

  if (visible.length === 0) {
    for (const [id, name] of [
      ['R1', 'type-tokens'],
      ['R2', 'answer-heaviest'],
      ['R6', 'headline-figure'],
      ['R7', 'prose-above-item'],
      ['R8', 'repeated-sentence'],
      ['R9', 'contrast'],
      ['R10', 'all-caps'],
      ['R11', 'above-the-fold'],
    ])
      put(id, name, 'unchecked', 'the snapshot carries no text — a check over nothing has not passed');
  }

  // R1 — type tokens, one size one job
  if (visible.length > 0) {
    const declared = ROLES.map((r) => ts[r]?.size).filter((x) => typeof x === 'number');
    if (declared.length === 0) put('R1', 'type-tokens', 'unchecked', 'the floor declares no type scale');
    else {
      const off = visible.filter((t) => !declared.some((d) => Math.abs(d - t.fontSize) <= SIZE_TOLERANCE_PX));
      const reuse =
        ts.answer && typeof ts.answer.size === 'number'
          ? visible.filter((t) => !t.inAnswer && Math.abs(t.fontSize - ts.answer.size) <= SIZE_TOLERANCE_PX)
          : [];
      const miss =
        ts.answer && typeof ts.answer.size === 'number'
          ? visible.filter((t) => t.inAnswer && Math.abs(t.fontSize - ts.answer.size) > SIZE_TOLERANCE_PX)
          : [];
      const sizes = [...new Set(off.map((t) => t.fontSize))].sort((a, b) => a - b);
      if (off.length > 0 || reuse.length > 0 || miss.length > 0) {
        const parts = [];
        if (off.length > 0)
          parts.push(`${off.length} element(s) at undeclared size(s) ${sizes.join(', ')}px (declared: ${declared.join(', ')}px)`);
        if (reuse.length > 0) parts.push(`${reuse.length} element(s) outside the answer use the answer size ${ts.answer.size}px`);
        if (miss.length > 0) parts.push(`the answer is set at ${miss[0].fontSize}px, not the answer role's ${ts.answer.size}px`);
        put(
          'R1',
          'type-tokens',
          'fail',
          parts.join('; '),
          [...miss, ...off, ...reuse].slice(0, 5).map((t) => `${t.fontSize}px "${t.text.slice(0, 60)}"`),
        );
      } else put('R1', 'type-tokens', 'pass', `${visible.length} text elements, all on the ${declared.length}-size scale`);
    }
  }

  // R2 — answer visually heavier than evidence
  if (visible.length > 0) {
    if (answer) {
      const a = visible.filter((t) => t.inAnswer);
      const aSize = Math.max(...a.map((t) => t.fontSize), 0);
      const rivals = visible.filter((t) => !t.inAnswer && t.fontSize >= aSize - SIZE_TOLERANCE_PX);
      if (a.length === 0) put('R2', 'answer-heaviest', 'unchecked', 'the [data-answer] element carries no visible text');
      else if (rivals.length > 0)
        put(
          'R2',
          'answer-heaviest',
          'fail',
          `${rivals.length} element(s) are set as large as the answer (${aSize}px) — the eye cannot tell the answer from the evidence`,
          rivals.slice(0, 5).map((t) => `${t.fontSize}px/${t.fontWeight} "${t.text.slice(0, 60)}"`),
        );
      else put('R2', 'answer-heaviest', 'pass', `the answer (${aSize}px) is the largest text on the surface`);
    } else {
      put('R2', 'answer-heaviest', 'unchecked', 'no element marked [data-answer] — cannot tell the answer from the evidence');
    }
  }

  // R3 / R4 / R5 — blocks
  const pageGround = parseColour(snapshot && snapshot.pageBackground) || { r: 1, g: 1, b: 1, a: 1, chroma: 0 };
  const tinted = [],
    bordered = [],
    stripes = [];
  for (const b of blocks) {
    const nWords = b.words ?? 0;
    const fill = parseColour(b.background);
    const sides = ['top', 'right', 'bottom', 'left'].map((k) => {
      const s = (b.border && b.border[k]) || {};
      const c = parseColour(s.color);
      return { k, width: s.width || 0, visible: (s.width || 0) >= 1 && s.style !== 'none' && c && c.a > 0, colour: c, raw: s.color };
    });
    const shown = sides.filter((s) => s.visible);
    // The tint is judged on the fill as the reader sees it: composited over the page ground.
    let seen = null;
    if (fill && fill.a > 0) {
      const g = pageGround;
      seen = oklchChroma(fill.r * fill.a + g.r * (1 - fill.a), fill.g * fill.a + g.g * (1 - fill.a), fill.b * fill.a + g.b * (1 - fill.a));
    }
    const isTint = seen !== null && seen >= CHROMA_TINT && Math.abs(seen - pageGround.chroma) >= CHROMA_TINT;
    if (isTint && nWords >= MIN_BLOCK_WORDS && !b.item && !b.control) tinted.push(b);
    if (shown.length === 4 && nWords >= MIN_BLOCK_WORDS && !b.item && !b.control) bordered.push(b);
    // A stripe: one of left / top / right drawn at 2px or more in a colour, or in a colour the other
    // edges do not share. A bottom rule is a divider, and a control's underline is a tab indicator.
    if (!b.control) {
      const edge = shown.find(
        (s) =>
          s.k !== 'bottom' &&
          s.width >= 2 &&
          shown.filter((o) => o !== s).every((o) => o.width * 2 <= s.width || o.raw !== s.raw) &&
          (s.colour.chroma >= CHROMA_TINT || shown.some((o) => o !== s && o.raw !== s.raw)),
      );
      if (edge) stripes.push(b);
    }
  }
  const show = (b) => `${b.tag}${b.cls ? '.' + b.cls : ''} "${(b.text || '').slice(0, 70)}"`;
  put(
    'R3',
    'tinted-callout',
    tinted.length > 0 ? 'fail' : 'pass',
    tinted.length > 0 ? `${tinted.length} block(s) of prose on a tinted fill — the notice-box pattern` : 'no prose sits on a tinted fill',
    tinted.map(show),
  );
  put(
    'R4',
    'bordered-budget',
    bordered.length > budgets.borderedAllowed ? 'fail' : 'pass',
    `${bordered.length} all-round bordered prose block(s) outside declared items; budget ${budgets.borderedAllowed}`,
    bordered.map(show),
  );
  put(
    'R5',
    'edge-stripe',
    stripes.length > 0 ? 'fail' : 'pass',
    stripes.length > 0 ? `${stripes.length} block(s) carry a coloured stripe on one edge` : 'no edge stripes',
    stripes.map(show),
  );

  if (visible.length > 0) {
    // R6 — headline within N words of a figure (the answer, then whatever follows it in reading order)
    if (answer) {
      const ordered = [...visible].sort((x, y) => (x.order ?? 0) - (y.order ?? 0));
      const startIdx = ordered.findIndex((t) => t.inAnswer);
      const run = ordered.slice(Math.max(startIdx, 0)).flatMap((t) => words(t.text));
      const at = run.findIndex((w) => /\d/.test(w));
      const n = at === -1 ? Infinity : at;
      put(
        'R6',
        'headline-figure',
        n > budgets.wordsToFigure ? 'fail' : 'pass',
        n === Infinity
          ? 'no figure follows the answer at all'
          : `${n} word(s) from the start of the answer to its first figure; budget ${budgets.wordsToFigure}`,
      );
    } else put('R6', 'headline-figure', 'unchecked', 'no element marked [data-answer]');

    // R7 — prose above the first actionable item
    if (first) {
      const above = visible.filter((t) => t.bottom <= first.top + 1 && !t.control);
      const n = above.reduce((acc, t) => acc + words(t.text).length, 0);
      put(
        'R7',
        'prose-above-item',
        n > budgets.proseAboveFirstItem ? 'fail' : 'pass',
        `${n} word(s) above the first item; budget ${budgets.proseAboveFirstItem}`,
      );
    } else put('R7', 'prose-above-item', 'unchecked', 'no element marked [data-first-item]');

    // R8 — repeated sentences, and a clause repeated down the items
    const sentenceCount = new Map();
    for (const t of visible)
      for (const s of sentencesOf(t.text)) {
        if (s.length < MIN_SENTENCE_CHARS) continue;
        // Literal, as artifact-policy-check.ts does: a sentence with a different number in it is a
        // different fact (a 30-day basis beside a 90-day one). Numbers are normalised only for
        // CLAUSES below, where the same wording down every row is the ledger pattern itself.
        const k = s
          .toLowerCase()
          .replaceAll(/\s+/g, ' ')
          .replace(/[.!?]+$/, '');
        const e = sentenceCount.get(k) || { n: 0, sample: s };
        e.n += 1;
        sentenceCount.set(k, e);
      }
    const clauseEls = new Map();
    for (const t of visible) {
      if (t.control) continue;
      for (const c of new Set(clausesOf(t.text).map(normalise))) {
        if (c.split(' ').filter((w) => /\p{L}/u.test(w)).length < 3) continue;
        clauseEls.set(c, (clauseEls.get(c) || 0) + 1);
      }
    }
    const dupS = [...sentenceCount.values()].filter((e) => e.n > 1);
    const dupC = [...clauseEls.entries()].filter(([, n]) => n > budgets.repeatedClauseMax);
    const ev = [...dupS.map((e) => `×${e.n} "${e.sample.slice(0, 70)}"`), ...dupC.map(([c, n]) => `×${n} clause "${c.slice(0, 70)}"`)];
    put(
      'R8',
      'repeated-sentence',
      ev.length > 0 ? 'fail' : 'pass',
      ev.length > 0
        ? `${dupS.length} sentence(s) said more than once, ${dupC.length} clause(s) repeated in more than ${budgets.repeatedClauseMax} places`
        : 'nothing said twice',
      ev,
    );

    // R9 — WCAG contrast
    const low = [],
      unread = [];
    for (const t of visible) {
      const fg = parseColour(t.color);
      if (!fg) {
        unread.push(t);
        continue;
      }
      const ground = compositeStack(t.bgStack && t.bgStack.length > 0 ? t.bgStack : [snapshot.pageBackground]);
      const ratio = contrastRatio(fg, ground);
      const large = t.fontSize >= 24 || (t.fontSize >= 18.66 && t.fontWeight >= 700);
      const min = large ? budgets.contrastLargeMin : budgets.contrastMin;
      if (ratio + 1e-9 < min) low.push(`${ratio.toFixed(2)}:1 < ${min}:1 ${t.color} "${t.text.slice(0, 50)}"`);
    }
    if (low.length > 0) put('R9', 'contrast', 'fail', `${low.length} element(s) under WCAG AA`, low.slice(0, 8));
    else if (unread.length > 0)
      put(
        'R9',
        'contrast',
        'unchecked',
        `${unread.length} text colour(s) could not be parsed`,
        unread.slice(0, 5).map((t) => t.color),
      );
    else put('R9', 'contrast', 'pass', `${visible.length} text colours meet AA`);

    // R10 — all caps
    const caps = [];
    for (const t of visible) {
      if (t.textTransform === 'uppercase' && /\p{L}/u.test(t.text)) {
        caps.push(`text-transform:uppercase "${t.text.slice(0, 50)}"`);
        continue;
      }
      for (const w of t.text.split(/[\s/·—–-]+/)) {
        const letters = w.replaceAll(/[^\p{L}]/gu, '');
        if (
          letters.length >= 3 &&
          letters === letters.toUpperCase() &&
          letters !== letters.toLowerCase() &&
          !/\d/.test(w) &&
          !ACRONYMS.has(letters)
        )
          caps.push(`"${w}" in "${t.text.slice(0, 50)}"`);
      }
    }
    put(
      'R10',
      'all-caps',
      caps.length > 0 ? 'fail' : 'pass',
      caps.length > 0 ? `${caps.length} shouted run(s)` : 'no all-caps text',
      caps.slice(0, 8),
    );
  }

  // R11 — first item above the fold at the declared viewport
  const vp = floor.viewport || { width: 1440, height: 900 };
  const svp = (snapshot && snapshot.viewport) || {};
  if (svp.width !== vp.width || svp.height !== vp.height)
    put('R11', 'above-the-fold', 'unchecked', `snapshot taken at ${svp.width}×${svp.height}, the floor declares ${vp.width}×${vp.height}`);
  else if (first) {
    const limit = Math.round(vp.height * budgets.headerMaxFraction);
    const problems = [];
    if (first.bottom > vp.height) problems.push(`the first item ends at y=${first.bottom}, below the ${vp.height}px fold`);
    if (first.top > limit)
      problems.push(
        `the first item starts at y=${first.top} (${Math.round((first.top / vp.height) * 100)}% down); the header may take ${limit}px`,
      );
    put(
      'R11',
      'above-the-fold',
      problems.length > 0 ? 'fail' : 'pass',
      problems.length > 0 ? problems.join('; ') : `first item at y=${first.top}–${first.bottom}`,
    );
  } else {
    put('R11', 'above-the-fold', 'unchecked', 'no element marked [data-first-item]');
  }

  results.sort((x, y) => Number(x.id.slice(1)) - Number(y.id.slice(1)));
  return results;
}

/* ─────────────────────────── the browser-side probe ─────────────────────────── */

/**
 * Runs IN the page (Playwright page.evaluate, or pasted into a console / Claude-in-Chrome javascript
 * tool). It returns the snapshot this checker reads. It reads computed style only — never source.
 * Markers the brief requires the page to carry: [data-answer], [data-first-item], [data-item] on each
 * item card or group, optional [data-page] as the scope (else <main>, else <body>).
 */
function probe(opts) {
  const o = opts || {};
  const scope = document.querySelector(o.scope || '[data-page]') || document.querySelector('main') || document.body;
  const answerEl = scope.querySelector(o.answer || '[data-answer]');
  const firstEl = scope.querySelector(o.firstItem || '[data-first-item]');
  const isControl = (el) => !!el.closest('button, a[role=button], input, select, textarea, [role=button], [role=tab]');
  const shown = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || Number(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const bgStack = (el) => {
    const out = [];
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const bg = getComputedStyle(n).backgroundColor;
      if (bg && bg !== 'transparent' && !/rgba\([^)]*,\s*0\)$/.test(bg)) out.push(bg);
    }
    return out;
  };
  const rect = (el) => {
    const r = el.getBoundingClientRect();
    return {
      top: Math.round(r.top + scrollY),
      bottom: Math.round(r.bottom + scrollY),
      left: Math.round(r.left),
      width: Math.round(r.width),
      height: Math.round(r.height),
    };
  };
  // innerText, not textContent: the checker must read what is RENDERED (hidden text excluded).
  // eslint-disable-next-line unicorn/prefer-dom-node-text-content
  const rendered = (el) => (el.innerText || '').replaceAll(/\s+/g, ' ').trim();
  const texts = [];
  let order = 0;
  for (const el of scope.querySelectorAll('*')) {
    if (!shown(el) || ['SCRIPT', 'STYLE', 'NOSCRIPT', 'SVG', 'svg'].includes(el.tagName)) continue;
    const own = [...el.childNodes]
      .filter((n) => n.nodeType === 3)
      .map((n) => n.textContent)
      .join(' ')
      .replaceAll(/\s+/g, ' ')
      .trim();
    if (!own) continue;
    const cs = getComputedStyle(el);
    texts.push({
      order: order++,
      tag: el.tagName.toLowerCase(),
      text: own,
      fontSize: Number.parseFloat(cs.fontSize),
      fontWeight: Number.parseInt(cs.fontWeight, 10),
      fontFamily: cs.fontFamily,
      color: cs.color,
      textTransform: cs.textTransform,
      bgStack: bgStack(el),
      inAnswer: !!(answerEl && answerEl.contains(el)),
      control: isControl(el),
      ...rect(el),
    });
  }
  const blocks = [];
  for (const el of scope.querySelectorAll('*')) {
    if (!shown(el)) continue;
    const cs = getComputedStyle(el);
    const side = (k) => ({ width: Number.parseFloat(cs[`border${k}Width`]), style: cs[`border${k}Style`], color: cs[`border${k}Color`] });
    const border = { top: side('Top'), right: side('Right'), bottom: side('Bottom'), left: side('Left') };
    const hasBorder = Object.values(border).some((s) => s.width >= 1 && s.style !== 'none');
    const bg = cs.backgroundColor;
    const hasFill = bg && bg !== 'transparent' && !/rgba\([^)]*,\s*0\)$/.test(bg);
    if (!hasBorder && !hasFill) continue;
    if (['TABLE', 'THEAD', 'TBODY', 'TR', 'TD', 'TH', 'HR'].includes(el.tagName)) continue;
    const text = rendered(el);
    blocks.push({
      tag: el.tagName.toLowerCase(),
      cls: (typeof el.className === 'string' ? el.className : '').split(/\s+/)[0] || '',
      text,
      words: text.split(/\s+/).filter(Boolean).length,
      background: bg,
      border,
      item: !!el.closest('[data-item]') && el.closest('[data-item]') === el,
      control: isControl(el),
      ...rect(el),
    });
  }
  return {
    schema: 'rendered-page-snapshot/1',
    url: location.href,
    capturedAt: new Date().toISOString(),
    theme: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light',
    viewport: { width: innerWidth, height: innerHeight },
    pageBackground: bgStack(scope)[0] || getComputedStyle(document.body).backgroundColor || 'rgb(255, 255, 255)',
    answer: answerEl ? { text: rendered(answerEl), ...rect(answerEl) } : null,
    firstItem: firstEl ? { text: rendered(firstEl).slice(0, 200), ...rect(firstEl) } : null,
    texts,
    blocks,
  };
}

async function snapshotFromUrl(url, floor, theme) {
  let playwright;
  try {
    // Resolved from the PROJECT (or NODE_PATH), never from the fork: the fork does not ship a browser.
    const browserModule = 'playwright';
    const where = require.resolve(browserModule, { paths: [process.cwd(), ...(process.env.NODE_PATH || '').split(':').filter(Boolean)] });
    playwright = require(where);
  } catch {
    return {
      error:
        'playwright is not resolvable from this directory, so the page could not be rendered here. Capture a snapshot instead: ' +
        'run the output of `--print-probe` in the page (console or Claude-in-Chrome) at 1440×900, save the JSON, and pass --snapshot. ' +
        'This is UNCHECKED, not passed.',
    };
  }
  const vp = floor.viewport || { width: 1440, height: 900 };
  const browser = await playwright.chromium.launch();
  try {
    const page = await browser.newPage({ viewport: vp, colorScheme: theme === 'dark' ? 'dark' : 'light' });
    await page.goto(url, { waitUntil: 'networkidle' });
    return { snapshot: await page.evaluate(probe, floor.selectors || {}) };
  } finally {
    await browser.close();
  }
}

/* ─────────────────────────────────── CLI ────────────────────────────────── */

function report(results, json) {
  const fails = results.filter((r) => r.status === 'fail');
  const unchecked = results.filter((r) => r.status === 'unchecked');
  if (json) console.log(JSON.stringify({ fails: fails.length, unchecked: unchecked.length, results }, null, 2));
  else {
    console.log(`rendered-page: ${results.length} checks, ${fails.length} failed, ${unchecked.length} could not run.`);
    for (const r of results) {
      console.log(`  ${{ pass: '✓', fail: '✗', unchecked: '?' }[r.status]} ${r.id} ${r.name}: ${r.detail}`);
      for (const e of r.evidence || []) console.log(`      · ${e}`);
    }
  }
  if (fails.length > 0) return 1;
  return unchecked.length > 0 ? 2 : 0;
}

async function main(argv) {
  const arg = (k) => {
    const i = argv.indexOf(k);
    return i === -1 ? undefined : argv[i + 1];
  };
  const json = argv.includes('--json');
  if (argv.includes('--print-probe')) {
    console.log(`(${probe.toString()})({})`);
    return 0;
  }
  if (arg('--validate-brief')) {
    const { findings } = validateBrief(fs.readFileSync(arg('--validate-brief'), 'utf8'));
    if (json) console.log(JSON.stringify({ hard: findings.length, findings }, null, 2));
    else {
      console.log(`presentation-floor brief check: ${findings.length} hard finding(s).`);
      for (const f of findings) console.log(`  ✗ ${f.code} ${f.detail}`);
    }
    return findings.length > 0 ? 1 : 0;
  }
  let floor;
  if (arg('--brief')) {
    const got = floorFromBrief(fs.readFileSync(arg('--brief'), 'utf8'));
    if (got.error) {
      console.error(`check-rendered-page: ${got.error}`);
      return 2;
    }
    floor = got.floor;
  } else if (arg('--floor')) floor = JSON.parse(fs.readFileSync(arg('--floor'), 'utf8'));
  else {
    console.error(
      'usage: check-rendered-page.js (--snapshot <json> | --url <url>) (--brief <brief.md> | --floor <json>) [--theme dark] [--json]',
    );
    console.error('       check-rendered-page.js --validate-brief <brief.md> [--json] | --print-probe');
    return 2;
  }
  let snapshot;
  if (arg('--snapshot')) snapshot = JSON.parse(fs.readFileSync(arg('--snapshot'), 'utf8'));
  else if (arg('--url')) {
    const got = await snapshotFromUrl(arg('--url'), floor, arg('--theme'));
    if (got.error) {
      console.error(`check-rendered-page: ${got.error}`);
      return 2;
    }
    snapshot = got.snapshot;
  } else {
    console.error('check-rendered-page: give --snapshot <json> or --url <url>');
    return 2;
  }
  return report(checkSnapshot(snapshot, floor), json);
}

if (require.main === module) {
  main(process.argv.slice(2)).then(
    (code) => process.exit(code),
    (error) => {
      console.error(`check-rendered-page: ${error.stack || error.message}`);
      process.exit(2);
    },
  );
}

module.exports = {
  checkSnapshot,
  validateBrief,
  floorFromBrief,
  parseColour,
  contrastRatio,
  compositeStack,
  probe,
  STANDARD,
  ROLES,
  BANNED_KEYS,
  REQUIRED_CITATIONS,
  DEFAULT_BUDGETS,
};
