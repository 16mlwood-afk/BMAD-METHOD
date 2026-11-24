/**
 * test-design-sendback-check.js — regression suite for tools/check-design-sendback.js
 *
 * The checker backs the design-implement DEPARTURE / SENDBACK contract (step-04 §5c), which exists
 * because of the 2026-09-26 owner ruling: "claude design is the source of truth for design never do
 * this again ... make this kind of SENDBACK formal".
 *
 * BOTH directions are pinned, and the SILENCE direction is the larger half. A checker that has only
 * ever been seen to fire is a checker nobody has proven is quiet — and this one scans prose, where a
 * false fire lands on a sentence a human wrote deliberately.
 *
 * THE THREE HEADLINE ROWS ARE THE REAL DEPARTURES that produced the ruling, lifted from the two
 * mapping-queue cockpit apply ledgers (inbound-flow, 2026-09-25 and 2026-09-26). Each must land as
 * a finding, because each shipped as a settled decision:
 *   G1  uppercase section labels dropped for a policy hard failure   -> D2 + D1
 *   G2  a detector table column dropped for a missing field          -> D1
 *   G3  a candidate-score treatment kept over the design's           -> D2 + D1
 * And the fourth, which must stay SILENT because it is the over-firing failure:
 *   G4  four design items honestly held back as NOT YET BUILT        -> silence
 *
 * Fixtures are inline rather than committed: they are small, and what is under test is the
 * RELATIONSHIP between a departure and its return leg, which reads better as contrasting ledgers
 * than as files on disk drifting away from the prose.
 *
 * Run: node test/test-design-sendback-check.js   (wired as `npm run test:design-sendback`)
 */

'use strict';
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const { checkLedger, checkSendback, stripQuoted, asksIn } = require('../tools/check-design-sendback.js');

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'design-sendback-check-'));

let pass = 0;
const failures = [];

function it(name, fn) {
  try {
    fn();
    pass += 1;
  } catch (error) {
    failures.push(`${name}\n      ${error.message}`);
  }
}

function write(name, body) {
  const p = path.join(TMP, name);
  fs.writeFileSync(p, body, 'utf8');
  return p;
}

const codes = (findings) => findings.filter((f) => f.severity === 'hard').map((f) => f.code);
const has = (findings, code) => codes(findings).includes(code);

/* ───────────────────────── a well-formed sendback ───────────────────────── */

function goodSendback({ departures = 1, asks = 1 } = {}) {
  return `---
type: design-sendback
target_slug: mapping-queue-cockpit
route: /mapping-queue
responds_to: "design-source-mapping-queue-cockpit-v15/Mapping Queue Cockpit.dc.html"
ledger: _bmad-output/implementation-artifacts/design-implement-mapping-queue-cockpit-pass2.md
verdict_record: n/a — no halt
brief: design-brief-mapping-queue-2026-07-10-v8.md (brief_status: active)
baseline_commit: abc1234
date: 2026-09-26
departures: ${departures}
asks: ${asks}
owner_questions: 1
---

# Sendback — Mapping Queue Cockpit v16

Two passes shipped. Read this as ${asks} ask and one question; sections 1 and 6 exist so no part of
v16 is spent re-deciding settled material.

## 1. What the design got right, and v16 keeps

The prepared-question card, the three queue groups by who has to act, and the decisive-section
prefix are all kept unchanged.

## 2. Why it did not fully ship

Twelve section labels are set \`text-transform: uppercase\` in the design. The shipped surface
renders them sentence case with no transform, so a reader comparing the two sees a different
label treatment throughout.

## 3. Why it happened, and where the gap was OURS

The brief quoted the policy's type rules but not §4's label-case prohibition or §5's hard-failure
list, so the design could not have known. That is a gap in what we handed over.

## 4. The asks

### Ask 1 — give the decisive sections a weight signal that is not capitals

What must be true: a scanning operator can tell a decisive section from supporting evidence at a
glance. Two shapes that would work, and the choice is yours: a weight/size step on the label, or a
rule-and-indent treatment on the section. If you see a third shape, take it.

answers: row-lbl-01

## 5. One question, and it is the owner's

Whether anyone other than the owner works this queue. Nothing in v16 turns on the answer.

## 6. Already settled — do not spend v16 on these

The tinted status fill is retired and stays retired; the primary commit stays in the centre.

## 7. Not for this round — for the next brief

A brief should quote the policy's prohibition list, not only its type scale. Raised separately; no
action for you.
`;
}

/* ───────────────── G1–G3: the real departures must all fire ────────────── */

it('G1 — uppercase labels dropped for a policy hard failure, recorded as a WIN: D2 + D1', () => {
  const p = write(
    'g1-ledger.md',
    `# apply ledger, pass 1

## 7. Section labels — v15 wins over the design, and it is logged

The design sets every section label uppercase at 11px. docs/design-policy.md §4 forbids it and §5
lists it as a hard failure, so the transform is dropped.

| Component | State | Property | Delta | Disposition |
|---|---|---|---|---|
| SectionLabel | default | text-transform | uppercase -> none | ⊘ departure(policy: §4 label case) |
`,
  );
  const f = checkLedger(p);
  assert.ok(has(f, 'D2-VERDICT-VERB'), `expected D2 on "v15 wins over the design", got [${codes(f)}]`);
  assert.ok(has(f, 'D1-DEPARTURE-NO-SENDBACK'), `expected D1 on the unreferenced row, got [${codes(f)}]`);
});

it('G2 — a table column dropped for a missing field, reason given, no sendback: D1', () => {
  const p = write(
    'g2-ledger.md',
    `# apply ledger, pass 2

The design's detector card carries three columns: detector name, what it read, and count. The
middle column does not exist in the data — PackDetection.detections carries { method, quantity }
and nothing else — so the table renders two columns and states the absence beneath itself.

| Component | State | Property | Delta | Disposition |
|---|---|---|---|---|
| DetectorTable | default | columns | 3 -> 2 | ⊘ departure(no field records the span) |
`,
  );
  const f = checkLedger(p);
  assert.ok(has(f, 'D1-DEPARTURE-NO-SENDBACK'), `expected D1, got [${codes(f)}]`);
  assert.ok(!has(f, 'D2-VERDICT-VERB'), 'G2 wrote no verdict verb — D2 must stay quiet here');
});

it('G3 — a score treatment kept because "the implementation beats the design": D2 + D1', () => {
  const p = write(
    'g3-ledger.md',
    `# apply ledger, pass 1

| Claim | Verdict | Where |
|---|---|---|
| A zero confidence score must never read as a real score | held, and the implementation beats the design | CandidateRow renders \`auto\` for a machine-found candidate. The design renders \`score not ranked\` in the same column as \`score 0.91\`. Keeping ours |

| Component | State | Property | Delta | Disposition |
|---|---|---|---|---|
| CandidateRow | default | score cell | design treatment -> ours | ⊘ departure(ours judged clearer) |
`,
  );
  const f = checkLedger(p);
  assert.ok(has(f, 'D2-VERDICT-VERB'), `expected D2 on "beats the design"/"keeping ours", got [${codes(f)}]`);
  assert.ok(has(f, 'D1-DEPARTURE-NO-SENDBACK'), `expected D1, got [${codes(f)}]`);
});

/* ───────── G4: the over-firing direction — honest deferrals stay silent ──── */

it('G4 — four design items held back as NOT YET BUILT: SILENT (the over-firing failure)', () => {
  const p = write(
    'g4-ledger.md',
    `# apply ledger, pass 2

## 7. What is NOT built, and why — nothing shipped on a guess

**The header.** Still production's multi-operator capability; the design hardcodes one operator
and assumes the answer to an open owner question. Untouched.

**The undo panel.** Needs undoAvailability computed server-side from six refusal conditions; five
never reach the cockpit.

**Proposal reasoning.** Left out — nothing persists why automation proposed a sell ASIN.

**The reads column** on the detector table. No field records it.

| Component | State | Property | Delta | Disposition |
|---|---|---|---|---|
| Header | default | operator | MISSING | ⊘ deferred(out-of-scope: owner question open) |
| UndoPanel | default | availability | MISSING | ⊘ deferred(needs-data: undoAvailability) |
| ProposalReasoning | default | row | MISSING | ⊘ deferred(judgment: requirement unratified) |
`,
  );
  const f = checkLedger(p);
  assert.deepStrictEqual(codes(f), [], `an honest deferral owes nothing — expected silence, got [${codes(f)}]`);
});

/* ───────────────── the compliant shape: silence both modes ─────────────── */

it('a departure carrying a resolvable sendback + ask is silent', () => {
  write('SENDBACK-mapping-queue-cockpit-v16.md', goodSendback({ departures: 1, asks: 1 }));
  const p = write(
    'compliant-ledger.md',
    `# apply ledger, pass 2

| Component | State | Property | Delta | Disposition |
|---|---|---|---|---|
| SectionLabel | default | text-transform | uppercase -> none | ⊘ interim(policy-conflict: §4 label case vs design) → sendback:SENDBACK-mapping-queue-cockpit-v16.md#ask-1 |
`,
  );
  const f = checkLedger(p);
  assert.deepStrictEqual(codes(f), [], `expected silence, got [${codes(f)}]`);
});

it('a well-formed sendback passes --sendback with no hard findings', () => {
  const p = write('SENDBACK-good.md', goodSendback());
  const f = checkSendback(p);
  assert.deepStrictEqual(codes(f), [], `expected silence, got [${codes(f)}]`);
});

/* ─────────────────────── quoting must not fire D2 ──────────────────────── */

it('a fenced or quoted banned phrase stays silent — an artefact may document the rule', () => {
  const p = write(
    'discusses-the-rule.md',
    `# apply ledger

The workflow forbids a verdict verb. From workflow.md:

> Never write \`policy wins\`, \`v15 wins\`, or \`keeping ours\` as a disposition.

\`\`\`
| SectionLabel | default | x | y | policy wins over the design |
\`\`\`

Nothing in this pass departed from the design.
`,
  );
  const f = checkLedger(p);
  assert.deepStrictEqual(codes(f), [], `quoted/fenced material must be stripped, got [${codes(f)}]`);
});

it('ordinary sentences containing "wins"/"better"/"beats" stay silent', () => {
  const p = write(
    'ordinary-prose.md',
    `# apply ledger

The narrower selector wins the specificity tie-break, which is why the token resolves.
This pass beats the previous one on coverage and gives a better contrast ratio.
Nothing was kept over the design.
`,
  );
  const f = checkLedger(p);
  assert.deepStrictEqual(codes(f), [], `bare wins/beats/better are ordinary English, got [${codes(f)}]`);
});

/* ───────────────── the remaining reference-integrity codes ─────────────── */

it('D3 — a cited sendback that does not exist', () => {
  const p = write('d3-ledger.md', '| X | d | p | delta | ⊘ departure(x) → sendback:SENDBACK-does-not-exist.md#ask-1 |\n');
  assert.ok(has(checkLedger(p), 'D3-SENDBACK-MISSING'));
});

it('D4 — a cited #ask-N that the sendback does not carry', () => {
  write('SENDBACK-d4.md', goodSendback({ departures: 1, asks: 1 }));
  const p = write('d4-ledger.md', '| X | d | p | delta | ⊘ departure(x) → sendback:SENDBACK-d4.md#ask-9 |\n');
  assert.ok(has(checkLedger(p), 'D4-ASK-UNRESOLVED'));
});

it('D5 — the sendback answers for fewer rows than the ledger raised', () => {
  write('SENDBACK-d5.md', goodSendback({ departures: 1, asks: 1 }));
  const p = write(
    'd5-ledger.md',
    `| A | d | p | delta | ⊘ departure(a) → sendback:SENDBACK-d5.md#ask-1 |
| B | d | p | delta | ⊘ departure(b) → sendback:SENDBACK-d5.md#ask-1 |
`,
  );
  assert.ok(has(checkLedger(p), 'D5-COUNT-MISMATCH'), 'two citing rows against `departures: 1` must fire');
});

/* ───────────────────── sendback structural findings ────────────────────── */

it('S1 — a missing section fires, and the empty case is a legal body', () => {
  const missing = goodSendback().replace(/## 6\. Already settled[\s\S]*?(?=## 7\.)/, '');
  const p = write('SENDBACK-s1.md', missing);
  assert.ok(has(checkSendback(p), 'S1-MISSING-SECTION'));

  const emptyStated = goodSendback().replace(
    /## 6\. Already settled — do not spend v16 on these\n\n[\s\S]*?(?=\n## 7\.)/,
    '## 6. Already settled — do not spend v16 on these\n\nNone — this is the first round on this surface.\n',
  );
  const q = write('SENDBACK-s1b.md', emptyStated);
  assert.ok(!has(checkSendback(q), 'S1-MISSING-SECTION'), '"None — …" is the correct empty form and must pass');
  assert.ok(!has(checkSendback(q), 'S6-EMPTY-SECTION'));
});

it('S2 — sections out of order', () => {
  const body = goodSendback();
  const s5 = body.match(/## 5\.[\s\S]*?(?=## 6\.)/)[0];
  const s6 = body.match(/## 6\.[\s\S]*?(?=## 7\.)/)[0];
  const p = write('SENDBACK-s2.md', body.replace(s5 + s6, s6 + s5));
  assert.ok(has(checkSendback(p), 'S2-SECTION-ORDER'));
});

it('S4 — a missing frontmatter key, and a wrong type', () => {
  const p = write('SENDBACK-s4.md', goodSendback().replace(/^baseline_commit: .*$/m, ''));
  assert.ok(has(checkSendback(p), 'S4-FRONTMATTER-MISSING'));
  const q = write('SENDBACK-s4b.md', goodSendback().replace('type: design-sendback', 'type: design-brief'));
  assert.ok(has(checkSendback(q), 'S4-FRONTMATTER-MISSING'));
});

it('S5 — frontmatter asks count disagrees with §4', () => {
  const p = write('SENDBACK-s5.md', goodSendback({ departures: 1, asks: 3 }));
  assert.ok(has(checkSendback(p), 'S5-ASKS-COUNT-MISMATCH'), 'declared 3 asks, §4 carries 1');
});

it('S3 — an ask with no second shape is a PROXY finding, never a hard one', () => {
  const single = goodSendback().replace(
    /What must be true:[\s\S]*?If you see a third shape, take it\./,
    'What must be true: the label uses a weight step of 600 and nothing else.',
  );
  const p = write('SENDBACK-s3.md', single);
  const f = checkSendback(p);
  assert.ok(
    f.some((x) => x.code === 'S3-ASK-SINGLE-SHAPE' && x.severity === 'proxy'),
    'expected S3 at proxy severity',
  );
  assert.ok(!has(f, 'S3-ASK-SINGLE-SHAPE'), 'S3 must never be a hard finding — it is a keyword scan');
});

/* ──────────────────────────── unit helpers ─────────────────────────────── */

it('stripQuoted removes fences and blockquotes and preserves line numbering', () => {
  const out = stripQuoted('a\n```\nb\n```\n> c\nd');
  assert.strictEqual(out.split('\n').length, 6, 'line count must be preserved so findings cite real lines');
  assert.ok(!out.includes('b') && !out.includes('c'));
  assert.ok(out.includes('a') && out.includes('d'));
});

it('asksIn recognises the three ask shapes', () => {
  assert.deepStrictEqual(asksIn('### Ask 1 — draw the empty state\n\n**Ask 2** — draw unreadable\n\n3. give it a home\n'), [1, 2, 3]);
});

/* ──────────────────────────────── report ──────────────────────────────── */

fs.rmSync(TMP, { recursive: true, force: true });

if (failures.length > 0) {
  process.stdout.write(`\n✗ design-sendback checker: ${pass} passed, ${failures.length} FAILED\n\n`);
  for (const f of failures) process.stdout.write(`  ✗ ${f}\n\n`);
  process.exit(1);
}
process.stdout.write(
  `✓ design-sendback checker: ${pass} cases passed (the 3 real mapping-queue departures fire; the 4 honest deferrals stay silent)\n`,
);
