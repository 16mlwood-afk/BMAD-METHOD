#!/usr/bin/env python3
"""check-brief-readiness.py — deterministic pre-generation probes over a design brief.

Home of the rule: custom/workflows/design/design-handoff/steps/step-03c-gate1-brief-ready.md
                  (Gate 1) + custom/workflows/design/shared/design-gate-artifacts.md.

A FIRED PROBE IS A QUESTION, NOT A DEFECT. Every finding this tool emits means "the brief
does not appear to determine X" — which a human or a model then resolves against the brief
text. It is wrong to read a fired probe as a defect, to count fired probes as a score, or to
put the count in front of an owner. Gate 1 exists to turn these questions into dispositions.

WHY IT IS A SEPARATE ARTIFACT FROM THE MODEL-DRIVEN REVIEW.
Frames coverage, state-set extraction and absence probes are mechanisable, and a model
should not be trusted to do arithmetic it can be handed instead. The reviewer reads for
sense; this reads for presence. Two independent derivations that must be reconciled is the
same discipline check-ingest-manifest.js applies to `sections_total`.

── What IS and ISN'T deterministically checkable (enforcement-expert axis) ──

 CHECKED (pure presence / arithmetic over the file — no judgement):
   P1  every frame declared in Block B `frames:` is referenced somewhere in the body
       (the same internal-consistency contract step-04-deliver.md §3 asserts pre-stage)
   P2  a declared state set carries an explicit partition claim
   P3  absence probes: does ANY synonym of a required concept appear, on a word boundary
   P4  money fields of differing semantics enumerated on one line

 NOT CHECKED, on purpose — and this is the important half:
   Whether a fired probe is a REAL gap, whether a silent probe means the brief got it
   right, and every class-2 (brief + rendered frames) and class-3 (pixels only) finding.
   Claiming a class-3 finding from a brief is a manufactured defect and is the primary
   failure mode of the whole instrument. A green run here means "the words are present",
   never "the brief is good".

── THE TWO PILOT-EVIDENCED FIXES ARE CANDIDATE FIXES PENDING F1 RUN 2 ──

Both defects below were CONFIRMED by the F1 pilot run under pre-registered predictions
(`.claude/worktrees/gate1-pilot/pilot-f1/f1-run1-status.md`, cash-recovery). That run was
declared INVALID FOR HEADLINE MEASUREMENT because of a fixture-schema defect, so:

  **the defects are measured; the fixes below are NOT.** They are candidate fixes pending
  F1 run 2 against a corrected, pre-registered fixture set. Do not report them as
  validated improvements, and do not quote a precision figure for them.

 D1 · SUBSTRING (candidate fix pending F1 run 2). Absence probes matched naively, so the
      terminal-states synonym "sold" matched inside `soldPrice` and the probe went silent on
      a brief with no terminal-state requirement at all. FIX: every synonym is matched on a
      word boundary (`(?<!\\w)…(?!\\w)`), so `soldPrice`, `sold_price` and `resold` no longer
      satisfy "sold".

 D2 · HOMONYM (candidate fix pending F1 run 2, and DELIBERATELY INCOMPLETE). "confirm"
      matched "the confirmation guard must confirm a specific payload identified by content
      digest" — a different sense of the word — so the irreversible-action probe went silent.
      A true fix needs word-sense analysis and is OUT OF SCOPE for a regex reporter.
      NARROWEST DEFENSIBLE IMPROVEMENT TAKEN: the confirmation probe alone is `context`-gated
      — a synonym hit counts as determining the concept only when an action/consequence term
      appears in the SAME SENTENCE (`irreversible`, `before …`, `undo`, `delete`, `publish`,
      `commit`, …). Nothing else in the brief's vocabulary is touched.

      KNOWN LIMITATION, STATED PLAINLY — this is a co-occurrence proxy, not sense analysis:
        · a homonym sentence that happens to carry an action word still goes silent
          ("the confirm-digest guard runs before the publish step");
        · a genuine requirement written without any context word now FIRES a probe it used
          to pass.
      The asymmetry is deliberate: a false fire costs one question, a silent miss costs the
      defect. That is the only reason this heuristic is defensible at all, and it is why the
      probe reports a QUESTION rather than a verdict.

── Modes ──
  python3 tools/check-brief-readiness.py <brief.md>                 report, exit 0
  python3 tools/check-brief-readiness.py <brief.md> --json          machine-readable
  python3 tools/check-brief-readiness.py <brief.md> --body-sha      print the body SHA-256
  python3 tools/check-brief-readiness.py <brief.md> --strict        exit 1 on any fired probe

`--body-sha` is the SINGLE implementation of the review-binding digest (frontmatter
EXCLUDED, body only). Gate 1 and Gate 3 both call it rather than hand-rolling a shell
recipe, because two copies of a hashing recipe is two hashing recipes.

`--strict` is NOT used by Gate 1. Gate 1 is warn-only in Phase 1 for every instrument
result; a non-zero exit here would make an ordinary question look like a blocking failure.
It exists for a caller that has deliberately decided otherwise.

Golden suite: tools/test/test-check-brief-readiness.py (both directions).
"""

import hashlib
import json
import re
import sys

USAGE = "usage: check-brief-readiness.py <brief.md> [--json] [--body-sha] [--strict]"

# Concepts a brief must determine, and the synonyms that count as determining them.
# Absence of EVERY synonym is what fires the probe (precision rule 3: absence must be
# CHECKED, not assumed — "not in the section I expected" is not "missing").
#
# `context`, when present, is the D2 narrowing: a synonym hit only counts when one of these
# terms appears in the same sentence. Used by exactly one probe, on purpose.
ABSENCE_PROBES = [
    {
        "id": "default-view",
        "concept": "default view",
        "synonyms": ["default view", "defaults to", "opens on", "default filter",
                     "initial view", "when the surface opens", "default tab"],
    },
    {
        "id": "per-item-navigation",
        "concept": "per-item navigation",
        "synonyms": ["next unit", "next item", "advance", "previous/next", "move between",
                     "sequential", "step through", "j/k"],
    },
    {
        "id": "density-budget",
        "concept": "row / density budget",
        "synonyms": ["rows per page", "row budget", "page size", "per page",
                     "density budget", "rows visible", "lines per row"],
    },
    {
        "id": "irreversible-confirmation",
        "concept": "confirmation for irreversible actions",
        "synonyms": ["confirm", "confirmation", "are you sure", "double-check",
                     "restate before"],
        # D2 — see the module docstring. A confirmation requirement is ABOUT an action and
        # its consequence; a confirm-the-payload guard is not.
        "context": ["irreversible", "irreversibly", "undo", "undone", "destructive",
                    "before", "consequence", "consequences", "delete", "deletes", "deleted",
                    "dispose", "publish", "publishes", "send", "sends", "commit", "commits",
                    "write-off", "write off", "approve", "approves", "cancel", "cancels",
                    "action", "permanent", "permanently", "cannot be reversed"],
        "context_note": ("co-occurrence proxy for word sense — see the D2 known limitation "
                         "in the tool docstring; this is a candidate fix pending F1 run 2"),
    },
    {
        "id": "terminal-states",
        "concept": "terminal states",
        "synonyms": ["terminal", "sold", "ended", "archived", "closed",
                     "left the workflow", "no longer actionable"],
    },
    {
        "id": "post-action-states",
        "concept": "post-action / pending states",
        "synonyms": ["pending state", "in-flight state", "loading", "after the press",
                     "post-action", "result state", "outcome must be drawn", "each outcome"],
    },
    {
        "id": "partition-claim",
        "concept": "partition claim over the population",
        "synonyms": ["partition", "partitions", "mutually exclusive", "sums to",
                     "adds up to", "every unit is in exactly", "counted separately"],
    },
]

PARTITION_TERMS = ["partition", "partitions", "mutually exclusive", "sums to",
                   "adds up to", "counted separately"]

# --- P5 conditional probe: disclosure layers (shared/disclosure-layer-contract.md).
#
# CONDITIONAL, and deliberately NOT an ABSENCE_PROBE. An unconditional layering probe would fire on
# every settings page and worklist in the corpus — the indiscriminate-detector anti-pattern that
# gets a tool switched off. It fires only when the brief's OWN TEXT indicates an audit/provenance
# contract (the design owes evidence, source, freshness, derivation, conflicts, override authorship
# or audit history for something the operator commits to) AND the brief determines nothing about
# WHERE that evidence lives.
#
# The failure it asks about: a brief can specify complete provenance, never say which layer it sits
# in, and still read as rigorous. It contradicts no other field, so every other probe passes it, and
# the generator then fills the unspecified slot by rendering the evidence model AS the interface.
# CALIBRATED AGAINST THE REAL CORPUS, not chosen by feel. The first cut of this list also carried
# "override", "stale", "freshness", "derivation", "traceable", "source record" and "generated
# value", with a single-hit trigger. Measured over all 122 design briefs on cash-recovery's
# origin/main it fired on 115 of them — an indiscriminate detector, which is what gets a tool
# switched off. Those words are ordinary UI vocabulary; they do not mark an audit contract.
#
# What survives names an audit obligation directly. Firing needs AUDIT_TERM_THRESHOLD distinct
# hits, because any one of these appears incidentally: measured distribution over the same 122
# briefs is 0 terms:10 · 1:72 · 2:28 · 3:9 · 4:2 · 9:1, so >=3 selects 12 briefs (~10%) and the
# selected set is the genuinely audit-contract-bearing one — listing-composer, owner-approvals,
# ebay-publish-lifecycle, owner-staging, regrade-lineage-ledger, claims-queue-linkage,
# canonical-unit-record, clerk-dispatch-station, owner-reimbursements.
#
# Re-measure before changing either the list or the threshold. `--json` over the corpus is one
# command; a threshold picked by feel is how the first cut reached 94%.
AUDIT_CONTRACT_TERMS = [
    "provenance", "audit event", "audit history", "audit trail", "evidence for",
    "attributable", "authorship", "derived rule", "override history", "who authored",
]

AUDIT_TERM_THRESHOLD = 3

# Any of these means the brief HAS determined the question — the probe stays silent.
#
# DELIBERATELY NARROW, and this list was cut down after it failed its own positive case. The first
# cut also carried "one action away", "default view", "at rest", "inspector", "disclosed",
# "behind a click" and "progressive disclosure". Measured against the real 08-31 Listing Composer
# brief — the brief this whole contract exists because of, which mandated permanent display on
# every ingredient — a SINGLE incidental "one action away" silenced the probe. A phrase appearing
# somewhere is not a determination: that is the mention-is-not-a-use trap, and on a silence list it
# is worse than on a fire list, because it produces a confident quiet.
#
# What survives names a LAYER. A brief cannot say "confidence layer" incidentally.
DISCLOSURE_TERMS = [
    "disclosure_model", "disclosure model",
    "work layer", "confidence layer", "evidence layer",
    "three-layer", "three layer",
]

MONEY_FIELD = re.compile(
    r"\b(price|soldprice|sold_price|recoverable|net|estimatednet|estimated_net|"
    r"cost basis|costbasis|gross|fees|recovery)\b", re.I)

# A sentence ends at ., !, ? or a line break. Markdown bullets and table cells are their own
# units for this purpose, which is what we want — a requirement and its context normally sit
# in one bullet.
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+|\s\|\s")


def phrase_re(phrase):
    """Word-boundary matcher for a possibly multi-word phrase (D1).

    `(?<!\\w)` / `(?!\\w)` rather than `\\b` so a phrase that starts or ends with a
    non-word character (`j/k`, `previous/next`) still anchors correctly. Interior spaces
    accept a hyphen or run of whitespace, never nothing — `nextunit` must not match
    `next unit`.
    """
    parts = [re.escape(w) for w in phrase.split()]
    return re.compile(r"(?<!\w)" + r"[\s\-]+".join(parts) + r"(?!\w)", re.I)


def any_phrase(text, phrases):
    return any(phrase_re(p).search(text) for p in phrases)


def concept_determined(sentences, probe):
    """Does the text determine this probe's concept?

    Without `context`: any word-boundary synonym hit anywhere.
    With `context`: a synonym hit AND a context term in the SAME sentence.
    """
    syns = probe["synonyms"]
    ctx = probe.get("context")
    for s in sentences:
        if not any_phrase(s, syns):
            continue
        if not ctx:
            return True
        if any_phrase(s, ctx):
            return True
    return False


def split_frontmatter(text):
    """Return (frontmatter, body). Body EXCLUDES the frontmatter and its fences.

    Same body definition as step-04-deliver.md §3, so the digest and the brief-contract
    assertion talk about the same bytes.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return "", text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:])
    return "", text


def body_sha256(text):
    body = split_frontmatter(text)[1]
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def declared_frames(fm):
    """Block B `frames:` — inline `[a, b]` OR a block list. Both shapes are legal YAML and
    both appear in the corpus; reading only the inline form silently reports zero frames."""
    m = re.search(r"^frames:\s*\[(.*?)\]", fm, re.M)
    if m:
        return [f.strip().strip("\"'") for f in m.group(1).split(",") if f.strip()]
    lines = fm.split("\n")
    out = []
    for i, ln in enumerate(lines):
        if not re.match(r"^frames:\s*$", ln):
            continue
        for nxt in lines[i + 1:]:
            if re.match(r"^\s*-\s+", nxt):
                out.append(re.sub(r"^\s*-\s+", "", nxt).strip().strip("\"',"))
            elif nxt.strip() == "":
                continue
            else:
                break
        break
    return [f for f in out if f]


def find_state_tables(lines):
    """Rows of any markdown table whose header row mentions 'state'."""
    states, in_tbl, hdr_ok = [], False, False
    for i, ln in enumerate(lines):
        if ln.strip().startswith("|"):
            if not in_tbl:
                in_tbl, hdr_ok = True, "state" in ln.lower()
                continue
            if set(ln.strip()) <= set("|-: "):
                continue
            if hdr_ok:
                cell = ln.strip().strip("|").split("|")[0]
                cell = re.sub(r"[*`]", "", cell).strip()
                if cell and cell.lower() not in ("state", "level"):
                    states.append((i + 1, cell))
        else:
            in_tbl, hdr_ok = False, False
    return states


def analyse(path, text):
    lines = text.split("\n")
    fm, body = split_frontmatter(text)
    sentences = [s for s in SENTENCE_SPLIT.split(body) if s.strip()]
    findings = []

    def fire(probe_id, probe, detail, line=None, informational=False):
        findings.append({"probe_id": probe_id, "probe": probe, "detail": detail,
                         "line": line, "informational": informational})

    # --- P1 frames declared vs referenced in the body
    frames = declared_frames(fm)
    for f in frames:
        if f not in body:
            fire("frames-unreferenced", "frame declared but never referenced in body", f)
    if frames:
        fire("frames-declared", "frames declared (informational)",
             f"{len(frames)}: {', '.join(frames)}", informational=True)

    # --- P2 state set + partition claim
    states = find_state_tables(lines)
    if states:
        names = [s for _, s in states]
        fire("state-set", "state set declared (informational)",
             f"{len(names)}: {', '.join(names)}", line=states[0][0], informational=True)
        if not any_phrase(body, PARTITION_TERMS):
            fire("state-set-no-partition", "state set declared with NO partition claim",
                 f"{len(names)} states declared; the brief never states whether they "
                 "partition the population. A chip row built from this can double-count.",
                 line=states[0][0])

    # --- P3 absence probes
    for probe in ABSENCE_PROBES:
        if concept_determined(sentences, probe):
            continue
        detail = "searched synonyms (word-boundary): " + ", ".join(probe["synonyms"][:4]) + "…"
        if probe.get("context"):
            detail += (" | context-gated: a synonym only counts alongside an "
                       "action/consequence term in the same sentence — "
                       + probe.get("context_note", ""))
        fire(probe["id"], f"no requirement determines: {probe['concept']}", detail)

    # --- P4 money field co-enumeration
    for i, ln in enumerate(lines):
        hits = {h.lower() for h in MONEY_FIELD.findall(ln)}
        if len(hits) >= 3:
            fire("money-co-enumeration",
                 "money fields of differing semantics enumerated together",
                 f"{sorted(hits)} on one line — invites a single shared column", line=i + 1)

    # --- P5 disclosure layers (CONDITIONAL — see AUDIT_CONTRACT_TERMS above).
    # Silent when the brief already carries `disclosure_model` in its frontmatter: that field IS
    # the determination, and `n/a — <why>` is a legitimate answer, not an omission.
    if "disclosure_model" not in fm:
        audit_hits = sorted({t for t in AUDIT_CONTRACT_TERMS if any_phrase(body, [t])})
        if len(audit_hits) >= AUDIT_TERM_THRESHOLD and not any_phrase(body, DISCLOSURE_TERMS):
            shown = ", ".join(audit_hits[:5])
            if len(audit_hits) - 5 >= 1:
                shown += "…"
            fire("disclosure-layers",
                 "audit/provenance obligations stated, but no requirement determines "
                 "WHERE that evidence lives",
                 f"the brief owes {shown} and never assigns a layer. Set `disclosure_model` "
                 "and render §4h (shared/disclosure-layer-contract.md D7), or record "
                 "`disclosure_model: n/a — <why>` if this surface carries no audit contract. "
                 "An unassigned layer is filled by the generator's default, which is to render "
                 "the evidence model AS the interface.")

    fired = [f for f in findings if not f["informational"]]
    return {
        "brief": path,
        "body_sha256": body_sha256(text),
        "frames_declared": len(frames),
        "fired": len(fired),
        "findings": findings,
        "note": "A fired probe is a QUESTION, not a defect.",
        "phase": "Phase 1 — WARN-ONLY: this tool never blocks a handoff.",
    }


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
    unknown = flags - {"--json", "--body-sha", "--strict"}
    if len(args) != 1 or unknown:
        print(USAGE, file=sys.stderr)
        return 2
    path = args[0]
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"check-brief-readiness: cannot read {path}: {exc}", file=sys.stderr)
        return 2

    if "--body-sha" in flags:
        print(body_sha256(text))
        return 0

    report = analyse(path, text)
    if "--json" in flags:
        print(json.dumps(report, indent=2))
    else:
        print(f"check-brief-readiness: {report['brief']}")
        print(f"  body sha256   : {report['body_sha256']}")
        print(f"  frames declared: {report['frames_declared']}")
        print(f"  probes fired  : {report['fired']}")
        print("  NOTE: a fired probe is a QUESTION, not a defect. Phase 1 is WARN-ONLY —")
        print("        no result from this tool blocks a handoff.\n")
        for f in report["findings"]:
            tag = "info " if f["informational"] else "FIRED"
            loc = f" (line {f['line']})" if f["line"] else ""
            print(f"  [{tag}] {f['probe']}{loc}\n         {f['detail']}\n")
    return 1 if ("--strict" in flags and report["fired"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
