# EGM dry run (ORDER 001), 2026-11-16 06:45 UTC / 12:15 IST
Skill used: egm:egm-review-loop (started through the Skill tool). Round 1 of max 1. Reviewers: egm:egm-style and egm:egm-comprehension, direct dispatch, both model sonnet. Target: egm-dryrun-target.md (3 lines). Standard: egm-dryrun-standard.md.
Not done on purpose: no fixes applied to the test paragraph, no egm-resolve run (dry run proves the reviewers run; the paragraph is deliberately bad). Not a converged review: only 1 round, as ordered.

## Result: both reviewers ran (status completed), the paragraph FAILS the standard
Findings merged (ids style-1-n, comprehension-1-n):
| Line | Severity | Finding | Raised by |
|---|---|---|---|
| 1 | Blocker | "gate" and "queue" unexplained; "checks" says no pass/fail rule | style, comprehension |
| 2 | Blocker | "Mistakes are handled" hides who acts; "window", "receipt", "bank" each have two readings | style, comprehension |
| 3 | Blocker | "the thing is secured" vague passive, no referent; "approval" and "unclear" undefined; two ideas joined by "and" | style, comprehension |
| 1-3 | Major | No shared subject; no flow from invoice arrival to outcome | style, comprehension |
| 1-3 | Major | No sentence says who does what to whom | comprehension |
| 2 | Major | "Mistakes" has no scope | style |
| 3 | Nit | "thing" is filler; "look" is vague | style, comprehension |
| 1-3 | Nit | Terms not kept to one meaning | comprehension |
Totals: 3 Blockers, 3 Majors, 3 Nits after merging duplicates. This is the expected outcome for the planted bad wording, so the reviewers do catch what the standard names.
