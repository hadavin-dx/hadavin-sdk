UPDATED_UTC: 2026-11-16T10:14:51Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 8
PERCENT: 35
AGENTS_RUNNING: 6
CAPACITY: 2.74 load of 4 cores, mem 0/15 GB, disk free 27G, agents 6 (light+heavy per list)
INTERRUPTED: none
FAILED: F8: r3 fixer reports ruff+format+bandit rc 0, self-test 538/0/52, 3 mutants killed (its own, not independent; evidence rerun running); n8n authentication values and credential kinds come from memory, UNVERIFIED; $env block (N8N_BLOCK_ENV_ACCESS_IN_NODE) unverified: 2 real-v5 nodes may fail; 2 real-v5 webhooks without auth (lead decision); raw/pristine-no-baseline.txt not regenerated
F3: evidence r5: 113 OK, gates rc 0, 8 of 20 mutants survive; security review r3 (read only, nothing run): 3 Medium + 3 Low in clean-up, partial copies, check, delete (no value leak found); r6 fixer running; py3.9/3.10, macOS, real n8n not run
ROLES: PARKED by lead (client build, after video, no new lanes). Script r6: independent rerun 71 tests OK, gate rc 0, but 7 of 15 random mutants survive (lines 141,145,147,280,358,371,417); not fixed because parked; v4 doc security Blocker (Part C unguarded) unfixed
claims: r5 counts independently rerun and match (113/69/48/28/69=327, 79 rows); BUT 37 Table 2 rows (41-77) have no LIVE/OUT tag; example.test vs example.com rows 2 and 5 rest on OWNER-STEPS v3 only; row 33 archive step unproven; 2 wrong cites (A-097, A-068); r6 fix pending (tags, desk-repo traces, cites)
F5: r5 rebuilt by script (rows not diffed by the fixer; rows B-067, B-091, B-215 now rest only on the lead decision, take script absent); no review of r5 yet (evidence runner + facts reviewer running); n8n own DB wording held until check P4b; Q-F, Q-G, Q-A defaults chosen
F2: C-1 Major withdrawn and now independently confirmed (Route and load_config both refuse NaN/Infinity on pydantic 2.14.1; zero, -1 and tiny prices are accepted, so the price-above-0 check is still a real gap); now 0 Blocker, 5 Major, 14 Nit; patches deferred by lead
ROLES folder marked NOT FOR THE TAKE in its README (lead decision 3); necessity review: RUNSHEET and CLAIMS still carry the 11-scene plan until r5 fixers finish
claims lane B cite check: 127 of 226 B rows, 123 OK, 4 WRONG (B-107, B-155, B-114, B-184) sent to the r5 fixer; 99 B rows unchecked
ORDER023 cancelled by ORDER 024: sed never ran (denied); 6 opus 64 sonnet 0 fable proven in REPORT.md
claims cite lane A+rest of B: 200 rows, 198 OK, 2 WRONG (A-097 trace sentence reversed v1/v2 README; A-068 off by one); desk repo IS on this machine (/home/user/duplicate-proof-lead-desk-n8n head f3c39cf) so several UNTRACED rows can be traced: tracer running
F5 evidence r5: checker check_runsheet_paste.py FAILS vs the new CLAIMS-TABLE (73 ids marked, B-219 has no row); 20 CLAIMS-TABLE line cites no longer hit the claimed text (valid in r4 layout only); checker crashes with no args; 23 of 44 changed rows not named in fix log; fixer will batch with facts review
claims stranger read of lines 1-260: 3 Blockers 16 Majors (gating of row 33 on a check that runs after the take, scope box contradicts itself, scenes 1-4 never described); r6 fixer running
F5 facts review r5: 0 Blocker 6 Major (about 25 wrong CLAIMS-TABLE line cites; A-084 example.test vs example.com; deleting saved runs may not remove n8n copy; decision 2 pasted as fact; B-215 cite; B-010 three vs two leads); r6 fixer running
NEXT: Lanes: F3 r6, F5 r6 fix, claims r6 fix, desk tracer, F8 ev+review
PUSHED_UTC: 2026-11-16T10:14:51Z

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
| a7f3r6 | f3-fix6 | sonnet | F3 round 6: kill 8 surviving mutants | 10:10 | 10:40 | 5 | running | fill_flows/fix-f3-r6.md |
| trdesk | desk-repo tracer for UNTRACED rows | sonnet | trace B-067.. in the public desk repo | 10:21 | 10:46 | 5 | running | reviews-f1/trace-desk-repo.md |
| f8ev3 | F8 r3 evidence runner | sonnet | rerun gates, mutants | 10:25 | 10:50 | 5 | running | flow-check/evidence-r3.md |
| f8rv3 | F8 r3 second reviewer (design angle) | sonnet | take-breaker coverage, false confidence | 10:25 | 10:45 | 5 | running | (inline) |
| clfix6 | claims r6 fixer | sonnet | tags, gating, counts, desk traces, cites | 10:24 | 10:54 | 5 | running | reviews-f1/fix-f1-r6.md |
| f5fix6 | F5 r6 fixer | sonnet | cites by id, A-084, B-219, checker | 10:27 | 10:57 | 5 | running | fix-f5-r6.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
