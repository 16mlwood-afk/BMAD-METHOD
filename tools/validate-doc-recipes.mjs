/**
 * validate-doc-recipes.mjs — lint the SHELL RECIPES the fork's own docs tell sessions to run.
 *
 * Why this exists (fork-gaps FG-2026-07-25-12). `docs/manifest-contract.md` §4a — the mitigation
 * for a hazard that had already fired three times on the fork's own backlog and workflow files —
 * prescribed, verbatim:
 *
 *     git commit -- <explicit paths> -m …
 *
 * That command cannot succeed. Everything after `--` is a pathspec, so git parses `-m` and the
 * commit message as filenames and dies with `did not match any file(s) known to git`. A session
 * following the doctrine literally hits an error, and the obvious recovery from that error is
 * `git add` then `git commit` — the exact two-step form the rule exists to forbid.
 *
 * The general shape: **doctrine ships an executable recipe that nothing ever executes.** A
 * behavioural test of every documented command is not worth building; ARGUMENT ORDER is, because
 * it is mechanically decidable and it is what actually bit.
 *
 * CHECKED (one thing, precisely): an option-looking token appearing AFTER a bare `--` separator
 * in a `git` recipe.
 *
 * NOT CHECKED, on purpose: whether the command does the right thing, whether its paths exist,
 * whether its flags are real. Faking those is the indiscriminate-detector anti-pattern this fork
 * keeps naming.
 *
 * Run: node tools/validate-doc-recipes.mjs   (wired into npm test)
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const SCAN_DIRS = ['docs', 'custom'];
// skills-native is GENERATED from custom/workflows — linting it would double-report every finding.
const SKIP_DIRS = new Set(['node_modules', 'skills-native']);

/** Every `git …` command found in a fenced block or an inline-code span. */
function gitRecipes(text) {
  const out = [];
  let inFence = false;
  let lineNo = 0;
  const push = (seg, line) => {
    const t = seg.trim();
    if (/^git\s/.test(t)) out.push({ cmd: t, line });
  };
  for (const raw of text.split('\n')) {
    lineNo++;
    if (/^\s*```/.test(raw)) {
      inFence = !inFence;
      continue;
    }
    // A doc that EXPLAINS a broken command necessarily contains it. Those are quotations,
    // not prescriptions, and a lint that cannot tell the difference blocks every commit and
    // gets deleted. So the author marks them: `recipe-lint:ignore` anywhere on the line
    // (an HTML comment renders invisibly in prose). Deliberately explicit — no heuristic
    // guessing at "this line sounds like a counter-example".
    if (raw.includes('recipe-lint:ignore')) continue;
    const sources = inFence ? [raw] : [...raw.matchAll(/`([^`]+)`/g)].map((m) => m[1]);
    for (const src of sources) {
      // A line may chain commands; each segment is its own recipe.
      for (const seg of src.split(/&&|\|\||;/)) push(seg, lineNo);
    }
  }
  return out;
}

/**
 * Returns the offending token, or null. Tokens after a bare `--` are pathspecs, so a leading dash
 * there is either a filename that does not need one or — far more likely — a flag the author meant
 * to put BEFORE the separator.
 */
function optionAfterSeparator(cmd) {
  const toks = cmd.split(/\s+/);
  const sep = toks.indexOf('--');
  if (sep === -1) return null;
  for (const t of toks.slice(sep + 1)) {
    if (/^-{1,2}[A-Za-z]/.test(t)) return t;
  }
  return null;
}

function walk(dir, acc = []) {
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return acc;
  }
  for (const e of entries) {
    if (e.isDirectory()) {
      if (!SKIP_DIRS.has(e.name) && !e.name.startsWith('.')) walk(join(dir, e.name), acc);
    } else if (e.name.endsWith('.md')) {
      acc.push(join(dir, e.name));
    }
  }
  return acc;
}

const files = SCAN_DIRS.flatMap((d) => {
  const p = join(ROOT, d);
  try {
    return statSync(p).isDirectory() ? walk(p) : [];
  } catch {
    return [];
  }
});

const findings = [];
for (const f of files) {
  let text;
  try {
    text = readFileSync(f, 'utf8');
  } catch {
    continue;
  }
  for (const { cmd, line } of gitRecipes(text)) {
    const bad = optionAfterSeparator(cmd);
    if (bad) findings.push({ file: relative(ROOT, f), line, cmd, bad });
  }
}

for (const f of findings) {
  console.log(`  ✗ ${f.file}:${f.line} — option \`${f.bad}\` sits AFTER the bare \`--\`; git reads it as a pathspec.`);
  console.log(`      ${f.cmd}`);
  console.log('      Fix: every option BEFORE the separator — `git <cmd> -m "…" -- <paths>`.');
}
console.log(`validate:doc-recipes: ${findings.length} error(s) across ${files.length} doc(s) — recipe argument order.`);
process.exit(findings.length > 0 ? 1 : 0);
