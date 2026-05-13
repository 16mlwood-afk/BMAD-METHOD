---
name: 'step-01-map-wires'
description: 'Parse handoff artifact and git diff to identify every data field that was added, changed, or wired up'

nextStepFile: './step-02-trace-wires.md'
---

# Step 1: Map the Wires

**Goal:** Build a complete inventory of every data field the implementation touches. Each field becomes a "wire" to trace in step 2.

---

## STATE VARIABLES (capture now, persist throughout)

- `{handoff_path}` — Path to the handoff artifact being audited
- `{wires}` — List of data fields to trace (built in this step)
- `{baseline_commit}` — The `source_pr` or baseline commit from the handoff (if available)
- `{stack}` — Project stack (auto-detected from project files)

---

## EXECUTION SEQUENCE

### 1. Load the Handoff

Read `{handoff_path}` fully. Extract:

- **What was implemented** — the summary, delivered-beyond-spec, and known-gaps sections
- **Files modified** — from the PR or by running `git log --oneline --name-only {baseline_commit}..HEAD` if a baseline commit is available
- **Recommended follow-ups** — these often hint at incomplete wiring

If the handoff references a PR or commit range, run `git diff {range} --name-only` to get the full file list.

### 2. Detect Stack

Read and follow: `{project-root}/_bmad/bmm/workflows/shared/detect-stack.md`

Store the result as `{stack}`. The stack profiles below are reference templates — if `{stack}` is `unknown`, use the closest match and adjust column names, file patterns, and transport mechanisms to fit the actual project.

### 3. Identify Data Fields

For each modified file, classify it using the **stack-specific layer table**:

---

#### `express-react-drizzle`

| Layer            | File patterns                                                                                                               | What to extract                                                                                                       |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Source**       | `server/src/db/schema.ts`, migration SQL files                                                                              | New columns, type changes, default values, constraints                                                                |
| **Shared types** | `shared/src/types/**/*.ts`, `shared/src/index.ts`                                                                           | New/changed interface fields, new types, updated `Pick`/`Partial` wrappers                                            |
| **Transport**    | `server/src/features/**/*.routes.ts` (Zod schemas), `server/src/features/**/*.service.ts` (rowTo\* mappers, CRUD functions) | Fields in Zod validation schemas, fields mapped in row-to-model functions, fields accepted in create/update functions |
| **Sink**         | `client/src/**/*.tsx`, `client/src/hooks/**/*.ts`, `client/src/lib/**/*.ts`                                                 | Fields destructured from API responses, fields rendered in JSX, fields read from React Query hooks                    |

**Counter/metric patterns to check:**

- Computed values in service layer (aggregations, `.length`, `.reduce()`)
- Derived fields in `rowTo*` functions that combine or transform columns
- Frontend computed values (`useMemo`, inline expressions) that derive from API data

**Outbound payload patterns to check:**

- Webhook payload builders that serialize a **subset** of a model — if the source model gains fields, the outbound payload silently drifts
- External API response shapes forwarded to third-party services
- Export endpoints (CSV, JSON, PDF) that serialize domain models

---

#### `python-fastapi-sse`

| Layer         | File patterns                                                      | What to extract                                                                                  |
| ------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| **Source**    | `src/agent.py`, `src/tools/*.py`, `src/main.py` (models/endpoints) | New fields on Pydantic models, new dict keys in tool output, new state variables in AgentState   |
| **Transport** | `src/main.py` (SSE streaming, `_ChunkProcessor`, API endpoints)    | Fields emitted in SSE `progress` events, fields in API response bodies, counter/metric variables |
| **Sink**      | `frontend/src/**/*.tsx`, `frontend/src/**/*.ts`                    | Fields read from SSE events, fields destructured from API responses, fields rendered in JSX      |

**Counter/metric patterns to check:**

- Variables that increment (`+= 1`, `+= len(...)`, `.count(...)`) in `_ChunkProcessor` or `_extract_pipeline_metadata`
- Dict keys in `progress_snapshot()` or API response builders
- Frontend state variables that display these values

**Outbound payload patterns to check:**

- Webhook payload builders (`webhook.py`, `*_webhook*`, `build_payload()`) that serialize a **subset** of a model — if the source model gains fields, the outbound payload silently drifts
- External API response shapes that forward data to other services (not the frontend)
- Export/download endpoints that serialize models to CSV, JSON, or PDF

---

#### `nextjs-prisma`

| Layer         | File patterns                                                                           | What to extract                                                                                         |
| ------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Source**    | `prisma/schema.prisma`, migration SQL files                                             | New model fields, relation changes, enum updates                                                        |
| **Transport** | `app/api/**/*.ts` (route handlers), `lib/actions/**/*.ts` (server actions), Zod schemas | Fields in request/response types, fields in server action returns, Prisma `select`/`include` clauses    |
| **Sink**      | `app/**/*.tsx` (pages/layouts), `components/**/*.tsx`, client-side hooks                | Fields consumed from `useQuery`/server components, fields rendered in JSX, fields from `useActionState` |

**Counter/metric patterns to check:**

- Prisma `_count` and aggregation queries
- Computed fields in server actions or API handlers
- Client-side derived state from query results

**Outbound payload patterns to check:**

- Webhook handlers or external notification functions that serialize a subset of a Prisma model
- Third-party API integrations that forward domain data
- Export/download routes that build payloads from domain models

---

### 4. Create Wire Entries

For each field, create a wire entry:

```
Wire: {field_name}
Source: {file:line where the value is produced}
Expected transport: {API endpoint / SSE event / server action / direct prop}
Expected sink: {component or hook that should consume it}
```

### 5. Check for Dead Exports

Scan for exports in shared constant/config files that were previously consumed by modified files. If the diff **removes an import** of a constant, check whether any other file still imports it. Orphaned exports are wires too — classify them as potential dead code.

### 6. Output Wire Inventory

Present the inventory to the conversation context (not to a file — this is intermediate state):

```
## Wire Inventory ({count} wires)

### New/Changed Wires
1. {field_name} — {one-line description}
   Source: {file:line}
   Transport: {mechanism}
   Sink: {file:line or "unknown"}

### Counter/Derived Wires
1. {counter_name} — {what it counts/derives}
   Produced: {file:line}
   Transported: {file:line in API response or hook}
   Displayed: {frontend file:line or "unknown"}

### Outbound Payload Wires
1. {payload_field or model_name} — {webhook / external API / export}
   Source model: {file:line}
   Payload builder: {file:line}
   Gap: {fields on source model NOT in outbound payload}

### Potentially Dead Exports
1. {export_name} — {file:line, was imported by {modified_file}, check remaining consumers}
```

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/wire-check/steps/step-02-trace-wires.md`.

---

## SUCCESS METRICS

- Handoff artifact loaded and parsed
- Stack auto-detected from project files
- All modified files categorized by the correct stack-specific layer table
- Every data field, counter, and potentially dead export identified as a wire
- Wire inventory presented with source/transport/sink columns
- No wires missed because a layer was skipped (e.g., only checking backend)

## FAILURE MODES

- Only looking at files mentioned in the handoff (the handoff is a summary — the diff has the truth)
- Using the wrong stack's layer table (e.g., looking for `_ChunkProcessor` in an Express project)
- Missing counters/metrics (these are the most common loose wires)
- Not checking for dead exports when the diff removes imports
- Assuming a field is wired because it exists in the backend — must verify transport AND sink
