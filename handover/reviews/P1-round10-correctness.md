# P1 ticket rev 11, round 10 correctness review

Status: saved by the lead from the reviewer's hand-back (condensed). Reviewer read all 328 lines of P1.md, LEAD-ORDERS and the snapshot textnorm.py, _confusables.py, runmap.py, egress_text.py. Not read: handover/reviews/. Verdict: NOT CLEAN, 0 Blocker, 2 Major, 5 Nit. All recounts match (86 distinct, runs 114+k max 132, P1a 18, P1b 19, constants 9 to 5, public names 21, 29 rows cut, 12 added). All snapshot cites checked match; ce70eb5 cites UNVERIFIED (not in snapshot).

| id | sev | finding | fix |
|---|---|---|---|
| COR-R10-1 | Major | Lines 71, 128, 172: the JSON-escape example reads as the plain digit (the backslash-u escape was lost in the rev 11 script edit). A row asserting a literal `1` is "not found" cannot pass; mutant "JSON escape decoded" has no killer that can fail. `\x31` and `%31` survived. | Restore the escape as backslash-u 0031 (write it as words if needed); re-check the row against `scan_keyset("<JSON-escape>2345")` not equal to `scan_keyset("12345")`. |
| COR-R10-2 | Major | Line 282 relay lists five stale P2d lines (3, 34, 264, 315, 334); P2d.md also has lines 30 and 33 (depends-on table, merge list without P1b). | Relay says "every statement in P2d.md that P2d-2 does not depend on P1b (at least lines 3, 30, 33, 34, 264, 315, 334; author greps P1b)"; drop "five, not four". |
| COR-R10-3 | Nit | Line 133 `FOLDERS` is not in `__all__`; line 39 underscore test would fail. | Delete or rename `_FOLDERS`. |
| COR-R10-4 | Nit | Line 80 names `LOOKALIKE_MIN_KEY_CHARS` and `LOOKALIKE_KINDS`; the design names `LOOKALIKE_MIN_RAW_CHARS`, `LOOKALIKE_MIN_KEY_CHARS`, `LOOKALIKE_WORD_KINDS`, `LOOKALIKE_BUDGET_S` (design may change in draft 7). Lines 282, 318 list three. | "P2d-2 adds its own LOOKALIKE_* constants (P2d-2 owns the list)", no names. |
| COR-R10-5 | Nit | Lines 287-289 UNVERIFIED section: leftovers of cut tier N in present tense (U+034F, U+17B4, U+17B5, enumeration test, "about 4.8 bytes"); leftover scan on line 315 searched only some names. | Delete or label history. |
| COR-R10-6 | Nit | Line 171: "rule 4 cap 512 raised" has no stated value (only 513 killed by R4-A); "size rule plain length" killer lists 1,000 U+FDFA rows (W = 18,000, below the cap, does not separate). | "cap raised to 513"; killers SEAM-1 (262,144 U+A516) and the U+FDFA row at line 43. |
| COR-R10-7 | Nit | Order 11(2) named negative test per table row: fullwidth, combining mark, newline split, upper/lower case are only differential-corpus classes, not named scan_keyset rows. | One sentence mapping each table row to its P1b row, or four one-line rows. |

Observation: P1.md has no "P0d"; no P0d ticket exists in handover/tickets (relay goes to P0e). UNVERIFIED whether P0d meant P0e.
