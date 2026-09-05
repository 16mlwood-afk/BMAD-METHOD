#!/usr/bin/env bash
# PreToolUse(Edit|Write|Bash) — SPRINT-APPLY GATE (v2: risk classifier + autopilot).
#
# Freezes the tracker files a pending correct-course proposal named. TWO lanes:
#   • OWNER-GATE lane (default, proven v1): freeze until APPROVE: APPLY_SPRINT_PROPOSAL::<id>
#     clears it (sprint-apply-approve.sh). Blocking governed by ~/.claude/sprint-apply-gate.mode
#     (dry-run DEFAULT → logs WOULD-BLOCK, allows; enforce → denies).
#   • AUTOPILOT lane (opt-in): a proposal whose ENTIRE files_to_change set is DETERMINISTICALLY
#     classified low-risk — single repo, count ≤ AUTOPILOT_MAX_FILES, no governance/doctrine path,
#     and every path is a SPRINT-EXECUTION artifact: under <root>/_bmad-output/implementation-artifacts/
#     OR a file named epics.md. (planning-artifacts — PRD/architecture/specs — are owner-gate: they
#     define what the product IS, not routine backlog bookkeeping.) Such a proposal auto-applies WITHOUT a token
#     — but only after a deterministic pre-edit SNAPSHOT makes the (otherwise untracked, data-loss
#     class) tracker files recoverable. Governed by ~/.claude/sprint-apply-autopilot.mode:
#       off  (DEFAULT) → no classification; pure owner-gate (byte-identical to v1).
#       classify-log   → classify + LOG the routing decision (WOULD-AUTOPILOT / WOULD-OWNERGATE),
#                        but still route everything through owner-gate (NO behavior change — the soak).
#       on             → autopilot_safe: snapshot + ALLOW + log AUTO-APPLY; everything else: owner-gate.
#
#   WHO CLASSIFIES: the gate, deterministically, from files_to_change — never an LLM self-label.
#   FAIL-CLOSED: any classify/parse/snapshot failure, missing metadata, or a path matching no rule
#     → owner_gate_required. A false owner-gate costs one token; a false autopilot is unrecoverable.
#   PAIRING: the autopilot lane only truly protects when the owner-gate mode is `enforce` (else the
#     owner-gate fall-through is advisory). Intended hands-off end-state = gate.mode=enforce +
#     autopilot.mode=on. Ladder: enforce owner-gate → classify-log soak → autopilot on.
#   Kill-switch: <root>/_bmad/.sprint-apply-autopilot.disable forces owner-gate regardless of mode.
#   Override (deliberate + LOGGED): <root>/_bmad/.sprint-apply-override with a reason.
#
# Global track (install-global-assets.sh → ~/.claude). NOT wired into any project's settings.
AUTOPILOT_MAX_FILES=6      # tunable ceiling: max files_to_change for the autopilot lane

in=$(cat)
root="${CLAUDE_PROJECT_DIR:-$PWD}"
pending="$root/_bmad/.sprint-apply-pending.json"
[ -f "$pending" ] || exit 0                      # nothing pending → allow everything

# Extract the target path from Edit/Write file_path, or from a Bash edit-equivalent. [v1, unchanged]
target=$(CC_IN="$in" CC_ROOT="$root" python3 <<'PY' 2>/dev/null
import os, json, re
root = os.environ["CC_ROOT"]
d = json.loads(os.environ.get("CC_IN", "{}")); ti = d.get("tool_input", {})
p = ti.get("file_path") or ""
if not p:
    cmd = ti.get("command", "")
    if re.search(r'\bsed\s+-i', cmd):
        toks = cmd.split()
        p = toks[-1] if toks else ""
    else:
        m = re.search(r'(?:>>?|tee|cat >)\s+([^\s;&|]+)', cmd)
        p = m.group(1) if m else ""
print(os.path.abspath(os.path.join(root, p)) if p and not p.startswith("/") else p)
PY
)
[ -n "$target" ] || exit 0

# Is the target in this proposal's frozen file set? [v1, unchanged]
frozen=$(CC_PEND="$pending" CC_ROOT="$root" CC_TARGET="$target" python3 <<'PY' 2>/dev/null
import os, json
pend, root, target = os.environ["CC_PEND"], os.environ["CC_ROOT"], os.environ["CC_TARGET"]
j = json.load(open(pend))
for f in j.get("files_to_change", []):
    if os.path.abspath(os.path.join(root, f)) == target:
        print(j.get("proposal_id", "?")); break
PY
)
[ -n "$frozen" ] || exit 0                        # target not frozen → allow

# Approved already (token cleared it this session)? [v1, unchanged]
appr="$root/_bmad/.sprint-apply-approved.json"
if [ -f "$appr" ] && grep -q "\"$frozen\"" "$appr" 2>/dev/null; then exit 0; fi

log="$HOME/.claude/sprint-apply-gate.log"
proj=$(basename "$root")
ts=$(date '+%F %T' 2>/dev/null || echo '?')

# Deliberate, logged override → allow. [v1, unchanged]
if [ -f "$root/_bmad/.sprint-apply-override" ]; then
  printf '%s OVERRIDE %s :: %s :: %s\n' "$ts" "$proj" "$frozen" "$target" >> "$log" 2>/dev/null
  exit 0
fi

# ─── v2: AUTOPILOT risk classifier (deterministic; fail-closed) ──────────────
amode="off"
[ -f "$HOME/.claude/sprint-apply-autopilot.mode" ] && amode=$(tr -d '[:space:]' < "$HOME/.claude/sprint-apply-autopilot.mode" 2>/dev/null)
[ -f "$root/_bmad/.sprint-apply-autopilot.disable" ] && amode="off"   # kill-switch forces owner-gate

if [ "$amode" = "classify-log" ] || [ "$amode" = "on" ]; then
  # Classify the WHOLE proposal from files_to_change. Empty stdout (any error) → bash fails closed.
  class=$(CC_PEND="$pending" CC_ROOT="$root" CC_MAX="$AUTOPILOT_MAX_FILES" python3 <<'PY' 2>/dev/null
import os, json
try:
    pend = os.environ["CC_PEND"]; root = os.environ["CC_ROOT"]; mx = int(os.environ["CC_MAX"])
    j = json.load(open(pend)); files = j.get("files_to_change", [])
    if not files or len(files) > mx:
        print("owner_gate_required"); raise SystemExit
    out_root = os.path.join(root, "_bmad-output") + os.sep
    impl = os.path.join(root, "_bmad-output", "implementation-artifacts") + os.sep
    GOV = ["/bmad-method-v6/", "/custom/", "/.claude/", "/docs/", "claude.md", "policy", "doctrine"]
    for f in files:
        ap = os.path.abspath(os.path.join(root, f)); low = ap.lower()
        if not ap.startswith(out_root):         # outside _bmad-output (incl. cross-repo) → gate
            print("owner_gate_required"); raise SystemExit
        # SAFE lane = sprint-execution artifacts only: implementation-artifacts/** + epics.md explicitly.
        # planning-artifacts (PRD/architecture/specs) is product-definition → owner-gate.
        if not (ap.startswith(impl) or os.path.basename(ap) == "epics.md"):
            print("owner_gate_required"); raise SystemExit
        if any(s in low for s in GOV):          # governance / shared-infra / doctrine path → gate
            print("owner_gate_required"); raise SystemExit
    print("autopilot_safe")
except SystemExit:
    pass
except Exception:
    pass    # any parse error → empty stdout → fail closed
PY
)
  [ "$class" = "autopilot_safe" ] || class="owner_gate_required"   # fail closed on empty / anything else

  if [ "$class" = "autopilot_safe" ] && [ "$amode" = "on" ]; then
    # PROOF-tier reversibility precondition: snapshot files_to_change BEFORE allowing the write.
    snapdir="$root/_bmad/.sprint-apply-backups/$frozen"
    snap_ok=0
    if [ -d "$snapdir" ] && [ -f "$snapdir/_manifest.txt" ]; then
      snap_ok=1                                   # already snapshotted this proposal
    else
      mkdir -p "$snapdir" 2>/dev/null
      CC_PEND="$pending" CC_ROOT="$root" CC_SNAP="$snapdir" python3 <<'PY' 2>/dev/null
import os, json, shutil
pend = os.environ["CC_PEND"]; root = os.environ["CC_ROOT"]; snap = os.environ["CC_SNAP"]
j = json.load(open(pend)); files = j.get("files_to_change", [])
present = []; absent = []
for f in files:
    ap = os.path.abspath(os.path.join(root, f))
    if os.path.isfile(ap):
        shutil.copy2(ap, os.path.join(snap, f.replace("/", "__"))); present.append(f)
    else:
        absent.append(f)
open(os.path.join(snap, "_manifest.txt"), "w").write(
    "proposal: %s\npresent (restore these to revert):\n%s\nabsent (delete these to revert):\n%s\n"
    % (j.get("proposal_id", "?"), "\n".join(present), "\n".join(absent)))
PY
      [ -f "$snapdir/_manifest.txt" ] && snap_ok=1
    fi
    if [ "$snap_ok" = "1" ]; then
      printf '%s AUTO-APPLY %s :: %s :: %s\n' "$ts" "$proj" "$frozen" "$target" >> "$log" 2>/dev/null
      exit 0
    fi
    printf '%s SNAP-FAIL→OWNER-GATE %s :: %s :: %s\n' "$ts" "$proj" "$frozen" "$target" >> "$log" 2>/dev/null
    # no backup ⇒ no autopilot → fall through to owner-gate
  elif [ "$amode" = "classify-log" ]; then
    if [ "$class" = "autopilot_safe" ]; then
      printf '%s WOULD-AUTOPILOT %s :: %s :: %s\n' "$ts" "$proj" "$frozen" "$target" >> "$log" 2>/dev/null
    else
      printf '%s WOULD-OWNERGATE %s :: %s :: %s\n' "$ts" "$proj" "$frozen" "$target" >> "$log" 2>/dev/null
    fi
    # classify-log NEVER auto-applies → fall through to owner-gate (no behavior change)
  fi
  # amode=on & class=owner_gate_required → fall through to owner-gate
fi

# ─── OWNER-GATE lane (v1, unchanged) ────────────────────────────────────────
mode=""
[ -f "$HOME/.claude/sprint-apply-gate.mode" ] && mode=$(tr -d '[:space:]' < "$HOME/.claude/sprint-apply-gate.mode" 2>/dev/null)
if [ "$mode" = "enforce" ]; then
  printf '%s DENY %s :: %s :: %s\n' "$ts" "$proj" "$frozen" "$target" >> "$log" 2>/dev/null
  reason="$target is frozen by pending Sprint Change Proposal $frozen. To apply: send 'APPROVE: APPLY_SPRINT_PROPOSAL::$frozen' (clears the gate for exactly the proposal's files_to_change). Or write $root/_bmad/.sprint-apply-override with a reason (logged)."
  rj=$(python3 -c "import json,sys;print(json.dumps(sys.argv[1]))" "$reason" 2>/dev/null)
  [ -n "$rj" ] && printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}' "$rj"
  exit 0
fi

# dry-run (default): record what it WOULD block, but ALLOW (no stdout).
printf '%s WOULD-BLOCK %s :: %s :: %s\n' "$ts" "$proj" "$frozen" "$target" >> "$log" 2>/dev/null
exit 0
