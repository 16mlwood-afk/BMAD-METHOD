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
 *   R12 prose-wall         nowhere on the page, above or below the fold, do more than 2 paragraphs run
 *                          back to back, and no paragraph is longer than maxParagraphWords (default 40)
 *   R13 section-form       every section the brief declares carries its declared form at rest: within its
 *                          word budget; rows are short labelled rows; held, provenance, method, skipped and
 *                          message sections are collapsed behind a disclosure with a one-line summary
 *   R14 footer-at-rest     the footer shows at most footerLinesAtRest (default 2) lines at rest; the rest
 *                          sits behind a disclosure
 *   R15 row-cells          in a label/value row group ([data-row-group]): one value cell and at most one
 *                          status per row, no cell repeating another cell of its row, a value of money, a
 *                          count or at most 4 words, an explanation of at most 12 words
 *   R16 row-grid           the value cells share one right edge and the status cells one left edge, values
 *                          are right-aligned in tabular numerals, and rows sit further apart than the
 *                          spacing inside a row
 *   R17 internal-words     no pipeline vocabulary (export, handoff, pipeline, record, run by default) in a
 *                          row group
 *   R18 row-total          a group with an unpriced row carries a total labelled as partial
 *   R19 inline-provenance  no provenance caption in the body ("Named from…", "Known because…", "· the
 *                          supplier's list", "as listed by…", "found by…"): provenance goes to the footer
 *                          or a closed disclosure (amazon-removal-assistant docs/artifact-policy.md §2, §4)
 *
 * ── Declared exemptions (presentation-floor.md §11, gap G12) — never global, always visible ──
 *   quotedSources   text inside [data-source="<source>"] is the source's own words, verbatim: exempt from
 *                   the checks the brief names for that source (R8, R10, R17, R19 only). An undeclared
 *                   source exempts nothing, and the answer is never exempt.
 *   exemptions      R6 for a named view whose answer has no figure by design; R8 for a sentence said once
 *                   in each of at most `max` different items (two products that share a name).
 *   internalWordExceptions  an exact phrase where an internal word carries its ordinary meaning.
 *   Every exemption used is printed in the check's detail; a check it clears reports "exempt", not "pass".
 *
 * ── Gate 1 (--validate-brief) ──
 *   B1–B11  the floor itself is specified (Part 2b and its machine block)
 *   B12–B20 brief completeness, presentation-floor.md §8: ranked-list evidence tiers, truncation's
 *           must-survive token, say-once inside the Copy deck, self-contained, states × views,
 *           responsive widths, action feedback, 15% word headroom, notation not literal. Each is a
 *           gap Claude Design found in a brief that had passed B1–B11 (shared/brief-gap-ledger.md).
 *   B21     every section of the page has a declared visual form and word budget (presentation-floor.md
 *           §9, gap G10): the below-the-fold prose wall of the price-list v6 design.
 *   B23     every exemption is declared, narrow and argued: known checks only, a reason, a view or a cap
 *   B24     the brief keeps its own budgets: each section's `sample` (its at-rest strings, found verbatim in
 *           the brief) fits its wordBudget (gap G13: the journey's own content was 96 words against 90)
 *   B22     every label/value row group is specified as one (presentation-floor.md §10, gap G11): its
 *           columns, value and explanation word caps, right-aligned tabular values, row gap larger than
 *           the gap inside a row, its total (partial and labelled so, or none with a reason), and the
 *           internal words it may not show.
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
 *        [signed in: --auth-header-env VAR [--auth-header-name NAME] [--auth-drop-header NAME]
 *                    [--auth-session-marker KEY] [--auth-storage-env KEY=VAR]]
 *        (needs `playwright` resolvable from the current directory, NODE_PATH or --playwright <dir>;
 *        otherwise exit 2 with the install command)
 *
 * ── Signed in (friction WF-20260928-085) ──
 *   A protected app renders its sign-in form to a stranger, and the checks then grade the form. The
 *   credential is only ever read from an ENVIRONMENT VARIABLE named on the command line, never from a
 *   literal, is sent only to the page's own origin, only over https or to localhost, and never printed.
 *     --auth-header-env VAR       send the value of $VAR as a request header on same-origin requests
 *     --auth-header-name NAME     that header's name (default Authorization; e.g. X-API-Key)
 *     --auth-drop-header NAME     remove this header from same-origin requests (an app's placeholder
 *                                 session header must not reach the server beside the real one)
 *     --auth-session-marker KEY   put a non-secret placeholder in localStorage KEY before the app starts,
 *                                 for an app that shows its sign-in form while that key is empty
 *     --auth-storage-env KEY=VAR  put the value of $VAR in localStorage KEY (a real session token)
 *   A page that still renders a password field and no [data-answer] is reported as UNCHECKED — the
 *   sign-in form is never graded as the page.
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
  // §9 (G10) — below the fold is not a place for running prose. The v6 price-list design ran six
  // paragraphs back to back under "Before you order", and a six-line provenance footer.
  maxConsecutiveParagraphs: 2,
  maxParagraphWords: 40,
  footerLinesAtRest: 2,
  sectionWordsMax: 60, // at rest, for any section that is not the items themselves
  summaryMaxWords: 12, // the one line a collapsed section shows at rest
  rowMaxWords: 12, // a labelled row: the label, then at most this many words
  maxRows: 5,
  // §10 (G11) — a label/value row group. The price-list drawer's journey section, bundle 6: a status
  // column repeating the value, statuses at a different x on every row, sentences in the value
  // column, two-line notes, pipeline words and no labelled total.
  valueMaxWords: 4,
  noteMaxWords: 12,
  gridTolerancePx: 2,
  maxFactRows: 10,
};
/** §10: words that name our own machinery, never shown in a row group. The owner's list, 2026-09-28. */
const DEFAULT_INTERNAL_WORDS = ['export', 'handoff', 'pipeline', 'record', 'run'];
/** A value that says no figure exists yet. A group holding one owes a total labelled as partial. */
// "open" was here and matched the control "Open WhatsApp": an ordinary word is not a missing figure.
const UNPRICED_VALUE = /\b(not priced|not quoted|unknown|not known|no figure)\b/i;
/**
 * §11 (G12): the checks a quoted source may be exempted from, and the checks a declared exemption may
 * clear. Everything else can never be exempted: a floor a brief could switch off is not a floor.
 */
const QUOTABLE_CHECKS = new Set(['R8', 'R10', 'R17', 'R19']);
const EXEMPTABLE_CHECKS = new Set(['R6', 'R8']);
const MAX_ACROSS_ITEMS = 3;
/**
 * R19: provenance written into the body. Each is a caption the owner rejected in the live drawer of
 * 2026-09-28, or its plain variant. A brief may add its own in `provenancePhrases`.
 */
const DEFAULT_PROVENANCE = [
  String.raw`\bnamed from\b`,
  String.raw`\bknown because\b`,
  String.raw`\bas listed by\b`,
  String.raw`\bfound by\b`,
  String.raw`\baccording to\b`,
  String.raw`\b(?:taken|sourced|read) from\b`,
  String.raw`[·•,]\s*the supplier[’']s (?:price-)?list\b`,
];
/** The words that label a total as partial. */
const PARTIAL_LABEL = /\b(partial|so far|priced only|not the full|incomplete|of the known)\b/i;
/** §9: the forms a section may take, and the kinds that must be collapsed at rest. */
const SECTION_FORMS = ['cards', 'rows', 'disclosure', 'message-block', 'value-rows'];
const SECTION_KINDS = ['items', 'caveats', 'facts', 'held', 'provenance', 'method', 'skipped', 'message', 'footer', 'other'];
const COLLAPSED_KINDS = new Set(['held', 'provenance', 'method', 'skipped', 'message', 'footer']);
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
  for (const f of completenessFindings(markdown, floor)) add(f.code, f.detail);
  return { findings, floor };
}

/* ───────────────────── brief completeness (B12–B20, the gap ledger) ───────────────────── */
/*
 * Each of these is a class of gap Claude Design found in a brief that had passed B1–B11 — the
 * price-list v4 brief of 2026-09-27. The ledger that records them, and every gap found since, is
 * custom/workflows/design/shared/brief-gap-ledger.md; the rule each enforces is
 * presentation-floor.md §8. A trigger (a ranked list, a truncated field, an action) is read from the
 * brief's prose; the specification it demands is read from the machine block, so a brief cannot pass
 * by containing the right words in the wrong place.
 */

/** Prose the triggers read: the brief without its fenced blocks (the machine copy is not prose). */
const proseOf = (markdown) => (markdown || '').replaceAll(/```[\s\S]*?```/g, (m) => m.replaceAll(/[^\n]/g, ''));
const TRIGGER_RANKED =
  /\b(ranked|ranking|ranks? by|sorted by|sorts? by|ordered by|highest first|lowest first|largest first|smallest first|biggest first|newest first|oldest first|most first)\b/i;
const TRIGGER_TRUNCATION = /\b(ellips[ie]s|truncat\w*|line[- ]clamp\w*|clamped to|cut off at)\b/i;
const TRIGGER_ACTION = /\b(toast|snackbar|button|copy control|copies|copied|save|saves|submit|send|delete|undo|confirm)\b/i;
const TRIGGER_DRAWER = /\b(drawer|side sheet|side panel|slide-over)\b/i;
/** "Keep X as it is" hands the designer a view the brief does not contain. */
const AS_IT_IS = /\bas (?:it|they) (?:is|are)\b(?=\s*(?:[,.;:|)\]—–]|$|re-set))/im;
/** A pointer to another brief in place of the content. "Do not design from the earlier brief" is not one. */
const OTHER_BRIEF =
  /\b(?:see|refer to|per|as in|same as in|carried forward(?: unchanged)? from|unchanged from|taken from|copied from|kept from|reuse)\s+(?:the |any |an )?(?:older|previous|earlier|prior|landed|last|original|old|v\d+)\s+(?:version of (?:the |this )?)?brief\b/i;
/** A deck cell that is an instruction or a pointer, not the words the surface ships. */
const DECK_PLACEHOLDER =
  /^\s*(?:|—|-|tbd|todo|tba|\?+|\.\.\.|…)\s*$|^\s*\(.*\)\s*$|carried forward|unchanged from|as before\b|same as (?:the )?(?:current|live|landed|previous|earlier|older|existing)\b|\{(?:for|if|endfor|endif)\b|\{s\./i;
/**
 * Where-cells the say-once screen skips: strings not at rest (said on an event, or never shown), and
 * controls, whose label may echo the thing they act on — R8 on the rendered page skips controls too.
 */
// "on open": text inside a disclosure that is closed at rest (presentation-floor.md §9) is not at rest.
const NOT_AT_REST = /toast|snackbar|hover|tooltip|screen reader|aria|alt text|title attribute|\bcontrols?\b|\bbutton|\blink\b|\bon open\b/i;
const STOP = new Set(
  'a an the and or but of to in on at for by with from as is are was were be been it its this that these those there their they them you your we our not no nothing so if then than into onto up out yet'.split(
    ' ',
  ),
);
const PHRASE_WORDS = 4;
const HEADROOM = 0.85;
const NARROW_MAX = 1024;

/** The phrases said in more than one at-rest deck string (different slots). Exported for the tests. */
function deckRepeats(markdown, exceptions = []) {
  let parseDeck;
  try {
    ({ parseDeck } = require('./check-copy-screen.js'));
  } catch {
    return { error: 'tools/check-copy-screen.js is not beside this checker, so the Copy deck could not be read' };
  }
  const deck = parseDeck(markdown || '');
  if (!deck || !deck.header || deck.rows.length === 0) return { error: 'no Copy deck table to screen for repeats' };
  const col = (names) => deck.header.findIndex((h) => names.some((n) => h.includes(n)));
  const where = col(['where']);
  const ships = col(['ships as', 'replacement']);
  if (ships === -1) return { error: 'the Copy deck has no "Ships as" column' };
  const allowed = exceptions.map((e) => normalise(String(e.phrase || '')));
  const grams = new Map();
  const rows = [];
  for (const r of deck.rows) {
    const w = where === -1 ? '' : r.cells[where] || '';
    if (NOT_AT_REST.test(w)) continue;
    // A slot is one place on the surface; its rows are alternatives never shown together.
    const slot = w.split(',')[0].trim().toLowerCase() || `row ${r.cells[0]}`;
    const text = (r.cells[ships] || '').replaceAll(/\{[^}]*\}/g, ' ');
    rows.push({ n: r.cells[0], slot, text });
    // An argued exception is blanked out of every string before the rest is screened.
    let screened = ` ${normalise(text)} `;
    for (const a of allowed) if (a) screened = screened.replaceAll(` ${a} `, ' | ');
    const tokens = screened.split(' ').filter((x) => x && x !== '#');
    const seen = new Set();
    for (let i = 0; i + PHRASE_WORDS <= tokens.length; i++) {
      const g = tokens.slice(i, i + PHRASE_WORDS);
      if (g.includes('|')) continue;
      if (g.filter((x) => !STOP.has(x) && x.length > 2).length < 2) continue;
      const key = g.join(' ');
      if (seen.has(key)) continue;
      seen.add(key);
      const e = grams.get(key) || [];
      e.push({ n: r.cells[0], slot });
      grams.set(key, e);
    }
  }
  const repeats = [];
  for (const [phrase, at] of grams) {
    if (new Set(at.map((x) => x.slot)).size < 2) continue;
    repeats.push({ phrase, rows: at.map((x) => x.n) });
  }
  // Overlapping windows of one repeated run are one finding, not five.
  const merged = [];
  for (const r of repeats) {
    const same = merged.find((m) => m.rows.join(',') === r.rows.join(','));
    if (same) same.phrases.push(r.phrase);
    else merged.push({ rows: r.rows, phrases: [r.phrase] });
  }
  return { repeats: merged, atRest: rows.length };
}

function completenessFindings(markdown, floor) {
  const out = [];
  const add = (code, detail) => out.push({ code, detail });
  const prose = proseOf(markdown);
  const f = floor || {};
  const text = (v) => typeof v === 'string' && v.trim().length > 0;

  // B12 — a ranked list declares evidence-strength tiers ahead of magnitude.
  if (TRIGGER_RANKED.test(prose)) {
    const o = f.ordering;
    if (!Array.isArray(o) || o.length === 0)
      add('B12', `the brief ranks a list ("${TRIGGER_RANKED.exec(prose)[0]}") but the machine block has no "ordering"`);
    else
      for (const e of o)
        if (!text(e.list) || !Array.isArray(e.tiers) || e.tiers.length < 2 || !e.tiers.every(text) || !text(e.thenBy))
          add(
            'B12',
            `ordering "${e.list || '?'}" needs "list", at least two evidence "tiers" (strongest first) and "thenBy" (the magnitude)`,
          );
  }

  // B13 — a truncated field names what must survive, and the near-duplicates it must tell apart.
  if (TRIGGER_TRUNCATION.test(prose)) {
    const t = f.truncation;
    if (!Array.isArray(t) || t.length === 0)
      add('B13', `the brief truncates a field ("${TRIGGER_TRUNCATION.exec(prose)[0]}") but the machine block has no "truncation"`);
    else
      for (const e of t) {
        if (!text(e.field) || !text(e.mustSurvive))
          add('B13', `truncation "${e.field || '?'}" needs "field" and "mustSurvive" (the token that tells near-identical items apart)`);
        const nd = e.nearDuplicates;
        const listed = Array.isArray(nd) && nd.length > 0 && nd.every(text);
        const declaredNone = typeof nd === 'string' && /^none\b.{10,}/i.test(nd.trim());
        if (!listed && !declaredNone)
          add(
            'B13',
            `truncation "${e.field || '?'}" needs "nearDuplicates": the near-identical items in the data, or "none: <how that was checked>"`,
          );
      }
  }

  // B14 — say-once inside the brief's own Copy deck.
  const deck = deckRepeats(markdown, Array.isArray(f.sayOnceExceptions) ? f.sayOnceExceptions : []);
  if (deck.error) add('B14', `${deck.error} — a deck that cannot be screened has not passed`);
  else
    for (const r of deck.repeats)
      add('B14', `the Copy deck says "${r.phrases[0]}" in more than one at-rest string (rows ${r.rows.join(', ')}) — say it once`);

  // B15 — self-contained: no placeholder rows, no "as it is", no pointer to another brief.
  const deckParsed = (() => {
    try {
      return require('./check-copy-screen.js').parseDeck(markdown || '');
    } catch {
      return null;
    }
  })();
  if (deckParsed && deckParsed.header) {
    const ships = deckParsed.header.findIndex((h) => h.includes('ships as') || h.includes('replacement'));
    if (ships !== -1)
      for (const r of deckParsed.rows)
        if (DECK_PLACEHOLDER.test(r.cells[ships] || ''))
          add('B15', `Copy deck row ${r.cells[0]} ships "${(r.cells[ships] || '').slice(0, 70)}" — a placeholder, not the words`);
  }
  const lineOf = (i) => prose.slice(0, i).split('\n').length;
  for (const m of prose.matchAll(new RegExp(AS_IT_IS.source, 'gim')))
    add('B15', `line ${lineOf(m.index)}: "${m[0]}" hands the designer a view the brief does not contain — write its content inline`);
  for (const m of prose.matchAll(new RegExp(OTHER_BRIEF.source, 'gi')))
    add('B15', `line ${lineOf(m.index)}: "${m[0]}" points at another brief — the designer can read only this one; carry the content here`);

  // B16 — every state × every view has a layout (or an explicit "same as …" / "cannot arise: …").
  const st = f.states;
  if (!Array.isArray(st) || st.length === 0) add('B16', 'the machine block has no "states" matrix (state × view → layout)');
  else {
    const states = [...new Set(st.map((s) => s.state))];
    const views = [...new Set(st.map((s) => s.view))];
    for (const s of st)
      if (!text(s.state) || !text(s.view) || !text(s.layout) || /^\s*(tbd|todo|\?|—|-)\s*$/i.test(s.layout))
        add('B16', `states entry "${s.state || '?'} × ${s.view || '?'}" needs a layout, "same as <state>", or "cannot arise: <why>"`);
    for (const s of states)
      for (const v of views)
        if (!st.some((x) => x.state === s && x.view === v))
          add('B16', `no layout for state "${s}" in view "${v}" — give one, "same as <state>", or "cannot arise: <why>"`);
    for (const [need, re] of [
      ['empty', /empty|nothing|no (items|lines|rows|results)/i],
      ['loading', /load/i],
      ['error', /error|fail|unreachable|refus/i],
    ])
      if (!states.some((s) => re.test(s))) add('B16', `the states matrix has no "${need}" state`);
  }

  // B17 — responsive: 1440, 1280 and a narrow width, each with a layout; drawer overlay or push.
  const rs = f.responsive;
  if (!Array.isArray(rs) || rs.length === 0) add('B17', 'the machine block has no "responsive" spec (1440, 1280 and one narrow width)');
  else {
    const widths = rs.map((r) => r.width);
    if (!widths.includes(1440)) add('B17', 'responsive has no 1440 entry');
    if (!widths.includes(1280)) add('B17', 'responsive has no 1280 entry');
    if (!widths.some((w) => typeof w === 'number' && w <= NARROW_MAX)) add('B17', `responsive has no narrow entry (≤ ${NARROW_MAX}px)`);
    const hasDrawer = TRIGGER_DRAWER.test(prose);
    for (const r of rs) {
      if (!text(r.layout)) add('B17', `responsive ${r.width || '?'}px has no "layout"`);
      if (hasDrawer && !['overlay', 'push'].includes(r.drawer))
        add('B17', `responsive ${r.width || '?'}px must say whether the drawer overlays or pushes ("drawer": "overlay" | "push")`);
    }
  }

  // B18 — actions ⇒ feedback: position, look, duration, wording.
  if (TRIGGER_ACTION.test(prose)) {
    const fb = f.feedback;
    if (!fb || typeof fb !== 'object')
      add('B18', `the brief has actions ("${TRIGGER_ACTION.exec(prose)[0]}") but the machine block has no "feedback" spec`);
    else {
      for (const k of ['position', 'look', 'wording']) if (!text(fb[k])) add('B18', `feedback needs "${k}"`);
      if (!(typeof fb.durationMs === 'number' && fb.durationMs > 0) && !/^until\b/i.test(String(fb.duration || '')))
        add('B18', 'feedback needs "durationMs" (a number) or "duration": "until <what dismisses it>"');
    }
  }

  // B19 — headroom: the brief's own count of words above the first item leaves 15% of the budget.
  const budget = { ...DEFAULT_BUDGETS, ...f.budgets }.proseAboveFirstItem;
  const declared = f.attention && f.attention.wordsAboveFirstItem;
  if (typeof declared === 'number') {
    const floorCount = words(f.attention.top).length;
    if (declared < floorCount)
      add('B19', `attention.wordsAboveFirstItem (${declared}) is fewer than the answer alone (${floorCount}) — the count is wrong`);
    if (declared > Math.floor(budget * HEADROOM))
      add(
        'B19',
        `${declared} words above the first item leaves no headroom: the brief may spend ${Math.floor(budget * HEADROOM)} of the ${budget}-word budget (85%)`,
      );
  } else {
    add('B19', 'attention.wordsAboveFirstItem is not declared — count the words the design puts above the first item');
  }

  // B20 — the brief's notation is not rendering: say so, and say what the page prints between items.
  const nt = f.notation;
  if (!nt || !text(nt.notLiteral) || !text(nt.separators))
    add(
      'B20',
      'the machine block needs "notation": { "notLiteral": what the brief\'s own marks mean, "separators": what the page prints between items }',
    );

  for (const d of sectionSpecFindings(f)) add('B21', d);
  for (const d of rowGroupSpecFindings(f)) add('B22', d);
  for (const d of exemptionSpecFindings(f)) add('B23', d);
  for (const d of ownBudgetFindings(markdown, f)) add('B24', d);

  return out;
}

/* ───────────────────── sections below the fold (B21, presentation-floor.md §9, G10) ───────────────────── */
/*
 * Owner, 2026-09-28, on Claude Design's v6 of the price-list page, scrolled down: "not too happy when I
 * scrolled down.. looks like text printed on a screen with no thought." The floor limited prose ABOVE
 * the first item only, so six paragraphs of caveats, five long held questions, a stand-in note and a
 * six-line provenance footer sat below it untouched. Every section now declares its form and budget.
 */
function sectionSpecFindings(floor) {
  const out = [];
  const b = { ...DEFAULT_BUDGETS, ...floor.budgets };
  const text = (v) => typeof v === 'string' && v.trim().length > 0;
  const secs = floor.sections;
  if (!Array.isArray(secs) || secs.length === 0) {
    out.push(
      'the machine block has no "sections": every section of the page needs { name, kind, form: cards|rows|disclosure|message-block, wordBudget }',
    );
    return out;
  }
  const names = new Set();
  for (const s of secs) {
    const n = s.name || '?';
    if (!text(s.name)) out.push('a section has no "name" (the value of its data-section marker)');
    else if (names.has(s.name)) out.push(`section "${n}" is declared twice`);
    else names.add(s.name);
    if (!SECTION_KINDS.includes(s.kind)) out.push(`section "${n}" needs "kind", one of ${SECTION_KINDS.join(', ')}`);
    if (!SECTION_FORMS.includes(s.form)) out.push(`section "${n}" needs "form", one of ${SECTION_FORMS.join(', ')}: never running prose`);
    if (typeof s.wordBudget !== 'number' || s.wordBudget <= 0)
      out.push(`section "${n}" needs a numeric "wordBudget" (words visible at rest)`);
    else if (s.kind !== 'items' && s.kind !== 'facts' && s.wordBudget > b.sectionWordsMax)
      out.push(
        `section "${n}" allows ${s.wordBudget} words at rest; a section that is not the items may show at most ${b.sectionWordsMax}`,
      );
    if (COLLAPSED_KINDS.has(s.kind) && s.kind !== 'footer') {
      const want = s.kind === 'message' ? 'message-block' : 'disclosure';
      if (s.form !== want) out.push(`section "${n}" is ${s.kind}: its form must be "${want}", collapsed at rest`);
      if (!text(s.summary) || s.summary.trim().split(/\s+/).length > b.summaryMaxWords)
        out.push(`section "${n}" is collapsed at rest: give its one-line "summary" (at most ${b.summaryMaxWords} words)`);
    }
    if (s.kind === 'footer') {
      if (typeof s.linesAtRest !== 'number' || s.linesAtRest > b.footerLinesAtRest)
        out.push(`the footer needs "linesAtRest" of at most ${b.footerLinesAtRest}; the rest goes behind a disclosure`);
      if (!text(s.disclosure)) out.push('the footer needs "disclosure": the label of the control that opens the rest');
    }
    if (s.kind === 'caveats' && s.form !== 'rows')
      out.push(`section "${n}" holds caveats: its form must be "rows" (a label and a short line each)`);
    if (s.form === 'rows') {
      if (typeof s.maxRows !== 'number' || s.maxRows > b.maxRows) out.push(`section "${n}" needs "maxRows" of at most ${b.maxRows}`);
      if (typeof s.rowMaxWords !== 'number' || s.rowMaxWords > b.rowMaxWords)
        out.push(`section "${n}" needs "rowMaxWords" of at most ${b.rowMaxWords} (after the row's label)`);
    }
    if (s.form === 'message-block' && !(Array.isArray(s.controls) && s.controls.length > 0 && s.controls.every(text)))
      out.push(`section "${n}" is a message block: name its "controls" (e.g. Copy, Open WhatsApp)`);
  }
  if (!secs.some((s) => s.kind === 'footer')) out.push('no section of kind "footer": say what the footer shows at rest');
  return out;
}

/* ───────────────────── label/value row groups (B22, presentation-floor.md §10, G11) ───────────────────── */
/*
 * Owner, 2026-09-28, on Claude Design's bundle 6 drawer, "The journey to Amazon UK, cost by cost": it
 * "reads as a mess printed on a screen, not much thought about font size, spacing". The brief itself
 * had asked for a standing column beside a figure that, for an unpriced leg, was the same words, and a
 * caption paragraph under every leg. A label/value list is now a named form with its own rules.
 */
function rowGroupSpecFindings(floor) {
  const out = [];
  const b = { ...DEFAULT_BUDGETS, ...floor.budgets };
  const text = (v) => typeof v === 'string' && v.trim().length > 0;
  const groups = (Array.isArray(floor.sections) ? floor.sections : []).filter((s) => s.form === 'value-rows' || s.kind === 'facts');
  if (groups.length === 0) return out;
  const internal = Array.isArray(floor.internalWords) ? floor.internalWords.map((w) => String(w).toLowerCase()) : [];
  for (const w of DEFAULT_INTERNAL_WORDS)
    if (!internal.includes(w)) out.push(`"internalWords" must list "${w}": a row group may not show our own machinery's words`);
  for (const g of groups) {
    const n = g.name || '?';
    if (g.form !== 'value-rows') out.push(`section "${n}" is a list of facts: its form must be "value-rows"`);
    const cols = Array.isArray(g.columns) ? g.columns : [];
    if (!cols.includes('label') || !cols.includes('value') || cols.some((c) => !['label', 'value', 'status', 'note'].includes(c)))
      out.push(`section "${n}" needs "columns" from label, value, status, note, with label and value`);
    if (cols.filter((c) => c === 'value').length > 1 || cols.filter((c) => c === 'status').length > 1)
      out.push(`section "${n}" has more than one value or status column: one value cell and one optional status per row`);
    if (typeof g.valueMaxWords !== 'number' || g.valueMaxWords > b.valueMaxWords)
      out.push(
        `section "${n}" needs "valueMaxWords" of at most ${b.valueMaxWords}: a value is money, a count or a few words, never a sentence`,
      );
    if (cols.includes('note') && (typeof g.noteMaxWords !== 'number' || g.noteMaxWords > b.noteMaxWords))
      out.push(`section "${n}" needs "noteMaxWords" of at most ${b.noteMaxWords}, in the secondary style`);
    if (g.valueAlign !== 'right' || g.numerals !== 'tabular')
      out.push(`section "${n}" needs "valueAlign": "right" and "numerals": "tabular"`);
    const sp = Array.isArray(floor.spacing) ? floor.spacing : [];
    if (typeof g.rowGap !== 'number' || typeof g.innerGap !== 'number' || g.rowGap <= g.innerGap)
      out.push(`section "${n}" needs "rowGap" larger than "innerGap": rows must sit further apart than the lines inside a row`);
    else if (sp.length > 0 && (!sp.includes(g.rowGap) || !sp.includes(g.innerGap)))
      out.push(`section "${n}": rowGap and innerGap must come from the spacing scale`);
    if (typeof g.maxRows !== 'number' || g.maxRows > b.maxFactRows) out.push(`section "${n}" needs "maxRows" of at most ${b.maxFactRows}`);
    if (cols.includes('status')) {
      const sv = g.statusValues;
      if (!Array.isArray(sv) || sv.length === 0 || sv.length > 5 || !sv.every((x) => text(x) && x.trim().split(/\s+/).length <= 3))
        out.push(`section "${n}" has a status column: list its "statusValues" (at most 5, each at most 3 words)`);
      else if (sv.some((x) => UNPRICED_VALUE.test(x)))
        out.push(`section "${n}": a status that says a figure is missing repeats the value cell; say it once, in the value`);
    }
    const t = g.total;
    if (typeof t === 'string') {
      if (!/^none:\s*\S.{8,}/i.test(t)) out.push(`section "${n}" "total" must be a { label, partial } object or "none: <why>"`);
    } else if (!t || !text(t.label) || typeof t.partial !== 'boolean')
      out.push(`section "${n}" needs "total": { "label", "partial": true|false }, or "none: <why>"`);
    else if (t.partial && !PARTIAL_LABEL.test(t.label))
      out.push(`section "${n}" total is partial but its label "${t.label}" does not say so`);
  }
  return out;
}

/* ───────────────────── declared exemptions (B23) and the brief's own budgets (B24) ───────────────────── */
/*
 * Owner's build agent, 2026-09-28, on the live price list: the checker failed strings the brief itself
 * prescribes — two real products sharing a name (R8), supplier codes and the supplier's own capitalised
 * Spanish title (R10), a supplier drawer whose answer has no figure by design (R6) — and R17/R18 made it
 * reword the brief's own copy. The fix is not a looser check: it is an exemption the BRIEF declares,
 * that this validator can see, that names its reason, and that the rendered report prints every time.
 */
function exemptionSpecFindings(floor) {
  const out = [];
  const text = (v) => typeof v === 'string' && v.trim().length >= 10;
  for (const q of Array.isArray(floor.quotedSources) ? floor.quotedSources : []) {
    if (!q || typeof q.source !== 'string' || !/^[a-z][a-z-]*$/.test(q.source))
      out.push('a quotedSources entry needs "source": the lower-case value of its data-source marker');
    if (!text(q && q.what)) out.push(`quoted source "${(q && q.source) || '?'}" needs "what": which strings are that source's own words`);
    const ex = Array.isArray(q && q.exempts) ? q.exempts : [];
    if (ex.length === 0 || ex.some((c) => !QUOTABLE_CHECKS.has(c)))
      out.push(`quoted source "${(q && q.source) || '?'}" may exempt only ${[...QUOTABLE_CHECKS].join(', ')}, and must name which`);
  }
  for (const e of Array.isArray(floor.exemptions) ? floor.exemptions : []) {
    const c = e && e.check;
    if (!EXEMPTABLE_CHECKS.has(c)) {
      out.push(
        `an exemption from "${c || '?'}" is not allowed: only ${[...EXEMPTABLE_CHECKS].join(', ')} can be exempted, and only narrowly`,
      );
      continue;
    }
    if (!text(e.why)) out.push(`the ${c} exemption needs "why": the reason in at least a sentence`);
    if (c === 'R6' && (typeof e.view !== 'string' || !e.view.trim()))
      out.push('an R6 exemption needs "view": the one data-page whose answer carries no figure by design');
    if (c === 'R8' && (e.scope !== 'across-items' || typeof e.max !== 'number' || e.max < 2 || e.max > MAX_ACROSS_ITEMS))
      out.push(`an R8 exemption needs "scope": "across-items" and "max" from 2 to ${MAX_ACROSS_ITEMS}`);
  }
  const internal = (Array.isArray(floor.internalWords) ? floor.internalWords : DEFAULT_INTERNAL_WORDS).map((w) => String(w).toLowerCase());
  for (const x of Array.isArray(floor.internalWordExceptions) ? floor.internalWordExceptions : []) {
    const ph = String((x && x.phrase) || '').toLowerCase();
    if (!internal.some((w) => new RegExp(String.raw`\b${w}\b`).test(ph)))
      out.push(`internalWordExceptions "${(x && x.phrase) || '?'}" contains no internal word: it exempts nothing, remove it`);
    else if (ph.trim().split(/\s+/).length < 3)
      out.push(`internalWordExceptions "${x.phrase}" must be a phrase of three or more words, not the word itself`);
    if (!text(x && x.why)) out.push(`internalWordExceptions "${(x && x.phrase) || '?'}" needs "why"`);
  }
  return out;
}

/**
 * B24 (G13). A brief used to declare a section's wordBudget and never count its own content against it:
 * the price-list journey declared 90 and its own row 7 came to 96 with the heading and caption, so a
 * build that followed the brief word for word failed R13. Each section below the items now carries a
 * `sample` — the at-rest strings of the brief's own worked instance — every one of which must appear in
 * the brief's prose, and whose words must fit the budget.
 */
function ownBudgetFindings(markdown, floor) {
  const out = [];
  const secs = Array.isArray(floor.sections) ? floor.sections : [];
  const flat = (t) =>
    String(t || '')
      .replaceAll(/[*`_]/g, '')
      .replaceAll(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  const prose = flat(proseOf(markdown));
  for (const s of secs) {
    if (s.kind === 'items') continue;
    const n = s.name || '?';
    if (!Array.isArray(s.sample) || s.sample.length === 0 || !s.sample.every((x) => typeof x === 'string' && x.trim())) {
      out.push(`section "${n}" needs "sample": the at-rest strings of this brief's own worked instance, in order`);
      continue;
    }
    for (const x of s.sample)
      if (!prose.includes(flat(x))) out.push(`section "${n}" sample "${x.slice(0, 50)}" is not written anywhere in the brief's prose`);
    const count = s.sample.reduce((a, x) => a + words(x).length, 0);
    if (typeof s.wordBudget === 'number' && count > s.wordBudget)
      out.push(`section "${n}": the brief's own content is ${count} words at rest, over its wordBudget of ${s.wordBudget}`);
  }
  return out;
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
  // §11: a text is exempt from check `id` only when its data-source is declared for that check, and
  // never when it is part of the answer.
  const quoted = new Map((floor.quotedSources || []).map((q) => [q.source, new Set(q.exempts || [])]));
  const isQuoted = (t, id) => !!t.quoted && !t.inAnswer && quoted.has(t.quoted) && quoted.get(t.quoted).has(id);
  const exemption = (id) => (floor.exemptions || []).filter((e) => e.check === id);
  const itemBlocks = blocks.filter((b) => b.item);
  const itemOf = (t) =>
    itemBlocks.findIndex(
      (b) =>
        t.top >= b.top - 1 && t.bottom <= b.bottom + 1 && t.left >= (b.left ?? 0) - 1 && t.left < (b.left ?? 0) + (b.width ?? Infinity),
    );

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
      ['R19', 'inline-provenance'],
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
    const r6 = exemption('R6').find((e) => snapshot.page && e.view === snapshot.page);
    if (answer && r6) put('R6', 'headline-figure', 'exempt', `exempt on "${snapshot.page}" by the brief: ${r6.why}`);
    else if (answer) {
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
    let quotedSkipped = 0;
    for (const t of visible) {
      if (isQuoted(t, 'R8')) {
        quotedSkipped += 1;
        continue;
      }
      for (const s of sentencesOf(t.text)) {
        if (s.length < MIN_SENTENCE_CHARS) continue;
        // Literal, as artifact-policy-check.ts does: a sentence with a different number in it is a
        // different fact (a 30-day basis beside a 90-day one). Numbers are normalised only for
        // CLAUSES below, where the same wording down every row is the ledger pattern itself.
        const k = s
          .toLowerCase()
          .replaceAll(/\s+/g, ' ')
          .replace(/[.!?]+$/, '');
        const e = sentenceCount.get(k) || { n: 0, sample: s, items: [] };
        e.n += 1;
        e.items.push(itemOf(t));
        sentenceCount.set(k, e);
      }
    }
    const clauseEls = new Map();
    for (const t of visible) {
      if (t.control || isQuoted(t, 'R8')) continue;
      for (const c of new Set(clausesOf(t.text).map(normalise))) {
        if (c.split(' ').filter((w) => /\p{L}/u.test(w)).length < 3) continue;
        clauseEls.set(c, (clauseEls.get(c) || 0) + 1);
      }
    }
    // A sentence said once in each of up to `max` different items is two products that share a name,
    // not a fact said twice — when, and only when, the brief declares it (§11).
    const across = exemption('R8').find((e) => e.scope === 'across-items');
    const acrossOk = (e) => !!across && e.n <= across.max && e.items.every((i) => i !== -1) && new Set(e.items).size === e.items.length;
    const exemptS = [...sentenceCount.values()].filter((e) => e.n > 1 && acrossOk(e));
    const dupS = [...sentenceCount.values()].filter((e) => e.n > 1 && !acrossOk(e));
    const dupC = [...clauseEls.entries()].filter(([, n]) => n > budgets.repeatedClauseMax);
    const ev = [...dupS.map((e) => `×${e.n} "${e.sample.slice(0, 70)}"`), ...dupC.map(([c, n]) => `×${n} clause "${c.slice(0, 70)}"`)];
    const exemptNote = [
      quotedSkipped > 0 ? `${quotedSkipped} quoted-source text(s) not compared` : '',
      exemptS.length > 0 ? `${exemptS.length} sentence(s) once in each of ≤ ${across.max} items, exempt by the brief: ${across.why}` : '',
    ]
      .filter(Boolean)
      .join('; ');
    put(
      'R8',
      'repeated-sentence',
      ev.length > 0 ? 'fail' : exemptNote ? 'exempt' : 'pass',
      ev.length > 0
        ? `${dupS.length} sentence(s) said more than once, ${dupC.length} clause(s) repeated in more than ${budgets.repeatedClauseMax} places`
        : exemptNote || 'nothing said twice',
      [...ev, ...exemptS.map((e) => `exempt ×${e.n} "${e.sample.slice(0, 70)}"`)],
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
    let capsQuoted = 0;
    for (const t of visible) {
      if (isQuoted(t, 'R10')) {
        capsQuoted += 1;
        continue;
      }
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
      caps.length > 0 ? 'fail' : capsQuoted > 0 ? 'exempt' : 'pass',
      caps.length > 0
        ? `${caps.length} shouted run(s)`
        : capsQuoted > 0
          ? `no all-caps text of ours; ${capsQuoted} quoted-source text(s) not read, as the brief declares`
          : 'no all-caps text',
      caps.slice(0, 8),
    );

    // R19 — provenance written into the body
    const prov = [...DEFAULT_PROVENANCE, ...(Array.isArray(floor.provenancePhrases) ? floor.provenancePhrases : [])].map(
      (x) => new RegExp(x, 'iu'),
    );
    const inline = [];
    let provQuoted = 0;
    for (const t of visible) {
      if (t.inFooter || t.inDisclosure || t.control) continue;
      const hit = prov.find((re) => re.test(t.text));
      if (!hit) continue;
      if (isQuoted(t, 'R19')) {
        provQuoted += 1;
        continue;
      }
      inline.push(`"${hit.exec(t.text)[0].trim()}" in "${t.text.slice(0, 70)}"`);
    }
    put(
      'R19',
      'inline-provenance',
      inline.length > 0 ? 'fail' : 'pass',
      inline.length > 0
        ? `${inline.length} provenance caption(s) in the body; they belong in the footer or a closed disclosure`
        : `no provenance caption in the body${provQuoted > 0 ? `; ${provQuoted} quoted-source text(s) not read` : ''}`,
      inline.slice(0, 10),
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

  for (const r of belowFoldChecks(snapshot || {}, floor, budgets)) put(r.id, r.name, r.status, r.detail, r.evidence);
  for (const r of rowGroupChecks(snapshot || {}, floor, budgets)) put(r.id, r.name, r.status, r.detail, r.evidence);

  results.sort((x, y) => Number(x.id.slice(1)) - Number(y.id.slice(1)));
  return results;
}

/** R12–R14 (presentation-floor.md §9): the page below the first item has structure, not prose. */
function belowFoldChecks(snapshot, floor, budgets) {
  const out = [];
  const put = (id, name, status, detail, evidence = []) => out.push({ id, name, status, detail, evidence });

  // R12 — prose wall, anywhere on the page
  if (Array.isArray(snapshot.paragraphs)) {
    const runs = (snapshot.paragraphRuns || []).filter((r) => r.length > budgets.maxConsecutiveParagraphs);
    const wc = (p) => p.words ?? words(p.text).length;
    const long = snapshot.paragraphs.filter((p) => wc(p) > budgets.maxParagraphWords);
    const ev = [
      ...runs.map((r) => `${r.length} paragraphs in a row${r.section ? ` in "${r.section}"` : ''}: "${(r.sample || '').slice(0, 60)}"`),
      ...long.map((p) => `${wc(p)}-word paragraph: "${(p.text || '').slice(0, 60)}"`),
    ];
    put(
      'R12',
      'prose-wall',
      ev.length > 0 ? 'fail' : 'pass',
      ev.length > 0
        ? `${runs.length} run(s) of more than ${budgets.maxConsecutiveParagraphs} paragraphs, ${long.length} paragraph(s) over ${budgets.maxParagraphWords} words: text printed on a screen`
        : `${snapshot.paragraphs.length} paragraph(s), none in a wall`,
      ev.slice(0, 8),
    );
  } else put('R12', 'prose-wall', 'unchecked', 'the snapshot carries no paragraph list (take it with the current --print-probe)');

  // R13 — every declared section in its form, and anything collapsible collapsed
  // A section declared for another view (the drawer, say) is not looked for on this snapshot.
  const declared = (Array.isArray(floor.sections) ? floor.sections : []).filter(
    (d) => !d.view || !snapshot.page || d.view === snapshot.page,
  );
  if (!Array.isArray(snapshot.sections)) put('R13', 'section-form', 'unchecked', 'the snapshot carries no [data-section] list');
  else if (declared.length === 0 && snapshot.sections.length === 0)
    put('R13', 'section-form', 'unchecked', 'the floor declares no sections and the page marks none');
  else {
    const bad = [];
    const missing = [];
    const byName = new Map(snapshot.sections.map((s) => [s.name, s]));
    const specs = declared.filter((d) => d.kind !== 'footer');
    for (const s of snapshot.sections)
      if (!declared.some((d) => d.name === s.name)) specs.push({ name: s.name, kind: s.kind, form: s.form, undeclared: true });
    for (const d of specs) {
      const s = byName.get(d.name);
      if (!s) {
        missing.push(d.name);
        continue;
      }
      if (d.undeclared && !d.form) {
        bad.push(`"${d.name}" is on the page but the brief declares no form for it`);
        continue;
      }
      const budget = typeof d.wordBudget === 'number' ? d.wordBudget : d.kind === 'items' ? Infinity : budgets.sectionWordsMax;
      if (s.wordsAtRest > budget) bad.push(`"${d.name}" shows ${s.wordsAtRest} words at rest; budget ${budget}`);
      if (COLLAPSED_KINDS.has(d.kind) || d.form === 'disclosure' || d.form === 'message-block') {
        if (s.collapsed !== true) bad.push(`"${d.name}" (${d.kind || d.form}) is open at rest; it belongs behind a disclosure`);
        else if (s.wordsAtRest > budgets.summaryMaxWords)
          bad.push(`"${d.name}" is collapsed but shows ${s.wordsAtRest} words; one summary line of at most ${budgets.summaryMaxWords}`);
      }
      if (d.form === 'rows') {
        const rows = s.rows || [];
        const maxRows = d.maxRows ?? budgets.maxRows;
        const rowMax = d.rowMaxWords ?? budgets.rowMaxWords;
        if (rows.length === 0) bad.push(`"${d.name}" is declared as rows but carries no [data-row]`);
        if (rows.length > maxRows) bad.push(`"${d.name}" has ${rows.length} rows; at most ${maxRows}`);
        for (const r of rows) {
          if (!r.label) bad.push(`"${d.name}" has a row with no [data-row-label]: "${(r.text || '').slice(0, 50)}"`);
          if (r.words > rowMax)
            bad.push(`"${d.name}" row "${(r.label || r.text || '').slice(0, 30)}" is ${r.words} words after its label; at most ${rowMax}`);
        }
      }
    }
    if (bad.length > 0) put('R13', 'section-form', 'fail', `${bad.length} section problem(s)`, bad.slice(0, 10));
    else if (missing.length > 0)
      put('R13', 'section-form', 'unchecked', `${missing.length} declared section(s) are not marked on the page: ${missing.join(', ')}`);
    else put('R13', 'section-form', 'pass', `${specs.length} section(s), each in its declared form`);
  }

  // R14 — footer lines at rest
  const ft = snapshot.footer;
  const footSpec = declared.find((d) => d.kind === 'footer');
  const maxLines = Math.min(
    budgets.footerLinesAtRest,
    footSpec && typeof footSpec.linesAtRest === 'number' ? footSpec.linesAtRest : Infinity,
  );
  if (!ft) put('R14', 'footer-at-rest', 'unchecked', 'no [data-footer] or <footer> in the snapshot');
  else if (ft.linesAtRest > maxLines)
    put(
      'R14',
      'footer-at-rest',
      'fail',
      `the footer shows ${ft.linesAtRest} lines at rest; at most ${maxLines}, the rest behind a disclosure`,
      [(ft.text || '').slice(0, 120)],
    );
  else if (ft.hasDisclosure) {
    put('R14', 'footer-at-rest', 'pass', `the footer shows ${ft.linesAtRest} line(s) at rest, the rest behind a disclosure`);
  } else {
    put(
      'R14',
      'footer-at-rest',
      'fail',
      'the footer has no disclosure: the provenance beyond its lines at rest must open, not be dropped or printed',
    );
  }

  return out;
}

/** R15–R18 (presentation-floor.md §10): a label/value row group is a grid, not text printed in rows. */
function rowGroupChecks(snapshot, floor, budgets) {
  const out = [];
  const put = (id, name, status, detail, evidence = []) => out.push({ id, name, status, detail, evidence });
  const ids = [
    ['R15', 'row-cells'],
    ['R16', 'row-grid'],
    ['R17', 'internal-words'],
    ['R18', 'row-total'],
  ];
  const groups = snapshot.rowGroups;
  const specs = (Array.isArray(floor.sections) ? floor.sections : []).filter((s) => s.form === 'value-rows');
  const here = specs.filter((d) => !d.view || !snapshot.page || d.view === snapshot.page);
  if (!Array.isArray(groups)) {
    for (const [id, name] of ids)
      put(id, name, 'unchecked', 'the snapshot carries no [data-row-group] list (take it with the current --print-probe)');
    return out;
  }
  if (groups.length === 0) {
    const detail =
      here.length > 0
        ? `the brief declares ${here.map((d) => `"${d.name}"`).join(', ')} as a row group here, but the page marks none`
        : 'no label/value row group is declared for this view or present on it';
    for (const [id, name] of ids) put(id, name, here.length > 0 ? 'unchecked' : 'pass', detail);
    return out;
  }
  const wc = (t) => (t || '').split(/\s+/).filter((w) => /[\p{L}\p{N}]/u.test(w)).length;
  const norm = (t) =>
    (t || '')
      .toLowerCase()
      .replaceAll(/[^\p{L}\p{N}£€$%.]+/gu, ' ')
      .trim();
  const isMoneyOrCount = (t) => /^[−-]?[£€$]?\s?[\d.,]+(\s?%|\s?[a-z]{0,6})?$/i.test((t || '').trim());
  const internal = (
    Array.isArray(floor.internalWords) && floor.internalWords.length > 0 ? floor.internalWords : DEFAULT_INTERNAL_WORDS
  ).map((w) => String(w).toLowerCase());
  // Internal words are plain words; anything that is not a letter is dropped rather than escaped.
  const quotedSrc = new Map((floor.quotedSources || []).map((q) => [q.source, new Set(q.exempts || [])]));
  const quotedFor = (c, id) => !!c.quoted && quotedSrc.has(c.quoted) && quotedSrc.get(c.quoted).has(id);
  const allowed = (floor.internalWordExceptions || []).map((x) => String(x.phrase || '').toLowerCase()).filter(Boolean);
  // An internal word inside a declared phrase ("an export from Spain") carries its ordinary meaning.
  const inAllowedPhrase = (t, at) =>
    allowed.some((ph) => {
      const low = (t || '').toLowerCase();
      for (let i = low.indexOf(ph); i !== -1; i = low.indexOf(ph, i + 1)) if (at >= i && at < i + ph.length) return true;
      return false;
    });
  const internalRe = new RegExp(`\\b(${internal.map((w) => w.replaceAll(/[^\p{L}]/gu, '')).join('|')})\\b`, 'iu');
  const cells = [],
    grid = [],
    words = [],
    totals = [];
  for (const g of groups) {
    const spec = specs.find((d) => d.name === g.name) || {};
    const vMax = spec.valueMaxWords ?? budgets.valueMaxWords;
    const nMax = spec.noteMaxWords ?? budgets.noteMaxWords;
    const rows = g.rows || [];
    const valueRights = [],
      statusLefts = [];
    let minRowGap = Infinity,
      maxInner = 0;
    for (const [i, r] of rows.entries()) {
      const cs = r.cells || [];
      const byRole = (role) => cs.filter((c) => c.role === role);
      const label = (byRole('label')[0] || {}).text || `row ${i + 1}`;
      const at = `"${g.name}" row "${label.slice(0, 40)}"`;
      if (byRole('value').length !== 1) cells.push(`${at} has ${byRole('value').length} value cells; exactly one`);
      if (byRole('status').length > 1) cells.push(`${at} has ${byRole('status').length} status badges; at most one`);
      for (let a = 0; a < cs.length; a++)
        for (let z = a + 1; z < cs.length; z++)
          if (norm(cs[a].text) && norm(cs[a].text) === norm(cs[z].text))
            cells.push(`${at}: the ${cs[z].role} repeats the ${cs[a].role} ("${cs[a].text.slice(0, 30)}")`);
      for (const v of byRole('value')) {
        if (!isMoneyOrCount(v.text) && wc(v.text) > vMax)
          cells.push(`${at}: the value "${v.text.slice(0, 50)}" is ${wc(v.text)} words; at most ${vMax}`);
        if (/\d/.test(v.text)) {
          if (!['right', 'end'].includes(v.textAlign)) grid.push(`${at}: the value is aligned ${v.textAlign || 'unknown'}, not right`);
          if (!/tabular-nums/.test(v.numeric || '')) grid.push(`${at}: the value is not in tabular numerals`);
        }
        if (typeof v.right === 'number') valueRights.push(v.right);
      }
      for (const n of byRole('note')) if (wc(n.text) > nMax) cells.push(`${at}: the explanation is ${wc(n.text)} words; at most ${nMax}`);
      for (const st of byRole('status')) if (typeof st.left === 'number') statusLefts.push(st.left);
      for (const c of cs) {
        if (quotedFor(c, 'R17')) continue;
        for (const m of (c.text || '').matchAll(new RegExp(internalRe.source, 'giu'))) {
          if (inAllowedPhrase(c.text, m.index)) continue;
          words.push(`${at}: "${m[0]}" in the ${c.role} ("${c.text.slice(0, 50)}")`);
        }
      }
      // Inside a row: the vertical space between stacked cells. Between rows: this row to the next.
      const stacked = [...cs].filter((c) => typeof c.top === 'number').sort((x, y) => x.top - y.top);
      for (let k = 1; k < stacked.length; k++) {
        const gap = stacked[k].top - Math.max(...stacked.slice(0, k).map((c) => c.bottom));
        if (gap > 0) maxInner = Math.max(maxInner, gap);
      }
      const next = rows[i + 1];
      if (next && typeof next.top === 'number' && typeof r.bottom === 'number') minRowGap = Math.min(minRowGap, next.top - r.bottom);
    }
    const spread = (xs) => (xs.length > 1 ? Math.max(...xs) - Math.min(...xs) : 0);
    if (spread(valueRights) > budgets.gridTolerancePx)
      grid.push(`"${g.name}": the value cells end at ${spread(valueRights)}px of different x across rows; one right edge`);
    if (spread(statusLefts) > budgets.gridTolerancePx)
      grid.push(`"${g.name}": the status text starts at ${spread(statusLefts)}px of different x across rows; one column`);
    if (rows.length > 1 && minRowGap !== Infinity && minRowGap <= maxInner)
      grid.push(`"${g.name}": rows are ${minRowGap}px apart and lines inside a row ${maxInner}px; the gap between rows must be larger`);
    const t = g.total;
    if (t && internalRe.test(t.text || '')) words.push(`"${g.name}" total: "${internalRe.exec(t.text)[0]}"`);
    const unpriced = rows.some((r) =>
      (r.cells || []).some((c) => c.role === 'value' && UNPRICED_VALUE.test(c.text || '') && !/\d/.test(c.text || '')),
    );
    const wantTotal = spec.total && typeof spec.total === 'object';
    if (unpriced || wantTotal) {
      if (!t) totals.push(`"${g.name}" ${unpriced ? 'has an unpriced row' : 'declares a total'} and shows no total`);
      else if (unpriced && !PARTIAL_LABEL.test(t.label || t.text || ''))
        totals.push(
          `"${g.name}" totals rows with an unpriced cost, but "${(t.label || t.text || '').slice(0, 50)}" does not say it is partial`,
        );
    }
  }
  put(
    'R15',
    'row-cells',
    cells.length > 0 ? 'fail' : 'pass',
    cells.length > 0 ? `${cells.length} cell problem(s)` : `${groups.length} row group(s), cells in order`,
    cells.slice(0, 10),
  );
  put(
    'R16',
    'row-grid',
    grid.length > 0 ? 'fail' : 'pass',
    grid.length > 0 ? `${grid.length} grid problem(s)` : 'values on one right edge, statuses in one column, rows spaced apart',
    grid.slice(0, 10),
  );
  put(
    'R17',
    'internal-words',
    words.length > 0 ? 'fail' : 'pass',
    words.length > 0 ? `${words.length} internal word(s) shown` : 'no internal vocabulary in a row group',
    words.slice(0, 10),
  );
  put(
    'R18',
    'row-total',
    totals.length > 0 ? 'fail' : 'pass',
    totals.length > 0 ? `${totals.length} total problem(s)` : 'every total says what it covers',
    totals,
  );
  return out;
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
      quoted: el.closest('[data-source]') ? el.closest('[data-source]').dataset.source : null,
      inFooter: !!el.closest('[data-footer], footer'),
      inDisclosure: !!el.closest('details[open], [data-disclosure]'),
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
  // §9 (G10): paragraphs, runs of paragraphs, declared sections and the footer, as seen at rest.
  const sectionOf = (el) => {
    const s = el.closest('[data-section]');
    return s ? s.dataset.section : null;
  };
  const countWords = (t) => t.split(/\s+/).filter((w) => /[\p{L}\p{N}]/u.test(w)).length;
  const paragraphs = [];
  for (const el of scope.querySelectorAll('p')) {
    if (!shown(el) || isControl(el)) continue;
    const t = rendered(el);
    if (t) paragraphs.push({ text: t, words: countWords(t), section: sectionOf(el), top: rect(el).top });
  }
  const paragraphRuns = [];
  for (const parent of new Set([...scope.querySelectorAll('p')].map((p) => p.parentElement))) {
    let run = [];
    const flush = () => {
      if (run.length > 1) paragraphRuns.push({ length: run.length, section: sectionOf(run[0]), sample: rendered(run[0]).slice(0, 80) });
      run = [];
    };
    for (const c of parent.children) {
      if (!shown(c)) continue;
      if (c.tagName === 'P' && rendered(c)) run.push(c);
      else flush();
    }
    flush();
  }
  const sections = [...scope.querySelectorAll('[data-section]')].filter(shown).map((el) => ({
    name: el.dataset.section,
    kind: el.dataset.sectionKind || null,
    form: el.dataset.sectionForm || null,
    wordsAtRest: countWords(rendered(el)),
    collapsed: !!el.querySelector('details:not([open]), [aria-expanded="false"]') || (el.tagName === 'DETAILS' && !el.open),
    rows: [...el.querySelectorAll('[data-row]')].filter(shown).map((r) => {
      const l = r.querySelector('[data-row-label]');
      const lt = l ? rendered(l) : '';
      const all = rendered(r);
      return { label: lt, text: all, words: countWords(all) - countWords(lt) };
    }),
  }));
  const footEl = scope.querySelector('[data-footer]') || document.querySelector('footer');
  // §10 (G11): label/value row groups, each cell with its role, box and alignment.
  const cellOf = (c) => {
    const r = c.getBoundingClientRect();
    const cs = getComputedStyle(c);
    return {
      role: c.dataset.cell,
      text: rendered(c),
      left: Math.round(r.left),
      right: Math.round(r.right),
      top: Math.round(r.top + scrollY),
      bottom: Math.round(r.bottom + scrollY),
      textAlign: cs.textAlign,
      numeric: cs.fontVariantNumeric,
      quoted: c.closest('[data-source]') ? c.closest('[data-source]').dataset.source : null,
    };
  };
  const rowGroups = [...scope.querySelectorAll('[data-row-group]')].filter(shown).map((g) => {
    const totalEl = g.querySelector('[data-row-total]');
    const totalLabel = totalEl && totalEl.querySelector('[data-cell="label"]');
    return {
      name: g.dataset.rowGroup,
      rows: [...g.querySelectorAll('[data-row]')]
        .filter((r) => shown(r) && !Object.hasOwn(r.dataset, 'rowTotal'))
        .map((r) => ({ ...rect(r), cells: [...r.querySelectorAll('[data-cell]')].filter(shown).map(cellOf) })),
      total:
        totalEl && shown(totalEl)
          ? { text: rendered(totalEl), label: totalLabel ? rendered(totalLabel) : '', partial: totalEl.dataset.total === 'partial' }
          : null,
    };
  });
  let footer = null;
  if (footEl && shown(footEl)) {
    const tops = new Map();
    for (const el of footEl.querySelectorAll('*')) {
      if (!shown(el) || ![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) continue;
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const lh = Number.parseFloat(cs.lineHeight) || Number.parseFloat(cs.fontSize) * 1.3;
      const key = Math.round(r.top);
      tops.set(key, Math.max(tops.get(key) || 0, Math.max(1, Math.round(r.height / lh))));
    }
    footer = {
      text: rendered(footEl),
      linesAtRest: [...tops.values()].reduce((a, b) => a + b, 0),
      hasDisclosure: !!footEl.querySelector('details, [aria-expanded]'),
    };
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
    paragraphs,
    paragraphRuns,
    sections,
    footer,
    rowGroups,
    page: scope.dataset ? scope.dataset.page || null : null,
  };
}

const PLAYWRIGHT_INSTALL = 'npm i -D playwright && npx playwright install chromium';
const ENV_NAME = /^[A-Za-z_]\w*$/;
const SESSION_MARKER = 'signed-in-by-check-rendered-page';

/**
 * Turn the --auth-* flags into a plan, or a refusal. Pure: it reads `env` and never prints a value.
 * Returns { plan } where plan is null when no auth flag was given, or { error }.
 */
function authPlan(url, opts, env) {
  const o = opts || {};
  const any = o.headerEnv || o.sessionMarker || (o.storageEnv && o.storageEnv.length > 0) || (o.dropHeaders && o.dropHeaders.length > 0);
  if (!any) return { plan: null };
  let origin;
  try {
    const u = new URL(url);
    origin = u.origin;
    const local = ['localhost', '127.0.0.1', '[::1]'].includes(u.hostname);
    if (u.protocol !== 'https:' && !local)
      return { error: `refusing to send a credential to ${origin} over ${u.protocol} — https, or localhost only` };
  } catch {
    return { error: `--url "${url}" is not a URL` };
  }
  const headers = {};
  if (o.headerEnv) {
    if (!ENV_NAME.test(o.headerEnv))
      return {
        error: `--auth-header-env takes the NAME of an environment variable, not a value ("${o.headerEnv.slice(0, 3)}…" is not a name)`,
      };
    const v = env[o.headerEnv];
    if (!v) return { error: `$${o.headerEnv} is not set or is empty; nothing was sent` };
    headers[(o.headerName || 'Authorization').toLowerCase()] = v;
  } else if (o.headerName) return { error: '--auth-header-name needs --auth-header-env' };
  const storage = {};
  if (o.sessionMarker) storage[o.sessionMarker] = SESSION_MARKER;
  for (const kv of o.storageEnv || []) {
    const m = /^([^=]+)=(.+)$/.exec(kv);
    if (!m || !ENV_NAME.test(m[2]))
      return { error: `--auth-storage-env takes KEY=ENV_VAR_NAME ("${kv.split('=')[0]}=…" does not name a variable)` };
    if (!env[m[2]]) return { error: `$${m[2]} is not set or is empty; nothing was stored` };
    storage[m[1]] = env[m[2]];
  }
  return { plan: { origin, headers, drop: (o.dropHeaders || []).map((h) => h.toLowerCase()), storage } };
}

/** The headers a request should carry under the plan: auth only to the page's own origin. */
function headersFor(plan, requestUrl, headers) {
  if (!plan) return headers;
  let origin;
  try {
    origin = new URL(requestUrl).origin;
  } catch {
    return headers;
  }
  if (origin !== plan.origin) return headers;
  const out = {};
  for (const [k, v] of Object.entries(headers || {})) if (!plan.drop.includes(k.toLowerCase())) out[k.toLowerCase()] = v;
  return { ...out, ...plan.headers };
}

/** Where to look for playwright: the project, NODE_PATH, and an explicit --playwright directory. */
function loadPlaywright(extraDir) {
  const paths = [process.cwd(), ...(process.env.NODE_PATH || '').split(':').filter(Boolean)];
  if (extraDir) paths.unshift(extraDir);
  try {
    const browserModule = 'playwright';
    return { playwright: require(require.resolve(browserModule, { paths })) };
  } catch {
    return {
      error:
        `playwright is not installed where this looked (${paths.join(', ')}), so the page could not be rendered. ` +
        `Install it in the project: \`${PLAYWRIGHT_INSTALL}\`, or point at one that has it: --playwright <dir containing node_modules>. ` +
        'Or capture a snapshot by hand: run the output of `--print-probe` in the page at 1440×900 and pass --snapshot. ' +
        'This is UNCHECKED, not passed.',
    };
  }
}

async function snapshotFromUrl(url, floor, theme, auth, playwrightDir) {
  const { plan, error: authError } = authPlan(url, auth, process.env);
  if (authError) return { error: `${authError}. This is UNCHECKED, not passed.` };
  const { playwright, error } = loadPlaywright(playwrightDir);
  if (error) return { error };
  const vp = floor.viewport || { width: 1440, height: 900 };
  let browser;
  try {
    browser = await playwright.chromium.launch();
  } catch (error_) {
    return {
      error: `playwright is installed but its browser is not (${String(error_.message).split('\n')[0]}). Run \`npx playwright install chromium\`. This is UNCHECKED, not passed.`,
    };
  }
  try {
    const context = await browser.newContext({ viewport: vp, colorScheme: theme === 'dark' ? 'dark' : 'light' });
    if (plan) {
      await context.route('**/*', (route) => {
        const r = route.request();
        return route.continue({ headers: headersFor(plan, r.url(), r.headers()) });
      });
      if (Object.keys(plan.storage).length > 0)
        await context.addInitScript((pairs) => {
          for (const [k, v] of pairs) localStorage.setItem(k, v);
        }, Object.entries(plan.storage));
    }
    const page = await context.newPage();
    await page.goto(url, { waitUntil: 'networkidle' });
    const gated = await page.evaluate(
      (answerSel) => !!document.querySelector('input[type=password]') && !document.querySelector(answerSel || '[data-answer]'),
      (floor.selectors || {}).answer,
    );
    if (gated)
      return {
        error: plan
          ? 'the page still rendered a sign-in form with the credentials given, so nothing was checked. UNCHECKED, not passed.'
          : 'the page rendered a sign-in form, so nothing was checked. Sign in with --auth-header-env (the signed-in flags are listed at the top of tools/check-rendered-page.js). UNCHECKED, not passed.',
      };
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
      console.log(`  ${{ pass: '✓', fail: '✗', unchecked: '?', exempt: '–' }[r.status]} ${r.id} ${r.name}: ${r.detail}`);
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
    const all = (k) => argv.flatMap((x, i) => (x === k && argv[i + 1] ? [argv[i + 1]] : []));
    const got = await snapshotFromUrl(
      arg('--url'),
      floor,
      arg('--theme'),
      {
        headerEnv: arg('--auth-header-env'),
        headerName: arg('--auth-header-name'),
        dropHeaders: all('--auth-drop-header'),
        sessionMarker: arg('--auth-session-marker'),
        storageEnv: all('--auth-storage-env'),
      },
      arg('--playwright'),
    );
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
  completenessFindings,
  sectionSpecFindings,
  deckRepeats,
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
  SECTION_FORMS,
  SECTION_KINDS,
  rowGroupSpecFindings,
  exemptionSpecFindings,
  ownBudgetFindings,
  DEFAULT_INTERNAL_WORDS,
  DEFAULT_PROVENANCE,
  authPlan,
  headersFor,
  loadPlaywright,
  snapshotFromUrl,
  PLAYWRIGHT_INSTALL,
};
