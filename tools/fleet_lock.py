#!/usr/bin/env python3
"""Fleet delivery lane lock — one mutator at a time, enforced before any project write.

WHY. On 2026-08-31 two sessions repaired the same fourteen projects concurrently and
overwrote each other. The damage was real (246 deletions recorded, 17 of them wrong) and
neither session could see the other coming. The owner then assigned a single delivery
owner. A prose rule would not have stopped either of us: both were following instructions
that were correct when issued and stale by the time they ran. So the boundary is a check
that runs BEFORE a write, and fails closed.

DEFAULT DENY. Any session may inspect. No session may mutate an active target unless it
presents the owner token whose hash is recorded in the lock. Absence of a lock does NOT
mean open season — a missing or unreadable lock denies too, because the failure mode of a
lock that vanishes must be "nobody writes", never "everybody writes".

TARGET-SPECIFIC HANDOFF. The owner grants one target back by adding an entry to
`handoffs`, naming the target, the operation, and an expiry. A handoff is scoped: it does
not confer general ownership, and it lapses on its own.

Read `~/.bmad-fleet-lock.json`. The token itself is never stored — only its hash.
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOCK = Path.home() / ".bmad-fleet-lock.json"
LEASE = Path.home() / ".bmad-fleet-lock.lease"
LEASE_TTL_S = 3600
TOKEN_ENV = "BMAD_FLEET_OWNER_TOKEN"


class Denied(Exception):
    pass


def _now():
    return datetime.now(timezone.utc)


def _parse(ts):
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None


def load():
    if not LOCK.is_file():
        raise Denied(
            f"no fleet lock at {LOCK}. Fleet mutation is DENIED by default: a missing "
            "lock must mean nobody writes, never everybody writes. Create the lock, or "
            "run a read-only command.")
    try:
        return json.loads(LOCK.read_text())
    except json.JSONDecodeError as e:
        raise Denied(f"fleet lock at {LOCK} is unreadable ({e}) — denying, fail closed.")


def is_owner(lock=None):
    lock = lock or load()
    tok = os.environ.get(TOKEN_ENV, "")
    if not tok:
        return False
    return hashlib.sha256(tok.encode()).hexdigest() == lock.get("owner_token_sha256")


def assert_may_mutate(target_id, operation="mutate"):
    """Raise Denied unless this session may mutate this target. Call BEFORE the write."""
    lock = load()
    owner = lock.get("fleet_owner", {}).get("identity", "the delivery owner")

    if is_owner(lock):
        return

    for h in lock.get("handoffs", []):
        if h.get("target") not in (target_id, "*"):
            continue
        if h.get("operation") not in (operation, "*"):
            continue
        exp = _parse(h.get("expires"))
        if exp and exp < _now():
            continue
        if h.get("to") == lock.get("source_side_owner", {}).get("identity"):
            return

    raise Denied(
        f"Fleet delivery is owned by {owner}. This session may inspect and prepare "
        f"remediation, but may not mutate active project installations.\n"
        f"    target   : {target_id}\n"
        f"    operation: {operation}\n"
        f"    lock     : {LOCK}\n"
        f"    A target-specific handoff is made by the owner adding an entry to "
        f"`handoffs` naming target, operation, `to`, and `expires`.")


def begin_mutation(who, targets):
    """Take the single-mutator lease, or refuse. Ownership says WHO may write; the lease
    stops the owner racing ITSELF from two terminals — a second run against a tree the
    first is halfway through rewriting decides deletions against a moving target, which
    is the incident in miniature."""
    if LEASE.is_file():
        try:
            cur = json.loads(LEASE.read_text())
        except json.JSONDecodeError:
            cur = None
        if cur:
            exp = _parse(cur.get("expires"))
            if (not exp or exp > _now()) and cur.get("who") != who:
                raise Denied(
                    f"another mutation is in progress: {cur.get('who')} started "
                    f"{cur.get('started')} on {len(cur.get('targets', []))} target(s). "
                    f"Two simultaneous mutators is the failure this exists to stop. "
                    f"Wait, or clear {LEASE} if that run is known dead.")
    LEASE.write_text(json.dumps({
        "who": who, "targets": targets,
        "started": _now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires": _parse(_now().strftime("%Y-%m-%dT%H:%M:%SZ")).replace(
            microsecond=0).isoformat().replace("+00:00", "Z"),
        "pid": os.getpid(),
    }, indent=2) + "\n")


def end_mutation(who):
    if LEASE.is_file():
        try:
            if json.loads(LEASE.read_text()).get("who") == who:
                LEASE.unlink()
        except Exception:
            pass


def status():
    try:
        lock = load()
    except Denied as e:
        return f"DENIED — {e}"
    live = [h for h in lock.get("handoffs", [])
            if not (_parse(h.get("expires")) and _parse(h["expires"]) < _now())]
    return (f"workstream    : {lock.get('workstream')}\n"
            f"fleet owner   : {lock.get('fleet_owner', {}).get('identity')}\n"
            f"source-side   : {lock.get('source_side_owner', {}).get('identity')}\n"
            f"this session  : {'OWNER' if is_owner(lock) else 'source-side (read-only on targets)'}\n"
            f"effective     : {lock.get('effective')}\n"
            f"review        : {lock.get('review_condition')}\n"
            f"live handoffs : {len(live)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        try:
            assert_may_mutate(sys.argv[2] if len(sys.argv) > 2 else "<target>")
            print("ALLOWED")
        except Denied as e:
            print(e)
            sys.exit(1)
    else:
        print(status())
