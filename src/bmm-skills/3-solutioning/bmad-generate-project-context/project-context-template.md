---
project_name: '{{project_name}}'
user_name: '{{user_name}}'
date: '{{date}}'
sections_completed: ['product_concept', 'technology_stack']
existing_patterns_found: { { number_of_patterns_discovered } }
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Product Concept & End-to-End Flow

_Read this BEFORE reasoning about tasks or tickets. The task tracker (sprint board / story files) tells you what is BUILT — never what the product IS. Derive the concept from here + the brief / PRD / architecture, never from the tracker alone._

**One line:** _{{one_line_concept}}_

**Value flow & spine:** _{{end_to_end_flow}}_ — the value stream(s) and the single intake spine that feeds them.

**Cause / effect — do not invert:** _{{which_events_are_pipeline_OUTPUTS_vs_INPUTS}}_ — name the events that are OUTPUTS of the pipeline running, so an agent never mistakes a downstream output for an upstream precondition.

**Forbidden agent behaviours:**

- Never infer the product concept from the task tracker / tickets alone — ground in this concept + brief + PRD + architecture first.
- Never invert the pipeline's cause/effect (treat a downstream output as if it were a precondition).
- _{{project_specific_forbidden_behaviours}}_

## Technology Stack & Versions

_Documented after discovery phase_

## Critical Implementation Rules

_Documented after discovery phase_
