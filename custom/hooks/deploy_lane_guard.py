#!/usr/bin/env python3
"""
Deploy-lane guard (STD-DEPLOY-002 R10) — a bare provider SHIP command must not
ship a BMAD-managed app from a Claude shell. The lane script must.

## Why this exists

A provider CLI's ship command uploads a DIRECTORY, not a commit. The provider
never learns which SHA it is running; only the project's deploy lane
(`scripts/deploy.sh` by default) can stamp that, pin the tree, assert the
upload root, read the running commit back and compare the source fingerprint —
the ten things `shared/deploy-lane-standard.md` requires.

Observed, all reporting SUCCESS: two deploys of a parked shared checkout
(2026-07-27), a deploy that moved no stamp (2026-07-28), and an upload of the
wrong directory under the right stamp (2026-09-04, cash-recovery).

## What this does NOT claim to fix

It stops the TOOL CALL. It cannot stop a skill, workflow or doc from teaching
the raw command; that is prose and stays the responsibility of the standard's
consumers. And it sees only Claude's shell — a terminal outside the harness is
outside this guard.

## Enforcement tier, honestly

WARN by default (`additionalContext`). A project promotes it to a hard deny by
declaring `deploy.guard_mode: deny` in `_bmad/bmm/config.yaml`, or per-shell with
`DEPLOY_LANE_MODE=deny`. Every decision carries `deny_eligible`, so promotion is a
config line, never a code change — the DECISION carries the weight.

DETECTION is a heuristic over shell text, by construction. When a target is
unresolvable it stays SILENT rather than guessing: a missed flag is recoverable
next session, a wrong flag erodes trust irreversibly. Quoted spans and heredoc
bodies are DATA and never fire (a commit message naming the command it polices
must not block the commit).

## Override

`DEPLOY_UNSTAMPED=1`, exact-match, logged to
`~/.claude/logs/deploy-lane-override.jsonl` (metadata only — never the command
string, which can carry credentials). Every FIRING is logged to
`~/.claude/logs/deploy-lane-firings.jsonl` so the warn→deny promotion has an
instrument.

Golden suite: `python3 .claude/hooks/test_deploy_lane_guard.py`.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

OVERRIDE_ENV = "DEPLOY_UNSTAMPED"
MODE_ENV = "DEPLOY_LANE_MODE"
OVERRIDE_LOG = Path.home() / ".claude" / "logs" / "deploy-lane-override.jsonl"
FIRE_LOG = Path.home() / ".claude" / "logs" / "deploy-lane-firings.jsonl"

# The sanctioned lane, by its path suffix. A project may name another lane in
# `deploy.lane`; that path is read from config at fire time.
DEFAULT_LANE = "scripts/deploy.sh"

# Provider CLIs and the subcommand shapes that SHIP. Everything else a CLI offers —
# status, logs, variables, link, whoami, inspect — is read-only or metadata and is
# none of this guard's business. A provider absent from this table is not policed
# (conservative detector: silence over guessing).
#
#   ship  — tokens that, appearing in the invocation's own argv, mean "deploy"
#   wrap  — subcommands that WRAP an arbitrary command: everything after them is
#           that command's argv (`railway run make up` must not fire)
#   ship_seq — multi-token ship shapes (`gcloud run deploy`, `wrangler pages deploy`)
PROVIDERS = {
    "railway":    {"ship": {"up", "redeploy"}, "wrap": {"run", "exec", "shell", "ssh", "connect"}},
    "vercel":     {"ship": {"deploy", "--prod", "--production"}, "wrap": {"env", "dev"}},
    "wrangler":   {"ship": {"deploy", "publish"}, "ship_seq": {("pages", "deploy"), ("versions", "deploy")}},
    "fly":        {"ship": {"deploy"}, "wrap": {"ssh", "console", "proxy"}},
    "flyctl":     {"ship": {"deploy"}, "wrap": {"ssh", "console", "proxy"}},
    "netlify":    {"ship": {"deploy"}, "wrap": {"dev", "functions:invoke"}},
    "gcloud":     {"ship_seq": {("run", "deploy"), ("app", "deploy"), ("functions", "deploy")}},
    "firebase":   {"ship": {"deploy"}},
    "heroku":     {"ship": {"container:release", "container:push"}},
    "eb":         {"ship": {"deploy"}},
    "sst":        {"ship": {"deploy"}},
    "serverless": {"ship": {"deploy"}},
    "sls":        {"ship": {"deploy"}},
    "cdk":        {"ship": {"deploy"}},
    "aws":        {"ship_seq": {("cloudformation", "deploy"), ("amplify", "start-deployment"),
                               ("lambda", "update-function-code")}},
}
# `git push <heroku-remote> …` is the classic Heroku ship; matched separately.
GIT_PUSH_SHIP = re.compile(r"\bgit\s+push\b[^|;&\n]*\b(heroku|dokku)\b")


def quoted_spans(cmd: str) -> list:
    """(start, end) ranges of single/double-quoted regions — DATA, not commands."""
    spans, i, n = [], 0, len(cmd)
    while i < n:
        ch = cmd[i]
        if ch in ("'", '"'):
            j = i + 1
            while j < n and cmd[j] != ch:
                if ch == '"' and cmd[j] == "\\":
                    j += 1
                j += 1
            spans.append((i, min(j, n - 1)))
            i = j + 1
        else:
            i += 1
    return spans


def in_quotes(pos: int, spans: list) -> bool:
    return any(start <= pos <= end for start, end in spans)


def _strip_heredocs(cmd: str) -> str:
    """Blank heredoc BODIES whose terminator is present; keep the introducing command.
    An unterminated heredoc is left alone — over-stripping would blind the guard."""
    for m in re.finditer(r"<<-?\s*[\"\']?([A-Za-z_][A-Za-z0-9_]*)[\"\']?", cmd):
        delim = m.group(1)
        end = re.search(rf"^\s*{re.escape(delim)}\s*$", cmd[m.end():], re.MULTILINE)
        if not end:
            continue
        body_start, body_end = m.end(), m.end() + end.end()
        cmd = cmd[:body_start] + (" " * (body_end - body_start)) + cmd[body_end:]
    return cmd


def _segments(cmd: str) -> list:
    """Split on command separators so `railway logs | grep up` cannot read grep's
    `up` as railway's subcommand. Returns (offset, text) pairs."""
    out, pos = [], 0
    for part in re.split(r"(\|\||&&|[|;\n])", cmd):
        if part and not re.fullmatch(r"\|\||&&|[|;\n]", part):
            out.append((pos, part))
        pos += len(part)
    return out


def find_bare_ship(cmd: str, lane: str = DEFAULT_LANE) -> str | None:
    """Return 'provider subcommand' for an UNQUOTED bare ship command outside the
    lane, or None. The lane's own token is removed first so `./scripts/deploy.sh`
    is silent while `./scripts/deploy.sh && railway up` still fires."""
    cmd = _strip_heredocs(cmd)
    lane_re = re.escape(lane.split("/")[-1])
    cmd = re.sub(rf"\S*{lane_re}\S*", " ", cmd)
    spans = quoted_spans(cmd)

    m = GIT_PUSH_SHIP.search(cmd)
    if m and not in_quotes(m.start(), spans):
        return f"git push {m.group(1)}"

    for offset, seg in _segments(cmd):
        tokens = seg.split()
        for i, tok in enumerate(tokens):
            name = tok.rsplit("/", 1)[-1]
            if name not in PROVIDERS:
                continue
            abs_pos = offset + seg.find(tok)
            if in_quotes(abs_pos, spans):
                continue
            spec = PROVIDERS[name]
            rest = tokens[i + 1:]
            for j, t in enumerate(rest):
                if t in spec.get("wrap", set()):
                    break
                if t in spec.get("ship", set()):
                    return f"{name} {t}"
                if j + 1 < len(rest) and (t, rest[j + 1]) in spec.get("ship_seq", set()):
                    return f"{name} {t} {rest[j + 1]}"
            break  # one provider invocation per segment is enough to judge it
    return None


def _config_value(key: str) -> str:
    """`deploy.<key>` from the nearest _bmad/bmm/config.yaml above cwd, else ''."""
    d = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
    for base in (d, *d.parents):
        cfg = base / "_bmad" / "bmm" / "config.yaml"
        if cfg.is_file():
            inside = False
            for raw in cfg.read_text(errors="ignore").splitlines():
                if re.match(r"^deploy:\s*(#.*)?$", raw):
                    inside = True
                    continue
                if inside:
                    if raw.strip() and not raw.startswith((" ", "\t")):
                        break
                    m = re.match(rf"^\s+{key}:\s*(.*?)\s*$", raw)
                    if m:
                        return m.group(1).split("#", 1)[0].strip().strip("'\"")
            return ""
    return ""


def mode() -> str:
    env = os.environ.get(MODE_ENV, "").strip().lower()
    if env in {"deny", "warn"}:
        return env
    return "deny" if _config_value("guard_mode").lower() == "deny" else "warn"


def _append(path: Path, row: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
    except OSError:
        pass  # the log is an audit aid, never the gate


def _row(what: str, kind: str) -> dict:
    return {"at": datetime.now(timezone.utc).isoformat(), "guard": "deploy_lane_guard",
            "kind": kind, "subcommand": what, "cwd": os.getcwd()}


def reason(what: str, lane: str, decision: str) -> str:
    return (
        f"DEPLOY LANE — `{what}` was invoked directly.\n\n"
        "A provider ship command uploads a DIRECTORY, not a commit: the provider never "
        "learns which SHA it is running, nothing pins the tree, nothing asserts which "
        "directory is uploaded, and nothing compares the running source to it afterwards. "
        f"That is STD-DEPLOY-002's whole list, and only the lane does it:\n"
        f"    ./{lane}\n\n"
        f"Deliberate exception: {OVERRIDE_ENV}=1 (logged). "
        + ("This project has promoted the guard to DENY (deploy.guard_mode)."
           if decision == "deny" else
           "Warn-only here; a project promotes it with deploy.guard_mode: deny.")
    )


def emit(what: str, lane: str) -> None:
    decision = mode()
    _append(FIRE_LOG, {**_row(what, "firing"), "decision": decision})
    payload = {"hookEventName": "PreToolUse", "deny_eligible": True}
    if decision == "deny":
        payload["permissionDecision"] = "deny"
        payload["permissionDecisionReason"] = reason(what, lane, decision)
    else:
        payload["additionalContext"] = reason(what, lane, decision)
    print(json.dumps({"hookSpecificOutput": payload}))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # garbage in: stay silent, never fire on noise
    cmd = (payload.get("tool_input") or {}).get("command") or ""
    if not cmd or not any(p in cmd for p in PROVIDERS) and "git push" not in cmd:
        return 0
    lane = _config_value("lane") or DEFAULT_LANE
    what = find_bare_ship(cmd, lane)
    if not what:
        return 0
    if os.environ.get(OVERRIDE_ENV) == "1":
        _append(OVERRIDE_LOG, _row(what, "override"))
        return 0
    emit(what, lane)
    return 0


if __name__ == "__main__":
    sys.exit(main())
