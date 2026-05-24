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
