---
stepsCompleted: []
inputDocuments: []
---

# {{project_name}} - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for {{project_name}}, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

{{fr_list}}

### NonFunctional Requirements

{{nfr_list}}

### Additional Requirements

{{additional_requirements}}

### FR Coverage Map

{{requirements_coverage_map}}

## Epic List

{{epics_list}}

<!-- Repeat for each epic in epics_list (N = 1, 2, 3...) -->

## Epic {{N}}: {{epic_title_N}}

{{epic_goal_N}}

<!-- Outcome DoD is EPIC-LEVEL, nested (###) so the epic's story list stays inside its ## span. This is the epic's end-to-end acceptance test, NOT a restatement of story ACs. -->

### Outcome DoD

Goal: {{epic_outcome_goal_N}}

Proven-when:

| Flow | Trigger | Expected observable | How to verify |
|------|---------|---------------------|---------------|
| {{flow_name}} | {{real_input}} | {{real_output_or_side_effect}} | {{check_command}} |

Rot-guard: This section must stay end-to-end acceptance only. Do NOT copy per-story ACs here. If it starts listing story acceptance criteria, it is wrong — delete and rewrite.

<!-- Repeat for each story (M = 1, 2, 3...) within epic N -->

### Story {{N}}.{{M}}: {{story_title_N_M}}

As a {{user_type}},
I want {{capability}},
So that {{value_benefit}}.

**Acceptance Criteria:**

<!-- for each AC on this story -->

**Given** {{precondition}}
**When** {{action}}
**Then** {{expected_outcome}}
**And** {{additional_criteria}}

<!-- End story repeat -->
