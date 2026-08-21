/**
 * Golden suite for check-ingest-manifest.js — the 2026-08-21 additions.
 *
 * Most cases assert SILENCE. A checker that fires on a legitimate manifest is one that gets
 * switched off, taking every real finding with it, so the cases that prove it stays quiet
 * carry as much weight as the cases that prove it fires.
 *
 * Plain node, no deps, no vitest: these tools must run when the dep tree is broken, which is
 * exactly when someone is debugging a gate.
 */
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const TOOL = join(dirname(fileURLToPath(import.meta.url)), 'check-ingest-manifest.js');
const dir = mkdtempSync(join(tmpdir(), 'ingest-check-'));
let pass = 0;
const failures = [];

/** A minimal manifest that is CONSISTENT — the baseline every case perturbs. */
function manifest({ grain = 'summary', drawn = 'true', sections = true, grid = true } = {}) {
  const inv = sections ? '### Frame: alpha (2 sections)\n\n- Header\n- Body\n' : '';
  const rows = grid
    ? '| frame | section | copy | data | props | status |\n|---|---|---|---|---|---|\n' +
      '| alpha | Header | h | - | x | UNVERIFIED |\n| alpha | Body | b | - | y | UNVERIFIED |\n'
    : '';
  return `---
ingest:
  target_slug: alpha
  manifest_grain: ${grain}
  completeness:
    frames_total: 1
    frames_drawn: 1
    sections_total: 2
    sections_per_frame:
      alpha: 2
    frames_with_empty_section_list: []
    sections_missing_property_rows: []
---

## Frame inventory

| frame | role | parent | declared_in | drawn | bytes | sections |
|---|---|---|---|---|---|---|
| alpha | primary | — | target | ${drawn} | 100 | 2 |

## Section inventory

${inv}

## Grid scaffold

${rows}
`;
}

let caseNo = 0;
function run(name, body, expect) {
  /* NEUTRAL FILENAME, deliberately. Deriving it from the test name put the string "C14" into
   * the path, which the tool prints — so every `absent: ['C14']` case matched its own
   * filename and failed. A probe that matches itself measures nothing. */
  const f = join(dir, `case-${++caseNo}.md`);
  writeFileSync(f, body);
  let out = '',
    code = 0;
  try {
    out = execFileSync('node', [TOOL, '--manifest', f, '--strict'], { encoding: 'utf8' });
  } catch (error) {
    out = (error.stdout ?? '') + (error.stderr ?? '');
    code = error.status;
  }
  const problems = [];
  if (expect.exit !== undefined && code !== expect.exit) problems.push(`exit ${code}, wanted ${expect.exit}`);
  for (const t of expect.contains ?? []) if (!out.includes(t)) problems.push(`missing: ${t}`);
  for (const t of expect.absent ?? []) if (out.includes(t)) problems.push(`should NOT contain: ${t}`);
  if (problems.length > 0) failures.push(`${name}\n    ${problems.join('\n    ')}`);
  else pass++;
}

/* ── C14 · enum validation ─────────────────────────────────────────────────── */
for (const g of ['value-exact', 'partial', 'summary']) {
  run(`C14 silent on legal grain ${g}`, manifest({ grain: g }), { exit: 0, absent: ['C14'] });
}
run('C14 fires on full', manifest({ grain: 'full' }), {
  exit: 1,
  contains: ['C14-GRAIN-ENUM', 'not one of value-exact | partial | summary'],
});
run('C14 does NOT coerce the file', manifest({ grain: 'full' }), {
  exit: 1,
  contains: ['manifest_grain          : full'],
});
run('C14 silent when the field is absent', manifest({ grain: 'summary' }).replace(/\s*manifest_grain:.*\n/, '\n'), {
  absent: ['C14'],
});

/* ── C4 · emit refusal ─────────────────────────────────────────────────────── */
run('C4 refuses drawn:true with no section inventory', manifest({ sections: false }), {
  exit: 2,
  contains: ['EMIT REFUSED', 'C4-MISSING-INV', 'set drawn:false'],
});
run('C4 silent for drawn:false — FRAME NOT DRAWN is preserved', manifest({ drawn: 'false', sections: false }), {
  absent: ['EMIT REFUSED'],
});
run('C4 exit 2 outranks strict exit 1 — a refusal is not advice', manifest({ sections: false }), { exit: 2 });

/* ── consumer trust ceiling ────────────────────────────────────────────────── */
run('ceiling caps value-exact when the grid cannot be read', manifest({ grain: 'value-exact', grid: false }), {
  contains: ['EFFECTIVE grain         : summary', 'OPEN THE AUTHORITATIVE DESIGN SOURCE'],
});
run('ceiling names WHY, not just the value', manifest({ grain: 'value-exact', grid: false }), {
  contains: ['nothing substantiates the declared grain'],
});
run('ceiling silent on a clean value-exact manifest', manifest({ grain: 'value-exact' }), { exit: 0, absent: ['EFFECTIVE grain'] });
run('ceiling silent on a clean summary manifest', manifest({ grain: 'summary' }), { exit: 0, absent: ['EFFECTIVE grain'] });
run('ceiling does not rewrite frontmatter', manifest({ grain: 'value-exact', grid: false }), {
  contains: ['manifest_grain          : value-exact'],
});

/* ── the baseline must stay clean, or every case above proves nothing ─────── */
run('baseline manifest is CONSISTENT', manifest(), { exit: 0, contains: ['CONSISTENT'] });

rmSync(dir, { recursive: true, force: true });
console.log(`check-ingest-manifest golden suite: ${pass} passed, ${failures.length} failed`);
if (failures.length > 0) {
  for (const f of failures) console.log(`  ✗ ${f}`);
  process.exit(1);
}
