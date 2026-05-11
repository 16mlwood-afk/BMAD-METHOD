---
name: detect-stack
description: 'Shared utility — detects the project tech stack from project files. Referenced by any workflow that needs stack-aware behavior.'
---

# Detect Stack

**Purpose:** Identify the project's tech stack by inspecting files in the project root. Returns a `{stack}` identifier that other workflows use to select stack-specific patterns.

**Usage:** Any workflow step can reference this file:

```
Read and follow: `{project-root}/_bmad/bmm/workflows/shared/detect-stack.md`
```

The result is stored as `{stack}` in the workflow's state variables.

---

## DETECTION RULES

Run these checks in order — **first match wins**:

### `express-react-drizzle`

All of:

- `server/` and `client/` directories exist
- `drizzle-orm` appears in any `package.json` dependencies, OR `server/src/db/schema.ts` exists

**Layers:** DB schema (Drizzle) → shared types → Express routes (Zod) + service layer → React hooks + components

### `python-fastapi-sse`

All of:

- `pyproject.toml` or `requirements.txt` exists
- Contains `fastapi` as a dependency

**Layers:** Pydantic models + agent state → SSE streaming / API endpoints → React/frontend components

### `nextjs-prisma`

All of:

- `prisma/schema.prisma` exists
- `app/` directory exists OR a `next.config.*` file exists

**Layers:** Prisma schema → API routes / server actions (Zod) → React server + client components

### `unknown`

No signals matched. The calling workflow should inspect the diff's file paths and adapt its layer table to what it observes. Log the detection result so the user can add a new stack profile if needed.

---

## QUICK DETECTION SCRIPT

For workflows that want a one-shot answer:

```bash
if [ -d server ] && [ -d client ] && (grep -q "drizzle-orm" package.json 2>/dev/null || grep -q "drizzle-orm" server/package.json 2>/dev/null || [ -f server/src/db/schema.ts ]); then
  echo "express-react-drizzle"
elif ([ -f pyproject.toml ] && grep -q "fastapi" pyproject.toml 2>/dev/null) || ([ -f requirements.txt ] && grep -q "fastapi" requirements.txt 2>/dev/null); then
  echo "python-fastapi-sse"
elif [ -f prisma/schema.prisma ] && ([ -d app ] || ls next.config.* 2>/dev/null); then
  echo "nextjs-prisma"
else
  echo "unknown"
fi
```

---

## EXTENDING

To add a new stack:

1. Add a detection rule section above (before `unknown`)
2. Add the corresponding layer table to `wire-check/steps/step-01-map-wires.md`
3. Add stack-specific failure patterns to `wire-check/steps/step-02-trace-wires.md`
4. Sync to all projects that use the wire-check workflow
