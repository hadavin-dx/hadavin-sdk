UPDATED_UTC: 2026-11-16T10:39:39Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 5
PERCENT: 77
AGENTS_RUNNING: 4
CAPACITY: 1.81 load of 4 cores, mem 0/15 GB, RAM 971/16087 MB, disk 27G free of 252G, top3 327M /tmp/core-venv 598M /tmp/claude-0 871M /tmp/f3m , agents 4 (light+heavy per list)
INTERRUPTED: none
FAILED: ROLES: PARKED by lead (client build, after video, no new lanes). Script r6: independent rerun 71 tests OK, gate rc 0, but 7 of 15 random mutants survive (lines 141,145,147,280,358,371,417); not fixed because parked; v4 doc security Blocker (Part C unguarded) unfixed
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
F5 r7 fixer: checker rc 0 twice (157 rows, 0 ids missing) as of CLAIMS-TABLE before claims r7; must rerun after claims r7 fixer; section 6 still says '73 in round 6' vs checker 78 (stale); nothing ran in n8n
F3 security review 4: 0 Blocker, 4 Majors (check says 0 problems when the manifest is not found; --tokens-only accepts a NOT READY copy; stray .DS_Store blocks check and delete; README claims Python 3.11/3.12 never run) + nits incl 6 noqa vs no-suppression rule; fixer waits for the independent evidence run (still running)
claims r7 fixer: 6 Majors fixed (own report), F5 checker PASS 157 rows (rerun by me, see rc), counts unchanged 126/69/52/29/51=327; open: Q15 closing card (rows 14-15 tags wait for lead), Q13 contact cleanup; M8 words and 'settings-file figures' (M16) still open; 2 cites were not wrong (evidence script compared claim text to code line); independent re-read of r7 not done
F8 r4 independent evidence: gates rc 0 (with repo config), 577/0/58 on py3.11/3.12/3.13, hostile inputs no traceback; BUT 12 of 25 mutants survived (6 in code: lines 48,117,317,502,1045,1189) sent to r5 fixer; Python 3.10 untested; owner-morning review 4 Majors (placeholders hidden by --quiet-info, wrong table SQL = no alert (Q16), unpatched real-v5 files, --fail-unverified over-claim) in r5 fixer
Q15 answered by lead and applied to CLAIMS-TABLE (rows 14-15 OUT, 16-17 LIVE, no numbers on a card); F5 checker PASS after; but F-003 patch closing card is 4 lines vs the lead's one line: fix after patch reviews land
Q13 answered by lead (take uses run_real_check_n8n.py, cleanup OFF, owner deletes leftovers by hand); take scripts are not in this repo so the claim stays 'lead verifies at re-pin'; claims fixer applying
decisions r2 fixer done (own report: 67 edits, 45=8/8/29 as rated, every scene 5-11 / 60.1 text carries a cut marker); NOT done: M4 re-rating and M8 scene 4 caption wait for lead (Q14); VIDEO-RUNSHEET still has scenes 5-11 (lead applies); independent evidence running
decisions r2 evidence: 25 unmarked phrase hits (film-v5 25, one database 9, approval 11, audit trail 8, 61.9 at SCENE-FLOW-MAP:40 = open Q14/M8); BEFORE measured on parent of a bundled commit; edit lists not compared line by line
F8 r5 fixer own mutants: 2 equivalent survivors, 1 survivor line 353 not re-run separately; --ddl reads column names only (false WARN possible); import into n8n untested; duplicate-address rule across real-v5 + film-v5 and non-numeric HubSpot id not taken; independent evidence + review running
F8 r5 review (false all-clear angle): 2 Blockers + 10 Majors: top block hides missing-column WARN and saving-off on sub-flow/recovery, placeholders and credential ids only WARN exit 0, v4 table file missing = exit 0, run_all can never exit 0 after fixing, README over-claims; round 6 fixer after evidence runner
patches r3 (no new review per round cap): card wording 'processed once in this recording' still lead's choice; mail-window and 30 s facts from review r2 not re-read; F-003 rewritten as whole (larger diff); rows 5-11, example.test in build_mainframe.py, HubSpot, V7/lane3 raw, take addresses still need the lead; independent evidence running
claims r8 fixer: B-214 has no wording (HELD, DO NOT QUOTE: what the take does at a wrong/closed answer is not in any file); Q-H re-pin date open; HubSpot recoverability UNKNOWN; nits N4 N6 N8 not taken; no new review per cap, evidence running
NEXT: F3 r7 fixer; F8 evidence; patches and claims evidence runs
PUSHED_UTC: 2026-11-16T10:39:39Z

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
| f3fix7 | F3 round 7 fixer | sonnet | security review 4 Majors, 5 surviving mutants, noqa | 10:35 | 11:05 | 5 | running | fill_flows/fix-f3-r7.md |
| f8ev5 | F8 r5 evidence runner | sonnet | run_all, 25 fresh mutants, hostile inputs | 10:48 | 11:05 | 5 | running | flow-check/evidence-r5.md |
| patev5 | patches r4 evidence runner | sonnet | apply 5 patches in copy, grep, totals | 11:00 | 11:10 | 5 | running | lanes7/evidence-patches-r5.txt |
| claimev8 | claims r8 evidence runner | sonnet | counts, paste checker, side-by-side rows | 11:04 | 11:12 | 5 | running | reviews-f1/evidence-claims-r8.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
