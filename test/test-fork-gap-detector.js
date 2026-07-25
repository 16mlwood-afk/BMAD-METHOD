// Golden-case regression lock for the fork-gap register tooling (fork-gap 2026-07-20).
//
// THREE STRUCTURAL INVARIANTS are locked here. I1 and I2 predate schema v1 and are carried
// forward unchanged in meaning; I3 arrives with the write-time gate (2026-07-25).
//
//   I1. THE REGISTER MUST NEVER COUNT ITSELF AS EVIDENCE.
//       fork-gaps.md lives under docs/, so an entry whose target is the broad `docs/`
//       directory would match its OWN prose and manufacture a phantom "already fixed"
//       verdict. A detector that fabricates closes is worse than no detector — the close-out
//       it invites is a human marking real work done. Directory searches must exclude
//       fork-gaps.md and fork-gaps-archive.md, and a file target that IS the register must be
//       skipped outright.
//
//   I2. THE SWEEP NEVER MUTATES THE REGISTER AND NEVER FAILS A BUILD.
//       It flags candidates for human review and exits 0. Closing a gap stays a human call —
//       a present marker proves a string exists, not that the gap is resolved.
//
//   I3. CREATION MODE IS THE ONLY FAILING PATH, AND IT FAILS OPEN.
//       A NEW entry (added in the staged diff) whose marker ALREADY exists in its target is
//       an ERROR: either the marker is too generic to prove anything, or the gap is already
//       fixed and should not be logged open. When the staged diff cannot be read, creation
//       mode degrades to advisory rather than blocking — a detector that cannot see must not
//       block.
//
// Hermetic: builds a throwaway fork-shaped tree and points the REAL linter at it via
// FORK_GAP_ROOT, so no assertion depends on live fork content. Also binds to the real source
// so a future edit that weakens an invariant fails here.

const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const FORK = path.join(__dirname, '..');
const LINT = path.join(FORK, 'tools', 'lib', 'fork_gap_lint.py');
const DETECTOR = path.join(FORK, 'tools', 'check-fork-gap-stale-open.sh');

let passed = 0;
let failed = 0;
function ok(name, cond) {
  console.log(`  ${cond ? '✓' : '✗'} ${name}`);
  cond ? passed++ : failed++;
}

function sandbox() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'forkgapdet-'));
  fs.mkdirSync(path.join(root, 'docs'), { recursive: true });
  fs.mkdirSync(path.join(root, 'custom', 'workflows'), { recursive: true });
  return root;
}

function entry({ id, target, marker, state = 'open', scope = 'fork' }) {
  return [
    `## ${id} — fixture entry`,
    '',
    '```yaml',
    `id: ${id}`,
    'class: fixture',
    `scope: ${scope}`,
    `target: ${target}`,
    `marker: "${marker}"`,
    `state: ${state}`,
    'owner: fork-maintenance',
    '```',
    '',
    '### Incident',
    'fixture evidence.',
    '',
    '### Work',
    '',
    '**Status (fixture):** fixture.',
    '',
  ].join('\n');
}

function run(root, mode, args = []) {
  return execFileSync('python3', [LINT, mode, ...args], {
    encoding: 'utf8',
    stdio: 'pipe',
    env: { ...process.env, FORK_GAP_ROOT: root },
  });
}

function exitCodeOf(root, mode, args = []) {
  try {
    execFileSync('python3', [LINT, mode, ...args], {
      stdio: 'pipe',
      env: { ...process.env, FORK_GAP_ROOT: root },
    });
    return 0;
  } catch (error) {
    return error.status;
  }
}

function candidates(out) {
  const m = out.match(/(\d+) candidate\(s\)/);
  return m ? Number(m[1]) : -1;
}

console.log('\nFork-gap register tooling — invariant tests\n');

const root = sandbox();
try {
  const register = path.join(root, 'docs', 'fork-gaps.md');
  const header = ['# Fork Gaps', '', '## Open', ''].join('\n');

  // ---- I1a: a marker present ONLY in the register's own prose is not evidence ----
  fs.writeFileSync(register, header + entry({ id: 'FG-2026-01-01-01', target: 'docs/fork-gaps.md', marker: 'self-match-token' }));
  ok('I1 a target that IS the register is skipped', candidates(run(root, 'stale-open')) === 0);

  // ---- I1b: a DIRECTORY target must not self-match through the register inside it ----
  fs.writeFileSync(register, header + entry({ id: 'FG-2026-01-01-02', target: 'docs/', marker: 'dir-self-match-token' }));
  ok('I1 a directory target excludes the register from the search', candidates(run(root, 'stale-open')) === 0);

  // ---- I1c: a real hit in a real file is still found — the detector must still work ----
  fs.writeFileSync(path.join(root, 'custom', 'workflows', 'thing.md'), 'contains real-fix-token here');
  fs.writeFileSync(register, header + entry({ id: 'FG-2026-01-01-03', target: 'custom/workflows/thing.md', marker: 'real-fix-token' }));
  ok('detector still finds a genuine marker hit', candidates(run(root, 'stale-open')) === 1);

  // ---- I2: never mutates; sweep always exits 0 even with a live candidate ----
  const before = fs.readFileSync(register, 'utf8');
  run(root, 'stale-open');
  ok('I2 sweep never mutates the register', fs.readFileSync(register, 'utf8') === before);
  ok('I2 sweep exits 0 (advisory, never a build gate)', exitCodeOf(root, 'stale-open') === 0);

  // ---- I3: creation mode fails OPEN when the staged diff is unreadable ----
  // The sandbox is not a git repo, so the staged-id set is empty; a detector that cannot see
  // the diff must degrade to advisory rather than block every commit.
  ok('I3 creation mode degrades to advisory when the staged diff is unreadable', exitCodeOf(root, 'stale-open', ['--creation-mode']) === 0);

  // ---- schema gate: mechanical errors only, and it must actually fire ----
  fs.writeFileSync(register, header + entry({ id: 'FG-2026-01-01-04', target: 'custom/workflows/thing.md', marker: 'ab' }));
  ok('schema gate rejects a marker under 3 chars', exitCodeOf(root, 'schema') === 1);
  fs.writeFileSync(register, header + entry({ id: 'FG-2026-01-01-05', target: 'custom/workflows/thing.md', marker: 'wide-enough' }));
  ok('schema gate passes a conformant entry', exitCodeOf(root, 'schema') === 0);

  // ---- targets gate: scope-aware severity ----
  fs.writeFileSync(register, header + entry({ id: 'FG-2026-01-01-06', target: 'custom/workflows/gone.md', marker: 'wide-enough' }));
  ok('targets gate ERRORs on scope:fork pointer rot', exitCodeOf(root, 'targets') === 1);
  fs.writeFileSync(
    register,
    header +
      entry({
        id: 'FG-2026-01-01-07',
        target: 'custom/workflows/gone.md',
        marker: 'wide-enough',
        scope: 'project',
      }),
  );
  ok('targets gate only WARNs for a non-fork scope', exitCodeOf(root, 'targets') === 0);

  // ---- bound to the REAL source, so weakening an invariant breaks this test ----
  const src = fs.readFileSync(LINT, 'utf8');
  ok('I1 bound: the register self-files are named as an exclusion', /SELF_FILES = \("fork-gaps\.md", "fork-gaps-archive\.md"\)/.test(src));
  ok('I1 bound: the directory walk skips the self-files', /if fn in SELF_FILES:/.test(src));
  ok('I1 bound: a file target that IS the register is skipped', /if os\.path\.basename\(full\) in SELF_FILES:/.test(src));
  ok('I2 bound: no write path to the register', !/open\(GAPS[^)]*"w"/.test(src));
  ok(
    'I2 bound: sweep cannot raise errors (errors only under creation_mode)',
    /if creation_mode and e\.header\.get\("id"\) in new_ids:/.test(src),
  );

  const wrapper = fs.readFileSync(DETECTOR, 'utf8');
  ok('wrapper delegates to the shared parser (logic not re-implemented)', /fork_gap_lint\.py" stale-open/.test(wrapper));

  console.log(`\n  ${passed} passed, ${failed} failed`);
  if (failed) process.exit(1);
} finally {
  fs.rmSync(root, { recursive: true, force: true });
}
