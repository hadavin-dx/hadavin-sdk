UPDATED_UTC: 2026-11-16T10:23:20Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 8
PERCENT: 52
AGENTS_RUNNING: 6
CAPACITY: 3.30 load of 4 cores, mem 0/15 GB, RAM 959/16087 MB, disk 27G free of 252G, top3 649M /tmp/pytest-of-root 657M /tmp/claude-0 871M /tmp/f3m , agents 6 (light+heavy per list)
INTERRUPTED: none
FAILED: F3: r6 fixer reports 128 tests, gates rc 0, 19 of 20 old mutants killed, 11 of 128 new tests fail on old code (its own numbers, independent rerun running); NOT proven: macOS F_GETPATH real call, n8n reading of escaped $env, mutation coverage of new code, py3.9/3.10/3.12, one unexplained suite failure that did not repeat; real n8n import not run
ROLES: PARKED by lead (client build, after video, no new lanes). Script r6: independent rerun 71 tests OK, gate rc 0, but 7 of 15 random mutants survive (lines 141,145,147,280,358,371,417); not fixed because parked; v4 doc security Blocker (Part C unguarded) unfixed
claims: r5 counts independently rerun and match (113/69/48/28/69=327, 79 rows); BUT 37 Table 2 rows (41-77) have no LIVE/OUT tag; example.test vs example.com rows 2 and 5 rest on OWNER-STEPS v3 only; row 33 archive step unproven; 2 wrong cites (A-097, A-068); r6 fix pending (tags, desk-repo traces, cites)
F2: C-1 Major withdrawn and now independently confirmed (Route and load_config both refuse NaN/Infinity on pydantic 2.14.1; zero, -1 and tiny prices are accepted, so the price-above-0 check is still a real gap); now 0 Blocker, 5 Major, 14 Nit; patches deferred by lead
ROLES folder marked NOT FOR THE TAKE in its README (lead decision 3); necessity review: RUNSHEET and CLAIMS still carry the 11-scene plan until r5 fixers finish
claims lane B cite check: 127 of 226 B rows, 123 OK, 4 WRONG (B-107, B-155, B-114, B-184) sent to the r5 fixer; 99 B rows unchecked
ORDER023 cancelled by ORDER 024: sed never ran (denied); 6 opus 64 sonnet 0 fable proven in REPORT.md
claims cite lane A+rest of B: 200 rows, 198 OK, 2 WRONG (A-097 trace sentence reversed v1/v2 README; A-068 off by one); desk repo IS on this machine (/home/user/duplicate-proof-lead-desk-n8n head f3c39cf) so several UNTRACED rows can be traced: tracer running
F5 evidence r5: checker check_runsheet_paste.py FAILS vs the new CLAIMS-TABLE (73 ids marked, B-219 has no row); 20 CLAIMS-TABLE line cites no longer hit the claimed text (valid in r4 layout only); checker crashes with no args; 23 of 44 changed rows not named in fix log; fixer will batch with facts review
claims stranger read of lines 1-260: 3 Blockers 16 Majors (gating of row 33 on a check that runs after the take, scope box contradicts itself, scenes 1-4 never described); r6 fixer running
F5 facts review r5: 0 Blocker 6 Major (about 25 wrong CLAIMS-TABLE line cites; A-084 example.test vs example.com; deleting saved runs may not remove n8n copy; decision 2 pasted as fact; B-215 cite; B-010 three vs two leads); r6 fixer running
F8 design review r3: 0 Blocker 5 Major (cross-folder duplicate webhook paths never checked; $env reads exit 0 by default; memory-sourced n8n rules are FAILs without UNVERIFIED tag; self-baseline makes IF gap only WARN; stale README/REPORT claims); r4 fixer running
desk repo trace: 18 UNTRACED rows traced (13 SUPPORTED text-only, 4 OVERSTATED, 1 UNSUPPORTED); desk script as checked in ARCHIVES contacts at the end, against decision 2 (Q13 asked); nothing ever ran against real HubSpot/Gmail; PLAN-4 cites wrong against the 1113-line file
claims r6 fixer done (own numbers: 126/69/52/29/51=327, 84 to-do rows all tagged; M8 words and M16 partly open; Q13: desk script archives contacts only with --cleanup, take script not in desk repo, decision 2 unconfirmed; closing card rows 16/17 vs scenes 1-4 open); independent rerun + reader running; F5 checker must be rerun after it
decisions applied by agent to 12 files (56 edits, own count); NOT done: F-003/F-004 patches still insert scene 5 text and 60.1 to 61.9 s (must be regenerated), ratings of rows for out-of-video scenes not re-rated (lead call), OWNER-STEPS v4 and VIDEO-RUNSHEET are LEAD-TO-APPLY; reviewer running
claims r6 independent rerun: counts match (126/69/52/29/51=327, 84 rows, tags 10+7+67); BUT F5 checker exits 1 (5 ids missing from RUNSHEET-WORDING: B-016,019,038,088,092); 2 cites (mf.py:158, stage_server.py:48) do not show the claimed text; F5 r7 fixer running
F8 r4 fixer done (own numbers: run_all rc 0, self-test 577/0/58 skips, gates rc 0, 3 survivors killed); NOT done: every n8n rule from memory UNVERIFIED, env-access setting invisible to a file check, run_all.sh/take_check.sh have no self-test, 58 skips never fail the run, 2 nits open; independent rerun + reviewer running
F5 r7 fixer: checker rc 0 twice (157 rows, 0 ids missing) as of CLAIMS-TABLE before claims r7; must rerun after claims r7 fixer; section 6 still says '73 in round 6' vs checker 78 (stale); nothing ran in n8n
NEXT: collect F3 ev+sec, F8 ev+review, claims r7, decisions review; rerun F5 checker after claims r7
PUSHED_UTC: 2026-11-16T10:23:20Z

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
| f3ev6 | F3 r6 evidence runner | sonnet | independent rerun, mutants on new code, e2e | 10:21 | 10:51 | 5 | running | fill_flows/evidence-f3-r6.md |
| f3sec4 | F3 security review 4 (fresh, owner-under-pressure angle) | sonnet | what r3 missed | 10:21 | 10:41 | 5 | running | (inline) |
| decrv | decisions-apply result review (egm-codebase-details) | sonnet | 56 edits vs 12 decisions, missed spots, counts | 10:26 | 10:41 | 5 | running | - |
| clfix7 | claims r7 fixer | sonnet | 6 Majors of stranger read + 2 wrong cites | 10:31 | 10:55 | 5 | running | reviews-f1/fix-f1-r7.md |
| f8ev4 | F8 r4 evidence runner | sonnet | independent rerun, 25 mutants, hostile inputs | 10:33 | 10:55 | 5 | running | flow-check/evidence-r4.md |
| f8rv4 | F8 r4 second reviewer (owner-morning angle) | sonnet | what r3 missed | 10:33 | 10:48 | 5 | running | - |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
