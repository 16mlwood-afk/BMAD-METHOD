/**
 * clean-git-env.js — strip the OUTER repo out of a child git process's environment.
 *
 * USE THIS IN EVERY TEST THAT RUNS GIT IN A SANDBOX REPO. `cwd` and `git -C` do NOT
 * override these variables — git env vars win over the working directory, so a sandbox
 * `git add` inherits whatever the parent process was handed.
 *
 * Why it matters, concretely (root-caused 2026-07-25, fork-gaps FG-2026-07-25-12):
 * a PATH-SCOPED commit (`git commit -m … -- <paths>`) is a PARTIAL commit, so git builds a
 * TEMPORARY index and exports it to hooks as `GIT_INDEX_FILE`. The fork's pre-commit runs
 * `npm test`. Any test that then runs `git add` inside a throwaway repo writes ITS entries
 * into the real commit's index — entries whose blobs exist only in the sandbox object store.
 * The commit dies with:
 *
 *     error: invalid object 100644 <sha> for '<a sandbox fixture path>'
 *     error: Error building trees
 *
 * That failure was mis-filed for weeks as intermittent index corruption in the fork repo,
 * and the "fix" recorded in docs/manifest-contract.md §4a was to stop using the one-step
 * commit form — which re-opens the shared-index sweep hazard that rule exists to close.
 * Only the one-step form was ever affected, because only it hands hooks a temp index.
 *
 * Two fixture paths have already caused it: `.claude/skills/bmad-example/SKILL.md`
 * (test-sync-skip-if-dirty) and `tracked.txt` (test-stash-health). Assume the next test
 * that shells git in a sandbox will be the third unless it uses this helper.
 */
'use strict';

const GIT_ENV_TO_STRIP = [
  'GIT_INDEX_FILE',
  'GIT_DIR',
  'GIT_WORK_TREE',
  'GIT_OBJECT_DIRECTORY',
  'GIT_ALTERNATE_OBJECT_DIRECTORIES',
  'GIT_COMMON_DIR',
  'GIT_PREFIX',
];

/** process.env minus every var that would leak the OUTER repo into a sandbox git call. */
function cleanGitEnv(extra = {}) {
  const env = { ...process.env, ...extra };
  for (const k of GIT_ENV_TO_STRIP) delete env[k];
  return env;
}

module.exports = { cleanGitEnv, GIT_ENV_TO_STRIP };
