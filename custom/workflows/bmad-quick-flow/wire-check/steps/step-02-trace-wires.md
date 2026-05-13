---
name: 'step-02-trace-wires'
description: 'For each wire in the inventory, verify the full chain: source produces → transport carries → sink consumes and renders'

nextStepFile: './step-03-report.md'
---

# Step 2: Trace Each Wire

**Goal:** For every wire in the inventory, read the actual code at each layer and verify the data flows end-to-end. Classify each wire as connected, loose, or mismatched.

---

## AVAILABLE STATE

From step 1:

- `{handoff_path}` — Handoff artifact path
- `{wires}` — Wire inventory with source/transport/sink for each field
- `{baseline_commit}` — Reference commit (if available)
- `{stack}` — Auto-detected project stack

---

## EXECUTION SEQUENCE

For each wire, perform these checks **by reading the actual code** (not by assumption):

### Check 1: Source Produces the Value

Read the source file at the identified line. Verify:

- [ ] The field/counter is actually populated (not just declared)
- [ ] The value type matches what downstream expects (string vs number vs array vs object)
- [ ] The value is produced in all code paths (not just one branch of an if/else)

**Common source failures by stack:**

#### `express-react-drizzle`

- Column added to Drizzle schema but migration not created or not applied
- `rowTo*` mapper skips the new column (field exists in DB but never reaches the API response)
- JSONB column with no `DEFAULT` — existing rows return `null`, frontend expects `[]` or `{}`
- Zod schema for create/update doesn't include the new field — API silently strips it from requests

#### `python-fastapi-sse`

- Counter increments inside a condition that never matches (e.g., `isinstance(data, list)` when data is always a string)
- Field exists on a Pydantic model but is never assigned a non-default value
- Value produced only in non-reduced mode but consumed unconditionally

#### `nextjs-prisma`

- Field added to Prisma schema but `prisma generate` not run — TypeScript types stale
- Server action's Prisma query uses `select` that excludes the new field
- Field present in server component but not forwarded to client component via props

### Check 2: Transport Carries the Value

Trace from source to the transport mechanism. Verify:

- [ ] The value reaches the API response / SSE event / server action return
- [ ] The key name in the transport matches what the sink expects (case-sensitive, exact match)
- [ ] The serialization preserves the type (e.g., Date → ISO string, JSONB → object, not double-serialized string)

**Common transport failures by stack:**

#### `express-react-drizzle`

- Service function maps the field but Zod schema for the route strips it (validation runs on both input AND output if using `.parse()` on responses)
- `rowTo*` casts JSONB to wrong TypeScript type — `as string[]` on data that's actually `null`
- Shared type updated but `shared/dist/` not rebuilt — frontend sees stale types (especially in worktrees without `worktree-setup.sh`)
- Field name uses `snake_case` in DB but `camelCase` in shared type — mismatch in the `rowTo*` mapper

#### `python-fastapi-sse`

- Counter tracked in `_ChunkProcessor` but not included in `progress_snapshot()` dict
- Field name mismatch: backend sends `search_results`, frontend expects `searchResults`
- Conditional inclusion: `if self.x > 0: data["x"] = self.x` — sink gets `undefined` when value is 0
- SSE event type mismatch: value emitted as `progress` but frontend listens for `update`

#### `nextjs-prisma`

- Server action returns `{ data }` but client destructures `{ result }` — no TypeScript error if using `any`
- `revalidatePath` not called after mutation — cached data stale until hard refresh
- Prisma `include` in one query but not another — field available on detail page but missing from list

### Check 3: Sink Consumes and Renders

Read the frontend code. Verify:

- [ ] The sink destructures or accesses the exact key name from the transport
- [ ] The value is actually rendered in JSX (not just stored in state and ignored)
- [ ] The display handles the value's actual type (e.g., doesn't call `.toFixed()` on undefined)
- [ ] Fallback/default values are reasonable (e.g., `?? 0` not `?? "—"` for a numeric counter)

**Common sink failures by stack:**

#### `express-react-drizzle`

- React Query hook fetches the data but component destructures the wrong key from the response wrapper (`data.data.field` vs `data.field`)
- Component renders `{value || "—"}` which shows "—" for the number `0` or empty array `[]`
- `useMutation` invalidates the list query but not the detail query (or vice versa) — stale UI after update
- Optional chaining `?.` masks a genuine null — renders nothing instead of a fallback

#### `python-fastapi-sse`

- Frontend reads `data.search_results` but backend sends `data.search_results_count`
- Component renders `{value || "—"}` which shows "—" for the number 0
- State initialized but never updated from SSE events
- Value displayed in one view (e.g., detail panel) but not another (e.g., live signals)

#### `nextjs-prisma`

- Server component passes data to client component but forgets to serialize (Date objects, Decimal types)
- `useOptimistic` hook initialized with wrong shape — rollback on error shows broken state
- Suspense boundary catches the right error but fallback doesn't render the cached value

### Check 4: Dead Export Verification

For wires flagged as "potentially dead" in step 1:

- [ ] `grep -rn "EXPORT_NAME"` across the entire `client/` and `server/` dirs (not just modified files)
- [ ] If zero consumers found outside the definition file → confirmed dead
- [ ] If consumers found → reclassify as connected and remove from issues

### Check 5: Outbound Payload Drift

For every outbound payload wire identified in step 1 (webhooks, external API forwards, exports):

- [ ] Read the **source model** (the Pydantic model, Drizzle schema, or Prisma model that owns the data)
- [ ] Read the **payload builder** (the function that constructs what gets sent outbound)
- [ ] Compare the fields: list every field on the source model that is **not** included in the outbound payload
- [ ] Classify the gap: is each missing field (a) intentionally excluded, (b) an oversight from a recent model expansion, or (c) not relevant to the outbound consumer?

**Why this matters:** When a model is expanded (new fields added), the frontend sink gets updated in the same PR, but outbound payloads (webhooks, external APIs) are a separate serialization path that is easy to forget. The result is **silent drift** — the outbound consumer sees a frozen schema while the rest of the system evolves. This is invisible until the outbound consumer needs the new data and discovers it was never sent.

**Common drift patterns by stack:**

#### `python-fastapi-sse`
- `WebhookPayload` / `build_payload()` manually maps fields from a domain model — new fields on the domain model don't automatically appear in the webhook
- `model_dump()` / `model_dump_json()` on a subset model (not the full domain model) — the subset was defined before the expansion

#### `express-react-drizzle`
- Webhook handler constructs a plain object from `rowTo*` output, cherry-picking fields — new columns are excluded
- Zod schema on the outbound payload acts as a whitelist — new fields stripped by validation

#### `nextjs-prisma`
- Server action or API route that forwards data to a third-party service uses a Prisma `select` that predates the schema change
- Webhook handler uses a TypeScript `Pick<>` type that doesn't include new fields

**Classification:**

| Gap type | Action |
|---|---|
| **Drift** — field added to source model after payload builder was written, clearly relevant to outbound consumer | Flag as **Loose** wire with fix suggestion |
| **Intentional** — field is internal-only or not relevant to the outbound consumer | Note as acknowledged, no fix needed |
| **Ambiguous** — unclear whether the consumer needs it | Flag for product decision |

---

## CLASSIFICATION

After tracing, classify each wire:

| Status         | Meaning                                                                                                          |
| -------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Connected**  | All checks pass — data flows end-to-end                                                                          |
| **Loose**      | Chain breaks at a specific point (source OK but transport drops it, or transport OK but sink doesn't consume it) |
| **Mismatched** | Data flows but format/type/name doesn't match between layers                                                     |
| **Dead**       | Value never produced, export never consumed, or counter never increments                                         |
| **Drifted**    | Outbound payload sends a frozen subset of a model that has since been expanded — silent schema divergence         |

For each non-connected wire, record:

```
Wire: {field_name}
Status: {Loose|Mismatched|Dead}
Break point: {layer where it fails}
Details: {what specifically is wrong, with file:line references}
Fix suggestion: {one-line description of what to change}
```

Store all findings as `{findings}`.

---

## NEXT STEP

Proceed immediately to `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/wire-check/steps/step-03-report.md`.

---

## SUCCESS METRICS

- Every wire traced through all layers (source, transport, sink)
- Stack-appropriate failure patterns checked (not Python patterns on an Express project)
- Each wire classified with a status
- Non-connected wires have specific break points with file:line
- Fix suggestions are concrete and actionable
- No wire assumed "connected" without reading the actual code at each layer
- Outbound payload wires checked for drift against their source models

## FAILURE MODES

- Checking only one direction (backend → frontend) without verifying the sink actually uses the value
- Assuming key names match without reading both sides
- Using the wrong stack's failure patterns (e.g., checking for `progress_snapshot()` in Express)
- Not checking conditional inclusion logic (the `if x > 0` / `?? []` pattern)
- Marking a wire as "connected" because the variable exists, without verifying it's populated
- Skipping dead export verification because "it's just a constant"
- **Not checking outbound payloads (webhooks, external APIs, exports) when a model is expanded** — the frontend gets updated but the webhook silently sends stale data. This is the most common source of cross-system drift.
