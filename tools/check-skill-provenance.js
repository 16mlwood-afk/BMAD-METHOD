/**
 * check-skill-provenance.js  —  default WARN-ONLY · --strict for the future gate
 *
 * Coverage check for STD-SKILLPROV-001 (skill-provenance standard, DRAFT —
 * docs/skill-provenance-standard-DRAFT.md). The skills-side sibling of the
 * brief-provenance contract.
 *
 * The standard: every authored skill carries a `provenance:` frontmatter block
 * (id, version, created_at, author, source_research[>=1 URL], origin_type,
 * exemption_reason?, last_reviewed_at, review_notes), produced only after a
 * MANDATORY external-discovery pass (web + GitHub/MCP) recorded as an
 * "External research checked" block in the skill body.
 *
 * What IS and ISN'T deterministically enforceable (per the enforcement-expert
 * DETERMINISTIC vs PROBABILISTIC axis — classified with the skill this run):
 *   - Whether the agent ACTUALLY ran an external web/GitHub discovery pass is a
 *     PROCESS WITH NO ARTIFACT. A linter cannot prove a search happened; a
 *     fabricated `source_research` URL passes. That act stays PROBABILISTIC —
 *     its lever is the global CLAUDE.md discovery-gate + the honesty rule. NOT
 *     checked here (checking it would be the indiscriminate-detector anti-pattern).
 *   - The PROXY artifact IS checkable: does the skill file carry a provenance
 *     block with the required fields and >=1 source_research URL (or a logged
 *     origin_type: original + exemption_reason)? This detector reports the gaps.
 *     Presence of the proxy != proof of the act — an honest ceiling, stated plainly.
 *
 * CONSERVATIVE DETECTION (bias to silence when uncertain — a wrong flag erodes
 * trust irreversibly, a missed one is recoverable next pass):
 *   - No provenance block at all           -> UNVERIFIED (the retrofit backlog).
 *   - Block present, missing required field -> INCOMPLETE (lists the field).
 *   - source_research empty AND not a logged original -> NO-SOURCE.
 *   - origin_type: original + non-empty exemption_reason -> OK even if
 *     source_research is thin (a genuine novel skill with a logged reason IS
 *     compliant; forcing a fake URL would be worse).
 *
 * MODES:
 *   - default (no flag): WARN-ONLY, exit 0 always — soak-style backlog visibility.
 *   - `--added`: only check SKILL.md files git sees as newly ADDED (staged) — the
 *     "new skills only" scope for the future phase-3 gate. Warn-only unless --strict.
 *   - `--strict`: a gap exits 1. NOT wired into any gate yet (warn-then-gate: arm
 *     only after the backlog is retrofitted and the detector is proven quiet, exactly
 *     as check:completion / check:digest were staged). Intended first arming:
 *     `--added --strict` in the pre-commit fast-path (new skills can't land unprovenanced).
 *
 * Run: `npm run check:skillprov`                    (warn-only, exit 0, full corpus)
 *      `npm run check:skillprov -- --added`          (only newly-added skills)
 *      `npm run check:skillprov -- --added --strict` (future gate mode)
 *
 * Fork-local tooling: guards the authoring locus (skills are authored in the fork),
 * NOT synced to the 13 projects. Pilot repo = the fork itself.
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

const ROOT = path.resolve(__dirname, '..');
const SKILL_ROOTS = [path.join(ROOT, 'custom', 'skills'), path.join(ROOT, 'custom', 'claude-global', 'skills')];
// The regenerated port mirror is NOT hand-authored skills — never scan it.
const EXCLUDE = /(^|\/)skills-native(\/|$)/;

const ADDED = process.argv.includes('--added');
const STRICT = process.argv.includes('--strict');
const JSON_OUT = process.argv.includes('--json');

const URL_RE = /https?:\/\/\S+/;
const REQUIRED = ['id', 'version', 'created_at', 'author', 'origin_type', 'last_reviewed_at'];

function findSkillFiles() {
  const out = [];
  const walk = (dir) => {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const e of entries) {
      const p = path.join(dir, e.name);
      if (EXCLUDE.test(p)) continue;
      if (e.isDirectory()) walk(p);
      else if (e.name === 'SKILL.md') out.push(p);
    }
  };
  for (const r of SKILL_ROOTS) walk(r);
  return out;
}

function addedSkillFiles() {
  try {
    const raw = execFileSync('git', ['diff', '--cached', '--name-only', '--diff-filter=A'], { cwd: ROOT, encoding: 'utf8' });
    return raw
      .split('\n')
      .filter((l) => /(^|\/)SKILL\.md$/.test(l) && !EXCLUDE.test(l))
      .map((l) => path.join(ROOT, l));
  } catch {
    return [];
  }
}

// Minimal, dependency-free frontmatter slice + the `provenance:` sub-block.
function parse(file) {
  const text = fs.readFileSync(file, 'utf8');
  const m = text.match(/^---\n([\s\S]*?)\n---/);
  const fm = m ? m[1] : '';
  const hasProvHeader = /^provenance:\s*$/m.test(fm);
  // grab the indented provenance block (lines indented under `provenance:`)
  let prov = '';
  if (hasProvHeader) {
    const lines = fm.split('\n');
    const start = lines.findIndex((l) => /^provenance:\s*$/.test(l));
    for (let i = start + 1; i < lines.length; i++) {
      if (/^\S/.test(lines[i])) break; // dedented -> block ended
      prov += lines[i] + '\n';
    }
  }
  const hasResearchBlock = /External research checked/i.test(text);
  return { hasProvHeader, prov, hasResearchBlock };
}

function evaluate(file) {
  const rel = path.relative(ROOT, file);
  const { hasProvHeader, prov, hasResearchBlock } = parse(file);
  if (!hasProvHeader) return { rel, status: 'UNVERIFIED', detail: 'no provenance: block' };

  const missing = REQUIRED.filter((k) => !new RegExp(`^\\s+${k}:\\s*\\S`, 'm').test(prov));
  const hasSourceUrl = URL_RE.test((prov.match(/source_research:[\s\S]*?(?=\n\s+\w+:|$)/) || [''])[0]);
  const isLoggedOriginal = /^\s+origin_type:\s*original\b/m.test(prov) && /^\s+exemption_reason:\s*\S/m.test(prov);

  const problems = [];
  if (missing.length > 0) problems.push(`missing: ${missing.join(', ')}`);
  if (!hasSourceUrl && !isLoggedOriginal) problems.push('no source_research URL and not a logged original');
  if (!hasResearchBlock) problems.push('no "External research checked" block in body');

  if (problems.length === 0) return { rel, status: 'OK', detail: '' };
  const status = missing.length > 0 || (!hasSourceUrl && !isLoggedOriginal) ? 'INCOMPLETE' : 'PROXY-WEAK';
  return { rel, status, detail: problems.join(' · ') };
}

const files = ADDED ? addedSkillFiles() : findSkillFiles();
const results = files.map(evaluate);
const gaps = results.filter((r) => r.status !== 'OK');
const ok = results.length - gaps.length;

if (JSON_OUT) {
  console.log(JSON.stringify({ scanned: results.length, ok, gaps }, null, 2));
} else {
  console.log(`\nSKILL-PROVENANCE (STD-SKILLPROV-001, DRAFT) — ${ADDED ? 'newly-added' : 'full corpus'}`);
  console.log(`scanned ${results.length} · ok ${ok} · gaps ${gaps.length}` + (STRICT ? ' · STRICT' : ' · warn-only'));
  for (const g of gaps) console.log(`  [${g.status}] ${g.rel} — ${g.detail}`);
  if (gaps.length === 0) console.log('  clean.');
  console.log('');
  if (gaps.length > 0 && !STRICT) {
    console.log('warn-only: this is the retrofit backlog, not a failure. Arm --strict (--added first) after retrofit.');
  }
  if (gaps.length > 0 && STRICT) {
    console.log('BLOCKED by STD-SKILLPROV-001 (newly-added skills must carry provenance).');
    console.log('For each skill above, add a top-level `provenance:` block to its SKILL.md frontmatter with:');
    console.log('  id · version · created_at · author · origin_type · source_research (>=1 URL) · last_reviewed_at');
    console.log('To satisfy the gate, EITHER cite >=1 real source_research URL, OR set');
    console.log('  origin_type: original WITH a non-empty exemption_reason (a logged reason is a valid pass).');
    console.log('Also add an "## External research checked" block to the body. See docs/skill-provenance-standard-DRAFT.md.');
  }
}

process.exit(STRICT && gaps.length > 0 ? 1 : 0);
