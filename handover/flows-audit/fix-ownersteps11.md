# fix-ownersteps11 log (Sonnet fixer; static; nothing run live)
Backup: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/bak-os11/OWNER-STEPS-q16-rows.md
## Changes (owner part only, in OWNER-STEPS-q16-rows.md)
- M1 clean-up/revoke: exception for answering retake yes added to row 4, row 7, item 4 and the chase list.
- M2 two facts: owner asks both as soon as clean-up starts arrives; lead answers by 16:00Z (21:30 IST); rule if (a) is no or (b) loses credits: do not revoke; owner writes missing: credits answer first at 17:00Z, lead after at 17:30Z; wrong cross-reference replaced by the chase list.
- M3 rows 1a and 1b: own message time, own missing words (delete message 1 08:30Z; delete message 2 12:00Z), no circular 'as 1a'; table, items and chase list carry the same.
- M4 cannot-reply words added to rows 1a and 1b and item 1.
- M5 recording message: retake question added to item 5.
- M6 'six' now 'seven': item 7 (retake decision) added; rows reordered by time; read-only rows named; silence line 75 reworded.
- Nits: IST explained at first use (line 9); studio rule explained.
## Consistency script output (script: /tmp/claude-0/-home-user/9d809a30-0790-5792-93c1-8c5abd22e849/scratchpad/cons.py). 'near' columns take every UTC time within 200 characters, so they include neighbouring times; the real trigger times are the ones that agree across columns.
word                           | table(near)    | items(near)    | chase     | present in prose
missing: GO or NO-GO           | 16:00          | -              | 16:00     | yes
missing: by when               | -              | -              | -         | yes
missing: clean-up message      | 14:00,17:00    | 14:00          | 14:00     | yes
missing: credits answer        | 08:00,17:00,17:30 | 17:00,17:30,18:29 | 17:00     | yes
missing: delete message 1      | 08:30          | 08:30,12:00    | 08:30     | yes
missing: delete message 2      | 12:00          | 08:30,12:00    | 12:00     | yes
missing: item 3 message        | 09:15,09:30    | 09:15,09:30,09:45 | 09:30     | yes
missing: re-check done         | 10:00,14:00    | -              | 10:00     | yes
missing: re-check time         | 10:00,14:00    | -              | -         | yes
missing: recording message     | 12:30          | 12:30,13:00,15:00 | 12:30     | yes
missing: reply words           | -              | -              | -         | yes
missing: safety test result    | 08:00,08:30    | -              | 08:30     | yes
missing: take-prep message     | 08:00,08:30    | -              | 08:00     | yes
missing: typing message        | 09:30          | 09:30          | 09:30     | yes
missing: what y confirms       | 09:30          | 10:00,11:15    | -         | no
missing: where to look         | -              | 07:00,08:00,08:30 | -         | no
missing: where to reply        | -              | -              | -         | yes
## Commands: check_secrets rc=0 (PASS 0 hits); check_refs rc=0 (PASS 5146 references); ruff check . rc=0; ruff format --check OWNER-STEPS-q16-rows.md rc=0
## Not checked: no independent re-read; the lead's part (line 106 onward) untouched; no commit.
