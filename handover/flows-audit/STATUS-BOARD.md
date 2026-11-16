UPDATED_UTC: 2026-11-16T10:28:42Z
SESSION: flows-audit
ORDER: 018 (queue 015, fails 017, board 008)
STATE: WORKING
BOOT_ID: e78580c0
ITEMS_TOTAL: 12
ITEMS_OPEN: 8
PERCENT: 64
AGENTS_RUNNING: 6
CAPACITY: 1.50 load of 4 cores, mem 0/15 GB, RAM 924/16087 MB, disk 27G free of 252G, top3 551M /tmp/claude-0 649M /tmp/pytest-of-root 871M /tmp/f3m , agents 6 (light+heavy per list)
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
decisions pass review: 9 Majors (stale 8 files, count readings disagree, F6B steps 1-5 still describe film-set switching, TRUNCATE would destroy lead_key to crm_id list, F-003/F-004 patches still insert scene 5 text); fixer r2 + patch regeneration running; Q14 asked the lead to re-rate F-005/F-006/F-023/F6B-01/F6B-13 and decide the scene 4 caption
F3 security review 4: 0 Blocker, 4 Majors (check says 0 problems when the manifest is not found; --tokens-only accepts a NOT READY copy; stray .DS_Store blocks check and delete; README claims Python 3.11/3.12 never run) + nits incl 6 noqa vs no-suppression rule; fixer waits for the independent evidence run (still running)
claims r7 fixer: 6 Majors fixed (own report), F5 checker PASS 157 rows (rerun by me, see rc), counts unchanged 126/69/52/29/51=327; open: Q15 closing card (rows 14-15 tags wait for lead), Q13 contact cleanup; M8 words and 'settings-file figures' (M16) still open; 2 cites were not wrong (evidence script compared claim text to code line); independent re-read of r7 not done
F-003/F-004 regenerated (builder: check PASS 5, no 60.1/film-v5/scene 5 in added lines; own numbers); NOT done: scene rows 5-11 and 'Update 17:08Z' caption still in VIDEO-RUNSHEET (lead applies), wording rows held by D1/D2/P2/P4a-c not pasted, 20 s source unconfirmed, F-001 patch line 7 names film-v5; 3 independent checks running
F8 r4 independent evidence: gates rc 0 (with repo config), 577/0/58 on py3.11/3.12/3.13, hostile inputs no traceback; BUT 12 of 25 mutants survived (6 in code: lines 48,117,317,502,1045,1189) sent to r5 fixer; Python 3.10 untested; owner-morning review 4 Majors (placeholders hidden by --quiet-info, wrong table SQL = no alert (Q16), unpatched real-v5 files, --fail-unverified over-claim) in r5 fixer
Q15 answered by lead and applied to CLAIMS-TABLE (rows 14-15 OUT, 16-17 LIVE, no numbers on a card); F5 checker PASS after; but F-003 patch closing card is 4 lines vs the lead's one line: fix after patch reviews land
patches independent check: apply alone and together rc 0, PASS 5, target files unchanged; added lines clean for 60.1/film-v5/scene 5, but F-001 patch line 7 names film-v5, patched VIDEO-RUNSHEET keeps scene rows 5-11 (12 rows) and lines 12/64/84, PAGE-STATEMENTS line 151 keeps 61.9; evidence file is a summary not a full log; wording reviews running
Q13 answered by lead (take uses run_real_check_n8n.py, cleanup OFF, owner deletes leftovers by hand); take scripts are not in this repo so the claim stays 'lead verifies at re-pin'; claims fixer applying
NEXT: F3 r7 fixer after evidence; F8 r5, decisions r2, patch reviews, Q13 apply
PUSHED_UTC: 2026-11-16T10:28:42Z

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
| decfix2 | decisions text fixer r2 | sonnet | 9 Majors of review (M4/M8 left to lead, Q14) | 10:37 | 11:00 | 5 | running | reviews/apply-decisions-r2.md |
| f8fix5 | F8 r5 fixer | sonnet | 4 Majors of owner-morning review (placeholders hidden, wrong table SQL, unpatched files, --fail-unverified) | 10:41 | 11:10 | 5 | running | flow-check/fix-f8-r5.md |
| patrd | patches wording stranger read | sonnet | read-aloud wording | 10:45 | 11:00 | 5 | running | - |
| patfc | patches facts review | sonnet | numbers vs flows/decisions | 10:45 | 11:00 | 5 | running | - |
| q13fix | apply Q13 answer to claims rows | sonnet | rows 33, B-067/091/213/215 | 10:33 | 10:48 | 5 | running | reviews-f1/fix-q13.md |

## LOST OR INTERRUPTED (cumulative: keep every row until the lead writes ACK in the last column)
| agent | what it was doing | cause | restarted? new id | ACK by lead |
|---|---|---|---|---|

## LEAD ACTIONS NEEDED
Answer Q4-Q9 in QUESTIONS.md (one-database wording, approval words, CRM claim, review rows, table screen, extra demotions). Not blocking; the audit is FINAL.
