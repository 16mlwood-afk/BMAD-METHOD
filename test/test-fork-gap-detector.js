// Golden-case regression lock for the fork-gap register tooling (fork-gap 2026-07-20).
//
// SIX STRUCTURAL INVARIANTS are locked here. I1 and I2 predate schema v1 and are carried
// forward unchanged in meaning; I3 and I4 arrive with the write-time gate (2026-07-25); I5
// arrives with entry-scoped blocking (2026-07-31).
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
//   I4. ARCHIVING IS THE ONLY MUTATION, AND IT IS NEVER IN THE GATE.
//       Terminal entries (`closed` / `superseded`) must leave the live file or the register's
//       open-only property decays — but moving them MUTATES, and the checks do not mutate.
//       So the archiver is an explicit human-invoked command with a dry run by default, and
//       the gate's only role is to notice and say so. `partly` / `blocked` /
//       `fork-fixed-distribution-owed` all name owed work and stay live.
//
//   I5. A FINDING BLOCKS ONLY THE COMMIT THAT CAUSED IT.
//       The register is one append-only file written by many sessions, so failing the whole
//       commit on any finding anywhere in it let one bad entry freeze gap logging for
//       everyone. Blast radius shrank; the rules did not. A finding on an entry the commit
//       created OR edited still blocks; one on an untouched historical entry is printed in
//       full and does not. When touched-ness is undeterminable (no staged register, or
//       `--all`) the check degrades to a full audit — scoping must never be the reason a real
//       finding goes unenforced.
//
//   I6. THE SCAFFOLD CANNOT MANUFACTURE A HOLLOW ENTRY.
//       `new-entry` lowers authoring cost, which is the real lever on logging rate. But a
//       scaffold whose placeholders satisfy the rules is worse than none — `marker: "TODO"`
//       is four chars and passes everything. Every slot emits `<<FILL: …>>` and schema
//       rejects that token in any field or body prose. Matched IN FULL: a bare `<<`
//       false-fired on a real entry quoting a shell heredoc. The scaffold never writes, and
//       a missing register is empty rather than an error (else it cannot produce entry #1).
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
const ARCHIVER = path.join(FORK, 'tools', 'archive-fork-gaps.py');

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

  // ---- I4: the archiver is the ONLY mutating tool, and it is never in the gate ----
  // Terminal entries must leave the live file or the open-only property decays, but archiving
  // MUTATES — so it is explicit and human-invoked, and the gate only notices.
  fs.mkdirSync(path.join(root, 'tools'), { recursive: true });
  fs.writeFileSync(path.join(root, 'docs', 'fork-gaps-archive.md'), '# Archive\n');
  fs.writeFileSync(
    register,
    header +
      entry({ id: 'FG-2026-01-01-08', target: 'custom/workflows/thing.md', marker: 'wide-enough', state: 'closed' }) +
      entry({ id: 'FG-2026-01-01-09', target: 'custom/workflows/thing.md', marker: 'wide-enough', state: 'partly' }),
  );
  const liveBefore = fs.readFileSync(register, 'utf8');
  execFileSync('python3', [ARCHIVER], { stdio: 'pipe', env: { ...process.env, FORK_GAP_ROOT: root } });
  ok('I4 archiver dry run writes nothing', fs.readFileSync(register, 'utf8') === liveBefore);

  execFileSync('python3', [ARCHIVER, '--write'], { stdio: 'pipe', env: { ...process.env, FORK_GAP_ROOT: root } });
  const liveAfter = fs.readFileSync(register, 'utf8');
  const archived = fs.readFileSync(path.join(root, 'docs', 'fork-gaps-archive.md'), 'utf8');
  ok(
    'I4 archiver moves a closed entry out of the live file',
    !liveAfter.includes('FG-2026-01-01-08') && archived.includes('FG-2026-01-01-08'),
  );
  ok(
    'I4 archiver leaves a partly entry live (it names owed work)',
    liveAfter.includes('FG-2026-01-01-09') && !archived.includes('FG-2026-01-01-09'),
  );
  ok(
    'I4 no content lost across the move',
    liveBefore
      .split('\n')
      .filter((l) => l.trim())
      .every((l) => liveAfter.includes(l) || archived.includes(l)),
  );

  const hook = fs.readFileSync(path.join(FORK, '.githooks', 'pre-commit'), 'utf8');
  ok('I4 bound: the mutating archiver is NOT wired into the commit gate', !/archive-fork-gaps/.test(hook));

  // ----------------------------------------------------------------- I5
  //   I5. A FINDING BLOCKS ONLY THE COMMIT THAT CAUSED IT.
  //       fork-gaps.md is one append-only file written by many sessions. When ANY finding
  //       anywhere in it failed the whole commit, one bad entry froze gap logging for
  //       everyone: a session authored a valid entry, hit a wall left days earlier by
  //       someone else, abandoned the commit, and left its entry dirty. Three entries were
  //       stranded that way on 2026-07-30/31 and the logging rate fell from 12-14/day to
  //       1-4/day.
  //
  //       The rules did NOT get weaker — the blast radius got smaller. A finding on an
  //       entry the commit created or edited still blocks. A finding on an untouched
  //       historical entry is printed in full and does not block. And when touched-ness
  //       cannot be determined (no staged register — a manual sweep, or `--all`) the check
  //       degrades to the FULL audit it has always been, so scoping can never be the reason
  //       a real finding goes unenforced.
  const git = (root, ...args) => execFileSync('git', args, { cwd: root, stdio: 'pipe', encoding: 'utf8' });

  // `run` throws on a non-zero exit, and half of these cases exit 1 BY DESIGN — the whole
  // point is asserting what a blocking run prints. Capture stdout either way.
  const runOut = (root, mode, args = []) => {
    try {
      return run(root, mode, args);
    } catch (error) {
      return error.stdout || '';
    }
  };

  function gitSandbox(entries) {
    const root = sandbox();
    git(root, 'init', '-q', '.');
    git(root, 'config', 'user.email', 't@t');
    git(root, 'config', 'user.name', 't');
    fs.writeFileSync(path.join(root, 'docs', 'fork-gaps.md'), `# Fork Gaps\n\n## Open\n\n${entries}`);
    git(root, 'add', '-A');
    git(root, 'commit', '-qm', 'baseline');
    return root;
  }

  // Baseline: one historical entry whose scope:fork target rotted long ago.
  const ROTTED = entry({ id: 'FG-2026-01-01-01', target: 'custom/workflows/gone.md', marker: 'rotted marker' });
  const HEALTHY = entry({ id: 'FG-2026-01-01-02', target: 'custom/workflows', marker: 'healthy marker' });

  // (a) a VALID new entry lands even though the register already carries rot.
  let g = gitSandbox(`${ROTTED}\n${HEALTHY}`);
  const NEW_OK = entry({ id: 'FG-2026-01-02-02', target: 'custom/workflows', marker: 'brand new marker' });
  fs.appendFileSync(path.join(g, 'docs', 'fork-gaps.md'), `\n${NEW_OK}`);
  git(g, 'add', 'docs/fork-gaps.md');
  const outA = runOut(g, 'targets');
  ok('I5 pre-existing rot does NOT block a commit that did not touch it', exitCodeOf(g, 'targets') === 0);
  ok('I5 …and that rot is still REPORTED, not silently dropped', /FG-2026-01-01-01/.test(outA) && /pre-existing/.test(outA));
  fs.rmSync(g, { recursive: true, force: true });

  // (b) a NEW entry with a schema defect still blocks — strictness unchanged.
  g = gitSandbox(`${ROTTED}\n${HEALTHY}`);
  fs.appendFileSync(
    path.join(g, 'docs', 'fork-gaps.md'),
    `\n${entry({ id: 'FG-2026-01-02-03', target: 'custom/workflows', marker: 'x' })}`.replace('### Incident\nfixture evidence.\n', ''),
  );
  git(g, 'add', 'docs/fork-gaps.md');
  ok('I5 a NEW entry with a schema defect still BLOCKS', exitCodeOf(g, 'schema') === 1);
  fs.rmSync(g, { recursive: true, force: true });

  // (c) EDITING an existing entry into a broken state blocks — "touched" is new OR edited.
  g = gitSandbox(`${ROTTED}\n${HEALTHY}`);
  const gp = path.join(g, 'docs', 'fork-gaps.md');
  fs.writeFileSync(gp, fs.readFileSync(gp, 'utf8').replace('target: custom/workflows\n', 'target: custom/workflows/newly-rotted.md\n'));
  git(g, 'add', 'docs/fork-gaps.md');
  const outC = runOut(g, 'targets');
  ok('I5 EDITING an entry into pointer rot BLOCKS (touched = new OR edited)', exitCodeOf(g, 'targets') === 1);
  ok('I5 …and the untouched historical rot stays advisory in the same run', /pre-existing/.test(outC));
  fs.rmSync(g, { recursive: true, force: true });

  // (d) no staged register -> FULL audit. This is what keeps a manual sweep a real sweep;
  //     if this ever flips, scoping has become a way to hide findings.
  g = gitSandbox(`${ROTTED}\n${HEALTHY}`);
  const outD = runOut(g, 'targets');
  ok('I5 no staged register => FULL audit, historical rot blocks', exitCodeOf(g, 'targets') === 1);
  ok('I5 …and the run says so rather than claiming a scope', /full audit \(unscoped\)/.test(outD));
  ok(
    'I5 --all forces the full audit even with a staged register',
    (() => {
      fs.appendFileSync(path.join(g, 'docs', 'fork-gaps.md'), `\n${NEW_OK}`);
      git(g, 'add', 'docs/fork-gaps.md');
      return exitCodeOf(g, 'targets', ['--all']) === 1;
    })(),
  );
  fs.rmSync(g, { recursive: true, force: true });

  // ----------------------------------------------------------------- I6
  //   I6. THE SCAFFOLD CANNOT MANUFACTURE A HOLLOW ENTRY.
  //       `new-entry` exists because authoring cost is the lever on logging rate — the
  //       register is strict and offered only a validator that judges an entry AFTER it was
  //       hand-built. But a scaffold whose placeholders satisfy the rules is worse than no
  //       scaffold: `marker: "TODO"` is four characters and passes every mechanical check.
  //       So every slot emits `<<FILL: …>>` and schema REJECTS any field or body prose still
  //       carrying that token. Tightening, not relaxation, and it can only fire on the entry
  //       the author is adding.
  //
  //       The token is matched IN FULL. A bare `<<` false-fired immediately on a real entry
  //       whose prose quotes a shell heredoc (`python3 - <<'PY'`) — the indiscriminate-
  //       detector anti-pattern, caught by the live register on the first run. Both
  //       directions are locked below so neither regresses.
  const sc = sandbox();
  const scReg = path.join(sc, 'docs', 'fork-gaps.md');
  const HEAD_ONLY = ['# Fork Gaps', '', '## Open', ''].join('\n');

  fs.writeFileSync(scReg, HEAD_ONLY + run(sc, 'new-entry', ['--title', 'unfilled']));
  ok('I6 an UNFILLED scaffold is rejected by schema', exitCodeOf(sc, 'schema') === 1);

  const filled = run(sc, 'new-entry', [
    '--title',
    'a real defect',
    '--class',
    'pointer-rot',
    '--scope',
    'fork',
    '--target',
    'custom/workflows',
    '--marker',
    'a real marker',
  ]).replaceAll(/<<FILL:[\s\S]*?>>/g, 'real evidence the author wrote.');
  fs.writeFileSync(scReg, HEAD_ONLY + filled);
  ok('I6 a FILLED scaffold passes schema and targets', exitCodeOf(sc, 'schema') === 0 && exitCodeOf(sc, 'targets') === 0);

  // Prose quoting a heredoc must not read as a placeholder.
  fs.writeFileSync(
    scReg,
    HEAD_ONLY +
      entry({ id: 'FG-2026-02-02-01', target: 'custom/workflows', marker: 'heredoc case' }).replace(
        'fixture evidence.',
        "A session ran `python3 - <<'PY'` and it mattered. Prose, not a placeholder.",
      ),
  );
  ok('I6 prose quoting a heredoc is NOT a placeholder (no bare `<<` match)', exitCodeOf(sc, 'schema') === 0);

  // The scaffold must never write — the file-level no-mutation invariant.
  const beforeScaffold = fs.readFileSync(scReg, 'utf8');
  run(sc, 'new-entry', ['--title', 'does not write']);
  ok('I6 the scaffold never mutates the register', fs.readFileSync(scReg, 'utf8') === beforeScaffold);

  // Ids must not collide with entries already dated today.
  fs.writeFileSync(scReg, HEAD_ONLY + entry({ id: 'FG-2026-03-03-01', target: 'custom/workflows', marker: 'taken' }));
  const nextId = (run(sc, 'new-entry', ['--title', 'x', '--date', '2026-03-03']).match(/^id: (FG-\S+)/m) || [])[1];
  ok('I6 the next id skips ids already taken on that date', nextId === 'FG-2026-03-03-02');
  fs.rmSync(sc, { recursive: true, force: true });

  // (e) BOUND: the gate must keep firing only when the register is staged. If that guard is
  //     ever removed, every fork commit inherits the register's historical rot again.
  ok('I5 bound: the register gate still fires only when fork-gaps.md is staged', /grep -qx 'docs\/fork-gaps\.md'/.test(hook));

  console.log(`\n  ${passed} passed, ${failed} failed`);
  if (failed) process.exit(1);
} finally {
  fs.rmSync(root, { recursive: true, force: true });
}
