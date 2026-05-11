---
name: 'step-01-map-stages'
description: 'Resolve the anchor point and discover every stage in the data pipeline from source to render'

nextStepFile: './step-02-snapshot-data.md'
---

# Step 1: Map the Stages

**Goal:** Starting from the anchor point, walk the code in both directions (upstream toward DB/source, downstream toward UI render) and identify every stage where data is produced, transformed, transported, or consumed. Each stage becomes a node in the pipeline diagram.

---

## STATE VARIABLES (capture now, persist throughout)

- `{anchor}` — The user-provided starting point (route, endpoint, component, table, or feature)
- `{anchor_type}` — Classification: `page` | `endpoint` | `component` | `model` | `feature`
- `{anchor_file}` — Resolved file path of the anchor
- `{anchor_line}` — Resolved line number of the anchor
- `{stack}` — Auto-detected project stack (detected in this step)
- `{stages}` — Ordered list of pipeline stages (built in this step)
- `{server_live}` — Whether the backend is running (detected in this step)
- `{live_data}` — Captured data values at each stage (populated in step 2)
- `{gaps}` — Audit findings (populated in step 4)

---

## EXECUTION SEQUENCE

### 0. Detect Stack and Server

Read and follow: `{project-root}/_bmad/bmm/workflows/shared/detect-stack.md`

Store the result as `{stack}`.

Check whether the backend is running:

```bash
lsof -iTCP:8000 -sTCP:LISTEN -P 2>/dev/null | grep -q LISTEN
```

Store as `{server_live}` (true/false).

### 1. Resolve the Anchor

Classify the anchor and find its entry point in the code:

| Anchor type | How to resolve |
|-------------|---------------|
| **Page route** | Find the route definition in `react-router-dom` config or file-based routing. Identify the page component. |
| **API endpoint** | Find the route handler in `src/main.py` (FastAPI), `server/src/features/**/*.routes.ts` (Express), or `app/api/**/*.ts` (Next.js). |
| **Component** | Find the component file directly. Identify its data sources (props, hooks, context). |
| **DB table/model** | Find the schema definition. Trace forward to where it's queried. |
| **Feature name** | Search for the feature across the codebase. Identify the primary page/endpoint that implements it. Reclassify as one of the above. |

Store the resolved file path and line as `{anchor_file}` and `{anchor_line}`.

### 2. Walk Upstream (toward source)

From the anchor, trace data backward to its origin. At each boundary crossing, record a stage.

#### `python-fastapi-sse` upstream walk:

1. **Component** → Find `useEffect`/`fetch`/`EventSource` calls → identify API endpoint or SSE event
2. **API endpoint** → Read the route handler in `src/main.py` → find the function body
3. **Service/agent** → Follow function calls into `src/agent.py`, `src/tools/*.py` → find where data is produced
4. **Database** → Follow queries to `aiosqlite` calls → find the table/columns accessed
5. **External API** → If the tool calls an external service (Exa, crawl4ai, etc.), record that as the ultimate source

#### `express-react-drizzle` upstream walk:

1. **Component** → Find React Query hooks / `fetch` calls → identify API endpoint
2. **API route** → Read the route handler → find service function call
3. **Service** → Follow through service layer, `rowTo*` mappers → find Drizzle queries
4. **Schema** → Trace to `server/src/db/schema.ts` → find table/column definitions

#### `nextjs-prisma` upstream walk:

1. **Component** → Find `useQuery` / server component data fetching / server actions
2. **Server action / API route** → Read the handler → find Prisma queries
3. **Prisma schema** → Trace to `prisma/schema.prisma` → find model definition

### 3. Walk Downstream (toward render)

From the anchor, trace data forward to where it's rendered to the user.

#### `python-fastapi-sse` downstream walk:

1. **Database/tool** → Follow the return value through the agent/tool function
2. **API response** → Find how the data is serialized (Pydantic model → JSON, SSE event format, `progress_snapshot()`)
3. **Transport** → Identify the mechanism: REST response body, SSE `data:` field, WebSocket message
4. **Frontend fetch** → Find the `fetch`/`EventSource` call that receives it
5. **State** → Trace through React state (`useState`, `useReducer`, context, Zustand store)
6. **Render** → Find the JSX that displays the value to the user

#### `express-react-drizzle` downstream walk:

1. **Schema** → Follow column through Drizzle query → `rowTo*` mapper
2. **Service** → Follow return value through service function → route handler response
3. **Shared types** → Check type definition in `shared/src/types/`
4. **React Query** → Find the hook that fetches this endpoint
5. **Component** → Trace destructuring through component tree to JSX render

#### `nextjs-prisma` downstream walk:

1. **Prisma query** → Follow through server action/API route return
2. **Props/RSC** → Trace through server → client component boundary
3. **Client state** → Follow through hooks, context
4. **Render** → Find the JSX display

### 4. Identify Stages

A **stage** is a point where data:
- **Originates** (DB query, external API call, user input)
- **Transforms** (mapping function, Pydantic model, `rowTo*`, computed field)
- **Crosses a boundary** (backend → API response, SSE event → frontend, prop drilling, context)
- **Is consumed** (rendered in JSX, written to DB, sent to external service)

For each stage, record:

```
Stage {n}: {name}
  Layer: {source | model | service | transport | state | render}
  File: {file_path}:{line_number}
  Description: {what happens at this stage — one sentence}
  Shape in: {fields/type entering this stage}
  Shape out: {fields/type leaving this stage}
  Transforms: {what changes — field renames, type conversions, computed values, filtering}
```

### 5. Detect Branches and Joins

Data pipelines aren't always linear. Look for:

- **Branches:** A single source feeds multiple consumers (e.g., one API response used by three components)
- **Joins:** Multiple sources combine at one stage (e.g., component fetches from two endpoints)
- **Conditional paths:** Data takes different routes based on state (e.g., SSE events have different types)

Record branch/join points in the stage list with `branch_to: [stage_n, stage_m]` or `joins: [stage_x, stage_y]`.

### 6. Output Stage Map

Present the stage map to conversation context (not to a file — this is intermediate state):

```
## Stage Map: {anchor description}

Stack: {stack}
Anchor: {anchor_type} — {anchor_file}:{anchor_line}
Stages: {count}
Live server: {server_live}

### Pipeline

{stage_n} → {stage_n+1} → ... → {stage_final}

### Stage Details

Stage 1: {name}
  Layer: {layer}
  File: {file}:{line}
  Description: {description}
  Shape: {fields entering} → {fields leaving}
  Transforms: {what changes}

Stage 2: {name}
  ...

### Branches / Joins
{If any branches or joins were detected, describe them here}
```

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/trace-flow/steps/step-02-snapshot-data.md`.

---

## SUCCESS METRICS

- Anchor resolved to a concrete file:line in the codebase
- Upstream walk reached the ultimate data source (DB, external API, or user input)
- Downstream walk reached the final render point (JSX, or "not rendered" if the data stops before the UI)
- Every boundary crossing identified as a stage
- Shape in/out recorded for each stage with actual field names (not generic "data object")
- Branches and joins detected where data splits or merges
- Stage map presented with clear pipeline visualization

## FAILURE MODES

- Only walking one direction (e.g., tracing from DB forward but not checking if the component actually renders it)
- Missing intermediate transformations (e.g., a `rowTo*` mapper that renames fields)
- Recording stages at too high a level ("backend" → "frontend" instead of "DB query" → "Pydantic model" → "SSE event" → "useState" → "JSX render")
- Not detecting branches when one API response feeds multiple components
- Using the wrong stack's patterns (checking for Prisma in a FastAPI project)
- Guessing field names from types instead of reading the actual code
