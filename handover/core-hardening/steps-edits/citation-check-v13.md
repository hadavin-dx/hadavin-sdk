# v13 citation check (citation checker, read-only, static), 2026-11-16
Files checked: S = OWNER-STEPS-realrun-v13.md (143 lines), C = OWNER-DAY-CARD-v13.md (67), A = OWNER-STEPS-v13-APPENDIX.md (142), CH = v13-CHANGES.md (73). Sources read: ORDERS.md (Q19, Q20, Q21), inputs/ (AGENT-SCOPE, DECISIONS-2026-11-16, DECISION-one-store, FACTS-ALREADY-DONE, OWNER-STEPS-realrun-v3), steps-edits/inputs-patch-Q20-5.md, review-v12-stranger.md, review-v12-security.md, citation-check-v12.md, v13-OPEN-FOR-LEAD.md, check-v13.py and its output, and one copy of hubspot_probe.py found under /tmp/c8b (an evidence copy, not the row 19 commit).
Result: 0 Blockers, 0 Majors, 5 Minors. Each of the 4 Majors of v12 is fixed (table below). Previous check: citation-check-v12.md (4 majors).
Not checked: any command, click path or screen (no program ran); `scripts/run_real_check_n8n.py` (not on disk, so exit codes, notice text and film-pause behaviour rest on v3 and ORDERS only); byte counts other than 28609 B for S; writer suggestions with no source (20 min margin, 5 min limit, 4 to 12 character run name, at most 3 retire-check runs, 60 s / 30 s ban items, shot list); the 45 s lease and "three tries" were checked only against inputs-patch-Q20-5.md round 2 (that file says it read the flows, not ran them); the v13-OPEN-FOR-LEAD.md rows themselves.

## Failures (holds = no)
| # | Claim (file:line) | Cited source | Holds | What the source says |
|---|---|---|---|---|
| 1 | C:44 (E.2) "layout may differ from appendix 5" (a sample notice) | A section 5 (A:50-60) | no | Appendix 5 has the masked form and a sample PRINTED RESULT after `end`; it has no notice sample. v13-OPEN L1 also says "appendix 5 ... notice layout". The owner is told to compare against a layout that does not exist. Fix: delete the phrase or add a notice sample marked invented. Minor |
| 2 | A:138 lists `cut` among new commands "UNVERIFIED on this laptop" | S step 0.5 (cut removed, per CH SE-m5) | no | `cut` appears in none of S, C, A as a command (S:122 "each cut" is a video cut). Stale list item. Minor |
| 3 | S:89 (0.6) "If the 'delete' line says FAIL or SKIPPED" | hubspot_probe.py copy under /tmp/c8b (lines 279-309) | no (copy only) | In that copy the delete line is PASS (permanent), PASS (normal delete...), FAIL or "NOT NEEDED (nothing was created)"; never SKIPPED. A delete FAIL also makes the exit code 1 (line 356: only PASS/SKIPPED count as good). S:88 says "Exit code 0 means no line says FAIL" (holds) but never says what the owner does with exit 1 from a delete FAIL. Version at row 19 commit not read. Minor |
| 4 | C:43 (E.1) "do not start again" after a login line differs from "still works" | v3 step 17 (v3:101): "retry at most once" | no (undisclosed change) | The change is safer and probably intended, but CH does not list it as a deviation from v3 or from any Q-answer. Minor |
| 5 | CH ST-m4 "C first line states draft until the stamp is filled" | C:1 and C:3 | no | C:1 is the title only ("DAY CARD v13 ..."); the draft statement is on C:3. Minor |
Also noted, outside the four files: v13-OPEN L12 says "Patch of decision 8 and decision 9 ... allowing step 0" but inputs-patch-Q20-5.md changes file lines X:2 and X:9 = decisions 1 and 8 (A:139 "decisions lines 2 and 9" and S:81 "decision 8" are right). Fix L12 to "decision 1 and decision 8".
Risk flag (holds = unverified): C:44 tells the owner to type `n` if any notice line says contacts will be deleted or archived. v3:95 describes the notice as "up to 3 contacts archived at the end" (old harness wording). If the real notice still prints that text, the owner types `n` on every run. Only the rehearsal (L1) can settle it.

## v12 Majors and minors: fixed?
| v12 item | v13 location | Holds |
|---|---|---|
| CI-M1 lease sentence vs Q21.2 | S:141 box "NOT APPROVED", "three tries in total including the first"; deviation text matches inputs-patch Q20-5 "DEVIATION" | yes |
| CI-M2 go item 7 self-contradiction | S:50, A:60, A:93, C:56 all say: no number named; any non-0 is Freeze unless the lead's written rule | yes |
| CI-M3 "12" vs 13 | S:143 "full list of 13"; A section 8 has items 1 to 13 | yes |
| CI-M4 F.2 vs F.4 | S:64 names F.4; C:57 is F.4 | yes |
| CI-m5 60 minutes | S:118, C:57, C:67 "same day" | yes |
| CI-m6 E.0 heading | C:31 "## E.0 Before E" | yes |
| CI-m7 "appendix G" | S:77 "appendix 12" = Step G | yes |
| CI-m9 F.1 vs F.2 | A:101 "at F.2"; C:55 F.2 | yes |
| CI-m11 placeholder words | check-v13 output: 0 in all five files (re-counted by reading: none in S, C, A, CH) | yes |

## Dates, times, arithmetic (all hold)
| Claim | Source | Holds |
|---|---|---|
| Mon 16 Nov, Wed 18 Nov, Mon 23 Nov, Wed 25 Nov 2026 weekdays | calendar (today is Mon 16 Nov 2026) | yes |
| 23 Nov 18:29 UTC = 23:59 IST (S:3, S:101, C) | Q21.1; AGENT-SCOPE:15 "2026-11-23 18:29Z" | yes |
| Latest start before 18:14:40 UTC = 23:44:40 IST (A:95); "about 14 minutes" | v3:171 (860 s; 18:29:00 minus 14:20 = 18:14:40) | yes |
| Post by Wed 25 Nov 15:00 UTC = 20:30 IST | Q21.1 | yes |
| Target Wed 18 Nov, "not fixed" | Q21.1 | yes |
| Worked money example: 0.27 per call; 0.81 total; 12.40 + 0.81 = 13.21; 3.90 - 3.10 = 0.80 (ok); 4.00 - 3.10 = 0.90 (over) | arithmetic redone | yes |
| Probe command flags `--plan`, `--yes-spend-calls <N>`, env name `HUBSPOT_PROBE_TOKEN`, "planned calls: N", SKIPPED also exits 0, example.com contact | hubspot_probe.py copy lines 47-52, 316-357 | yes (copy) |

## Counts and cross references (all hold)
| Claim | Source | Holds |
|---|---|---|
| 23 run card rows; rows 8 and 9 "not used" | A:17-41 | yes |
| 13 sends = A 2 + B 10 + C 1; 3 model calls; 2 or 3 contacts | v3:11; AGENT-SCOPE:23 (N-i); A:51 | yes |
| 9 go items; 6 money-rule items; 13 ban items; 17 appendix sections; rules 1 to 12 | S, A (counted; check-v13 agrees) | yes |
| Every "row N" in S and C names the right content (3, 4-7, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23) | A section 2 | yes |
| Every "appendix N" / "section N" in S, C, A (3, 4, 5, 8, 9, 10, 11, 12, 13, 14 item 10, 15 step 7, 16, 17) | A headings | yes |
| Step ids A.0, A.0b, A.1-A.6, 0.1-0.6, C.1-C.3, E.0, E.1-E.4, F.1-F.5, I.0-I.7 | headings in S and C | yes |
| "four commands of appendix 15 step 7" | A:131 lists ls, ps, pgrep, date | yes |
| Ports 5678 and 5679 are the owner's own | DECISIONS 6 | yes |
| "default decision 8" (real-account smoke replaced) and S:81 patch need | DECISIONS line 9 = decision 8; inputs-patch row 7 | yes |
| "decision 5" no closed gate, fallback not accepted (A:138) | DECISIONS 5 (S9-1 fallback) | yes |
| "decision 10" one Postgres server, two databases; journal is the second record | DECISIONS 10; Q21.3; DECISION-one-store item 4 | yes |
| Caption "one Postgres server, two databases", never "Postgres is the one store" | Q21.3 | yes |
| Post wording "a lead sent twice with the same id is processed once" | DECISIONS 1; Q21.2 | yes |
| Lease 45 s; recovery re-claims after lease; up to 3 tries incl. first; differs from Q21.2 "no takeover after expiry" | Q21.2; inputs-patch Q20-5 round 2 | yes |
| Take program has no delete call, read-only identity, leftovers listed; go item 5 only after lead's final-head check | Q19.1 | yes |
| A:139 old text `run_real_check_n8n.py:1051`, `crm_hubspot.py:504-509`, F-01 | AGENT-SCOPE:20 | yes |
| "scope lines 5, 9, 13, 20 and decisions lines 2 and 9 (Q20.5)" | Q20.5; inputs-patch table rows 1-7 | yes |
| Shared Linux user exposure, owner may veto, old keys cancelled except reasoned | Q19.3, Q19.5 | yes |
| Ledger cumulative, no reset between trial and real run; "lead verifies at re-pin" | Q19.2 | yes |
| Do not edit settings after start; re-read UNVERIFIED | Q19.4 | yes |
| Owner never stops or starts n8n; no extra cue UNVERIFIED | Q20.1; decision 7 | yes |
| Clean start empties `mf_leads` with take database admin role; fresh container; names filled at re-pin | Q20.2 | yes |
| Probe key separate; take key read-only stated only as unverified | Q20.3 | yes |
| Exit code for C unknown: none stated | Q20.4 | yes |
| Retake count "lead computes" (A row 10) | Q21.4 | yes |
| Exit codes 0 / 1 / 2 / 3; retire check 0 / 3 / 2; lock file beside run folder; marker file never deleted; 2-second minimum | v3:96, 169-172 | yes |
| Screen order: two "login: still works" lines, notice, "Type y to start"; "type exactly: end" | v3:95, v3 step 18 | yes (v3 wording) |
| Film pause ends early with exit code 3 and deletes nothing (C:55) | v3 step 18 says old harness archived anyway; no source for exit 3 | not sourced; already marked "lead verifies at re-pin" and A:138 "assumed" |
| `DESK_*` / `MF_*` read inside nodes, local flow copy needed | AGENT-SCOPE:23 (BL-wp6-G1) | yes |
| US$180 / US$189 not used in S or C; A:140 describes both | FACTS-ALREADY-DONE line 3; AGENT-SCOPE:15 | yes |
| "owner statement 2026-11-16" for accounts done (A:7) | FACTS line 1 | yes |
| `stage.env` is the model settings file; backstop and window end are settings | AGENT-SCOPE:16 | yes |

## CH ids against the reviews
| Claim | Source | Holds |
|---|---|---|
| ST-B1 to B5, ST-M1 to M12, ST-m1 to m12 map to the stranger read in order | review-v12-stranger.md (B1-B5, M1-M12 as truncated, 12 minors in listed order) | yes (ST-M6 to M12 read from a truncated copy) |
| SE-M1 to M7, SE-m1 to m9, SE-nit | review-v12-security.md | yes |
| CI-M1 to M4, CI-m5 to m11 | citation-check-v12.md | yes |
| Every L-number cited in CH (L1 to L20) exists and matches its topic | v13-OPEN-FOR-LEAD.md | yes |
| S size 28.6 KB vs 25 KB target | 28609 bytes | yes |
