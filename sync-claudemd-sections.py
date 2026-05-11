#!/usr/bin/env python3
"""Sync missing CLAUDE.md sections from the BMAD template to project CLAUDE.md files.

Usage:
  sync-claudemd-sections.py --check  TEMPLATE  PROJECT_CLAUDE_MD
  sync-claudemd-sections.py --sync   TEMPLATE  PROJECT_CLAUDE_MD

--check: prints missing section headings, exits 0 if none missing, 1 if any missing
--sync:  injects missing sections into the project file, prints what was added
"""
import re
import sys


def extract_sections(text):
    """Extract ### sections under ## Agent Behavior Rules."""
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
        sections.append((heading, content))

    return sections


def strip_comments(text):
    """Remove HTML comments from text."""
    return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)


def heading_present(heading, project_text):
    """Check if a heading (or close variant) exists in the project file."""
    key_words = re.sub(r'\s*[\u2014\u2013-]+\s*', ' ', heading).strip()
    key_words = re.split(r'\s+', key_words)
    for line in project_text.splitlines():
        if line.startswith('### '):
            normalized = re.sub(r'\s*[\u2014\u2013-]+\s*', ' ', line[4:]).strip()
            if all(w.lower() in normalized.lower() for w in key_words):
                return True
    return False


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
    missing = []

    for heading, content in template_sections:
        if not heading_present(heading, project_text):
            clean_content = strip_comments(content)
            clean_content = re.sub(r'\n{3,}', '\n\n', clean_content).strip() + '\n'
            missing.append((heading, clean_content))

    if mode == '--check':
        for heading, _ in missing:
            print(heading)
        sys.exit(1 if missing else 0)

    if not missing:
        sys.exit(0)

    anchor = find_anchor(project_text)
    insertion = '\n' + '\n'.join(content for _, content in missing) + '\n'
    new_text = project_text[:anchor] + insertion + project_text[anchor:]

    with open(project_path, 'w') as f:
        f.write(new_text)

    for heading, _ in missing:
        print(heading)


if __name__ == '__main__':
    main()
