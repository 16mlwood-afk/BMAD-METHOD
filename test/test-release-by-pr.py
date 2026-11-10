#!/usr/bin/env python3
"""Golden cases for the release LAST MILE: a release reaches a project's origin through a
pull request, never as a commit stranded on the project's local main.

Expected behaviour comes from the owner's delivery rule (~/.claude/CLAUDE.md, "Delivery
mechanics are MINE": commit -> push -> PR -> merge) and docs/global-bmad-workflow.md
(routine distribution executes; the owner is not the operator). Evidence of the defect:
eleven projects carried 6-13 `chore(bmad): distribute release` commits, absent from
origin/main for five weeks, and a failed push anywhere in that path was swallowed.

Fixtures are throwaway repos: a bare "origin", a project clone whose local main has
DIVERGED from origin, and a stub syncer standing in for sync-bmad-workflows.sh.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

FORK = Path(__file__).resolve().parent.parent
TOOL = FORK / "tools" / "bmad-release.py"
PASS, FAIL = [], []

_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
_ENV.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
            GIT_COMMITTER_EMAIL="t@t")


def check(label, got, want):
    ok = got == want
    (PASS if ok else FAIL).append(label)
    print(("  PASS  " if ok else "  FAIL  ") + label + ("" if ok else f"\n          got={got!r} want={want!r}"))


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=_ENV)


def gout(cwd, *args):
    return git(cwd, *args).stdout.strip()


spec = importlib.util.spec_from_file_location("bmad_release_pr", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SHA = gout(FORK, "rev-parse", "HEAD")
TREE = gout(FORK, "rev-parse", "HEAD^{tree}")


def fixture(td):
    """-> (proj, origin, wt). proj's local main carries a stranded release commit AND
    origin/main has moved on, so local main cannot fast-forward."""
    td = Path(td)
    origin = td / "origin.git"
    git(td, "init", "-q", "--bare", "-b", "main", str(origin))
    seed = td / "seed"
    git(td, "clone", "-q", str(origin), str(seed))
    (seed / "README.md").write_text("app\n")
    git(seed, "add", "."), git(seed, "commit", "-q", "-m", "init")
    git(seed, "push", "-q", "origin", "HEAD:main")
    proj = td / "proj"
    git(td, "clone", "-q", str(origin), str(proj))
    (proj / "_bmad").mkdir()
    (proj / "_bmad" / "old.md").write_text("old release\n")
    git(proj, "add", "."), git(proj, "commit", "-q", "-m", "chore(bmad): distribute release 0ld0ld0ld0ld")
    (seed / "app.txt").write_text("app work\n")
    git(seed, "add", "."), git(seed, "commit", "-q", "-m", "feat: app work")
    git(seed, "push", "-q", "origin", "HEAD:main")
    git(proj, "fetch", "-q", "origin")
    wt = td / "wt"
    wt.mkdir()
    sync = wt / "sync-bmad-workflows.sh"
    sync.write_text('#!/bin/bash\nwhile [[ $# -gt 0 ]]; do [[ "$1" == "--only" ]] && T="$2"; shift; done\n'
                    'mkdir -p "$T/_bmad/bmm/workflows"; echo "new release" > "$T/_bmad/bmm/workflows/demo.md"\n')
    sync.chmod(0o755)
    return proj, origin, wt


class FakeGh:
    def __init__(self, ok=True):
        self.calls, self.ok = [], ok

    def __call__(self, args, cwd=None):
        self.calls.append(args)
        return subprocess.CompletedProcess(args, 0 if self.ok else 1,
                                           "https://github.com/o/r/pull/7\n" if self.ok else "",
                                           "" if self.ok else "gh: boom")


mod.repo_slug = lambda real: "o/r"
T = {"id": "fx", "path": "unused"}

print("release last-mile golden cases:\n")

# G1 -- a target whose local main has DIVERGED gets a pull request, not a local commit.
with tempfile.TemporaryDirectory() as td:
    proj, origin, wt = fixture(td)
    gh = FakeGh()
    mod.gh_run = gh
    local_before = gout(proj, "rev-parse", "HEAD")
    origin_main_before = gout(origin, "rev-parse", "refs/heads/main")
    results, proposed, exceptions = [], [], []
    tmp = Path(td) / "work"
    tmp.mkdir()
    status = mod.record_pr_delivery(dict(T, path=str(proj)), proj, wt, SHA, TREE, tmp,
                                    results, proposed, exceptions)
    branch = f"bmad/release-{SHA[:12]}"
    check("G1a outcome is a PR", status, "pr")
    check("G1b local main was not touched", gout(proj, "rev-parse", "HEAD"), local_before)
    check("G1c origin/main was not pushed to directly", gout(origin, "rev-parse", "refs/heads/main"), origin_main_before)
    check("G1d the release branch is on origin", bool(gout(origin, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}")), True)
    check("G1e the branch is built on origin/main's tip", gout(origin, "merge-base", branch, "main"), origin_main_before)
    check("G1f it carries the release content", gout(origin, "show", f"{branch}:_bmad/bmm/workflows/demo.md"), "new release")
    check("G1g it does NOT carry the stranded local commit", git(origin, "cat-file", "-e", f"{branch}:_bmad/old.md").returncode != 0, True)
    check("G1h gh was asked for a PR on that head", any(c[:2] == ["pr", "create"] and branch in c for c in gh.calls), True)
    check("G1i the PR is recorded as proposed, no exception", (len(proposed), exceptions), (1, []))
    check("G1j the throwaway project worktree is gone", [l for l in gout(proj, "worktree", "list").splitlines() if "proj-fx" in l], [])

    # G3 -- after the PR merges, the main checkout is levelled and the stranded commits
    #       survive on a pushed backup branch.
    git(origin, "update-ref", "refs/heads/main", branch)  # the merge
    stranded = gout(proj, "rev-parse", "HEAD")
    st, detail = mod.align_main(dict(T, path=str(proj)), proj, SHA, today="20261110")
    check("G3a aligned", st, "aligned")
    check("G3b local main equals origin/main", gout(proj, "rev-parse", "HEAD"), gout(origin, "rev-parse", "refs/heads/main"))
    check("G3c backup branch on the REMOTE holds the stranded commit",
          gout(origin, "rev-parse", "refs/heads/bmad-backup/local-main-20261110"), stranded)
    check("G3d the working tree carries the release content", (proj / "_bmad/bmm/workflows/demo.md").read_text().strip(), "new release")

# G2 -- a FAILED PUSH is a named refusal, and it is ledgered. Never swallowed.
with tempfile.TemporaryDirectory() as td:
    proj, origin, wt = fixture(td)
    mod.gh_run = FakeGh()
    git(proj, "config", "remote.origin.pushurl", str(Path(td) / "does-not-exist.git"))
    results, proposed, exceptions = [], [], []
    tmp = Path(td) / "work"
    tmp.mkdir()
    status = mod.record_pr_delivery(dict(T, path=str(proj)), proj, wt, SHA, TREE, tmp,
                                    results, proposed, exceptions)
    check("G2a push failure is a refusal", status, "refused")
    check("G2b it is NAMED", exceptions[0][1].startswith("PUSH REFUSED:"), True)
    check("G2c nothing was proposed", proposed, [])
    old = mod.LEDGER
    mod.LEDGER = Path(td) / "ledger.jsonl"
    try:
        mod.write_ledger(SHA, TREE, results, proposed, exceptions)
        row = json.loads(mod.LEDGER.read_text().splitlines()[-1])
    finally:
        mod.LEDGER = old
    check("G2d the ledger row carries the named exception",
          [e["reason"].split(":")[0] for e in row["exceptions"]], ["PUSH REFUSED"])
    check("G2e and says it was not delivered", row["delivered"], [])

# G4 -- a PR that cannot be opened is also named (the branch is pushed, the PR is not).
with tempfile.TemporaryDirectory() as td:
    proj, origin, wt = fixture(td)
    mod.gh_run = FakeGh(ok=False)
    results, proposed, exceptions = [], [], []
    tmp = Path(td) / "work"
    tmp.mkdir()
    mod.record_pr_delivery(dict(T, path=str(proj)), proj, wt, SHA, TREE, tmp, results, proposed, exceptions)
    check("G4 failed PR creation is a named exception", exceptions[0][1].startswith("PR REFUSED:"), True)

# G5 -- align-main stops on project work, and on a release that has not reached origin.
with tempfile.TemporaryDirectory() as td:
    proj, origin, wt = fixture(td)
    st, detail = mod.align_main(dict(T, path=str(proj)), proj, SHA, today="20261110")
    check("G5a release not on origin: main is left alone", (st, detail.split(":")[0]), ("refused", "RELEASE NOT ON ORIGIN"))
    (proj / "work.txt").write_text("real work\n")
    git(proj, "add", "."), git(proj, "commit", "-q", "-m", "feat: project work")
    st, detail = mod.align_main(dict(T, path=str(proj)), proj, SHA, today="20261110")
    check("G5b project work on local main is never reset", (st, detail.split(":")[0]), ("refused", "PROJECT WORK ON LOCAL MAIN"))

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
