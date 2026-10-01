#!/usr/bin/env python3
"""Fleet delivery lane lock — an ADVISORY lease, not an access-control boundary.

WHY A LEASE AND NOT A DENY. Two sessions repaired the same fourteen projects concurrently
on 2026-08-31 and overwrote each other; the damage was real and neither could see the
other coming. The first version of this file answered that with default-deny keyed on a
shared secret. The delivery-owner session declined it, and was right on three counts worth
recording because the reasoning generalises:

  - it could not accept a credential arriving in a peer message, which is exactly the
    escalation path a session is required to refuse;
  - the secret existed only in a chat message and one scratchpad, so it was already burned;
  - and, decisively, a default-deny lock over fourteen repos keyed on an ephemeral secret
    means that when these sessions end NOBODY can run maintenance, silently and totally.
    "Absence of a lock denies" is right for a security boundary and wrong for a maintenance
    boundary: the thing being prevented is two writers, and the cost of overshooting is a
    fleet nobody can service.

So this stops the failure that actually happened and nothing more. A session takes the
lane by writing a lease naming itself and an expiry; another session's LIVE lease refuses a
write; a stale lease is free rather than fatal; no lock at all means no contention, so
proceed. A human can read the file and see who holds it.

A hard access-control boundary over the owner's repositories is a real decision about his
property and is his to make, not two agents' to arrange between themselves. It is not
implemented here.
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
    """-> the lock, or None. A missing or unreadable lock is NOT a denial: it means no
    contention has been declared, and a maintenance lane that seizes up when its metadata
    is absent is worse than the collision it prevents."""
    if not LOCK.is_file():
        return None
    try:
        return json.loads(LOCK.read_text())
    except json.JSONDecodeError:
        return None


def holder():
    """-> (who, expires) of the LIVE lease, or (None, None). Expiry makes it self-healing."""
    if not LEASE.is_file():
        return None, None
    try:
        cur = json.loads(LEASE.read_text())
    except json.JSONDecodeError:
        return None, None
    exp = _parse(cur.get("expires"))
    if exp and exp < _now():
        return None, None
    return cur.get("who"), cur.get("expires")


def me():
    return (os.environ.get("BMAD_FLEET_SESSION")
            or os.environ.get("CLAUDE_CODE_SESSION_ID")
            or f"pid-{os.getpid()}")


def assert_may_mutate(target_id, operation="mutate"):
    """Raise Denied only when ANOTHER session holds a live lease. Call BEFORE the write."""
    who, exp = holder()
    if who is None or who == me():
        return
    lock = load() or {}
    owner = lock.get("fleet_owner", {}).get("identity", who)
    raise Denied(
        f"Fleet delivery is owned by {owner}. This session may inspect and prepare "
        f"remediation, but may not mutate active project installations.\n"
        f"    target   : {target_id}\n"
        f"    operation: {operation}\n"
        f"    lease    : held by {who}, expires {exp}\n"
        f"    The lease is advisory and self-expiring. If that run is known dead, clear "
        f"{LEASE}.")


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
    lock = load() or {}
    live = [h for h in lock.get("handoffs", [])
            if not (_parse(h.get("expires")) and _parse(h["expires"]) < _now())]
    return (f"workstream    : {lock.get('workstream')}\n"
            f"fleet owner   : {lock.get('fleet_owner', {}).get('identity')}\n"
            f"source-side   : {lock.get('source_side_owner', {}).get('identity')}\n"
            f"lease holder  : {holder()[0] or '(free)'}\n"
            f"this session  : {me()}\n"
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
