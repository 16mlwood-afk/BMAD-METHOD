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
 * THREE MODES:
 *   1. bare                          — fork ADOPTION scan over custom/workflows/:
 *                                      a workflow that produces or consumes scope-register
 *                                      rows but never references STD-SCOPEREG-001.
 *                                      (Same shape as check:completion / check:digest.)
 *   2. --register <path>             — lint the ROWS of a project's scope register.
 *   3. --register <path> --audit     — the INERT-SCOPE SWEEP (STD-SCOPEREG-001 §9):
 *                                      accepted-with-no-next_artifact, parked-with-no-trigger,
 *                                      and next_artifact paths that don't exist on disk.
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

const ROOT = path.resolve(__dirname, '..');
const WF_DIR = path.join(ROOT, 'custom', 'workflows');

const argv = process.argv.slice(2);
const STRICT = argv.includes('--strict');
const AUDIT = argv.includes('--audit');
const regIdx = argv.indexOf('--register');
const REGISTER = regIdx === -1 ? null : argv[regIdx + 1];

const ROUTES = ['R1-capability', 'R2-bounded-local', 'R3-design', 'R4-operational-milestone', 'R5-parked'];

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

  for (const row of rows) {
    const b = row.body;
    const where = `${path.basename(file)} ${row.id}`;

    const routeM = /`?route`?\s*[:=]\s*`?(R[1-5]-[a-z-]+|TBD)`?/i.exec(b);
    const nextM = /`?next[_-]artifact`?\s*[:=]\s*([^\n|]+)/i.exec(b);
    const dispM =
      /`?disposition`?\s*[:=]?\s*`?(accepted|pending|deferred|rejected|moved)`?/i.exec(b) ||
      /\|\s*`(accepted|pending|deferred|rejected|moved)`\s*\|/i.exec(b);
    const disposition = dispM ? dispM[1].toLowerCase() : null;

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
  return { rows: rows.length };
}

// ---------------------------------------------------------------------------
// MODE 1 — fork adoption scan
// ---------------------------------------------------------------------------
function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p, out);
    else if (entry.isFile() && entry.name.endsWith('.md')) out.push(p);
  }
  return out;
}

function adoptionScan() {
  if (!fs.existsSync(WF_DIR)) {
    console.error(`check:scoperegister: workflow dir not found: ${WF_DIR}`);
    return { files: 0, adopters: 0 };
  }
  const files = walk(WF_DIR);
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
// report
// ---------------------------------------------------------------------------
const mode = REGISTER ? (AUDIT ? 'REGISTER + INERT-SCOPE AUDIT' : 'REGISTER LINT') : 'FORK ADOPTION SCAN';
let summary;
if (REGISTER) summary = lintRegister(REGISTER);
else summary = adoptionScan();

const fails = findings.filter((f) => f.sev === 'fail');
const warns = findings.filter((f) => f.sev === 'warn');

console.log(
  `\ncheck:scoperegister (${mode} · ${STRICT ? 'STRICT — exit 1 on a finding' : 'WARN-ONLY — exit 0'}): ` +
    (REGISTER ? `${summary.rows} row(s) parsed` : `${summary.files} workflow files · ${summary.adopters} adopter(s)`) +
    ` · ${fails.length} inert/invalid · ${warns.length} warning(s).`,
);

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
