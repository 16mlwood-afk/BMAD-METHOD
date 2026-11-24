/**
 * check-design-sendback.js  —  deterministic checker for the design-implement
 *                              DEPARTURE / SENDBACK contract (step-04 §5c).
 *
 * Home of the rule: custom/workflows/implement/design-implement/workflow.md
 *                     Critical Rule "Claude Design is the source of truth for design"
 *                   custom/workflows/implement/design-implement/steps/step-04-apply-and-deliver.md §5c
 * Artefact contract: custom/workflows/implement/design-implement/sendback-template.md
 *
 * WHY THIS EXISTS.
 * Owner ruling 2026-09-26, verbatim: "u cherry picked from the design... this is very bad practice...
 * claude design is the source of truth for design never do this again... if you wish to perform a
 * SENDBACK/debate/ask any design Q's make this kind of SENDBACK formal okay?? so the iterative loop
 * is between u two."
 *
 * The failure was NOT concealment, and that is the whole reason a checker is worth writing. The two
 * mapping-queue apply ledgers that produced the ruling disclosed every departure at length — one
 * headed a section "Section labels — v15 wins over the design, and it is logged", another listed
 * "Where v15 beat the design" as a numbered achievement, a third kept a candidate-score treatment
 * because "the implementation beats the design ... Keeping ours". Every word was true. What was
 * wrong is that a well-documented unilateral decision closed as a legitimate outcome. So a check
 * for MISSING disclosure would have passed both runs. This checks for the missing RETURN LEG.
 *
 * ── What IS and ISN'T deterministically checkable (enforcement-expert axis) ──
 *
 *  CHECKED — mode `--check <ledger.md>` (a design-implement apply ledger / grid artifact):
 *    D1  a row disposed `⊘ departure(...)` / `⊘ interim(...)` carries NO `sendback:` reference
 *    D2  a VERDICT VERB appears in prose ("policy wins", "wins over the design", "beats the
 *        design", "keeping ours", ...) — banned as a disposition or heading, because the verdict
 *        belongs to the designer
 *    D3  a cited `sendback:<path>` does not exist on disk
 *    D4  a cited `#ask-N` does not resolve to a numbered ask in that sendback
 *    D5  the sendback's frontmatter `departures:` disagrees with the number of rows citing it
 *
 *  CHECKED — mode `--sendback <file.md>` (the artefact itself):
 *    S1  a required section (1-7) is absent            S4  a required frontmatter key is absent
 *    S2  the sections are out of order                 S5  frontmatter `asks:` != numbered asks in §4
 *    S3  an ask offers no second shape (PROXY — see below)
 *    S6  a required section has no body at all (an omitted section and an empty one read
 *        identically and mean opposite things — "None - ..." is the correct empty form)
 *    S7  a numbered section's heading does not look like the section it occupies (PROXY)
 *
 *  NOT CHECKED, on purpose — and this is the important half:
 *    Whether a departure was CORRECTLY CLASSIFIED. Whether the thing the run did instead of the
 *    design was reasonable. Whether an ask is the RIGHT ask, whether its two shapes are genuinely
 *    acceptable, whether §3 located the real cause, or whether the designer would agree with any
 *    of it. None of that is textually decidable, and a checker that guessed would launder a
 *    judgement into a green tick. This proves a REFERENCE EXISTS and a SECTION IS PRESENT. The
 *    substance is judged by the designer, which is the entire point of the artefact.
 *
 *    It also cannot see a departure that was never recorded as one. A run that silently matched
 *    its own taste and wrote `✓ applied` is invisible here — that half is the workflow prose, and
 *    §5c says so rather than letting this tool imply coverage it does not have.
 *
 *  TWO PROXIES, LABELLED AS SUCH (S3, S7). "Does this ask offer a real alternative?" is a
 *  judgement; what is decidable is whether the ask's text contains any choice marker at all
 *  ("two shapes", "or", "either", "your call"). An ask with none is very likely a specification
 *  wearing a question mark — the failure §5c names in the other direction — but a well-written ask
 *  could phrase its alternatives without those words. Both are reported at `proxy` severity and
 *  are NOT counted as hard findings under --strict, so neither can block on a guess.
 *
 *  DIRECTION OF THE ERROR (deliberate). D2's verb list is SHORT and phrase-anchored rather than
 *  generous, the opposite calibration from check-commit-boundary.js's write-class list — because
 *  here a false fire lands on prose a human wrote deliberately, and the observed failures all used
 *  one of a handful of phrasings. Bare "wins" / "better" / "beats" are NOT matched: "the render
 *  wins the tie-break", "a better contrast ratio" and "beats the previous pass" are ordinary
 *  sentences. Fenced blocks and blockquotes are STRIPPED before scanning, so an artefact that
 *  quotes the ruling (or this file's own rule) stays silent — the same discipline as
 *  delegation-card-guard.py.
 *
 * Usage:
 *   node tools/check-design-sendback.js --check    <ledger.md>    [--json] [--strict]
 *   node tools/check-design-sendback.js --sendback <sendback.md>  [--json] [--strict]
 *
 * Exit: 0 always, unless --strict and hard findings exist (then 1). Bad usage: 2.
 */

'use strict';

const fs = require('node:fs');
const path = require('node:path');

/* ─────────────────────────── contract constants ─────────────────────────── */

/** The seven required sendback sections, in order. `any` = keyword alternatives for the S7 proxy. */
const REQUIRED_SECTIONS = [
  { n: 1, label: 'What the design got right, and the next version keeps', any: ['got right', 'keeps', 'keep', 'carried forward'] },
  { n: 2, label: 'Why it did not fully ship', any: ['did not ship', "didn't ship", 'did not fully', 'why it did not', 'not shipped'] },
  { n: 3, label: 'Why it happened, and where the gap was OURS', any: ['why it happened', 'ours', 'our gap', 'the gap was', 'gap in what'] },
  { n: 4, label: 'The asks', any: ['ask'] },
  { n: 5, label: "Questions that are the OWNER's", any: ['owner'] },
  { n: 6, label: 'Already settled — do not spend this round on these', any: ['settled'] },
  { n: 7, label: 'Not for this round — for the next brief', any: ['not for this round', 'next brief', 'next round'] },
];

const REQUIRED_FRONTMATTER = [
  'type',
  'target_slug',
  'responds_to',
  'ledger',
  'baseline_commit',
  'date',
  'departures',
  'asks',
  'owner_questions',
];

/**
 * Verdict verbs — phrase-anchored, deliberately short. Each was observed in a real ledger.
 * A verdict is the designer's to give; an implementer writing one has taken the decision.
 */
const VERDICT_VERBS = [
  /policy\s+wins/i,
  /\bwins?\s+over\s+the\s+design\b/i,
  /\bbeats?\s+the\s+design\b/i,
  /\bbeat\s+the\s+design\b/i,
  /\bkeeping\s+ours\b/i,
  /\bours\s+is\s+kept\s+over\s+the\s+design\b/i,
  /\bv\d+\s+wins\b/i,
  /\bwhere\s+v\d+\s+beat\s+the\s+design\b/i,
];

/** A departure-class disposition. `⊘ departure(...)` or `⊘ interim(...)`. */
const DEPARTURE_ROW = /⊘\s*(departure|interim)\s*\(/i;
/** A sendback citation: `sendback:<path>#ask-<N>` (the `#ask-N` half is optional at match time). */
const SENDBACK_CITE = /sendback:\s*([^\s|)#]+)(?:#ask-(\d+))?/gi;

/* ─────────────────────────────── helpers ────────────────────────────────── */

/**
 * Strip fenced code blocks and blockquote lines. An artefact discussing the rule — quoting the
 * owner, reproducing a banned phrase to forbid it — must not fire D2 on its own documentation.
 */
function stripQuoted(text) {
  const out = [];
  let fenced = false;
  for (const line of text.split('\n')) {
    if (/^\s*(```|~~~)/.test(line)) {
      fenced = !fenced;
      out.push('');
      continue;
    }
    if (fenced) {
      out.push('');
      continue;
    }
    if (/^\s*>/.test(line)) {
      out.push('');
      continue;
    }
    out.push(line);
  }
  return out.join('\n');
}

/** Flat YAML frontmatter -> object. Only the scalar keys this contract uses. */
function frontmatter(text) {
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return null;
  const obj = {};
  for (const line of m[1].split('\n')) {
    const kv = line.match(/^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$/);
    if (!kv) continue;
    let v = kv[2].trim().replaceAll(/^["']|["']$/g, '');
    obj[kv[1]] = v;
  }
  return obj;
}

/** Numbered markdown headings -> [{ n, title, line, body }]. Any heading level. */
function numberedSections(text) {
  const lines = text.split('\n');
  const found = [];
  for (const [i, line] of lines.entries()) {
    const m = line.match(/^#{1,6}\s+(\d+)[.)]\s+(.*)$/);
    if (m) found.push({ n: Number(m[1]), title: m[2].trim(), line: i + 1, start: i + 1 });
  }
  for (const [i, s] of found.entries()) {
    const end = i + 1 < found.length ? found[i + 1].start - 1 : lines.length;
    s.body = lines.slice(s.start, end).join('\n').trim();
  }
  return found;
}

/** Numbered asks inside a §4 body: `### Ask 3 — ...`, `**Ask 3**`, or `3. ...`. */
function asksIn(body) {
  const nums = new Set();
  for (const line of body.split('\n')) {
    let m = line.match(/^#{1,6}\s*\**\s*Ask\s+(\d+)/i) || line.match(/^\s*\**\s*Ask\s+(\d+)\s*\**\s*[—\-:]/i);
    if (m) {
      nums.add(Number(m[1]));
      continue;
    }
    m = line.match(/^\s{0,3}(\d+)[.)]\s+\S/);
    if (m) nums.add(Number(m[1]));
  }
  return [...nums].sort((a, b) => a - b);
}

const CHOICE_MARKERS = [
  /two\s+shapes/i,
  /either\b/i,
  /\bor\b/i,
  /your\s+call/i,
  /the\s+choice\s+is\s+yours/i,
  /any\s+shape/i,
  /a\s+third\s+shape/i,
  /up\s+to\s+you/i,
];

function read(file) {
  try {
    return fs.readFileSync(file, 'utf8');
  } catch {
    return null;
  }
}

/* ────────────────────────────── mode: --check ───────────────────────────── */

function checkLedger(file) {
  const findings = [];
  const raw = read(file);
  if (raw === null) return [{ code: 'IO', severity: 'hard', line: 0, message: `cannot read ${file}` }];

  const scrubbed = stripQuoted(raw);
  const lines = scrubbed.split('\n');
  const dir = path.dirname(path.resolve(file));

  /** sendback path -> how many rows cite it (for D5) */
  const citeCounts = new Map();
  /** resolved sendback path -> its parsed asks (lazy) */
  const sendbackAsks = new Map();

  function resolveSendback(p) {
    const candidates = [path.resolve(dir, p), path.resolve(p), path.resolve(dir, path.basename(p))];
    return candidates.find((c) => fs.existsSync(c)) || null;
  }

  for (const [i, line] of lines.entries()) {
    const lineNo = i + 1;

    /* D1 — a departure-class row with no sendback reference on it. */
    if (DEPARTURE_ROW.test(line)) {
      const cites = [...line.matchAll(SENDBACK_CITE)];
      if (cites.length === 0) {
        findings.push({
          code: 'D1-DEPARTURE-NO-SENDBACK',
          severity: 'hard',
          line: lineNo,
          message:
            'departure-class disposition with no `sendback:<file>#ask-N` reference. A reason alone is not a legal disposition for a departure (step-04 §5c).',
        });
      }
      for (const c of cites) {
        const p = c[1];
        citeCounts.set(p, (citeCounts.get(p) || 0) + 1);
        const resolved = resolveSendback(p);
        if (!resolved) {
          findings.push({
            code: 'D3-SENDBACK-MISSING',
            severity: 'hard',
            line: lineNo,
            message: `row cites sendback \`${p}\` and no such file exists (looked relative to the ledger and as given).`,
          });
          continue;
        }
        if (c[2] !== undefined) {
          if (!sendbackAsks.has(resolved)) {
            const sbRaw = read(resolved) || '';
            const s4 = numberedSections(sbRaw).find((s) => s.n === 4);
            sendbackAsks.set(resolved, s4 ? asksIn(s4.body) : []);
          }
          const known = sendbackAsks.get(resolved);
          if (!known.includes(Number(c[2]))) {
            findings.push({
              code: 'D4-ASK-UNRESOLVED',
              severity: 'hard',
              line: lineNo,
              message: `row cites #ask-${c[2]} and ${path.basename(resolved)} §4 carries asks [${known.join(', ') || 'none'}].`,
            });
          }
        }
      }
    }

    /* D2 — a verdict verb. Banned as a disposition or heading; the verdict is the designer's. */
    for (const re of VERDICT_VERBS) {
      if (re.test(line)) {
        findings.push({
          code: 'D2-VERDICT-VERB',
          severity: 'hard',
          line: lineNo,
          message: `verdict verb ${re} — an implementer may not issue a verdict over the design. Write the interim behaviour and a sendback ask instead (step-04 §5c).`,
        });
        break;
      }
    }
  }

  /* D5 — the two records must agree on how many departures the sendback answers for. */
  for (const [p, count] of citeCounts) {
    const resolved = resolveSendback(p);
    if (!resolved) continue;
    const fm = frontmatter(read(resolved) || '');
    if (!fm || fm.departures === undefined) continue;
    const declared = Number(fm.departures);
    if (Number.isFinite(declared) && declared !== count) {
      findings.push({
        code: 'D5-COUNT-MISMATCH',
        severity: 'hard',
        line: 0,
        message: `${path.basename(resolved)} declares \`departures: ${declared}\` and ${count} ledger row(s) cite it. A sendback answering for fewer rows than the ledger raised leaves a departure standing on the implementer's own authority.`,
      });
    }
  }

  return findings;
}

/* ───────────────────────────── mode: --sendback ─────────────────────────── */

function checkSendback(file) {
  const findings = [];
  const raw = read(file);
  if (raw === null) return [{ code: 'IO', severity: 'hard', line: 0, message: `cannot read ${file}` }];

  /* S4 — frontmatter. */
  const fm = frontmatter(raw);
  if (fm) {
    for (const key of REQUIRED_FRONTMATTER) {
      if (fm[key] === undefined || fm[key] === '') {
        findings.push({
          code: 'S4-FRONTMATTER-MISSING',
          severity: 'hard',
          line: 1,
          message: `frontmatter key \`${key}\` absent or empty (sendback-template.md).`,
        });
      }
    }
    if (fm.type !== undefined && fm.type !== 'design-sendback') {
      findings.push({
        code: 'S4-FRONTMATTER-MISSING',
        severity: 'hard',
        line: 1,
        message: `frontmatter \`type\` is "${fm.type}", expected "design-sendback".`,
      });
    }
  } else {
    findings.push({ code: 'S4-FRONTMATTER-MISSING', severity: 'hard', line: 1, message: 'no YAML frontmatter block.' });
  }

  /* S1 / S2 / S6 / S7 — the seven sections. */
  const sections = numberedSections(raw).filter((s) => s.n >= 1 && s.n <= 7);
  const seen = new Map();
  for (const s of sections) if (!seen.has(s.n)) seen.set(s.n, s);

  for (const req of REQUIRED_SECTIONS) {
    const s = seen.get(req.n);
    if (!s) {
      findings.push({
        code: 'S1-MISSING-SECTION',
        severity: 'hard',
        line: 0,
        message: `section ${req.n} absent — "${req.label}". All seven are required; the empty case is stated ("None — …"), never omitted.`,
      });
      continue;
    }
    if (!s.body || s.body.length < 3) {
      findings.push({
        code: 'S6-EMPTY-SECTION',
        severity: 'hard',
        line: s.line,
        message: `section ${req.n} has no body. An omitted section and an empty one read identically and mean opposite things — state "None — …".`,
      });
    }
    const hay = `${s.title} ${s.body}`.toLowerCase();
    if (!req.any.some((k) => hay.includes(k))) {
      findings.push({
        code: 'S7-SECTION-MISLABELLED',
        severity: 'proxy',
        line: s.line,
        message: `section ${req.n} reads "${s.title}" — expected something about "${req.label}". PROXY: keyword match, not a judgement about the content.`,
      });
    }
  }

  const order = sections.map((s) => s.n);
  const ascending = order.every((n, i) => i === 0 || n >= order[i - 1]);
  if (!ascending) {
    findings.push({
      code: 'S2-SECTION-ORDER',
      severity: 'hard',
      line: 0,
      message: `sections appear as [${order.join(', ')}] — the contract order is 1-7 (sendback-template.md).`,
    });
  }

  /* S5 / S3 — the asks. */
  const s4 = seen.get(4);
  if (s4) {
    const asks = asksIn(s4.body);
    if (fm && fm.asks !== undefined && Number.isFinite(Number(fm.asks)) && Number(fm.asks) !== asks.length) {
      findings.push({
        code: 'S5-ASKS-COUNT-MISMATCH',
        severity: 'hard',
        line: s4.line,
        message: `frontmatter \`asks: ${fm.asks}\` and §4 carries ${asks.length} numbered ask(s) [${asks.join(', ') || 'none'}].`,
      });
    }
    /* S3 — per-ask second-shape proxy. Split §4's body at each ask boundary. */
    const askLines = s4.body.split('\n');
    const bounds = [];
    for (const [i, line] of askLines.entries()) {
      if (/^#{1,6}\s*\**\s*Ask\s+\d+/i.test(line) || /^\s*\**\s*Ask\s+\d+\s*\**\s*[—\-:]/i.test(line) || /^\s{0,3}\d+[.)]\s+\S/.test(line))
        bounds.push(i);
    }
    for (const [i, start] of bounds.entries()) {
      const end = i + 1 < bounds.length ? bounds[i + 1] : askLines.length;
      const chunk = askLines.slice(start, end).join('\n');
      if (!CHOICE_MARKERS.some((re) => re.test(chunk))) {
        findings.push({
          code: 'S3-ASK-SINGLE-SHAPE',
          severity: 'proxy',
          line: s4.line + start,
          message:
            'ask offers no visible second shape — an ask with exactly one acceptable shape is a specification wearing a question mark (step-04 §5c). PROXY: choice-marker scan, not a judgement.',
        });
      }
    }
  }

  return findings;
}

/* ───────────────────────────────── CLI ──────────────────────────────────── */

function main(argv) {
  const json = argv.includes('--json');
  const strict = argv.includes('--strict');
  const modeIdx = argv.findIndex((a) => a === '--check' || a === '--sendback');
  if (modeIdx === -1 || !argv[modeIdx + 1]) {
    process.stderr.write('usage: check-design-sendback.js --check <ledger.md> | --sendback <sendback.md> [--json] [--strict]\n');
    return 2;
  }
  const mode = argv[modeIdx];
  const file = argv[modeIdx + 1];
  const findings = mode === '--check' ? checkLedger(file) : checkSendback(file);
  const hard = findings.filter((f) => f.severity === 'hard');
  const proxy = findings.filter((f) => f.severity === 'proxy');

  if (json) {
    process.stdout.write(`${JSON.stringify({ mode, file, verdict: hard.length > 0 ? 'findings' : 'consistent', hard, proxy }, null, 2)}\n`);
  } else if (findings.length === 0) {
    process.stdout.write(`consistent — ${file}\n`);
  } else {
    process.stdout.write(`${hard.length} finding(s)${proxy.length > 0 ? ` + ${proxy.length} proxy` : ''} — ${file}\n`);
    for (const f of [...hard, ...proxy]) {
      process.stdout.write(`  ${f.severity === 'proxy' ? '~' : '✗'} ${f.code}${f.line ? ` (line ${f.line})` : ''}: ${f.message}\n`);
    }
    if (hard.length === 0)
      process.stdout.write('  (proxy findings only — these are keyword scans, never a judgement; --strict does not fail on them)\n');
  }
  return strict && hard.length > 0 ? 1 : 0;
}

if (require.main === module) process.exit(main(process.argv.slice(2)));

module.exports = { checkLedger, checkSendback, stripQuoted, numberedSections, asksIn, frontmatter };
