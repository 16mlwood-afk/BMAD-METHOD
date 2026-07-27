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
 *    C10 the body's prose grain claim ("Grain: value-exact") matches the frontmatter
 *        `manifest_grain` field — including the case where the field is ABSENT, which the
 *        schema says a consumer MUST read as `summary`. Two disagreeing copies of the trust
 *        level is worse than one wrong copy: it reads as corroborated.
 *    C11 no UNRESOLVED VOCABULARY REFERENCE (`DECISION[x].label`, `DEFECT[].label`) survives in
 *        a manifest claiming value-exact grain. The literals such a reference names are not in
 *        the file, so the consumer must re-read the design source — which a delegated sub-agent
 *        structurally cannot do (session-bound MCP). Override: declare it in
 *        `completeness.unresolved_references` and it reports as a disclosed deferral instead.
 *
 *  CEDED, explicitly (a checker that guesses is worse than one that says it cannot tell):
 *    When the grid scaffold's first column is not a frame name — a manifest may legitimately key
 *    its grid on a ROW NUMBER and carry the frame in each sub-table's heading — C1–C5 are not
 *    evaluated and ONE finding says so. The first time this parser was pointed at a real manifest
 *    in that shape it emitted 98 findings for two real defects; a checker nobody trusts protects
 *    nothing. C6–C11 do not depend on table layout and still apply.
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
/* Real manifests NUMBER their headings — `## 2. Frame inventory`, `## 4. Grid scaffold — 83
 * rows`, `### 3c. <frame> — 7 sections`. The first version of these matchers anchored on the
 * bare heading text and therefore found NOTHING in the first real manifest it was pointed at:
 * 0 grid rows against an 83-row file, reported as three confident "no such table" findings.
 *
 * That is the worst possible failure for a checker, because BOTH of its outcomes read as
 * reassuring: a document it cannot parse reports either CONSISTENT (nothing to disagree with)
 * or "your tables are missing" (which a reader assumes is a manifest defect, not a parser
 * one). The same lesson as the heading-level/column-count fix in 175f8373 — a manifest is
 * prose that people format; a parser that assumes one exact phrasing will keep being inert. */
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

const frameRows = tableRowsUnder(/^##+\s+(?:\d+[a-z]?\.\s*)?Frame inventory\b/i, 5);
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
/* Two accepted shapes, both allowing a `<n>.` / `<n><letter>.` section prefix:
 *   A  `### Frame: <name> (7 sections)`   — the schema's own shape
 *   B  `### 3c. \`<name>\` — 7 sections`  — the shape real manifests actually write
 * B is anchored to end-of-line and requires the literal "N sections" tail, so a prose heading
 * that merely contains an em-dash (`### 3a. Canonical section list — the register family`)
 * does not match. Loosening past this would start inventing frames out of headings. */
const headingReA = /^#{2,4}\s+(?:\d+[a-z]?\.\s*)?Frame:\s+(.+?)\s*\((\d+)\s+sections?\)/;
const headingReB = /^#{2,4}\s+(?:\d+[a-z]?\.\s*)?`?(.+?)`?\s+[—–-]\s+(\d+)\s+sections?\s*$/;
for (const l of lines) {
  const m = l.match(headingReA) || l.match(headingReB);
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
const gridRows = tableRowsUnder(/^##+\s+(?:\d+[a-z]?\.\s*)?Grid scaffold\b/i, 5);
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

/* ── 4a. Is the grid scaffold in the layout these checks assume? ──
 *
 * C1–C5 all key on "column 0 of a grid row is a frame name". A real manifest may legitimately
 * lead with a ROW NUMBER instead (`| 1 | R1 owner shell nav | … |`) and carry the frame in its
 * per-table heading. Run the frame-keyed checks against that and every row number is reported as
 * an undeclared frame: the first time this parser was made to see a real manifest it produced 98
 * findings on a document whose actual defects were two.
 *
 * A checker that cries wolf 98 times gets switched off, and then it protects nothing — so when
 * the layout is not the one these checks understand, CEDE the dimension in one line rather than
 * guess row-by-row. This is the same add-vs-cede call the workflow makes elsewhere: owning the
 * boundary by disclosure beats a check that lies. The body-scanned checks (C10, C11) are
 * unaffected — they do not depend on table layout at all, which is exactly why they still fire
 * on a manifest whose scaffold shape this tool cannot read. */
const gridKeys = [...gridPerFrame.keys()];
const gridKeysMatchingFrames = gridKeys.filter((k) => declaredFrames.has(k)).length;
const gridLayoutRecognised = gridKeys.length === 0 || declaredFrames.size === 0 || gridKeysMatchingFrames * 2 >= gridKeys.length;
if (!gridLayoutRecognised) {
  fail(
    'GRID-LAYOUT-UNRECOGNISED',
    `grid scaffold's first column is not a frame name (${gridKeysMatchingFrames}/${gridKeys.length} rows match a declared frame) — this manifest keys its grid on something else, most likely a row number with the frame carried in each sub-table's heading. C1–C5 are NOT evaluated for it; the frame/section arithmetic is unverified here, not verified-clean. C6–C11 still apply`,
  );
}

/* ── 5. The checks ── */
if (gridLayoutRecognised && C.sections_total !== undefined && gridRows && gridCount !== C.sections_total) {
  fail(
    'C1-TOTAL',
    `C1 sections_total is ${C.sections_total} but the grid scaffold has ${gridCount} data rows — one section was enumerated and not scaffolded, or the count was hand-summed wrong`,
  );
}
/* Frames already reported as having zero grid rows — so the drawn-frame sweep below does not
 * report the SAME defect a second time from the other side. One condition, one finding. */
const reportedNoGridRows = new Set();
for (const [name, n] of gridLayoutRecognised ? invDeclared : new Map()) {
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
for (const f of gridLayoutRecognised ? drawnFrames : []) {
  if (!invDeclared.has(f))
    fail('C4-MISSING-INV', `C4 frame "${f}" is drawn:true in the Frame inventory but has no section-inventory entry`);
  if (!gridPerFrame.has(f) && !reportedNoGridRows.has(f))
    fail('C4-MISSING-GRID', `C4 frame "${f}" is drawn:true in the Frame inventory but has no grid-scaffold rows`);
}
for (const f of gridLayoutRecognised ? gridPerFrame.keys() : []) {
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
/* ── C10: the manifest CLAIMS a grain in prose that its frontmatter does not declare ──
 *
 * `manifest_grain` is the field consumers branch on, and the schema is explicit that an ABSENT
 * field must be read as `summary` — i.e. "re-read the design source for values". But a manifest
 * can, and did, announce **"Grain: `value-exact`"** in its body while carrying no frontmatter
 * field at all. Every human reader — and every agent reading top-down — takes the prose. The
 * conservative default then never fires, and the source re-read it exists to force is skipped.
 *
 * This is the fork's own recurring shape one layer up: a field an agent self-reports will
 * eventually be wrong, so never key a gate on the copy of it that is easiest to write. Here the
 * two copies actively disagree, which is strictly worse than one wrong copy — it looks
 * corroborated. Deterministic and judgement-free: either the strings match, or they do not. */
const proseGrain = src.match(/^\*{0,2}Grain:?\*{0,2}\s*:?\s*`?(value-exact|partial|summary)`?/im);
if (proseGrain) {
  const claimed = proseGrain[1];
  if (!grain) {
    fail(
      'C10-GRAIN-PROSE-ONLY',
      `C10 the body announces grain "${claimed}" but frontmatter has no \`manifest_grain\` field — the schema says an absent field MUST be read as \`summary\`, so this manifest reads as value-exact to every human and as "re-read the source" to the one rule that is written down. Declare \`manifest_grain: ${claimed}\` in the frontmatter, or drop the prose claim`,
    );
  } else if (grain !== claimed) {
    fail(
      'C10-GRAIN-CONFLICT',
      `C10 frontmatter declares \`manifest_grain: ${grain}\` but the body announces grain "${claimed}" — a consumer will trust whichever it reads first`,
    );
  }
}

/* ── C11: an UNRESOLVED VOCABULARY REFERENCE in a value-exact manifest ──
 *
 * A manifest may record `DECISION[decision].label` / `DEFECT[].label` / `GAPS[k].label` where the
 * literal copy belongs — naming a lookup it never resolves. The strings the surface actually
 * displays are then nowhere in the artifact built to carry them, while the manifest declares
 * value-exact grain and design-implement is told to reproduce copy VERBATIM. The consumer's only
 * legal moves become "re-read the design source" or "halt" — and the fan-out sub-agents that a
 * large surface delegates to structurally CANNOT re-read it (the design MCP is session-bound,
 * FG-2026-07-26-01/-06). Compose the two and a delegated run has no legal continuation; the
 * remaining exit is to invent "Claim reversed", which is the one thing the transcription rule
 * forbids. (FG-2026-07-27-09, cash-recovery /write-offs: five strings behind three references.)
 *
 * Conservative by construction — it fires ONLY on an ALL-CAPS identifier indexed and dereferenced
 * (`NAME[...].field`), which is the vocabulary-constant convention. `entries[0].id`,
 * `e.scopedComponents[]`, `rows[]` and every lowercase accessor are invisible to it. The
 * frontmatter escape hatch is the logged override: a reference that genuinely cannot be resolved
 * is declared, with its reason, and reported rather than silently passing. */
/* `.length` is excluded: it is a JS builtin describing HOW MANY, never a piece of copy, so
 * `ORDER_LINES["1SJ7K9RQ"].length` states a count the manifest can carry itself. Every other
 * dereference names a FIELD of the vocabulary — which is where the literal lives. */
const VOCAB_REF = /\b([A-Z][A-Z0-9_]{2,})\s*\[[^\]\n]*\]\s*\.\s*(?!length\b)[A-Za-z_]\w*/g;
const bodyStart = (() => {
  if (lines[0] !== '---') return 0;
  const end = lines.indexOf('---', 1);
  return end === -1 ? 0 : end + 1;
})();
const resolvedVocab = new Set((Array.isArray(C.resolved_vocabularies) ? C.resolved_vocabularies : []).map((v) => v.toUpperCase()));
const declaredUnresolved = new Set(
  (Array.isArray(C.unresolved_references) ? C.unresolved_references : []).map((v) =>
    String(v)
      .split(/[\s:(]/)[0]
      .toUpperCase(),
  ),
);
/* A `Vocabulary: NAME` block in the body resolves it too — the same dereference affordance the
 * grid already uses for `→ §6/<id>`. */
for (const l of lines) {
  const m = l.match(/^#{2,6}\s+.*\bVocabulary:\s*`?([A-Z][A-Z0-9_]{2,})`?/);
  if (m) resolvedVocab.add(m[1].toUpperCase());
}
const unresolvedHits = new Map(); // NAME -> {line, sample}
for (let i = bodyStart; i < lines.length; i++) {
  for (const m of lines[i].matchAll(VOCAB_REF)) {
    const name = m[1].toUpperCase();
    if (resolvedVocab.has(name)) continue;
    if (!unresolvedHits.has(name)) unresolvedHits.set(name, { line: i + 1, sample: m[0] });
  }
}
for (const [name, hit] of unresolvedHits) {
  if (declaredUnresolved.has(name)) {
    fail(
      'C11-DECLARED',
      `C11 vocabulary "${name}" is referenced but not resolved (first at line ${hit.line}: \`${hit.sample}\`) — DECLARED in completeness.unresolved_references, so this is a disclosed deferral, not a defect. The consumer must re-read the design source for it`,
    );
  } else if (grain === 'value-exact' || (proseGrain && proseGrain[1] === 'value-exact')) {
    fail(
      'C11-UNRESOLVED-VOCAB',
      `C11 vocabulary "${name}" is referenced but never resolved (first at line ${hit.line}: \`${hit.sample}\`) while this manifest claims value-exact grain — the literals it names are not in this file, so a consumer must re-read the design source or halt, and a delegated sub-agent can do neither. Resolve it into a \`Vocabulary: ${name}\` block, or declare it in completeness.unresolved_references with a reason`,
    );
  }
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
