Status: resolved
# P1d-a plan pass 7 resolve (rev 9 -> rev 10) (egm:egm-resolve, headless, auto accept; resolver Opus 5.5 via Skill)
Target: `handover/tickets/P1d-a.md` (full file). Findings: `round7-readiness.md` (F1-F12: 1B/2M/8N) and `round7-design.md` (M1-M5, N6-N10: 0B/5M/5N). Probe P10: `handover/evidence/P1d-a/probes-r8/` (README: apply command and tree stamp). Counts after: 118 rows (fb 63, pb 51, ow 4), 72 mutants (script `probes-r6/count_rows.py`, run on the rev 10 file). All 22 findings: PROPOSE FIX (N9 and N8 fixed in this ticket per fix-dont-defer, as D4 and D6), 0 CONTEST, 0 ESCALATE, 0 DECLINE.

## Groups
| group | findings | fix in rev 10 |
|---|---|---|
| G1 round trip and link property | M1, F1 | Not narrowed. Minimal input found (`EM + EM`: model path `<EMAIL_1>.m@example.org`, card `m@example[.]org`); fixed in `redact_for_card` by D5 (extra redactor pass in runmap, rows E2, E2b, E2c, mutants A66-A67). P10: round trip 1 of 2,000 is more masking only, 0 fixed-point failures, 0 secrets shown; link property on all 2,000 texts, 0 failures (`links3.out`). F1 wording: the two parts are named CARD FIXED POINT and ROUND TRIP. |
| G2 N8, N9 | N8, N9 | D6 (code spans read per paragraph) and D4 (wide dots first in the `defang=False` branch). NEEDS LEAD 8 closed. |
| G3 generated JSON and fixtures | F2, F6 | JSON hash keys and `\u0001X\u0001` markers so no raw secret sits in generated JSON; `test_fixtures_hold_no_secret`; `test_patterns_kinds` compares sets. |
| G4 hidden and S8d | F3, M4 | "hidden" defined for reported-only shapes; over-mask redefined; S8d draws with total 740 (P10: card 15, model 9 hidden of 18 placeholders each side, `s8d18-*.out`). |
| G5 rows on the right tree | F4, F5, F7, F8 | BTK and MENT rows run on P9/P10 (`rows-p10.out`); H27 spy; `_slack_blocks_driver` function; K43c and K43d. |
| G6 real-population differential | F9, M2, M3 | Tree named (git ls-files), character-level gate, handover via `--also-dir`; NEEDS LEAD 1 no longer defaults to accepted: DEFAULT is hold the PR. |
| G7 timing | M5 (new finding D7(c): `![](` repeated was quadratic on base and P9, 17 s at 32,000 characters) | HL2 card-path rows and quick check; A68-A70 time mutants; D7(c) `_drop_targets` (linear; P10 0.2-1.0 s at 262k; `b2.txt`, `b3.txt`). No mutant for D7(c) (not slow with `str.find`); HL2 guards it. |
| G8 nits | F10-F12, N6, N7, N10 | Applied as written in the rev 10 log line. |

## Open lead questions (with defaults)
1. NEEDS LEAD 1: real-population over-mask numbers. DEFAULT: hold the PR (no acceptance without the lead).
2. NEEDS LEAD 9 (new). DEFAULT: proceed.
3. Existing 2, 3, 4, 6 unchanged.
