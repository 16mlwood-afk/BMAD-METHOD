#!/usr/bin/env python3
"""Stop — block a reply that hands Mason a decision that is CLAUDE'S to make.

WHY THIS EXISTS
---------------
2026-09-14, verbatim: *"i want claude to be independant with this sort of descision
making can we enforce this"* — quoting a reply that had just ended:

    The full ranking goes to output/ - rebuilt each run, not committed - because a run
    against different stock is a different answer, not a correction to this one. [...]
    If you'd rather every run be permanently archived, say so and I'll change where it
    lands.

READ WHAT WENT WRONG, BECAUSE IT IS NOT THE OBVIOUS THING.  The reasoning was right, the
rule was applied correctly, and the placement was correct.  The defect is the last
sentence: having decided, the session offered the decision back.  That is not caution,
it is work handed upward — the owner now has to hold a question about gitignore
semantics that the project's own file-tree doctrine already answers, in writing, with a
two-question test.

WHY THE EXISTING GATE DOES NOT CATCH IT, STATED SO NOBODY ASSUMES IT DOES
-------------------------------------------------------------------------
The global `autonomy-gate.py` blocks a permission-seeking reply carrying neither an
`[OWNER GATE: <class>]` label nor a `NEXT AUTONOMOUS ACTION:` line.  The offending reply
carried `NEXT AUTONOMOUS ACTION:` and passed cleanly.  That is the gate's OWN declared
ceiling — presence, never correctness — and this hook fills exactly that one hole for one
decision class, rather than re-litigating the question of whether a reply asked too much.

THE CLASS, AND WHY IT IS DRAWN THIS NARROWLY
---------------------------------------------
Only decisions this repository has ALREADY SETTLED IN WRITING, where offering a choice
contradicts a rule rather than exercising judgement:

  * WHERE A GENERATED FILE LIVES — tracked or gitignored, dated or stable-path.  CLAUDE.md
    § *Which generated files are tracked, and which are not* settles it with two questions:
    would a cold session be WRONG without it (track it) or merely have to re-run something
    cheap (ignore it); and does a second copy SUPERSEDE the first (stable path) or SIT
    BESIDE it (dated).  Both are answerable from the file's own properties.
  * DELIVERY MECHANICS — branch, commit, PR, merge, cleanup.  `~/.claude/CLAUDE.md`
    § *Delivery mechanics are MINE* is explicit, and presenting two branches as a choice
    is the failure it names.

NOT in the class, and deliberately: what a record should SAY, a commercial commitment, a
partner-facing write, anything irreversible, and any question whose answer is a fact only
Mason holds.  Those are his and must keep reaching him.

HOW IT DECIDES, AND WHY A CONJUNCTION
--------------------------------------
It fires only when an OFFER shape and a SETTLED-CLASS term appear in the same reply.  Either
alone is ordinary: explaining that a file is gitignored is useful and common, and asking him
a real question is often right.  It is the pair that marks work going the wrong way.  The
offer phrases are the exact shapes a deferral takes — *"if you'd rather"*, *"say so and I'll"*,
*"would you prefer"* — not a generic question mark, because a reply may legitimately ask
something else entirely while also mentioning a path.

WHAT IT CANNOT DO, so a silent run is not a certificate
--------------------------------------------------------
It reads words.  It cannot tell whether the decision was RIGHT, only that it was not handed
over in one of the shapes listed.  A deferral phrased differently passes, and the same
deferral made in a tool call rather than in prose is invisible to it.  It grades the reply
being closed, and if the harness does not pass that text inline it falls back to the
transcript, which ends at the PREVIOUS turn — in that case it is grading the wrong reply and
says nothing rather than guessing.

Override: `OWNED_DECISION_OVERRIDE=1`, for the case where the placement genuinely turns on
something only Mason knows — a retention obligation, a partner's requirement.  Using it for
ordinary indecision is the thing this exists to stop.
"""

from __future__ import annotations

import json
import os
import re
import sys

# The shapes a deferral actually takes. Not a generic '?' — a reply may ask a real question
# while also mentioning a path, and firing on that would make the guard noise.
OFFER = re.compile(
    r"if you'd rather|if you would rather|if you prefer|would you prefer"
    r"|say so and I'?ll|let me know if you'?d|let me know which|tell me which"
    r"|do you want (?:it|them|me) to|shall I (?:put|keep|track|commit|archive)"
    r"|or should I (?:put|keep|track|commit|archive)|happy to (?:change|move) it",
    re.IGNORECASE,
)

# Decisions this repository has already settled in writing.
SETTLED = re.compile(
    r"\bgitignored?\b|\btracked\b|\buntracked\b|where it lands|permanently archived"
    r"|\bdated (?:file|document|copy|snapshot)\b|stable path"
    r"|which branch|open (?:a|the) PR|squash|merge it|delete the branch",
    re.IGNORECASE,
)

MARKER = 'OWNED-DECISION'


def _content_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                out.append(block.get('text') or '')
        return '\n'.join(out)
    return ''


def current_turn_text(payload: dict) -> str:
    """The reply being closed, which the harness passes inline under a version-dependent key.

    A Stop hook fires as the reply finishes, so the transcript file still ends at the
    PREVIOUS turn. Grading the file would answer "did an earlier reply comply?" when the
    question is "does this one?" — so if the inline text is absent this returns empty and
    the caller stays silent rather than grading the wrong reply.
    """
    for key in ('last_assistant_message', 'assistant_message', 'response', 'message', 'output'):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
        if isinstance(val, dict):
            text = _content_text(val.get('content'))
            if text.strip():
                return text
    return ''


def offending(text: str) -> tuple[str, str] | None:
    """The offer phrase and the settled-class term, when both are present."""
    offer = OFFER.search(text)
    settled = SETTLED.search(text)
    if offer and settled:
        return offer.group(0), settled.group(0)
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    # Never block twice on one turn, and never block a turn that is already a re-run.
    if payload.get('stop_hook_active'):
        return 0

    text = current_turn_text(payload)
    if not text:
        return 0

    hit = offending(text)
    if not hit:
        return 0

    if os.environ.get('OWNED_DECISION_OVERRIDE') == '1':
        return 0

    offer, settled = hit
    print(
        json.dumps(
            {
                'decision': 'block',
                'reason': (
                    f'{MARKER}: this reply offers Mason a decision that is YOURS, and the '
                    'project has already settled it in writing.\n\n'
                    f'  the offer:  "{offer}"\n'
                    f'  the class:  "{settled}"\n\n'
                    'WHERE A GENERATED FILE LIVES is answered by CLAUDE.md, "Which generated '
                    'files are tracked, and which are not", with two questions you can answer '
                    'from the file itself: would a cold session be WRONG without it (track it) '
                    'or merely have to re-run something cheap (ignore it)? And does a second '
                    'copy SUPERSEDE the first (stable path, overwrite) or SIT BESIDE it '
                    '(dated filename)? DELIVERY MECHANICS - branch, commit, PR, merge, cleanup '
                    '- are settled by ~/.claude/CLAUDE.md, "Delivery mechanics are MINE".\n\n'
                    'Decide it, say what you decided and why in one line, and stop. Do not '
                    'append an offer to change it.\n\n'
                    'If the placement genuinely turns on something only he knows - a retention '
                    'obligation, a partner requirement - that is a real owner question: label '
                    'it [OWNER GATE: product-or-policy-doctrine] and set '
                    'OWNED_DECISION_OVERRIDE=1.'
                ),
            }
        )
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
