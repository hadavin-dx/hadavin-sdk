# G7-F3 build notes (branch wip-f3): a phone number before a full stop

Measured through redact() on the base (scratch patch of PATTERNS), over the 101 rows, 84 K-rows, FULL_STOP F1-F6, AT rows
and the property corpus (idempotent_property CORPUS):
- Candidate A (`(?![0-9]|\.\w)` on the `+` entry only): only F3 and F4 change.
- Candidate B (the same end on all four PHONE entries: `+` entry, main entry `(?!\w|\.\w)`, `_` entry, phone-word entry):
  F1-F6 all change (masked up to the full stop: `call <PHONE_1>.`, `call tel_<PHONE_1>.`, F4 `call x<PHONE_1>.`);
  no other row of g8_cases or the property corpus changes.
Chosen: B (A leaves F1, F2, F5, F6 readable).
Over-masks accepted: a number before `.` + space / end / `)` / `,` / `.`; e.g. `ref 1234567890. Next` is now masked.
Still kept (new K85-K90): `1732095071.123`, `1234567890.tar`, `415-555-0132.5`, `+1 415-555-0132.x`, `tel_4155550132.x`, `tel4155550132.5`.
Flipped: F1-F6 pins now expect the masked output; F5/F6 strict xfails (L7) became normal passing tests.
Pins: KEEP 84 -> 90; FULL_STOP stays 6; CASES/limits unchanged.
Mutants: G8-P15..P22 added (4 end conditions back to the old end, 4 drop the `.word` rule); P5/P8/P10/P13 and the E6/E7/MAIN
anchors re-pointed to the new text.
Note: `python tests/g8_cases.py` (step 0 on the base) now reports F1-F6 as differing: the `now` column is the pre-fix base.
Test runs: see the builder report.
