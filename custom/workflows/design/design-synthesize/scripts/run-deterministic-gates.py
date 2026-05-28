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

# G.7 — §3 color hierarchy.
# Each operational state binds to exactly one color family per policy §3.
# A state rendered with two different families on the same page = inconsistency.
STATE_TO_FAMILY = {
    # red — primary/blocking weight
    "action required": "red",
    "failed": "red",
    "blocked": "red",
    "not filed": "red",
    "error": "red",
    "rejected": "red",
    # yellow/amber — mid weight (needs attention)
    "needs review": "yellow",
    "attention required": "yellow",
    "manual classification pending": "yellow",
    "review required": "yellow",
    "pending review": "yellow",
    # green — restrained weight (success / done)
    "ready": "green",
    "filed": "green",
    "reconciled": "green",
    "success": "green",
    "completed": "green",
    "verified": "green",
    # gray — resting weight
    "queued": "gray",
    "unknown": "gray",
    "not-yet-processed": "gray",
    "not yet processed": "gray",
    "archived": "gray",
    "pending": "gray",
    "excluded": "gray",
}

# Hex/RGB color-string → family. Built defensively — only entries that
# unambiguously identify a family. Ambiguous neutrals stay un-mapped (None).
COLOR_TO_FAMILY = {
    # red / rose family
    "#7f1d1d": "red", "#991b1b": "red", "#b91c1c": "red", "#dc2626": "red",
    "#ef4444": "red", "#f87171": "red", "#fca5a5": "red", "#fecaca": "red",
    "#fee2e2": "red", "#fef2f2": "red",
    # amber / yellow family
    "#78350f": "yellow", "#92400e": "yellow", "#b45309": "yellow",
    "#d97706": "yellow", "#f59e0b": "yellow", "#fbbf24": "yellow",
    "#fcd34d": "yellow", "#fde68a": "yellow", "#fef3c7": "yellow",
    "#fffbeb": "yellow",
    # green / emerald family
    "#14532d": "green", "#166534": "green", "#15803d": "green",
    "#16a34a": "green", "#22c55e": "green", "#4ade80": "green",
    "#86efac": "green", "#bbf7d0": "green", "#dcfce7": "green",
    "#f0fdf4": "green", "#059669": "green", "#10b981": "green",
    # gray / neutral / slate family
    "#171717": "gray", "#262626": "gray", "#404040": "gray",
    "#525252": "gray", "#737373": "gray", "#a3a3a3": "gray",
    "#d4d4d4": "gray", "#e5e5e5": "gray", "#f5f5f5": "gray",
    "#fafafa": "gray",
}

# Tailwind color-token prefixes → family (when classes leak into bundle HTML).
CLASS_PREFIX_TO_FAMILY = {
    "red": "red", "rose": "red",
    "amber": "yellow", "yellow": "yellow", "orange": "yellow",
    "green": "green", "emerald": "green", "lime": "green",
    "gray": "gray", "slate": "gray", "neutral": "gray", "zinc": "gray", "stone": "gray",
}

# State-label synonyms — different surface phrasings of the same operational
# state. The semantic state is the dict value; rendered label is the dict key.
STATE_SYNONYMS = {
    "need action": "action required",
    "needs action": "action required",
    "action-required": "action required",
    "needs filing": "not filed",
    "needs review": "needs review",
    "review needed": "needs review",
    "action required": "action required",
}


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
# G.7 — status_color_consistency_with_§3_hierarchy
# ----------------------------------------------------------------------------

class _TreeNode:
    """Lightweight DOM node — children is a list of _TreeNode or str."""
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs, parent):
        self.tag = tag
        self.attrs = dict(attrs) if attrs else {}
        self.children: list = []
        self.parent = parent


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.root = _TreeNode("__root__", {}, None)
        self._current = self.root

    def handle_starttag(self, tag, attrs):
        child = _TreeNode(tag, attrs, self._current)
        self._current.children.append(child)
        self._current = child

    def handle_endtag(self, tag):
        if self._current.parent is not None:
            self._current = self._current.parent

    def handle_startendtag(self, tag, attrs):
        # Void/self-closing — append but don't descend.
        self._current.children.append(_TreeNode(tag, attrs, self._current))

    def handle_data(self, data):
        self._current.children.append(data)


# Grouping elements whose immediate inner content is treated as a single
# "state rendering" — colors found in this subtree are correlated with state
# labels found in the same subtree.
GROUPING_TAGS = {"button", "a", "td", "li", "div", "span", "section", "nav"}


def _node_text(node: _TreeNode) -> str:
    """Concatenated text content of a node and its descendants."""
    parts: list[str] = []
    stack: list = [node]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            parts.append(item)
        else:
            for child in reversed(item.children):
                stack.append(child)
    return " ".join(p.strip() for p in parts if p.strip())


def _collect_colors_in_subtree(node: _TreeNode) -> set[tuple[str, str]]:
    """All (family, source) pairs from inline styles + classes within this
    subtree. Recurses into children but stops at nested grouping elements
    deeper than two levels — siblings of the state-label container are
    in-scope; distant cousins are not.
    """
    found: set[tuple[str, str]] = set()
    stack: list[tuple[_TreeNode, int]] = [(node, 0)]
    while stack:
        current, depth = stack.pop()
        if not isinstance(current, _TreeNode):
            continue
        style = current.attrs.get("style", "")
        classes = current.attrs.get("class", "")
        for m in re.finditer(r"#[0-9a-fA-F]{6}", style):
            family = COLOR_TO_FAMILY.get(m.group(0).lower())
            if family:
                found.add((family, f"style: {m.group(0)}"))
        for cls in classes.split():
            m = re.match(
                r"(?:text|bg|border|ring|fill|stroke|from|to|via)-([a-z]+)-\d+",
                cls,
            )
            if m:
                family = CLASS_PREFIX_TO_FAMILY.get(m.group(1))
                if family:
                    found.add((family, f"class: {cls}"))
        for child in current.children:
            if isinstance(child, _TreeNode):
                stack.append((child, depth + 1))
    return found


def _canonical_state(label: str) -> str:
    return STATE_SYNONYMS.get(label, label)


def detect_g7_status_color_consistency(html: str, path: str) -> list[dict]:
    """For each operational state label rendered on the page, verify all
    visual treatments use the §3-mandated color family.

    Strategy: parse the HTML into a tree; for each state-label text node,
    find the smallest enclosing grouping element (button/td/li/div/span);
    collect color context from that element's full subtree (siblings of the
    label container, not just ancestors — the amber dot + amber count in
    the inline-summary chip are siblings of the "need action" label).
    """
    violations: list[dict] = []
    builder = _TreeBuilder()
    try:
        builder.feed(html)
        builder.close()
    except Exception:  # noqa: BLE001
        return violations

    # state_canonical → set of (family, source)
    observations: defaultdict[str, set[tuple[str, str]]] = defaultdict(set)

    # All known labels including synonyms, longest-first to prefer specific.
    all_labels = sorted(
        set(STATE_TO_FAMILY.keys()) | set(STATE_SYNONYMS.keys()),
        key=len, reverse=True,
    )

    # Walk every text node; find labels; locate the smallest enclosing
    # grouping element; harvest its subtree's color context.
    stack: list = [builder.root]
    seen_pairs: set[tuple[int, str]] = set()
    while stack:
        node = stack.pop()
        if isinstance(node, str):
            continue
        for child in node.children:
            if isinstance(child, _TreeNode):
                stack.append(child)
                continue
            text = child.lower().strip()
            text = re.sub(r"\s+", " ", text)
            if not text:
                continue
            for label in all_labels:
                if label not in text:
                    continue
                # Tighten: the label must be the dominant content of this
                # text node (≥70% of the trimmed text). This skips false
                # positives where the state word appears inside a longer
                # phrase that's clearly not a status rendering — e.g.,
                # "match verified · Xero push blocked …" mentions "verified"
                # but is not a verified-state pill.
                if len(label) < 0.7 * len(text) and text != label:
                    # Allow short prefixes/suffixes (counts, separators)
                    # e.g., "47 need action", "need action ·"
                    stripped = re.sub(r"^[\d\s·•,()]+|[\d\s·•,()]+$", "", text)
                    if stripped != label and len(label) < 0.7 * len(stripped):
                        continue
                # Walk up ancestors until we find a grouping element whose
                    # subtree carries color context. The state label's visual
                    # treatment may live on siblings of its immediate wrapper
                    # — e.g., the amber dot + count chip are siblings of the
                    # inner <span> that holds "need action", so we have to
                    # walk past the inner <span> to its <button> ancestor.
                canonical = _canonical_state(label)
                container = node
                found_colors: set[tuple[str, str]] = set()
                while container is not None:
                    if container.tag in GROUPING_TAGS:
                        pair = (id(container), label)
                        if pair in seen_pairs:
                            break
                        colors = _collect_colors_in_subtree(container)
                        if colors:
                            seen_pairs.add(pair)
                            found_colors = colors
                            break
                    container = container.parent
                for fam_src in found_colors:
                    observations[canonical].add(fam_src)
                break  # one label per text node — longest-first preference

    for canonical, obs in observations.items():
        families = {family for family, _ in obs}
        if len(families) <= 1:
            continue
        expected = STATE_TO_FAMILY.get(canonical)
        sources = sorted({src for _, src in obs})
        if expected and expected in families:
            extras = sorted(families - {expected})
            detail = (
                f"state '{canonical}' (per §3 → {expected}) renders with "
                f"additional families {extras} elsewhere on the screen. "
                f"sources: {sources[:6]}"
            )
        else:
            detail = (
                f"state '{canonical}' (per §3 → {expected or 'unmapped'}) "
                f"renders with multiple non-§3-aligned families "
                f"{sorted(families)}. sources: {sources[:6]}"
            )
        violations.append({
            "check": "status_color_consistency_with_§3_hierarchy",
            "screen": path,
            "detail": detail,
            "fix": (
                f"route every rendering of '{canonical}' through the §3 "
                f"weight ({expected or 'mapped family'}); drop the other "
                f"families from any element labelled with this state "
                f"(inline summary, count chips, segment buttons, banners)"
            ),
            "source": "deterministic_gate_G7",
        })
    return violations


# ----------------------------------------------------------------------------
# G.8 — tier1_column_placement
# ----------------------------------------------------------------------------

# Tier 1 headers per policy §6 — identifier-class + primary status column.
# "Status" is the literal §6-mandated Tier 1 column most commonly misplaced.
TIER1_HEADER_PATTERNS = (
    re.compile(r"^status\b", re.I),
)


def detect_g8_tier1_column_placement(html: str, path: str) -> list[dict]:
    """For each <table>, find the first <thead>; flag any Tier-1 column
    (per policy §6) landing at index > 3 (1-based: position > 4).
    """
    violations: list[dict] = []
    # Extract the first <thead>...</thead> block per table
    thead_blocks = re.findall(r"<thead[^>]*>(.*?)</thead>", html, re.I | re.S)
    if not thead_blocks:
        return violations

    for thead in thead_blocks:
        # Extract <th> contents in order
        ths = re.findall(r"<th[^>]*>(.*?)</th>", thead, re.I | re.S)
        if len(ths) < 4:
            # Too few columns for tier-1 placement to be meaningful
            continue
        for idx, th in enumerate(ths):
            text = re.sub(r"<[^>]+>", " ", th)
            text = re.sub(r"\s+", " ", text).strip()
            for pattern in TIER1_HEADER_PATTERNS:
                if pattern.match(text):
                    # 1-based index for human-readable detail
                    position = idx + 1
                    if position > 4:
                        violations.append({
                            "check": "tier1_column_placement",
                            "screen": path,
                            "detail": (
                                f"Tier-1 column '{text}' placed at "
                                f"position {position} of {len(ths)}; "
                                f"policy §6 mandates Tier-1 columns "
                                f"(identifiers + status) leftmost (≤4)"
                            ),
                            "fix": (
                                f"move '{text}' to position ≤ 4 (after "
                                f"date + primary identifier columns). "
                                f"Keep Action / row-action columns rightmost."
                            ),
                            "source": "deterministic_gate_G8",
                        })
                    break
    return violations


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
        all_violations += detect_g7_status_color_consistency(html, rel)
        all_violations += detect_g8_tier1_column_placement(html, rel)
    all_violations += detect_g6_empty_state_deliverable(bundle_dir, brief_path)

    emit(all_violations)
    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
