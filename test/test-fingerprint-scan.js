/**
 * test-fingerprint-scan.js — regression suite for custom/scripts/design-fingerprint-scan.sh
 *
 * The scanner is the deterministic arm of design-standards.md § AI Fingerprint Detection
 * (see § Enforcement coverage). Both directions are pinned — a scanner that has only ever
 * been seen to fire is a scanner nobody has proven is quiet — plus the two honesty
 * properties Mason's 2026-08-24 spec made load-bearing:
 *
 *   F1  forbidden left-border card      -> exit 1, FINDING left-border-accent (both CSS and
 *                                          Tailwind forms of the construct)
 *   F2  declared exception (--allow)    -> exit 0, the match is still REPORTED as
 *                                          DECLARED-EXCEPTION (visibility survives the allow)
 *   F3  clean artifact                  -> exit 0, zero FINDING lines — and the output STILL
 *                                          carries the advisory list + the "NOT design
 *                                          compliance" line (zero matches is never compliance)
 *   F4  multi-fingerprint artifact      -> exit 1, distinct rules each fire exactly where
 *                                          expected (gradient, ai-purple, glassmorphism,
 *                                          shadow-heavy, hover-transform, uppercase-tracking)
 *   F5  advisory rule stays advisory    -> no FINDING line ever names a judgment-only row
 *                                          (e.g. stat cards / bento) — the scanner must not
 *                                          pretend to enforce what it cannot detect
 *
 * Fixtures live in test/fixtures/fingerprint-scan/ (committed — they double as the worked
 * examples the taxonomy row cites).
 *
 * Run: node test/test-fingerprint-scan.js   (wired as `npm run test:fingerprint-scan`)
 */

'use strict';
const assert = require('node:assert');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const SCANNER = path.join(__dirname, '..', 'custom', 'scripts', 'design-fingerprint-scan.sh');
const FIX = (name) => path.join(__dirname, 'fixtures', 'fingerprint-scan', name);

let pass = 0;
const failures = [];

function run(args) {
  const r = spawnSync('bash', [SCANNER, ...args], { encoding: 'utf8' });
  return { code: r.status, out: (r.stdout || '') + (r.stderr || '') };
}

function check(name, fn) {
  try {
    fn();
    pass += 1;
  } catch (error) {
    failures.push(`${name}: ${error.message}`);
  }
}

/* F1 — forbidden left-border card fails, both construct forms found */
check('F1 exit 1 on forbidden left-border card', () => {
  const { code, out } = run([FIX('forbidden-left-border.html')]);
  assert.strictEqual(code, 1, `expected exit 1, got ${code}\n${out}`);
  const hits = out.split('\n').filter((l) => l.startsWith('FINDING left-border-accent'));
  assert.ok(hits.length >= 2, `expected both CSS + Tailwind forms flagged, got:\n${out}`);
  assert.ok(/border-left: 3px solid/.test(out), 'CSS construct not quoted in finding');
  assert.ok(/border-l-4/.test(out), 'Tailwind construct not quoted in finding');
});

/* F2 — --allow downgrades to DECLARED-EXCEPTION but still reports */
check('F2 declared exception reported, not failed', () => {
  const { code, out } = run(['--allow', 'left-border-accent', FIX('declared-exception.html')]);
  assert.strictEqual(code, 0, `expected exit 0 with --allow, got ${code}\n${out}`);
  assert.ok(out.includes('DECLARED-EXCEPTION left-border-accent'), `allowed match must still be reported:\n${out}`);
  assert.ok(!/^FINDING /m.test(out), `no FINDING lines expected:\n${out}`);
});

/* F3 — clean artifact passes but is never called compliant */
check('F3 clean artifact: exit 0, advisory + non-compliance line present', () => {
  const { code, out } = run([FIX('clean.html')]);
  assert.strictEqual(code, 0, `expected exit 0, got ${code}\n${out}`);
  assert.ok(!/^FINDING /m.test(out), `no FINDING lines expected:\n${out}`);
  assert.ok(out.includes('ADVISORY'), 'advisory remainder must be named');
  assert.ok(out.includes('NOT design compliance'), 'the not-compliance disclaimer is load-bearing and must always print');
});

/* F4 — distinct rules fire on the multi-fingerprint fixture */
check('F4 multiple distinct rules fire', () => {
  const { code, out } = run([FIX('multi-fingerprint.html')]);
  assert.strictEqual(code, 1, `expected exit 1, got ${code}\n${out}`);
  for (const rule of ['gradient', 'ai-purple', 'glassmorphism', 'shadow-heavy', 'hover-transform', 'uppercase-tracking']) {
    assert.ok(new RegExp(`^FINDING ${rule} `, 'm').test(out), `rule ${rule} did not fire:\n${out}`);
  }
});

/* F5 — advisory-only rows never appear as FINDING rule ids */
check('F5 judgment rows are never emitted as deterministic findings', () => {
  const { out } = run([FIX('forbidden-left-border.html'), FIX('multi-fingerprint.html'), FIX('clean.html')]);
  const findingIds = new Set(
    out
      .split('\n')
      .filter((l) => l.startsWith('FINDING '))
      .map((l) => l.split(' ')[1]),
  );
  const deterministicIds = new Set([
    'left-border-accent',
    'gradient',
    'ai-purple',
    'shadow-heavy',
    'glassmorphism',
    'hover-transform',
    'uppercase-tracking',
  ]);
  for (const id of findingIds) {
    assert.ok(deterministicIds.has(id), `unexpected deterministic rule id: ${id}`);
  }
  assert.ok(out.includes('stat cards'), 'advisory list must name the judgment rows');
});

if (failures.length > 0) {
  console.error(`fingerprint-scan: ${pass} passed, ${failures.length} FAILED`);
  for (const f of failures) console.error(`  ✗ ${f}`);
  process.exit(1);
}
console.log(`fingerprint-scan: all ${pass} cases passed`);
