# Step 2: Gather Visual Intent

## MANDATORY EXECUTION RULES (READ FIRST):

- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`
- Gather input through structured questions, not open-ended conversation
- If the user says "I don't know" or "I'm not sure" to 2+ questions, set `{brainstorm_needed}` = "yes" and proceed to step-03
- In autonomous mode: infer answers from the codebase, product type, and user context. Set `{brainstorm_needed}` = "no" unless the signals are genuinely ambiguous.

## CONTEXT BOUNDARIES:

- Findings from step-01 are available (existing policy, brand identity, codebase scan)
- If brand identity exists, pre-populate answers and ask for confirmation rather than re-asking
- The goal is to understand WHAT the user wants — not to design anything yet

## YOUR TASK:

Gather the inputs needed to write a design policy. There are 7 dimensions to capture.

## GATHERING SEQUENCE:

### 1. Product Type

**Question:** "What kind of product is this?"

Offer categories if the user isn't sure:
- **Operations tool** — users process work (orders, invoices, tickets, shipments)
- **Analytics platform** — users understand data (dashboards, reports, trends)
- **Workflow manager** — users move items through stages (pipelines, kanban, approvals)
- **Data entry / forms** — users input structured data (CRM, ERP, accounting)
- **Hybrid** — multiple of the above

Set `{product_type}` from the answer.

### 2. User Role

**Question:** "Who are the primary users, and what's their context?"

Guide with:
- What is their job title / function?
- Are they power users (use this daily) or occasional users?
- Do they work under time pressure?
- Do they make financial/consequential decisions from this data?

Set `{user_role}` from the answer.

### 3. Tone / Emotional Register

**Question:** "What should this product FEEL like to use?"

If the user struggles, offer anchors:
- **Precise & restrained** — like a financial terminal. Data-dense, serious, minimal decoration.
- **Clean & approachable** — like a modern SaaS tool. Generous spacing, friendly without being playful.
- **Efficient & utilitarian** — like a logistics console. Dense, scannable, action-oriented.
- **Premium & polished** — like enterprise software. Sophisticated typography, restrained palette, refined details.

Set `{tone}` from the answer.

### 4. Reference Products

**Question:** "Name 2-3 products whose visual approach you admire — and be specific about WHAT you'd borrow from each."

Examples to prompt with:
- "Linear's density and restraint"
- "Stripe Dashboard's typography and whitespace"
- "Notion's simplicity and content-first approach"
- "Bloomberg Terminal's data density"
- "Shopify Admin's operational clarity"

Set `{reference_products}` from the answer.

### 5. Anti-References

**Question:** "What should this product NEVER look like?"

Examples to prompt with:
- "A startup landing page"
- "A colorful consumer app"
- "A generic Bootstrap admin template"
- "An over-designed portfolio piece"
- "A dated enterprise system from 2010"

Set `{anti_references}` from the answer.

### 6. Operational vs Analytical Bias

**Question:** "When users open this app, are they primarily here to DO things (process orders, approve items, take actions) or UNDERSTAND things (analyze trends, compare metrics, spot patterns)?"

- **Operational** — tables, queues, action buttons, status transitions
- **Analytical** — charts, comparisons, filters, drill-downs
- **Hybrid** — both, with operational as the primary mode

Set `{operational_bias}` from the answer.

### 7. Uncertainty Check

If the user answered "I don't know" or was vague on 2+ dimensions:
- Set `{brainstorm_needed}` = "yes"
- Tell the user: "You're not sure about some of these — that's normal. I'll run a brainstorming mode that presents 2-4 plausible visual directions for your product type. You'll pick the closest one, and we'll refine from there."

If the user had clear answers for all dimensions:
- Set `{brainstorm_needed}` = "no"
- Synthesize the answers into a one-paragraph `{visual_direction}` statement

## NEXT STEP:

**If `{brainstorm_needed}` = "yes":**
Proceed to `{project-root}/_bmad/bmm/workflows/design/create-design-policy/steps/step-03-brainstorm-directions.md`.

**If `{brainstorm_needed}` = "no":**
Skip step-03 and proceed directly to `{project-root}/_bmad/bmm/workflows/design/create-design-policy/steps/step-04-write-policy.md`.
