---
name: 'step-04-converge'
description: 'Mandatory convergence: cluster themes, rank a shortlist, give ONE biased recommendation, write the session artifact'
---

# Step 4: Converge (Mandatory)

**Progress: Step 4 of 4** — Terminal.

## RULES — read before acting

- **The session MUST end decision-ready:** themes → ranked shortlist → ONE biased recommendation. A raw idea list is an unfinished session.
- **One recommendation, not a menu.** Rank the shortlist, then say which one you'd pursue and why. Alternatives live in the ranking, not in an option menu.
- **Write the artifact** from `template.md` — the session's durable output for downstream consumption.
- YOU MUST ALWAYS SPEAK OUTPUT in your agent communication style with the config `{communication_language}`.

## SEQUENCE OF INSTRUCTIONS

### 1. Cluster into themes

Group `{ideas}` into 2-4 themes (name + one-line pattern insight each). Every idea lands in exactly one theme; flag at most 1-2 as breakthrough outliers if genuinely orthogonal. Store the regrouped list as `{ideas_by_theme}`.

### 2. Rank the shortlist

Select and rank the top 3-5 ideas as `{shortlist}`, scored against `{grounding_summary}`'s constraints: impact on `{ask_target}`, feasibility given `{grounding_sources}`, and effort. One line of rationale per entry — cite the constraint that justifies the rank.

### 3. Give ONE biased recommendation

Set `{recommendation}`: which shortlist entry you'd pursue first and why, in 2-3 sentences. Answer-shape compliant — a verdict, not a hedge. If the honest answer is "none clear a bar worth acting on," say that plainly; a null recommendation is a valid verdict.

### 4. Decide the handoff consumer

Set `{handoff}` BEFORE writing the artifact: `quick-spec` if the recommendation is a code change; `design-router` if it implies a new/redesigned surface (design-router owns which design specialist runs — never pre-pick design-handoff or any other); `n/a` if the recommendation implies no action.

### 5. Write the session artifact

All template variables now exist (`{ask}`, `{ask_target}`, `{grounding_summary}`, `{grounding_sources}`, `{selected_techniques}`, `{idea_count}`, `{ideas_by_theme}`, `{shortlist}`, `{recommendation}`, `{handoff}`). Populate `template.md` and write to `{session_artifact_path}` (create `{session_artifact_dir}` if needed) in `{document_output_language}`. Fill every `{{variable}}` — writing with an unfilled placeholder is a failure. The artifact must stand alone for a reader who wasn't in the session.

### 6. Deliver — verdict first

Close the session in answer-shape:

1. **The recommendation** (lead with it).
2. The ranked shortlist, one line each.
3. Artifact path.
4. **Handoff line (when `{handoff}` ≠ `n/a`):** ONE line naming the consumer and offering or invoking it. The artifact's Recommendation + Shortlist sections are the consumer's input.
5. **Escalation aside (only if §2 ranking showed the space is genuinely rich beyond 30 ideas):** one default-no line — *"The space runs deeper than the quick pass — the full core `brainstorming` workflow (`/bmad:core:workflows:brainstorming`) is there if you want a 100+ idea session; not recommending it unless the shortlist misses."* Omit entirely when the shortlist covers the space.

---

## SUCCESS METRICS

- Themes, ranked `{shortlist}` (3-5), and ONE `{recommendation}` produced
- Artifact written to `{session_artifact_path}` with no unfilled placeholders
- Delivery led with the recommendation; escalation aside only when earned, phrased default-no

## FAILURE MODES

- Ending on "here are your ideas organized by theme!" with no ranking or recommendation
- Presenting the shortlist as an option menu ("which would you like to pursue?")
- Escalating to the core workflow as a routine closer instead of an earned, default-no aside
- An artifact that references the chat ("as discussed above") instead of standing alone
