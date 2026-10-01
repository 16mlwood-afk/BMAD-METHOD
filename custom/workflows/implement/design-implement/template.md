---
status: '{{status}}'
date: '{{date}}'
page: '{{page_name}}'
design_url: '{{design_url}}'
design_file: '{{design_file}}'
baseline_commit: '{{baseline_commit}}'
delta_count: '{{delta_count}}'
fixed_count: '{{fixed_count}}'
---

# Design Implementation Grid — {{page_name}}

**Design source:** `{{design_file}}` from `{{design_url}}`
**Implementation page:** `{{impl_page}}`
**Date:** {{date}}

---

## Token Resolution

### Design Tokens

| Category | Token | Value |
|----------|-------|-------|
{{design_token_rows}}

### Tailwind Config Overrides

| Tailwind Class | Default | Project Override | Actual |
|---------------|---------|------------------|--------|
{{tailwind_override_rows}}

---

## Page Shell

_Mandatory row (step-03 §2d) — the page container's width/centering/padding, which no component owns and the full-bleed bundle can't supply. Design column from `{design_layout_constraints}` (README prose + bundle wrapper); Implementation column from `{impl_page_shell}` (effective width after every nested layout cap). A width/centering mismatch is Tier-1._

| Property | Design | Implementation | Delta |
|----------|--------|----------------|-------|
| container width | {{design_shell_width}} | {{impl_shell_effective_width}} | {{shell_width_delta}} |
| centering | {{design_shell_centered}} | {{impl_shell_centered}} | {{shell_centered_delta}} |
| horizontal padding | {{design_shell_padding}} | {{impl_shell_padding}} | {{shell_padding_delta}} |

{{#if shell_convention_divergence}}> Convention note: {{shell_convention_divergence}}{{/if}}

---

## Component × Property Comparison Grid

{{#each component}}
### {{component_name}}

**Design file:** `{{design_component_path}}`
**Implementation file:** `{{impl_component_path}}`

| Property | Design | Implementation | Delta |
|----------|--------|----------------|-------|
{{property_rows}}

{{/each}}

---

## Delta Summary

| Tier | Count | Description |
|------|-------|-------------|
| Tier 1 — Structural | {{tier1_count}} | Missing components, wrong grid structure, content changes |
| Tier 2 — Visual | {{tier2_count}} | Border radius, font size, padding, width, color |
| Tier 3 — Micro | {{tier3_count}} | Font weight, letter spacing, minor padding |
| **Total** | **{{delta_count}}** | |

## Fix Log

| # | Component | Property | Was | Now | Status |
|---|-----------|----------|-----|-----|--------|
{{fix_log_rows}}

**Fixed:** {{fixed_count}}/{{delta_count}} deltas
