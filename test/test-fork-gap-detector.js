// Golden-case regression lock for the fork-gap stale-open detector (fork-gap 2026-07-20).
//
// TWO STRUCTURAL INVARIANTS are locked here, both promoted from one-off patches after they bit:
//
//   I1. THE REGISTER MUST NEVER COUNT ITSELF AS EVIDENCE.
//       fork-gaps.md lives under docs/, so an entry whose Target file is the broad `docs/`
//       directory will match its OWN prose and manufacture a phantom "already fixed" verdict.
//       A detector that fabricates closes is worse than no detector — the close-out it invites
//       is a human marking real work done. Directory searches must exclude fork-gaps.md and
//       fork-gaps-archive.md, and a file target that IS the register must be skipped outright.
//
//   I2. THE DETECTOR NEVER MUTATES THE REGISTER AND NEVER FAILS A BUILD.
//       It flags candidates for human review and exits 0. Closing a gap stays a human call —
//       a present marker proves a string exists, not that the gap is resolved.
//
// Hermetic: builds a throwaway fork-shaped tree (tools/ + docs/ + custom/) and copies the REAL
// scripts into it, so ROOT resolves inside the sandbox and no assertion depends on live fork
// content. Also binds to the real source so a future edit that weakens either invariant fails.

const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const FORK = path.join(__dirname, '..');
const DETECTOR = path.join(FORK, 'tools', 'check-fork-gap-stale-open.sh');
const LIB = path.join(FORK, 'tools', 'lib', 'fork-gap-paths.sh');

let passed = 0;
let failed = 0;
function ok(name, cond) {
  console.log(`  ${cond ? '✓' : '✗'} ${name}`);
  cond ? passed++ : failed++;
}

// A fork-shaped sandbox with the real detector + shared resolver copied in.
function sandbox() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'forkgapdet-'));
  fs.mkdirSync(path.join(root, 'tools', 'lib'), { recursive: true });
  fs.mkdirSync(path.join(root, 'docs'), { recursive: true });
  fs.mkdirSync(path.join(root, 'custom'), { recursive: true });
  fs.copyFileSync(DETECTOR, path.join(root, 'tools', 'check-fork-gap-stale-open.sh'));
  fs.copyFileSync(LIB, path.join(root, 'tools', 'lib', 'fork-gap-paths.sh'));
  fs.chmodSync(path.join(root, 'tools', 'check-fork-gap-stale-open.sh'), 0o755);
  return root;
}

function run(root, args = []) {
  const res = execFileSync('bash', [path.join(root, 'tools', 'check-fork-gap-stale-open.sh'), ...args], {
    encoding: 'utf8',
    stdio: 'pipe',
  });
  return res;
}

function candidates(out) {
  const m = out.match(/(\d+) stale-open candidate\(s\)/);
  return m ? Number(m[1]) : -1;
}

const root = sandbox();
try {
  const register = path.join(root, 'docs', 'fork-gaps.md');

  // ---- I1: self-match. The marker exists ONLY inside the register's own prose. ----
  fs.writeFileSync(
    register,
    [
      '# Fork Gaps',
      '## Open',
      '',
      '## 2026-01-01 — an entry whose target is the broad docs/ directory',
      '**Target file:** `docs/`',
      '**Marker:** `ZZSELFMATCHONLYZZ`',
      'Body prose mentioning ZZSELFMATCHONLYZZ exactly as a real gap would.',
      '',
    ].join('\n'),
  );
  let out = run(root);
  ok('I1 register does not count itself (docs/ target, marker only in the register)', candidates(out) === 0);

  // ---- true positive must survive the exclusion ----
  fs.writeFileSync(path.join(root, 'custom', 'fixed.md'), 'the fix landed: ZZREALFIXZZ present\n');
  fs.writeFileSync(path.join(root, 'custom', 'unfixed.md'), 'nothing here yet\n');
  fs.writeFileSync(
    register,
    [
      '# Fork Gaps',
      '## 2026-01-02 — a gap whose fix really did land',
      '**Target file:** `custom/fixed.md`',
      '**Marker:** `ZZREALFIXZZ`',
      '',
      '## 2026-01-03 — a gap that is genuinely still open',
      '**Target file:** `custom/unfixed.md`',
      '**Marker:** `ZZMISSINGZZ`',
      '',
    ].join('\n'),
  );
  out = run(root);
  ok('true positive still detected (marker present in a real target)', candidates(out) === 1);
  ok('genuinely-open gap is NOT flagged', !/2026-01-03/.test(out));
  ok(
    'candidate report carries evidence (target + marker + action)',
    /target:/.test(out) && /marker:/.test(out) && /review and close if correct/.test(out),
  );

  // ---- tagged entries excluded by default, included under --all ----
  fs.writeFileSync(
    register,
    [
      '# Fork Gaps',
      '## 2026-01-04 — already closed  `[RESOLVED: 2026-01-04 — done]`',
      '**Target file:** `custom/fixed.md`',
      '**Marker:** `ZZREALFIXZZ`',
      '',
    ].join('\n'),
  );
  ok('tagged entry excluded from the routine run', candidates(run(root)) === 0);
  ok('tagged entry included under --all (audit mode)', candidates(run(root, ['--all'])) === 1);

  // ---- I2: never mutates the register; always exits 0 ----
  const before = fs.readFileSync(register, 'utf8');
  run(root, ['--all']);
  ok('I2 detector never mutates the register', fs.readFileSync(register, 'utf8') === before);

  let exitCode = 0;
  try {
    execFileSync('bash', [path.join(root, 'tools', 'check-fork-gap-stale-open.sh'), '--all'], { stdio: 'pipe' });
  } catch (error) {
    exitCode = error.status;
  }
  ok('I2 detector exits 0 (advisory, never a build gate)', exitCode === 0);

  // ---- bind to the REAL source so weakening an invariant breaks this test ----
  const src = fs.readFileSync(DETECTOR, 'utf8');
  ok('I1 bound: directory search excludes fork-gaps.md', /--exclude='fork-gaps\.md'/.test(src));
  ok('I1 bound: directory search excludes fork-gaps-archive.md', /--exclude='fork-gaps-archive\.md'/.test(src));
  ok('I1 bound: a file target that IS the register is skipped', /fork-gaps\.md\|fork-gaps-archive\.md\)\s*continue/.test(src));
  ok('shares the resolver lib (is_checkable not re-implemented)', /lib\/fork-gap-paths\.sh/.test(src) && !/^is_checkable\(\)/m.test(src));
  ok('I2 bound: no write-redirect into the register', !/>\s*"?\$GAPS/.test(src));

  const lib = fs.readFileSync(LIB, 'utf8');
  ok('shared resolver exposes fg_is_checkable', /fg_is_checkable\(\)\s*\{/.test(lib));

  console.log(`\n  ${passed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
} finally {
  fs.rmSync(root, { recursive: true, force: true });
}
