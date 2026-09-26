#!/usr/bin/env python3
"""Golden suite for deploy_lane_guard.py — BOTH directions.

    python3 .claude/hooks/test_deploy_lane_guard.py

Every FIRE case has a SILENT twin. A deploy guard that fires on `railway logs`,
on a commit message that names the command it polices, or on `railway run make up`
is a guard somebody switches off — and then it protects nothing.

Drives the real stdin/JSON contract as well as the pure detector, and pins the
warn/deny mode selection, so a settings change cannot silently flip it.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUARD = HERE / "deploy_lane_guard.py"
spec = importlib.util.spec_from_file_location("dlg", GUARD)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

passed = failed = 0


def check(label, expected, actual):
    global passed, failed
    if expected == actual:
        passed += 1
    else:
        failed += 1
        print(f"  ✗ {label}\n      expected: {expected!r}\n      actual:   {actual!r}")


FIRE = [
    ("bare railway up", "railway up", "railway up"),
    ("railway up with flags", "railway up --detach", "railway up"),
    ("railway redeploy", "railway redeploy", "railway redeploy"),
    ("global flag before the subcommand", "railway --service cash-recovery up", "railway up"),
    ("after a cd", "cd /Users/x/code/app && railway up", "railway up"),
    ("chained after an unrelated command", "git pull && railway up", "railway up"),
    ("lane AND a bare up (the compound bypass)", "./scripts/deploy.sh && railway up", "railway up"),
    ("heredoc then a real up", "cat <<EOF > /tmp/n\nnotes about railway up\nEOF\nrailway up", "railway up"),
    ("unterminated heredoc still fires", "cat <<EOF\nrailway up", "railway up"),
    ("vercel --prod", "vercel --prod", "vercel --prod"),
    ("vercel deploy", "npx vercel deploy", "vercel deploy"),
    ("wrangler deploy", "wrangler deploy", "wrangler deploy"),
    ("wrangler pages deploy", "wrangler pages deploy ./dist", "wrangler pages deploy"),
    ("fly deploy", "fly deploy --remote-only", "fly deploy"),
    ("flyctl deploy", "flyctl deploy", "flyctl deploy"),
    ("gcloud run deploy", "gcloud run deploy api --source .", "gcloud run deploy"),
    ("firebase deploy", "firebase deploy --only hosting", "firebase deploy"),
    ("netlify deploy", "netlify deploy --prod", "netlify deploy"),
    ("serverless deploy", "sls deploy --stage prod", "sls deploy"),
    ("cdk deploy", "cdk deploy --all", "cdk deploy"),
    ("git push heroku", "git push heroku main", "git push heroku"),
    ("absolute path to the CLI", "/opt/homebrew/bin/railway up", "railway up"),
]

SILENT = [
    ("the lane itself", "./scripts/deploy.sh"),
    ("the lane with a cd", "cd /Users/x/code/app-deploy && ./scripts/deploy.sh"),
    ("the lane with an env prefix", "DEPLOY_ROLLBACK=1 ./scripts/deploy.sh"),
    ("the lane's dry run", "./scripts/deploy.sh --dry-run 2>&1 | tail -20"),
    ("railway status", "railway status"),
    ("railway variables", "railway variables --json | python3 -c 'import json,sys'"),
    ("railway logs piped to grep up", "railway logs | grep up"),
    ("railway ssh printenv", "railway ssh printenv APP_COMMIT_SHA"),
    ("railway run wrapping a task runner", "railway run make up"),
    ("railway deployment list", "railway deployment list --json | head"),
    ("railway link", "railway link --project app --environment production --service app"),
    ("the command in double quotes", 'echo "never run railway up by hand"'),
    ("the command in single quotes", "python3 -c 'print(\"railway up\")'"),
    ("git commit heredoc naming the lane",
     "git commit -q -F - <<EOF\nfix: block a bare railway up\nUse ./scripts/deploy.sh\nEOF\ngit log -1"),
    ("heredoc with a quoted delimiter", "git commit -q -F - <<'EOF'\nrailway up is forbidden\nEOF"),
    ("dash-indented heredoc", "cat <<-EOF > /tmp/doc\n\trailway up is the wrong lane\n\tEOF"),
    ("vercel env pull", "vercel env pull .env.local"),
    ("vercel inspect", "vercel inspect https://x.vercel.app"),
    ("wrangler tail", "wrangler tail"),
    ("wrangler dev", "wrangler dev"),
    ("fly status", "fly status"),
    ("fly ssh console", "fly ssh console -C 'railway up'"),
    ("gcloud run services list", "gcloud run services list"),
    ("git push origin", "git push -u origin feat/x"),
    ("git push to a branch named deploy", "git push origin deploy"),
    ("an unrelated word", "grep -rn 'deploy' src | head"),
    ("a file path containing a provider name", "cat docs/railway-notes.md"),
    ("empty", ""),
]

print("── detector: must fire ──")
for label, cmd, expected in FIRE:
    check(label, expected, g.find_bare_ship(cmd))

print("── detector: must stay silent ──")
for label, cmd in SILENT:
    check(label, None, g.find_bare_ship(cmd))

print("── a custom lane name ──")
check("custom lane token is sanctioned", None, g.find_bare_ship("./scripts/ship.sh", lane="scripts/ship.sh"))
check("default lane is NOT sanctioned when the project names another",
      "railway up", g.find_bare_ship("./scripts/deploy.sh && railway up", lane="scripts/ship.sh"))


def run(cmd, env=None, cwd=None):
    e = {**os.environ, "HOME": tempfile.gettempdir()}
    e.pop("DEPLOY_UNSTAMPED", None); e.pop("DEPLOY_LANE_MODE", None); e.pop("CLAUDE_PROJECT_DIR", None)
    e.update(env or {})
    r = subprocess.run([sys.executable, str(GUARD)], input=json.dumps({"tool_input": {"command": cmd}}),
                       capture_output=True, text=True, env=e, cwd=cwd)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else None)


print("── stdin contract, modes and override ──")
with tempfile.TemporaryDirectory() as tmp:
    plain = Path(tmp) / "plain"; (plain / "_bmad" / "bmm").mkdir(parents=True)
    (plain / "_bmad" / "bmm" / "config.yaml").write_text("deploy:\n  method: manual_cli\n")
    deny = Path(tmp) / "deny"; (deny / "_bmad" / "bmm").mkdir(parents=True)
    (deny / "_bmad" / "bmm" / "config.yaml").write_text("deploy:\n  method: manual_cli\n  guard_mode: deny\n  lane: scripts/ship.sh\n")

    rc, out = run("railway up", cwd=plain)
    check("exit 0 always (never a hook error)", 0, rc)
    check("default mode is WARN via additionalContext", True,
          bool(out and "additionalContext" in out["hookSpecificOutput"]))
    check("warn carries no permissionDecision", False,
          bool(out and "permissionDecision" in out["hookSpecificOutput"]))
    check("every decision is deny-eligible", True, bool(out and out["hookSpecificOutput"].get("deny_eligible")))

    rc, out = run("railway up", cwd=deny)
    check("deploy.guard_mode: deny promotes to a hard deny", "deny",
          out and out["hookSpecificOutput"].get("permissionDecision"))
    check("the deny reason names the project's own lane", True,
          bool(out and "scripts/ship.sh" in out["hookSpecificOutput"]["permissionDecisionReason"]))
    rc, out = run("./scripts/ship.sh", cwd=deny)
    check("the project's named lane is silent in deny mode", None, out)

    rc, out = run("railway up", env={"DEPLOY_LANE_MODE": "deny"}, cwd=plain)
    check("DEPLOY_LANE_MODE=deny promotes per shell", "deny", out and out["hookSpecificOutput"].get("permissionDecision"))
    rc, out = run("railway up", env={"DEPLOY_LANE_MODE": "warn"}, cwd=deny)
    check("DEPLOY_LANE_MODE=warn demotes per shell", True, bool(out and "additionalContext" in out["hookSpecificOutput"]))

    rc, out = run("railway up", env={"DEPLOY_UNSTAMPED": "1"}, cwd=deny)
    check("the override is silent (and logged)", None, out)
    rc, out = run("railway up", env={"DEPLOY_UNSTAMPED": "yes"}, cwd=deny)
    check("the override is exact-match — 'yes' does not open it", "deny",
          out and out["hookSpecificOutput"].get("permissionDecision"))

    rc, out = run("railway status", cwd=deny)
    check("a read-only subcommand is silent even in deny mode", None, out)
    r = subprocess.run([sys.executable, str(GUARD)], input="not json", capture_output=True, text=True)
    check("malformed stdin: silent, exit 0", (0, ""), (r.returncode, r.stdout.strip()))

print()
if failed:
    print(f"FAIL — {failed} failing, {passed} passing"); sys.exit(1)
print(f"ok — {passed} cases, both directions")
