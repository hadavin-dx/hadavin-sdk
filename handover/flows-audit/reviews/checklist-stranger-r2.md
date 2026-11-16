# TAKE-CHECKLIST.md stranger read r2 (egm:egm-comprehension), 2026-11-16 11:40Z; condensed by flows-audit; reviewer words unverified. No Blockers, 15 Majors.
1 Row 1 grep -c "^ACCEPTED: recovery flow..." = 1 cannot be met: take_check.sh prints it at ~72 and cats the checker output again at ~156, so a correct run gives 2 (other counts may double).
2 Exported-copy run: pin is read only from flow-check/take-warns.pin or TAKE_CHECK_WARN_PIN (take_check.sh:23); row never says to set it or overwrite the pin; conflicts with 'no other variable'.
3 Folder names (patched copy, NEW folder, take folder, filled copy, exported copy, TAKE_FOLDER) never defined or related; how F-002/F-008 are applied not stated; fill_flows not named.
4 Undefined: F-002, F-008, F-044, A-016f, decision 4, r20-r22, test-only, Step A, owner vs lead, scenes, run sheet, ledger, money stop, lease/claim/takeover, single-instance guard, take path, Blocker/Major.
5 GO/NO-GO pass line 'no open Blocker or Major in the take path' names no list; take path undefined.
6 Row 2: gate (a) has no pass line; 'four gates' mixes action with queries; SELECT-only login vs write login undefined.
7 Row 3: 'HubSpot identity read-only' has no command; result.json no path; two of three pass items cannot fail.
8 Row 4: 'contact number is all digits' ambiguous (contact id vs phone); 'lead's own look' cannot fail; 'Row 4 parts 1 and 2' undefined; 'row' two meanings; Step D message 1 only on failure vs always after Row 4 (Q26).
9 Rows 5-6: when POST 2 is sent (after first run finished?) not said; late-reply threshold set after rehearsal; 'the take's mailbox' ambiguous; 'exactly 1 mail' which mail; attempts expected value missing.
10 Row 7: 'Caption and card match' what; Q25-2 caption on screen AND card vs 'one line, no numbers'; Q24-5 wording 'one mail sent, one row in state done' second caption or replaced.
11 Row 8: 'takeover shows' undefined; 3-minute start point (n8n stop or start); two numbers (3 min and 'lead sets').
12 Row 10: 'Not found' third answer; how leftover contacts are found (listed once by lead key and contact id) no command/owner.
13 Practice run defined as loopback re-smoke (Tue) but Q26 lists re-smoke Tue and separate practice run Wed before Row 4.
14 Stale list omits PLAN-4:106 and the inputs/ correction (Q25 13d, 14); 'a README line near 240' which README; take_check.sh:19 comment contradicts Row 1; ORDERS.md:20 deletion text.
15 Open risk '+2 to 3 h' not placed on the schedule.
Checked by reviewer: UTC to IST and weekdays right.
