/**
 * check-commit-boundary.js  —  deterministic detector for the design-implement
 *                              COMMIT-BOUNDARY pass (step-02b §4e).
 *
 * Home of the rule: custom/workflows/implement/design-implement/steps/step-02b-regression-surface.md §4e
 * Golden cases:     custom/workflows/implement/design-implement/commit-boundary-golden-matrix.md
 *
 * WHY THIS EXISTS.
 * A design bundle can supply the CONTROLS of a consequential interaction while omitting its
 * LIFECYCLE, and every existing check passes it. On the cash-recovery `/listings` eBay publish
 * surface, "Preview what will be sent" and "Re-attempt publish" pointed at the same target around
 * an irreversible external write: there was no durable publish-attempt object, no states, no
 * evidence snapshot the operator had actually reviewed, no staleness rule, no idempotency, and no
 * single control that owned the write. UI-copy review could not see it — nothing was misworded.
 * The missing artifact was an interaction MODEL, and no gate asked for one.
 *
 * ── What IS and ISN'T deterministically checkable (enforcement-expert axis) ──
 *
 *  CHECKED — mode `--scan` (TRIGGER SIGNALS ONLY):
 *    S1  a WRITE-CLASS signal appears in the design source (outward write · durable mutation ·
 *        approval · binding/merge · retry). Any one hit ⇒ the pass FIRES.
 *    S2  a SUPPORT-CLASS signal (preview / "what will be sent" / dry-run / confirm-before)
 *        appears. Reported, and it fires the pass ONLY alongside an S1 hit — "pre-commit evidence
 *        review" is a support signal by definition, so on its own it is a read-only review surface,
 *        which is exactly the case this must not fire on.
 *
 *  CHECKED — mode `--check` (REQUIRED-FIELD PRESENCE ONLY):
 *    F1  a `commit_boundary:` record exists in the artifact
 *    F2  all nine required determinations are present, non-empty, and not a placeholder
 *        (`TBD` / `TODO` / `n/a` / `see design` / `responsive`-class non-answers)
 *    F3  `outcomes` carries all three of `success`, `failure`, `unknown`
 *
 *  NOT CHECKED, on purpose — and this is the important half:
 *    Whether the state model is CORRECT. Whether the states are the right states, the transitions
 *    legal, the evidence snapshot the one the operator actually saw, the idempotency key sound, or
 *    the named control the only thing that writes. None of that is textually decidable, and a
 *    checker that guessed at it would launder a judgement into a green tick. This tool proves a
 *    TRIGGER fired and a FIELD is present. The model is judged by a human at the §4e halt.
 *
 *  DIRECTION OF THE ERROR (deliberate). The WRITE-CLASS list is generous: a false fire costs one
 *  bounded pass, a miss costs the /listings failure. Three terms are deliberately LEFT OUT because
 *  they are furniture on read-only surfaces and would fire on nearly every page:
 *    · `cancel`       — dialog dismissal
 *    · `assigned to`  — a column header
 *    · `authorise/authorize` — ACCESS CONTROL vocabulary, not business approval. Measured
 *      2026-08-09 against four real cash-recovery surfaces: it fired on `/lineage`,
 *      `/raw-records` and `/ingestion-runs` — all read-only — from route comments reading
 *      "request-authorized and live-read". Three false fires, zero true ones. A business
 *      approval says "approve"; that is still matched.
 *    · `void`         — a TypeScript keyword before it is a business verb. Same measurement:
 *      every `() => void` prop signature on `/pricing` fired it. "Write off" and "finalise"
 *      still match.
 *  Those are ceded dimensions, stated rather than hidden.
 *
 * Usage:
 *   node tools/check-commit-boundary.js --scan <file-or-dir>... [--json] [--strict]
 *   node tools/check-commit-boundary.js --check <artifact.md>   [--json] [--strict]
 *
 * Exit: 0 always, unless --strict and findings exist (then 1). Bad usage: 2.
 */

'use strict';

const fs = require('node:fs');
const path = require('node:path');

/* ── Signals ── */

// WRITE-CLASS — any single hit fires the pass.
const WRITE_SIGNALS = [
  { code: 'outward-write', re: /\b(publish|unpublish|republish|submit|resubmit|transmit)\w*\b/i },
  { code: 'outward-write', re: /\b(send|post|push)\s+(it\s+)?to\b/i },
  { code: 'durable-mutation', re: /\b(finali[sz]e|write[- ]off)\w*\b/i },
  { code: 'approval', re: /\b(approve|approval|reject|decline|sign[- ]off)\w*\b/i },
  { code: 'binding-merge', re: /\b(merge|bind)\w*\b/i },
  { code: 'retry', re: /\b(retry|re-?attempt|resend|try\s+again)\w*\b/i },
];

// SUPPORT-CLASS — reported always; fires the pass only when a WRITE-CLASS signal is also present.
const SUPPORT_SIGNALS = [
  { code: 'pre-commit-evidence-review', re: /\bpreview\w*\b/i },
  { code: 'pre-commit-evidence-review', re: /\bwhat\s+will\s+be\s+(sent|submitted|published|written)\b/i },
  { code: 'pre-commit-evidence-review', re: /\bdry[- ]run\b/i },
  { code: 'pre-commit-evidence-review', re: /\bbefore\s+(you\s+)?(send|submit|publish|commit)\w*\b/i },
];

const SCANNABLE = new Set(['.html', '.htm', '.jsx', '.tsx', '.js', '.md', '.txt', '.css']);

/* ── Required determinations (mode --check) ── */

const REQUIRED_FIELDS = [
  ['durable_object', 'the durable object representing the attempted action'],
  ['states', 'its states'],
  ['transitions', 'the legal transitions between them'],
  ['evidence_snapshot', 'the exact evidence/payload snapshot the operator reviewed'],
  ['freshness', 'freshness / staleness conditions on that snapshot'],
  ['preconditions', 'preconditions for the irreversible transition'],
  ['outcomes', 'success, failure and unknown-external-outcome handling'],
  ['idempotency', 'duplicate-submit / idempotency and retry behaviour'],
  ['commit_control', 'the SOLE control that performs the irreversible write'],
];
const REQUIRED_OUTCOMES = ['success', 'failure', 'unknown'];
const PLACEHOLDER = /^(tbd|todo|t\.b\.d\.?|n\/?a|none|unknown|\?+|see\s+(the\s+)?(design|brief|bundle)|responsive)$/i;

/* ── CLI ── */

const argv = process.argv.slice(2);
const JSON_OUT = argv.includes('--json');
const STRICT = argv.includes('--strict');
const mode = argv.includes('--scan') ? 'scan' : argv.includes('--check') ? 'check' : null;
const targets = argv.filter((a) => !a.startsWith('--'));

if (!mode || targets.length === 0) {
  console.error('usage: check-commit-boundary.js --scan <file-or-dir>... | --check <artifact.md> [--json] [--strict]');
  process.exit(2);
}

const report = mode === 'scan' ? runScan(targets) : runCheck(targets[0]);
emit(report);
// `process.exitCode`, never `process.exit()`: an explicit exit tears the process down before a
// large stdout write to a PIPE has flushed. Observed 2026-08-09 — `--scan src/app/(owner)/staging
// --json | node` truncated a 65KB report mid-string and the consumer died on invalid JSON, which
// reads as a broken surface rather than a broken printer.
process.exitCode = STRICT && report.findings.length > 0 ? 1 : 0;

/* ── Mode: scan ── */

function runScan(roots) {
  const files = roots.flatMap((r) => collectFiles(r));
  const writeHits = [];
  const supportHits = [];

  for (const file of files) {
    let lines;
    try {
      lines = fs.readFileSync(file, 'utf8').split('\n');
    } catch {
      continue; // an unreadable input is not a signal; it is nothing
    }
    for (const [i, line] of lines.entries()) {
      for (const sig of WRITE_SIGNALS) {
        const m = line.match(sig.re);
        if (m) writeHits.push(hit(sig.code, file, i + 1, line, m[0]));
      }
      for (const sig of SUPPORT_SIGNALS) {
        const m = line.match(sig.re);
        if (m) supportHits.push(hit(sig.code, file, i + 1, line, m[0]));
      }
    }
  }

  const triggered = writeHits.length > 0;
  const findings = [];

  // NO-INPUT is its own verdict, never NOT-TRIGGERED. A bad path, an empty dir or a bundle whose
  // files are all unscannable would otherwise report a confident "no consequential interaction"
  // from having read nothing — the report-green-from-seeing-nothing anti-pattern this fork names
  // elsewhere. Seeing nothing is not evidence of absence.
  if (files.length === 0) {
    findings.push({
      code: 'CB-NO-INPUT',
      msg: 'no scannable file was read (bad path, empty directory, or no .html/.jsx/.tsx/.js/.md/.txt/.css content) — this is UNKNOWN, not "no consequential interaction"',
    });
  } else if (triggered) {
    findings.push({
      code: 'CB-TRIGGERED',
      msg:
        `commit-boundary pass FIRES — ${writeHits.length} write-class signal(s)` +
        `${supportHits.length > 0 ? ` + ${supportHits.length} pre-commit-review signal(s)` : ''}. ` +
        'step-02b §4e must determine the nine lifecycle facts before the grid is built.',
    });
  }

  return {
    mode: 'scan',
    files_scanned: files.length,
    triggered,
    trigger_classes: [...new Set(writeHits.map((h) => h.code))].sort(),
    write_hits: writeHits,
    support_hits: supportHits,
    findings,
    verdict: files.length === 0 ? 'NO-INPUT' : triggered ? 'TRIGGERED' : 'NOT-TRIGGERED',
  };
}

function collectFiles(root) {
  let stat;
  try {
    stat = fs.statSync(root);
  } catch {
    return [];
  }
  if (stat.isFile()) return [root];
  const out = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    if (entry.name.startsWith('.') || entry.name === 'node_modules') continue;
    const full = path.join(root, entry.name);
    if (entry.isDirectory()) out.push(...collectFiles(full));
    else if (SCANNABLE.has(path.extname(entry.name).toLowerCase())) out.push(full);
  }
  return out;
}

function hit(code, file, line, text, match) {
  return { code, file, line, match, sample: text.trim().slice(0, 120) };
}

/* ── Mode: check ── */

function runCheck(artifact) {
  const findings = [];
  let text;
  try {
    text = fs.readFileSync(artifact, 'utf8');
  } catch (error) {
    return {
      mode: 'check',
      artifact,
      present: false,
      findings: [{ code: 'F1-UNREADABLE', msg: error.message }],
      verdict: 'FINDINGS',
    };
  }

  const record = parseCommitBoundaryBlock(text);
  if (!record) {
    findings.push({
      code: 'F1-NO-RECORD',
      msg: 'no `commit_boundary:` record found — a triggered surface must carry one (step-02b §4e); a record that does not exist cannot be reviewed',
    });
    return { mode: 'check', artifact, present: false, fields_present: [], findings, verdict: 'FINDINGS' };
  }

  const present = [];
  for (const [field, meaning] of REQUIRED_FIELDS) {
    const value = record[field];
    if (value === undefined) {
      findings.push({ code: 'F2-MISSING', msg: `\`${field}\` is absent — ${meaning}` });
      continue;
    }
    if (isPlaceholder(value)) {
      findings.push({ code: 'F2-PLACEHOLDER', msg: `\`${field}\` is a placeholder (${JSON.stringify(flat(value))}) — ${meaning}` });
      continue;
    }
    present.push(field);
  }

  const outcomes = record.outcomes;
  if (outcomes !== undefined && !isPlaceholder(outcomes)) {
    for (const key of REQUIRED_OUTCOMES) {
      const sub = typeof outcomes === 'object' && !Array.isArray(outcomes) ? outcomes[key] : undefined;
      if (sub === undefined || isPlaceholder(sub)) {
        findings.push({
          code: 'F3-OUTCOME',
          msg: `\`outcomes.${key}\` is absent or a placeholder — an UNKNOWN external outcome is not the same as a failure, and both must be handled`,
        });
      }
    }
  }

  return {
    mode: 'check',
    artifact,
    present: true,
    fields_required: REQUIRED_FIELDS.length,
    fields_present: present,
    findings,
    verdict: findings.length > 0 ? 'FINDINGS' : 'FIELDS-PRESENT',
  };
}

/**
 * Parse the `commit_boundary:` block out of frontmatter or a fenced yaml block.
 * Deliberately a small indentation scanner, not a YAML engine: the tool checks PRESENCE, so
 * scalars, inline lists and one nesting level are all it needs — and a missing dependency is
 * one more way for a check to be silently absent.
 */
function parseCommitBoundaryBlock(text) {
  const lines = text.split('\n');
  const start = lines.findIndex((l) => /^\s*commit_boundary:\s*$/.test(l));
  if (start === -1) return null;
  const baseIndent = lines[start].match(/^\s*/)[0].length;

  const record = {};
  let currentKey = null;
  for (let i = start + 1; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim() === '') continue;
    if (/^(---|```)\s*$/.test(line.trim())) break;
    const indent = line.match(/^\s*/)[0].length;
    if (indent <= baseIndent) break;

    const kv = line.match(/^\s*([a-z_][a-z0-9_]*):\s*(.*)$/i);
    const item = line.match(/^\s*-\s+(.*)$/);

    if (kv && indent === baseIndent + 2) {
      currentKey = kv[1];
      record[currentKey] = kv[2].trim() === '' ? {} : kv[2].trim();
    } else if (currentKey && kv) {
      if (typeof record[currentKey] !== 'object' || Array.isArray(record[currentKey])) record[currentKey] = {};
      record[currentKey][kv[1]] = kv[2].trim();
    } else if (currentKey && item) {
      if (!Array.isArray(record[currentKey])) record[currentKey] = [];
      record[currentKey].push(item[1].trim());
    }
  }
  return record;
}

function isPlaceholder(value) {
  if (value === null || value === undefined) return true;
  if (Array.isArray(value)) return value.every((v) => isPlaceholder(v));
  if (typeof value === 'object') return Object.keys(value).length === 0;
  const s = String(value)
    .trim()
    .replaceAll(/^["']|["']$/g, '');
  return s === '' || PLACEHOLDER.test(s);
}

function flat(value) {
  if (Array.isArray(value)) return value.join(', ');
  if (value && typeof value === 'object') return Object.keys(value).join(', ');
  return String(value);
}

/* ── Report ── */

function emit(r) {
  if (JSON_OUT) {
    console.log(JSON.stringify(r, null, 2));
    return;
  }
  if (r.mode === 'scan') {
    console.log(`check-commit-boundary --scan: ${r.files_scanned} file(s)`);
    console.log(
      `  write-class signals   : ${r.write_hits.length}${r.trigger_classes.length > 0 ? ` [${r.trigger_classes.join(', ')}]` : ''}`,
    );
    console.log(`  pre-commit-review     : ${r.support_hits.length}`);
    for (const h of [...r.write_hits, ...r.support_hits].slice(0, 12)) {
      console.log(`    · ${h.code}  ${h.file}:${h.line}  "${h.match}"`);
    }
    console.log(`  verdict               : ${r.verdict}`);
    if (r.verdict === 'NO-INPUT') {
      console.log('  NOTE: nothing was read, so nothing is known. Do NOT record `Commit boundary: n/a`');
      console.log('        on the back of this — fix the path and re-run, or run the trigger test by hand.');
    } else if (r.verdict === 'NOT-TRIGGERED') {
      console.log('  NOTE: no write-class signal. A pre-commit-review signal ALONE does not fire the');
      console.log('        pass — that is a read-only review surface, the case this must not fire on.');
    } else {
      console.log('  NOTE: this proves a SIGNAL, not a defect. The pass may still conclude the design');
      console.log('        already models the boundary correctly — §4e judges that, this does not.');
    }
  } else {
    console.log(`check-commit-boundary --check: ${r.artifact}`);
    console.log(`  commit_boundary record: ${r.present ? 'present' : 'ABSENT'}`);
    if (r.present) console.log(`  required fields       : ${r.fields_present.length}/${r.fields_required} present`);
    console.log(`  verdict               : ${r.verdict}`);
    console.log('  NOTE: presence only. This tool cannot tell whether the state model is CORRECT —');
    console.log('        whether the states are the right states or the named control is the only writer.');
  }
  for (const f of r.findings) console.log(`    ✗ [${f.code}] ${f.msg}`);
}
