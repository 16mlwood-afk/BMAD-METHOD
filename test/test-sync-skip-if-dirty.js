// Golden-case regression lock for the skip-if-dirty guard (fork-gap 2026-07-10).
//
// The 13-project `rsync -a --delete` fan-out in sync-bmad-workflows.sh must REFUSE any target
// with uncommitted TRACKED modifications in BMAD-managed paths — the deterministic backstop for
// the highest-blast-radius action in the blast-radius autonomy ladder
// (feedback-lead-on-policy-governed-maintenance, Tier 3). Drives the REAL script end-to-end via
// `--check --only` against constructed temp git projects, and binds to the guard's source so a
// future edit that weakens it breaks this test.

const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SCRIPT = path.join(__dirname, '..', 'sync-bmad-workflows.sh');
let passed = 0;
let failed = 0;

function ok(name, cond) {
  if (cond) {
    console.log(`  ✓ ${name}`);
    passed++;
  } else {
    console.log(`  ✗ ${name}`);
    failed++;
  }
}

function git(cwd, args) {
  execFileSync('git', args, { cwd, stdio: 'pipe' });
}

// A minimal, valid sync target: a git repo whose _bmad/bmm/workflows exists with a committed
// managed file. Returns the project root.
function makeProject(home, name) {
  const root = path.join(home, name);
  const wf = path.join(root, '_bmad', 'bmm', 'workflows', 'shared');
  fs.mkdirSync(wf, { recursive: true });
  fs.writeFileSync(path.join(wf, 'STANDARDS.md'), '# committed baseline\n');
  git(root, ['init', '-q']);
  git(root, ['config', 'user.email', 't@t']);
  git(root, ['config', 'user.name', 't']);
  git(root, ['config', 'commit.gpgsign', 'false']);
  git(root, ['add', '-A']);
  git(root, ['commit', '-q', '-m', 'baseline']);
  return root;
}

function runCheck(home, projectRoot) {
  // Real script, --check (non-destructive) --only the one project. Temp HOME → temp targets file.
  try {
    return execFileSync('bash', [SCRIPT, '--check', '--only', projectRoot], {
      env: { ...process.env, HOME: home },
      encoding: 'utf8',
      stdio: 'pipe',
    });
  } catch (error) {
    // --check can exit non-zero on drift; stdout carries the surface we assert on.
    return (error.stdout || '') + (error.stderr || '');
  }
}

const home = fs.mkdtempSync(path.join(os.tmpdir(), 'bmad-skipdirty-'));
try {
  const clean = makeProject(home, 'clean-proj');
  const dirty = makeProject(home, 'dirty-proj');
  const untracked = makeProject(home, 'untracked-proj');

  const targets = [clean, dirty, untracked].map((p) => path.join(p, '_bmad', 'bmm', 'workflows')).join('\n') + '\n';
  fs.writeFileSync(path.join(home, '.bmad-targets'), targets);

  // dirty-proj: uncommitted TRACKED modification in a managed path (a peer session mid-edit).
  fs.writeFileSync(path.join(dirty, '_bmad', 'bmm', 'workflows', 'shared', 'STANDARDS.md'), '# peer edit in flight\n');
  // untracked-proj: only an UNTRACKED new file — classify_local_only's job, NOT the guard's.
  fs.writeFileSync(path.join(untracked, '_bmad', 'bmm', 'workflows', 'shared', 'local-note.md'), '# untracked local\n');

  const SKIP = /sync would SKIP this target/;

  console.log('skip-if-dirty guard — golden cases (drives the real sync-bmad-workflows.sh)');
  ok('dirty tracked modification → sync would SKIP', SKIP.test(runCheck(home, dirty)));
  ok('clean managed tree → not skipped', !SKIP.test(runCheck(home, clean)));
  ok('untracked-only → not skipped (guard ignores untracked; classify_local_only owns it)', !SKIP.test(runCheck(home, untracked)));

  // Bind to the REAL guard implementation so weakening it breaks this test.
  const src = fs.readFileSync(SCRIPT, 'utf8');
  ok('guard predicate uses --untracked-files=no', /--untracked-files=no/.test(src));
  ok('guard scopes _bmad/bmm/workflows', /BMAD_MANAGED_GIT_PATHS=\([^)]*_bmad\/bmm\/workflows/.test(src));
  ok('sync-mode refusal present', /BLOCK \$project — uncommitted TRACKED changes/.test(src));

  console.log(`\n  ${passed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
} finally {
  fs.rmSync(home, { recursive: true, force: true });
}
