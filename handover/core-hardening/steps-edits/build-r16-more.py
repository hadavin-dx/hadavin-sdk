# E-23 plain words
rsub('E-23', '(at the time of writing fix round 3 on `take/nlite-int-r3`, fix round 4 on `take/nlite-int-r4`, fix round 5 being built on `take/nlite-int-r5`; source: the plan\'s own header notes of 2026-11-16)', '(at the time of writing the plan is at its fifth fix round; the names of the code branches are in the plan\'s header notes of 2026-11-16 and are not needed by you)')
why_add('E-23', 'Round 16 (stranger minor): branch names are out of the owner text.')

# E-56 plain words, no codes
set_new('E-56', '''- UNVERIFIED: two statements later in this line (the clause that says the end of the take makes a delete request, and the note at the end of the MAY part of this line; the word "archive" in the next line of this file means the same) say that the end of the take removes the take's HubSpot contacts. That is an earlier reading of the code. A later independent review found no delete or archive path, and the decision of 16 Nov 2026 says the take never deletes contacts. Which reading is right is NOT SETTLED; the studio lead shows a search of the final code when the code version is fixed. Until then do not rely on either statement, and do not widen the HubSpot key.
- MAY: post this take's own generated lead keys (L plus hex);''')
why_add('E-56', 'Round 16 (stranger minor): the owner-facing text no longer carries the codes Q23, r17 and F-01 or file line numbers.')

# E-54 split heading and paragraph
set_new('E-54', '''## Phase 1: the assistant checks.
You only need to be reachable and to answer the questions it asks. The take is aimed at Wed 18 Nov 2026. The time of day is not yet chosen: the assistant proposes one, in UTC and IST, not later than the latest start we plan (18:00 UTC = 23:30 IST, the time at which you start typing), in the request for your yes (step 16), and you answer it before any take; no take starts on a guess.''')
why_add('E-54', 'Round 16 (stranger minor): the heading is only a heading; the paragraph is its own line.')

# E-37 (3) UNVERIFIED and (4) own list widened
rsub('E-37', 'must be the key of app 2, which can read and write contacts, because the flows create the contacts.', 'should be the key of app 2, which can read and write contacts, because the flows create the contacts (this reading of step 7 is UNVERIFIED; if you are not sure which app a key belongs to, tell the assistant and do not say yes).')
rsub('E-37', 'your own list of every file in which you saved a copy of the secret key for the model, each with its full path.', 'your own list of every file in which you saved a secret (the secret key for the model, a password, or any other secret that the take uses), each with its full path.')
why_add('E-37', 'Round 16 (stranger minor, security m8): which key belongs to which app is marked UNVERIFIED; the own list holds the files that hold a secret you saved, not only the key for the model.')

# ---------- E-62: input line 112
NEW62 = '''### E-62: OWNER-STEPS-realrun-v3.md, line 112, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
delete any leftover HubSpot contacts the lead counted
~~~~
NEW (exact):
~~~~
delete any leftover HubSpot contacts that the assistant counted, and only those whose e-mail address is exactly `take-<id>-a@example.com`, `take-<id>-b@example.com` or `take-<id>-c@example.com` (with the id of the take that failed). If you find more than 3 such contacts, or any other contact, you delete nothing and tell the assistant
~~~~
Why: Security F2 of round 15: input line 112 (step 20) told the owner to delete "leftover HubSpot contacts the lead counted" with no limit on which contacts, while E-04 and E-42 (held on gate G1) limit them to the take's exact addresses. This row is Apply now because step 20 is about a failed take, which can leave contacts whatever the final code does; the rule is the same exact address, at most 3. The old text is part of line 112 and occurs once there; E-57 and E-12 do not overlap it.
'''
sub('\n## Lines checked and found consistent', '\n' + NEW62 + '\n## Lines checked and found consistent')
sub('| E-61 | OWNER-STEPS-realrun-v3.md | 144 | Apply now | - | - | STALE |', '| E-61 | OWNER-STEPS-realrun-v3.md | 144 | Apply now | - | - | STALE |\n| E-62 | OWNER-STEPS-realrun-v3.md | 112 | Apply now | - | - | CONTRADICTION |')

# ---------- counts
sub('## Counts (computed by script, `resolve-r15.md` and `resolve-r15-check-output.txt`)', '## Counts (computed by script, `resolve-r16.md` and `resolve-r16-check-output.txt`)')
sub('59 rows in total: E-01 to E-61 without E-10 and E-35. By file: OWNER-STEPS 40 rows,', '60 rows in total: E-01 to E-62 without E-10 and E-35. By file: OWNER-STEPS 41 rows,')
sub('**Apply now 47**', '**Apply now 48**')
sub('**Conditional 0**; total 56.', '**Conditional 0**; total 60 (48 Apply now and 12 Hold).')
sub('The Apply now ids (47) are:', 'The Apply now ids (48) are:')
sub('E-59, E-60, E-61. Round 15 added E-59', 'E-59, E-60, E-61, E-62. Round 16 added E-62 (step 20, input line 112: the owner deletes leftover contacts only by the exact take addresses) and rewrote E-48 (key steps A to K are shorter and their detail moved to Appendix K; the new word `key gone, no more decisions`; the one numbered order; shred done 1 and 2), E-04, E-11, E-12, E-16, E-23, E-37, E-42, E-54, E-55, E-56, E-57, E-59 and E-60 and the rules R7 and the confirmations o, p and q. Round 15 added E-59')

# ---------- definition of latest start (line 30)
sub('so a start at 18:00 UTC = 23:30 IST ends about 4 minutes 40 seconds before the last time to revoke, on a duration that is a reading and not measured)', 'and 18:00 UTC = 23:30 IST is the time at which the owner STARTS TYPING; the program starts about 1 minute later, 18:01 UTC = 23:31 IST, and ends about 18:15:20 UTC = 23:45:20 IST, 3 minutes 40 seconds before the last time to revoke, on a duration that is a reading and not measured)')

# ---------- confirmation o and p, q
sub('leaves 4 minutes 40 seconds before the last time to revoke (18:19 UTC = 23:49 IST) if the take lasts 860 seconds (it would end at 18:14:20 UTC = 23:44:20 IST); 860 seconds is a reading of the take program, not measured, and the margin ignores the time to type `y`, the confirmation number and the take id.', 'is the time at which the owner STARTS TYPING; with about 1 minute of typing the program starts at 18:01:00 UTC = 23:31:00 IST and, if the take lasts 860 seconds, ends at 18:15:20 UTC = 23:45:20 IST, which leaves 3 minutes 40 seconds before the last time to revoke (18:19 UTC = 23:49 IST) (round 15 said 4 minutes 40 seconds and ignored the typing; round 16 corrects it); 860 seconds is a reading of the take program, not measured. STILL OPEN: this confirmation is not answered; confirm 18:00 UTC = 23:30 IST or give an earlier time.')
sub('letters run a to p without gaps', 'letters run a to q without gaps')
T = T.replace('(5) the new rows E-59 to E-61.', '(5) the new rows E-59 to E-61.\n\nq. Round 16 additions of the builder, to confirm: (1) the word `key gone, no more decisions` counts at any time, and `key revoked` counts as the confirmation only after 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 with no `no more takes` typed before it (security F1); (2) `shred done 1` = parts (a) and (b), `shred done 2` = parts (c) and (d) (security F3, F4); (3) the contacts the owner may delete are only `take-<id>-a`, `-b`, `-c` at the example domain, at most 3 (security F2, row E-62); (4) route B keeps a live paid key and its copy on the laptop for up to five days; the exposure is stated in ND15 and is not removed, because the retake value is the owner\'s choice; (5) the new row E-62.', 1)

# ---------- R7 and ND15
rsub_all = None
sub('The owner\'s two alarms (key step C: 17:49 UTC = 23:19 IST on 23 Nov, and a repeating evening alarm from the first take) are the only reminders', 'The owner\'s three alarms (key step C: 17:49 UTC = 23:19 IST and 18:09 UTC = 23:39 IST on 23 Nov, and a repeating evening alarm from the first take) are the only reminders')
sub('and `shred done` (or `shred not done`). The studio lead writes the outcome', '`shred done 1` and `shred done 2` (or `shred not done 1` or `shred not done 2`) in the order of the card (key step C). The studio lead writes the outcome')
sub('Risk of B:', 'Risk of B:') if False else None
sub('risk of B: a live paid key and its copy stay on the disk longer,', 'risk of B (exposure kept on purpose and stated): a live paid key and its copy stay on the disk and in the chat of this laptop for up to five days, where any program that runs under the owner\'s Linux user can read them;')

# ---------- what I did not check
T = T.rstrip('\n') + '\n- Round 16 added: nothing was run except text, count, weekday and time-pair checks by script (`resolve-r16-check-output.txt`; `verify16.py` has negative controls, among them the nine mutations that `verify15.py` missed). I did not run any program of the take, did not read the take code, and did not check any click path (the key list page of the model provider, the clipboard sharing setting). Not finished in round 16, stated plainly: see `r16-CHANGES.md` (the list of open items first).\n'

# ---------- Appendix K (detail text, nothing deleted)
APP = '\n## Appendix K: the detail of the key steps (round 16)\nThe owner reads key steps A to K in row E-48. Where a key step says "Detail", the text is here. Nothing was deleted; the detail was moved.\n\n' + '\n\n'.join(APPX.values()) + '\n'
sub('\n## Lines checked and found consistent', APP + '\n## Lines checked and found consistent')
