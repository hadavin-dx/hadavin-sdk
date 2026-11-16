# v12 CHANGES: one row per finding, status and where (line numbers are of the v12 files)

Files: S = `OWNER-STEPS-realrun-v12.md`, C = `OWNER-DAY-CARD-v12.md`, A = `OWNER-STEPS-v12-APPENDIX.md`. Id prefixes: SB/SM/SN = `review-v11-security.md` blocker/major/nit; TB/TM/TN = `review-v11-stranger.md` (its 20 majors are numbered by me from the condensed list: the mapping may differ from the full report); C1-C5 = `citation-check-v11.md` mismatches; LD = the task list; F01-F24 = `review-contradictions-r1.md`; Q19/Q20/Q21 = the lead's answers.

**Not done / worse than asked, first:** (1) The day sheet is over the target: see the size line at the end. (2) Nothing was run: every command is UNVERIFIED. (3) Input files (AGENT-SCOPE, DECISIONS) are not edited here: F01, F05, F13, F17, F18 depend on the lead applying the patch text in v12-NOTES-FOR-LEAD.md. (4) The shot list and several suggested limits (20 minutes, 5 minutes) are the writer's suggestions.

| Id | Finding | Status | Where |
|---|---|---|---|
| SB1 | delete by the take / safe exit | fixed in text (the fact: lead verifies at re-pin) | S:38, C:29, A:139 go item 5 not given by the writer |
| SM1 | old model keys not forced out | fixed | S:83, S:48, A:141 |
| SM2 | baseline drift | fixed | S:52, S:51 |
| SM3 | backstop counter | fixed (counter = the program ledger, lead verifies at re-pin) | S:50, A:45 |
| SM4 | false reassurance, piped y | fixed | S:25, S:59 |
| SM5 | same Linux user; connection values; no agent on a row | fixed (exposure named, owner may veto) | S:82, S:97, A:15 |
| SM6 | step 0 file umask, rm, unset | fixed | S:75, S:77 |
| SM7 | clipboard order, Recall, empty paste | fixed (labels UNVERIFIED) | A:124, A:128 |
| SM8 | go condition 6 decoy pid, clock | fixed (still cannot show which key loaded) | S:39, A:131 |
| SM9 | flow copy on disk | partly fixed (what DESK_*/MF_* hold unknown; lead states it) | S:121, A:134 |
| SN1 | key-like text = exposed | fixed | S:63 |
| SN2 | cut -c1-12 | fixed | S:76 |
| SN3 | python3 -I imports | not fixed (UNVERIFIED; rehearsal must use the printed form) | A:138 |
| SN4 | start line vs ban on & | fixed (printed lines are exempt by rule 10; the start line holds no &) | S:64 |
| SN5 | shred weak | fixed (stated) | S:121 |
| SN6 | no retire check for model key | fixed (stated) | S:106 |
| SN7 | read -rs needs bash | fixed | A:126 |
| TB1 | what y gates | fixed (one place) | S:25, S:59 |
| TB2 | hard stop not met; appendix 14 "owner can ignore" | fixed (go item 5 scoped; no ignore section) | S:38, A:137 |
| TB3 | n8n commands are guesses | fixed (owner never stops n8n) | S:27, A:97 |
| TM1 | "stop" two meanings | fixed | S:14 |
| TM2 | go message two definitions | fixed (one definition) | S:18 |
| TM3 | 5-minute wait vs do not leave waiting | fixed | S:9, C:18 |
| TM4 | rule 12 vs F.3/G deleting | fixed | S:65, C:32 |
| TM5 | money thresholds differ | fixed (one rule) | S:52 |
| TM6 | A.2 two token numbers, message one | fixed | A:45 |
| TM7 | row 12 two numbers | fixed (rows 16 and 17) | A:34, A:35 |
| TM8 | row 4 four jobs | fixed (rows 4 to 7) | A:22, A:25 |
| TM9 | no shot list / recording start | fixed (shot list PROPOSED) | A:121, C:7 |
| TM10 | sender account origin | fixed | A:7, S:6 |
| TM11 | appendix needed on the day | partly fixed (card is self-contained; sheet needs appendix 14, 15, 16) | S:3 |
| TM12 | go 6 example; E.0 too much | partly fixed (E.0 still 10 ticks) | A:131, C:5 |
| TM13 | step 0 regex, count above 0 | fixed | S:76, S:64 |
| TM14 | "owner" HubSpot meaning | fixed | S:13 |
| TM15 | post wording, lease length | fixed (sentence: lead verifies at re-pin) | S:128, A:21 |
| TM16 | trial run order | fixed | S:90, A:100 |
| TM17 | rule 10 vs commands | fixed | S:64, A:47 |
| TM18 | length and split | partly fixed: three files; sheet is OVER the target (see below) | S:1 |
| TM19 | hedges in steps | partly fixed (UNVERIFIED tags kept; some "can" wording remains) | C:3 |
| TM20 | ~40 "row N" references | partly fixed (about 30 remain in the sheet) | S:35 |
| TN1 | late or undefined terms | partly fixed | S:11 |
| TN2 | one word several meanings | partly fixed (lead, key, stop, owner defined) | S:14, S:13 |
| TN3 | one concept several names | fixed in Words (run name/take id, person id/lead key, window end) | S:17 |
| TN4 | earlier versions referenced | partly fixed (the sheet cites the earlier v3 sheet nowhere; decision dates remain) | S:3 |
| TN5 | useless unset | fixed | S:75 |
| TN6 | ls error when tags folder missing | fixed | S:7 |
| TN7 | model account click path | not fixed (the studio lead gives page names; UNVERIFIED) | A:125 |
| TN8 | --yes flags wording | fixed (sentence removed) | S:19 |
| TN9 | card "If missing" column | partly fixed | A:17 |
| C1 | decisions called owner decisions | fixed | S:69, A:142 |
| C2 | 180 vs 189 | fixed (neither used) | A:140 |
| C3 | appendix 14 leftover codes | fixed | A:139 |
| C4 | section 7 number reused | fixed (sections renumbered) | A:86 |
| C5 | "row" vs table row | fixed (table column "No.", card "row") | A:63 |
| LD1 | delete "Nothing you type starts a run" and siblings | fixed | S:25 |
| LD2 | one go message | fixed | S:18 |
| LD3 | stop / freeze | fixed | S:14, C:3 |
| LD4 | money rule one rule, new yes on any figure | fixed | S:53 |
| LD5 | step 0 umask, rm on stop, no unset | fixed | S:75, S:77 |
| LD6 | clipboard sync before copy, Recall, empty paste | fixed | A:124 |
| LD7 | ps -o pid=,args= vs card; clock drift | fixed | A:131, A:41 |
| LD8 | erase local flow copy in I.5/I.6 | fixed | S:120, S:121 |
| LD9 | key-like text | fixed | S:63 |
| LD10 | cut -c1-12 | fixed | S:76 |
| LD11 | defined terms before use | partly fixed | S:11 |
| LD12 | decision labels | fixed | A:142 |
| LD13 | appendix leftover codes, 180/189 | fixed | A:140 |
| LD14 | row 12 and row 4 split | fixed | A:34, A:22 |
| LD15 | shot list | fixed | A:121 |
| LD16 | UNVERIFIED commands marked in the day card | fixed | C:3 |
| LD17 | no agent on any run-card row | fixed | A:15, S:34 |
| LD18 | accepted exposure in writing or sheet stops | changed by the lead (Q19.3): exposure stated, owner may veto | S:82 |
| F01 | scope sheet says DELETE vs no delete call | fixed in sheet and appendix; input S lines to be patched by the lead (patch text in the notes) | S:38, A:139 |
| F02 | conditional branches about deleting | fixed (cut) | C:32 |
| F03 | closing the terminal doubt | fixed (exit 3, deletes nothing; lead verifies) | C:29 |
| F04 | go item 5 scope | fixed (scripts/run_real_check_n8n.py only) | S:38 |
| F05 | decision 8 vs probe | partly fixed (sheet states it; input X line 9 patch text in the notes) | S:69 |
| F06 | counter; third counter ledger | fixed (lead verifies at re-pin) | S:50 |
| F07 | old keys stated once at A.0b | fixed | S:83 |
| F08 | n8n scripts named; no process number from the card | fixed (owner never touches n8n; extra cue UNVERIFIED) | S:27, A:97 |
| F09 | settings change restarts and repeats go 6 | fixed | S:39, S:83 |
| F10 | extra claim sentences; lease | fixed (extra sentences removed; one honest sentence, lead verifies) | S:128 |
| F11 | post ban "deletes or does not delete" | fixed | S:129, A:89 |
| F12 | clean start owner and database names | partly fixed (names UNVERIFIED, lead fills) | S:42, A:66 |
| F13 | S:5 own table vs two databases | not fixed here (input S; patch text in the notes) |  |
| F14 | execution clean-up one wording | fixed (I.5 owns it) | S:120 |
| F15 | HubSpot key scopes in one place | partly fixed (read-only take key, separate probe key; scopes UNVERIFIED) | S:71, A:37 |
| F16 | stop meanings in Words | fixed | S:14 |
| F17 | scope row for the lead's own acts | not fixed here (input S; text in the notes) |  |
| F18 | S:13 key file location vs row 12 | not fixed here (input S; patch text in the notes) |  |
| F19 | rule 11 start line | fixed | S:65 |
| F20 | exit code C unknown | partly fixed (no code stated; lead reads it) | S:40 |
| F21 | pushed branch page vs local only | fixed | S:73 |
| F22 | owner types only y, challenge, end in the run window | fixed | C:3 |
| F23 | owner decision vs lead decision | fixed | A:142 |
| F24 | vocabulary lead key/lead id/person id/stage name | partly fixed | S:17, S:19 |
| Q19.1-5 | PENDING markers Q19.1 to Q19.5 | all REMOVED (answers applied: no delete call, ledger counter, accepted exposure, take scripts, cancel old keys) | S:82 |
| Q20.1-5 | PENDING markers Q20.1 to Q20.5 | all REMOVED; unverified parts marked UNVERIFIED / lead verifies at re-pin | S:27 |
| Q21.1 | dates in one line | fixed | S:3 |
| Q21.2 | one claim plus honest sentence; index not seen | fixed (lead verifies at re-pin) | S:128 |
| Q21.3 | caption "one Postgres server, two databases" | fixed | S:129, A:90 |
| Q21.4 | retake count | fixed (lead computes) | A:28 |

Sizes at the time of writing (bytes, lines): S (26294, 129); C (5832, 42); A (25126, 142). The sheet target was at most 150 lines and 25 KB: lines are met, bytes are NOT (26.3 KB).
