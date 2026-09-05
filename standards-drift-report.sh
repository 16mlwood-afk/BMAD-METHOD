#!/usr/bin/env bash
# Cross-project standards drift report — the LOCAL sweep the cloud quarterly
# review can't do (it can't see project checkouts). Compares each BMAD project's
# synced STANDARDS.md against the fork canonical and prints the governance metric:
# "N / M projects in drift", plus which standards drift where.
#
# Run as the local half of the quarterly Standards Governance Review (and any
# time you want the number). Read-only — never edits a project.
#
#   ~/bmad-method-v6/standards-drift-report.sh
#
CANON="$HOME/bmad-method-v6/custom/workflows/shared/STANDARDS.md"
TARGETS="$HOME/.bmad-targets"
[ -f "$CANON" ] || { echo "canon not found: $CANON" >&2; exit 1; }
[ -f "$TARGETS" ] || { echo "targets not found: $TARGETS" >&2; exit 1; }

# Build the list of project roots (strip the trailing /_bmad/bmm/workflows).
roots=()
while IFS= read -r line; do
  case "$line" in ''|\#*) continue;; esac
  roots+=("${line%/_bmad/bmm/workflows}")
done < "$TARGETS"

CANON="$CANON" python3 - "${roots[@]}" <<'PY'
import os, re, sys

def parse(path):
    out = {}
    try:
        text = open(path, encoding="utf-8").read()
    except Exception:
        return out
    cur = None
    for line in text.splitlines():
        a = re.match(r"^ID:\s*(\S+)", line)
        if a:
            cur = a.group(1); out[cur] = {"version": None, "breaking": False}; continue
        if not cur:
            continue
        v = re.match(r"^Version:\s*(\S+)", line)
        if v:
            out[cur]["version"] = v.group(1); continue
        b = re.match(r"^Breaking:\s*(\S+)", line)
        if b:
            out[cur]["breaking"] = b.group(1).strip().lower() in ("yes", "true"); cur = None
    return out

canon = parse(os.environ["CANON"])
canon_v = {k: v["version"] for k, v in canon.items()}
roots = sys.argv[1:]

in_drift = 0
total = 0
lines = []
for root in roots:
    name = os.path.basename(root)
    # command-layout path first, then skills-layout
    proj_file = None
    for rel in ("_bmad/bmm/workflows/shared/STANDARDS.md", "_bmad/bmad-shared/STANDARDS.md"):
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            proj_file = p; break
    total += 1
    if not proj_file:
        in_drift += 1
        lines.append(f"  DRIFT  {name:<26} STANDARDS.md not synced")
        continue
    proj = {k: v["version"] for k, v in parse(proj_file).items()}
    issues = []
    for sid, cv in sorted(canon_v.items()):
        pv = proj.get(sid)
        if pv is None:
            issues.append(f"{sid} missing")
        elif pv != cv:
            tag = "BREAKING " if canon[sid]["breaking"] else ""
            issues.append(f"{sid} {tag}{pv}->{cv}")
    if issues:
        in_drift += 1
        lines.append(f"  DRIFT  {name:<26} " + "; ".join(issues))
    else:
        lines.append(f"  ok     {name:<26} in sync")

print("Standards Drift Report")
print(f"Drift count: {in_drift} / {total} projects in drift")
print("")
print("\n".join(lines))
PY
