# Humanizer bake-off — `writing:humanize-text` vs `humanize-research`

**Date:** 2026-07-24 · **Session:** claude-session-20260724-195406
**Purpose:** settle the stale ledger row *"Strip AI tells (Humanizer) → writing:humanize-text → Redundant → Do not install"*, which was decided on trigger-collision grounds and had never compared research provenance or output quality.
**Method:** three real sent emails from Mason's Gmail, each run through both routes. Evaluated on recipient-fit first, detector-fit second.

## Contenders

| | `writing:humanize-text` ("wiki route") | `humanize-research` ("research route") |
|---|---|---|
| Origin | LorcanChinnock marketplace plugin (installed, not authored) | harshaneel/humanize, MIT, commit `4ec7973` |
| Basis | Wikipedia *Signs of AI writing* field guide — 31 patterns, 362-line catalogue | 50+ peer-reviewed detection papers; 9 levers over 8 stylometric signals + RLHF fingerprint |
| Evidence | None published | 25-case benchmark, externally validated vs Binoculars |
| Adoption | 1 star | 293 stars, 32 forks |
| Mechanism | Pattern catalogue, one pass + self-check literals | Hard rules with mandatory counted pre-output gate + audit loop |

## Baseline measurement (the surprise)

Before rewriting, both skills' mechanical criteria were measured against the three originals:

| Email | Words | Sentence counts | Range ≥20 | Mid-band <half | No 3-consec-within-5 | Has ≤6 | Em dash | Semicolon | Curly |
|---|---|---|---|---|---|---|---|---|---|
| A — agent outreach (James Douglas, 24 Jul) | 112 | 20,6,20,9,35,16,6 | PASS (29) | PASS (3/7) | PASS | PASS | 0 | 0 | 0 |
| B — funder reply (Uncapped/Brade, 22 Jul) | 128 | 4,16,9,10,27,21,27,14 | PASS (23) | PASS (3/8) | PASS | PASS | 0 | **1** | 0 |
| C — accountant query (Kathlyn, 7 Jul) | 65 | 8,22,18,17 | n/a | n/a | n/a | n/a | 0 | 0 | 0 |

**Mason's unassisted email already passes the research skill's headline lever.** Burstiness (hard rule 7) is the research route's most distinctive and most-cited contribution, and it has nothing to fix on this corpus — A and B pass all four rhythm conditions outright, and C is under the skill's own ~80-word applicability threshold, so the rule does not fire. C's failing counts in the table are shown for completeness and are correctly exempt.

**Exactly one mechanical AI-tell exists across all three emails:** a single semicolon in email B.

## Per-email outcome

### A — agent outreach (broker, 112 words)

Wiki route: **no-op.** No catalogue pattern fires. Correct behaviour.

Research route: pressure to dissolve the three-item bullet list into prose ("no bullet lists unless the user requested them") and to satisfy Lever 5 by grounding the £272k claim harder. Applying it produced a longer email, cost the broker the scannable three-ask list, and — following Lever 5 literally — tempted an inference that was not in Mason's knowledge ("the estimates were generated before the work happened"). **Regression.** The bullets are the reason a busy agent answers all three questions.

### B — funder reply (Uncapped, 128 words) — the only email with real work

Original defects: `This transition is formally reflected in our updated share structure; he transferred...` — copula avoidance plus the corpus's only semicolon. Plus a hedged closer.

Wiki route rewrite:
> Bradley left the company to enter academia. Our updated share structure reflects this. He transferred his shares on June 8, 2026 and no longer holds any interest in the company.
> [...] Let me know if you need anything else to release the funds.

Fixes the copula (catalogue #8) and the stiff "as confirmation of" → "confirming". Keeps the numbered structure that mirrors Brade's own numbered asks. **Misses the semicolon** — semicolons are not in this skill's self-check literals, and PATTERNS.md does not carry a semicolon entry.

Research route rewrite:
> Bradley left to go into academia. He transferred his shares on June 8, 2026 and holds no interest in the company now. I've attached the CS01 Confirmation Statement filed at Companies House on July 21 as confirmation: Mason Wood and Harry Scardifield at 150 ordinary shares each, Bradley Smith reduced to nil.
> That should be everything you need to release the funds.

Catches the semicolon deterministically (hard rule 2) and reads more like a person. But it dissolves the numbered list a compliance reviewer uses to check both items were answered, and Lever 9 cuts the offer-to-supply-more closer — replacing it with an assertion ("that should be everything you need") that overclaims while the funds release is still pending on their side.

### C — accountant query (65 words)

Both routes: **near no-op.** Wiki changes "regarding those transfers" → "about those transfers". Research route correctly exempts the email from its rhythm rules at 65 words. No meaningful difference.

## Verdict

**Neither wins outright. Split by axis:**

- **Recipient-fit (the axis that matters for Mason's outbound email): wiki route wins.** It preserves correspondence structure — numbered replies that mirror the sender's numbered asks, scannable bullet lists for multi-part requests, and the cooperative closer that keeps a pending funding request warm. The research route treats every text as an essay; business email is not an essay, and its bullet-dissolution and closer-cutting rules are net-negative on all three samples.
- **Mechanical tell-catching: research route wins,** but on a corpus where there was almost nothing to catch. Its one real win — the semicolon — is a single rule, not a skill's worth of value.
- **Fact-safety: wiki route wins.** Lever 5 (specificity insertion) creates pressure to add grounding detail, which in business correspondence is a correctness risk, not a style improvement. The wiki skill's explicit "do not add facts or remove claims" contract is the safer default when the text is a factual reply to an accountant, funder, or agent.
- **The peer's premise was right about provenance and wrong about consequence.** The research skill genuinely is better-sourced (50+ papers vs one crowdsourced guide). That did not translate into better outbound email, because its research optimises for surviving detectors on long-form prose, and Mason's problem is short transactional correspondence a human reads once.

## Decision

- **Canonical for outbound email: `writing:humanize-text`** (wiki route). Unchanged from the previous ledger verdict, but now decided on evidence rather than trigger-collision.
- **`humanize-research` retained as optional alternate**, explicit invocation only, for long-form or public-facing prose where detector-facing signals matter. Installed under an alias with a narrowed description so it does not auto-trigger on a bare "humanize this".
- **Adopt the one rule that won:** add the semicolon to the deterministic pre-draft AI-tell scan in `~/.claude/hooks/gmail-draft-humanize-gate.py`. The gate currently scans em dashes, AI-vocab, bolded-header bullets, curly quotes and sycophantic openers, but not semicolons — and the semicolon was the only mechanical tell present in the real corpus. This captures the research route's sole demonstrated advantage as a deterministic check, with none of its format damage.

## Honest limits (part 1)

- n=3, one author, one register band (65–128 words). This settles the outbound-email question and nothing wider.
- No external detector was run. Deliberate: the ledger's use case is a human recipient, and the research skill's own README concedes rule-based rewriting cannot defeat learned classifiers.
- Rewrites were produced by applying both skills' published instructions in this session, not by A/B testing against recipients. No email was sent or drafted during this bake-off.
- **Structural limit, addressed in part 2 below:** every input was already human-written Mason prose, so this half measured **damage** (false-positive risk), not **tell removal**. It could not tell us which route actually strips AI tells, because there were almost none present to strip.

---

# Part 2 — Tell-removal test (AI-ish drafts)

**Date:** 2026-07-24 · **Session:** claude-session-20260724-195919
**Why:** part 1 tested both routes on already-human emails. That is the false-positive half. This half supplies the missing one: take the same briefs, write deliberately LLM-styled drafts of them, and measure which route actually removes the tells and at what cost.
**Method:** two briefs — the Uncapped funder reply (part 1's email B) and the American Pharma Wholesale supplier enquiry (new, sent 18 Jul). For each, an AI-ish draft was written carrying the **same facts and the same commitments** as Mason's real email, then run through both routes. Scoring order per `humanizer-selection`: recipient-fit > meaning preservation > tell removal > detector score.

**Design note that matters:** the AI-ish drafts deliberately keep the hard commercial language intact — "no substitution to a different manufacturer, even at the same price" and "as a condition of our order". Softening obligations was left to the humanizers to do or avoid, rather than baked into the input. Otherwise the test measures the draft, not the route.

## Tells planted (both drafts)

Sycophantic opener and closer ("I hope this email finds you well", "Happy to help!", "Thank you so much"), em dashes (4 in B, 2 in D), one semicolon in B, bolded-header bullets, significance inflation ("serves as definitive confirmation"), promotional register ("exciting opportunity", "mutually beneficial partnership", "strong commitment to quality"), AI vocabulary (robust, pivotal, fostering, comprehensive), negative parallelism ("It's not just a formality; it's a complete picture"), filler ("To provide further clarity", "kindly", "Before proceeding"), generic upbeat closer ("look forward to moving things forward"), copula avoidance ("serves as"), hedge padding ("it would be ideal", "where possible").

## D1 — Funder reply (Uncapped), AI-ish draft ~250 words

**Wiki route.** Removes the sycophantic opener and closer, the promotional and inflated language, all four em dashes, "comprehensive"/"successfully", the negative parallelism, the copula avoidance ("serves as definitive confirmation" → "confirming"), and converts the bolded-header bullets back to plain numbered points. Keeps the two-item numbered structure mirroring Brade's two numbered asks, keeps the full date "July 21, 2026", and keeps the cooperative closer ("Let me know if you need anything further to release the funds"). Facts and figures intact.

**Semicolon note:** it disappeared, but by accident — the clause containing it was restructured under catalogue #8 (copula avoidance). The wiki route still has no semicolon rule, so a semicolon in an otherwise-clean sentence would survive. Part 1's finding reproduces exactly.

**Research route.** Catches every tell the wiki route caught, plus the semicolon deterministically (hard rule 2), and produces visibly better rhythm — sentence counts 4, 15, 6, 16, 28, 9 pass all four burstiness conditions, where the wiki output has a 10/6/6 run that fails the no-three-consecutive-within-5 rule. Then three costs, all repeats of part 1 and all reproduced on AI-ish input:

- Dissolves the numbered structure a compliance reviewer uses to tick off both items.
- Drops the year from the filing date ("July 21" not "July 21, 2026") — small, but this is a Companies House filing reference in a KYC thread.
- Lever 9 cuts the offer-to-supply-more closer and replaces it with an assertion — "That's everything on our side for the funds release" — which overclaims completeness while the release is still pending on the funder's side.

## D2 — Supplier enquiry (American Pharma Wholesale), AI-ish draft ~230 words

**Wiki route.** Removes the "hope this email finds you well" opener, "exciting opportunity", "mutually beneficial partnership", "strong commitment to quality", "robust", "pivotal", "fostering", "absolutely", "kindly", the em dashes, the bolded-header bullets, and the "Thank you so much — I look forward to hearing from you!" closer. Keeps the three numbered asks as three numbered asks. **Every identifier survives**: item OTC752631, NDC 46122-0741-38, $335.08, Bionpharma / GNP, the three named documents. **Both obligations survive verbatim:** "no substitution to a different manufacturer, even at the same price" and "Please confirm you can provide these as a condition of our order."

**Research route.** Cleanest prose of the four outputs, and it also preserves both obligations. But it introduces the sharpest failure in either half of this bake-off:

- **It invents a justification.** Lever 5 (specificity insertion) pushed it to ground the no-substitution demand, and it produced "because we resell and import these units and *the NDC follows them through customs*". Mason never said that. It is a fabricated regulatory claim, asserted to a pharmaceutical wholesaler, in an email about import documentation.
- Collapses three separately-numbered asks into one dense paragraph, so a supplier answering by return has nothing to answer against. On a three-question enquiry this is the difference between three answers and one.
- Drops "Further to our registered wholesaler account (Bison Management Ltd, OTC items only)" — the line that tells the supplier which account this is.
- Sharpens "the ability to supply this documentation is important to us for ongoing repeat business" into "Documentation is what decides repeat business for us", which converts a stated preference into a stated decision criterion. Defensible, but it is a change in commercial posture the sender did not authorise.

## Verdict (part 2)

**The routes rank exactly as part 1 said, but the reasons are stronger and one is new.**

- **Tell removal: research route wins, and by more than part 1 implied.** On real AI-flavoured input its counted pre-output gate (explicit counts for em dashes, semicolons, curly quotes, banned vocabulary, then a written-out sentence-length list) catches things a literal self-check list misses, and it enforces rhythm the wiki route has no rule for at all. Part 1 understated this because its corpus had one mechanical tell in total.
- **Correctness risk: research route loses, and the risk is HIGHER here than in part 1.** This is the new finding. AI-ish drafts are vaguer than Mason's own prose, so Lever 5 has more abstract claims to "ground" — and it grounds them by inventing. Part 1 caught this as *pressure* toward an unsupported inference on the broker email; part 2 caught it *actually firing*, producing a false regulatory statement in a regulated-goods enquiry. A humanizer that fabricates more when the input is worse is exactly backwards for our use case, because worse input is precisely when a humanizer gets invoked.
- **Recipient-fit: wiki route wins again, same mechanism.** Both funder and supplier emails are structured replies to structured asks. The research route treats every text as an essay and dissolves the enumeration in both. Two for two on AI-ish input, three for three on human input.
- **Meaning preservation: wiki route wins.** Research route dropped a filing year, dropped account context, converted an offer into an assertion, and added a fact. Wiki route dropped nothing across either draft.
- **Detector score: not run.** Tie-break unused — the first three axes did not tie.

## Decision (part 2)

- **No change to canonical routing.** Outbound email stays `writing:humanize-text`. Long-form / public-facing / detector-sensitive stays `humanize-research`, explicit invocation only. The tell-removal half strengthens the existing verdict rather than disturbing it: the research route's advantage is real but sits on the third-ranked axis, and it is paid for on the second-ranked one.
- **No new use case splits off.** This test used no long-form sample, so it says nothing new about memos or public artifacts. The long-form route stands on part 1's reasoning, unchanged, and should not be described as re-validated here.
- **New guard rule, earned by D2 and now written into `humanizer-selection` Test B:** any clause a humanizer *adds* — especially a causal or explanatory one ("because…", "which means…") — must be checked against the source facts before the text ships. Rewriters are licensed to remove and reshape, never to explain. In correspondence about regulated goods, tax, or funding, an invented justification is a bigger liability than any AI tell it was added to disguise.
- **Nothing further to harvest from the research route.** Part 1 already moved its one clean mechanical win (semicolon detection) into `gmail-draft-humanize-gate.py`. Its remaining edge is burstiness enforcement, which is low value at 65–250 words and cannot be harvested without importing the structural damage.

## Honest limits (part 2)

- n=2 briefs, one author. Both are structured replies to structured asks, which is the shape that most disadvantages the research route — a discursive email might score differently, and none was tested.
- The AI-ish drafts were written in this session to be recognisably LLM-styled. They are representative of cold-model output, not sampled from a real model run, so the tell mix reflects the published catalogues rather than an empirical frequency distribution.
- Both routes were executed by applying their published rulebooks in-session, not by invoking the skills through the harness. Same method and same limitation as part 1.
- No detector was run, so "tell removal" is scored against the two catalogues, not against an independent classifier.
- No email was sent or drafted. All four outputs are evaluation artifacts only.
