# fix-ownersteps7: owner part of OWNER-STEPS-q16-rows.md rewritten (fixer; nothing ran except the two checkers)

## What failed or is uncertain (first)
- No silence rule, no clock time for items 3 and 4, no ceiling number, no recording-ready time, no delete-message count was given by the lead (ORDERS.md lines 105-171 read). Each is written "NOT YET DECIDED: ..." or "the lead states this in <message>" in the sheet; none was invented.
- Times I derived are marked "(planned by the audit, not yet confirmed by the lead)": take-prep message 07:00Z and its 08:00Z fallback, Row 4 07:00-07:30Z, delete message 1 about 07:30Z, delete message 2 after 11:00Z, "message 2 only after reply to message 1", the lead's reaction to "stop". Lead-given times are unmarked (06:00Z practice run, 07:00Z F-002 test, 07:30Z cut, 07:30Z rehearsal, 09:30-10:00Z GO or slip, 10:00Z take, 15:00Z post, 08:00Z Tue re-check, Tue 14:00Z test, 23 Nov 12:00Z and 18:29Z, 25 Nov).
- "The take lasts about 1 hour" is from Q27 item 6's arithmetic (practice 1 h, Row 4 0.5 h, rehearsal 2 h, take 1 h); left unmarked.
- Not checked: lead part lines other than the two edits; no reread by a fresh stranger after this edit.

## Reviewer findings checked against the file, then applied
- B1 right (no owner-silence stated): every owner item now has "If you are silent" with the lead's statement pointing to a named message.
- B2 right: items 3, 4, 5 clock times/ready time marked NOT YET DECIDED; timeline lists the take and the items; "why compare figures" added from DECISIONS item 5 (S9-2).
- M3 right: challenge defined, "on camera" = lead's screen recording, where it runs left NOT YET DECIDED; "script deletes nothing" shown as not yet confirmed.
- M4 right: "you type no password" removed; paragraph "What you type and what you never type".
- M5 right: GO, NO-GO, slip defined once; Tue 14:00Z notice marked NOT YET DECIDED; 08:00Z fallback marked planned by the audit.
- M6 right: ceiling and model credits defined; no reply needed; number NOT YET DECIDED; money-stop time given.
- M7 right: Postgres, n8n, key, token, scopes, retake, take day (UTC and IST) defined.
- M8 right: "the video", "the demo program", "a run" defined; "demo" no longer used alone.
- M9 right: line-4 reference removed; precedence stated (act on nothing, may reply "missing: ...").
- M10 right: "stop" defined; case-sensitivity reason given; one search box wording kept.
- M11 right: delete count stated (at least two, extras, optional rehearsal contact, count NOT YET DECIDED); missing delete message covered.
- Citation r8 (IST on lines 35 and 109, derived times): IST added at both (line 109 is lead-part step 10, now line 119); derived times marked. Lead-part step numbers unchanged.
- Kept "Step D" as the lead's label so the lead part still matches.

## Commands (run from handover/flows-audit)
python3 -I tools/check_secrets.py : PASS 0 hits in 1738 files
python3 tools/check_refs.py : PASS 5147 references
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-os7/OWNER-STEPS-q16-rows.md

## QUESTIONS FOR LEAD (main session: copy into QUESTIONS.md)
1. Silence rules: what happens when the owner is silent on delete message 1, delete message 2, the ceiling announcement, the item 6 question, items 3 and 4, the key revocation and the post? (state in which message)
2. Clock times (UTC and IST) for item 3 (settings-file comparison) and item 4 (key revocation); plus V17/V18 contents (file, figures, what they must equal, which key, provider, revoke page).
3. The ceiling number in US dollars and the confirmation of the split "up to 3 paid calls: HubSpot test, rehearsal, take".
4. Ready time and place of the recording, and the post text or "owner writes it" (V19, V20).
5. Total count of delete messages (does the rehearsal go into real HubSpot? decided at re-pin).
6. Does the lead send the owner a message after Tue 17 Nov 14:00Z with the GO or NO-GO result?
7. What typing y confirms, the exact challenge, which window, and whether the owner types live or remotely.
8. Confirm the audit-planned times: take-prep message 07:00Z (fallback 08:00Z), delete message 1 about 07:30Z, delete message 2 after 11:00Z; and that message 2 waits for the reply to message 1.
9. Which chat (V1) and the reply deadline default.
