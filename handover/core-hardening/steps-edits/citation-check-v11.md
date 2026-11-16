# v11 citation check (read-only), 2026-11-16

Files checked: `OWNER-STEPS-realrun-v11.md` (209 lines), `OWNER-STEPS-v11-APPENDIX.md` (184 lines), `v11-CHANGES.md` (67 lines). Sources opened: `inputs/DECISIONS-2026-11-16.md`, `inputs/FACTS-ALREADY-DONE.md`, `inputs/OWNER-STEPS-realrun-v3.md`, `inputs/AGENT-SCOPE-DO-AND-DONT.md`, `inputs/plan-wp6-resmoke-v5.md`, `QUESTIONS.md`, `steps-edits/citation-check-v10.md`, `v11-NOTES-FOR-LEAD.md`, and `scripts/hubspot_probe.py` (copy under /tmp/c8b/kC/.../t3-r7t/scripts).

## What I could NOT check
- The program at the row 14 commit does not exist on disk (no `run_real_check_n8n.py` anywhere). So `run_real_check_n8n.py:1051` is checked only against the scope sheet text that quotes it, not against code. The only `crm_hubspot.py` on disk is a different snapshot (568 lines, lines 504-509 show `rows_with_prefix`, not an archive call), so `crm_hubspot.py:504-509` cannot be confirmed or refuted. `review-codebase-1.md` (named by the scope sheet for F-01) was not found on disk.
- Commands and click paths (all UNVERIFIED by the writer; not my task). Text-only claims: the 20-min margin, 5-min notice limit, 60-min I.0 limit, run-name rule 4-12 chars, "at most 3 retire-check runs", exit code "120" are writer suggestions with no source; the sheets label most of them.
- No ANSWER-Q*.md or QUESTIONS.md Q-number is cited in the two sheets (only in v11-NOTES); nothing to check there. `ANSWER-Q18-lead.md` was not used.

## Table of mismatches (first)
| # | Where | Claim | Source says | Verdict |
|---|---|---|---|---|
| 1 | Day sheet line 89 ("owner's decision of 2026-11-16 (item 8)"), appendix 11 (line 144), 14 (lines 172, 174: "owner decision 5 / 2 / 8") | the numbered decisions are the owner's | `DECISIONS-2026-11-16.md` header: "Lead decisions ... default decisions per RIGHT-SIZE; the owner may veto any line; each is reversible". They are the studio lead's defaults, not stated as owner decisions. Numbers 2, 5, 8 and the content match | MISMATCH of attribution (nit). v11-NOTES Q4 already asks whether the owner lifted decision 8. |
| 2 | Day sheet line 66: "backstop of US$180 and credit of US$189 to Mon 23 Nov 2026 18:29 UTC = 23:59 IST" | 180 = backstop, 189 = credit | `FACTS-ALREADY-DONE.md`: "API credits usable (US$180 of 189 in-code backstop, window to Mon 23 Nov 23:59 IST". Ambiguous: could mean 180 usable of a 189 backstop. The sheet says "not re-checked" | PARTLY SUPPORTED (ambiguous source). The UTC half (18:29) comes from v3, not FACTS. |
| 3 | `v11-CHANGES.md` Nv n6 ("codes ... decision numbers replaced by plain words in appendix 14") | no decision numbers left in appendix 14 | Appendix 14 still has "owner decision 5 of 2026-11-16" (line 172), "Owner decision 2" with no date (line 174), "finding F-01" (line 174) | PARTLY. Contradicts the claim "v11 cites decisions by full name" (Cit M2) for line 174 (no date). BL-/S9- codes: 0 hits (that part is true). |
| 4 | `v11-CHANGES.md` SecM9 ("appendix section 7 deleted") | old section 7 gone | Appendix section 7 now exists as "What to send the studio lead" (different content; intro line 3 says no section about copying a connection value) | NOT A DEFECT, wording only: the claim means the v10 section 7, but the number 7 is reused. |
| 5 | Appendix 6 order table, rows 12/13 ("person on row 5", "person on row 4") | "row" = run card row | The same table has its own "No." column (rows 1-20), so "row 5" can be read as table row 5 | Nit (ambiguity), not a source mismatch. |

All other items below MATCH.

## Dates, weekdays, UTC/IST (python datetime)
| Cited | Computed | Result |
|---|---|---|
| Mon 16 Nov 2026 | 2026-11-16 = Mon | match |
| Mon 23 Nov 2026 | Mon | match |
| Wed 25 Nov 2026 | Wed | match |
| 23 Nov 18:29 UTC = 23:59 IST | 18:29 + 5:30 = 23:59 | match |
| 23 Nov 18:14:40 UTC = 23:44:40 IST | 23:44:40 | match |
| 25 Nov 15:00 UTC = 20:30 IST | 20:30 | match |
| "about 14 minutes" before stop time | 18:29:00 - 18:14:40 = 14:20 | match (v3 line 171: 860 s) |

## Citation table (cited / source line text (short) / result)
| Cited (sheet) | Source | Result |
|---|---|---|
| 18:29 UTC window end, 23 Nov | v3 line 119 "Retirement, by Mon 23 Nov 18:29 UTC (23:59 IST)"; FACTS "window to Mon 23 Nov 23:59 IST" | match |
| Post Wed 25 Nov 15:00 UTC = 20:30 IST | v3 line 130 heading | match (single source, as the sheet says) |
| Latest start before 18:14:40 UTC | v3 line 171 "before 18:14:40Z at the default lease" | match |
| "2 seconds" think time (E.4) | v3 lines 22, 96 "under 2 seconds is refused" | match |
| 13 sends: A twice, B ten times, C once | v3 line 11; scope sheet N-i "B ten times at once" literal string | match |
| 3 model calls, 3 people | v3 line 92 | match |
| Login lines `mailbox login: still works`, `HubSpot login: still works`, then notice, "Type y to start" | v3 line 95 (a)-(c) | match |
| Notice: "Confirmation number (type it, a space and ...)" | v3 line 95 (b) | match |
| Older program printed "up to 3 contacts archived at the end" | v3 line 95 "up to 3 contacts archived at the end" | match |
| `--take`, `--retire-check` forms | v3 lines 95, 125 | match |
| Retire check "refused as expected" / "STILL WORKS" / "could not tell"; codes 0 / 3 / 2 | v3 lines 125, 172 | match |
| Exit codes 0,1,2,3 and causes (refusal list, Ctrl-C before/after sends) | v3 line 172 | match (appendix adds nothing contradicting; "120 or another" at the very end has no source) |
| `type exactly: end`; second wrong line also ends pause | v3 line 103 | match |
| Film-pause prompt asks to type `end` | v3 line 103 | match (v3 says "to archive"; that is the delete-line issue go condition 5 covers) |
| Marker file `~/.hadavin-take-tags/<run name>.used`; name usable once | v3 line 97; scope sheet line 20 | match (the `.used` suffix: v3 line 97 cut off at `~/`; scope sheet line 20 names the directory; suffix agrees with v10, not independently seen) |
| `take-<run name>.lock` | scope sheet / DECISION-one-store mention locks; exact file name not opened | source-missing for the exact name (only "lock exists" refusal confirmed) |
| `demo-take` profile; label `demo`; `[demo] lead` subject | v3 lines 107, 52; plan-wp6 | match |
| Ports 5678/5679 are the owner's own | DECISIONS item 6; plan-wp6 line 121 | match; run's own n8n port 5690 not cited in the sheets (row 9) |
| Step 0 `hubspot_probe.py --plan`, `--yes-spend-calls <N>`, `HUBSPOT_PROBE_TOKEN`; "studio lead expects 7" | script docstring: `--yes-spend-calls 7`, `HUBSPOT_PROBE_TOKEN`, "7 properties check, owners, create, patch owner, patch lead status, read back, permanent delete" | match (script copy not proven to be the row 14 commit) |
| Step 0 "tries to delete it" / "the delete line does not matter" | script lines 5, 59, 279-288 | match |
| Appendix 14 "scope sheet: archives at the end by a DELETE call, `run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, F-01" | `AGENT-SCOPE-DO-AND-DONT.md` line 20: "ARCHIVE ... which the code does as a DELETE call (`run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, per `review-codebase-1.md` F-01)" | match to the scope sheet text; code itself source-missing |
| "owner decision 2 says the program never deletes" | DECISIONS item 2 "the take never deletes contacts" | match |
| "owner decision 5 ... fallback not accepted" | DECISIONS item 5 "do NOT accept the S9-1 fallback" | match |
| "owner decision 8 ... replaced extra real-account checks" | DECISIONS item 8 | match |
| "item 7 of DECISIONS-2026-11-16 (n8n first-visit setup)" (CHANGES Cit M2) | DECISIONS item 7; citation-check-v10 M2 | match |
| Accounts/keys made earlier by owner (owner statement 2026-11-16) | FACTS header | match |
| 17-row run card; rows 1-17 references in both sheets (row 3 start, 4 films, 5 n8n, 6 trial, 7 deadlines, 8 paths, 9 n8n port, 10 proof, 11 post check, 12 minutes, 13 I.3, 14 step 0/E, 15, 16, 17 sender) | appendix section 2 table | all 17 rows exist and every row reference in the day sheet points to the right content |
| Appendix section pointers (1-14) from the day sheet | appendix headings | all exist and match their use (sec 2 card list, 3 messages, 4 rule 10, 5 samples/masked, 8 ban list, 9 lock file, 10 n8n lines, 11 trial, 12 G, 13 retire, 14 not proven) |
| "full list of 12" ban lines (J) | appendix 8 | 12 bullets: match |
| A.0 to A.6 labels, A.5 accounts, A.6 yes; go condition numbers 1-9 | day sheet | internally consistent; E.0, order table rows 7/8/11 use them |
| v11 line counts 209 / 184 / "v10 had 240" | wc -l | match (v10 sheet 240 lines) |
| "about 1.8 KB BIGGER than v10" | wc -c: v10 42742, v11 44543 = +1801 bytes | match |
| Banned vendor words, 0 hits | scanned all 10 words of the repo test's BANNED tuple (case-insensitive) in 5 v11 files | 0 hits (words not printed) |

## v11-CHANGES "fixed" claims: 25 sampled against the text (all found unless noted)
Security majors: SecM1 (money rule line 61; A.0 (1); E.0 redo; I.0 box) found. SecM2 (counters 1/2, "No answer: your answer is no") found. SecM3 (A.1 per setting name; F.2 per-model line) found. SecM4a-e (emergency "increased since the latest reading"; cancel any key any time; I.0 box; "may cancel at once" after non-zero code; 60 min suggestion) found. SecM5 (E.0 redo, "E reading replaces A reading") found. SecM6 (DO THIS FIRST item 3, E warning, appendix 8 first line, appendix 14; phrases "No one can start without your written yes" and "starts nothing and deletes nothing" absent) found, 0 hits. SecM7 (go condition 6 `ls -l --time-style=full-iso`, `ps -o lstart= -p`, `date`; condition 5 "file and line"; condition 2 first line names commit; 0.2 public branch sentence) found. SecM8 (appendix 10 forms, row 5 words) found. SecM9 (section deleted, C.3 stop rule) found. SecM10 (step 0 warning quotes written yes; appendix 11 "yes step T"; leftover rule before D.9) found. SecM11 (0.6 `rm` in every case) found.
Naive blockers/majors: NvB1 (A.0 `read -rs`/`set -C` method, clipboard clearing) found. NvB2 ("deletes nothing" 0 hits; go condition 5; F.1 safe exit) found. NvB3 (E "What is normal", row 5 exact words; PARTLY as CHANGES itself says) found. NvM1 (5 minutes, `n`) found. NvM2 (C.3 last paragraph, ports) found. NvM3 (T last; A.5 before A.6) found. NvM9 (appendix 5 sample, F.2/J pointers) found. NvM10 (DO THIS FIRST item 2 criteria) found. NvM12 (appendix 11, F.1 trial) found.
Nits: SecN1 "E.5" 0 hits; SecN2 I.0 uses "cancel"; SecN3/N11 A.5 and E.0; SecN4 "unless the studio lead changed it" 0 hits; SecN7 0.1 compares go message and remembered name; SecN12 J ban list inline = 7 items and clipboard caution inline in A.0; Nv n4 date on 18:14:40 (line 151, appendix 9); Nv n7 masked example `de…r@example.net`; Nv n3 "C.4"/"section 7" no stale references (0 hits).
Not matching: Nv n6 partly (see mismatch 3). CHANGES line 3 "NvM11 length target not met" is honest and true (209 lines vs 180-200).

## Result
0 wrong dates, weekdays, UTC/IST pairs, ports, counts or minute totals. 3 real (minor) mismatches: attribution of DECISIONS items as "owner" decisions (1), the 180/189 split resting on an ambiguous FACTS line (2), and CHANGES claiming decision numbers were fully replaced when appendix 14 still has an undated "decision 2" and "F-01" (3). Code-line citations (`:1051`, `:504-509`) are confirmed only against the scope sheet; the code at the row 14 commit is not on disk.
