| # | mutation | my checker | verify15.py |
|---|---|---|---|
| 1 | key end 18:19 -> 18:29 (tied to 23:49) | caught [istwrong | 18:29 UTC = 23:49 IST] | caught [r13 time arithmetic: 18:29 UTC = 23:49 IST] |
| 2 | key end tied 18:19 = 23:59 | caught [istwrong | 18:19 UTC = 23:59 IST] | caught [r13 time arithmetic: 18:19 UTC = 23:59 IST] |
| 3 | window end 18:29 tied 23:49 | caught [istwrong | 18:29 UTC = 23:49 IST] | caught [r13 time arithmetic: 18:29 UTC = 23:49 IST] |
| 4 | wrong weekday Mon 23 Nov -> Tue | caught [weekday | Tue 23 Nov 2026 is really Mon 2026] | caught [r14 wrong weekday: Tue 23 Nov 2026] |
| 5 | wrong weekday Wed 18 Nov -> Thu | caught [weekday | Thu 18 Nov 2026 is really Wed 2026] | caught [r14 wrong weekday: Thu 18 Nov 2026] |
| 6 | wrong date Mon 16 Nov -> Mon 17 Nov | caught [weekday | Mon 17 Nov 2026 is really Tue 2026] | caught [r14 wrong weekday: Mon 17 Nov 2026] |
| 7 | wrong weekday of Sun date | caught [weekday | Sun 23 Nov 2026 is really Mon 2026] | caught [r14 wrong weekday: Sun 23 Nov 2026] |
| 8 | IST dropped from key rule | caught [istmissing | E-48: ' ends by Mon 23 Nov 2026 18:19 UTC ] | caught [E-48 UTC time without IST: ' used ends by Mon 23 Nov 20] |
| 9 | IST dropped in E-12 NEW time | caught [istmissing | E-12: ' a start only from about 18:14 UTC ] | caught [E-12 lacks 18:14 UTC = 23:44 IST] |
| 10 | IST wrong +5:00 | caught [istwrong | 17:49 UTC = 22:49 IST] | caught [r13 time arithmetic: 17:49 UTC = 22:49 IST] |
| 11 | IST wrong 23:30 -> 23:34 only | caught [istwrong | 18:00 UTC = 23:34 IST] | caught [r13 time arithmetic: 18:00 UTC = 23:34 IST] |
| 12 | 18:04 back in place of 18:00 (NEW heading) | caught [oldstart | a NEW text has 18:04 / 23:34 or a start late] | caught [r13 "latest start we plan" followed by time 18:04] |
| 13 | 18:04 UTC with 23:30 IST | caught [istwrong | 18:04 UTC = 23:30 IST] | caught [r13 "latest start we plan" followed by time 18:04] |
| 14 | latest start text 18:30 | caught [lateststart | latest start near a different time ['18:3] | caught [r13 "latest start we plan" followed by time 18:30] |
| 15 | not-looking wait removed (E-48 step H) | caught [notlooking | E-48: stop-looking not followed by the wai] | MISSED [RES 0] |
| 16 | not-looking wait removed (E-09 f) | caught [notlooking | E-09: stop-looking not followed by the wai] | caught [r14 E-09 sub-step g does not wait for `not looking`] |
| 17 | typing rule definition: wait removed | caught [notlooking | E-09: stop-looking not followed by the wai] | MISSED [RES 0] |
| 18 | E-09 a scope list dropped | caught [typingrule_scope | E-09 a does not list sub-steps c, f,] | MISSED [RES 0] |
| 19 | shred ls -l check removed | caught [e48_ls_-l | E-48 NEW lacks `ls -l '<path>'`] | MISSED [RES 0] |
| 20 | shred realpath removed | caught [e48_realpath | E-48 NEW lacks realpath] | caught [r14 3f lacks realpath] |
| 21 | shred no .. rule removed | caught [e48_dotdot_rule | E-48 NEW lacks contains no `..`] | caught [r13 E-48 lacks contains no `..`] |
| 22 | shred -u replaced by rm in rule | caught [e48_shred_-u | E-48 NEW lacks `shred -u`] | MISSED [RES 0] |
| 23 | shred absolute path rule removed | caught [e48_starts_with_/ | E-48 NEW lacks starts with `/`] | caught [r14 3f lacks starts with `/`] |
| 24 | shred take-10 prefix rule removed | caught [e48_take-10_prefix | E-48 NEW lacks /x/take-10/key] | MISSED [RES 0] |
| 25 | shred whole line (G intro) removed | caught [e48_realpath | E-48 NEW lacks realpath] | caught [E-48 lacks shred -u] |
| 26 | item 6 wildcard shred back | caught [shredwild | E-59 shred with ~ or * in NEW text] | caught [r15 E-59 missing or still has the star] |
| 27 | yes, no more takes sentence removed | caught [e48_confirm_sentence | E-48 NEW lacks Only a new messag] | caught [r15 E-48 D lacks 'Only a new message from you with the ] |
| 28 | yes, no more takes whole confirmation line removed | caught [e48_confirm_sentence | E-48 NEW lacks Only a new messag] | caught [r15 E-48 D lacks 'Are you sure?'] |
| 29 | anything-else-counts-as-more-takes removed | caught [e48_anything_else_counts_more_takes | E-48 NEW lacks An] | caught [r15 E-48 D lacks 'Anything else, or no reply, counts as] |
| 30 | shred done scope (a) only | caught [e48_shred_done_scope | E-48 NEW lacks EVERY file of (a)] | caught [r15 E-48 G done lacks '`shred done` means that EVERY fi] |
| 31 | alarm names swapped (key step C line) | caught [e48_alarm1_revoke | E-48 NEW lacks Alarm 1: Mon 23 Nov ] | MISSED [RES 0] |
| 32 | alarm names swapped (E-12 request line) | caught [alarmswap | E-12 alarm 1 named is the secret key for th] | MISSED [RES 0] |
| 33 | alarm 1 time moved 17:49 -> 18:49 | caught [e48_alarm1_revoke | E-48 NEW lacks Alarm 1: Mon 23 Nov ] | caught [r13 E-48 lacks 17:49 UTC = 23:19 IST] |
| 34 | row deleted (E-61) | caught [rowcount | 58 rows, need 59] | caught [rows != 59] |
| 35 | row deleted (E-30) | caught [rowcount | 58 rows, need 59] | caught [rows != 59] |
| 36 | duplicate id E-20 -> E-19 | caught [dupid | ['E-19']] | caught [ids differ {'E-20'}] |
| 37 | id out of order (E-12 <-> E-13 header swap) | caught [idorder | ids not E-01..E-61 minus 10,35 in order: diff] | caught [ids differ set()] |
| 38 | OLD text altered (E-02) | caught [oldcount | E-02 OLD occurs 0x] | caught [E-02 old count 0] |
| 39 | OLD text altered (E-48) | caught [oldcount | E-48 OLD occurs 0x] | caught [E-48 old count 0] |
| 40 | OLD stated line wrong (E-02 line 3 -> 4) | caught [indexmismatch | E-02 index ('OWNER-STEPS-realrun-v3.md'] | caught [E-02 old on line [3] stated [4]] |
| 41 | count Apply now 47 -> 48 | caught [statustext | **Apply now 48**, **Hold 12**] | caught [status counts in text differ] |
| 42 | count rows in total 59 -> 58 | caught [totaltext | 58 rows in total] | caught [file counts differ] |
| 43 | count OWNER-STEPS 40 -> 39 | caught [filecounts | text ('39', '15', '4') vs rows {'OWNER-STE] | caught [file counts differ] |
| 44 | Hold label removed (first Hold NEW) | caught [holdlabel | E-04 NEW label lacks HOLD G: NEW [hold g1: ] | caught [hold row NEW without label E-04] |
| 45 | Hold gate removed from header (E-04) | caught [indexgate | E-04 index gate G1 vs Hold] | caught [hold without gate E-04] |
| 46 | index status flipped (E-01 -> Hold) | caught [indexmismatch | E-01 index ('OWNER-STEPS-realrun-v3.md'] | caught [index mismatch E-01 ('OWNER-STEPS-realrun-v3.md', '3', ] |
| 47 | index line changed (E-03) | caught [indexmismatch | E-03 index ('OWNER-STEPS-realrun-v3.md'] | caught [index mismatch E-03 ('OWNER-STEPS-realrun-v3.md', '6', ] |
| 48 | E-nn code in owner text | caught [ownercode | E-48 E-code: 'The fixed rule (see E-12). Th] | caught [E-48 owner NEW text contains E-nn] |
| 49 | ND code in owner text | caught [ownercode | E-48 ND-code: ' A. The fixed rule (ND 7). T] | caught [E-48 owner NEW text contains ND] |
| 50 | Q code in owner text | caught [ownercode | E-48 Q-code: ' A. The fixed rule (Q23). The] | caught [r14 internal code in owner text E-48: Q23] |
| 51 | secret key sk-ant-api03 pattern added | caught [secretshape | sk-ant-api03-? matched] | MISSED [RES 0] |
| 52 | AWS-like key added | caught [secretshape | AKIA[0-9A-Z]{1 matched] | caught [secret-like] |
| 53 | banned string inserted (read at run time) | caught [banned | 1 of 10 banned strings present] | caught [banned strings] |
| 54 | fence line deleted | caught [fence | unterminated fence in row region] | caught [rows != 59] |
| 55 | key step letter relabelled | caught [keysteps | key step letters ABCDEGHIJK] | caught [r14 3e bare no] |
| 56 | In short line removed | caught [e48_in_short | E-48 NEW lacks In short:] | caught [r15 E-48 intro lacks 'In short:'] |
| 57 | whatever-you-answer removed | caught [e48_whatever_you_answer | E-48 NEW lacks WHATEVER you a] | caught [r13 E-48 lacks WHATEVER you answer] |
| 58 | only-typed-words rule weakened | caught [typedonly_e09 | E-09 lacks count only when you type the] | caught [r15 E-09 a lacks 'count only when you type them yoursel] |
| 59 | window end 23:59 -> 23:29 IST | caught [istwrong | 18:29 UTC = 23:29 IST] | caught [r13 time arithmetic: 18:29 UTC = 23:29 IST] |
| 60 | Hold row marked Apply now in header (E-04) | caught [statuscount | {'Apply now': 48, 'Hold': 11}] | caught [status counts in text differ] |
