# DOCS notes (docs builder, branch wip/cloud-core-c/docs from origin/cloud/core-c beb2b3ea6)

Code described: 2552bcc95 (last change to src and tests, 2026-11-20 15:44 UTC). Docs only: no src or test file was edited.

## What was written
- `handover/core-c/SECURITY-README-v8.md` (new; v7 kept, only its brand string removed): v7 brought in line with G13c, G12c, G9b, G4c, the gate mutant repairs, the PU1 re-pin (REC), G8T and TIDYT. K ids unchanged (K1 to K85). Change log in its 4.8, sources that disagreed in 4.4 items 18 to 25, open items in 4.6. Status counts now PINNED 24, STATED 13, WAITING 7, OPEN 18, FIXED 23 (v7: 23, 13, 7, 20, 22): K36 OPEN to FIXED, K85 OPEN to PINNED.
- `handover/core-c/CHANGELOG-lines-v8.md` (new): v7 blocks C1 to C22 revised (C15, C16, C17, C19 and C11 changed; C18 host note removed), plus C24 (host names) and C25 (tests: gate breaks repaired, PU1). Headings carry no ticket codes.
- Repo root: `SECURITY.md` (contact paragraph kept, stated limits corrected, v8 part 2 appended without `[INTERNAL]` lines), `CHANGELOG.md` (v8 blocks added under Unreleased, in the first "Upgrade steps" and "Changed" sections; the "K5-core, stated limits of redaction" entry corrected in place; one host-name sentence of an older entry updated), `README.md` (a "Checking your Python" subsection from part 3, base64 and host names in the "Limits and trust" redaction bullet, a cost figure and the run-map cap corrected).
- Evidence files `evidence/G4-build-notes.md` and `inputs/evidence-cfull.md`: one token replaced (the vendor brand string in a quoted test failure) so the brand test names fewer files.

## How the facts were checked
- Probes: direct `runmap.redact_text`, `runmap.enforce_map` and `runmap.held_value_left` calls on Python 3.13.18 (`/usr/local/bin/python3.13`, Unicode 15.1.0) with `src` of this checkout. Scripts were in the scratchpad, not committed. Examples re-measured: K2, K3, K4, K36 (44 host rows: 7 still have a readable label, host-06, -08, -09, -10, -15, -16, -42), K43, K70 (incl. `+44 ... 0958.Thanks` partial mask and `tok 4155550132.-Ab9`), K71 (a letter also sets a UUID off), K75, K76, K77, K78, K80 (separators, auth words), K84, K85 (`the quick brown fox`, dense shape gives `InputTooLarge`), K46 and the stated-limits section.
- Line references of v7 were moved to the head by a script that follows `git diff -U0 fd1fb3e31 HEAD` per file; 18 references that fall inside a changed stretch carry `[re-check]`. The entries rewritten in v8 (K36, K64, K70 to K73, K77, K80, K83 to K85) were read from the head. The other references were NOT individually re-read: UNVERIFIED beyond the script's logic (spot checks of `_touching_piece`, `held_value_left`, `_bare`, `_read_back`, `_SETTLE_ROUNDS`, `NO_MAP`, `MODE_ENFORCED`, two test names matched).
- Doc tests: `pytest -k "changelog or security or readme or brand or docs"`, plus `tests/test_k5_fixes4.py`, `test_textnorm_meta.py`, `test_stage_names.py`, `test_k1b_cli.py` (README line) and the CHANGELOG pin tests of `test_textnorm.py` and `test_mutation_runner.py`: all green except `test_no_vendor_brand_string_is_tracked`. That test was red before this pass (five handover files held the brand string; it is not a code defect). After this pass two files still hold it: `handover/BRIEF-PREAMBLE.md` (the lead's) and `handover/core-c/STATUS-BOARD.md` (written by the board script). They are not changed here. Nothing in the root files or in v8, the lines file or these notes holds it.

## UNVERIFIED or not done
- No whole-suite or perf run was made. The only batch figures used are the board's (STATUS-BOARD.md line 4: 16,071 passed 2 failed, commit not named; perf 96 passed at 2552bcc95). The G13c, G12c builds report no pass counts for their new tests.
- No review of G9b, G12c, G13c or G4c exists on file.
- Tests added by G13c/G12c/G9b/G4c were not run by this pass; only the doc tests above.
- G12c "not done" list (named entity at a start, mixed-case cut-short entity, tags over 16 characters) is the builder's list, not re-run.
- README: the 2.2 s figure for 256 KiB of distinct IP addresses is the old measurement, not re-measured. The rest of the K5 "Limits and trust" bullets were read, not re-verified.
- The decoded-view claim of the README bullet ("Not decoded for the generic patterns: URL-encoded client PII, HTML-entity, octal or hex escapes") was left as it was; it sits beside the CHANGELOG's K5 entry that says percent and entity escapes are undone for pattern-shaped secrets. I did not resolve that older difference.

## OPEN lead questions (listed, not decided; part 1b of v8)
L-D13, L-D15, L-D17; G10 D1-D10 and the M3 factor; G4 L24-L28 and L-B8; the G4c start rule (new row); G9 L-D1, L-D6', L-D7, L-D3b; E23 numbers (new row; ESCALATIONS.md E23 still says OPEN); E17; E20 (R8); E14 constants; the G13c per-key cap 4,096 (new row); G12 6.1-6.7 and the G12c numbers (4,096 and 16, edge list; new row); G13 D1-D8; G13 round 2 letter-only minimum and refusal code (K85 is now PINNED as it is); gate (c) contract; E9 option (b); PU1 (re-pinned twice; REC asked the lead to confirm); E21. Owner: decisions 1 to 8; decision 3 is now only "should a client note on host names be sent" (the default of the earlier draft was no note; whether it still holds is OPEN). K84 (interior punctuation, `%250A`) stays OPEN: no fix is built and nobody has accepted it as a stated limit.

## Things the lead may want to look at
- Root `SECURITY.md` now holds the whole of v8 part 2 (about 600 lines, glossaries included), as the v7 strip step prescribes. It names owner deadlines (2026-11-23 12:00 UTC) that ORDERS.md and DECISIONS.md do not hold (v7 4.4 item 2). Say if you want those lines out of the shipped file.
- Part 2 still says "the project's written plan" and similar for K19, K27, K28, K30, K33; these were in v7.
- The CHANGELOG blocks are long, in the file's own style; they sit at the end of the first "Upgrade steps" and "Changed" sections, not in date order.
