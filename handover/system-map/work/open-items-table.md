# Open items still blank or unknown in the owner and lead pages (agent table, unverified; written 16 Nov 2026 about 13:45 UTC / 19:15 IST; the 13:45 UTC stamp is unreliable; rewritten 16 Nov about 11:55 UTC / 17:25 IST after a cold read, see work/decision-list-for-lead.md D3)
Open work/decision-list-for-lead.md FIRST: it holds the questions with proposed owners and dates (sections A-G); this table holds only the leftovers from a sweep and does not copy them. No file I can read names a person; every "answerer" below is a role, and decision list A1 and A8 ask the studio head to name the people. Until then a question cannot be assigned to a person.
Words: studio lead = the Claude session that works with the owner (a session cannot be asked in person; the owner or studio head relays); owner = the human who runs the take; studio head = the person who decides for the studio; take = the one filmed real-v5 run (scenes 1-4); loopback re-smoke = the lead's own technical self-check before any rehearsal (decision 12; decision list A4 asks to start it Mon 16 Nov 14:00 UTC / 19:30 IST); rehearsal = a laptop run of the changed flows on made-up data, after the re-smoke; post = the public post, Wed 25 Nov 15:00 UTC / 20:30 IST; UNKNOWN = no file states it; LP-1..LP-5, D-05, L-02, F-002, ORDER 013 = items on LEAD-PAGE.md; Row C1 and step 11.7 = rows of TAKE-BLOCKERS.md and the re-smoke plan; `$vars` = n8n's way for a flow to read a setting; UNVERIFIED list = the unnumbered list at TAKE-BLOCKERS.md:55; v3 = the old owner steps file (decision 10: archive it, never delete).
Source: a read-only agent sweep of README.md, LEAD-PAGE.md, TAKE-BLOCKERS.md, OWNER-VIEW.md and the two cards. Line numbers can shift after edits. The sweep was case-sensitive, so lowercase "open" is not covered.
Rows settled by the decisions of 16 Nov are struck out below and kept only for the record.

| # | Question (yes/no or pick one) | Where | Answerer (role) | Answer by (UTC / IST) | Blocks the take start? |
|---|---|---|---|---|---|
| 1 | Will a named builder finish row 1 (filled patched flows) by the date given? Name and date: ____ | README.md:3, TAKE-BLOCKERS.md row 1 | studio head | Tue 17 Nov 12:00 UTC / 17:30 IST (proposal) | yes (row 4 and run (b) wait for it); decisions 7 and 12 may already make the studio lead the builder: confirm yes/no |
| 2 | Send the owner the HubSpot check line: yes/no? (the login-key part is dropped: decision 3 parks the four logins; the delete part is moot: decision 2) | OWNER-VIEW.md:27, TAKE-BLOCKERS.md row 5 | studio lead | Tue 17 Nov 12:00 UTC / 17:30 IST (proposal) | yes while open |
| 3 | Do the flows read their settings through `$vars`? yes/no | TAKE-BLOCKERS.md:33 | row 1 builder | with row 1 | not stated |
| 4 | Does Row C1 still apply against step 11.7? yes/no | TAKE-BLOCKERS.md:47 | studio lead | Tue 17 Nov 12:00 UTC / 17:30 IST (proposal) | indirect |
| 5 | Who works through the UNVERIFIED list: plan author or studio lead? pick one | TAKE-BLOCKERS.md:55 | studio lead | Tue 17 Nov 12:00 UTC / 17:30 IST (proposal) | not stated |
| 6 | How does the receiver Gmail account look before a Trash delete? Write one sentence. (The card is unsafe while this is empty; decision 2 covers HubSpot only, so confirm yes/no that the Gmail delete stays.) | OWNER-RUN-DAY-CARD.md:31 | studio lead | Tue 17 Nov 12:00 UTC / 17:30 IST (proposal) | card unsafe while empty |
| ~~7~~ | ~~Proof screen candidates~~ SETTLED by decision 9: a rehearsal screenshot or the Postgres node preview | OWNER-RUN-DAY-CARD.md:35 | | | |
| 8 | Who films: owner or someone else? pick one | OWNER-RUN-DAY-CARD.md:35 | owner | Tue 17 Nov 12:00 UTC / 17:30 IST (proposal) | not stated |
| 9 | How does the studio lead see the pause: (a) shared screen, (b) a log line, (c) the owner says it aloud? pick one | OWNER-RUN-DAY-CARD.md:49 | studio head | Tue 17 Nov 12:00 UTC / 17:30 IST (proposal) | step 17 depends on it |
| ~~10~~ | ~~How the demo HubSpot account looks before a delete~~ MOOT under decision 2 for the take (the owner's by-hand delete after the take still needs the account check; ask in row 6 style) | OWNER-RUN-DAY-CARD.md:59 | | | |
| 11 | LP-1: demand a shared form code? yes/no | LEAD-PAGE.md:45 | owner | Tue 17 Nov 12:29 UTC / 17:59 IST | not stated |
| 12 | LP-3: keep or archive extract.py? pick one (can wait until after the take) | LEAD-PAGE.md:47 | owner | after the take | no |
| 13 | LP-4: accept the crash risk (D-05) in writing, or wait for the crash test? pick one | LEAD-PAGE.md:48 | owner | Tue 17 Nov 12:29 UTC / 17:59 IST | post only |
| ~~14~~ | ~~LP-4 build estimate 20 h / 41 h~~ STRUCK: the estimate comes from v3 (decision 10) and decision 1 narrowed the scope | LEAD-PAGE.md:48 | | | |
| ~~15~~ | ~~LP-5 session can read take secrets~~ SETTLED by decision 5 (S9-5, S9-12: the lead reads only masked outputs; owner-only secrets) | LEAD-PAGE.md:49 | | | |
| ~~16~~ | ~~Click paths in v3 lines 178-193~~ MOOT: v3 is archived by decision 10; re-point to v4 or v5 | LEAD-PAGE.md:55 | | | |
| 17 | F-002 effect and ORDER 013 text: define each in one sentence or remove the reference. yes (define) / no (remove) | LEAD-PAGE.md:62, :72 | studio lead | Tue 17 Nov 12:00 UTC / 17:30 IST (proposal) | no |
| ~~18-19~~ | ~~C-01 full fix~~ CUT by decision 4 | LEAD-PAGE.md:64 | | | |

Overdue note: decision list A4 was due Mon 16 Nov 13:00 UTC / 18:30 IST. Status: UNKNOWN (no answer in any file I hold).

Digest 385 still open: add a Person column (studio head names owner, builder, filmer by Tue 17 Nov 12:00 UTC / 17:30 IST); rows 1, 4, 6, 9 need rewording as strict yes/no; a row for who checks the demo HubSpot account before the owner's by-hand delete; one-line glosses for shared form code, D-05, crash test, the pause, Row C1.
