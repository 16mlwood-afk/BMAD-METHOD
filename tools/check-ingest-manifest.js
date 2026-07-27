/**
 * check-ingest-manifest.js  —  deterministic verifier for a design-ingest manifest's
 *                              own completeness arithmetic.
 *
 * Home of the rule: custom/workflows/implement/design-ingest/manifest-schema.md
 *                   ("Completeness invariant") + steps/step-03-emit-manifest-and-handoff.md §2.
 *
 * WHY THIS EXISTS (FG-2026-07-27-06).
 * step-03 §2 mandates "verify `completeness.sections_total` == the number of grid-scaffold
 * rows". Both sides of that equation were produced by the agent, by hand, and §2 offered no
 * mechanism — so "verify" meant "add it up again and hope". On 2026-07-27 a real run wrote
 * `sections_total: 66` against a 73-row grid (the five `claim-workspace--*` variants were
 * under-counted by one frame's worth) and caught it only via a throwaway python heredoc. Had
 * the agent trusted its own arithmetic, the manifest would have shipped declaring the
 * workflow's headline structural gate SATISFIED against a wrong denominator, and
 * design-implement would have consumed it as authoritative.
 *
 * That is this fork's own named anti-pattern applied to its own gate: "a field an agent
 * self-reports will eventually be wrong; the harness must stamp anything a gate keys on"
 * (the actor / claimed_by / claimed_at through-line in the collision-guard design).
 * `sections_total` looks like a fact, is self-reported, and the gate is keyed on it.
 *
 * DELIBERATELY NOT DONE: this tool does not WRITE `sections_total`. The agent still declares
 * it and the checker still disagrees. A self-stamping counter would remove the disagreement
 * that catches the error — the whole point is two independent derivations that must match.
 *
 * ── What IS and ISN'T deterministically checkable (enforcement-expert axis) ──
 *
 *  CHECKED (pure arithmetic and set membership over the emitted file — no judgement):
 *    C1  grid-scaffold data-row count == completeness.sections_total
 *    C2  per-frame grid row count == the N declared in that frame's section-inventory heading
 *    C3  per-frame grid row count == completeness.sections_per_frame[frame], when declared
 *    C4  every frame with drawn:true in the Frame inventory appears in BOTH the section
 *        inventory AND the grid scaffold
 *    C5  every frame appearing in the grid scaffold exists in the Frame inventory
 *        (a grid row for an undeclared frame is a copy-paste artefact)
 *    C6  completeness.frames_with_empty_section_list is empty
 *    C7  grain consistency — manifest_grain: value-exact REQUIRES
 *        sections_missing_property_rows to be empty (the §2a lie-prevention pair)
 *    C8  no duplicate frame rows in the Frame inventory
 *    C9  sum(sections_per_frame) == sections_total, when the map is declared
 *
 *  NOT CHECKED, on purpose — and this is the important half:
 *    Whether the ENUMERATION IS COMPLETE. Whether a real section of a real frame was missed
 *    is the single thing this whole workflow exists to prevent, and no linter can see it: the
 *    manifest is the only artifact, so a section nobody wrote down is invisible to a reader of
 *    that artifact by construction. That axis is carried by the per-frame fan-out (step-02)
 *    and by the human review at the step-03 handoff pause — never by this tool.
 *
 *    **A green run here means the manifest's numbers agree with themselves. It does NOT mean
 *    nothing was missed.** Anyone quoting this checker as evidence of completeness has made
 *    exactly the indiscriminate-detector mistake the fork warns about.
 *
 * ── Modes ──
 *   node tools/check-ingest-manifest.js --manifest <path>            report, exit 0 (warn-only)
 *   node tools/check-ingest-manifest.js --manifest <path> --strict    exit 1 on any finding
 *   node tools/check-ingest-manifest.js --manifest <path> --json      machine-readable report
 *
 * Arming note: unlike check-scope-register.js (whose route-correctness axis is honestly ceded
 * to a golden eval), every check here is arithmetic over the file with no interpretive step, so
 * a false positive requires the file to actually disagree with itself. step-03 §2 therefore
 * invokes it with --strict — the workflow's own standard already says "halt, do not emit a
 * malformed manifest". Default stays warn-only so the tool is safe to run anywhere.
 */

'use strict';
const fs = require('node:fs');

const argv = process.argv.slice(2);
function arg(name) {
  const i = argv.indexOf(name);
  return i === -1 ? null : argv[i + 1];
}
const MANIFEST = arg('--manifest');
const STRICT = argv.includes('--strict');
const JSON_OUT = argv.includes('--json');

if (!MANIFEST) {
  console.error('usage: check-ingest-manifest.js --manifest <path> [--strict] [--json]');
  process.exit(1);
}
if (!fs.existsSync(MANIFEST)) {
  console.error(`check-ingest-manifest: no such manifest: ${MANIFEST}`);
  process.exit(1);
}

const src = fs.readFileSync(MANIFEST, 'utf8');
const lines = src.split('\n');
const findings = [];
const fail = (code, msg) => findings.push({ code, msg });

/* ── 1. completeness block (line-based; no YAML dep, matching house tooling) ── */
function readCompleteness() {
  const out = { sections_per_frame: null };
  const start = lines.findIndex((l) => /^\s{2}completeness:\s*$/.test(l));
  if (start === -1) return out;
  const baseIndent = lines[start].match(/^\s*/)[0].length;
  let inPerFrame = false;
  let perFrameIndent = null;
  for (let i = start + 1; i < lines.length; i++) {
    const l = lines[i];
    if (!l.trim()) continue;
    const indent = l.match(/^\s*/)[0].length;
    if (indent <= baseIndent) break; // dedent → block over
    const m = l.match(/^\s*([A-Za-z_][\w-]*):\s*(.*)$/);
    if (!m) continue;
    const [, key, rawVal] = m;
    if (inPerFrame && indent > perFrameIndent) {
      out.sections_per_frame[key] = Number(rawVal.trim());
      continue;
    }
    inPerFrame = false;
    if (key === 'sections_per_frame' && rawVal.trim() === '') {
      inPerFrame = true;
      perFrameIndent = indent;
      out.sections_per_frame = {};
      continue;
    }
    const v = rawVal.trim().replace(/\s+#.*$/, '');
    if (/^\[\s*\]$/.test(v)) out[key] = [];
    else if (/^\[.*\]$/.test(v)) {
      out[key] = v
        .slice(1, -1)
        .split(',')
        .map((s) => s.trim().replaceAll(/^["']|["']$/g, ''))
        .filter(Boolean);
    } else if (/^-?\d+$/.test(v)) out[key] = Number(v);
    else out[key] = v.replaceAll(/^["']|["']$/g, '');
  }
  return out;
}
const C = readCompleteness();
if (C.sections_total === undefined)
  fail('NO-COMPLETENESS', 'frontmatter has no `completeness.sections_total` — cannot verify the gate this manifest claims to satisfy');

const grainMatch = src.match(/^\s*manifest_grain:\s*(\S+)/m);
const grain = grainMatch ? grainMatch[1] : null;

/* ── 2. Frame inventory: which frames are declared, and drawn? ──
 *
 * Section scoping is by HEADING LEVEL, not by naming the next section, and rows are filtered by
 * column count. Both guards exist because the naive version broke on its own first real use: it
 * scanned from `## Grid scaffold` to `## Data-availability`, so a perfectly legitimate 3-column
 * table added between them (a retraction table of commit SHAs) was read as grid rows and its
 * SHAs reported as undeclared frames. A manifest is prose that people add sections to; a parser
 * that assumes a fixed next-heading is a parser that will be wrong again.
 *   - stop at the next heading of the SAME-or-higher level as the start heading
 *   - keep only rows with at least `minCells` columns (frame inventory 5, grid scaffold 6)
 */
function tableRowsUnder(headingRe, minCells) {
  const start = lines.findIndex((l) => headingRe.test(l));
  if (start === -1) return null;
  const startLevel = (lines[start].match(/^#+/) || ['##'])[0].length;
  const rows = [];
  for (let i = start + 1; i < lines.length; i++) {
    const l = lines[i];
    const h = l.match(/^(#+)\s/);
    if (h && h[1].length <= startLevel) break; // next same-or-higher heading ends the section
    if (!l.startsWith('|')) continue;
    if (/^\|[\s\-:|]+\|?\s*$/.test(l)) continue; // separator
    const cells = l
      .split('|')
      .slice(1, -1)
      .map((c) => c.trim());
    if (cells.length < minCells) continue; // a narrower table is not this table
    rows.push(cells);
  }
  return rows;
}

const frameRows = tableRowsUnder(/^##+\s+Frame inventory\s*$/, 5);
const declaredFrames = new Map(); // name -> drawn(bool)
if (frameRows) {
  for (const cells of frameRows) {
    const name = cells[0]
      .replace(/\s*\(primary\)\s*$/i, '')
      .replaceAll('`', '')
      .trim();
    if (!name || /^frame$/i.test(name)) continue; // header row
    const drawnCell = (cells[4] || '').toLowerCase();
    const drawn = /true/.test(drawnCell);
    if (declaredFrames.has(name)) fail('DUP-FRAME', `C8 Frame inventory declares "${name}" more than once`);
    declaredFrames.set(name, drawn);
  }
} else {
  fail('NO-FRAME-INVENTORY', 'no `## Frame inventory` table found');
}
const drawnFrames = [...declaredFrames].filter(([, d]) => d).map(([n]) => n);

/* ── 3. Section inventory headings: `## Frame: <name> (N sections)` (h2 or h3) ── */
const invDeclared = new Map();
const headingRe = /^#{2,4}\s+Frame:\s+(.+?)\s*\((\d+)\s+sections?\)/;
for (const l of lines) {
  const m = l.match(headingRe);
  if (!m) continue;
  const name = m[1].replaceAll('`', '').trim();
  invDeclared.set(name, Number(m[2]));
}
if (invDeclared.size === 0)
  fail(
    'NO-SECTION-INVENTORY',
    'no `Frame: <name> (N sections)` headings found — the section inventory is the completeness gate; without it there is nothing to verify',
  );

/* ── 4. Grid scaffold rows ── */
/* minCells 5, not 6. The schema EXAMPLE shows six columns (frame · section · design copy/structure ·
 * data fields · component×property rows · status), but a real manifest may legitimately merge the
 * copy and property columns into one locator and carry the resolved values per-section instead —
 * which is what `property_rows_location` exists to declare. Column-count conformance is therefore
 * deliberately NOT checked: the essential keys are frame + section + status, and the grain fields,
 * not the column layout, are what tell a consumer where the values live. 5 is the floor that still
 * excludes a narrower foreign table. */
const gridRows = tableRowsUnder(/^##+\s+Grid scaffold/, 5);
const gridPerFrame = new Map();
let gridCount = 0;
if (gridRows) {
  for (const cells of gridRows) {
    const f = cells[0].replaceAll('`', '').trim();
    if (!f || /^frame$/i.test(f)) continue; // header row
    if (/^\.\.\.|^…/.test(f)) continue; // schema-example ellipsis row
    gridCount++;
    gridPerFrame.set(f, (gridPerFrame.get(f) || 0) + 1);
  }
} else {
  fail('NO-GRID', 'no `## Grid scaffold` table found');
}

/* ── 5. The checks ── */
if (C.sections_total !== undefined && gridRows && gridCount !== C.sections_total) {
  fail(
    'C1-TOTAL',
    `C1 sections_total is ${C.sections_total} but the grid scaffold has ${gridCount} data rows — one section was enumerated and not scaffolded, or the count was hand-summed wrong`,
  );
}
/* Frames already reported as having zero grid rows — so the drawn-frame sweep below does not
 * report the SAME defect a second time from the other side. One condition, one finding. */
const reportedNoGridRows = new Set();
for (const [name, n] of invDeclared) {
  const g = gridPerFrame.get(name);
  if (g === undefined) {
    reportedNoGridRows.add(name);
    fail(
      'C4-NO-GRID-ROWS',
      `C4 frame "${name}" declares ${n} sections in the section inventory but has NO grid-scaffold rows — design-implement would be structurally blind to all of them`,
    );
  } else if (g !== n) {
    fail('C2-PER-FRAME', `C2 frame "${name}": section inventory declares ${n} sections, grid scaffold has ${g} rows`);
  }
  if (C.sections_per_frame && C.sections_per_frame[name] !== undefined && C.sections_per_frame[name] !== n) {
    fail(
      'C3-FRONTMATTER',
      `C3 frame "${name}": frontmatter sections_per_frame says ${C.sections_per_frame[name]}, section inventory heading says ${n}`,
    );
  }
}
for (const f of drawnFrames) {
  if (!invDeclared.has(f))
    fail('C4-MISSING-INV', `C4 frame "${f}" is drawn:true in the Frame inventory but has no section-inventory entry`);
  if (!gridPerFrame.has(f) && !reportedNoGridRows.has(f))
    fail('C4-MISSING-GRID', `C4 frame "${f}" is drawn:true in the Frame inventory but has no grid-scaffold rows`);
}
for (const f of gridPerFrame.keys()) {
  if (declaredFrames.size > 0 && !declaredFrames.has(f)) {
    fail('C5-UNDECLARED', `C5 grid scaffold has rows for "${f}", which is not in the Frame inventory`);
  }
}
if (Array.isArray(C.frames_with_empty_section_list) && C.frames_with_empty_section_list.length > 0) {
  fail(
    'C6-EMPTY-LIST',
    `C6 frames_with_empty_section_list is non-empty (${C.frames_with_empty_section_list.join(', ')}) — step-02's frame-completeness gate should have halted; this manifest is malformed and design-implement should refuse it`,
  );
}
if (grain === 'value-exact' && Array.isArray(C.sections_missing_property_rows) && C.sections_missing_property_rows.length > 0) {
  fail(
    'C7-GRAIN',
    `C7 manifest_grain is value-exact but sections_missing_property_rows lists ${C.sections_missing_property_rows.length} section(s) — that combination is the exact lie the grain field exists to prevent`,
  );
}
if (C.sections_per_frame) {
  const sum = Object.values(C.sections_per_frame).reduce((a, b) => a + b, 0);
  if (C.sections_total !== undefined && sum !== C.sections_total) {
    fail('C9-SUM', `C9 sections_per_frame sums to ${sum} but sections_total is ${C.sections_total}`);
  }
}

/* ── 6. Report ── */
const report = {
  manifest: MANIFEST,
  sections_total_declared: C.sections_total ?? null,
  grid_rows_counted: gridCount,
  frames_declared: declaredFrames.size,
  frames_drawn: drawnFrames.length,
  frames_in_section_inventory: invDeclared.size,
  frames_in_grid: gridPerFrame.size,
  manifest_grain: grain,
  findings,
  verdict: findings.length > 0 ? 'FINDINGS' : 'CONSISTENT',
};

if (JSON_OUT) {
  console.log(JSON.stringify(report, null, 2));
} else {
  console.log(`check-ingest-manifest: ${MANIFEST}`);
  console.log(`  sections_total declared : ${C.sections_total ?? '(absent)'}`);
  console.log(`  grid-scaffold rows      : ${gridCount}`);
  console.log(`  frames  declared/drawn  : ${declaredFrames.size}/${drawnFrames.length}`);
  console.log(`  frames  inventory/grid  : ${invDeclared.size}/${gridPerFrame.size}`);
  console.log(`  manifest_grain          : ${grain ?? '(absent)'}`);
  if (findings.length === 0) {
    console.log('  verdict                 : CONSISTENT — the numbers agree with themselves.');
    console.log('  NOTE: this proves ARITHMETIC, not completeness. Whether a real section was');
    console.log('        missed is invisible to this tool by construction — that is carried by');
    console.log('        the step-02 fan-out and the human review at the step-03 handoff.');
  } else {
    console.log(`  verdict                 : ${findings.length} FINDING(S)`);
    for (const f of findings) console.log(`    ✗ [${f.code}] ${f.msg}`);
  }
}

process.exit(STRICT && findings.length > 0 ? 1 : 0);
