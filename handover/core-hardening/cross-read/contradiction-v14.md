# Contradiction check v14 (read-only; nothing run; I do not judge design)
Mon 16 Nov 2026. Files: S = steps-edits/OWNER-STEPS-realrun-v14.md, C = OWNER-DAY-CARD-v14.md, A = OWNER-STEPS-v14-APPENDIX.md. D = inputs/DECISIONS-2026-11-16.md, O = ORDERS.md (Q15 to Q21 answers at lines 121-153), R2 = cross-read/other-sessions-r2.md, N1 = cross-read/not-checked-r1.md. Preamble read (EGM-GATE v1, no secrets, edit only my report). R-numbers: none looked up (a contradiction check, not a design).

## FAILURES FIRST (v14 contradicts a decision, an answer, or itself)
1. **Credentials: two vs three.** S:50 (go item 4) and S:113 (C.3) say "exactly two" (HubSpot take key, sender mail login). R2:6 and N1:37: the flows-audit checker expects three (Postgres app role, mail, HubSpot). Following S makes the owner Stop on a correct setup. S:13 (B1) leaves open who types the Postgres one. A:161 and A:163 also list only two n8n connections. Fix: three, none of a model type, name who enters each.
2. **n8n sign-in vs decision 7.** D:8 and O:145 (Q20.1): the lead imports and starts n8n; the owner only types y, the challenge and end; the owner "never" touches n8n. S:113 has the owner sign in to n8n; A:35 (row 13) "do not open n8n" implies the same; A:133 shot S2 films n8n's list of runs (needs a sign-in); S:9 and C:3 list the owner's typed lines without any n8n step. Also S:13/S:50 (B1) "how the two values get into n8n" leaves open what D:8 already answers (lead, by n8n_api.py). Pick one.
3. **`MF_*` is film-v5, which decision 1 cuts.** S:137, A:9, A:153 name `DESK_*` and `MF_*`. R2:8 and R2:16: real-v5 reads only `DESK_URL`, `DESK_TIMEOUT_MS`, `DESK_ALERT_TO`. D:2 and O:123 (Q15.1) say film-v5 is OUT. Drop `MF_*`; B8 shrinks to `DESK_*` plus the six placeholders.
4. **Lease sentence is required by the lead but banned by v14.** O:123 (Q15.3) and O:151 (Q21.2): write ONE honest sentence on the lease ("a gap longer than the lease is not claimed"). S:144 says "Nothing else about repeats or crashes" and A:102 item 11 bans any sentence about the lease. The only lease sentence v14 offers (S:145) is the opposite (recovery after lease, up to three tries), marked NOT APPROVED, and S:145 itself says it differs from the lead's ruling (no pickup after the lease ends). The required honest sentence is in none of the three files.
5. **Take key read-only (decision 2, Q19.1, Q20.3) vs "take key writes contacts".** D:3 and O:145-147: the take identity is read-only; the card line must say "the HubSpot key used by the take is read-only; the probe key is separate". S:51(c) and A:41 (row 19) and A:161 say n8n's take key creates and changes contacts (it must, the flow writes contacts). Two identities are named in v14 (program: read-only, UNVERIFIED; n8n: writes). Lead must say which one "the take key" is; as written, S:17 "take key = the HubSpot key the run uses" is ambiguous and C:23/S:104 check "take-key names" against one list.
6. **Step 0 vs decision 8 and decision 2.** D:9 (decision 8): no extra real-account smoke. S:85 runs a live HubSpot step 0 (creates, changes, tries to delete one contact); S:85 admits it needs a patch of decision 8 (B5), and O:127 (Q17) still counts "the owner's HubSpot probe" as coverage. The two lead answers pull apart; the lead must choose. Also: the probe must hold delete permission (S:87 permission names, S:93 "delete line"), while D:3 calls the delete-scope question moot. R2:12 flagged the "probe app, not the take key" wording; S:85 still does not say it in those words (S:85 says "the separate step 0 program").
7. **Step 0 leftover contact timing contradicts itself.** S:93: the leftover contact goes on the F.5 list and you delete it "by hand, before step D". F.5 (C:62) is after the run, step D is before it. A:132 item 9 needs it gone in the film. Pick one moment (before D, by a separate list).
8. **Exit codes stated as fact on the card.** O:148 (Q20.4): "do not state one"; lead reads codes at the final head. C:50 states "exit code 2, nothing sent" and "exit code 1, nothing sent"; C:59 states "exit code 3 ... deletes nothing" (the last is marked "lead verifies at re-pin"; C:50 is not). R2:11 said v14 never claims "exit 1 = nothing sent": C:50 does, for the wrong confirmation line. A:105 marks only code 3 UNVERIFIED. Mark all three UNVERIFIED or remove "nothing sent".
9. **Take port still named nowhere; two fill-in places.** D:7 (decision 6): "the plan names it in one place". S:113 and C:15 and A:35 each point at the run card row 13, and C:15 holds a second blank for the same value. The plan (R2:18) names only the rehearsal ports. Not a wording conflict, but one value has two blanks.
10. **Stop words defined in two files while S says "the only place".** S:27 says the table is the only place. C:29-32 redefines all four (and C:64-68 a third time) with different triggers: S:31 Key exposed names the probe app, C:29 does not; S:32 Emergency cancel lists "money rule items 4 and 6, any figure you cannot account for", C:30 says "(money)"; S:33 Freeze lists exit code, sleep, silence, C:31 lists none. Same intent, different words: rewrite C to point at S, or copy exactly.
11. **Q18(3): one owner sheet.** O (ANSWER-Q18-lead.md line 3): collapse into ONE who-types-what sheet. v14 is three files (S, C, A) and S:3 says so. Not a contradiction of content, but the lead's wording was "one sheet".
12. **Inputs not yet fixed.** inputs/DECISION-one-store.md:14 still says "ONE database" (decision 10 and Q18(4) order "one Postgres server, two databases"). v14 uses the new wording (S:55, S:147, A:102 items 8 and 13); the input file disagrees with it. (Lead owns inputs; A:151 says so.)

## One row per decision
| # | Verdict | Where (both sides) |
|---|---|---|
| 1 scope real-v5 only | **contradicts** (small) | MF_* S:137, A:9, A:153 vs D:2. No flow-set switch, no scene 5, no "60.1 to 61.9" found in v14 (grep): consistent there. |
| 2 take read-only, owner deletes | consistent for the take (S:51, C:62, A:55, A:151); **contradicts** in tension: step 0 deletes (S:85) and take key "writes" (A:41) | see items 5, 6, 7 |
| 3 ROLES-PROPOSAL parked | not covered (grep: no mention; no new lanes) | fine |
| 4 C5 patches | not covered (not an owner step) | fine; no mutation-ceiling or A-01/C-01 text in v14 |
| 5 S9 items | consistent: rules fixed mid-take S:81, A:48; lead reads masked outputs only S:81; owner compares figures, program does not print them S:60; run key cancelled S:120; no "nothing can spend" claim S:40, A:102 item 1, A:150; fallback not accepted A:150 | S9-1/S9-4 stay describe-only: yes |
| 6 ports | partly: C:15, S:113 say "own port, not 5678/5679"; take port not named (item 9) | |
| 7 n8n first visit done, lead activates | **contradicts** | item 2; also B1 |
| 8 no extra real smoke | **contradicts** (acknowledged, S:85) | item 6; ONE made-up lead in take prep not in A:78 order table (not covered) |
| 9 counts proof screen = rehearsal screenshot | consistent | A:132 item 5, S:9 |
| 10 wording one server two databases | consistent in v14 | S:55, S:147, A:102; input file line 14 stale (item 12). "archive v3": not stated in v14 (S:3 says older versions are replaced); not covered |
| 11 licence copies | not covered | fine, not owner steps |
| 12 lead rehearses after re-smoke | partly: stamp row C:6 and A:150; target time "tonight or tomorrow" and times in handoff not stated | not covered |

Q15 to Q21: Q15.1 film-v5 out: contradicts via MF_* (item 3). Q15.2 clean start, fresh ids, empty mf_leads, named lead: consistent (S:55, A:78); both "empties mf_leads" and "fresh container" are stated, redundant but not conflicting. Q15.3 narrow claim and honest lease sentence: **contradicts** (item 4). Q15.4 spend limit by owner eye: consistent (S:60). Q17 label "real-v5 minus one node": consistent (A:150). Q19.1 no delete in take program: consistent (S:51, A:151). Q19.2 ledger cumulative, "lead verifies": consistent (S:60). Q19.3 exposure accepted: consistent (S:98). Q19.4 do not edit settings after start: consistent (S:99). Q19.5 cancel old keys: consistent (S:99). Q20.1 owner never stops n8n: consistent (C:3, C:53, A:110) but see item 2. Q20.2 clean start at take prep: consistent. Q20.3: contradicts (item 5). Q20.4 no exit code stated: consistent for C "unknown" (A:72), contradicts for codes 1, 2 (item 8). Q21.1 dates (Wed 18 target, Mon 23 Nov 18:29 UTC = 23:59 IST, post Wed 25 Nov 15:00 UTC = 20:30 IST, owner cancels run key same day): consistent (S:3, C:12, S:120-122); my own arithmetic: 18:29 UTC + 5:30 = 23:59 IST, 15:00 UTC = 20:30 IST: correct. Q21.2 one wording: consistent for the claim (S:144), lease sentence missing (item 4); "index not seen" present (S:145). Q21.3 caption: consistent (A:102 item 13). Q21.4 retake count "lead computes": consistent (A:32).

## Cross-read conflicts (R2 and N1): status in v14
- 3 vs 2 credentials: still open in v14 (item 1).
- n8n sign-in: still open (item 2).
- MF_* names: still open (item 3).
- Probe contact delete vs decision 2: still open and wider than R2 said (items 5, 6, 7). R2:12 called it "not a conflict"; I read it as a conflict of wording plus the F.5/before-D timing error (item 7), which R2 and N1 did not list.
- R2 item 4 (lead tells owner the crash-test result before posting): S:145 and S:144 do not say this; not covered.
- R2 item 6 (exit 1): see item 8; R2's grep missed C:50.
- N1 row 5 (run-key cancel, v13 emergency cancel spared the run key): fixed in v14 (S:32, S:69 "the run key too").

## One place per job (same rule, different wording or several places)
| Rule | Places | Differs? |
|---|---|---|
| Money stop 18:29 UTC = 23:59 IST | S:3, S:105 (A.6), C:48, A:59 notice | Same figure; names differ: "money stop" S:3, "window end" C:48 and A:59 (S:3 explains it). OK. |
| Stop words | S:27-34, C:29-32, C:64-68 | Yes (item 10) |
| Run key cancel | S:10, S:97, S:120-122, C:12, C:61, C:71, A:43 (row 21), A:159 | Wording differs: S:10 "end of the run day or 24 hours after, whichever first"; S:122 "same day... and in any case 24 hours"; A:159 "same day (24 hours at most)"; C:61 "same day; do not wait for the lead". Same meaning, five wordings; make S:122 the one place. A:43 row 21 "kept (reason, end date)" vs S:120 "stays only with your written yes": same. |
| Lease | S:22, S:145, C:10, A:25 (row 3), A:102 item 11, A:102 item 3 | Defined as "row 3 gives it" in S:22; the claim about it differs from the lead's ruling (item 4). |
| Take port | S:113, C:15, A:35, A:110 | Two blanks (run card row 13 and C:15). |
| Times / deadlines | S:3, C:10, C:12, A:25, A:33, A:107, C:42 | Latest start: "row 3 is the only source" (A:107) but C:10 holds the same blank; A:107 "about 14 minutes" vs row 3 formula S/C:10 "run length + longest pause + 5 minutes". Two sources. |
| Exit-code rule C "unknown" | S:53, S:144, C:26, C:60, A:72, A:105 | Same meaning; fine, but C:26 adds "the cell reads `none`" which no other place says. |
| Which file the owner types lines from | S:80 rule 11 vs C:3 | Same list. OK. |
| Typed-lines gate ("no closed gate") | S:40, A:102, A:150 | Same. OK. |
| Number of blanks | S:13 B1-B13 vs C:5-26 table vs A:153 L1-L22 | Three lists with different numbering. |

## NOT CHECKED
Did not open v14-CHANGES, v14-OPEN-FOR-LEAD, check-v14.py, older versions, the flow JSON, take scripts or any branch; the 3 vs 2 credentials fact comes from R2 and N1 (files I did not verify against take_check.sh). Did not check wording rules (14) or the 13 post bans against the claims table. Line numbers are those of the files as read now.
