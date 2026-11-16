# fix-rwct31: round 31 fixes to RUNSHEET-WORDING.md (RW) and CLAIMS-TABLE.md (CT)
Fixer: one agent (Sonnet 5.5). Edited only RW and CT. Nothing committed. EGM skipped for this pass as a mechanical wording fix inside a review round already running under EGM (lead runs the next review).

## Failures and uncertainty first
- Nothing failed. All required checks pass (raw output below).
- NOT verified by me: every relayed figure (12 of 20, 2 of 5, 0 of 15, 1 of 5, 3 of 10, the K1 medians) stays relayed; I saw no raw files. The facts that the desk harness deletes only with --cleanup, and that the n8n step CrmUpsert has a HubSpot credential entry, are taken from CT text (CT lines 125, 209; B-062), not from the code or a run.
- M2 is only half-fixable: I made every string say WHICH identity is read-only (the HubSpot login of the take scripts) and that this says nothing about the n8n step CrmUpsert. Whether the CrmUpsert login is the same login, and whether it could delete, is not written anywhere I read. It stays "NOT WRITTEN: LEAD FILLS" (new question below).
- M10 uses two reading choices that I took from CT: "recovery attempt" = alert_attempts (a lead ends failed or unknown at 3, CT P4a line and B-150 rows), and "try" = per-step retries. The flows were not run.
- Section totals (330 = 102/64/84/15/65, 45 rows, 87 rows) were NOT changed. M1 proved only the "has a row" split wrong, not the verdict totals.

## Finding to result table
| Finding | Checked against file/script | Result |
|---|---|---|
| M1 count claim | Script (scratchpad m1.py): ids named in the claim-id column of the 87 to-do rows of Tables 1 and 2 = 97; rowless = 233 = SUPPORTED 100, RELAYED-ONLY 63, UNTRACED 54, OVERSTATED 16. B-032 and B-056 are in rows 15b and 15c. Reviewer was right. | CT "What this file is" and "Count (by script)" paragraphs: 95 -> 97, 235 -> 233, 18 -> 16, 81 -> 83 (84 + 15 = 99, minus 16), "95 claims in all" -> "97 claims in all (83 + 14)"; B-032 and B-056 removed from both lists of rowless ids (a sentence says why). 16 ids listed in both places = script list. |
| M2 read-only identity | Confirmed: B-062/CT 4 shows CrmUpsert has a HubSpot credential and upserts contacts | All strings in RW (93? defs at lines 23, 94, 115, 128, 360, 378, 381, 422, 423) and CT (4, 94-area, 125, 190-area, 288-290, 320, 775, 807, 969-971) now say "the HubSpot login of the take scripts is read-only (this says nothing about the n8n step that creates the contacts)"; take identity redefined in RW lines 23 and 94 and CT item 4. Remaining gap: new question Q-new-1. |
| M3 "still deletes" | CT 125/209: deletes only with --cleanup, default off, read in code | All 12 CT and 10 RW occurrences now: "deletes contacts only when started with --cleanup (off by default; read in its code, not observed); the take does not delete." The "take itself still deletes nothing" at CT 192 was already true and stays. CT 91 (restore unknown) already says UNKNOWN; unchanged. |
| M4 A-057 alert repeat | RW 395, 396, 406, 408 and CT row 30: repeat only if the follow-up table update fails (F-014) | A-057 string (RW A-057 row, CT row 24 and lane row A-057) now: "The alert can be sent more than once if the follow-up update of the lead table after the alert fails." |
| M5 D2 moot | CT 64, 141, 151, 179, 181 say open | CT 130 and the D1 to D3 definition (162): "D2 open with a default and moot only for the caption figures". |
| M6 "12 of 20 and 2 of 5 runs" | CT 165: variants a to e are test set-ups of n8n's duplicate removal, not the take's flows | Every occurrence (RW 6, CT 7) now "12 of 20 and 2 of 5 bursts of variant a (a test set-up of n8n's duplicate removal, not the take's flows)"; "runs of variant a" -> "bursts of variant a" in RW 252, 273. B-195 string already said bursts and variant a; unchanged. |
| M7 B-197 "no effect" | CT row 74 note and file table call it kill rows where no client lost its connection | B-197 string (RW, CT row 74, CT lane row) now keeps the file's words and adds that the file's results table calls the count "kill rows where no client lost its connection" and does not define no effect. |
| M8 B-198/199/200 | CT 119, 127: nothing run by this audit | RW notes now say "the file's own rerun ... relayed, not run by this audit". |
| M9 A-059 sources | CT B-099 (v3 flows, V7) and P:155 (lane3, film-v4) are two relayed sources | A-059 string (RW, CT row 41, lane row) now "Other test sessions reported similar CRM-error cases on older flows (one on the version 3 flows, one on the film flows of version 4); we have not seen their raw files." |
| M10 "tries" | RW 391, 400 per-step; B-150c, CT P4a attempts | Defined in RW words line 23 and CT Parts of the system: try = one go of one step; recovery attempt = one pass of recovery (alert_attempts). B-150c string, CT A-095, CT P4a text, RW T8 note changed to "recovery attempts". Quoted file text ("after 3 tries" inside the alert body) left as quoted. |
| Small: WL-6 | RW A-050b and A-051b are SUPERSEDED | CT WL-6 says A-050a/A-051a DELETE and A-050b/A-051b SUPERSEDED. |
| Small: CT 12 garbled | RW 432 names the column "What the owner does" | Rewritten to name that column. |
| Small: RW 443 "his" | lead is a Claude session | "its" at RW 278, 443 and CT 69. No other he/his/him in RW. |
| Small: RW 432 pointer | "Who decides what" is under Quick words, not Start here | "section Quick words" at RW 93 (twice) and 432. RW 432 also said the owner is "the person who films", but the CT bullet says edits and posts: fixed. |
| Small: CT 736 B-032 | cell quoted relayed K1 figures | Cell now starts "Safe wording is only the paste string at the end of this cell; the rest is for the lead only, never said or shown (relayed figures)." |

## Raw output (from handover/flows-audit)
```
check_refs.py: PASS 5177 references
check_names.py: PASS 655 rows
check_secrets.py: PASS 0 hits in 2718 files
check_rw_ct_pairs.py: paste strings in RW: 142 | found word for word in CT: 142 | not found in CT: 0
check_runsheet_paste.py: total rows: 197; flagged ids with no row here: []; UNTRACED ids with no row 53; RESULT: PASS
claims-count.py: verdicts UNSUPPORTED 15, OVERSTATED 84, UNTRACED 65, SUPPORTED 102, RELAYED-ONLY 64 total 330; lanes A 100, B 226, X 4; to-do rows 87; offenders 0; ids 330 unique 330
check_counts.py: PASS 52 files / 655 nodes
ruff format --check .: 866 files already formatted
```
M1 script output: `87 97 []`, `rowed OVERSTATED 68, UNSUPPORTED 15, UNTRACED 11, SUPPORTED 2, RELAYED-ONLY 1`, `rowless SUPPORTED 100, RELAYED-ONLY 63, UNTRACED 54, OVERSTATED 16 (233)`, rowless OVERSTATED ids: A-002 A-003 A-010 A-015 A-024 A-045 A-049 A-074 A-096 B-003 B-086 B-102 B-107 B-126 B-140 B-155. The phrase "one database" appears in RW only in prose at lines 3 and 226 (about the ban), not in any paste string (paste check passes).

## Not checked
RW 1-321 and 452-558 and CT 468-629, 880-end were not re-read by me beyond grep-driven edits; a grep for each changed phrase shows no leftover old wording (`still deletes`, `sending it fails`, `runs of variant a`, `Start here, paragraph Who decides what`, `his own`).

## Proposed new question for Q31 (text only; QUESTIONS.md not edited)
Q-new-1 (M2): "In the n8n flow step CrmUpsert, which HubSpot login (credential entry) creates the contacts, is it the same login the take scripts use (the read-only one), and what may it do (create, update, delete)? If it is a different login, please name its permissions in plain words. Until you answer, every sentence says only that the take scripts' login is read-only." Needed by: rows B-067, B-091, B-213, B-215, B-215b and the take identity definition.
