# EGM dry run (ORDER 001): review of a 3-line made-up paragraph
Run: 2026-11-16 06:44 UTC (12:14 IST). Input: handover/core-hardening/egm-dryrun-input.md (not edited).
Skill: egm:egm-review-loop, direct dispatch, round 1 only. Reviewers: egm:egm-structural and egm:egm-style, both Agent calls with model sonnet. Reports below are the reviewers' findings, condensed.

## Structural (egm:egm-structural): 0 Blocker, 0 Major, 4 Nit
1. Nit, line 1-2: no blank line after the heading.
2. Nit, lines 2-3: hard-wrapped lines, inconsistent wrap.
3. Nit, line 1: heading names no subject (fine for a test file).
4. Nit, whole file: none of the feature-spec sections exist. Reviewer downgraded from Major because the text is a behaviour note, not a spec.

## Style (egm:egm-style): 0 Blocker, 3 Major, 4 Nit
Major 1 (lines 2-3): "too big", "busy", "bad" have no limit, unit or definition; no retry count or what happens when retries run out.
Major 2 (line 3): "skipped" does not say whether the run continues or the exit code; which log and what the note holds is not named; "a person can look at it later" names no person or step.
Major 3 (line 2): two different "it" in one sentence; use "the tool".
Nits: "the store" undefined; passive voice on line 3; heading names no subject; the tool is not named.

## Result
Both reviewer agents ran and returned reports: EGM review path works from this session.
Not done (dry run scope): egm:egm-resolve was not run and no fixes were applied, so the loop did not reach "converged" (needs two clean rounds). Only round 1 ran. The findings are expected, because the paragraph is deliberately vague.
