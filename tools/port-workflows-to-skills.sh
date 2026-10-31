#!/usr/bin/env bash
#
# port-workflows-to-skills.sh — Phase 2/3 engine of the v6.8 skills migration.
#
# Generates skills-native ports of the fork's custom workflows from custom/workflows/ (old layout)
# into an output tree of `bmad-<name>/` skill dirs. GENERATED ARTIFACT — re-runnable; the source of
# truth stays custom/workflows/ during the dual-layout transition. See custom/MIGRATION-v6.8-skills-plan.md.
#
# SOURCE OF RECORD (do not confuse the two channels): this porter reads ONLY `custom/workflows/`.
# That tree — e.g. `custom/workflows/4-implementation/dev-story/` — IS the fork source of record;
# edit fork workflows THERE. The separate `src/bmm-skills/.../<skill>/SKILL.md` tree is the PLUGIN
# MARKETPLACE source (registered in `.claude-plugin/marketplace.json`), a different downstream
# channel that this porter does NOT read and that does NOT auto-reconcile from custom/. A fork edit
# made only in `src/bmm-skills/` never reaches the 14 synced projects.
#
# Transformations (per the proven pilot):
#   - workflow.md            -> SKILL.md, frontmatter `name:` -> bmad-<name> (== dir, installer gate)
#   - steps/*.md             -> flattened to skill root (installed skills keep step files at root)
#   - templates/, scripts/   -> preserved as subdirs
#   - self step refs         {project-root}/_bmad/bmm/workflows/<self>/steps/X -> ./X
#   - self workflow.md ref   .../<self>/workflow.md -> ./SKILL.md
#   - {installed_path}        rebased to the skill root; {installed_path}/steps/ -> {installed_path}/
#   - cross-workflow refs    .../workflows/<g>/<w>/{workflow.md|steps/X|Y} -> {project-root}/.claude/skills/bmad-<w>/{SKILL.md|X|Y}
#   - shared policy refs     .../workflows/[design/]shared/P and bare shared/P -> {project-root}/_bmad/bmad-shared/P
#   - core workflow refs     {project-root}/_bmad/core/workflows/<w>/workflow.(md|xml) -> {project-root}/.claude/skills/bmad-<w>/SKILL.md
#   - {project-root}/_bmad/bmm/config.yaml, {project-root}/docs/*, core/tasks/* -> left literal (real project files)
#
# Usage: port-workflows-to-skills.sh [<output-dir>]   (default: custom/skills-native/)

set -euo pipefail
FORK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$FORK/custom/workflows"
OUT="${1:-$FORK/custom/skills-native}"
SHARED_OUT="$OUT/_shared"

rm -rf "$OUT"; mkdir -p "$OUT" "$SHARED_OUT"

# Shared-policy home: consolidate both shared dirs + the loose design-level assets
# (brand-identity-template, GREENFIELD-* runbooks) -> {project-root}/_bmad/bmad-shared/.
cp "$SRC/shared/"*.md "$SHARED_OUT/" 2>/dev/null || true
cp "$SRC/design/shared/"*.md "$SHARED_OUT/" 2>/dev/null || true
cp "$SRC/design/"*.md "$SHARED_OUT/" 2>/dev/null || true   # loose design assets (depth-1 files only)
# Alternation of shared filenames, for rewriting BARE `shared/<policy>.md` refs safely.
SHARED_ALT="$(cd "$SHARED_OUT" && ls *.md 2>/dev/null | sed 's/\.md$//' | paste -sd'|' -)"

# Reusable rewrite applied to every .md/.toml in a skill (REL set = self rules on) OR to the
# shared home (REL empty = self rules off). Rules run in order: self -> shared -> cross -> core -> bare.
rewrite_file() {
  REL="${2:-}" SKILL="${3:-}" SHARED_ALT="$SHARED_ALT" perl -0777 -pi -e '
    my $rel=$ENV{REL}//""; my $skill=$ENV{SKILL}//""; my $alt=$ENV{SHARED_ALT};
    if ($rel ne "") {                                   # 1. SELF (skill files only)
      my $p = quotemeta("{project-root}/_bmad/bmm/workflows/$rel");
      s#$p/workflow\.md#./SKILL.md#g;
      s#$p/steps/#./#g;
      s#$p\b#{project-root}/.claude/skills/$skill#g;
    }
    s#\{installed_path\}/steps/#{installed_path}/#g;     # 2. {installed_path} steps collapse
    # 3. SHARED: shared/ subdir, loose design assets, and bare shared/<policy>.md
    #    {project-root}/ prefix is OPTIONAL — some source refs drop it (e.g. _bmad/bmm/workflows/
    #    design/shared/design-standards.md); both forms resolve in the overlay but only the
    #    rewritten form survives cutover. Left lookbehind (?<![\w]) prevents partial-token matches.
    s#(?:\{project-root\}/)?(?<![\w])_bmad/bmm/workflows/(?:design/)?shared/#{project-root}/_bmad/bmad-shared/#g;
    s#\{project-root\}/_bmad/bmm/workflows/design/([A-Za-z0-9_-]+\.md)#{project-root}/_bmad/bmad-shared/$1#g;
    s#(?<![\w./-])shared/($alt)\.md#{project-root}/_bmad/bmad-shared/$1.md#g if $alt;
    # 4. CROSS-WORKFLOW -> sibling skills
    s#\{project-root\}/_bmad/bmm/workflows/[a-z0-9-]+/([a-z0-9-]+)/workflow\.md#{project-root}/.claude/skills/bmad-$1/SKILL.md#g;
    s#\{project-root\}/_bmad/bmm/workflows/[a-z0-9-]+/([a-z0-9-]+)/steps/#{project-root}/.claude/skills/bmad-$1/#g;
    s#\{project-root\}/_bmad/bmm/workflows/[a-z0-9-]+/([a-z0-9-]+)/#{project-root}/.claude/skills/bmad-$1/#g;
    # 5. CORE workflows -> sibling skills
    s#\{project-root\}/_bmad/core/workflows/([a-z0-9-]+)/workflow\.(?:md|xml)#{project-root}/.claude/skills/bmad-$1/SKILL.md#g;
    # 6. BARE workflows dir ref (corpus-location refs in orchestrate/dispatch) -> skills dir
    s#\{project-root\}/_bmad/bmm/workflows/#{project-root}/.claude/skills/#g;
  ' "$1"
}

ported=0
while IFS= read -r wfmd; do
  wdir="$(dirname "$wfmd")"
  rel="${wdir#"$SRC"/}"          # e.g. design/design-elevation  or  4-implementation/code-review
  name="$(basename "$wdir")"
  skill="bmad-$name"
  dst="$OUT/$skill"
  mkdir -p "$dst"

  cp "$wfmd" "$dst/SKILL.md"
  [[ -d "$wdir/steps" ]] && cp "$wdir/steps/"*.md "$dst/" 2>/dev/null || true
  find "$wdir" -maxdepth 1 -type f ! -name workflow.md -exec cp {} "$dst/" \; 2>/dev/null || true
  for sub in templates scripts; do [[ -d "$wdir/$sub" ]] && cp -R "$wdir/$sub" "$dst/"; done

  # Rewrite every .md/.toml in the skill (self rules ON).
  while IFS= read -r f; do rewrite_file "$f" "$rel" "$skill"; done \
    < <(find "$dst" -type f \( -name '*.md' -o -name '*.toml' \))

  # Frontmatter name -> bmad-<name>
  NAME="$name" SKILL="$skill" perl -0777 -pi -e 'my $n=$ENV{NAME}; my $s=$ENV{SKILL}; s/^name:\s*\Q$n\E\s*$/name: $s/m;' "$dst/SKILL.md"
  ported=$((ported + 1))
done < <(find "$SRC" -name workflow.md)

# Rewrite the shared home's own internal cross-references (self rules OFF).
while IFS= read -r f; do rewrite_file "$f"; done < <(find "$SHARED_OUT" -type f -name '*.md')

echo "ported $ported workflows -> $OUT"
echo "shared home: $(ls "$SHARED_OUT" | wc -l | xargs) policies -> $SHARED_OUT (delivers to {project-root}/_bmad/bmad-shared/)"
