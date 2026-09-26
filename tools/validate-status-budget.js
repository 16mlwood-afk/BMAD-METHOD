/**
 * validate-status-budget.js
 *
 * Deterministic guard for STATUS.md's hot path. The mason-bmad-workflow-expert
 * skill reads STATUS.md's `## Now` block + the top of `## Changelog` on EVERY
 * invocation, so that region must stay compact. STATUS regresses in two ways the
 * 2026-06-12 restructure was meant to remove (logged in docs/fork-gaps.md):
 *
 *   1. STRAY BLOCKS ABOVE `## Now` — `**Last updated:**` / `**Prior:**` wave
 *      paragraphs wedged between the title and `## Now`, in a no-man's-land that
 *      is neither Now nor Changelog but is read as the file head. A wave record
 *      belongs in `## Changelog` as a discrete `### YYYY-MM-DD — title (commit)`
 *      entry; `## Now` is REPLACED each wave, not appended to.
 *   2. `## Now` BULLET PILE-UP — `- **Latest wave:**` / `- **Prior wave:**`
 *      bullets stacking far past the "latest 1-2 waves" the block should carry.
 *
 * WARN only (exit 0) by default — surfaced, not blocked, because the cleanup of
 * an existing pile-up is a focused pass, not something to hard-gate mid-stream
 * (matches validate-context-budget.js's philosophy). Run with --strict to
 * escalate findings to a failure (exit 1) — intended for AFTER the one-time
 * re-split, to keep STATUS.md from regressing.
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const STATUS = path.join(ROOT, 'STATUS.md');

// --- thresholds (tunable) ---------------------------------------------------
const MAX_STRAY_BLOCKS_ABOVE_NOW = 0; // any `**Last updated:**`/`**Prior:**` above `## Now` is a finding
const MAX_NOW_WAVE_BULLETS = 6; // `## Now` should carry only the latest handful, not the full history

const strict = process.argv.includes('--strict');

function main() {
  if (!fs.existsSync(STATUS)) {
    console.log('status-budget: STATUS.md not found — skipping.');
    return 0;
  }
  const lines = fs.readFileSync(STATUS, 'utf8').split('\n');

  const nowIdx = lines.findIndex((l) => /^##\s+Now\b/.test(l));
  const changelogIdx = lines.findIndex((l) => /^##\s+Changelog\b/.test(l));

  const findings = [];

  if (nowIdx === -1) {
    findings.push(
      'STATUS.md has no `## Now` section — the structured format (## Now + ## Changelog) is gone; re-split per assets/STATUS-template.md.',
    );
  } else {
    // 1. stray wave blocks ABOVE `## Now`
    const strayAbove = lines.slice(0, nowIdx).filter((l) => /^\*\*(Last updated|Prior):\*\*/.test(l)).length;
    if (strayAbove > MAX_STRAY_BLOCKS_ABOVE_NOW) {
      findings.push(
        `${strayAbove} stray \`**Last updated:**\`/\`**Prior:**\` block(s) above \`## Now\` ` +
          `(allowed ${MAX_STRAY_BLOCKS_ABOVE_NOW}). These are read as the file head every invocation. ` +
          'Convert each to a discrete `### YYYY-MM-DD — title (commit)` entry under `## Changelog` and remove them.',
      );
    }

    // 2. `## Now` wave-bullet pile-up
    const nowEnd = changelogIdx > nowIdx ? changelogIdx : lines.length;
    const nowWaveBullets = lines.slice(nowIdx, nowEnd).filter((l) => /^-\s+\*\*(Latest wave|Prior wave):\*\*/.test(l)).length;
    if (nowWaveBullets > MAX_NOW_WAVE_BULLETS) {
      findings.push(
        `\`## Now\` carries ${nowWaveBullets} \`Latest wave\`/\`Prior wave\` bullets ` +
          `(soft ceiling ${MAX_NOW_WAVE_BULLETS}). \`## Now\` is the compact current state — ` +
          'move older wave one-liners into `## Changelog` discrete entries; keep only the latest handful.',
      );
    }
  }

  if (findings.length === 0) {
    console.log('status-budget: OK — `## Now` is compact, no stray blocks above it.');
    return 0;
  }

  const tag = strict ? 'ERROR' : 'WARN';
  console.log(`status-budget: ${findings.length} ${tag}(s)${strict ? '' : ' (non-blocking)'}:`);
  for (const f of findings) console.log(`  ⚠ ${f}`);
  if (!strict) {
    console.log('status-budget: warn-only — run with --strict to enforce after the re-split. See docs/fork-gaps.md.');
    return 0;
  }
  return 1;
}

process.exit(main());
