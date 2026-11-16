# v30 changes (round 2 of the owner sheet; builder; 2026-11-16)
Built from the v29 sources; no v27, v28 or v29 file and no EDITS.md or ../inputs file was edited. Nothing was run on any vendor page: every vendor page, button and Windows or n8n step stays UNVERIFIED. No commit, no push, no spend, no secret.

## Gaps and open items first (honest list)
1. **Reading load is not reduced (stranger M9).** The sheet is under the lead's cap (A 6,285 words, B 6,097; limit 6,300, lead order L-LEN) and nothing was deleted: detail moved to the linked appendix. The four pages together are A 12,454 words (sheet 6,285 + card 1,777 + appendix 3,950 + film page 442), B 12,131, more than the v29 pages (about 10,900). The owner still reads more than before. Only the lead can decide to cut content (it would be a deletion, which the order forbids).
2. **Who acts if the owner is unreachable on the deadline day: OWNER-OPEN (Open 107).** The sheet gives the owner a blank on the card ("a person who may cancel the older key if you cannot") and appendix part 10 says that person acts after being asked in advance; the builder cannot name a person. If the blank says "none", the sheet says so plainly: nobody else can act.
3. **Revoke names (security m6).** The brief asked for names that must contain the run name. Names of app passwords and CRM apps come from the lead's message and the vendor page may not show them; so the rule is: revoke only an item whose exact name contains the run name; a name without it is confirmed on the other channel first (UNVERIFIED how the vendor page shows names). Open 108.
4. **Minor 12 (words with several meanings) is only partly fixed**: "film pause", "wait", "alarm", "alarm time", "card step" and "sheet step" are now defined once; no full word-by-word audit was done.
5. **Pointers (check C19) were read by the builder only**, not by an independent person: 142 new pointers were checked by script for existing targets and by reading about 12 appendix fragments. pointers-v30.txt now has 916 entries.
6. **Still OWNER-OPEN by the lead's orders:** L7, DB-2, the delete-path criterion, the meaning of Q27 (Open 109). Open 96 is closed (A no longer waits for a lead message). Open 103 (how 18:04 is derived) is still asked.
7. 9 checks of v29 (C161, C162, C164 to C169, C171) do not fail on v28: they are regression guards for text that v28 already had (the older-key point, FREEZE is not a cancel, state words, the no-delete line, "unknown means no run", the word cap, and so on). They cannot fail on the old file by design; mut30.py plants W01 to W16 and P-plants prove each one fails when its text is removed. All 23 new checks of Part 7 do fail on built v29 (v30-fail-proof.py).
8. The "nothing else I know uses it" phrase stays for the planned cancel at 6.7 only; the forced cancel at 7.11 has its own phrase ("I cancel the older key <its name> now, the yes covers it") so the owner never has to assert something he may not know (security M2).

## Findings and fixes (finding id -> fix -> check or plant that proves it)
SECURITY
- M1 stale lead text: release note v14 and open list say A's older key does NOT wait for a lead message; the 7-day warning (last used before Wed 11 Nov 2026 10:30 UTC = 16:00 IST, from facts) sits next to "money-safe default: A"; if used less than 7 days ago the owner takes B (L-A/B) -> C188, C189; plants X04, X05.
- M2 "unless you know something else uses it" escape: removed; 7.11 describes, then cancels anyway; forced-cancel phrase without the claim -> C186; plants X02, X26.
- M3 deadline-day stop: owner action through Sun 22 Nov (deadline reminder set after the yes, 5.8; cancel any still-valid older key by Sun 22 Nov 2026 18:09 UTC = 23:39 IST, or the last-resort step); appendix part 10 holds who acts, the no-yes path and the missed-7.11 path; Mon 23 Nov: 7.11 and alarm 4 apply, no take planned -> C187, C208; plants X03, X23.
- m1 one 7-day wording (in full once, at 5.1; 6.7 points to it) and the last-used lag sentence (appendix part 6) -> C185; plants X01, X25.
- m2 18:04 is a plan fact, not a start that fits a run (18:04 + 5 + 15 + 10 = 18:34 UTC = 00:04 IST; deadline 18:29 UTC = 23:59 IST; gap to the refusal limit 18:14:40 UTC = 23:44:40 IST is 10 min 40 s): note and open list -> C209; plant X24.
- m3 6.1 Recall page: STOP (no tolerated difference) -> C190; plant X06.
- m4 clipboard: any clipboard manager, remote tool, screen-capture tool off (R1, 6.1) -> C191; plant X07.
- m5 film person: no file manager, second terminal window or clipboard (sheet 7.6 and film page) -> C192; plant X08.
- m6 revoke names contain the run name (8.2 name rule used at 8.3 and 8.4) -> C193; plant X10.
- m7 gap between earliest key time and latest start at most 60 minutes (facts GAP_MAX; sheet check and open row 100; literal 60 in the check) -> C194; plant X11.
STRANGER
- B1 film rules contradiction: R9(a) says which rule wins; the film person never stops for the From column; the editor cuts it; the film person is told (sheet and film page) -> C192; plant X09.
- M1 5.7 against 6.1 timing: the intro says 5.1 to 5.8 and 6.1 may be done early; 5.7 says what to do with the switches and 8.7 puts them back -> C14 family (existing) and C195/C199 on the text.
- M2 R10 empty reference: the silence trigger is spelled out in R10 (no bare appendix pointer).
- M3 the card stands alone: latest start, alarm time, cancel-by, older-key time and deadline are blanks as UTC = IST pairs; backup person and the delegate blank; set phrases and alarm words on the card -> C195 (every UTC time has its IST pair).
- M4 the three waits are named (y minutes, run length, film pause) and the 5-minute rule is worded the same in 6.2, W5 and the card words -> C196; plants X13, X27.
- M5 one person for a failed cancel: the backup person only -> C197; plant X14. 7-day rule worded once (see m1).
- M6/M7 orphaned appendix fragments removed (every fragment starts with "Step" or a sentence); "press Enter once" put in 6.4; parentheses balanced -> C198, C199; plants X15, X16.
- M8 codes: labels W1 to W9, L1 to L5, R1 to R10 and card step against sheet step numbers explained where first used; no double colon -> C200; plant X17.
- retire check defined (8.6) -> C202; plant X19. Appendix parts numbered 1 to 10 with no gap -> C201; plant X18. "at re-pin", `<name and how>` and the date row explained -> C203; plant X20.
- Film pause wording and the cue the film person gets ("film pause now"); the pause length comes from the numbers message.
- Minors 10 to 20: applied in the sheet text (wording, labels, the "Privacy switches back" sentence is one wording in R1, 6.1 and 8.7).
EVIDENCE
- UTC without IST pair on the six lines (appendix A and B line 10; open list lines with 15:00 UTC, 11:30 UTC twice, 17:39 UTC): pairs added -> C195; plant X12.
- Exact placeholder spellings `[OWNER FILLS: ...]` and `[LEAD FILLS at re-pin: ...]` in the open list -> C206; plant X21. Open rows 107 to 109 -> C207; plant X22.
- C07 info line repaired: it now prints the four real pages (sheet, card, appendix, film person page).
- Cannot-fail checks: see gap 7.

## Evidence (commands run in this folder with python3 -B -I)
- build-v30.py then check-v30.py: 0 failure(s). Word counts: sheet A 6285, B 6097; card A 1777, B 1711; appendix A 3950, B 3881; film page 442.
- mut30.py: 209 plants, 208 caught by the meant check, 0 missed, 0 anchor-not-found (the 209th is the negative control, which must print MISSED and does). The 27 new plants are X01 to X27.
- v30-fail-proof.py: Part 7 (C185 to C209, 23 checks): 23 fail on built v29, none fails on v30.
- Banned-string scan: list read at run time from tests/test_no_reference_material.py; 10 entries; 20 files scanned; 0 files with a hit (counts only; no word written to any file).
- __pycache__ removed (python3 -B -I used throughout).
