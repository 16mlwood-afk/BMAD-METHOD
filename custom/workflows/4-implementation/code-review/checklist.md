# Senior Developer Review - Validation Checklist

## Guard Rails

- [ ] Git state verified (commits exist OR user chose fallback scoping strategy)
- [ ] Review scoped to story-relevant files (not entire repository)
- [ ] File read count within limit (max 10 per pass, or user override)
- [ ] Progress checkpoint output produced after each step

## Story Loading

- [ ] Story file loaded from `{{story_path}}`
- [ ] Story Status verified as reviewable (review)
- [ ] Epic and Story IDs resolved ({{epic_num}}.{{story_num}})
- [ ] Story Context located or warning recorded
- [ ] Epic Tech Spec located or warning recorded
- [ ] Architecture/standards docs loaded (as available)
- [ ] Tech stack detected and documented
- [ ] MCP doc search performed (or web fallback) and references captured

## Review Execution

- [ ] Acceptance Criteria cross-checked against implementation
- [ ] File List reviewed and validated for completeness
- [ ] Tests identified and mapped to ACs; gaps noted
- [ ] Code quality review performed on changed files
- [ ] Stack-specific anti-pattern checks performed (via shared/detect-stack.md)
- [ ] Security review performed on changed files and dependencies

## Completion

- [ ] Outcome decided (Approve/Changes Requested/Blocked)
- [ ] Review notes appended under "Senior Developer Review (AI)"
- [ ] Change Log updated with review entry
- [ ] Status updated according to settings (if enabled)
- [ ] Sprint status synced (if sprint tracking enabled)
- [ ] Story saved successfully

_Reviewer: {{user_name}} on {{date}}_
