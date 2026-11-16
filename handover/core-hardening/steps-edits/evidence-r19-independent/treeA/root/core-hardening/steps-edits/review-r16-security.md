# EDITS r16 security review, round 4 (egm-design, condensed copy of the inline report), 2026-11-16
Target: EDITS.md (r16), r16-CHANGES.md, resolve-r16.md. Read-only; nothing run. Verdict: REVISE, close. 0 blockers, 1 major (new), 8 minors. r15 F2 and F4 closed; F1 and F3 closed in intent, each with one small gap.
## FAILURES FIRST
### MAJOR
- N1 (E-48 key steps A, C, I, K; ND15; R7) Nobody but the owner can cancel the key, and nothing limits it if he cannot be reached: step A says revoke is "a promise by you, backed by your alarms", no timer in the program; all 3 alarms on one person's device; a missed alarm leaves a live paid key plus its copy in the take folder, n8n's encryption key and saved credentials on the laptop; `key not revoked` is only a handoff note; no second person named; no provider-side spend limit on this key found (grep); the model stage's own cap protects the program, not a leaked or copied key. Recommendation (OWNER-OPEN, not a builder fix): key in a project/workspace with a provider-side spend limit equal to the take cap, or a named second person who may revoke, or a written owner acceptance of the exposure. Stronger for route B (key up to five days).
### MINOR
1. Alarm 3 (18:09 UTC = 23:39 IST, "stop everything else and do key step I now") has no take exception; a take started at the latest start runs to about 18:15:20 UTC = 23:45:20 IST; alarm 1 and K say the take may finish. Money safe either way; owner cannot tell which line wins. Add "unless a take is running; then key step K", or make alarm 3 the revoke command.
2. E-48 D.5 / E-55: no source for "after 18:19 UTC" (assistant has no timer). Name the clock (chat message timestamp) and say what the assistant does if there is none (treat as before 18:19, ask again).
3. G.2 vs E-16 vs E-55: G.2 start conditions omit the `yes, no more takes` confirmation and do not say whether `key gone, no more decisions` stands in for `key revoked`; E-16 does not accept the new word; E-55 says it confirms at any time. Item 1 deletes irreversibly. One list of start conditions used in all three rows.
4. E-09 f vs key step G part (d): the nano backup (`<name>~`, `.save`) is not made by the owner; E-09 f does not say to add its path to his list first. Add "write its full path on your list, then shred".
5. n8n's encryption key (`.n8n/config`, `n8n.env`): part (d) lists n8n.env but G forbids a file only the assistant named; `.n8n/config` removed only by item 1's plain rm (ND9, OWNER-OPEN) stays in free space. Residual F3 does not close.
6. Stale text: line 42 "E-01 to E-58" (file goes to E-62); line 5 "result of round 14 NOT reviewed yet"; confirmation h still says "CONFIRMED latest start 18:04" next to 18:00 of confirmation o. Counts paragraph right (60 rows, 48 Apply now, 12 Hold).
7. E-62, E-04, E-42: exact address `take-<id>-a@example.com` not in the listed inputs (OWNER-SHEET-v23, lead notes, E-12 id rule UNVERIFIED). Fails closed. Add "format not checked against the program" to E-62's Why.
8. E-16 vs card: card "items 2 and 4 and the HubSpot part of item 3"; E-16 "items 2 and 3"; input item 4 is saving screenshots. One wording.
## r15 fixes
F1 closed in intent (gaps 2, 3); new word `key gone, no more decisions` counts only when typed by the owner, no "Are you sure?" (owner-chosen); F2 closed (E-62 exact addresses, at most 3); F3 closed for named files (residual 4, 5); F4 closed for order (G.2 omits confirmation, minor 3); m1 m2 m3 m4(text) m7 closed; m5 L-LEN NOT met (18,632 words against 6,300, builder figure, not recounted); m6 stated not removed; m8 partly. r15 naive: cross-refs, D.1-D.5, broken E-16 sentence, margin fixed; still open E-09 "What the assistant can reach", E-12 "Block 2" labels, E-37 item (4).
## Checked right
17:49, 18:09, 18:19, 18:29 UTC = 23:19, 23:39, 23:49, 23:59 IST; 18:00 + 1:00 + 14:20 = 18:15:20 UTC = 23:45:20 IST (3 min 40 s before 18:19; 860 s is a reading); 18:29:00 - 860 s = 18:14:40 UTC = 23:44:40 IST; weekdays; counts. No path types, prints or keeps the model key in a file.
## OWNER-OPEN (not findings)
L-A/B (ND15), confirmation o, ND9 (rm vs shred), L-LEN.
## Not checked
Nothing run; verify16.py and its 161 controls not read; many held rows not read; no diff against EDITS.round15.md; word count not redone; address format not checked against the program; whether a take stops safely when its key is revoked is UNVERIFIED.
