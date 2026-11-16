UPDATED_UTC: 2026-11-16T10:09:18Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 8
PERCENT: 85
AGENTS_RUNNING: 6
CAPACITY: 0.86 load of 4 cores, mem 0/15 GB, disk free 27G, agents 6 (light+heavy per list)
INTERRUPTED: none
FAILED: F8: independent rerun: self-test 469/0/32 and run_all rc 0 match the claim, but ruff check FAILS (213 errors) and ruff format --check fails on check_flows.py and selftest.py; 3 of 20 line mutants survive (lines 389, 398, 462); r3 fixer told to fix both plus 5 Majors from the second review; $env nodes may fail on n8n default (unverified); 2 webhooks without auth are lead decisions
F3: evidence r5: 113 OK, gates rc 0, 8 of 20 mutants survive; security review r3 (read only, nothing run): 3 Medium + 3 Low in clean-up, partial copies, check, delete (no value leak found); r6 fixer running; py3.9/3.10, macOS, real n8n not run
ROLES: PARKED by lead (client build, after video, no new lanes). Script r6: independent rerun 71 tests OK, gate rc 0, but 7 of 15 random mutants survive (lines 141,145,147,280,358,371,417); not fixed because parked; v4 doc security Blocker (Part C unguarded) unfixed
claims: r4 facts review 3 Majors (row 33 says script does not delete contacts but 3 files say it archives; rows 2 and 5 example.test vs example.com; row 21 sibling at OWNER-STEPS:107), reader review of lines 1-133 found 6 Blockers; remainder reader and r5 fixer running; F-01 review unreadable so B-214, B-215 UNTRACED; this lane deleted fix-f5-r4.md earlier (rebuilt shorter)
F5: r4 facts review 3 Majors (wrong line cites, wrong file named for stand-in start, CRM refuse switch exists) and reader review 6 Blockers (machine actions have no owner, step 9.1 placeholders, "recording" two meanings, rows claim more than evidence); r5 fixer applying scope cut real-v5 only; fix-f5-r4.md was deleted by another agent and rebuilt shorter; Q-A to Q-E moot after scope cut
F2: C-1 Major withdrawn and now independently confirmed (Route and load_config both refuse NaN/Infinity on pydantic 2.14.1; zero, -1 and tiny prices are accepted, so the price-above-0 check is still a real gap); now 0 Blocker, 5 Major, 14 Nit; patches deferred by lead
ROLES folder marked NOT FOR THE TAKE in its README (lead decision 3); necessity review: RUNSHEET and CLAIMS still carry the 11-scene plan until r5 fixers finish
claims lane B cite check: 127 of 226 B rows, 123 OK, 4 WRONG (B-107, B-155, B-114, B-184) sent to the r5 fixer; 99 B rows unchecked
NEXT: F3 r6 fixer (8 mutants + 6 security), F8 r3, F5 r5, claims r5, cite lane A; D-04/D-05 not flows-audit
PUSHED_UTC: 2026-11-16T10:09:18Z

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
| f5-fix5 | F5 r5 fixer (scope cut + Majors) | sonnet | real-v5 only, fix facts+reader Majors | 10:12 | 10:30 | 5 | running | fix-f5-r5.md |
| cl-fix5 | claims r5 fixer (scope + Majors) | sonnet | triage OUT rows, fix facts+reader Majors | 10:20 | 10:38 | 5 | running | reviews-f1/fix-f1-r5.md |
| cl-cite2 | claims lane A + rest of B cite checker | sonnet | 97 A rows + 99 B rows | 10:30 | 10:45 | 5 | running | reviews-f1/citations-laneA-and-rest.md |
| a7f3r6 | f3-fix6 | sonnet | F3 round 6: kill 8 surviving mutants | 10:10 | 10:40 | 5 | running | fill_flows/fix-f3-r6.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
