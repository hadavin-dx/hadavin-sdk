# Evidence r13 (independent): EDITS.md round 13. EVIDENCE RUNNER: records only, no judgement.

Files: `chk13.py` (my own checker), `chk13-on-r13.txt`, `chk13-on-round12.txt`, `run_mutations.py`, `mutations-output.txt`, `mut/` (the 37 planted copies that were written), `verify13-copy.py` (verify13.py with only its scratch path changed to `scratch13/`), `verify13-as-is-output.txt`, `sha256-before.txt`, `sha256-after.txt`.

## 1. Failures and deviations (first)

**F1. No failure of EDITS.md round 13 against my checker.** `chk13-on-r13.txt`: FAILS 0. Nothing in the target failed any check I wrote. Two things first went wrong in MY work and were fixed before the final runs: (a) my first checker had false positives (reverse label window too wide; shred rule applied to `shred -u <file>` as well as `shred -u <path>`; route words in the wrong case; `different key` context word); (b) my key-end rule was case sensitive ("Revoke" capital R) so mutation M10 slipped through it until I fixed that. All numbers below are from the final versions.

**F2. verify13.py did NOT catch 7 of my 37 planted mutations that it could run** (it is green on the real file, 0 failures, all 56 of its own negative controls caught):
- M10 key end 18:29 UTC = 23:59 IST in part 3h of E-48 (the other 18:19 mentions in the row keep verify13 happy).
- M12 E-09 no longer says the owner waits for the written reply `not looking` (verify13 checks only that the phrases exist somewhere in the row).
- M22, M23, M34 wrong weekday for a date (Tue 23 Nov, Thu 18 Nov, Tue 18 Nov): verify13 has no weekday/date check at all.
- M29 a Q-number (Q25) in owner-facing NEW text, M30 an L-id (L-23NOV) in owner-facing NEW text: verify13's code scan covers E-nn, ND, G1-5, EL, WP6, D-items and single-digit R only.

**F3. My checker did NOT catch 3 of 39 mutations** (it was not written to look at them): M32 (E-12 "you revoke the secret key ... anyway" changed to "you may keep"), M33 (HOLD label removed from the E-13 block), M36 (index table line of E-14 changed). verify13 catches all three.

**F4. Observations on the reply phrases (recorded, not judged; section 3 has the full list).**
- `no more takes` is one phrase, one meaning (the owner wants no further take), but its effect depends on the route: route A starts parts 3d to 3h at once, route B only after `cut accepted`. No message selects the route; the timing of the phrase does (E-48 part 3c, E-52). A `no more takes` written before `cut accepted` is therefore route A by definition. Not the same phrase with two meanings; flagged because the consequence differs by timing.
- The bare word `no` is a refusal in E-03, E-11, E-12, E-16 (`No`) and E-49 (held). In the secret key question 1 a bare `no` is not `no, other things use it`: any other reply counts as `not sure` (E-48; E-52 says the same). The effect is safe (both lead to part 3g), but the bare word does not mean "refuse" there.
- No phrase was found with two incompatible meanings. No `key kept` left (verify13 and mine both check).
- E-12 still contains the placeholder `[LEAD FILLS at re-pin: ...]` (3 occurrences in the file: E-12, E-54 and the rule R11 text). Expected by the file's own rule R11; recorded because it is an unfilled time of day.

**F5. Not run through verify13:** M38 (banned string) and M39 (secret-shaped string) were planted IN MEMORY only and checked only by my checker, so that no banned name and no secret-shaped text was written to disk. Mine caught both.

## 2. Passes (final head of EDITS.md, sha256 `322302de...3ecf`, before = after; round-12 copy and the six inputs also unchanged, `sha256-before.txt` = `sha256-after.txt`)
| Check | Result |
|---|---|
| rows | 56; ids unique and in order (E-01 to E-58 without E-10 and E-35) |
| Header counts | computed Apply now 44, Hold 12 (and 0 other); header says 44 and 12; header id lists for Apply now (44) and Hold (12) equal the rows |
| OLD text once on its stated line | 57 OLD blocks (E-13 has two): 0 failures (each occurs exactly once in its input file, on the stated line, or the stated second line) |
| UTC = IST pairs | 97 pairs in the whole file, every IST is UTC + 5:30; no UTC time without IST in any NEW block (one UTC time without IST outside blocks: a Why line that quotes the old text "has no IST") |
| Weekday and date pairs | 58 pairs, all right for 2026 (Mon 16, Wed 18, Mon 23 Nov) |
| Labels | `latest start we plan` appears 19 times (case-insensitive) and every time it is directly followed by a time it is 18:04 UTC = 23:34 IST (7 direct pairs; E-12 5, E-52 1 plus header text); `program refusal limit` 9 times, direct pairs (5) all about 18:14 UTC = 23:44 IST; no bare "latest start" and no "refusal limit" without "program"; reverse scan (each 18:04 / 18:14 follows its own label) 0 failures. 18:04 + 14:20 = 18:18:20, matches the 18:18 UTC = 23:48 IST in E-12. |
| Key end 18:19 UTC = 23:49 IST | present in NEW of E-12, E-37, E-48, E-52, E-55, E-57, E-58; no key-revoke sentence names 18:29 without 18:19 |
| Content the round must keep | E-09 not-looking step (`please stop looking`, wait for `not looking`, `you may look again`); E-48 routes A and B, 3j, WHATEVER wording, shred rule (`it contains no ..`); E-55, E-16 trigger `no more takes`; E-58 `key revoked` / `key not revoked` |
| Internal codes in owner-facing NEW text (OWNER-STEPS rows, 37 rows) | 0 of E-nn, ND, R-number, L-id, L-row, Q-number, D-item, gate, EL, WP, S9 |
| Banned list (counts only) | 0 of 10 in EDITS.md; 0 in my whole evidence folder (108 files) |
| Secret-shaped strings | 0 (AWS key shape, sk-, ghp_, xox, private key, password/token assignments, JWT, long hex, e-mail not example.com) |
| verify13.py as-is (copy, scratch in `scratch13/`) | exit 0, "FAILURES 0", 56 of 56 own negative controls caught |
| My checker on the round-12 copy | 34 failures (label 14, rowcontent 12, content 5, key end 1, shred 1, phrase 1): it discriminates round 12 from 13 |
| Changed vs round 12 | NEW changed in E-01, E-02, E-03, E-06, E-09, E-12, E-16, E-37, E-48, E-52, E-54, E-55, E-57, E-58; OLD changed only in E-55 |

## 3. Reply phrases (owner-facing NEW text; rows using each)
- `please stop looking` E-09, E-48, E-52; `not looking` (assistant's written reply) E-09, E-48, E-52; `you may look again` E-09, E-48, E-52; report line `password file created; <password file name>; <folder>; you may look again` E-52. One meaning each.
- `no more takes` E-16, E-48, E-52, E-55, E-57; `more takes` E-48, E-52 (no reply counts as `more takes`). One meaning (see F4 on timing).
- `cut accepted` E-16, E-48, E-52, E-55, E-57. One meaning (the cut is acceptable); never defined as the other phrase.
- `key revoked` E-48, E-58; `key not revoked` E-48, E-58. One meaning each.
- `yes`, `no, other things use it`, `not sure` (key question 1) E-37, E-48 (E-52 for `not sure`); `same key`, `different key`, `not sure` (key question 2) E-37, E-48. `not sure` has one meaning: unknown, so the safe path.
- `tested` / `untested` (crash check) E-12 only.
- `ok` E-03, E-11 (as "ok") and E-52; `no` E-03, E-11, E-12, E-52; `No` and `Yes, remove the container only` E-16; `Yes, take <take id>; ...` E-12; `Yes, send the one enquiry on <day>` E-49, E-50, E-53 (all three held, gate G5).
- `end` E-37, E-41 (held): same meaning (ends the pause of the take).
- `revoke the model key` is the name of the owner's alarm (E-12, E-48), not a reply.
- Four full-sentence yes messages exist; each starts differently (take, send the one enquiry, remove the container only), so no message is shared.

## 4. Mutations (39 planted, `mutations-output.txt`)
Mine caught 36 of 39 (misses M32, M33, M36). verify13 caught 30 of the 37 it could run (misses M10, M12, M22, M23, M29, M30, M34). Both caught: M01-M09, M11, M13-M21, M24-M28, M31, M35, M37 (wrong IST x4, old labels x3, refusal-limit pairing, key end 18:29 in E-55, route A only, shred rule removed, 45 vs 44, Hold 13, id list, duplicate id, order swap, wrong OLD text, wrong stated line, phrase meaning changed, E-nn, ND and R-number in owner text, unpaired UTC, weakened WHATEVER wording).
Requested kinds: wrong IST M01-M04; old label M05, M06, M37; key end 18:29Z M10, M11; missing not-looking step M12; route A only M13; shred without no-.. rule M14; count 45 vs 44 M15; duplicated phrase meaning M24, M25.

## 5. Not run / not checked
- Whether the wording is understandable to a non-technical reader, whether the plan facts (14 min 20 s, program refusal limit, UNVERIFIED claims) are true: not checked; only text consistency.
- Applying the rows to scratch copies of the inputs and the resulting file (verify13 does it; I did not write my own).
- Index table versus row headers, gate definitions, ND items 1 to 15, confirmations a to n, UNVERIFIED list counts: covered only by verify13, not by my checker.
- No mutation of the input files; no code, no model call, no spend. Max 1 heavy job at a time; no stray processes started.
