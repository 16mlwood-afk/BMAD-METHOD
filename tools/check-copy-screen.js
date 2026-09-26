/**
 * check-copy-screen.js  —  deterministic half of the on-screen copy screen (STD-COPY-SCREEN-001).
 *
 * Home of the rule: custom/workflows/design/shared/on-screen-copy-screen.md
 * Consumers:        design-handoff  steps/step-03c-gate1-brief-ready.md §1   (the brief's Copy deck)
 *                   design-implement steps/step-04-apply-and-deliver.md §5b   (every shipped string)
 * Fixture:          custom/workflows/design/shared/copy-screen-golden-matrix.md
 *
 * WHY THIS EXISTS. Owner, 2026-09-26, reading a price-list page: "It's the LLM language on the screen
 * that makes no sense to a human ... 'Check · 13 — boxes compared, something else to settle'". The
 * humanizer was wired to outbound email and nothing screened what a page says.
 *
 * ── What IS and ISN'T deterministically checkable (enforcement-expert axis) ──
 *
 *  CHECKED, hard (fails --strict):
 *    V1  internal vocabulary in a shipped string (the list in the contract §2c, any inflection)
 *    V2  CHECK / SKIP as a bare upper-case code, or `Check ·` / `Skip ·` used as a label
 *    R1  (deck mode) no Copy deck section, or a deck with no rows
 *    R2  (deck mode) a row whose Screen cell does not record all four parts a, b, c, d
 *    R3  (deck mode) a row whose Screen cell records a part as failed (✗)
 *    R4  (deck mode) a row with an empty Ships-as string
 *
 *  CHECKED, proxy (reported, never fails --strict — a guess must not block):
 *    P1  an ID-shaped first word (a run id, an ASIN, a 3+ digit number, `search #188`)
 *    P2  `label · number` shorthand, a count with no noun
 *    P3  any other upper-case code (UNCLEAR, DORMANT-WEAK, EAN-UK) that is not a common acronym
 *
 *  NOT CHECKED, on purpose: part (a) humanizing, part (b) the cold-reader test, part (d) the
 *  added-clause rule. Each is a judgement about a reader or about meaning, and a checker that guessed
 *  would launder that judgement into a green tick. A green run means the words are clean and the
 *  marks are present, never that the copy is good.
 *
 * Usage:
 *   node tools/check-copy-screen.js --deck    <brief.md>    [--json] [--strict]
 *   node tools/check-copy-screen.js --strings <file.txt>    [--json] [--strict]   (one string a line; # comments)
 *   node tools/check-copy-screen.js --string  "<text>"      [--json] [--strict]
 *
 * Exit: 0, unless --strict and hard findings exist (then 1). Bad usage: 2.
 */

'use strict';

const fs = require('node:fs');

/* ─────────────────────────── contract constants ─────────────────────────── */

/** Contract §2c. Word-boundary, case-insensitive, inflections included. */
const BANNED = [
  { word: 'verdict', re: /\bverdicts?\b/i },
  { word: 'disposition', re: /\bdisposition(?:s|ed)?\b/i },
  { word: 'lane', re: /\blanes?\b/i },
  { word: 'gate', re: /\bgat(?:e|es|ed|ing)\b/i },
  { word: 'route', re: /\brout(?:e|es|ed|ing)\b/i },
  { word: 'provenance', re: /\bprovenance\b/i },
  { word: 'identity test', re: /\bidentity[\s-]+tests?\b/i },
  { word: 'figure-listing', re: /\bfigure[\s-]+listings?\b/i },
  { word: 'precondition', re: /\bpre-?conditions?\b/i },
  { word: 'settle', re: /\bsettl(?:e|es|ed|ing|ement)\b/i },
  { word: 'rests on', re: /\b(?:rests?|resting)\s+on\b/i },
];

/** Acronyms a reader knows. Anything else in capitals is a P3 look. */
const KNOWN_ACRONYMS = new Set([
  'VAT',
  'EAN',
  'ASIN',
  'UK',
  'EU',
  'ECB',
  'FBA',
  'USB',
  'IVA',
  'GBP',
  'EUR',
  'USD',
  'SKU',
  'FX',
  'UTC',
  'API',
  'PDF',
  'CSV',
  'URL',
  'ID',
  'OK',
  'DE',
  'ES',
  'FR',
  'IT',
  'NL',
  'PL',
  'GB',
  'HMRC',
  'EORI',
  'DHL',
  'UPS',
  'LED',
  'AM',
  'PM',
]);

const TEMPLATE_VAR = /\$\{[^}]*\}|\{[^}]*\}/g;
/** A variable that stands for a count, so `Check · {n}` still reads as the `label · number` shorthand. */
const COUNT_VAR = /^\$?\{\s*(?:[a-z]|n\w*|count\w*|num\w*|total\w*)\s*\}$/i;

/* ─────────────────────────────── screening ─────────────────────────────── */

function clean(text) {
  return String(text)
    .replaceAll(/<[^>]+>/g, ' ')
    .replaceAll('`', '')
    .replaceAll(/^\s*["“']|["”']\s*$/g, '')
    .replaceAll(TEMPLATE_VAR, (v) => (COUNT_VAR.test(v) ? '7' : 'x'))
    .trim();
}

/** Screen one shipped string. Returns [{code, severity, detail}]. Pure. */
function screenString(raw) {
  const text = clean(raw);
  const out = [];
  if (!text) return out;
  for (const b of BANNED) {
    const m = b.re.exec(text);
    if (m) out.push({ code: 'V1', severity: 'hard', detail: `internal vocabulary "${m[0]}" (${b.word})` });
  }
  const bare = /\b(CHECK|SKIP)\b/.exec(text);
  if (bare) out.push({ code: 'V2', severity: 'hard', detail: `bare code "${bare[1]}"` });
  else if (/^(check|skip)\s*[·:|—–-]/i.test(text))
    out.push({ code: 'V2', severity: 'hard', detail: `"${text.split(/\s*[·:|—–-]/)[0]}" used as a label` });
  const first = text.split(/\s+/)[0] ?? '';
  if (
    /^#?\d{3,}\b/.test(first) ||
    /^B0[A-Z0-9]{8}\b/.test(first) ||
    /^[A-Z]{1,5}-\d{4,}(?:-\d+)?\b/.test(first) ||
    /^(?:search|run|box)\s+#?[A-Z0-9-]*\d{2,}/i.test(text)
  )
    out.push({ code: 'P1', severity: 'proxy', detail: `an ID-shaped first word "${first}"` });
  if (/^[^·\n]{1,30}\s·\s\d+\b/.test(text))
    out.push({ code: 'P2', severity: 'proxy', detail: '`label · number` shorthand — a count with no noun' });
  const codes = (text.match(/\b[A-Z][A-Z0-9]{2,}(?:-[A-Z0-9]+)*\b/g) ?? []).filter(
    (c) => !KNOWN_ACRONYMS.has(c) && c !== 'CHECK' && c !== 'SKIP' && !/\d/.test(c),
  );
  for (const c of new Set(codes)) out.push({ code: 'P3', severity: 'proxy', detail: `upper-case code "${c}"` });
  return out;
}

/* ─────────────────────────────── deck mode ─────────────────────────────── */

function splitRow(line) {
  const body = line.trim().replace(/^\|/, '').replace(/\|$/, '');
  return body.split(/(?<!\\)\|/).map((c) => c.trim());
}

/** Find the Copy deck section and its first table. Returns {rows, header} or null. */
function parseDeck(markdown) {
  const lines = markdown.replaceAll(/```[\s\S]*?```/g, '').split('\n');
  const start = lines.findIndex((l) => /^#{1,6}\s.*\bcopy deck\b/i.test(l));
  if (start === -1) return null;
  const level = (lines[start].match(/^#+/) ?? ['#'])[0].length;
  // Every table in the section, kept apart: a summary table above the deck is not the deck.
  const tables = [];
  let current = null;
  for (let i = start + 1; i < lines.length; i++) {
    const l = lines[i];
    const h = /^(#{1,6})\s/.exec(l);
    if (h && h[1].length <= level) break;
    if (!/^\s*\|/.test(l)) {
      current = null;
      continue;
    }
    const cells = splitRow(l);
    if (!current) {
      current = { header: cells.map((c) => c.toLowerCase()), rows: [] };
      tables.push(current);
      continue;
    }
    if (cells.every((c) => /^:?-{2,}:?$/.test(c))) continue;
    current.rows.push({ line: i + 1, cells });
  }
  const deck = tables.find((t) => columnIndex(t.header, ['ships as', 'replacement']) !== -1);
  return deck ?? tables[0] ?? { header: null, rows: [] };
}

function columnIndex(header, names) {
  return header ? header.findIndex((h) => names.some((n) => h.includes(n))) : -1;
}

function checkDeck(markdown) {
  const findings = [];
  const deck = parseDeck(markdown);
  if (!deck) {
    findings.push({ code: 'R1', severity: 'hard', detail: 'no "Copy deck" section' });
    return { findings, rows: 0 };
  }
  const ships = columnIndex(deck.header, ['ships as', 'replacement']);
  const screen = columnIndex(deck.header, ['screen']);
  if (ships < 0 || screen < 0) {
    findings.push({ code: 'R1', severity: 'hard', detail: 'the Copy deck table has no "Ships as" or no "Screen" column' });
    return { findings, rows: deck.rows.length };
  }
  if (deck.rows.length === 0) findings.push({ code: 'R1', severity: 'hard', detail: 'the Copy deck has no rows' });
  for (const r of deck.rows) {
    const where = `line ${r.line}`;
    const s = r.cells[ships] ?? '';
    const mark = r.cells[screen] ?? '';
    if (!s.trim()) findings.push({ code: 'R4', severity: 'hard', line: r.line, detail: `${where}: empty Ships-as string` });
    for (const part of ['a', 'b', 'c', 'd']) {
      const re = new RegExp(`(?:^|[^a-z])${part}\\s*([✓✔✗✘x])`, 'i');
      const m = re.exec(mark);
      if (!m) findings.push({ code: 'R2', severity: 'hard', line: r.line, detail: `${where}: part (${part}) not recorded` });
      else if (/[✗✘x]/i.test(m[1]))
        findings.push({ code: 'R3', severity: 'hard', line: r.line, detail: `${where}: part (${part}) failed — ${mark}` });
    }
    for (const f of screenString(s)) findings.push({ ...f, line: r.line, detail: `${where}: ${f.detail} — "${s}"` });
  }
  return { findings, rows: deck.rows.length };
}

function checkStrings(list) {
  const findings = [];
  for (const [i, s] of list.entries()) {
    for (const f of screenString(s)) findings.push({ ...f, line: i + 1, detail: `${f.detail} — "${s}"` });
  }
  return { findings, rows: list.length };
}

/* ─────────────────────────────────── CLI ────────────────────────────────── */

function main(argv) {
  const arg = (k) => {
    const i = argv.indexOf(k);
    return i === -1 ? undefined : argv[i + 1];
  };
  const json = argv.includes('--json');
  const strict = argv.includes('--strict');
  let result;
  if (arg('--deck')) result = checkDeck(fs.readFileSync(arg('--deck'), 'utf8'));
  else if (arg('--strings'))
    result = checkStrings(
      fs
        .readFileSync(arg('--strings'), 'utf8')
        .split('\n')
        .map((l) => l.trim())
        .filter((l) => l && !l.startsWith('#')),
    );
  else if (arg('--string') === undefined) {
    console.error('usage: check-copy-screen.js --deck <brief.md> | --strings <file> | --string "<text>" [--json] [--strict]');
    return 2;
  } else {
    result = checkStrings([arg('--string')]);
  }
  const hard = result.findings.filter((f) => f.severity === 'hard');
  if (json) console.log(JSON.stringify({ rows: result.rows, hard: hard.length, findings: result.findings }, null, 2));
  else {
    console.log(
      `copy-screen: ${result.rows} string(s) screened, ${hard.length} hard finding(s), ${result.findings.length - hard.length} proxy.`,
    );
    for (const f of result.findings) console.log(`  ${f.severity === 'hard' ? '✗' : '?'} ${f.code} ${f.detail}`);
  }
  return strict && hard.length > 0 ? 1 : 0;
}

if (require.main === module) process.exit(main(process.argv.slice(2)));

module.exports = { screenString, checkDeck, checkStrings, parseDeck, BANNED };
