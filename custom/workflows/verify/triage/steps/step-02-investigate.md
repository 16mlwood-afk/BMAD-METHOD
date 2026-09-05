---
name: 'step-02-investigate'
description: 'Query production data, read code, and break the symptom into concrete findings with data behind each one'

nextStepFile: './step-03-diagnose.md'
---

# Step 2: Investigate

**Goal:** Execute the investigation plan from step 1. Query production data, read the relevant source code, and produce a list of concrete findings — each backed by data, not speculation.

**Principle:** Go wide before going deep. Start with aggregate queries that reveal the shape of the problem, then drill into anomalies. Don't get tunnel-visioned on the first interesting thing you find.

---

## AVAILABLE STATE

From step 1:

- `{observation}` — normalized description of the symptom
- `{observation_type}` — classification
- `{page_context}` — page, route, feature, filter state
- `{investigation_plan}` — specific queries and reads to perform

## STATE VARIABLES (set in this step)

- `{findings}` — ordered list of concrete data points, each with source and evidence

---

## EXECUTION SEQUENCE

### 1. Query Production Data

Execute the queries from `{investigation_plan}`. For each query:

- **Record the actual result** — row counts, distributions, specific values
- **Note anomalies** — unexpected nulls, skewed distributions, outlier values
- **Follow the data** — if an aggregate reveals a surprising cluster, drill in with a follow-up query

**Query patterns by observation type:**

#### `error-count` / `error-message`

```
1. Status distribution:     GROUP BY status ORDER BY count DESC
2. Error breakdown:          GROUP BY error_message ORDER BY count DESC
3. Source clustering:        GROUP BY supplier/batch/source ORDER BY count DESC
4. Time clustering:          GROUP BY date_trunc(created_at) ORDER BY date
5. Drill into nulls:         WHERE error_message IS NULL — these are silent failures
```

#### `unexpected-state`

```
1. Field population:         SELECT {field}, COUNT(*) GROUP BY {field}
2. Source check:             Does the field exist in the DB? Is it populated?
3. Transport check:          Does the API/loader include this field in its response?
4. Render check:             Does the component read and display this field?
```

#### `silent-failure`

```
1. Pipeline status:          Check system-status endpoint or equivalent health check
2. Stuck records:            WHERE status IN ('pending','processing') AND updated_at < {threshold}
3. Recent activity:          ORDER BY updated_at DESC LIMIT 10 — when did the last thing happen?
4. Cron/queue history:       Check scheduled job logs or queue depth
```

#### `absent-change`

**Walk these in order and record a result for each. The order is causal, not a menu** — an
earlier cause makes every later check meaningless, and the last one is the one that gets
guessed first when the walk is skipped.

```
1. NOT DEPLOYED           Is the commit carrying the change in the RUNNING build?
                          Read the live commit off the container / deploy record, never
                          off origin/main. Merged is not shipped.
2. WRONG VARIANT SERVED   What does the route the operator opened actually serve ON THEIR
                          DEVICE? Device/viewport routing, middleware redirects and
                          ?view= variants can hand them a different station from the one
                          that was changed.
3. NO WAY IN              Does a way in exist and is it reachable at their viewport — a nav
                          entry, a link, a button? An off-nav route and a nav strip that
                          overflows off-screen are both this cause.
4. RENDERS BUT EMPTY      Is a value actually bound, and does it answer the operator's
                          question? An empty element matching an empty design mock is a
                          perfect visual match showing nothing; a panel filled with the
                          wrong GRAIN of data answers nothing while looking complete.
5. EXCLUDED BY STATE      Did the write pass the state gate the surface filters on? A row
                          created through a side path can be absent from every operator
                          list by design, with nothing wrong anywhere.
6. CLIENT / SESSION       Only now: stale bundle, service worker, a tab opened before the
                          deploy, permissions, rollout timing.
```

**Which frame, not which page.** Causes 2–4 turn on the exact frame the operator is on. A
route can serve several — a scan step and a by-sight step, a picker and a confirm — and a
change wired to one of them is invisible from the others. Name the frame, not just the route.

##### Instrument scope — what each check actually proves

None of these observes the operator's path. Report each as what it is; **no combination of
them may be cited as evidence that the user saw the change on the surface they use.**

| Instrument | Proves | Does NOT prove |
|---|---|---|
| `check-reachability` | a module-graph path exists from some route entry to the component | that any operator path reaches it, or that it renders |
| `wire-check` | producer and consumer agree on field names and shapes | that the wired field appears on the frame the operator opens |
| `trace-flow` | the data topology from source to render, with live values | which route or frame the operator actually navigates |
| design comparison grid | the built values match the design's values | that anything is visible — an empty box matching an empty mock passes |
| deploy guard (`LIVE SHA:`) | a commit was read back off the running container | that the change is reachable, rendered, or correct |
| completion guard (`NEXT/OWNER/TRIGGER`) | the three fields are present | that the named trigger describes the right frame |
| tests / `tsc` / build | the code behaves as its own tests assert | anything about the operator's path |

**The only evidence that closes cause 2–5 is the operator's own anchor** — their URL, their
named entry point on their device, or their screenshot. Until that is in hand, report
operator-path reachability as `UNVERIFIED` and say so in the same breath as any "it is live".

#### `ui-concern`

```
1. Read the page component and its data loader
2. List all fields available in the loader response
3. List all fields actually rendered in the template
4. Identify fields available but not shown
```

#### `performance`

```
1. Data volume:              SELECT COUNT(*) from the primary table
2. Query analysis:           Read the loader/API route, identify query patterns
3. N+1 detection:            Look for loops that issue individual queries
4. Pagination check:         Is the query bounded? Does it fetch everything?
```

### 2. Read Relevant Source Code

Based on the query results, read the code that's involved:

- **Error producers:** Find where error messages are generated — `grep -rn "{error_string}" src/`
- **Pipeline stages:** If the issue involves processing, read the handler/processor that transitions records through states
- **UI components:** If the issue involves display, read the page component and its data loader
- **Don't over-read.** Read the files that the data points at, not every file in the feature area.

### 3. Cross-Reference

Check whether the investigation reveals things the user didn't mention:

- **Related failures:** Are there other error types in the same table/pipeline that the user didn't see?
- **Upstream causes:** Is the symptom caused by something earlier in the pipeline?
- **Downstream impact:** Does this failure affect other parts of the system? (e.g., failed extraction → missing data in reports)
- **Recurrence pattern:** Is this a one-time issue or will it keep happening?

### 4. Compile Findings

For each finding, record:

```
### Finding {n}: {one-line title}

**Evidence:** {the query result, code reference, or data point that supports this}
**Count/Scope:** {how many records/users/pages are affected}
**Source:** {which query or file read produced this finding}
**Anomaly:** {what's surprising or unexpected about this — if anything}
```

Group findings by relatedness — findings that share a root cause should be adjacent.

---

## INVESTIGATION DISCIPLINE

### Do

- Query aggregates first, then drill into specifics
- Record exact numbers — "26 invoices" not "many invoices"
- Note what you checked AND what the result was, even if normal
- Follow null/missing data — silent failures hide in null error_message fields
- Check batch/source clustering — problems often come from one source

### Don't

- Assume the first finding explains everything — keep querying
- Stop at the symptom — trace to the root cause
- Read code without querying data first — the data tells you where to look
- On `absent-change`, run a repository-side check and report its green result as though it answered the operator's question — see the instrument-scope table
- Query one record and generalize — always check the distribution
- Ignore "working" records — comparing failed vs. successful often reveals the cause

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/verify/triage/steps/step-03-diagnose.md`.

---

## SUCCESS METRICS

- Every item in `{investigation_plan}` was executed (or explicitly skipped with reason)
- Each finding has concrete evidence — numbers, query results, code references
- Silent failures (null error messages, stuck states) were specifically checked
- For `absent-change`: causes 1–5 each carry a recorded result before cause 6 was considered at all
- Clustering was checked (by source, batch, time, error type)
- Findings are grouped by relatedness
- Code was read only where data pointed — not speculative broad reading

## FAILURE MODES

- Querying one record instead of aggregating across all affected records
- Stopping after the first finding ("found it!") without checking for compound problems
- Reading code before querying data — leads to theory-driven investigation instead of data-driven
- Not checking for null/missing error messages — silent failures are the hardest bugs to find
- Reporting "I found 37 failures" without breaking down the error types — this is just restating the symptom
- Answering an `absent-change` observation from the repository alone — a green deploy, reachability or test result describes the artifact, never the operator's path
- Over-reading code — reading 10 files "for context" instead of the 2 files the data points to
