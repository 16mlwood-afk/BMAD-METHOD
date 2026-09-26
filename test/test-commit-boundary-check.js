/**
 * test-commit-boundary-check.js — regression suite for tools/check-commit-boundary.js
 *
 * The detector backs the design-implement step-02b §4e commit-boundary pass. Its whole value is
 * that it fires on the narrow case and stays silent everywhere else, so BOTH directions are pinned
 * here — a checker that has only ever been seen to fire is a checker nobody has proven is quiet.
 *
 * The two headline rows are the golden cases named in commit-boundary-golden-matrix.md:
 *   G1  read-only review surface        -> NOT-TRIGGERED   (the false-positive direction)
 *   G2  eBay preview/retry/shared write -> TRIGGERED       (the origin failure)
 * The remaining rows pin the --check field-presence mode, which is the other half of what a script
 * is allowed to decide.
 *
 * Fixtures are built inline in a temp dir rather than committed: they are small, and what is under
 * test is the RELATIONSHIP between the two signal classes, which reads better as one pair of
 * contrasting surfaces than as files on disk drifting away from the prose.
 *
 * Run: node test/test-commit-boundary-check.js   (wired as `npm run test:commit-boundary`)
 */

'use strict';
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const CHECKER = path.join(__dirname, '..', 'tools', 'check-commit-boundary.js');
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'commit-boundary-check-'));

let pass = 0;
const failures = [];

/* ── Fixtures ── */

/**
 * G1 — a read-only review surface. It carries review vocabulary ("Review", "Preview") and a
 * detail drawer, and writes nothing. This is the case the pass must NOT fire on: the whole
 * point of the write-class/support-class split.
 */
const READ_ONLY_REVIEW_SURFACE = `<!doctype html>
<main class="ingestion-runs">
  <h1>Ingestion runs</h1>
  <p>Review the records pulled in each run. This page is read-only.</p>
  <table>
    <thead><tr><th>Run</th><th>Started</th><th>Records</th><th>Status</th></tr></thead>
    <tbody>
      <tr><td>run-8814</td><td>2026-08-04 09:12</td><td>1,204</td><td>Complete</td></tr>
      <tr><td>run-8815</td><td>2026-08-05 09:12</td><td>977</td><td>Partial</td></tr>
    </tbody>
  </table>
  <button data-action="open-detail">Open run detail</button>
  <button data-action="preview-records">Preview records</button>
  <button data-action="export">Export CSV</button>
  <aside class="drawer"><h2>Run detail</h2><p>Records, timings and the raw report header.</p></aside>
</main>
`;

/**
 * G2 — the origin failure, reduced: a publish frame whose preview and retry controls both point at
 * the same irreversible external write, with no lifecycle anywhere in the bundle.
 */
const EBAY_PUBLISH_FRAME = `<!doctype html>
<main class="listing-publish">
  <h1>Listing — Krups EA8108</h1>
  <section class="payload"><h2>What will be sent</h2><p>Title, aspects, photos, price.</p></section>
  <button data-target="publish">Preview what will be sent</button>
  <button data-target="publish">Publish to eBay</button>
  <button data-target="publish">Re-attempt publish</button>
  <p class="hint">Publishing sends this listing to eBay.</p>
</main>
`;

const COMPLETE_RECORD = `---
type: design-implement-preflight
target_slug: listings-publish
commit_boundary:
  triggered_by: [outward-write, retry]
  durable_object: publish_attempt
  states: [prepared, submitted, succeeded, failed, unknown_outcome]
  transitions: prepared to submitted via the commit control only; submitted to succeeded/failed/unknown_outcome
  evidence_snapshot: the payload rendered in Preview, stored on the attempt at commit time
  freshness: invalid if price, photos or aspects changed since capture
  preconditions: aspects complete, photos committed, account armed, no open attempt
  outcomes:
    success: listing id stored, publish control disabled for that unit
    failure: eBay error surfaced verbatim, retry permitted under a new attempt id
    unknown: reconcile read before any retry, never auto-resend
  idempotency: one attempt per (unit, payload hash); duplicate submit refused
  commit_control: the "Publish to eBay" button only
---

# Preflight
`;

/* ── Harness ── */

function write(name, body) {
  const p = path.join(TMP, name);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, body);
  return p;
}

function run(args) {
  const out = execFileSync('node', [CHECKER, ...args, '--json'], { encoding: 'utf8' });
  return JSON.parse(out);
}

function check(label, fn) {
  try {
    fn();
    console.log(`  PASS  ${label}`);
    pass++;
  } catch (error) {
    console.log(`  FAIL  ${label}  ${error.message}`);
    failures.push(label);
  }
}

console.log('check-commit-boundary golden cases:\n');

/* ── G1: read-only review surface must NOT trigger ── */

check('G1-read-only-review-surface-does-not-trigger', () => {
  const file = write('g1/ingestion-runs.html', READ_ONLY_REVIEW_SURFACE);
  const r = run(['--scan', file]);
  assert.strictEqual(r.verdict, 'NOT-TRIGGERED', `expected NOT-TRIGGERED, got ${r.verdict}`);
  assert.strictEqual(r.write_hits.length, 0, `expected 0 write-class hits, got ${JSON.stringify(r.write_hits)}`);
  assert.ok(r.support_hits.length > 0, 'expected the "Preview" support signal to be REPORTED, not suppressed');
});

/* ── G2: the eBay preview/retry/shared-write-path failure must trigger ── */

check('G2-ebay-publish-preview-retry-triggers', () => {
  const file = write('g2/listing-publish.html', EBAY_PUBLISH_FRAME);
  const r = run(['--scan', file]);
  assert.strictEqual(r.verdict, 'TRIGGERED', `expected TRIGGERED, got ${r.verdict}`);
  assert.ok(r.trigger_classes.includes('outward-write'), `expected outward-write, got ${r.trigger_classes}`);
  assert.ok(r.trigger_classes.includes('retry'), `expected retry, got ${r.trigger_classes}`);
  assert.ok(r.support_hits.length > 0, 'expected the pre-commit-review signal alongside the write signals');
});

/* ── Access-control vocabulary is not a business approval ── */

check('G11-auth-guarded-read-only-page-does-not-trigger', () => {
  const file = write(
    'g11/lineage-page.tsx',
    [
      '/**',
      ' * `force-dynamic`: request-authorized and live-read, never statically prerendered.',
      ' */',
      'type Props = { onLookup: () => void }; // `void` is a TS keyword, not a business verb',
      'export default async function LineagePage() {',
      '  const session = await requireSession(); // unauthorized users are redirected',
      '  return <LineageTable rows={await readLineage()} />;',
      '}',
    ].join('\n'),
  );
  const r = run(['--scan', file]);
  assert.strictEqual(r.verdict, 'NOT-TRIGGERED', `expected NOT-TRIGGERED, got ${r.verdict} on ${JSON.stringify(r.write_hits)}`);
});

/* ── An empty/bad input is UNKNOWN, never "no consequential interaction" ── */

check('G10-empty-input-reports-NO-INPUT-not-NOT-TRIGGERED', () => {
  const r = run(['--scan', path.join(TMP, 'does-not-exist')]);
  assert.strictEqual(r.verdict, 'NO-INPUT', `expected NO-INPUT, got ${r.verdict}`);
  assert.strictEqual(r.files_scanned, 0);
  assert.ok(
    r.findings.some((f) => f.code === 'CB-NO-INPUT'),
    'a checker that reports green from seeing nothing protects nothing',
  );
});

/* ── --check: a triggered surface with no record, a partial record, and a complete one ── */

check('G3-missing-record-is-a-finding', () => {
  const file = write('g3/preflight.md', '---\ntype: design-implement-preflight\n---\n\n# no record here\n');
  const r = run(['--check', file]);
  assert.strictEqual(r.present, false);
  assert.strictEqual(r.findings[0].code, 'F1-NO-RECORD');
});

check('G4-partial-record-names-each-absent-field', () => {
  const partial = COMPLETE_RECORD.replace(/ {2}idempotency:.*\n/, '').replace(/ {2}freshness:.*\n/, '');
  const r = run(['--check', write('g4/preflight.md', partial)]);
  const missing = r.findings.filter((f) => f.code === 'F2-MISSING').map((f) => f.msg);
  assert.strictEqual(missing.length, 2, `expected 2 missing fields, got ${JSON.stringify(r.findings)}`);
  assert.ok(missing.some((m) => m.includes('freshness')));
  assert.ok(missing.some((m) => m.includes('idempotency')));
});

check('G5-placeholder-is-not-an-answer', () => {
  const placeheld = COMPLETE_RECORD.replace(/ {2}idempotency:.*\n/, '  idempotency: TBD\n');
  const r = run(['--check', write('g5/preflight.md', placeheld)]);
  assert.ok(
    r.findings.some((f) => f.code === 'F2-PLACEHOLDER' && f.msg.includes('idempotency')),
    `expected an idempotency placeholder finding, got ${JSON.stringify(r.findings)}`,
  );
});

check('G6-unknown-outcome-must-be-handled-separately', () => {
  const noUnknown = COMPLETE_RECORD.replace(/ {4}unknown:.*\n/, '');
  const r = run(['--check', write('g6/preflight.md', noUnknown)]);
  assert.ok(
    r.findings.some((f) => f.code === 'F3-OUTCOME' && f.msg.includes('outcomes.unknown')),
    `expected an outcomes.unknown finding, got ${JSON.stringify(r.findings)}`,
  );
});

check('G7-complete-record-passes-clean', () => {
  const r = run(['--check', write('g7/preflight.md', COMPLETE_RECORD)]);
  assert.strictEqual(r.verdict, 'FIELDS-PRESENT', `expected FIELDS-PRESENT, got ${JSON.stringify(r.findings)}`);
  assert.strictEqual(r.fields_present.length, 9, `expected 9 fields, got ${r.fields_present.length}`);
});

/* ── Warn-only default must not exit non-zero, so the tool is safe to run anywhere. ── */

check('G8-warn-only-does-not-exit-nonzero', () => {
  const file = write('g8/listing-publish.html', EBAY_PUBLISH_FRAME);
  execFileSync('node', [CHECKER, '--scan', file], { encoding: 'utf8' }); // throws on non-zero exit
});

check('G12-large-json-report-survives-a-pipe', () => {
  // An explicit process.exit() truncates a >64KB stdout write to a pipe; the consumer then dies on
  // invalid JSON and it reads as a broken surface rather than a broken printer.
  const dir = path.join(TMP, 'g12');
  for (let i = 0; i < 60; i++) write(`g12/frame-${i}.html`, EBAY_PUBLISH_FRAME);
  const raw = execFileSync('node', [CHECKER, '--scan', dir, '--json'], { encoding: 'utf8' });
  assert.ok(raw.length > 65_536, `fixture too small to exercise the flush (${raw.length} bytes)`);
  const r = JSON.parse(raw); // throws if truncated
  assert.strictEqual(r.verdict, 'TRIGGERED');
});

check('G9-strict-exits-nonzero-on-findings', () => {
  const file = write('g9/listing-publish.html', EBAY_PUBLISH_FRAME);
  let exit = 0;
  try {
    execFileSync('node', [CHECKER, '--scan', file, '--strict'], { encoding: 'utf8', stdio: 'pipe' });
  } catch (error) {
    exit = error.status;
  }
  assert.strictEqual(exit, 1, `expected exit 1 under --strict, got ${exit}`);
});

fs.rmSync(TMP, { recursive: true, force: true });

console.log(`\n${pass} passed, ${failures.length} failed`);
if (failures.length > 0) {
  console.error(`FAILED: ${failures.join(', ')}`);
  process.exit(1);
}
console.log('check-commit-boundary: both directions pinned (quiet on read-only, fires on the shared write path).');
