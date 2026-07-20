// Golden-case regression lock for the stash preflight (fork-gap 2026-07-20).
//
// lint-staged stashes the working state before every commit. A corrupt EXISTING stash makes that
// backup fail as an opaque `invalid object … Error building trees` naming a path unrelated to the
// commit — while HEAD, the index and `git fsck` all look clean. In a fork shared by ~25 concurrent
// sessions that is a repo-wide commit outage whose only working escape is `--no-verify`.
//
// tools/check-stash-health.sh must catch it FIRST and print the real remedy. Two properties:
//   P1 a stash with a genuinely missing object => refuse (exit 1) and name `git stash drop`.
//   P2 everything else => silent exit 0. It is a diagnostic aid, so it must never become a new
//      way to block commits: healthy stash, no stash, and non-repo all pass.
//
// Corruption is REAL here, not mocked: a stash is created and one of its loose objects is deleted.

const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SCRIPT = path.join(__dirname, '..', 'tools', 'check-stash-health.sh');

let passed = 0;
let failed = 0;
function ok(name, cond) {
  console.log(`  ${cond ? '✓' : '✗'} ${name}`);
  cond ? passed++ : failed++;
}

function git(cwd, args) {
  return execFileSync('git', args, { cwd, stdio: 'pipe', encoding: 'utf8' });
}

// Returns { code, out } of the preflight run inside `cwd`.
function preflight(cwd) {
  try {
    const out = execFileSync('bash', [SCRIPT], { cwd, stdio: 'pipe', encoding: 'utf8' });
    return { code: 0, out };
  } catch (error) {
    return { code: error.status, out: `${error.stdout || ''}${error.stderr || ''}` };
  }
}

function newRepo(home, name) {
  const root = path.join(home, name);
  fs.mkdirSync(root, { recursive: true });
  git(root, ['init', '-q']);
  git(root, ['config', 'user.email', 't@t']);
  git(root, ['config', 'user.name', 't']);
  git(root, ['config', 'commit.gpgsign', 'false']);
  fs.writeFileSync(path.join(root, 'tracked.txt'), 'baseline\n');
  git(root, ['add', '-A']);
  git(root, ['commit', '-q', '-m', 'baseline']);
  return root;
}

const home = fs.mkdtempSync(path.join(os.tmpdir(), 'stashhealth-'));
try {
  // ---- P2: no stash at all → silent pass (the common case, must cost nothing) ----
  const clean = newRepo(home, 'nostash');
  let r = preflight(clean);
  ok('P2 no stash → exit 0, silent', r.code === 0 && r.out.trim() === '');

  // ---- P2: a HEALTHY stash → pass ----
  const healthy = newRepo(home, 'healthy');
  fs.writeFileSync(path.join(healthy, 'tracked.txt'), 'modified\n');
  fs.writeFileSync(path.join(healthy, 'untracked.txt'), 'new file\n');
  git(healthy, ['stash', 'push', '-u', '-m', 'healthy stash']);
  r = preflight(healthy);
  ok('P2 healthy stash → exit 0', r.code === 0);

  // ---- P1: a stash with a REALLY missing object → refuse ----
  const broken = newRepo(home, 'broken');
  fs.writeFileSync(path.join(broken, 'tracked.txt'), 'modified\n');
  fs.writeFileSync(path.join(broken, 'gone.txt'), 'this blob will be deleted\n');
  git(broken, ['stash', 'push', '-u', '-m', 'tmp']);

  // Delete one loose object belonging to the stash (the untracked blob).
  const objs = git(broken, ['rev-list', '--objects', '--no-walk', 'stash@{0}', 'stash@{0}^3'])
    .split('\n')
    .filter(Boolean)
    .map((l) => l.split(' '))
    .filter((p) => p[1] === 'gone.txt');
  const sha = objs.length > 0 ? objs[0][0] : null;
  const loose = sha ? path.join(broken, '.git', 'objects', sha.slice(0, 2), sha.slice(2)) : null;
  const removable = loose && fs.existsSync(loose);
  if (removable) fs.rmSync(loose);
  ok('setup: a stash object was really deleted (corruption is real, not mocked)', removable);

  r = preflight(broken);
  ok('P1 corrupt stash → exit 1 (refuses the commit)', r.code === 1);
  ok('P1 names the offending stash ref', /stash@\{0\}/.test(r.out));
  ok('P1 gives the exact remedy (git stash drop)', /git stash drop stash@\{0\}/.test(r.out));
  ok('P1 says it is unrestorable', /UNRESTORABLE/i.test(r.out));
  ok('P1 warns against --no-verify', /--no-verify/.test(r.out));

  // Context: the raw git error names a path unrelated to the commit, which is what misleads.
  // (In the live incident `git fsck` ALSO came back clean, making it worse; that depends on
  // whether the corrupt objects are reachable from a ref, so it is not asserted here.)
  let fsckOut = '';
  try {
    fsckOut = git(broken, ['fsck', '--connectivity-only']) || '';
  } catch (error) {
    fsckOut = `${error.stdout || ''}${error.stderr || ''}`;
  }
  ok('context: fsck output captured without throwing the test', typeof fsckOut === 'string');

  // ---- bind to the wiring so a future edit cannot silently unhook it ----
  // Compare EXECUTABLE lines, not any mention — the explanatory comment also says "lint-staged".
  const hookLines = fs
    .readFileSync(path.join(__dirname, '..', '.githooks', 'pre-commit'), 'utf8')
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith('#'));
  const stashLine = hookLines.findIndex((l) => l.includes('check-stash-health.sh'));
  const lintLine = hookLines.findIndex((l) => l.includes('lint-staged'));
  ok('wired into .githooks/pre-commit', stashLine !== -1);
  ok('runs BEFORE lint-staged (the whole point)', stashLine !== -1 && lintLine !== -1 && stashLine < lintLine);

  const src = fs.readFileSync(SCRIPT, 'utf8');
  ok('fails OPEN when health cannot be determined (not a new blocker)', /command -v git .*\|\| exit 0/.test(src));

  console.log(`\n  ${passed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
} finally {
  fs.rmSync(home, { recursive: true, force: true });
}
