/**
 * standards-corpus.js — the ONE corpus walk for every standards-adoption gate.
 *
 * ┌───────────────────────────────────────────────────────────────────────────┐
 * │ MANDATE — read before authoring any new standards-adoption scanner.        │
 * │                                                                           │
 * │ ALL standards-adoption / contract-coverage gates MUST call                 │
 * │ `collectStandardsCorpus()` and MUST NOT hard-code a corpus root.           │
 * │ Copy-pasting `path.join(ROOT, 'custom', 'workflows')` into a fourth gate   │
 * │ re-introduces exactly the bug this file exists to kill.                    │
 * └───────────────────────────────────────────────────────────────────────────┘
 *
 * WHY THIS EXISTS (fork-gaps 2026-07-25, class `contract-dimension-gap` at the
 * tooling layer). Three gates — `check-completion-disposition.js`,
 * `check-digest-adoption.js`, `validate-close-out-contract.js` — each hard-coded
 * `custom/workflows/` as their only root. After the v6.8 skills migration, 261 `.md`
 * files live under the `custom/skills` trees, and 22 already reference the very
 * standards those gates enforce. Two of the three (`check:completion --strict`,
 * `validate:close-out`) are ARMED in `npm test` and the pre-commit fast-path — so
 * they were blocking commits on a pass/fail claim computed over a PARTIAL corpus.
 * "0 likely gaps" read as proof when it was an artifact of where the tool looked.
 *
 * Discovered the same way it will be rediscovered: a new scanner, authored in the
 * house shape, reported "clean" while structurally blind to
 * `custom/skills/bmad-correct-course/SKILL.md` — the single most important file in
 * the standard it was written to check.
 *
 * THE ROOTS, AND THE HONEST ASYMMETRY:
 *
 *   custom/workflows/   INCLUDED — hand-authored source of record (command layout).
 *
 *   custom/skills/      INCLUDED — hand-authored source of record (policy skills,
 *                       incl. `bmad-correct-course`). Not defensibly excluded: it is
 *                       edited by hand and it carries standards references.
 *
 *   custom/skills-native/  EXCLUDED — a GENERATED, gitignored port produced by
 *                       `tools/port-workflows-to-skills.sh` from the two roots above.
 *                       Scanning it would flag PORTS rather than SOURCES: every
 *                       finding would be a duplicate of a workflows/ finding, and
 *                       "fixing" one there is silently discarded by the next porter
 *                       run. The exclusion is a DECISION recorded here, not an
 *                       accident of a hard-coded path — which is precisely the
 *                       distinction the original bug lacked.
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');

/** Fork root (this file lives at <root>/tools/lib/). */
const ROOT = path.resolve(__dirname, '..', '..');

/**
 * Source-of-record roots, repo-relative. Order is stable so gate output is stable.
 * See the header for why `custom/skills-native/` is deliberately absent.
 */
const CORPUS_ROOTS = [path.join('custom', 'workflows'), path.join('custom', 'skills')];

/** Generated port — never scanned. Named explicitly so the exclusion is greppable. */
const EXCLUDED_ROOTS = [path.join('custom', 'skills-native')];

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p, out);
    else if (entry.isFile() && entry.name.endsWith('.md')) out.push(p);
  }
  return out;
}

/**
 * Collect every source-of-record markdown file a standards-adoption gate should scan.
 *
 * Never throws and never exits — a caller owns its own missing-root policy (the three
 * existing gates disagree: close-out exits 2, the other two exit 0), so this returns
 * the facts and lets each keep its behaviour.
 *
 * @returns {{files: string[], roots: string[], missingRoots: string[]}}
 *   files        absolute paths, sorted, deduped
 *   roots        absolute paths of roots that exist and were walked
 *   missingRoots absolute paths of configured roots absent from disk
 */
function collectStandardsCorpus() {
  const roots = [];
  const missingRoots = [];
  const files = new Set();

  for (const relRoot of CORPUS_ROOTS) {
    const abs = path.join(ROOT, relRoot);
    if (!fs.existsSync(abs)) {
      missingRoots.push(abs);
      continue;
    }
    roots.push(abs);
    for (const f of walk(abs)) files.add(f);
  }

  return { files: [...files].sort(), roots, missingRoots };
}

module.exports = { collectStandardsCorpus, ROOT, CORPUS_ROOTS, EXCLUDED_ROOTS };
