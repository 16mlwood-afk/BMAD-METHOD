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

// Sandbox git MUST NOT inherit the outer repo's git env. `cwd` / `git -C` do NOT override
// GIT_INDEX_FILE et al, and under a PATH-SCOPED commit the parent's GIT_INDEX_FILE is the
// TEMP index git will build the commit tree from — so an inherited `git add -A` in a sandbox
// writes sandbox-only blobs into the real commit and kills it with `Error building trees`.
// Full account (this suite was the first of two confirmed instances): test/lib/clean-git-env.js
// and fork-gaps FG-2026-07-25-12. Proven here: 13/13 standalone AND 13/13 with GIT_INDEX_FILE
// set; it was 11/13 leaked before the fix.
const { cleanGitEnv: cleanEnv } = require('./lib/clean-git-env');

function git(cwd, args) {
  execFileSync('git', args, { cwd, stdio: 'pipe', env: cleanEnv() });
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

// A minimal v6.8 SKILLS-LAYOUT target: a git repo with .claude/skills committed and NO
// _bmad/bmm/workflows dir. The targets file still names <root>/_bmad/bmm/workflows (that path
// simply doesn't exist), which is exactly how the script detects the skills layout.
function makeSkillsLayoutProject(home, name) {
  const root = path.join(home, name);
  const skill = path.join(root, '.claude', 'skills', 'bmad-example');
  fs.mkdirSync(skill, { recursive: true });
  fs.writeFileSync(path.join(skill, 'SKILL.md'), '# committed baseline\n');
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
      env: cleanEnv({ HOME: home }),
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
  // fork-gap 2026-07-20: the skills-layout delivery path bypassed the guard entirely.
  const slClean = makeSkillsLayoutProject(home, 'sl-clean-proj');
  const slDirty = makeSkillsLayoutProject(home, 'sl-dirty-proj');
  const slUntracked = makeSkillsLayoutProject(home, 'sl-untracked-proj');

  const targets =
    [clean, dirty, untracked, slClean, slDirty, slUntracked].map((p) => path.join(p, '_bmad', 'bmm', 'workflows')).join('\n') + '\n';
  fs.writeFileSync(path.join(home, '.bmad-targets'), targets);

  // dirty-proj: uncommitted TRACKED modification in a managed path (a peer session mid-edit).
  fs.writeFileSync(path.join(dirty, '_bmad', 'bmm', 'workflows', 'shared', 'STANDARDS.md'), '# peer edit in flight\n');
  // untracked-proj: only an UNTRACKED new file — classify_local_only's job, NOT the guard's.
  fs.writeFileSync(path.join(untracked, '_bmad', 'bmm', 'workflows', 'shared', 'local-note.md'), '# untracked local\n');
  // sl-dirty-proj: the SAME hazard on the skills-layout path — a peer mid-edit in .claude/skills.
  fs.writeFileSync(path.join(slDirty, '.claude', 'skills', 'bmad-example', 'SKILL.md'), '# peer edit in flight\n');
  // sl-untracked-proj: untracked-only on the skills layout — must behave like its old-layout twin.
  fs.writeFileSync(path.join(slUntracked, '.claude', 'skills', 'bmad-example', 'local-note.md'), '# untracked local\n');

  const SKIP = /sync would SKIP this target/;

  console.log('skip-if-dirty guard — golden cases (drives the real sync-bmad-workflows.sh)');
  ok('dirty tracked modification → sync would SKIP', SKIP.test(runCheck(home, dirty)));
  ok('clean managed tree → not skipped', !SKIP.test(runCheck(home, clean)));
  ok('untracked-only → not skipped (guard ignores untracked; classify_local_only owns it)', !SKIP.test(runCheck(home, untracked)));

  // --- Layout symmetry (fork-gap 2026-07-20) ---
  // The guard must behave IDENTICALLY on the v6.8 skills-layout path. Before the fix,
  // deliver_skills_layout_project ran with no guard at all while --check advertised one.
  console.log('\nskills-layout parity — the guard is layout-agnostic');
  ok('skills-layout dirty tracked modification → sync would SKIP', SKIP.test(runCheck(home, slDirty)));
  ok('skills-layout clean managed tree → not skipped', !SKIP.test(runCheck(home, slClean)));
  ok('skills-layout untracked-only → not skipped (parity with old layout)', !SKIP.test(runCheck(home, slUntracked)));

  // Bind to the REAL guard implementation so weakening it breaks this test.
  const src = fs.readFileSync(SCRIPT, 'utf8');
  ok('guard predicate uses --untracked-files=no', /--untracked-files=no/.test(src));
  ok('guard scopes _bmad/bmm/workflows', /BMAD_MANAGED_GIT_PATHS=\([^)]*_bmad\/bmm\/workflows/.test(src));
  ok('sync-mode refusal present', /BLOCK \$project — uncommitted TRACKED changes/.test(src));
  // The gate is a shared function called once per target, NOT re-inlined per write path — that
  // re-inlining is precisely how the skills-layout path came to have no guard.
  ok('gate is a layout-agnostic function', /bmad_target_blocked_dirty\(\)\s*\{/.test(src));
  ok('skills-layout dispatch calls the gate', /elif bmad_target_blocked_dirty "\$sl_proot"/.test(src));
  ok('old-layout dispatch calls the same gate', /if bmad_target_blocked_dirty "\$project_root"/.test(src));
  ok('--force is the sole override, inside the shared gate', /bmad_target_blocked_dirty\(\)[\s\S]{0,400}?\$FORCE && return 1/.test(src));

  console.log(`\n  ${passed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
} finally {
  fs.rmSync(home, { recursive: true, force: true });
}
