#!/usr/bin/env python3
"""bmad-release — the release-and-distribution boundary for the BMAD fork.

THE MODEL, stated because the old one was implicit and wrong.

    Canonical source   ~/bmad-method-v6, branch `custom`, at an immutable commit SHA
    Release unit       a validated commit on origin/custom
    Distribution       source SHA -> registry -> replica sync -> verification -> receipt
    Targets            ~/.bmad-targets.json, approved roots only
    Replica rule       a project's BMAD tree is DISTRIBUTED STATE, never an authoring surface

The source of truth is not "the fork directory". It is origin/custom at a specific,
verified commit. Previously one half of the sync warned about unpushed commits while the
other half copied whatever working tree happened to be checked out — so the release could
carry a feature branch, or an uncommitted edit, and nothing said so.

This tool owns the release boundary ONLY. The actual copying, skills porting, hook merge
and command generation stay in sync-bmad-workflows.sh, which is run FROM a clean detached
worktree at the release SHA. Reimplementing that here would fork the distributor in two.

    bmad-release.py check       read-only preflight; writes nothing
    bmad-release.py publish     release: test, dry-run, sync, receipt, verify, ledger
    bmad-release.py reconcile   read-only drift classification per target
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

FORK = Path(__file__).resolve().parent.parent
REGISTRY = Path.home() / ".bmad-targets.json"
LEGACY_TARGETS = Path.home() / ".bmad-targets"
LEDGER = FORK / "docs" / "release-ledger.jsonl"
CHANNEL = "custom"
REMOTE = "myfork"
RECEIPT = ".bmad-distribution.json"
TOOL_VERSION = "1.0.0"

STATES = ("CURRENT", "STALE", "LOCAL_DRIFT", "MISSING", "UNREACHABLE",
          "MISREGISTERED", "UNSAFE_PATH", "PARTIAL_RELEASE")


def sh(args, cwd=None, check=False):
    r = subprocess.run(args, cwd=cwd or FORK, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed: {r.stderr.strip()}")
    return r


def out(args, cwd=None):
    r = sh(args, cwd)
    return r.stdout.strip() if r.returncode == 0 else ""


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- source gate
def source_gate(fetch=True):
    """Findings about whether a canonical release commit can be identified at all."""
    f = []
    if fetch:
        if sh(["git", "fetch", REMOTE, CHANNEL, "--quiet"]).returncode != 0:
            f.append(("BLOCK", f"cannot fetch {REMOTE}/{CHANNEL} — the canonical revision "
                               "cannot be verified, so nothing may be released"))
    head_branch = out(["git", "branch", "--show-current"])
    if head_branch != CHANNEL:
        f.append(("BLOCK", f"fork HEAD is on {head_branch or '(detached)'}, not {CHANNEL} — "
                           "a release is cut from the canonical channel only"))
    dirty = out(["git", "status", "--porcelain", "--", "custom", "src/modules", "tools", "test"])
    if dirty:
        f.append(("BLOCK", "the fork worktree is dirty in release-relevant paths:\n"
                  + "\n".join("      " + l for l in dirty.splitlines())))
    local = out(["git", "rev-parse", f"refs/heads/{CHANNEL}"])
    remote = out(["git", "rev-parse", f"refs/remotes/{REMOTE}/{CHANNEL}"])
    if not remote:
        f.append(("BLOCK", f"{REMOTE}/{CHANNEL} does not resolve"))
    elif local != remote:
        ahead = out(["git", "rev-list", "--count", f"{REMOTE}/{CHANNEL}..refs/heads/{CHANNEL}"])
        behind = out(["git", "rev-list", "--count", f"refs/heads/{CHANNEL}..{REMOTE}/{CHANNEL}"])
        f.append(("BLOCK", f"local {CHANNEL} differs from {REMOTE}/{CHANNEL} "
                           f"({ahead} ahead / {behind} behind) — the release commit is the "
                           "REMOTE one; push or fast-forward before releasing"))
    # stranded work: a branch carrying commits not reachable from the release commit
    stranded = []
    for b in out(["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/"]).splitlines():
        if b in (CHANNEL, "main") or b.startswith(("backup/", "deliver/", "probe/")):
            continue
        mark = out(["git", "rev-parse", "--verify", "--quiet", f"refs/delivered/{b}"])
        tip = out(["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{b}"])
        if mark and mark == tip:
            continue
        n = len([l for l in out(["git", "cherry", f"refs/heads/{CHANNEL}", b]).splitlines()
                 if l.startswith("+")])
        if n:
            stranded.append((b, n))
    for b, n in stranded:
        f.append(("WARN", f"branch {b} holds {n} commit(s) not on {CHANNEL} — "
                          "no target can see that work"))
    return remote or local, f


# ---------------------------------------------------------- target registry
def load_registry():
    if not REGISTRY.is_file():
        raise SystemExit(f"no target registry at {REGISTRY} — the path-only list is not "
                         "sufficient to validate target identity")
    reg = json.loads(REGISTRY.read_text())
    if reg.get("version") != 1:
        raise SystemExit(f"unsupported registry version {reg.get('version')!r}")
    return reg


def validate_target(t, seen_real):
    """Return (findings, resolved_root|None). A BLOCK finding means: do not sync it."""
    f = []
    root = Path(t["path"])
    if not root.exists():
        return [("BLOCK", "path does not exist")], None
    if not root.is_dir():
        return [("BLOCK", "path is not a directory")], None
    real = root.resolve()
    if real == FORK:
        return [("BLOCK", "target IS the fork — a distributor must never sync onto itself")], None
    if FORK in real.parents:
        return [("BLOCK", "target is nested inside the fork")], None
    prev = seen_real.get(str(real))
    if prev:
        return [("BLOCK", f"resolves to the same real path as target {prev!r} — an alias, "
                          "so one of them would silently overwrite the other")], None
    seen_real[str(real)] = t["id"]

    managed = real / t.get("managed_root", "_bmad")
    if managed.is_symlink():
        f.append(("BLOCK", f"{t.get('managed_root','_bmad')} is a symlink — a destructive "
                           "sync must not follow one out of the target"))
    elif managed.exists():
        mreal = managed.resolve()
        if real != mreal and real not in mreal.parents:
            f.append(("BLOCK", "managed root resolves outside the target"))
    else:
        f.append(("WARN", "managed root does not exist yet (first release?)"))

    exp = t.get("expected_repo_remote")
    if exp:
        actual = out(["git", "remote", "get-url", "origin"], cwd=real)
        if not actual:
            f.append(("WARN", "target is not a git repo, or has no origin — identity unverified"))
        elif actual.rstrip("/").removesuffix(".git") != exp.rstrip("/").removesuffix(".git"):
            f.append(("BLOCK", f"repo identity mismatch: expected {exp}, found {actual}"))
    return f, real


# ------------------------------------------------------------------ receipts
def read_receipt(real, t):
    p = real / t.get("managed_root", "_bmad") / RECEIPT
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return {"_corrupt": True}


def managed_tree_hash(real, t):
    """Stable hash of the managed tree, so a receipt can be checked against reality."""
    managed = real / t.get("managed_root", "_bmad")
    if not managed.is_dir():
        return None
    h = hashlib.sha256()
    for p in sorted(managed.rglob("*")):
        if p.is_file() and p.name != RECEIPT and ".git" not in p.parts:
            h.update(str(p.relative_to(managed)).encode())
            h.update(p.read_bytes() if p.stat().st_size < 2_000_000 else b"<large>")
    return h.hexdigest()[:16]


def write_receipt(real, t, release_sha, release_tree):
    managed = real / t.get("managed_root", "_bmad")
    managed.mkdir(parents=True, exist_ok=True)
    body = {
        "schema_version": 1,
        "managed_by": "bmad-method-v6",
        "note": "GENERATED — do not edit. This tree is a distributed replica, not a source.",
        "channel": CHANNEL,
        "release_commit": release_sha,
        "release_tree": release_tree,
        "source_remote": REMOTE,
        "synced_at_utc": now(),
        "target_id": t["id"],
        "manifest_version": 1,
        "sync_tool_version": TOOL_VERSION,
    }
    (managed / RECEIPT).write_text(json.dumps(body, indent=2) + "\n")
    return body


# ------------------------------------------------------------- classification
def classify(t, release_sha):
    """-> (state, detail). Read-only."""
    seen = {}
    findings, real = validate_target(t, seen)
    blocks = [m for lvl, m in findings if lvl == "BLOCK"]
    if real is None:
        m = blocks[0] if blocks else "unknown"
        if "does not exist" in m:
            return "MISSING", m
        if "alias" in m or "identity mismatch" in m:
            return "MISREGISTERED", m
        return "UNSAFE_PATH", m
    if blocks:
        bad = blocks[0]
        return ("MISREGISTERED" if "identity" in bad else "UNSAFE_PATH"), bad

    if not (real / ".git").exists():
        return "UNREACHABLE", "target is not a git repository"

    # Drift is checked FIRST and outranks a missing receipt. Both are true of an
    # untracked replica, but only one of them means a publish would DELETE work, and
    # that is the one an operator has to see.
    dirty = out(["git", "status", "--porcelain", "--", t.get("managed_root", "_bmad")], cwd=real)
    if dirty:
        n = len(dirty.splitlines())
        return "LOCAL_DRIFT", (f"{n} uncommitted change(s) under the managed root — a sync "
                               "would DELETE them; inspect before releasing")

    receipt = read_receipt(real, t)
    if receipt is None:
        return "PARTIAL_RELEASE", "no receipt — this replica predates release tracking"
    if receipt.get("_corrupt"):
        return "PARTIAL_RELEASE", "receipt is unreadable"
    if receipt.get("release_commit") != release_sha:
        return "STALE", (f"holds {str(receipt.get('release_commit'))[:12]}, "
                         f"release is {release_sha[:12]}")
    return "CURRENT", f"at {release_sha[:12]}"


# ------------------------------------------------------------------- commands
def cmd_check(args):
    print(f"BMAD RELEASE CHECK — {now()}\n")
    release_sha, findings = source_gate(fetch=not args.no_fetch)
    print(f"canonical channel : {REMOTE}/{CHANNEL}")
    print(f"release commit    : {release_sha[:12] if release_sha else '(unresolved)'}"
          f"  {out(['git','log','-1','--format=%s',release_sha])[:60] if release_sha else ''}\n")

    blocks = [m for lvl, m in findings if lvl == "BLOCK"]
    warns = [m for lvl, m in findings if lvl == "WARN"]
    if blocks:
        print("SOURCE — BLOCKING:")
        for m in blocks:
            print(f"  x {m}")
    if warns:
        print("SOURCE — warnings:")
        for m in warns:
            print(f"  ! {m}")
    if not blocks and not warns:
        print("SOURCE — clean.")
    print()

    reg = load_registry()
    seen, rows, target_blocks = {}, [], 0
    for t in reg["targets"]:
        if not t.get("enabled", True):
            rows.append((t["id"], "DISABLED", t.get("decommission_reason", "")))
            continue
        f, real = validate_target(t, seen)
        tb = [m for lvl, m in f if lvl == "BLOCK"]
        target_blocks += len(tb)
        state, detail = (("BLOCKED", tb[0]) if tb else classify(t, release_sha or ""))
        rows.append((t["id"], state, detail))

    print("TARGETS:")
    width = max(len(r[0]) for r in rows) + 2
    for tid, state, detail in rows:
        print(f"  {tid:<{width}}{state:<16}{detail[:82]}")
    for t in reg["targets"]:
        if t.get("owner") == "owner-gate":
            print(f"\n  OWNER GATE — {t['id']}: {t.get('review','')}")

    legacy = set()
    if LEGACY_TARGETS.is_file():
        legacy = {l.strip().replace("/_bmad/bmm/workflows", "")
                  for l in LEGACY_TARGETS.read_text().splitlines()
                  if l.strip() and not l.startswith("#")}
    reg_paths = {t["path"] for t in reg["targets"]}
    for extra in sorted(legacy - reg_paths):
        print(f"\n  ! {LEGACY_TARGETS} lists {extra} which the registry does not — "
              "the old distributor would still write to it")

    ok = not blocks and target_blocks == 0
    print(f"\n{'PASS' if ok else 'FAIL'} — {len(blocks)} source block(s), "
          f"{target_blocks} target block(s). check writes nothing.")
    return 0 if ok else 1


def cmd_reconcile(args):
    print(f"BMAD RECONCILE — {now()}  (read-only)\n")
    release_sha, _ = source_gate(fetch=not args.no_fetch)
    reg = load_registry()
    buckets = {s: [] for s in STATES}
    buckets["DISABLED"] = []
    for t in reg["targets"]:
        if not t.get("enabled", True):
            buckets["DISABLED"].append((t["id"], t.get("decommission_reason", "")))
            continue
        state, detail = classify(t, release_sha or "")
        buckets.setdefault(state, []).append((t["id"], detail))
    for state in list(STATES) + ["DISABLED"]:
        rows = buckets.get(state) or []
        if not rows:
            continue
        print(f"{state} ({len(rows)})")
        for tid, detail in rows:
            print(f"    {tid:<28}{detail[:88]}")
        remedy = {
            "STALE": "bmad-release.py publish --target <id>",
            "LOCAL_DRIFT": "inspect the drift, commit or discard it, then publish --target <id>",
            "PARTIAL_RELEASE": "bmad-release.py publish --target <id>   (writes the first receipt)",
            "MISSING": "fix or disable the entry in ~/.bmad-targets.json",
            "MISREGISTERED": "correct id/path/expected_repo_remote in the registry",
            "UNSAFE_PATH": "do not sync; resolve the path or containment problem first",
            "UNREACHABLE": "restore the checkout, or disable the entry",
        }.get(state)
        if remedy:
            print(f"    -> {remedy}")
        print()
    print("reconcile changed nothing. LOCAL_DRIFT is never repaired silently — a sync "
          "would delete those edits.")
    return 0


def cmd_publish(args):
    print(f"BMAD RELEASE PUBLISH — {now()}\n")
    release_sha, findings = source_gate(fetch=not args.no_fetch)
    blocks = [m for lvl, m in findings if lvl == "BLOCK"]
    if blocks:
        print("REFUSED — the source is not a canonical release:")
        for m in blocks:
            print(f"  x {m}")
        return 1
    release_tree = out(["git", "rev-parse", f"{release_sha}^{{tree}}"])
    print(f"release commit {release_sha[:12]}  tree {release_tree[:12]}")

    reg = load_registry()
    chosen = [t for t in reg["targets"] if t.get("enabled", True)
              and (not args.target or t["id"] == args.target)]
    if args.target and not chosen:
        print(f"no enabled target with id {args.target!r}")
        return 1

    # Immutable release worktree — an edit to the developer checkout mid-release
    # cannot reach a target.
    tmp = Path(tempfile.mkdtemp(prefix="bmad-release-"))
    wt = tmp / "release"
    print(f"materialising an immutable release worktree at {release_sha[:12]}")
    if sh(["git", "worktree", "add", "--detach", str(wt), release_sha]).returncode != 0:
        print("REFUSED — could not create the release worktree")
        shutil.rmtree(tmp, ignore_errors=True)
        return 1

    results, exceptions = [], []
    try:
        # A fresh worktree has no node_modules, so the suite cannot run there at all
        # (it dies on `Cannot find module 'yaml'` before the first case). Link the fork's
        # tree in rather than installing: local custom is verified identical to the remote
        # release commit above, so the fork's dependencies ARE the release commit's.
        # HONEST LIMIT: this cannot catch a dependency change that was never installed
        # locally. A release from a machine whose node_modules predates a package.json
        # change would test against the older deps. `npm ci` here would be correct and
        # costs minutes per release; revisit if a dependency change ever ships broken.
        fork_modules = FORK / "node_modules"
        if fork_modules.is_dir() and not (wt / "node_modules").exists():
            (wt / "node_modules").symlink_to(fork_modules)

        if not args.no_test:
            print("running the release suite against that exact commit...")
            r = subprocess.run(["npm", "test"], cwd=wt, capture_output=True, text=True)
            if r.returncode != 0:
                print("REFUSED — the release suite failed on the release commit:")
                print("\n".join(r.stdout.strip().splitlines()[-12:]))
                return 1
            print("  suite green\n")

        syncer = wt / "sync-bmad-workflows.sh"
        for t in chosen:
            seen = {}
            f, real = validate_target(t, seen)
            if [m for lvl, m in f if lvl == "BLOCK"] or real is None:
                why = next((m for lvl, m in f if lvl == "BLOCK"), "unresolved path")
                exceptions.append((t["id"], f"preflight: {why}"))
                print(f"  SKIP {t['id']} — {why}")
                continue
            state, detail = classify(t, release_sha)
            if state == "LOCAL_DRIFT" and not args.force_drift:
                exceptions.append((t["id"], f"LOCAL_DRIFT: {detail}"))
                print(f"  SKIP {t['id']} — {detail}")
                continue

            print(f"  publishing {t['id']}")
            # --allow-unclean-source is CORRECT here and only here: the release worktree is
            # a detached checkout of the verified release commit, so the syncer's own
            # "must be on custom" gate would refuse the one source that is canonical by
            # construction. Every condition that gate protects has already been checked
            # above, against the real fork, before this worktree existed.
            r = subprocess.run([str(syncer), "--only", str(real), "--allow-unclean-source"],
                               cwd=wt, capture_output=True, text=True)
            if r.returncode != 0:
                exceptions.append((t["id"], "sync failed"))
                print(f"    FAILED: {r.stdout.strip().splitlines()[-3:]}")
                continue
            receipt = write_receipt(real, t, release_sha, release_tree)

            # COMMIT THE REPLICA. Without this the release is not finished: the managed
            # root is git-tracked, so a synced-but-uncommitted replica reads as
            # LOCAL_DRIFT the instant the publish ends — the tool would manufacture the
            # exact condition it exists to detect, and the next release would refuse the
            # target it had just written. A replica is distributed state, so committing it
            # is part of distributing it, not a separate decision.
            mroot = t.get("managed_root", "_bmad")
            sh(["git", "add", "--", mroot], cwd=real)
            staged = out(["git", "diff", "--cached", "--name-only", "--", mroot], cwd=real)
            if staged:
                msg = (f"chore(bmad): distribute release {release_sha[:12]}\n\n"
                       f"Generated replica, synced from {REMOTE}/{CHANNEL}@{release_sha[:12]}.\n"
                       f"Receipt: {mroot}/{RECEIPT}. Do not edit this tree by hand — it is\n"
                       f"overwritten by the next release.\n")
                c = sh(["git", "commit", "--no-verify", "-m", msg, "--", mroot], cwd=real)
                if c.returncode != 0:
                    exceptions.append((t["id"], "replica synced but could not be committed"))
                    print("    FAILED to commit the replica")
                    continue
                print(f"    committed {len(staged.splitlines())} replica file(s)")

            digest = managed_tree_hash(real, t)
            back = read_receipt(real, t)
            if not back or back.get("release_commit") != release_sha:
                exceptions.append((t["id"], "post-sync verification failed: receipt mismatch"))
                print("    FAILED post-sync verification")
                continue
            results.append((t["id"], digest))
            print(f"    ok — receipt {release_sha[:12]}, tree {digest}")
    finally:
        sh(["git", "worktree", "remove", "--force", str(wt)])
        shutil.rmtree(tmp, ignore_errors=True)

    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a") as fh:
        fh.write(json.dumps({
            "at": now(), "release_commit": release_sha, "release_tree": release_tree,
            "channel": CHANNEL, "tool_version": TOOL_VERSION,
            "delivered": [t for t, _ in results],
            "exceptions": [{"target": t, "reason": r} for t, r in exceptions],
        }) + "\n")

    print(f"\ndelivered {len(results)}, exceptions {len(exceptions)}")
    for t, r in exceptions:
        print(f"  EXCEPTION {t}: {r}")
    print(f"ledger: {LEDGER}")
    return 0 if not exceptions else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("check", cmd_check), ("publish", cmd_publish), ("reconcile", cmd_reconcile)):
        p = sub.add_parser(name)
        p.add_argument("--no-fetch", action="store_true", help="skip the remote fetch (offline)")
        p.set_defaults(fn=fn)
        if name == "publish":
            p.add_argument("--target", help="publish one registry id only")
            p.add_argument("--no-test", action="store_true", help="skip the release suite")
            p.add_argument("--force-drift", action="store_true",
                           help="publish over LOCAL_DRIFT, DELETING those edits")
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
