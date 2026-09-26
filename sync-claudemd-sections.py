#!/usr/bin/env python3
"""Sync missing CLAUDE.md sections from the BMAD template to project CLAUDE.md files.

Usage:
  sync-claudemd-sections.py --check  TEMPLATE  PROJECT_CLAUDE_MD
  sync-claudemd-sections.py --sync   TEMPLATE  PROJECT_CLAUDE_MD

--check: prints missing section headings, exits 0 if none missing, 1 if any missing
--sync:  injects missing sections into the project file, prints what was added.
         Also backfills stable-id markers onto sections that already match by
         keyword but carry no marker yet (self-healing — see "Section identity").

Section identity (root-cause fix)
---------------------------------
A section's identity is a stable id declared in the template as an HTML-comment
marker on the line directly under its heading:

    ### Deployment — BMAD contract
    <!-- bmad:deploy-contract -->

The id is decoupled from the visible heading text. When a section is RENAMED in
the template, its id stays the same, so project copies are still recognised and
NOT re-inserted as duplicates. Previously, identity was inferred purely from
heading keywords: requiring every template-heading word to appear in a project
heading. A rename that changed the wording (e.g. "ALWAYS Deploy After Merge —
CRITICAL" -> "Deployment — BMAD contract", sharing only "deploy") defeated that
heuristic and the section was re-inserted with stale/generic content.

Matching precedence per template section:
  1. id marker present anywhere in the project file  -> present (rename-safe)
  2. else keyword-all-match against project headings  -> present (legacy fallback)
  3. else                                             -> missing (insert)

On --sync, any section that matches by keyword but lacks its marker in the
project file gets the marker backfilled under the matched heading. After one
clean sync the whole fleet carries markers, so subsequent renames never
duplicate. Markers are invisible in rendered Markdown.
"""
import re
import sys

# A section-identity marker: <!-- bmad:some-stable-id -->
MARKER_RE = re.compile(r'<!--\s*bmad:([a-z0-9][a-z0-9-]*)\s*-->')


def section_id_in(text, section_id):
    """True if the given stable id marker appears anywhere in text."""
    return any(m.group(1) == section_id for m in MARKER_RE.finditer(text))


def extract_sections(text):
    """Extract ### sections under ## Agent Behavior Rules.

    Returns a list of (heading, section_id_or_None, content) tuples. The content
    retains the heading line and any bmad id marker so insertion carries the id.
    """
    rules_match = re.search(r'^## Agent Behavior Rules\s*\n', text, re.MULTILINE)
    if not rules_match:
        return []

    rules_start = rules_match.end()
    next_h2 = re.search(r'^## ', text[rules_start:], re.MULTILINE)
    rules_text = text[rules_start:rules_start + next_h2.start()] if next_h2 else text[rules_start:]

    sections = []
    for match in re.finditer(r'^### (.+)', rules_text, re.MULTILINE):
        heading = match.group(1).strip()
        start = match.start()
        next_section = re.search(r'^### ', rules_text[match.end():], re.MULTILINE)
        if next_section:
            end = match.end() + next_section.start()
        else:
            end = len(rules_text)
        content = rules_text[start:end].rstrip('\n') + '\n'
        id_match = MARKER_RE.search(content)
        section_id = id_match.group(1) if id_match else None
        sections.append((heading, section_id, content))

    return sections


def strip_comments(text):
    """Remove HTML comments from text, but PRESERVE bmad id markers.

    Stripping the marker on insertion would discard the section's identity, so
    the next sync would re-insert it as a duplicate. Only non-marker comments
    (template authoring notes) are removed.
    """
    def repl(m):
        return m.group(0) if MARKER_RE.fullmatch(m.group(0).strip()) else ''
    return re.sub(r'<!--.*?-->', repl, text, flags=re.DOTALL)


def heading_key_words(heading):
    """Distinctive words of a heading, with em/en dashes normalised to spaces."""
    key_words = re.sub(r'\s*[—–-]+\s*', ' ', heading).strip()
    return re.split(r'\s+', key_words)


def matching_heading_line(heading, project_lines):
    """Index of the first project '### ' line whose words cover the heading's, else None."""
    key_words = heading_key_words(heading)
    for i, line in enumerate(project_lines):
        if line.startswith('### '):
            normalized = re.sub(r'\s*[—–-]+\s*', ' ', line[4:]).strip()
            if all(w.lower() in normalized.lower() for w in key_words):
                return i
    return None


def section_present(section_id, heading, project_text, project_lines):
    """A template section is present if its id marker exists, or a heading matches."""
    if section_id and section_id_in(project_text, section_id):
        return True
    return matching_heading_line(heading, project_lines) is not None


def find_anchor(project_text):
    """Find the best insertion point for missing sections."""
    for anchor in ['Do NOT search endlessly', 'Stale Server Code', 'NEVER Hardcode Secrets']:
        m = re.search(rf'^### {re.escape(anchor)}', project_text, re.MULTILINE)
        if m:
            return m.start()

    rules_match = re.search(r'^## Agent Behavior Rules\s*\n', project_text, re.MULTILINE)
    if rules_match:
        next_h2 = re.search(r'^## ', project_text[rules_match.end():], re.MULTILINE)
        if next_h2:
            return rules_match.end() + next_h2.start()
        return len(project_text)

    return len(project_text)


def backfill_markers(template_sections, project_text):
    """Stamp stable-id markers onto present-but-unmarked project sections.

    Returns (new_project_text, backfilled_ids). Idempotent: a section whose id
    marker already exists is skipped. Only runs for sections matched by keyword
    (so the marker lands under the correct, possibly-renamed heading).
    """
    backfilled = []
    for heading, section_id, _ in template_sections:
        if not section_id or section_id_in(project_text, section_id):
            continue
        lines = project_text.splitlines()
        line_idx = matching_heading_line(heading, lines)
        if line_idx is None:
            continue  # genuinely missing — handled by the insertion pass
        lines.insert(line_idx + 1, f'<!-- bmad:{section_id} -->')
        trailing_nl = '\n' if project_text.endswith('\n') else ''
        project_text = '\n'.join(lines) + trailing_nl
        backfilled.append(section_id)
    return project_text, backfilled


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ('--check', '--sync'):
        print(__doc__, file=sys.stderr)
        sys.exit(2)

    mode = sys.argv[1]
    template_path = sys.argv[2]
    project_path = sys.argv[3]

    with open(template_path) as f:
        template_text = f.read()
    with open(project_path) as f:
        project_text = f.read()

    template_sections = extract_sections(template_text)

    def compute_missing(text):
        lines = text.splitlines()
        missing = []
        for heading, section_id, content in template_sections:
            if not section_present(section_id, heading, text, lines):
                clean = strip_comments(content)
                clean = re.sub(r'\n{3,}', '\n\n', clean).strip() + '\n'
                missing.append((heading, clean))
        return missing

    if mode == '--check':
        missing = compute_missing(project_text)
        for heading, _ in missing:
            print(heading)
        sys.exit(1 if missing else 0)

    # --sync: backfill identity markers first, then insert genuinely-missing sections.
    project_text, backfilled = backfill_markers(template_sections, project_text)
    missing = compute_missing(project_text)

    if not missing and not backfilled:
        sys.exit(0)

    if missing:
        anchor = find_anchor(project_text)
        insertion = '\n' + '\n'.join(content for _, content in missing) + '\n'
        project_text = project_text[:anchor] + insertion + project_text[anchor:]

    with open(project_path, 'w') as f:
        f.write(project_text)

    for heading, _ in missing:
        print(heading)
    for section_id in backfilled:
        print(f'[marker backfilled] {section_id}')


if __name__ == '__main__':
    main()
