---
name: fork-gap-axes-v2
status: DRAFT — awaiting owner approval
supersedes_field: state
gap: FG-2026-07-27-04
---

# Fork-gap register: split the overloaded `state` into `fix` + `delivery`

**Owner ruling 2026-07-27:** proceed 1 → 2 → 3. Step 1 (contradiction detector) is **BUILT**; this
document is step 2 (the schema change) and step 3 (the derivability note), plus the rollout order.

---

## 1. Why one field cannot hold this

A verify-and-close sweep on 2026-07-27 reclassified **8 entries in one sitting**. None needed work.
Every one already recorded, *in its own status line*, that the fork fix was DONE with distribution the
only residue — and every one still sat at `open`/`partly`.

Eight independent authors wrote the truth in prose and left the field wrong. That is not carelessness;
it is the signature of a field that cannot express what the author needed to say.

One entry spans **three lifecycles**, and `state` is a single enum across all of them:

| Layer | Changes | Owner |
|---|---|---|
| **FINDING** — this is broken, here is the evidence | never, once written | the noticer |
| **DECISION** — may anyone start, and on what | rarely (`routing:` already covers it) | Mason |
| **DELIVERY** — authored → synced → committed → pushed | at every stage | whoever ships |

`open | partly | blocked | fork-fixed-distribution-owed | closed | superseded` mixes *"has anyone
diagnosed this"* with *"is it fixed"* with *"has it shipped"*. An author who fixed a thing but has not
distributed it has **no field that says so** — `partly` is technically true and carries no information,
`closed` is a lie, and `fork-fixed-distribution-owed` (added later, as a patch on exactly this problem)
is a single point solution to one of the several combinations that exist.

---

## 2. The replacement: two orthogonal axes

```yaml
fix:      none | partial | done
delivery: n/a  | owed    | done
```

### `fix:` — is the defect repaired at source?

| value | means | test |
|---|---|---|
| `none` | diagnosed, nothing built | no implementing change exists |
| `partial` | some named sub-fixes landed, others explicitly not taken | the entry NAMES which are outstanding |
| `done` | the defect is repaired at source | nothing further to build for this entry |

**`partial` owes an enumeration.** "Partly" with no list of what remains is the state that rotted the
old field. If you cannot name what is outstanding, it is `none` or `done`.

### `delivery:` — has the repair reached the places that consume it?

| value | means | when to use |
|---|---|---|
| `n/a` | nothing to distribute | fork-local tooling, docs consumed only in the fork, harness-vendor entries |
| `owed` | built, not yet reaching consumers | needs the sync fan-out, a re-port, a push, a project PR |
| `done` | consumers actually have it | verified, not assumed |

**`delivery` is meaningless while `fix: none`.** Enforce `fix: none ⇒ delivery: n/a`.

### Terminal states keep their own field

`closed` and `superseded` are lifecycle, not progress. Keep `state: closed|superseded|live` (or drop
`state` and treat `closed_at`/`superseded_by` as the terminal markers — implementer's choice, no
behavioural difference). **Everything else moves to the two axes.**

---

## 3. Mapping table — current value → new pair

| current `state` | `fix` | `delivery` | notes |
|---|---|---|---|
| `open` | `none` | `n/a` | the honest default for an undiagnosed-fix entry |
| `partly` | `partial` | `n/a` \| `owed` | **AMBIGUOUS BY CONSTRUCTION — must be read, never bulk-mapped.** This is the whole bug: today `partly` means both "half-built" and "built, undelivered". |
| `blocked` | `none` \| `partial` | `n/a` | `blocked_by` stays; blocking is orthogonal to both axes |
| `fork-fixed-distribution-owed` | `done` | `owed` | exact, mechanical — the state that was invented because the axes were missing |
| `closed` | `done` | `done` | |
| `superseded` | — | — | terminal; `superseded_by` carries it |

**Only `partly` requires human reading.** Everything else maps mechanically. That is ~17 entries at the
time of writing — an afternoon, not a project — and the contradiction detector already tells you which
of them are the "done + owed" kind.

---

## 4. Worked examples

**1 — broken and untouched**
```yaml
fix: none
delivery: n/a
```
*Diagnosed, evidence recorded, nothing built. `delivery: n/a` because there is nothing to deliver yet —
not because delivery does not apply.*

**2 — fixed locally, not distributed** (the 8-entry case)
```yaml
fix: done
delivery: owed
distribution: "sync-bmad-workflows.sh fan-out to the 13 projects"
```
*Reads at a glance as ONE sync item, not an open investigation. Thirteen of these are currently one
command.*

**3 — fixed and fully delivered**
```yaml
fix: done
delivery: done
state: closed
```

**4 — blocked on an owner decision**
```yaml
fix: none
delivery: n/a
blocked_by: "owner ruling on whether R3 admits a policy-lane artifact"
```
*Blocking is not a progress value. An entry can be blocked at `fix: partial` too.*

**5 — not applicable for delivery** (fork-local tooling)
```yaml
fix: done
delivery: n/a
```
*`tools/*` runs from the fork; no project consumes it. Marking this `owed` would inflate the sync
queue with items no sync can move — the failure mode in the opposite direction.*

**6 — genuinely partial, with the residue named**
```yaml
fix: partial
delivery: owed
```
*e.g. `FG-2026-07-20-07`: candidate fix 1 shipped; 2 and 3 explicitly not taken. The entry must name
them — that enumeration is what `partial` costs.*

**7 — harness-vendor entry**
```yaml
fix: none
delivery: n/a
owner: harness-vendor
```
*We cannot repair it. A documented recovery path around it is a SEPARATE entry at `fix: done`, not a
mutation of this one.*

**8 — fixed here, owed to twelve others**
```yaml
fix: done
delivery: owed
```
*A project-scope fix applied in one repo and pending in the rest — same pair as example 2, different
distribution mechanism. The pair does not care which mechanism.*

---

## 5. What is derivable, and what is not (step 3)

**Delivery may be DERIVED only where distribution is machine-checkable.** Concretely:

| target class | derivable? | how |
|---|---|---|
| `custom/workflows/**`, `custom/skills/**` | **yes** | diff fork copy vs each project's synced copy |
| `custom/githooks/**` | **yes** | same, per project `.githooks/` |
| `tools/**`, fork `docs/**` | **n/a** | consumed from the fork; nothing to compare |
| `.claude/hooks/**`, `settings.local.json` | **no** | gitignored, machine-local, no remote truth |
| project-scope targets | **no** | needs that project's own delivery notion (a PR, a deploy) |
| harness targets | **no** | outside our control entirely |

**Three rules, and the third is the one that gets forgotten:**

1. Derived delivery **backs** the written axis — it never replaces it. Where derivation is possible it
   should *contradict-check* the written value, exactly as the prose detector does now.
2. Where derivation is impossible, `delivery:` stays **written state** and is honest about being so.
3. **A derivation that cannot answer must say UNKNOWN, never `done`.** Absence of a diff is not proof
   of delivery when the comparison could not run — the same discipline as `authorship: unknown` and
   "unparseable ≠ young".

**This is why derivation is step 3 and not step 1.** It covers roughly half the register, so building
it first would have left the other half with the same rotting field and a false sense of coverage.

---

## 6. Rollout order

| step | what | status |
|---|---|---|
| **1** | contradiction detector — WARN-only, `npm test` + `check:forkgap-contradiction` | **BUILT 2026-07-27** |
| **2** | split `state` → `fix` + `delivery`; migrate; update schema check, surfacer, archiver | **THIS DOC — awaiting approval** |
| **3** | derive `delivery` per-target where checkable; contradict-check the written value | after 2 |

**Step 2's work list**, so approval is a yes/no rather than a discovery exercise:

1. Extend `fork_gap_lint.py`: accept both shapes during migration, require the pair afterwards,
   enforce `fix: none ⇒ delivery: n/a` and `partial ⇒ residue named`.
2. Mechanically map every non-`partly` entry (table §3).
3. Hand-read the `partly` entries — the detector already lists the "done + owed" ones.
4. Update the three consumers that read `state`: `check-fork-gaps.sh` (SessionStart surfacer),
   `archive-fork-gaps.py`, and the `--report` mode built in step 1.
5. Keep `state` as a deprecated alias for one cycle so a parallel session's in-flight entry does not
   fail the gate mid-write — the register takes concurrent writes from many sessions, and a hard
   cutover would block all of them.

---

## 7. Honest limits of step 1 (already built)

- It is a **keyword conjunction**, not comprehension: it fires only when the prose asserts *fix done*
  **and** *distribution owed* while the field disagrees. A differently-worded stale entry is missed.
- First cut fired **15/69** — 8 of them `partly resolved` prose on a `partly` entry, which is
  *agreement*. Tightened to the conjunction: **1 true finding, 2 acknowledged**. That tightening is the
  point: a detector that cannot tell agreement from disagreement gets ignored.
- `contradiction_ack: <reason>` silences a legitimate match and **requires a reason** — a bare ack is
  rejected.
- It catches the **symptom**. Until step 2 lands, entries will keep acquiring the same disagreement,
  because the field still cannot say what the author means.
