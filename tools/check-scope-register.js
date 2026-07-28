/**
 * check-scope-register.js  —  WARN-ONLY at v1 (NOT armed in the gate)
 *
 * Checker for STD-SCOPEREG-001 (custom/workflows/shared/scope-register-routing.md).
 *
 * The standard says a scope-register ROW must declare a `route` (closed enum), a
 * route-appropriate `next_artifact`, and — for `R5-parked` only — a complete
 * `activation` (owner + trigger + why-not-now). A row missing those is
 * REGISTERED-BUT-INERT: agreed, recorded, owned by nobody, consumed by nothing.
 *
 * Unlike STD-SCOPEROUTE-001 (which governs a prose ANSWER and is therefore honestly
 * probabilistic), this standard governs a FILE — so a deterministic tier exists and
 * is taken here.
 *
 * What is and ISN'T deterministically checkable (per the enforcement-expert
 * DETERMINISTIC vs PROBABILISTIC axis):
 *   - CHECKED: does the row declare a route from the enum? does an `accepted` row
 *     carry a next_artifact? is that next_artifact route-appropriate in SHAPE?
 *     does a parked row carry all three activation parts? does a promised
 *     next_artifact path actually exist on disk?
 *   - NOT CHECKED, on purpose: whether the declared route is the CORRECT one. A
 *     linter can prove a row says `R2-bounded-local` and points at a quick-spec; it
 *     cannot prove the item was not really `R1-capability`. That axis is ceded to
 *     the golden eval (evals/scope-register-routing.md) — measured, not gated.
 *     Faking that check would be the indiscriminate-detector anti-pattern.
 *
 * FOUR MODES:
 *   1. bare                          — fork ADOPTION scan over custom/workflows/:
 *                                      a workflow that produces or consumes scope-register
 *                                      rows but never references STD-SCOPEREG-001.
 *                                      (Same shape as check:completion / check:digest.)
 *   2. --register <path>             — lint the ROWS of a project's scope register.
 *   3. --register <path> --audit     — the INERT-SCOPE SWEEP (STD-SCOPEREG-001 §9):
 *                                      accepted-with-no-next_artifact, parked-with-no-trigger,
 *                                      next_artifact paths that don't exist on disk, AND the
 *                                      reverse signature — DELIVERED-BUT-PENDING: a row still
 *                                      `pending` whose artifact ALREADY exists. That one is
 *                                      report-only by design; the owner closes the row, never
 *                                      this tool (§9 keeps the disposition flip human).
 *   4. --register <path> --new-row   — AUTHORING: emit a correctly-columned skeleton for BOTH
 *                                      paired tables, derived from the live header, plus the
 *                                      next free SR id. The standard mandates an append from
 *                                      every shaping session and shipped no writable affordance;
 *                                      this is it. Prints, never writes.
 *
 * `--strict` makes a finding exit 1. NOT armed in `npm test` or the pre-commit
 * fast-path at v1: the row-shape heuristic is unproven against hand-maintained
 * registers written before this standard existed, and a linter that false-blocks a
 * commit on a legacy row is exactly what gets gates ripped out. Promotion requires
 * the fork scan quiet AND >=1 project register passing clean after backfill.
 *
 * Run: `npm run check:scoperegister`
 *      `npm run check:scoperegister -- --register ../cash-recovery/_bmad-output/planning-artifacts/scope-register.md --audit`
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');

// Corpus comes from the shared helper — do NOT hard-code a root here.
// See tools/lib/standards-corpus.js (fork-gaps 2026-07-25, archived RESOLVED).
const { collectStandardsCorpus, ROOT } = require('./lib/standards-corpus');

const argv = process.argv.slice(2);
const STRICT = argv.includes('--strict');
const AUDIT = argv.includes('--audit');
const NEW_ROW = argv.includes('--new-row');
const regIdx = argv.indexOf('--register');
const REGISTER = regIdx === -1 ? null : argv[regIdx + 1];

if (NEW_ROW && !REGISTER) {
  console.error('check:scoperegister --new-row requires --register <path>.');
  process.exit(1);
}

const ROUTES = ['R1-capability', 'R2-bounded-local', 'R3-design', 'R4-operational-milestone', 'R5-parked'];

/**
 * WHY-NOT-NOW — the closed set of reasons an accepted row may sit unbuilt.
 *
 * THE FAILURE THIS EXISTS FOR (2026-07-28, cash-recovery SR-49/SR-50). A session diagnosed
 * two small changes — attach an identity already in memory, expose a boolean already
 * computed, select a column that already existed — wrote "nobody is doing it / ready to be
 * picked up", registered both rows, and stopped. Nothing blocked either one. The owner had
 * to ask three times before the work happened, and it then took a single pass.
 *
 * A row registered because it is BLOCKED and a row registered because it was AVOIDED were
 * byte-identical in the file: both had a route, a next_artifact, and an owner. Only
 * `R5-parked` was ever required to say why-not-now. So the register — whose whole job is
 * that work does not get lost — became a place to put work instead of doing it, and nothing
 * could tell the difference.
 *
 * `NOT-BLOCKED` is deliberately IN the enum and deliberately FAILS. The point is that there
 * is no silent option: either you name a real blocker, or you write down that there isn't
 * one — and writing that down is the moment you notice you should just do it.
 */
const WHY_NOT_NOW = {
  'owner-decision': 'needs a ruling only the owner can give',
  'blocked-by-data': 'the data/source does not exist yet',
  'blocked-by-artifact': 'an upstream artifact or workflow must land first',
  'other-session': "another session's surface or an active claim",
  'too-large-for-now': 'a genuine multi-pass build, not a same-session change',
  'NOT-BLOCKED': 'nothing prevents it — this should have been DONE, not registered',
};

// Shape expectations per route (STD-SCOPEREG-001 §3). Deliberately SHAPE-only —
// this asks "does the named artifact look like the kind this route requires",
// never "is this the right route".
const ROUTE_ARTIFACT_SHAPE = {
  'R1-capability': {
    // The FIRST STORY FILE — not the epic, not the epic's story list. Story files are
    // conventionally named `<epic>-<n>-<slug>` (e.g. `9-1-unified-single-touch-shell`),
    // so accept that shape as well as a literal "story". Rejecting it would false-fire on
    // every correctly-routed R1 row — a noisy detector is worse than none.
    ok: (s) => (/\b\d+-\d+-[a-z0-9-]+/i.test(s) || /stor(y|ies)/i.test(s)) && !/^\s*epic[\s-]*\d*\s*$/i.test(s),
    want: 'the first STORY FILE path at ready-for-dev, e.g. `<epic>-<n>-<slug>.md` (an epic name does NOT satisfy R1 — see §4)',
  },
  'R2-bounded-local': {
    ok: (s) => /quick-spec|tech-spec/i.test(s),
    want: 'the quick-spec / tech-spec file path',
  },
  'R3-design': {
    ok: (s) => /brief/i.test(s),
    want: 'the ACTIVE design brief path (produced by design-handoff; a hand-edit is invalid by construction)',
  },
  'R4-operational-milestone': {
    ok: (s) => /sprint-status|milestone/i.test(s),
    want: 'the milestone-block key, e.g. sprint-status.yaml#<milestone-key>',
  },
  'R5-parked': {
    ok: () => true, // `—` is legal here and ONLY here; activation carries the obligation
    want: 'nothing (— is legal); the obligation is carried by `activation`',
  },
};

const findings = [];
const note = (sev, where, msg) => findings.push({ sev, where, msg });

// ---------------------------------------------------------------------------
// on-disk probes — shared, so "does the artifact exist" has exactly ONE answer
// ---------------------------------------------------------------------------

/** Resolve a path-ish artifact reference near the register. Returns the path, or null. */
function resolveNear(regDir, ref) {
  for (const form of [ref, `${ref}.md`]) {
    for (const base of [regDir, path.resolve(regDir, '..'), path.resolve(regDir, '../..')]) {
      const p = path.resolve(base, form);
      if (fs.existsSync(p)) return p;
    }
  }
  return null;
}

const SKIP_DIRS = new Set(['node_modules', '.git', '.next', 'dist', 'build', '.claude', 'coverage']);

/**
 * A story id (`2-14`, `Story 2-14`) is NOT a path, and the register cites them bare all
 * the time — SR-07 literally predicted "new Story 2-14 (on apply)". Walk a bounded slice
 * of the project for a file whose NAME starts with that id. Depth-capped and
 * directory-filtered: this is a hand-run audit, not a hot path.
 */
function findByStoryId(regDir, id, depth = 5) {
  const root = path.resolve(regDir, '../..');
  const wanted = new RegExp(`^${id.replaceAll('.', String.raw`\.`)}[-.]`);
  const walk = (dir, left) => {
    if (left < 0) return null;
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return null;
    }
    for (const e of entries) {
      if (e.isFile() && wanted.test(e.name)) return path.join(dir, e.name);
    }
    for (const e of entries) {
      if (e.isDirectory() && !SKIP_DIRS.has(e.name) && !e.name.startsWith('.')) {
        const hit = walk(path.join(dir, e.name), left - 1);
        if (hit) return hit;
      }
    }
    return null;
  };
  return walk(root, depth);
}

// ---------------------------------------------------------------------------
// MODE 2/3 — lint a project's scope register
// ---------------------------------------------------------------------------
function lintRegister(file) {
  if (!fs.existsSync(file)) {
    console.error(`check:scoperegister: register not found: ${file}`);
    process.exit(0); // warn-only: a missing register is not this tool's failure to declare
  }
  const text = fs.readFileSync(file, 'utf8');
  const regDir = path.dirname(path.resolve(file));

  // A row's information is legitimately spread across MORE THAN ONE place: a markdown
  // table line (`| SR-NN | ... |`), a narrative block (`**SR-NN — ...`), and/or a
  // routing-index line. Merge every fragment carrying the same id into ONE body before
  // checking — otherwise a routed row still fails on its unrouted table fragment, which
  // is a false positive on correct work (the anti-pattern that gets gates ripped out).
  const byId = new Map();
  const add = (id, frag) => byId.set(id, (byId.get(id) || '') + '\n' + frag);

  for (const line of text.split('\n')) {
    const m = /^\|\s*`?(SR-\d+)`?\s*\|(.*)$/.exec(line);
    if (m) add(m[1], line);
  }
  // Narrative blocks: from an `**SR-NN` heading to the next SR heading / H2.
  for (const block of text.split(/\n(?=\*\*`?SR-\d+|## )/)) {
    const m = /^\*\*`?(SR-\d+)\b/.exec(block);
    if (m) add(m[1], block);
  }

  const rows = [...byId.entries()].map(([id, body]) => ({ id, body })).sort((a, b) => Number(a.id.slice(3)) - Number(b.id.slice(3)));

  if (rows.length === 0) {
    console.log(`check:scoperegister: no SR-* rows parsed in ${file} — nothing to check.`);
    return { rows: 0 };
  }

  const missingWhy = [];

  for (const row of rows) {
    const b = row.body;
    const where = `${path.basename(file)} ${row.id}`;

    const routeM = /`?route`?\s*[:=]\s*`?(R[1-5]-[a-z-]+|TBD)`?/i.exec(b);
    const nextM = /`?next[_-]artifact`?\s*[:=]\s*([^\n|]+)/i.exec(b);
    const dispM =
      /`?disposition`?\s*[:=]?\s*`?(accepted|pending|deferred|rejected|moved)`?/i.exec(b) ||
      /\|\s*`(accepted|pending|deferred|rejected|moved)`\s*\|/i.exec(b);
    const disposition = dispM ? dispM[1].toLowerCase() : null;

    // -- AUDIT: DELIVERED-BUT-PENDING (STD-SCOPEREG-001 §9) -----------------
    // Rows move ONTO `pending` automatically (a workflow appends them) and move OFF it
    // only by a human remembering — a one-way ratchet, so delivered-but-unclosed rows
    // accumulate and are indistinguishable BY INSPECTION from real open decisions. The
    // owner then reads N blockers on their desk that are actually one. (2026-07-25:
    // three of four `route: TBD` rows surfaced as "waiting on Mason" were waiting on
    // nobody — SR-07/2-14, SR-08/2-15, SR-12/the resolved shell decision.)
    //
    // Cheapest signature: still `pending` while the thing it was waiting for EXISTS.
    // Runs BEFORE the route checks on purpose — all three exemplars were `route: TBD`,
    // which the route branch below legitimately `continue`s past.
    //
    // DETECTION ONLY. Never flip a disposition here: owner-only off `pending` is the
    // audit anchor and is deliberate (§9). The gap is detection, not authority.
    // `pending` ONLY — an UNPARSED disposition is not a pending one. Treating null as
    // pending fired on 11 extra rows in the first cut of this detector, every one of them
    // an already-`accepted`/`absorbed` row whose disposition the row-shape heuristic simply
    // did not read. Same discipline as AD-24g: no signal is not a story, and a detector
    // that manufactures 11 false blockers to catch 3 real ones costs exactly the attention
    // it was built to save.
    if (AUDIT && disposition === 'pending') {
      const nextForProbe = nextM ? nextM[1].trim().replaceAll(/^[`*\s]+|[`*\s]+$/g, '') : '';
      const pathish = /([\w./-]+\.(?:md|ya?ml))/.exec(nextForProbe);
      let found = pathish ? resolveNear(regDir, pathish[1]) : null;
      let via = found ? `next_artifact "${pathish[1]}"` : null;

      // No path-ish next_artifact? The row may still NAME its answer in prose — a story
      // id, which is how SR-07 recorded the story that closed it four weeks earlier.
      if (!found) {
        const idM = /\bstor(?:y|ies)\s+`?(\d+[-.]\d+)/i.exec(b) || /\b(\d+-\d+)-[a-z0-9-]{3,}/i.exec(nextForProbe);
        if (idM) {
          const hit = findByStoryId(regDir, idM[1].replace('.', '-'));
          if (hit) {
            found = hit;
            via = `story ${idM[1]} → ${path.basename(hit)}`;
          }
        }
      }

      if (found) {
        note(
          'stale',
          where,
          `DELIVERED-BUT-PENDING: still \`pending\`, but its ${via} EXISTS on disk. ` +
            'Either the row was delivered and nobody closed it, or the artifact is a coincidence — READ it before touching the row. ' +
            "A stale `pending` row is indistinguishable from a real open decision, and it spends the owner's attention (§9).",
        );
      }
    }

    // -- route presence -----------------------------------------------------
    if (!routeM) {
      if (disposition === 'pending') {
        note(
          'warn',
          where,
          'pending row with no `route` — legal only until dispositioned; set `route: TBD` + the decision that unblocks it (§2).',
        );
      } else {
        note(
          'fail',
          where,
          `no \`route\` field. STD-SCOPEREG-001 §2 requires one of: ${ROUTES.join(' | ')} (or TBD on a pending row). This row is REGISTERED-BUT-INERT.`,
        );
      }
      continue;
    }
    const route = routeM[1];
    if (route.toUpperCase() === 'TBD') {
      if (disposition && disposition !== 'pending') {
        note('fail', where, `\`route: TBD\` on a \`${disposition}\` row — TBD expires when the owner dispositions the row (§2).`);
      }
      continue;
    }
    if (!ROUTES.includes(route)) {
      note('fail', where, `\`route: ${route}\` is not in the closed enum: ${ROUTES.join(' | ')}.`);
      continue;
    }

    // -- R5 activation ------------------------------------------------------
    // -- why_not_now: is this row registered because it is BLOCKED, or because it was
    // AVOIDED? Without this field those two are indistinguishable (see WHY_NOT_NOW).
    // Only `accepted` rows are asked: a `pending` row is BY DEFINITION awaiting a
    // decision, which is its own why-not-now.
    // `R5-parked` is EXEMPT: it already owes a three-part activation block whose why-not-now
    // is legitimately free text (§3 R5), and enforcing the enum on top of that flagged real,
    // correct rows (SR-25 on the first run). One contract per row — the enum governs the
    // rows that had NO why-not-now requirement at all.
    if (disposition === 'accepted' && route !== 'R5-parked') {
      // UNDERSCORE ONLY, deliberately. The register's PROSE already uses the hyphenated
      // phrase "why-not-now" when quoting the standard or explaining a park, and matching
      // that grabbed the next word and reported it as an invalid enum value on rows that
      // were entirely correct (SR-25, first run). `why_not_now` is the FIELD; "why-not-now"
      // is English. A detector that cannot tell them apart costs more than it catches.
      const whyM = /`?why_not_now`?\s*[:=]\s*`?([A-Za-z-]+)`?/i.exec(b);
      if (!whyM) {
        missingWhy.push(row.id);
      } else {
        const why = whyM[1];
        const key = Object.keys(WHY_NOT_NOW).find((k) => k.toLowerCase() === why.toLowerCase());
        if (!key) {
          note('fail', where, `\`why_not_now: ${why}\` is not in the closed enum: ${Object.keys(WHY_NOT_NOW).join(' | ')}. Free text here re-opens the hole the field closes.`);
        } else if (key === 'NOT-BLOCKED') {
          note('fail', where, "declares `why_not_now: NOT-BLOCKED` — nothing is stopping this, so it is not registrable scope, it is UNDONE WORK with paperwork attached. Do it, or name the real blocker.");
        }
      }
    }

    if (route === 'R5-parked') {
      const missing = ['owner', 'trigger', 'why-not-now'].filter((k) => !new RegExp(`${k}\\s*[:=]\\s*\\S`, 'i').test(b));
      if (missing.length > 0) {
        note(
          'fail',
          where,
          `parked but \`activation\` incomplete — missing: ${missing.join(', ')}. A parked row owes an owner, an OBSERVABLE trigger, and a why-not-now (§3 R5); "sits in the register" is not parked.`,
        );
      }
      continue;
    }

    // -- next_artifact presence + shape -------------------------------------
    // Strip trailing markdown emphasis/backticks the field value picks up in a table cell.
    const nextRaw = nextM ? nextM[1].trim().replaceAll(/^[`*\s]+|[`*\s]+$/g, '') : '';
    const isEmpty = !nextRaw || /^[—\-–]$/.test(nextRaw);
    if (isEmpty) {
      if (disposition === 'accepted') {
        note(
          'fail',
          where,
          `\`accepted\` with no \`next_artifact\` — the exact inert state (§4). Route ${route} wants: ${ROUTE_ARTIFACT_SHAPE[route].want}.`,
        );
      } else {
        note('warn', where, `no \`next_artifact\` (disposition: ${disposition || 'unstated'}). Mandatory once accepted.`);
      }
      continue;
    }
    const shape = ROUTE_ARTIFACT_SHAPE[route];
    if (!shape.ok(nextRaw)) {
      note(
        'warn',
        where,
        `\`next_artifact\` "${nextRaw.slice(0, 70)}" does not look route-appropriate for ${route}. Expected ${shape.want}.`,
      );
    }

    // -- AUDIT: does the promised artifact actually exist? -------------------
    if (AUDIT) {
      // Accept an extensionless artifact reference (story files are routinely cited without
      // `.md`); probe both forms before declaring it missing.
      const pathish = /([\w./-]+\.(?:md|ya?ml))/.exec(nextRaw) || /([\w./-]*\/[\w.-]*\d+-\d+-[a-z0-9-]+)/i.exec(nextRaw);
      if (pathish) {
        const forms = [pathish[1], `${pathish[1]}.md`];
        const candidates = forms.flatMap((f) => [path.resolve(regDir, f), path.resolve(regDir, '..', f), path.resolve(regDir, '../..', f)]);
        if (!candidates.some((c) => fs.existsSync(c))) {
          note(
            'fail',
            where,
            `PROMISED-NOT-PRODUCED: \`next_artifact\` names "${pathish[1]}" but no such file exists near the register. The row is routed but still inert.`,
          );
        }
      } else if (route !== 'R4-operational-milestone') {
        note('warn', where, `\`next_artifact\` "${nextRaw.slice(0, 60)}" names no checkable path — cannot verify it was produced.`);
      }
    }
  }
  // ONE aggregate line, never one per row. ~50 legacy rows predate this field, and 50
  // individual warnings would bury the two findings that matter — the indiscriminate-detector
  // anti-pattern that gets a checker switched off. New rows get the field from `--new-row`.
  if (missingWhy.length) {
    note(
      'warn',
      path.basename(file),
      `${missingWhy.length} accepted row(s) carry no \`why_not_now\` — cannot tell registered-because-BLOCKED from registered-because-AVOIDED: ${missingWhy.join(', ')}. Legacy rows are grandfathered; add it when you next touch one.`,
    );
  }

  return { rows: rows.length };
}

// ---------------------------------------------------------------------------
// MODE 1 — fork adoption scan
// ---------------------------------------------------------------------------
function adoptionScan() {
  // Corpus comes from the shared helper — see tools/lib/standards-corpus.js. Its
  // MANDATE applies to this scanner too: never hard-code a root. (The primary
  // producer, bmad-correct-course, lives under custom/skills/, so a workflows-only
  // walk would be blind to the one file that matters most.)
  const { files, roots } = collectStandardsCorpus();
  if (roots.length === 0) {
    console.error('check:scoperegister: no corpus roots found');
    return { files: 0, adopters: 0 };
  }
  const TOUCHES_SCOPE = /scope-register|scope_register|scope-lineage/i;
  const ADOPTS = /scope-register-routing\.md|STD-SCOPEREG-001/;
  let adopters = 0;

  for (const file of files) {
    const base = path.basename(file);
    if (base === 'scope-register-routing.md' || base === 'STANDARDS.md') {
      adopters++;
      continue;
    }
    const text = fs.readFileSync(file, 'utf8');
    if (!TOUCHES_SCOPE.test(text)) continue;
    if (ADOPTS.test(text)) {
      adopters++;
      continue;
    }
    note(
      'warn',
      path.relative(ROOT, file),
      'writes/consumes scope-register rows but does not reference STD-SCOPEREG-001 — its rows can be produced with no route (§6).',
    );
  }
  return { files: files.length, adopters };
}

// ---------------------------------------------------------------------------
// MODE 4 — --new-row: emit a correctly-columned skeleton from the LIVE header
// ---------------------------------------------------------------------------
// The standard MANDATES an append from any shaping session, and shipped no writable
// affordance: two tables that must be filled in lockstep (nothing says so), rows
// 400–2000 chars wide, the header ~70 lines above the rows it describes, and a
// validator that only tells you the row is wrong AFTER you hand-built it. The cost
// lands on a cold session at the END of other work — the exact moment it decides
// "naming the lane was enough" and leaves inert scope behind (fork-gaps FG-2026-07-25-08).
//
// Derived from the live header, never a hard-coded column list: a register that grows
// a column gets a correct skeleton on the next run, with no edit here.
function newRow(file) {
  if (!fs.existsSync(file)) {
    console.error(`check:scoperegister --new-row: register not found: ${file}`);
    process.exit(1);
  }
  const lines = fs.readFileSync(file, 'utf8').split('\n');

  // A header line is a `|`-row whose NEXT line is the `|---|---|` separator.
  const headers = [];
  for (let i = 0; i < lines.length - 1; i++) {
    if (/^\s*\|/.test(lines[i]) && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
      const cols = lines[i]
        .split('|')
        .slice(1, -1)
        .map((c) => c.trim().replaceAll(/[`*]/g, ''));
      if (cols.some((c) => /^id$/i.test(c))) headers.push({ line: i + 1, cols });
    }
  }
  if (headers.length === 0) {
    console.error('check:scoperegister --new-row: no `| id | … |` table header found. Is this a scope register?');
    process.exit(1);
  }

  // Next free id, so the two tables cannot disagree about which row you are adding.
  const ids = [...fs.readFileSync(file, 'utf8').matchAll(/\bSR-(\d+)\b/g)].map((m) => Number(m[1]));
  const nextId = `SR-${String(ids.length > 0 ? Math.max(...ids) + 1 : 1).padStart(2, '0')}`;

  // NO `|` inside a placeholder — a pipe in a cell silently splits the row and the
  // skeleton stops being correctly-columned, which is the one thing this mode owes.
  // Enum choices are `/`-separated for that reason.
  const PLACEHOLDER = {
    id: nextId,
    route: 'R1-capability / R2-bounded-local / R3-design / R4-operational-milestone / R5-parked / TBD',
    disposition: 'pending / accepted / deferred / rejected / moved',
    state: 'REGISTERED / PROPOSED / DESCRIBED / SHAPED',
    next_artifact: '<story file / quick-spec / ACTIVE brief / milestone key — the thing that makes it actionable>',
    why_not_now: `<${Object.keys(WHY_NOT_NOW).join(' | ')}> — if NOT-BLOCKED, do the work instead of filing this row`,
    'next artifact': '<the thing that makes it actionable>',
    owner: '<who>',
    trigger: '<OBSERVABLE condition, not "when we get to it">',
  };
  const cell = (c) => (PLACEHOLDER[c.toLowerCase()] ?? `<${c}>`).replaceAll('|', '/');

  console.log(`\ncheck:scoperegister --new-row · ${path.basename(file)} · next free id: ${nextId}\n`);
  console.log('  BOTH tables take a row. They are paired by id and nothing in the file says so —');
  console.log('  appending to one and not the other is the single most common way a row goes inert.\n');
  for (const [n, h] of headers.entries()) {
    console.log(`  ── table ${n + 1} (header at line ${h.line}, ${h.cols.length} columns) ──`);
    console.log(`  | ${h.cols.map(cell).join(' | ')} |\n`);
  }
  console.log('  Then verify what you wrote:');
  console.log(`    node tools/check-scope-register.js --register ${file} --audit\n`);
  console.log('  Rules that the skeleton cannot enforce (STD-SCOPEREG-001):');
  console.log('    • `route: TBD` is legal ONLY while `disposition: pending`, and owes the named unblocking decision (§2).');
  console.log('    • `R5-parked` owes all three activation parts — owner, OBSERVABLE trigger, why-not-now (§3).');
  console.log('    • "Recorded in the register" is REGISTERED, not done. Actionable needs the next artifact (§4).\n');
  return { rows: headers.length };
}

// ---------------------------------------------------------------------------
// report
// ---------------------------------------------------------------------------
if (NEW_ROW) {
  newRow(REGISTER);
  process.exit(0);
}

const mode = REGISTER ? (AUDIT ? 'REGISTER + INERT-SCOPE AUDIT' : 'REGISTER LINT') : 'FORK ADOPTION SCAN';
let summary;
if (REGISTER) summary = lintRegister(REGISTER);
else summary = adoptionScan();

const fails = findings.filter((f) => f.sev === 'fail');
const warns = findings.filter((f) => f.sev === 'warn');
const stales = findings.filter((f) => f.sev === 'stale');

console.log(
  `\ncheck:scoperegister (${mode} · ${STRICT ? 'STRICT — exit 1 on a finding' : 'WARN-ONLY — exit 0'}): ` +
    (REGISTER ? `${summary.rows} row(s) parsed` : `${summary.files} workflow files · ${summary.adopters} adopter(s)`) +
    ` · ${fails.length} inert/invalid · ${stales.length} delivered-but-pending · ${warns.length} warning(s).`,
);

// Printed FIRST: these are the rows most likely sitting on the owner's desk pretending
// to be open decisions. They cost attention, which is the scarcest thing here.
if (stales.length > 0) {
  console.log(`\n  ⏳ ${stales.length} DELIVERED-BUT-PENDING row(s) — still \`pending\` while the artifact they waited for exists:`);
  for (const f of stales) console.log(`      • ${f.where}: ${f.msg}`);
  console.log('      → Read each artifact, then the OWNER closes the row. This tool never flips a disposition.');
}
if (fails.length > 0) {
  console.log(`\n  ✗ ${fails.length} INERT or INVALID row(s) — registered scope with no route, no next artifact, or an incomplete park:`);
  for (const f of fails) console.log(`      • ${f.where}: ${f.msg}`);
}
if (warns.length > 0) {
  console.log(`\n  ⚠ ${warns.length} warning(s):`);
  for (const f of warns) console.log(`      • ${f.where}: ${f.msg}`);
}
if (findings.length === 0) {
  console.log('  ✓ clean — every row declares a route and names what makes it actionable.');
}
console.log(
  '\n  Route correctness is NOT checked here (a linter cannot prove R2 should have been R1) —\n' +
    '  that axis is ceded to evals/scope-register-routing.md. See shared/scope-register-routing.md §8.\n',
);

process.exit(STRICT && fails.length > 0 ? 1 : 0);
