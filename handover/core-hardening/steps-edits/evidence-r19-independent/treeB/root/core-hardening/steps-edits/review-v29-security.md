# Owner sheet v29 security review, round 1 (egm-design, condensed copy of the inline report), 2026-11-16
Target: OWNER-SHEET-v29-A/B, CARD, APPENDIX, FILM-PERSON, LEAD-RELEASE-NOTE-v13, v29-OPEN-FOR-LEAD. Read-only, nothing run. Verdict: 0 blockers, 3 majors, 7 minors. The v28 blockers B1 (A had no owner-side end for the older key) and B2 (lease sentence in the public post) are fixed in the owner pages.

## MAJOR
- M1 Lead-facing text still says that in A, 7.11 waits for a lead message "cancel the older key <name>" (old v28 design): LEAD-RELEASE-NOTE-v13.md lines 11, 144, 163 and v29-OPEN-FOR-LEAD.md line 8 (row 96 at line 102 says the opposite). Owner pages say no lead message is needed or accepted. Also "money-safe default: A" has no warning next to it that A probably fails its 7-day rule on Wed 18 Nov (warning only in row 78 and the section 3 table). Fix: strike the lead-message wording in all four places; add the warning next to the default.
- M2 OWNER-SHEET-v29-A.md and -B.md line 85: "you still cancel unless you know something else uses it: then describe and FREEZE" lets the older key stay valid after the deadline; contradicts "a FREEZE never stops 7.11". A run day of Sun 22 Nov could leave a valid key spending toward Mon 23 Nov 18:29 UTC = 23:59 IST. Fix: remove the escape; describe, then cancel anyway (or a written time before 18:19 UTC = 23:49 IST by which the lead must answer).
- M3 The deadline-day stop (revoke by 18:19 UTC = 23:49 IST) is not an owner action anywhere (grep for 18:04, 18:14, 18:19 in owner pages = 0). Uncovered: 7.11 skipped when "no yes yet" (older key stays valid with no end before 23 Nov 18:29 UTC); a missed 7.11 (phone off at 16:00 UTC = 21:30 IST) has no backup; "not done by the older-key time: describe, keep trying, last resort" has no later time or person. Fix: fifth reminder or an owner step through Sun 22 Nov ("if an older key is still valid at 18:09 UTC = 23:39 IST, cancel it or use the last-resort step"), name who acts if the owner is unreachable; or write that this is accepted, with the reason.

## MINOR
- m1 A 7-day condition worded three ways (sheet A line 52 "8 days or more by dates"; line 57 and card L2 "7 days (168 hours) or more"; note line 11 "more than 7 days"); the "last used" lag (G5) is not covered for an irreversible cancel. One wording plus a lag sentence.
- m2 18:04 plan figure cannot start a full run (18:04 + 5 + 15 + 10 = 18:34 UTC = 00:04 IST, after 18:29 UTC = 23:59 IST); note and Open 103 do not say so. Gap to refusal limit 18:14:40 UTC = 23:44:40 IST is 10 min 40 s. Add a sentence: 18:04 is a plan fact, not a start that fits a filmed run.
- m3 6.1 contradicts itself on the Recall page (sheet line 63): "no such page: until the lead says so, no key" and "UNVERIFIED, tolerated". Pick stop.
- m4 Clipboard exposure: other clipboard managers, remote-access tools, password-manager capture, browser history not covered. Add "any clipboard manager or remote tool: off".
- m5 Film person page does not forbid the read terminal, file manager path to the Linux folders, or any copy/paste while the key is alive.
- m6 App-password and CRM private-app revokes (8.3, 8.4) act on names from the lead's clean-up message with no owner check that the names belong to this run (as R7 does for contacts). Require the run name in the name or an other-channel confirmation.
- m7 Key can sit alive between earliest key time and start; no cap on the gap (sample 10:30 UTC = 16:00 IST to 11:30 UTC = 17:00 IST). Suggest a check: latest start minus earliest key time at most 60 minutes.

## Prior v28 security findings
B1 FIXED in owner pages (note stale: M1). B2 FIXED. M1 (18:14 vs 18:04) FIXED in the note with labels; owner pages show neither figure (m2). M2 (three workflow-tool credentials) FIXED as a slot; names unknown (Open 105). M3 (A/B marking) FIXED. M4 (B 7.11 FREEZE) FIXED except the M2 escape. M5 (L-LEN) not fixed by design (A 6,296 words; the card is a fourth page; Open 102).

## Checked, no finding
Key never typed into the shell (`read -rs` into a `umask 077`, `set -C` file); model key not stored in the workflow tool; key file removed only after proven cancel; delete paths conservative (exact address, `@example.com`, count must match, mismatch means delete none and FREEZE); all UTC/IST pairs and weekdays correct; A/B consistent between sheets and cards; four alarms in A and B.

## Not checked
Vendor pages, key list wording, last-used lag, cancel behaviour (UNVERIFIED); word counts; check/build/mutation scripts and outputs; test program source; whether built pages equal SOURCE; most of appendix B; the 17:39 vs 18:04 derivation.
