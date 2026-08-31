/**
 * validate-standards-delivery.mjs — the cites-without-loading check (2026-08-24).
 *
 * Origin: docs/design-policy.md and four design workflows all cited
 * design-standards.md as a precedence authority, and NO step ever opened it —
 * so the AI-fingerprint taxonomy reached Claude Design only as a hand-copied
 * excerpt, and a taxonomy-class pattern (left-border accent container) shipped
 * unflagged. Citation is not delivery. This validator fails the build when a
 * REQUIRED consumer of design-standards.md carries no load/read/embed/run
 * instruction for it.
 *
 * WHAT IT CHECKS (and only this): each required consumer tree/file contains at
 * least one line where a delivery verb (read/load/open/copy/embed/run/scan)
 * and a reference to the standards file (`design-standards.md` or the
 * `{design_standards}` / `{design_standards_path}` variable) co-occur.
 * Additionally, any OTHER workflow tree that cites the file without such a
 * line is reported as a WARN (visible drift, not a build failure — some trees
 * legitimately receive standards content only through sister artifacts, e.g.
 * design-synthesize).
 *
 * HONEST CEDE — this proves an INSTRUCTION EXISTS, never that a session obeys
 * it. It is the same reference-not-compliance ceiling as
 * validate-prose-consumers.mjs, and it is still worth having: it removes the
 * silent state where a workflow's own text never asks for the file at all.
 *
 * Exit 1 on any required consumer missing its delivery line. Run via
 * `npm run validate:standards-delivery` (wired into the `test` chain).
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WORKFLOWS = path.join(ROOT, 'custom', 'workflows');

/** Required consumers: tree (dir) or single file, relative to custom/workflows. */
const REQUIRED = [
  'design/design-handoff',
  'design/design-review',
  'design/design-review-pr',
  'design/design-tuning',
  'design/design-synthesize',
  'design/shared/claude-design-prompt.md',
  'implement/design-ingest',
];

const FILE_REF = /(design-standards\.md|\{design_standards(_path)?\})/i;
const DELIVERY_LINE =
  /\b(read|reads|load|loads|open|opens|copy|copies|embed|embeds|embedded|run|runs|scan|scans)\b[^\n]{0,300}(design-standards\.md|\{design_standards(_path)?\})|(design-standards\.md|\{design_standards(_path)?\})[^\n]{0,300}\b(read|reads|load|loads|open|opens|copy|copies|embed|embeds|embedded|run|runs|scan|scans)\b/i;

function walk(dir, out = []) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const e of entries) {
    if (e.name === 'node_modules' || e.name === '.git') continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith('.md')) out.push(p);
  }
  return out;
}

function filesFor(rel) {
  const abs = path.join(WORKFLOWS, rel);
  if (fs.existsSync(abs) && fs.statSync(abs).isDirectory()) return walk(abs);
  if (fs.existsSync(abs)) return [abs];
  return null;
}

function hasDeliveryLine(files) {
  for (const f of files) {
    const text = fs.readFileSync(f, 'utf8');
    for (const line of text.split('\n')) {
      if (DELIVERY_LINE.test(line)) return { file: f, line };
    }
  }
  return null;
}

let errors = 0;
let warns = 0;

for (const rel of REQUIRED) {
  const files = filesFor(rel);
  if (!files) {
    console.error(`ERROR  required consumer missing from tree: ${rel}`);
    errors += 1;
    continue;
  }
  const hit = hasDeliveryLine(files);
  if (!hit) {
    console.error(
      `ERROR  ${rel} cites design-standards.md as authority but contains NO load/read/embed/run instruction for it — citation is not delivery (the 2026-08-24 failure).`,
    );
    errors += 1;
  }
}

/* WARN sweep: any other tree citing the file with no delivery line. */
const requiredRoots = REQUIRED.map((r) => path.join(WORKFLOWS, r));
const byTree = new Map();
for (const f of walk(WORKFLOWS)) {
  if (requiredRoots.some((r) => f === r || f.startsWith(r + path.sep))) continue;
  if (f.includes(`${path.sep}shared${path.sep}`) || path.dirname(f) === WORKFLOWS) continue;
  const text = fs.readFileSync(f, 'utf8');
  if (!FILE_REF.test(text)) continue;
  const parts = path.relative(WORKFLOWS, f).split(path.sep);
  const tree = parts.slice(0, 2).join('/');
  if (!byTree.has(tree)) byTree.set(tree, []);
  byTree.get(tree).push(f);
}
for (const [tree, files] of byTree) {
  const treeFiles = filesFor(tree) ?? files;
  if (!hasDeliveryLine(treeFiles)) {
    console.warn(
      `WARN   ${tree} cites design-standards.md without a delivery instruction (not required to load — but check it is not treating citation as delivery)`,
    );
    warns += 1;
  }
}

if (errors) {
  console.error(`validate:standards-delivery — ${errors} error(s), ${warns} warn(s)`);
  process.exit(1);
}
console.log(`validate:standards-delivery — all ${REQUIRED.length} required consumers carry a delivery instruction (${warns} warn(s))`);
