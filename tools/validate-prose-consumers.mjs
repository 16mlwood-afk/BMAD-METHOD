/**
 * validate-prose-consumers.js — FG-2026-07-25-09, fix (2).
 *
 * A doctrine file that carries a "Prose consumers" table is asserting a set of
 * BINDINGS: "these workflows are bound by this contract." That table is the
 * fork's named anti-drift mechanism for prose consumers — and until now nothing
 * checked its claims, so it could assert a binding that does not exist.
 *
 * It did. `operator-artifact-contract.md` listed `design-artifact-loop` as bound
 * ("A + B by reference") while that workflow tree contained no reference to the
 * contract at all. The mechanism built to catch prose drift had undetected drift
 * in itself, which is the failure this validator closes.
 *
 * WHAT IT CHECKS (and only this): for every row of a "Prose consumers" table, if
 * the row names a path that resolves inside the doctrine file's workflow root,
 * that path's tree must contain at least one textual reference to the doctrine
 * file. A listed-but-unbound consumer is an ERROR.
 *
 * HONEST CEDE — this proves REFERENCE, never COMPLIANCE. It cannot tell whether
 * the consumer's prose actually implements the contract, only that the consumer
 * mentions it. A row that points at a workflow which name-drops the contract in a
 * comment passes. That is deliberate: reference is mechanically decidable and
 * compliance is not, and a check that pretended otherwise would be the same class
 * of lie this file exists to catch. Compliance stays with review.
 *
 * Exit 1 on any listed-but-unbound consumer. --strict is accepted for symmetry
 * with the other validators; the check is strict by default because a false
 * binding claim is never acceptable debt.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WORKFLOWS = path.join(ROOT, 'custom', 'workflows');

const HEADING = /^#{1,6}\s.*prose consumers/i;
const ANY_HEADING = /^#{1,6}\s/;

/** Recursively list files under dir, skipping node_modules/.git. */
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
    else out.push(p);
  }
  return out;
}

/** Extract the lines of the "Prose consumers" section (up to the next heading). */
function proseConsumerSection(text) {
  const lines = text.split('\n');
  const start = lines.findIndex((l) => HEADING.test(l));
  if (start === -1) return null;
  const rest = lines.slice(start + 1);
  const end = rest.findIndex((l) => ANY_HEADING.test(l));
  return (end === -1 ? rest : rest.slice(0, end)).join('\n');
}

/**
 * Pull candidate consumer paths out of a table row's first cell.
 * Rows look like:  | `design-handoff` (step-01 §3f, brief-template §4g/§7) | ... |
 * We take every backticked token that looks like a path or workflow name.
 */
function candidatesFromRow(row) {
  const firstCell = row.split('|')[1] ?? '';
  const ticked = [...firstCell.matchAll(/`([^`]+)`/g)].map((m) => m[1].trim());
  return (
    ticked
      .map((t) => t.replace(/\s*\(.*$/, '').trim())
      // strip a trailing section marker (`design-handoff/steps/step-01.md §3f`)
      .map((t) => t.split(/\s+/)[0])
      .filter((t) => t && !t.startsWith('§') && /^[\w./-]+$/.test(t))
  );
}

/** Resolve a candidate token against the doctrine file's workflow root. */
function resolveCandidate(token, workflowRoot) {
  const tries = [path.join(workflowRoot, token), path.join(workflowRoot, '..', token), path.join(WORKFLOWS, token)];
  for (const t of tries) {
    if (fs.existsSync(t)) return t;
  }
  // One level down from the workflows root — a consumer named bare
  // ('design-implement') may live in a sibling family dir ('implement/').
  // Without this, a cross-family consumer resolves to nothing and is silently
  // downgraded to UNVERIFIED, which is how a real unbound row would hide.
  let families;
  try {
    families = fs.readdirSync(WORKFLOWS, { withFileTypes: true }).filter((d) => d.isDirectory());
  } catch {
    return null;
  }
  for (const fam of families) {
    const t = path.join(WORKFLOWS, fam.name, token);
    if (fs.existsSync(t)) return t;
  }
  return null;
}

/** Does `target` (file or dir) textually reference `needle`? */
function referencesDoctrine(target, needle) {
  const files = fs.statSync(target).isDirectory() ? walk(target) : [target];
  for (const f of files) {
    if (!/\.(md|js|cjs|mjs|sh|ya?ml)$/.test(f)) continue;
    let content;
    try {
      content = fs.readFileSync(f, 'utf8');
    } catch {
      continue;
    }
    if (content.includes(needle)) return true;
  }
  return false;
}

const errors = [];
const notes = [];
let tablesChecked = 0;
let rowsChecked = 0;

for (const file of walk(WORKFLOWS)) {
  if (!file.endsWith('.md')) continue;
  let text;
  try {
    text = fs.readFileSync(file, 'utf8');
  } catch {
    continue;
  }
  const section = proseConsumerSection(text);
  if (!section) continue;

  tablesChecked += 1;
  const doctrineBase = path.basename(file);
  // The doctrine file's own workflow root, e.g. custom/workflows/design/
  const workflowRoot = path.dirname(path.dirname(file));
  const rel = path.relative(ROOT, file);

  for (const row of section.split('\n')) {
    if (!row.trim().startsWith('|')) continue;
    if (/^\|[\s:|-]+\|$/.test(row.trim())) continue; // separator
    const cands = candidatesFromRow(row);
    if (cands.length === 0) continue;

    // A row is satisfied if ANY of its named paths resolves AND references the
    // doctrine. Rows naming several files (a workflow + its template) bind as a
    // unit; requiring every token would fire on prose like "(step-01 §3f)".
    let resolvedAny = false;
    let boundAny = false;
    const resolvedTokens = [];

    for (const c of cands) {
      const target = resolveCandidate(c, workflowRoot);
      if (!target) continue;
      resolvedAny = true;
      resolvedTokens.push(c);
      if (referencesDoctrine(target, doctrineBase)) {
        boundAny = true;
        break;
      }
    }

    rowsChecked += 1;
    if (!resolvedAny) {
      // Cannot verify — the row names no resolvable path. Report, never fail:
      // a table may legitimately name a human process or an external consumer.
      notes.push(`${rel}: row names no resolvable path (${cands.join(', ')}) — UNVERIFIED, not failed`);
      continue;
    }
    if (!boundAny) {
      errors.push(
        `${rel}: listed consumer '${resolvedTokens.join("' / '")}' contains NO reference to '${doctrineBase}' — ` +
          `the table asserts a binding that does not exist. Wire the reference into that consumer, or drop the row.`,
      );
    }
  }
}

for (const n of notes) console.warn(`prose-consumers [note]: ${n}`);
for (const e of errors) console.error(`prose-consumers [ERROR]: ${e}`);

if (errors.length > 0) {
  console.error(
    `\nprose-consumers: ${errors.length} unbound consumer(s) across ${tablesChecked} table(s).\n` +
      `A "Prose consumers" table is a set of BINDING CLAIMS. An unbound row is worse than no row:\n` +
      `it reports the drift surface as covered while nothing binds it.\n`,
  );
  process.exit(1);
}

console.log(
  `prose-consumers: OK — ${rowsChecked} row(s) across ${tablesChecked} table(s); every resolvable consumer references its doctrine.` +
    (notes.length > 0 ? ` ${notes.length} unverifiable row(s) noted.` : ''),
);
