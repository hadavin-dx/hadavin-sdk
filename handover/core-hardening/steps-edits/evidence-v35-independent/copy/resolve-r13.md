# Resolve, round 13 (EDITS.md; builder only, EGM skills are run by the studio lead)

## Failures, gaps and open questions first
1. NOT DECIDED 15 conflicts with the brief. The old default was route A (`no more takes` right after the last take). The round-13 brief asks the owner text to recommend route B (`no more takes` only after `cut accepted`). I did not choose: E-48 part 3c and E-57 write BOTH routes with their conditions, E-48 carries ONE recommendation sentence ("The assistant recommends route B; the choice is yours."). Studio lead: keep it, change it to A, or delete it. Either way the key ends by 18:19 UTC = 23:49 IST.
2. The 18:04 UTC = 23:34 IST latest start we plan leaves a margin of 40 seconds: 18:04 plus 860 seconds (14 min 20 s, a reading of the program) is about 18:18:20, and the last time to revoke is 18:19 UTC = 23:49 IST. The owner text now says so, and says the planned start for Wed 18 Nov is much earlier. Question for the studio lead: move the latest start we plan earlier (for example 17:49 UTC = 23:19 IST)? The owner's alarm is already at 17:49 UTC = 23:19 IST.
3. Placeholder `[LEAD FILLS at re-pin: start time of day for Wed 18 Nov 2026, in UTC and IST]` in E-12 and E-54 (rule R11): the studio lead fills it; I invented nothing.
4. Not fixed here (a new row would be needed and the row count stays 56): OWNER-STEPS line 144 ("By Mon 16 ...", no time) and line 171 ("18:29Z", "18:14Z" without IST). Next step: the v4 writer, or the studio lead adds two rows. Quoted old texts keep the words "the lead" (they are old text, not edited).
5. Still UNVERIFIED: where n8n's encryption key is kept (E-30 names n8n.env and the take's own settings folder; the owner text says "files in the take folder, which file is UNVERIFIED"), the click paths, the HubSpot app for the key (L-APP2), whether a take stops safely when its key is revoked, the 860 seconds, the take id rule, the stage settings file location (E-51), the Docker volume.
6. Needs the studio lead: confirmation m (narrowing Q19.5, the 7-day figure taken from L-A/B) and confirmation n (the widened yes sentence).
7. Nothing was run except the text checks. The studio lead's EGM review of round 13 has not happened. The model for planning skills was not involved (builder only).

## Map: finding to fix
Security review (`review-c4-r12-security.md`)
- B-1 key can stay alive: E-48 part 3a (key ends by 18:19 UTC = 23:49 IST WHATEVER the answer, `not sure` never keeps it alive, S9-3 and L-23NOV cited), 3b (owner alarm 17:49 UTC = 23:19 IST, named `revoke the model key`), 3g (new keys first), 3h (revoke ALWAYS, `key revoked` or `key not revoked` plus the reason); E-37 questions; E-58 row 1 unconditional; E-12 last-day bullet; ND7 and R7 rewritten.
- M-1 reach of the assistant (n8n encryption key, three saved credentials): E-09 new paragraph "What the assistant can reach"; sub-step g no longer says "none of them is a password"; E-12 yes sentence widened with an explanation bullet (confirmation n).
- M-2 no reminder on 23 Nov: E-12 and E-48 3b alarm; the assistant has no timer (Q26); R7 says what a session does if open.
- M-3 line 120 trigger: E-55 old text is now lines 119 and 120; the new second line starts item 1 only after `no more takes` (and `cut accepted` in route B); E-16 carries the same trigger; R10.
- M-4 key identification: E-48 3h (name and last four characters, compared by the owner alone, never told to the assistant; cropped screenshot is a record, not proof; it shows names and dates only).
- M-5 owner's own n8n, "used recently", Q19.5: E-48 3g (new key for own n8n and others, typing rule), 3i (7 days, not held by an n8n, purpose known), confirmation m.
- Minors: shred path (3f: starts with the take folder path, no `..`, `ls -l` starts with `-`, full path in the assistant's message); Wed 18 Nov time (placeholder, R11); lines 144 and 171 (left, item 4 above); "step 17" citation (now the section name); E-09 "Password" field name stays unchecked (said so), open fallback closed (sub-step e); E-51 location UNVERIFIED (left).

Naive review (`review-c4-r12-naive.md`)
- B1 when to write `no more takes`: E-48 3c both routes plus one recommendation; E-57 heading has one deadline (18:19 UTC = 23:49 IST), line 857 ordering fixed (E-55 heading says: revoke right after `no more takes`, route B after `cut accepted`); ND15 marked for the studio lead.
- B2 typing rule for all secrets: E-09 sub-step a (one rule, three parts), sub-steps f, g and new h (mailbox app password, HubSpot key) and E-37, E-48 3g refer to it.
- M1 unfinished fallback: E-09 sub-step e.
- M2 reply phrases: E-09 five fixed one-message replies; `<line name>` comes from the message "Add a line to n8n.env"; E-12 reply slots (search file slot, `<X>` with two decimals, `latest start we plan <time in UTC and IST>`); E-52 "How you reply".
- M3 unseen references: E-12 "In the older sentences of this step", part 1 lists its figures; E-37 and E-48 write the questions in full; E-16 "the numbered items 2 to 6 that follow this item"; E-37 "of step 8".
- M4 shred path and "the others": E-48 3d, 3f, 3i, 3g.
- M5 port: E-06, E-37, E-48 3e, E-52 (port number = number after the colon, 5678 is the owner's own n8n).
- M6 contacts contradiction: E-37 says read "archived" in steps 17 and 18 as "not settled"; the owner does not judge the code search.
- M7 words collide: E-52 one bullet defines the assistant and the studio lead; the later duplicate is removed. Quoted old texts keep "the lead" (item 4).
- M8 UNVERIFIED: E-01 and E-52.
- M9 step 16 reply shape: E-12 (see M2); to refuse type `no`.
- M10 hidden second path and 14 versus 15 minutes: E-12 says "No take is planned for Mon 23 Nov (the line above only says last day)" and gives the arithmetic (14 min 20 s, 40 seconds margin).
- m1 UTC and IST: E-12 and E-52. m2 Wed 18 Nov time: placeholder in E-12 and E-54. m3 spacing of reply words: E-52 "How you reply". m4 bad stretches: E-57 `<minutes>:<seconds> to <minutes>:<seconds> <a few words>`. m5 words: E-52 (IMAP, label `demo`, person A, B and C, mail step of a run, model stage settings file). m6 E-03. m7 E-16. m8 E-48 3c. m9 E-48 first paragraph (own deadline for the HubSpot apps, 18:29 UTC = 23:59 IST). m10 post clause: removal condition in rule R11 and the Why of E-17. m11 E-37 exception. m12 E-02.

Evidence run (`evidence-r12-independent/00-SUMMARY.md`, read last): no failure; one observation, the label "latest start time" with two times: now two names, "latest start we plan" (18:04 UTC = 23:34 IST) and "program refusal limit" (about 18:14 UTC = 23:44 IST), in the words list, confirmation h, rule list, E-12, E-48, E-52 and the Why lines; verify13.py fails on a bare old label, on a name followed by the other name's time, and on any UTC and IST pair that is not plus 5:30. Its note that `key kept` was a reply anchor: replaced by `key not revoked`. Its note that `../inputs/` is not under steps-edits: the inputs are `core-hardening/inputs/` (unchanged; not edited by me).

## Files
EDITS.md (round 13, 56 rows, ids unchanged, Apply now 44, Hold 12, HOLD blocks 13), EDITS.round12.md (byte copy of round 12), build-r13.py (head, body1, body2, tail parts are in build-r13-*.py), verify13.py, resolve-r13-check-output.txt, checkpoint-r13.md, resolve-r13.md.
