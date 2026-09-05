#!/usr/bin/env python3
"""EXECUTE the distributor's target loop once, against a throwaway project.

WHY THIS AND NOT ONLY A STATIC CHECK. Three distributor defects shipped on 2026-08-31 and
not one was reachable without running the loop:

  - `$proot` used where the loop binds `$project_root` — aborted all fourteen targets under
    `set -u`, after printing three green OK lines, so the visible tail of a FAILING run
    read as success;
  - the flattened shared-policy refresh guarded on a flag, so it never fired for a target
    that had the directory without the flag, and one project sat a contract version behind
    for weeks;
  - a blanket `git add` over a managed tree, which recorded 246 deletions as intentional.

`bash -n` sees none of these. The sister static suite (test-sync-scope-smoke.py) catches
the first class by scanning variable binding, which is cheaper and would have caught it
before it left the tree — this one is the complement: it runs the body.

The project here is DISPOSABLE and lives in a temp directory. It is never a real target,
and the run is pointed at it by BMAD_TARGETS_FILE so the real fourteen are untouched.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FORK = Path(__file__).resolve().parent.parent
SYNC = FORK / "sync-bmad-workflows.sh"
PASS, FAIL = [], []


def check(label, got, want):
    ok = got == want
    (PASS if ok else FAIL).append(label)
    print(("  PASS  " if ok else "  FAIL  ") + label
          + ("" if ok else f"\n          got={got!r} want={want!r}"))


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def make_project(root: Path, *, with_bmad_shared: bool):
    """A minimal but REAL target: git repo, config, workflow tree."""
    (root / "_bmad" / "bmm" / "workflows").mkdir(parents=True)
    (root / "_bmad" / "bmm" / "config.yaml").write_text(
        "project_name: smoke\nproject_phase: brownfield\n")
    if with_bmad_shared:
        d = root / "_bmad" / "bmad-shared"
        d.mkdir(parents=True)
        # Deliberately STALE, so a refresh that does not run is detectable.
        (d / "delivery-to-main.md").write_text("---\ncontract_version: 0\n---\nstale\n")
    git("init", "-q", "-b", "main", cwd=root)
    git("config", "user.email", "smoke@test", cwd=root)
    git("config", "user.name", "smoke", cwd=root)
    git("add", "-A", cwd=root)
    git("commit", "-qm", "init", cwd=root)


def run_sync(root: Path, targets_file: Path, *extra):
    env = dict(os.environ, BMAD_TARGETS_FILE=str(targets_file))
    return subprocess.run(
        [str(SYNC), "--only", str(root), "--allow-unclean-source", *extra],
        cwd=FORK, capture_output=True, text=True, env=env)


print("distributor execution smoke (runs the target loop):\n")

with tempfile.TemporaryDirectory() as td:
    td = Path(td)

    # --- E1: the loop body RUNS to completion on a plain target ---------------
    proj = td / "plain"
    proj.mkdir()
    make_project(proj, with_bmad_shared=False)
    tf = td / "targets"
    tf.write_text(f"{proj}/_bmad/bmm/workflows\n")

    r = run_sync(proj, tf)
    check("E1  the target loop completes (no unbound variable, no abort)", r.returncode, 0)
    check("E1b it reports the target as synced",
          "SYNC" in r.stdout or "OK" in r.stdout, True)
    # The specific 2026-08-31 abort signature, named so it cannot come back quietly.
    check("E1c no unbound-variable abort in the loop",
          "unbound variable" in (r.stdout + r.stderr), False)
    check("E1d workflows were actually delivered",
          (proj / "_bmad" / "bmm" / "workflows" / "shared").is_dir(), True)

    # --- E2: a target WITH the flattened shared copy gets it refreshed --------
    #     This is the flag-conditional defect. The fixture ships contract_version 0;
    #     if the refresh does not fire, it stays 0 and the run still "succeeds".
    proj2 = td / "shared"
    proj2.mkdir()
    make_project(proj2, with_bmad_shared=True)
    tf2 = td / "targets2"
    tf2.write_text(f"{proj2}/_bmad/bmm/workflows\n")

    r2 = run_sync(proj2, tf2)
    check("E2  the loop completes on a target with a flattened shared copy", r2.returncode, 0)
    body = (proj2 / "_bmad" / "bmad-shared" / "delivery-to-main.md").read_text()
    check("E2b the stale shared copy was REFRESHED (not left at contract_version 0)",
          "contract_version: 0" in body, False)
    check("E2c and it now carries real content", len(body) > 200, True)

    # --- E3: a target WITHOUT the directory does not have one created ---------
    #     Creating it would silently migrate a target's layout as a side effect of a sync.
    check("E3  no flattened copy is created where none existed",
          (proj / "_bmad" / "bmad-shared").exists(), False)

    # --- E4: the run is idempotent — a second pass changes nothing ------------
    before = subprocess.run(["git", "status", "--porcelain"], cwd=proj2,
                            capture_output=True, text=True).stdout
    git("add", "-A", cwd=proj2)
    git("commit", "-qm", "after first sync", cwd=proj2)
    run_sync(proj2, tf2)
    after = subprocess.run(["git", "status", "--porcelain", "--", "_bmad/bmm/workflows"],
                           cwd=proj2, capture_output=True, text=True).stdout
    check("E4  a second sync leaves the workflow tree unchanged", after.strip(), "")

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
