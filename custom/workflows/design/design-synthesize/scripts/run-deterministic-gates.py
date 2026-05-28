#!/usr/bin/env python3
"""Deterministic pre-emit gates for design-synthesize step-06.

Runs concrete shell detectors against an emitted bundle BEFORE step-06's
rubric-graded brief-faithfulness pass (§5a g/h/i). The detector output IS
the violation — the agent does not get to rationalize gate hits away.

Detector → §5a check mapping:
    G.2 → active_filter_matches_rows
    G.3 → action_not_duplicated_across_three_surfaces
    G.5 → dividers_consistent_with_filter   (twin of G.2, emitted separately)
    G.6 → empty_state_deliverable_present

The agent's rubric pass in §5a runs AFTER this script, additively. It can
find project-specific contradictions the gates don't cover. But anything
the gates fire on enters the violation arrays unconditionally.

Usage:
    python3 run-deterministic-gates.py <bundle_dir> [--brief <brief.md>]

Exit codes:
    0 — no violations
    1 — at least one violation (correction loop in step-06)
    2 — bad inputs / runtime error (workflow bug)
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path


KNOWN_STATE_LABELS = (
    "action required",
    "awaiting xero push",
    "awaiting xero",
    "reconciled",
    "archived",
    "needs review",
    "ready",
    "filed",
    "excluded",
    "blocked",
    "pending",
    "in progress",
    "completed",
)

UNIVERSAL_BUTTON_TEXT = {
    "×", "x", "close", "dismiss", "cancel", "ok", "save",
    "prev", "next", "previous", "more", "less",
}

# G.3 only fires when the button text contains an entity identifier — a
# specific card, order, invoice, or record reference. This eliminates the
# false-positive class where a generic action ("Run auto-match", "Verify
# matches", "stuck longest") legitimately appears in multiple regions
# (e.g., page header + empty-state CTA).
ENTITY_PATTERN = re.compile(
    r"\b("
    r"\d{3,}"                       # bare digit run: card 9012, period 2026
    r"|[A-Z]{2,}[-_]?\d+"           # INV-09817, PO_12345
    r"|[A-Z0-9]{6,}"                # alphanumeric ID
    r"|\d{3}-\d{6,}-\d{6,}"         # Amazon order ID 306-2841092-4738155
    r")\b"
)


def _strip_tags(html: str) -> str:
    """Strip HTML tags and collapse whitespace — for text-level regex matching."""
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def find_html_files(bundle_dir: Path) -> list[Path]:
    return sorted(p for p in bundle_dir.glob("*.html"))


# ----------------------------------------------------------------------------
# G.2 — active_filter_matches_rows
# ----------------------------------------------------------------------------

def detect_g2_active_filter_matches_rows(html: str, path: str) -> list[dict]:
    """Active filter says X, but in-table dividers introduce other state groups."""
    violations: list[dict] = []
    # Operate on stripped text so inline tags between "Showing" and the state
    # name don't break the match (the bundle frequently wraps the state name
    # in a <span> for typography).
    text = _strip_tags(html)
    match = re.search(
        r"Showing\s+([a-z][a-z\s\-]{2,30}?)\s*(?:[·•]|of\s+\d|\d|rows?|sorted)",
        text, re.I,
    )
    if not match:
        return violations
    active = match.group(1).strip().lower()
    # Trim trailing connector words the lookahead may have left behind.
    active = re.sub(r"\s+(of|the|a)$", "", active).strip()
    if active == "all" or not active:
        return violations

    other_states = [s for s in KNOWN_STATE_LABELS if s != active]
    found: list[str] = []
    for state in other_states:
        # Match "<STATE> · N rows" or "<STATE> · N" near a divider context.
        pattern = re.compile(
            rf"{re.escape(state)}\s*[·•]\s*\d+\s*(?:rows?|matched|ready|verified)",
            re.I,
        )
        if pattern.search(text):
            found.append(state)
            continue
        # Fallback: bare state label inside a section-divider role (raw HTML)
        divider_pattern = re.compile(
            rf"(?:section.?divider|data-component=[\"']SectionDivider[\"'])"
            rf"[^>]*>[^<]*{re.escape(state)}",
            re.I,
        )
        if divider_pattern.search(html):
            found.append(state)
    found = sorted(set(found))
    if found:
        violations.append({
            "check": "active_filter_matches_rows",
            "screen": path,
            "detail": (
                f"active filter label is 'Showing {active}' but in-table "
                f"dividers introduce groups: {', '.join(found)}"
            ),
            "fix": (
                "either (a) when status filter ≠ 'all', remove SectionDivider "
                "elements from rendered rows; OR (b) when dividers are desired, "
                "force the active filter to 'all'. The two cannot coexist."
            ),
            "source": "deterministic_gate_G2",
        })
    return violations


# ----------------------------------------------------------------------------
# G.3 — action_not_duplicated_across_three_surfaces
# ----------------------------------------------------------------------------

class _ButtonExtractor(HTMLParser):
    """Walk the HTML and collect (button_text, ancestor_data_component) pairs.

    A button is anything with tag 'button' or role='button' or an <a> with an
    href that looks like an action (not pure navigation). The ancestor's
    data-component value (if any) is captured so we can detect duplication
    ACROSS regions, not within the same region.
    """

    def __init__(self) -> None:
        super().__init__()
        self._region_stack: list[str | None] = []
        self._capture_stack: list[bool] = []
        self._buf: list[list[str]] = []
        self.buttons: list[tuple[str, str | None]] = []

    def handle_starttag(self, tag, attrs):
        adict = dict(attrs)
        region = adict.get("data-component")
        if region is None and self._region_stack:
            region = self._region_stack[-1]
        self._region_stack.append(region)

        is_button = tag == "button" or adict.get("role") == "button"
        self._capture_stack.append(is_button)
        if is_button:
            self._buf.append([])

    def handle_endtag(self, tag):
        if self._region_stack:
            self._region_stack.pop()
        if self._capture_stack:
            was_button = self._capture_stack.pop()
            if was_button and self._buf:
                text = " ".join(self._buf.pop()).strip()
                text = re.sub(r"\s+", " ", text)
                # Region at the time the button opened is the top of the stack now
                region = self._region_stack[-1] if self._region_stack else None
                if text:
                    self.buttons.append((text, region))

    def handle_startendtag(self, tag, attrs):
        # self-closing — no buffer impact
        pass

    def handle_data(self, data):
        if any(self._capture_stack):
            text = data.strip()
            if text:
                # Append to the innermost open button buffer
                if self._buf:
                    self._buf[-1].append(text)


def detect_g3_action_duplicated(html: str, path: str) -> list[dict]:
    """The same button text appears 2+ times on the same screen."""
    violations: list[dict] = []
    parser = _ButtonExtractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # noqa: BLE001 — best-effort parser
        return violations

    counts: defaultdict[str, list[str | None]] = defaultdict(list)
    for text, region in parser.buttons:
        norm = text.lower().strip()
        if norm in UNIVERSAL_BUTTON_TEXT or len(norm) < 4:
            continue
        counts[text].append(region)

    for text, regions in counts.items():
        if len(regions) < 2:
            continue
        # Only flag entity-specific actions — generic verbs (Run auto-match,
        # Import, Verify) legitimately repeat in header + empty-state + bulk
        # bar. The failure mode this gate exists for is "Map card 9012"
        # surfaced as both a page-level alert button AND a row-level action
        # — one named entity, multiple actionable surfaces.
        if not ENTITY_PATTERN.search(text):
            continue
        # Distinct regions (None counts as 'unscoped')
        distinct_regions = {r if r else "(unscoped)" for r in regions}
        if len(distinct_regions) < 2:
            continue
        violations.append({
            "check": "action_not_duplicated_across_three_surfaces",
            "screen": path,
            "detail": (
                f"button text '{text}' renders {len(regions)} times across "
                f"regions {sorted(distinct_regions)} — entity-specific "
                f"action surfaced on multiple actionable affordances"
            ),
            "fix": (
                "keep the action affordance on a single primary surface "
                "(typically the page-level alert/CTA when one exists). Other "
                "places that surface the underlying state should be quiet "
                "(icon + muted text), not actionable buttons."
            ),
            "source": "deterministic_gate_G3",
        })
    return violations


# ----------------------------------------------------------------------------
# G.5 — dividers_consistent_with_filter (twin of G.2)
# ----------------------------------------------------------------------------

def detect_g5_dividers_consistent_with_filter(html: str, path: str) -> list[dict]:
    return [
        {**v, "check": "dividers_consistent_with_filter",
         "source": "deterministic_gate_G5"}
        for v in detect_g2_active_filter_matches_rows(html, path)
    ]


# ----------------------------------------------------------------------------
# G.6 — empty_state_deliverable_present
# ----------------------------------------------------------------------------

EMPTY_STATE_KEYWORDS = re.compile(
    r"(empty|no[\s\-]results|zero|blank)\s*(?:[\-,]?\s*)?(state|results|view|page)",
    re.I,
)


def detect_g6_empty_state_deliverable(
    bundle_dir: Path, brief_path: Path | None
) -> list[dict]:
    violations: list[dict] = []
    if not brief_path or not brief_path.exists():
        return violations
    brief = brief_path.read_text(errors="ignore")

    # Locate a §7 Deliverable Format / Deliverables section
    deliverables = re.search(
        r"(##\s*7\.[^\n]*?deliver[^\n]*?\n)(.+?)(?=^##\s|\Z)",
        brief, re.M | re.S | re.I,
    )
    if not deliverables:
        deliverables = re.search(
            r"(##\s*Deliverable[s]?[^\n]*?\n)(.+?)(?=^##\s|\Z)",
            brief, re.M | re.S | re.I,
        )
    if not deliverables:
        return violations

    section = deliverables.group(2)
    if not EMPTY_STATE_KEYWORDS.search(section):
        return violations

    empty_files = list(bundle_dir.glob("*-empty.html")) + list(
        bundle_dir.glob("empty-*.html")
    )
    if empty_files:
        return violations

    violations.append({
        "check": "empty_state_deliverable_present",
        "screen": str(bundle_dir),
        "detail": (
            "brief §7 names an empty/no-results state deliverable; bundle "
            "contains no <screen>-empty.html file"
        ),
        "fix": (
            "produce bundle/<screen>-empty.html for each primary worklist "
            "screen, using the same chrome (header, sub-tabs, filter row, "
            "table frame) as the active state — no centered-card-on-gray, "
            "no illustration, short operational copy"
        ),
        "source": "deterministic_gate_G6",
    })
    return violations


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def emit(violations: list[dict]) -> None:
    if not violations:
        print("# deterministic_gates: 0 violations")
        return
    print(f"# deterministic_gates: {len(violations)} violations")
    for v in violations:
        print(f"- check: {v['check']}")
        print(f"  screen: {v['screen']}")
        # YAML-safe one-line detail / fix
        for key in ("detail", "fix", "source"):
            value = v[key].replace("\n", " ")
            # Quote if it contains a colon to keep YAML valid
            if ":" in value:
                value = '"' + value.replace('"', '\\"') + '"'
            print(f"  {key}: {value}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bundle_dir", help="Path to the bundle/ directory")
    ap.add_argument(
        "--brief",
        default=None,
        help="Path to the design brief (.md) for G.6 empty-state check",
    )
    args = ap.parse_args()

    bundle_dir = Path(args.bundle_dir).resolve()
    if not bundle_dir.is_dir():
        print(f"error: bundle_dir is not a directory: {bundle_dir}",
              file=sys.stderr)
        return 2

    brief_path = Path(args.brief).resolve() if args.brief else None

    all_violations: list[dict] = []
    for screen in find_html_files(bundle_dir):
        html = screen.read_text(errors="ignore")
        rel = screen.name
        all_violations += detect_g2_active_filter_matches_rows(html, rel)
        all_violations += detect_g3_action_duplicated(html, rel)
        all_violations += detect_g5_dividers_consistent_with_filter(html, rel)
    all_violations += detect_g6_empty_state_deliverable(bundle_dir, brief_path)

    emit(all_violations)
    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
