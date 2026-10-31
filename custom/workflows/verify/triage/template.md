---
title: 'Triage: {{observation_summary}}'
created: '{{date}}'
source: 'triage workflow'
type: triage-report
observation_type: '{{observation_type}}'
issues_found: {{issue_count}}
resolved_inline: {{resolved_count}}
routed: {{routed_count}}
---

# Triage: {{observation_summary}}

**Observation:** {{observation}}
**Page/Feature:** {{page_context}}
**Date:** {{date}}

## Investigation Summary

{{investigation_summary — what was queried, key data points, how many records examined}}

## Diagnosed Issues

{{For each issue, repeat this block:}}

### Issue {{n}}: {{title}} — {{category}}

- **Root cause:** {{root_cause}}
- **Category:** {{category}}
- **Severity:** {{severity}}
- **Scope:** {{scope}}
- **Affected:** {{count and description of affected records}}
- **Evidence:** {{key finding(s) supporting this diagnosis}}
- **Resolution:** {{resolved-inline | routed-to-quick-dev | routed-to-design | routed-to-story | documented}}

{{If resolved inline:}}
**Fix applied:** {{what was done}}
**Verified:** {{how the fix was confirmed}}

{{If routed:}}
**Artifact:** {{path to handoff artifact}}
**Next:** {{slash command to trigger downstream workflow}}

## Resolution Summary

| Issue | Category | Severity | Resolution | Artifact |
|-------|----------|----------|------------|----------|
{{table row for each issue}}

## Next Steps

{{Numbered list of downstream workflow commands to run, in recommended order}}

{{If all issues were resolved inline:}}
All issues resolved in-session. No downstream workflows needed.
