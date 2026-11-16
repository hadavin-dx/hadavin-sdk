# fix-claims10 (fixer, CLAIMS-TABLE.md only), 2026-11-16
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/CLAIMS-TABLE.bak. Not committed. RW wins everywhere.

## Changes
- A-083 (row 42, lane row): status HELD, named wait A-073a, 19-vs-20 statements note.
- B-037 (row 49, lane row): full real old sentence; note that the paste drops IMAP, Postgres, model setting; RW status PASTE.
- B-196 (row 73, lane row): full real line with list dash and bracket; delete the whole line; RW status DELETE.
- A-057 (row 24, lane row): RW status HELD; laptop agent runs the Q16 psql check, lead reads it, not a studio owner step.
- A-021 / A-077 (row 23, lane rows): A-021 HELD; page version is A-077b (P:153), A-077a is P:150; A-021 lane replace cell set to the RW string word for word.
- A-024 (lane row): RW status DELETE, only 'One alert mail arrives.'
- Live rows section: new bullet with these statuses and the counts PASTE 53, DELETE 30, HELD 85, NO PASTE 5, SUPERSEDED 12.
- Extra (not on the list): paste strings added to lane rows A-080 (P-155), A-055 (V-57), B-062 (V-11), B-003 (B-003a, B-003d), copied from RW, to cut 'not found in CT' from 18 to 13.

## Not fixed
13 RW rows still not found word for word in CT: N-5a, N-6, N-9, N-10, N-11b, X-6a, X-6b, X-6c, S5-voice, N-4c, N-2, S5-a, S5-b. They are RW-only note or new rows with no CT lane row; not in the RW fixer log, so left; a fixer would need to add a CT home for them (decision of the lead).

## Raw output
$ python3 -I tools/check_rw_ct_pairs.py RUNSHEET-WORDING.md CLAIMS-TABLE.md
paste strings in RW: 136 | found word for word in CT: 123
not found in CT: 13
  RW line 231 N-5a / HELD / APPROVED: ____: n8n lets another run take over a lead that stopped only after a waitin
  RW line 233 N-6 / PASTE / APPROVED: ____: A CRM is the program where a company keeps its customer contacts.
  RW line 234 N-9 / HELD / APPROVED: ____: the real wait is read from the rehearsal, never predicted; no phone is
  RW line 235 N-10 / HELD / APPROVED: ____: wherever a wait is sped up, the screen shows the words sped up; the re
  RW line 237 N-11b / HELD / APPROVED: ____: Waits for the takeover with no timer on screen, then cuts or speeds up
  RW line 315 X-6a / PASTE / APPROVED: ____: recovery wording: no time or estimate is quoted; the recording shows n
  RW line 316 X-6b / PASTE / APPROVED: ____: No recovery estimate is quoted, because nothing is measured at 45 s.
  RW line 317 X-6c / PASTE / APPROVED: ____: Decided (decision 1): no recovery estimate and no recovery number goes
  RW line 452 S5-voice / HELD / APPROVED: ____: The CRM and the mailbox in this scene are test copies.
  RW line 457 N-4c / HELD / APPROVED: ____: An alert e-mail message goes to the person who receives the alerts.
  RW line 479 N-2 / HELD / APPROVED: ____: the SMTP stand-in with .drop = 1; scene 10 shows a rehearsal screensho
  RW line 493 S5-a / HELD / APPROVED: ____: Stand-in CRM: a test copy of the customer list
  RW line 494 S5-b / HELD / APPROVED: ____: Test mailbox: not a real mailbox
$ check_runsheet_paste
claim ids marked UNSUPPORTED, OVERSTATED, DELETE or STALE in CLAIMS-TABLE.md: 86 | with no row here: []
claim ids marked UNTRACED there: 48 | with no row here: 41 (scope: UNTRACED claims have no safe wording, so they get a row only when a file sentence had to change)
RESULT: PASS
$ check_refs
PASS 5166 references
$ ruff format --check .
621 files already formatted
$ claims-count
to-do rows: 87
offenders: 0 []
ids: 327 unique: 327
Before: not found in CT = 18; after: 13.
