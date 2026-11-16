Status: resolved (round 1 of 2), 2026-11-16 08:39 UTC (14:09 IST)
# Resolve report, ORDER 007 review round 1 (egm:egm-resolve, run by the main session)
Inputs: zoom-out report (agent a577d18e9204efeb3: M1-M4, N1, Q2-Q5) and codebase-details report (agent a390bf5b8417b9bee: Majors 1-7, Nits 8-17). Both are reviewer words, unverified until checked; I checked each against the files before acting. Lead instruction: no questions; PROPOSE FIX for valid findings; CONTEST only with evidence. Reviewers could not run n8n; neither could I, so nothing below is verified in n8n.
Counts: reviewer findings grouped into the lines below: PROPOSE FIX 18 lines, CONTEST 1 (line 11), DECLINE 2 (lines 15, 24), ESCALATE 1 (line 25).

| # | Source | Sev | Decision | What I did (file) |
|---|---|---|---|---|
| 1 | ZO M1, CB 1 | Major | PROPOSE FIX | Applied the one rule to all rows. Demoted to Nit (after the video, each says "a Major for a client build"): F-014 (F-040 merged in), F-019, F-035, F-036, F-039, F-044, F-045. Counts recomputed by script: 45 rows = 8 Blocker, 9 Major, 28 Nit; BEFORE 18, AFTER 27. This goes beyond the lead's list; flagged as Q9 in QUESTIONS.md. (FINDINGS.md) |
| 2 | ZO M2, CB 7 | Major | PROPOSE FIX | F-040 merged into F-014; giving-up mail dropped; order stated: F-035 watchdog first, then the cap; duplicated "why not Blocker" sentence removed. (FINDINGS.md, FIX-PLAN.md) |
| 3 | ZO M3 | Major | PROPOSE FIX | F-037, F-029, F-018 now say "rated together, one gate (FIX-PLAN item 3)" and explain why F-037 is Blocker and F-029 Major; gate fix kinds set to config. |
| 4 | ZO M4 | Major | PROPOSE FIX | One Nit definition in the rubric text; F-028 explained (Nit by content, BEFORE because the text sits in filmed files); the "take" column defined as "file is in the take"; a Scenes paragraph says plainly that F-002 is a Blocker by the lead's order until T19 and T20 pass and that I found no scene for F-007 and F-031. |
| 5 | ZO N1 | Nit | PROPOSE FIX | Table sorted BEFORE first, then severity. |
| 6 | ZO Q2, CB 5 | Major | PROPOSE FIX | CUT-LIST: desk-error-notifier.json taken off the archive list (2 files move, KEEP the notifier). |
| 7 | ZO Q2 | Major | PROPOSE FIX | F-041 pointers fixed (FIX-PLAN items 8 and 10); F-046 pointer fixed; F-011 now says four roles. |
| 8 | ZO Q2 | Major | PROPOSE FIX | Estimate re-based to 2 to 3 working days, marked "an estimate, not measured". |
| 9 | ZO Q2 Nits | Nit | PROPOSE FIX | FIX-PLAN item 7 no longer names F-020/F-041; CUT-LIST says the lead checks that the raw result file landed; LEDGER-ROWS regenerated from FINDINGS (45 rows, all 10 columns, summary from the bold title). |
| 10 | ZO Q3 | Major | PROPOSE FIX | QUESTIONS.md: Q3 marked answered (ORDER 012); new Q4 to Q9 with recommendations; Q4 says the one-database wording is the lead's Reading A and asks for confirmation. Verdict row 2b relabelled "NEEDED for a client build"; row 6 "AVOIDS A DUPLICATE". |
| 11 | ZO Q4 F-002 | Major | CONTEST | Lighter route (CHECK constraint on lead_key plus only the Claim error output) rejected: a bad key would get 503 "retry" instead of 422 "never retry", so the sender resends a key that can never work. Evidence: PLAN-4-NLITE-FROM-LEAD.md:47 resend rule; reason written into the F-002 row. Severity not changed. |
| 12 | ZO Q4 F-023 | Major | PROPOSE FIX | F-023 and FIX-PLAN item 7: do not run the table screen; pick the scene 10 fallback now; the three README texts say "NOT run in n8n". |
| 13 | ZO Q4 Nits, Q5 | Nit | PROPOSE FIX | F-035 now [code]; F-036 [config, needs a reverse proxy]; F-044 states which part is config and which is n8n node; F-002 states the generator change; F-031 says the sentence discloses the gap but does not close it. |
| 14 | ZO Q4 readability | Major | PROPOSE FIX | "rung" replaced by "fix kind" everywhere; Words used now defines fix kind, BM, onError, continueErrorOutput, alwaysOutputData, continueRegularOutput, K1-K5, M0, M1, T17-T21 and the proposed T-tests; NOT-COVERED heading says which items could break the take. |
| 15 | ZO Q4 "plain summary first" | Nit | DECLINE | Every long row already starts with a bold one-sentence summary. |
| 16 | CB 2, 16 | Major | PROPOSE FIX | One conditioned paste now sits in EXCEPTIONS.md ("One-database wording", with the ORDER 012 owner and trigger filled in); F-011, F-019, F-020 point to it instead of three present-tense copies; "item 6" corrected. |
| 17 | CB 3 | Major | PROPOSE FIX | F-008 row and FIX-PLAN item 4 now list N8N-START.md lines 15-27 and DESIGN-A-README.md line 23 as edits ("ON for the take only"). |
| 18 | CB 4 | Major | PROPOSE FIX | Cite corrected to build_mainframe.py:114 (F-002 row, evidence-7a.md); T19 pass line (reply to POST 2 in under 10 s, one mail); fallback written. |
| 19 | CB 6 | Major | PROPOSE FIX | F-029 gate adds PG_CREDENTIAL_ID and SMTP_CREDENTIAL_ID (FIX-PLAN item 3). |
| 20 | CB 8-12, 14, 17 | Nit | PROPOSE FIX | "does not trim"; sender-contract note; key-shape floor note; "11 columns" removed (F-043, verdict row 3); F-004 patch statement 17 points to line 157; N7 citations fixed (RUN-ON-LAPTOP.md:67, ORDER 007 "item 6" claim withdrawn, "15 different places", M0/M1 at :119-138); "(planned, not built)" added. |
| 21 | CB 13 | Nit | PROPOSE FIX | check_patches re-run on the current files: raw output in lanes7/evidence-7b-check-patches.txt (PASS 5 patches, exit 0). evidence-7a.md stays a typed summary and says so here. |
| 22 | CB 15 | Nit | PROPOSE FIX | The UNVERIFIED words removed from the comment inside the F-008 patch (one line changed, hunk counts unchanged; check_patches passes). |
| 24 | ZO "order NOT-COVERED by risk" | Nit | DECLINE | Kept the number order; added the "could break the take" sentence instead. |
| 25 | ESCALATE | | Q4 to Q9 | Lead decisions: one-database wording, approval or audit words, CRM claim, review rows, table screen, my extra demotions. |

Not done and why: nothing here ran in n8n or Postgres (impossible now: not installed; next step is the laptop run T17-T21). I did not re-run the F-002 rebuild diff after the review fixes: the F-002 patch itself did not change, only text rows and two comment lines in other patches; check_patches (apply + JSON parse) was re-run and passed.
