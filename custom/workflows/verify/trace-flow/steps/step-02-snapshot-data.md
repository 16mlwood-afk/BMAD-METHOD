---
name: 'step-02-snapshot-data'
description: 'Capture live data at each pipeline stage by hitting endpoints, querying the DB, and inspecting runtime state'

nextStepFile: './step-03-render-pipeline.md'
---

# Step 2: Snapshot Data

**Goal:** For each stage in the pipeline, capture the actual data values flowing through it. This transforms the abstract stage map into a live pipeline view — like the difference between a circuit diagram and an oscilloscope trace.

---

## AVAILABLE STATE

From step 1:

- `{anchor}` — The user-provided anchor point
- `{anchor_type}` — Classification of the anchor
- `{stack}` — Auto-detected project stack
- `{stages}` — Ordered list of pipeline stages with shape in/out
- `{server_live}` — Whether the backend is running

---

## EXECUTION SEQUENCE

### 1. Determine Snapshot Strategy

Based on `{server_live}` and `{stack}`, choose the data capture approach:

| Condition | Strategy |
|-----------|----------|
| Server live + REST endpoint in pipeline | `curl` the endpoint, capture response JSON |
| Server live + SSE endpoint in pipeline | `curl` with streaming, capture events |
| Server live + DB stage | Query SQLite directly via `sqlite3` CLI |
| Server NOT live + DB exists on disk | Query SQLite directly (read-only) |
| Server NOT live + no DB | Static analysis only — extract example values from code (defaults, test fixtures, mock data) |

### 2. Capture Data at Each Stage

Work through the stages in pipeline order (source → sink). For each stage, capture a representative data sample.

#### Database / Source Stage

```bash
# SQLite — get a recent row from the relevant table
# Find the DB file from the project's config or .env, e.g.:
sqlite3 -json {project-root}/{db_file} "SELECT * FROM {table} ORDER BY ROWID DESC LIMIT 1"
```

Record the actual column names and values. If the table has many columns, focus on the ones that flow through the pipeline (identified in step 1's shape analysis).

For external API sources (Exa, crawl4ai), capture from the code:
- The request parameters/URL pattern
- A sample response structure from recent logs, test fixtures, or inline examples

#### Model / Transform Stage

Read the transformation code and apply it mentally to the captured source data:
- Which fields are renamed? Record old → new name with the actual value
- Which fields are computed? Show the computation and its result
- Which fields are dropped? Note them as "filtered out at this stage"
- Which fields are added? Show the default or computed value

#### Transport Stage (API / SSE)

If `{server_live}`:

```bash
# REST endpoint
curl -s http://127.0.0.1:8000{endpoint_path} | python3 -m json.tool | head -60

# SSE endpoint — capture first few events
timeout 5 curl -s -N http://127.0.0.1:8000{sse_path} 2>/dev/null | head -30

# With query parameters if needed
curl -s "http://127.0.0.1:8000{endpoint_path}?{params}" | python3 -m json.tool | head -60
```

If not live, extract the response shape from:
- Pydantic response models (`class FooResponse(BaseModel)`)
- Express Zod schemas
- TypeScript return types

Record the actual JSON keys and values (or the typed shape if no live data).

#### Frontend State Stage

This stage can't be directly queried from the CLI. Instead:
- Read the hook/component that receives the transport data
- Map which transport fields are destructured into state variables
- Record the variable names and their values (same as transport, unless transformed)

#### Render Stage

Read the JSX that displays each value. Record:
- The display label (what the user sees, e.g., "Buy-box", "Status", "Last checked")
- The value expression (e.g., `{lead.buyBoxPrice}`, `{formatCurrency(price)}`)
- The formatted output (apply the formatter to the captured value)

### 3. Handle Missing / Null Data

For each stage, if the captured data shows `null`, `undefined`, empty string, or missing field:

- **Note it explicitly** — this is valuable signal, not noise
- Record what the code does with the missing value (fallback? error? silent skip?)
- Check if this is expected (optional field) or a bug (field should always be populated)

### 4. Assemble Live Data Map

Store the captured data as `{live_data}` — a per-stage mapping:

```
Stage {n}: {name}
  Data captured: {yes | no — static only | no — not accessible}
  Sample values:
    {field_1}: {actual_value}
    {field_2}: {actual_value}
    ...
  Nulls/missing: {list of fields that were null or absent}
  Capture method: {curl endpoint | sqlite3 query | code analysis | test fixture}
```

---

## CHOOSING A REPRESENTATIVE RECORD

When querying the DB or hitting an endpoint, aim for a record that exercises the most stages:

- Prefer a record with **non-null optional fields** (shows the full pipeline)
- If the pipeline handles different record types (e.g., leads with different statuses), capture one of each major type
- If the user specified a particular ID or record, use that one
- For list endpoints, capture the first item from the list response

If the query returns sensitive data (API keys, passwords, tokens), redact the values but keep the field names.

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/verify/trace-flow/steps/step-03-render-pipeline.md`.

---

## SUCCESS METRICS

- Every stage with an accessible data source has real captured values
- Database stages queried with actual SQL, not guessed from schema
- API stages hit with actual curl, not inferred from route definitions
- Null/missing fields explicitly noted (not silently skipped)
- Capture method recorded for each stage (transparency about what's real vs. inferred)
- Sensitive data redacted

## FAILURE MODES

- Skipping live capture when the server IS running ("I'll just read the types")
- Assuming field values from type definitions instead of querying
- Not detecting null/missing values as signal
- Querying the wrong DB file (e.g., worktree DB instead of main DB)
- Hitting an endpoint that requires auth without including credentials
- Capturing list data but only showing the array length, not the actual field values
