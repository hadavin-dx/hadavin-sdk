# M17: the take never deletes (decision 2); replacement lines for "end"
Written Mon 16 Nov 2026 by the system-map session from a read-only agent report (UNVERIFIED against the program: `scripts/run_real_check_n8n.py` is not in this checkout; only docs name it). Reader: the studio lead. Made-up data only.
Rule being applied (lead ANSWERS 16 Nov 10:13Z, item 1): `end` only closes the film pause. The program deletes nothing. It prints the leftover made-up contacts by lead key and contact id. The owner deletes them by hand after the studio lead's list.
Files marked V5 are owned by core-hardening (this session does not edit them): V5 = inputs/OWNER-STEPS-realrun-v5-core-hardening.md. RDC = OWNER-RUN-DAY-CARD.md, OV = OWNER-VIEW.md, OCC = OWNER-CLEANUP-CARD.md (this session's own; held until the run-day card rewrite lands).

| File | Line | Old (start of text) | New |
|---|---|---|---|
| V5 | 31 | "The program's own screens say "archive" for the contact deletion; it means delete. HubSpot may keep a recoverable copy..." | Delete both sentences. Say: you delete the HubSpot contacts by hand; the program deletes nothing. |
| V5 | 43-44 | "F: the film pause; you type `end` only when..." / "After the run: G, H, I, J" | Add: "`end` only closes the pause; the 3 made-up contacts stay in HubSpot until you delete them by hand from the studio lead's list." Add a step "delete the leftover contacts" after F. |
| V5 | 114 | "up to 3 contacts deleted at the end" | "up to 3 contacts left in HubSpot for you to delete by hand" |
| V5 | 124 | "...ENDS the pause and DELETES the test contacts from HubSpot BEFORE they are filmed." | "...ENDS the pause. The program deletes nothing; the 3 contacts stay in HubSpot. Type `end` only when filming is done, because the pause cannot be reopened." |
| V5 | 127 | "type `end` and press Enter to archive" (it means delete)... "The program then deletes this run's contacts." | New prompt wording to be set with the program; "The program then stops the pause and prints the leftover contacts by lead key and contact id." A second wrong line ends the pause (nothing deleted). |
| V5 | 128 | "HubSpot show no contacts of this run afterwards" | "HubSpot still show the 3 contacts of this run, and the program print the list of leftover contacts" |
| V5 | 129-130 | early close "Leftover contacts are deleted by hand..." / "If the HubSpot key ... cannot delete contacts..." | Keep 129 with "always deleted by hand". Remove 130 (the take key is read-only, decision 2). |
| V5 | 137 | "delete any leftover contacts the studio lead counted" | Now the normal route after every run, not only a failed one; rule: only contacts whose email is exactly the listed address. |
| V5 | 182 | send table, "After a failed run" | Add row: after `end`: "contacts deleted" and the number. |
| RDC | 19 | "up to 3 contacts deleted at the end" | "up to 3 contacts left for you to delete by hand" |
| RDC | 24-27 | "THE PAUSE: DANGER, `end` DELETES THE 3 CONTACTS", step 13 "archive", step 14 "`end` cannot be undone", step 15 "check that HubSpot shows no contacts" | "`end` ONLY CLOSES THE PAUSE; you delete the 3 contacts by hand afterwards"; remove the "archive" and recoverable-copy sentences; step 15: contacts are still in HubSpot, wait for the studio lead's list, delete by hand under the step 16 rules, reply "contacts deleted" and the number. |
| RDC | 30 | release word "demo mails may be deleted" covers Gmail and HubSpot | The lead decides whether one word or two covers the after-`end` contact deletion. |
| OV | 8, 17 | "(7) you type `end`" / "typing `end` DELETES the 3 contacts" | Add "(7b) the studio lead sends the list of leftover contacts and you delete them by hand." / "typing `end` closes it; you delete the 3 contacts by hand afterwards." |
| OCC | new | no step for leftover contacts | Add step 3a: delete only the contacts the studio lead listed, email exactly `take-<run name>-a@example.com`, `-b@`, `-c@`; new release word set by the studio lead. |
| LEAD-PAGE | 6 | "...asks you to confirm and archives its own contacts afterwards;" | "...asks you to confirm, and at `end` only closes the pause and lists leftover made-up contacts by lead key and contact id; the owner deletes them by hand;" |

Open: the program itself (notice line, prompt) must change to match; no file in this checkout is that program, so who changes it is a question for the lead. Until it changes, the owner pages must not say the text above as fact about the program.

## Corrections after a cite check (16 Nov, an independent read of every row)
- Row V5 43-44: line 44 is really "7. After the run: G (only if it failed), H (watch the edited video), I (clean-up), J (post)." Quote it that way.
- Row LEAD-PAGE: the "take script" text is on LEAD-PAGE.md line 9, not line 6.
- Also still says "deleted" at `end` and is NOT yet in the table above (to be added to the same edit pass): V5 line 124 start of the warning ("closing the terminal, Ctrl-C or two wrong words in a row ENDS the pause and DELETES the contacts"); V5 line 127 second half ("a second wrong line also ends the pause and deletes the contacts. Closed input on the first prompt ends the pause at once"); V5 line 138 ("the number of contacts you deleted", a failed-run reply, fine if the owner deletes by hand); OWNER-RUN-DAY-CARD lines 25 and 27 (ends the pause "and delete the contacts"; "the program's own screen says archive where it means delete"; "if the HubSpot key used cannot delete contacts, the deletion can fail after the sends").
- The OCC (clean-up card) row cites no old text and was not checked.
