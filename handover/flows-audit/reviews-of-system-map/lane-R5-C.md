# R5-C (egm-comprehension, sonnet): naive reader of ONE-PLACE-TABLE (full) and SWEEP.md 1-34, 356-386
Saved by the lead 2026-11-16 ~08:05 UTC, condensed (every finding kept). OPT = ONE-PLACE-TABLE.md, SW = SWEEP.md.
Reader checked: per-job counts match (STORE 11, LOG 9, FILTER 9, COUNTER 5, RETRY 8, NOTICE 6, OTHER 1 = 49, +10 appendix = 59); 183 = 18+66+99 correct.
Not checked: FD ids and Findings section, Counts section, SW 35-355, exception list L6-EX-01..11, DECISION text vs table, evidence quotes, "10 of 12 nodes identical" (lane M1: TRUE), take repo.
| id | sev | where | finding |
|---|---|---|---|
| R5-C-1 | Blocker | SW:17 vs 360-378 | Headline lists only row 7 as open for the studio head; before-18-Nov band needs a yes on 7 rows (1,3,7,13,14,16,17) plus optional 5,6; 19 table rows "yes needed" not counted in headline |
| R5-C-2 | Blocker | SW:376-378 | Rows 15,16,17 hold a finding not an action; row 15 cut mid-sentence; "pending patch", "codeant", "apply order matters" unexplained; credentials/spend items banded inconsistently (15 after, 16/17 before) |
| R5-C-3 | Blocker | SW:363, OPT:81,83,87 | Decision (a) dollar-cap place not decidable: row 2 proposes stage.journal, OPT says three times it is not a dollar ceiling; no figure, no candidates |
| R5-C-4 | Blocker | SW:366, OPT:110 | Decision (b) second alert channel not decidable: no candidates, cost, watcher or effort |
| R5-C-5 | Major | SW:16,363, OPT:72,81 | Decision (c) is a fact to look up, not a decision; "counter" undefined |
| R5-C-6 | Major | SW:17,368 | Decision (d) key rotation and history rewrite: consequences not stated; row 7 mixes untrack/rotate, move to archive/, rewrite |
| R5-C-7 | Major | SW:5-6 vs 16-17 | Fifth laptop-lead decision (continuation lane for 183 unread files) missing from the open list |
| R5-C-8 | Major | OPT:129,11 | J-058 live shared Postgres credential labelled NOT-NEEDED; could be deleted by a skimmer |
| R5-C-9 | Major | OPT:11,48,49,118,137,141,143 | NOT-NEEDED rows proposing ARCHIVE (J-012, 017/019, 039, 049, 055) do not say whether the caller grep was done; J-010 keeps rig because plan needs it, yet J-049/J-019 archive rig scripts |
| R5-C-10 | Major | SW:24 vs 378, OPT:61,115 | "lead" used for laptop lead, sales request and the person who sent it |
| R5-C-11 | Major | OPT:7 vs 88,138 | "owner is a place, never a person" but J-037 "needs owner yes", J-012 "after owner yes" |
| R5-C-12 | Major | OPT:72,76,87 vs SW:12 | COUNTER owner given two ways: Owner line stage.journal; J-034 OWNER = independent count; J-035 stage.journal NEEDED |
| R5-C-13 | Major | OPT:56,60,129 | FILTER owner and OWNER rows cite rig files while J-058 says take flows NOT VISIBLE; never said rig flows = take flows |
| R5-C-14 | Major | OPT:1, SW:25 | "one place per job"/"one Postgres" overclaims: three stores by design, one a file |
| R5-C-15 | Major | OPT:24,25,44,152-153 vs 13 | CONFLICT and PLAN NOT DONE used inconsistently for same situation |
| R5-C-16 | Major | OPT:13,61,97,114 vs SW:365 | State "OK" means "no conflict with DECISION" but reads "works"; J-025 OK yet review-state request gets no mail/alert; J-041 OK yet DB errors swallowed; head not told the video would run with known Blocker J-051 |
| R5-C-17 | Major | SW:9-15 vs OPT:3,131-146 | Headline omits the 10-row appendix; per-job keyed totals 12,11,10,7,10,7,2; "1 rows" grammar |
| R5-C-18 | Major | SW:372 vs OPT:64,98 | Row 11 says studio-head yes "no" for J-028/J-042; table says "yes" for both; dead-node removal step omitted |
| R5-C-19 | Major | SW:360-385 | "order" column is not an order of work; no priority among 8 mandatory before-video rows; no effort for two days; row 1 stops at first failed step, no fallback |
| R5-C-20 | Major | SW:362-368 | Band label "decision or config change: no new node, no new identity" does not fit rows 3,7,13,14,16; "PR #1", "three live pull request bodies" unexplained |
| R5-C-21 | Major | SW:379-385, OPT:27 | Rows 18-24 ask blanket yes per block while items blocked/conditional |
| R5-C-22 | Major | OPT:14 | Severity definition refers to "severity cells" that do not exist in this file; Blocker definition so broad most CONFLICT rows qualify; no Blocker count in headline |
| R5-C-23 | Major | OPT:11 vs 139-140,144-145 | KEEP-CORE includes CI files, yet J-022/J-033 CI are NOT-NEEDED keep, J-050/J-057 KEEP-CORE; "core" ambiguous |
| R5-C-24 | Major | OPT:16,99,101,143 | Words with 2+ meanings: sweep, claim, heartbeat, counter, take, journal |
| R5-C-25 | Major | OPT:3,7-16,34,39,62,138,158; SW:362,373 | Used before explained: "copy" column, L6-EX-01..11 (EX-11 gates all desk archives), re-smoke, planted-data check, "DECISION seed row six", "Lane wording", "Result review", k1b, creds-lane.json, CodeRabbit/SonarCloud/DeepSource/codeant/Semgrep, film-v5/real-v5 |
| R5-C-26 | Nit | OPT:52 | J-023 "empty in all 126 run folders" vs "most of 378 log files empty" and non-empty fl45k6c |
| R5-C-27 | Nit | SW:376,383, OPT:98 | Truncated text (row 15 cut; row 22 missing bracket); OPT:98 says lines 35 and 91 but cites 36 |
| R5-C-28 | Nit | OPT:141 vs SW:371,382 | J-039 ARCHIVE of test counts vs row 10 "reconcile": unclear what moves |
| R5-C-29 | Nit | OPT:27 etc. | Evidence citations break after archive moves; no note |
