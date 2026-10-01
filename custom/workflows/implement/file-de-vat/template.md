---
title: 'German VAT Filing Receipt — {{period}}'
period: '{{period}}'
filed_date: '{{filed_date}}'
confirmation_ref: '{{confirmation_ref}}'
workflow: file-de-vat
status: filed
---

# German VAT Filing Receipt — {{period}}

## Submission

| Item | Value |
|------|-------|
| Period | {{period}} |
| Submitted at | {{filed_date}} |
| Portal confirmation | {{confirmation_ref}} |
| Invoices included | {{invoice_count}} |
| Uploads | {{upload_count}} ({{upload_names}}) |

## Return figures

<!-- One row per rate/box as entered in the portal. Figures only — commentary goes in Notes. -->

| Line | Amount |
|------|--------|
{{return_figure_rows}}

## Missing data

<!-- Every n/a value from the session, or "none". Never blank. -->

{{missing_data_list}}

## Notes

<!-- Caveats, overrides taken (e.g. filed outside the 4th–8th window), validation flags carried, and the amendability status at time of filing. -->

{{notes}}

## Session trail

| Phase | Outcome |
|-------|---------|
| 1 Pre-flight | {{preflight_outcome}} |
| 2 Data pull | {{datapull_outcome}} |
| 3 Validation | {{validation_outcome}} |
| 4 Portal fill | {{portalfill_outcome}} |
| 5 Human review | approved by {{approver}} at {{approval_time}} |
| 6 Submit | {{submit_outcome}} |
| 7 Receipt | this document |
