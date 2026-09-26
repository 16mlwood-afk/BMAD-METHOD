---
name: skill-provenance-standard
description: "STD-SKILLPROV-001 (DRAFT) — discovery goes OUTWARD before any skill is built; adopt-over-build is the default; a skill without provenance frontmatter carrying ≥1 source_research URL is UNVERIFIED. Retrofit when touched."
contract_version: 1
status: DRAFT
---

# STD-SKILLPROV-001 — Skill provenance & external discovery (DRAFT)

> **Why this file exists at all, stated first because it is the point.** This standard has been
> enforced by citation since 2026-07-24 — `human-writing-capabilities.md` treats it as authority, a
> fork-gap entry judged two skills UNVERIFIED against it, and the
> `skill-provenance-and-external-discovery` memory names this exact path as its home. **The file was
> never written.** For five weeks the rule was real, cited, and unreadable: nobody could comply with
> it deliberately, only by remembering it. A standard that exists only in the citations of other
> documents is the drift it exists to prevent.
>
> Written 2026-07-31 to say exactly what was already being enforced. **No rule below is new.** If
> something here surprises you, that is the five-week gap talking, not a change of policy.

## Origin

Owner ruling, Mason, 2026-07-24, from two measured failures in one session:

1. **An inward-only check reported a capability as absent.** "No Outlook connection" was stated from
   the installed-tool registry while an official Anthropic M365 connector and several GitHub Outlook
   MCP servers existed, unsearched. The claim was true of the session and false of the world.
2. **Two skills were built from scratch without looking first.** The humanizer and
   `property-appraisal` were authored as originals with no search for existing evidence-based
   solutions, and no record of why building was the right call.

Both are the same defect: **treating "what I can see from here" as "what exists."**

## The rule

### 1 · Discovery goes OUTWARD

"I searched the tool registry / installed skills" tells you what is **wired into this session**. It
is **not** evidence that a thing does not exist.

Before claiming *"there is no X"*, or proposing to build one, run **both**:

- an external **web** search (docs, marketplace, vendor blog), and
- a **GitHub / MCP / extension** search.

**State where you looked, with URLs.** A search whose sources are not named did not happen, for
review purposes.

**Never report "no X integration" from an inward check** without the qualifier: *"not installed in
this session — I have NOT searched the web or marketplace."* Then offer to search, or better, search
first and answer once.

### 2 · Adopt over build

After the outward pass, make an **explicit call** and name which it is:

| call | meaning |
|---|---|
| **adopt** | use the existing thing as-is |
| **adapt** | wrap, configure or fork an existing thing |
| **build-original** | write it from scratch |

**`build-original` requires a named reason** — one of: licence, security/privacy, quality of the
candidate, or poor fit. Stated, not implied. *"I didn't find anything"* is not a reason unless §1 was
actually run and its sources named.

### 3 · Provenance frontmatter, or UNVERIFIED

**Revised 2026-07-31 after the outward pass this standard requires of everyone else.** The first cut
was hand-rolled and wrong in two ways the prior art makes obvious. Both corrections are below, with
the reasoning, because the reasoning is the transferable part.

**Correction 1 — nest under `metadata:`.** The Agent Skills standard treats `version` and similar as
NOT top-level spec fields; portable implementations put them in the `metadata` map. The first cut put
everything at top level, which breaks portability with the spec our own skills are written against.

**Correction 2 — separate SELF-ASSERTED from MACHINE-GENERATED.** This is the important one. SLSA,
in-toto and AgentHub all split provenance the same way: what the author *claims* is recorded
separately from what the platform can *verify*, because a field the author writes is the weakest link
in the chain. Our first cut was 100% self-asserted — which is precisely why "a lazy link that looks
compliant is worse than an honest blank" was a fair objection to gating on it.

The consequence is a better gate: **`discovery_performed` is machine-knowable.** The authoring
workflow knows whether it executed a search, and writes that flag itself. An author can fill
`source_research` with a junk URL; they cannot fake having run the step, because the step is what
sets the flag.

```yaml
name: <skill-or-agent-name>
description: <one line>
metadata:
  # ---- MACHINE-GENERATED — written by the authoring workflow, never by hand ----
  id: <stable-slug>
  version: <integer>
  created_at: <ISO timestamp>
  authored_by: <workflow name + version>
  discovery_performed: true | false   # did the outward pass actually RUN?
  discovery_ran_at: <ISO timestamp>   # absent when discovery_performed is false

  # ---- SELF-ASSERTED — the author's claims, recorded as claims ----
  source_research:                     # >=1 URL, or empty with an override/exemption
    - https://...
  origin_type: adopted | adapted | original
  adoption_reason: <required when origin_type is `original`>
  override_reason: <required when source_research is empty and discovery was skipped>
  exemption_reason: <required when no external prior art could exist>
  predecessor_id: <optional>
  superseded_by: <optional>
  last_reviewed_at: <ISO date>
```

**A skill missing this is UNVERIFIED.** Not broken, not banned — *unverified*, and it must be
described that way whenever its trustworthiness is at issue. The word is doing work: it says "nobody
has checked," not "this is wrong."

**Read the two halves differently.** `discovery_performed: false` is a fact about the process and is
trustworthy. `source_research: [<url>]` is a claim about diligence and is only as good as the author
— it tells you a search was *reported*, not that it was *good*. Treat the machine half as evidence
and the self-asserted half as testimony.

### 4 · Retrofit when touched

Do **not** schedule a fleet-wide backfill. When you edit a skill for any other reason, bring its
frontmatter up to this schema in the same change. The corpus converges through ordinary work, and
nothing is blocked waiting for a migration nobody has time for.

## Scope

**Applies to:** skills (`.claude/skills/`, `custom/skills-native/`), custom agents (`custom/agents/`),
and any workflow that AUTHORS one — `create-agent` and `create-workflow` are **consumers** of this
standard, not exceptions to it.

**Does not apply to:** briefs (they have their own provenance contract in `brief-revision-policy.md`,
which this deliberately mirrors), or to prose docs.

## Enforcement tier — stated honestly

**PROBABILISTIC.** Everything above is prose a model must choose to follow. There is no linter, no CI
gate, and no hook.

That is not an oversight; it is the current state, and pretending otherwise is the exact failure mode
this standard names. The deterministic tier, when built, is:

- a **provenance linter** over the skill corpus — frontmatter present, ≥1 `source_research` or an
  `exemption_reason`, `adoption_reason` present when `origin_type: original`; and
- a **new-skill gate** in CI or pre-commit that fails an added skill lacking it.

Both are **unbuilt**. Per the fork's own rule, design them with `enforcement-expert` before wiring —
prose is not enforcement, and a gate authored by guesswork gets switched off.

**Piloted in one skills-heavy repo before fork-wide promotion.** Until that pilot runs, this stays
**DRAFT**.

## Known non-compliance at time of writing

Recorded so the standard's first act is honesty about its own corpus:

- `outreach-email` — house-built, no provenance frontmatter. UNVERIFIED.
- the installed humanizer — no provenance frontmatter. UNVERIFIED.
- `property-appraisal` — named in the origin ruling as the first exemplar to retrofit. Still owed.
- **`create-agent` / `create-workflow`** — the two workflows that AUTHOR agents and workflows carry no
  provenance support, so everything they emit is born UNVERIFIED. The sharpest gap on this list,
  because it compounds: every future skill inherits the omission.

## Prior art — the outward pass for this standard itself

Run 2026-07-31. **Call: ADAPT**, not build-original — the schema above is our shape carrying two
corrections lifted directly from existing work.

| source | what was taken |
|---|---|
| [SLSA build provenance](https://slsa.dev/spec/draft/build-provenance) · [in-toto + SLSA](https://slsa.dev/blog/2023/05/in-toto-and-slsa) | provenance is generated BY the build platform, not self-asserted by the author; separate builder identity from declared inputs |
| [AgentHub: a registry for discoverable, verifiable, reproducible AI agents](https://arxiv.org/pdf/2510.03495) | the explicit self-asserted vs machine-generated/registry-verified split, and which fields fall on each side |
| [The Agent Skills standard (SKILL.md)](https://medium.com/@loccarrre/the-agent-skills-standard-how-a-simple-skill-md-file-turns-ai-agents-into-on-demand-specialists-172af1d9737d) | `version` and non-spec fields belong under `metadata:` for cross-tool portability |
| [SkillSieve](https://arxiv.org/pdf/2604.06550) · [SkillClone](https://arxiv.org/pdf/2603.22447) | why provenance matters in the agent-skill ecosystem specifically: malicious-skill triage and clone propagation |

**Why ADAPT rather than adopt outright:** SLSA and in-toto solve *build-artifact* provenance with
cryptographic signing and a registry. We have no registry, no signing, and markdown skills authored
by a workflow — adopting the machinery wholesale would be heavier than the problem. What transfers is
the *model*: separate what the platform knows from what the author claims, and never let a
self-asserted field carry a gate on its own.

**Honest note on this pass:** two web searches and one paper fetch. Not exhaustive. It was enough to
find two concrete defects in the first cut, which is the argument for the gate.

## Related

- `skill-provenance-and-external-discovery` — the global behavioural memory this file is the
  fork-canon home for.
- `brief-revision-policy.md` — the sibling provenance contract for briefs; this mirrors its shape.
- `tool-discovery` — the skill that performs the §1 outward pass.
- **STD-PERSONA-002** (`persona-placement`) — decides whether a flow earns a persona at all; this
  decides whether what you build has a recorded origin.
