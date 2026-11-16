UPDATED_UTC: 2026-11-16T10:11:55Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 8
PERCENT: 85
AGENTS_RUNNING: 8
CAPACITY: 0.46 load of 4 cores, mem 0/15 GB, disk free 27G, agents 8 (light+heavy per list)
INTERRUPTED: none
FAILED: F8: independent rerun: self-test 469/0/32 and run_all rc 0 match the claim, but ruff check FAILS (213 errors) and ruff format --check fails on check_flows.py and selftest.py; 3 of 20 line mutants survive (lines 389, 398, 462); r3 fixer told to fix both plus 5 Majors from the second review; $env nodes may fail on n8n default (unverified); 2 webhooks without auth are lead decisions
F3: evidence r5: 113 OK, gates rc 0, 8 of 20 mutants survive; security review r3 (read only, nothing run): 3 Medium + 3 Low in clean-up, partial copies, check, delete (no value leak found); r6 fixer running; py3.9/3.10, macOS, real n8n not run
ROLES: PARKED by lead (client build, after video, no new lanes). Script r6: independent rerun 71 tests OK, gate rc 0, but 7 of 15 random mutants survive (lines 141,145,147,280,358,371,417); not fixed because parked; v4 doc security Blocker (Part C unguarded) unfixed
claims: r5 edited (counts 113/69/48/28/69 = 327, 79 rows, by the fixer, not yet independently rerun); example.test vs example.com on rows 2 and 5 rests on OWNER-STEPS v3 only (take program absent); row 33 whether the script archives is unproven; F-01 review file unreadable so B-214/B-215 untraced
F5: r5 rebuilt by script (rows not diffed by the fixer; rows B-067, B-091, B-215 now rest only on the lead decision, take script absent); no review of r5 yet (evidence runner + facts reviewer running); n8n own DB wording held until check P4b; Q-F, Q-G, Q-A defaults chosen
F2: C-1 Major withdrawn and now independently confirmed (Route and load_config both refuse NaN/Infinity on pydantic 2.14.1; zero, -1 and tiny prices are accepted, so the price-above-0 check is still a real gap); now 0 Blocker, 5 Major, 14 Nit; patches deferred by lead
ROLES folder marked NOT FOR THE TAKE in its README (lead decision 3); necessity review: RUNSHEET and CLAIMS still carry the 11-scene plan until r5 fixers finish
claims lane B cite check: 127 of 226 B rows, 123 OK, 4 WRONG (B-107, B-155, B-114, B-184) sent to the r5 fixer; 99 B rows unchecked
ORDER023 cancelled by ORDER 024: sed never ran (denied); 6 opus 64 sonnet 0 fable proven in REPORT.md
claims cite lane A+rest of B: 200 rows, 198 OK, 2 WRONG (A-097 trace sentence reversed v1/v2 README; A-068 off by one); desk repo IS on this machine (/home/user/duplicate-proof-lead-desk-n8n head f3c39cf) so several UNTRACED rows can be traced: tracer running
NEXT: ORDER 023 cancelled (ORDER 024). Lanes: F3 r6, F8 r3, F5 r5 ev+facts, claims r5 ev+read, desk tracer
PUSHED_UTC: 2026-11-16T10:11:55Z

## ITEMS
| # | item | state | % | evidence or output file | note |
|---|---|---|---|---|---|
| F1 | claims table | running | 95 | CLAIMS-TABLE.md | round 2 applied; checker + reader running; citation fixes running |
| F2 | core patches cross-review | done | 100 | reviews-of-core-patches/REVIEW.md | 6 Majors, apply after fixes |
| F3 | fill_flows tool | running | 95 | fill_flows/ | round 2 fixed (68 tests); delta evidence running |
| F4 | patch apply check | done | 100 | patch-apply/REPORT.md | F-002 needs T19 on the laptop |
| F5 | run-sheet wording | running | 85 | RUNSHEET-WORDING.md | final fixer running |
| F6 | idle fallback + recovery audit | done | 100 | F6-AUDIT.md, F6B-AUDIT.md | n8n facts unverified; F6b SQL untested |
| F7 | facts already done | done | 100 | inputs/FACTS-ALREADY-DONE.md | applied |
| F8 | stronger JSON flow checker | running | 88 | flow-check/ | 3 reviews in; fixer running |
| F9 | scene to flow map | done | 100 | SCENE-FLOW-MAP.md | 2 review rounds; static |
| H1 | heavy test lane | done | 100 | heavy-test-lane/SUMMARY.md | 2 same failures in both runs, handover guards |

## AGENTS
| id | role | model | what it does | started UTC | expected end UTC | % | state | last output |
|---|---|---|---|---|---|---|---|---|
| f8-fix3 | F8 r3 fixer (Majors) | sonnet | fix 5 Majors + docs after evidence | 10:05 | 10:20 | 5 | running | flow-check/fix-f8-r3.md |
| a7f3r6 | f3-fix6 | sonnet | F3 round 6: kill 8 surviving mutants | 10:10 | 10:40 | 5 | running | fill_flows/fix-f3-r6.md |
| f5ev5 | F5 r5 evidence runner | sonnet | checker + r4/r5 diff + cites | 10:14 | 10:34 | 5 | running | evidence-f5-r5.md |
| f5rv5 | F5 r5 facts reviewer | sonnet | facts on real-v5 rows | 10:14 | 10:34 | 5 | running | (inline) |
| clev5 | claims r5 evidence runner | sonnet | counts + verdict diff + cites | 10:18 | 10:38 | 5 | running | reviews-f1/evidence-claims-r5.md |
| clrd5 | claims r5 stranger read (1-260) | sonnet | reader review of the new top | 10:18 | 10:35 | 5 | running | (inline) |
| trdesk | desk-repo tracer for UNTRACED rows | sonnet | trace B-067.. in the public desk repo | 10:21 | 10:46 | 5 | running | reviews-f1/trace-desk-repo.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
