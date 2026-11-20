# Ticket G11: the opaque-token post-pass (E16 candidate 2, revised): a UUID or phone number inside a long token is masked with the token again

Status: BUILD TICKET, core-c drafter, 2026-11-20. NOT built: a ticket only until the lead chooses G11 for E16 (section 0). Base:
cloud/core-c HEAD `4ea3a9d99` (G8; G9 as `9652b20aa`..`3ee2361d4`; G4 Phases 0-3 as `b4ac46668`..`35a068f2a`: all IN it; G4 Phase 4
(host names, branch `wip-g4-p4`, local, STOPPED) is NOT). Labels: MEASURED (run on a scratch `git archive` copy, figure recorded), BY
READING, NOT RUN. Scratch copies (drafter's, the repo untouched): `head` = `git archive a60da3394` (G8 only), `g11` = head + this
ticket's diffs; `h2` = `e75871df3` (G8 + G9), `h2g` = h2 + diffs; `h3` = `4ea3a9d99` (G8 + G9 + G4 P0-3), `h3g` = h3 + Appendix A + B. Inputs: ESCALATIONS.md E16
and its 12:1xZ update, `handover/core-c/tickets/G11-files/` (cand2_postpass.diff, rows.py, cmp.py, tokexp.py, prop.py, memut.py),
G8 v6 (OL1-OL7, L15), tests/g8_cases.py `OPAQUE_LIMITS`, tests/test_redact_glued_rest.py, tests/fixtures/timing.py.

## 0. Decision for the lead (E16 (a) or (b))

| option | what ships | consequence |
| --- | --- | --- |
| (a) DEFAULT until decided: accept L15 | nothing; OL1-OL7 stay strict-xfail pins | 96-97 % of the injected tokens leak (4,765 of 4,971 UUID, 7,547 of 7,747 phone, MEASURED by the E16 measurer; 4,765 / 3,733 / 3,814 re-MEASURED here on `head`, N=20,000) |
| (b) G11 as THIS ticket (recommended if (b)) | Appendix A (one pass, one method, two constants) + Appendix B | 0 of 4,971 / 3,820 / 3,927 injected tokens leak (MEASURED on `g11`); only OL1-OL7 change among the 218 G8 records; L15 narrowed, not removed (section 9) |
| (c) candidate 2 as shipped (`cand2_postpass.diff`) | NOT recommended | three measured defects, section 2 |

The build starts only on the lead's "G11". The builder builds on the tree as it is then (after G4 Phase 4 if that has merged); every
number below is re-measured there (section 4); a number of this ticket is a prediction for that tree, not a pass mark.

## 1. The problem (E16, unchanged)
G8 made the UUID and PHONE entries cut a value set off by `_` or a letter inside a run of token characters; they run before
HIGHENTROPY, so a remainder under 40 characters stays readable: `tok_<UUID_1>_DKRYfmt07ELSZgnu18FMTahov29GNUbi` (OL1). The base
(`29af3b88a` = `6a852c7d3^`) masked the whole run as one `<HIGHENTROPY_1>` (`_` is no `\b`). Pinned as limit L15 (OL1-OL7: the as-is
output asserted, the ideal a strict xfail on six rows).

## 2. Why not candidate 2 as shipped: three defects, each MEASURED (scratch `c2` = head + cand2_postpass.diff)
- C2-F1 memory and time. cand2 writes back EVERY placeholder of the run, HIGHENTROPY ones included, whose values have no length bound.
  `redact(text, mapping={"<HIGHENTROPY_1>": 20,000 chars, "<UUID_1>": uuid})` over 1,000 runs `<HIGHENTROPY_1>_<UUID_1>` + a distinct
  suffix (27,889 characters): HEAD 0.54 s, 9 MB peak, 2 entries; c2 17.03 s, 86 MB, 1,002 entries. `X<UUID_1>` repeated to 128 KiB with
  the UUID in the map: one entry of 538,832 characters, 273 MB peak (tracemalloc), 1.57 s against HEAD 0.39 s.
- C2-F2 a placeholder the map does not hold is "written back" as itself (`mapping.get(p, p)`), so its own letters count: `tok_<UUID_7>_`
  + 30 token characters (a quoted placeholder, map empty) becomes `<HIGHENTROPY_1>` holding the literal text; and the first call's
  output `tok_<UUID_1>_abcdefghijklmnopqrstuvwxyz0` (written back: 67 characters, no upper case, kept) becomes `<HIGHENTROPY_1>` on a
  second call with a FRESH map (the literal `UUID` is upper case): not a fixed point under a fresh map.
- C2-F3 base64 padding: the run stops before `=`, its look-ahead refuses `=`, so `tok_<uuid>_<32>==` stays
  `tok_<UUID_1>_DKRY...==` (OL15); HIGHENTROPY itself takes `={0,2}`.
A variant that leaves HIGHENTROPY placeholders out of the run (bounded, no orphan) was MEASURED and REJECTED: 23 of 382 and 25 of
396 injected phone tokens leak (N=2,000), the shape `<20 chars>_<PHONE_1><HIGHENTROPY_1>` (the head is under 40 and HIGHENTROPY took
the tail). So HIGHENTROPY stays in the run and the WRITTEN-BACK size is capped instead (G11-D3).

## 3. Decisions (drafter; the lead may overrule each, fallback stated)
- G11-D1 Where: the LAST step of `_Redactor.find`, after the `for label, pattern in PATTERNS:` loop, on the whole text
  (`return _PH_RUN.sub(self._remask_run, out) if "<" in out else out`). So it runs after the fold scan and after every pattern, in every
  caller of `find` (first pass, `settle` rounds, the views and the decoded base64 view through `redact`). Not in the sweep, the gate
  (`enforce_map` runs no pattern) or `_fold_scan`. Fallback: none (any earlier place sees a half-masked text).
- G11-D2 OL2's orphan: KEEP it. OL2 (`tok_<uuid>_<40>`): G8 gives `tok_<UUID_1><HIGHENTROPY_1>`; the pass masks the whole run as
  `<HIGHENTROPY_2>`; `<HIGHENTROPY_1>` (the 41-character tail) stays in the map, no longer in the text. Not removed, because (1) it is
  not special: `_place` already adds a piece entry for every secret-kind value that holds placeholders (OL1's map is
  `HIGHENTROPY_1` = token, `HIGHENTROPY_2` = `_` + tail, `UUID_1`: MEASURED), so OL2's map has the same shape as OL1's; (2) removing it is
  NOT cheap or safe: the map is shared across the strings of a call (`redact_many`, a caller's `mapping=`) and the gate's runs, the key
  can be in another string, in the journal (`_journal`, rollback) or a spelled form; a removal needs a use count over every string;
  (3) it is fail-safe: HIGHENTROPY is a secret kind, never restored, and as a stored value it makes the sweep mask another copy of the
  tail. Pinned by `keys` in OL2 and mutant G11-13. Fallback if the lead wants it gone: a ticket of its own (cross-string use count).
- G11-D3 `_PH_RUN_CHARS = 1024`: a run longer than that with the values written back is left as the patterns cut it (L15 narrowed).
  Measured bound: 4,000 runs of 950 written-back characters, 114,889 characters of text: 4.15 s, 26 MB, 4,002 entries (HEAD 0.44 s, 1 MB);
  1,000 runs of 20,000: 0.44 s (left). Size is computed BEFORE the value is built. Private module constant (not defaults.py: it is a
  shape rule like HIGHENTROPY's 40, not a budget). Fallback: 512 or 4,096 (re-pin OL13/OL14, mutants G11-10/11).
- G11-D4 a placeholder the map does not hold leaves the run as it is (OL16, mutant G11-9). Fixes C2-F2.
- G11-D5 `={0,2}` before the run's look-ahead, as HIGHENTROPY (OL15, mutant G11-12). Fixes C2-F3.
- G11-D6 names: `OPAQUE_LIMITS` -> `OPAQUE_RUNS` (tuple grows `g8` and `keys`), test
  `test_a_value_inside_an_opaque_token_is_a_stated_limit` -> `..._is_masked_with_it`; the strict xfail of
  `test_opaque_token_tail_is_masked_with_it` goes (its rows pass). L15 stays as a NAME for what is left (section 9).

## 4. Placement on the merged tree and how to rebase
Appendix A is against `4ea3a9d99` (`find` at line 1231); MEASURED with `--fuzz=0`: the same +/- lines apply to `a60da3394` (G8 only)
and `e75871df3` (G8 + G9) with line offsets only; Appendix B applies unchanged to all three (the three test files are byte-identical). If `patch -p1 --fuzz=0` fails on the tree of the day, apply BY NAME
(three places in src/hadavin_sdk/guard/redact.py; nothing else in src):
1. Module docstring: replace the two lines that start `token) (G8). A UUID or phone number set off by` and end
   `(limit L15: tests/g8_cases.py OPAQUE_LIMITS).` with Appendix A's four `+` lines.
2. Module level: insert the `_PH_RUN` comment, `_PH_RUN = re.compile(...)` and `_PH_RUN_CHARS = 1024` right after the line that
   starts `ARN_CHAR = ` and before `PATTERNS: list[tuple[str, re.Pattern[str]]] = [`.
3. `class _Redactor`, method `find`: its final `return out` (the line after the `for label, pattern in PATTERNS:` loop) becomes the
   `return _PH_RUN.sub(...)` line; the method `_remask_run` goes right after `find` and before `settle`.
STOP if `find` no longer ends with that loop and `return out` (a step was added after the loop by G4 Phase 4 or another change):
ask core-c where the pass goes (the drafter's answer is "after every pattern step of find", but that needs a re-read). `_PLACEHOLDER`
(module level, defined further down) is used only at call time: fine. Then RE-MEASURE every figure of sections 5-8 on the merged
tree; record each beside this ticket's figure; a difference in a count is NOT a failure by itself, a difference in a pinned output is
a STOP (section 10).

## 5. Tests (Appendix B; MEASURED on `g11` and `h2g`)
OL1-OL7 (were limit pins; the `after` column changes; `base` kept; new `g8` = the old `after`; new `keys`):

| row | G8 (`g8`) | G11 (`after`) | keys after one call |
| --- | --- | --- | --- |
| OL1 | `tok_<UUID_1>_` + T32 | `<HIGHENTROPY_1>` | HE_1, HE_2, UUID_1 |
| OL2 | `tok_<UUID_1><HIGHENTROPY_1>` | `<HIGHENTROPY_2>` | HE_1 (orphan, D2), HE_2, UUID_1 |
| OL3 | T20 + `_<UUID_1>` | `<HIGHENTROPY_1>` (base: `<HIGHENTROPY_1><ACCOUNTID_1>`) | HE_1, HE_2, UUID_1 |
| OL4 | `a<UUID_1>` + 30 | `<HIGHENTROPY_1>` | HE_1, HE_2, UUID_1 |
| OL5, OL7 | `tok_<PHONE_1>_` + T32 | `<HIGHENTROPY_1>` | HE_1, HE_2, PHONE_1 |
| OL6 | `tok_` + T20 + `_<PHONE_1>_` + T20r | `<HIGHENTROPY_1>` | HE_1, HE_2, HE_3, PHONE_1 |

New rows OL8-OL16 (one per guard; `tail` None except OL15): OL8 `Tk_`+uuid (39 written back: kept `Tk_<UUID_1>`); OL9 `Tok_`+uuid
(40: `<HIGHENTROPY_1>`); OL10 no upper case, OL11 no lower case, OL12 no digit (a digit-free UUID shape): kept as G8 cut them;
OL13 `Tok_`+uuid+`_`+983 `a` (1,024: `<HIGHENTROPY_2>`; the `a` run is a HIGHENTROPY of its own, the 129+ entry takes any letters);
OL14 984 `a` (1,025: kept `Tok_<UUID_1><HIGHENTROPY_1>`); OL15 OL1 + `==` (`<HIGHENTROPY_1>`); OL16 `tok_<UUID_7>_`+T32, empty map:
kept. Every row also asserts a second call with a fresh map and with the same map changes nothing.

Pins that change: the L15 sentence of the redact.py docstring (Appendix A hunk 1); the comment above the rows in g8_cases.py; the two
test docstrings; `test_row_counts_are_pinned`: `len(G.OPAQUE_LIMITS) == 7` -> `len(G.OPAQUE_RUNS) == 16`. Unchanged: `len(G.CASES) ==
101`, KEEP 84, FULL_STOP 6, AT_REST 9, UNTRUSTED 2, the `cls` counter, `LIMITS` (no CASES row changes: MEASURED, rows.py 209 records:
only OL1-OL7 differ). New perf test `test_opaque_run_pass_is_linear` (section 7).
Counts, tests/test_redact_glued_rest.py (MEASURED on `h3g`; the same on `g11` and `h2g`):

| run | HEAD `4ea3a9d99` | after G11 |
| --- | --- | --- |
| `-m "not perf"` | 451 passed, 14 deselected, 43 xfailed | 468 passed, 18 deselected, 37 xfailed |
| `-m perf` | 14 passed | 18 passed (`h2g`, 53 s on a loaded box) |
| new tests on HEAD's src (fail-before, `g11` tests on `head`) | - | 17 failed, 451 passed, 37 xfailed: main test OL1-7, 9, 13, 15 (10), tail test OL1, 3-7, 15 (7) |

(+16 main, +8 tail, -7 old main, -6 old xfails: 451 - 7 + 16 + 8 = 468; 43 - 6 = 37.)

## 6. Mutants (Appendix B, tests/g8_mutants.py; killer `test_a_value_inside_an_opaque_token_is_masked_with_it` for all; `m()` learns
`expect` "OLn " -> param `[OLn]`; every `expect` is the row id plus a space (>= 4 characters) and every message of the killer starts
with it). Each `old` occurs once in redact.py after Appendix A (MEASURED). Real runner, `python tests/g8_mutants.py`: 49 of 49 good on
`g11` (35 G8 + 14 G11; MEASURED, G11-7's expect re-pointed from OL3 to OL2 after the first run, then re-run alone: KILLED).

| name | old -> new | expect |
| --- | --- | --- |
| G11-1 the opaque-run pass removed | the `return _PH_RUN.sub(...)` line -> `return out` | `OL1 ` |
| G11-2 the run needs 41 characters | `if size < 40 or` -> `if size < 41 or` | `OL9 ` |
| G11-3 the run needs 39 characters | `< 40` -> `< 39` | `OL8 ` |
| G11-4 no upper case needed | `[A-Z]` test dropped | `OL10 ` |
| G11-5 no lower case needed | `[a-z]` test dropped | `OL11 ` |
| G11-6 no digit needed | `\d` test dropped | `OL12 ` |
| G11-7 the size counts the run as written | `size = len(run)` | `OL2 ` (27 characters as written) |
| G11-8 the classes are read from the run as written | `full = run` | `OL10 ` (the literal `UUID` is upper case) |
| G11-9 an unknown placeholder is written back as itself | guard dropped, `.get(k, k)` | `OL16 ` |
| G11-10 / G11-11 the cap one lower / higher | `_PH_RUN_CHARS = 1023` / `1025` | `OL13 ` / `OL14 ` |
| G11-12 the run without `=` padding | `={0,2}` dropped | `OL15 ` |
| G11-13 HIGHENTROPY placeholders not taken into a run | `UUID|PHONE` only | `OL2 ` |
| G11-14 the run's head without `_` | `_` out of the head class | `OL1 ` |

Not mutated, with the reason: the `if "<" in out` shortcut (EQUIVALENT: with no `<` the run regex cannot match); the
`"<UUID_" not in run and "<PHONE_" not in run` early return (a cost guard: without it a run of HIGHENTROPY placeholders and token text
is re-masked; on one call such a run cannot arise, HIGHENTROPY's look-behind refuses a start inside a run; with a caller's map it
over-masks quoted `ab<HIGHENTROPY_1>`; BY READING, no row); the run's trailing look-ahead (BY READING: only `===` or more after the run
differs; HIGHENTROPY refuses it alike).
On the merged tree run ALL of tests/g8_mutants.py (49) and the other mutant files the build touches nothing in (`redact_mutants.py`,
`b64_mutants.py`, `gate_mutants.py`) once each; their anchors are outside the three places of section 4 (BY READING); any mutant that
was good before and is not after is a STOP.

## 7. Perf, idempotence, property corpus, token experiment
- Perf row (in Appendix B, `@pytest.mark.perf`): `redact(text, mapping=...)` over 64 KiB and 128 KiB of four units, the rule of
  tests/fixtures/timing.py (`measure_sizes` with `block_seconds`, best of 3; red when big > `PER_SIZE` 3.0 x (128/64) x max(small, 1 ms),
  a ratio limit of 6.0). MEASURED (`g11`, scratch perf.py / perf2.py, same rule), ratio big/small:

| unit | HEAD | G11 |
| --- | --- | --- |
| `x<HIGHENTROPY_1>` (the lead's row; no UUID/PHONE: the run is read once and left) | 1.99 (0.109 / 0.217 s) | 2.49 then 2.01 (0.109-0.114 / 0.229-0.272 s) |
| `X<UUID_1>` with the UUID in the map (one 128 KiB run: over the cap, left) | 3.04 (0.128 / 0.388 s) | 1.83 (0.144 / 0.264 s), 5 MB peak |
| `Xy_<UUID_1>_` | 2.00 | 1.99, 4 MB |
| `tok_<UUID_1>_` + `Ab1` x 10 + space (each run masked, one entry) | 1.82 (0.124 / 0.226 s) | 1.99 (0.151 / 0.300 s) |

  The existing `test_glued_patterns_are_linear` (14) still passes (MEASURED on `h2g`). Also run `python -m tests.g8_cost run` on HEAD
  and on the build and `compare` (the G8 acceptance rule: big < 3.0 s, ratio <= 6.0, build <= 1.5 x base + 0.05 s): NOT RUN by the
  drafter. The E16 measurer's cost ratios for cand2 were 0.90-1.06; G11's pass is cand2's plus an O(run) size sum.
- Idempotence: rows.py over the 218 records (209 at HEAD + OL8-OL16): 0 non-idempotent (MEASURED `g11`, `h2g`; rows.py needs
  `getattr(G, "OPAQUE_RUNS", None) or G.OPAQUE_LIMITS` in its `for o in` line, a scratch copy, the G11-files original stays). The OL test
  asserts the second call with a fresh and with the same map.
- Property corpus (G11-files/prop.py, the repo's .venv python): `corpus pinned ok`, `no refusal ok`, 0 fail: 1,836 inputs on `g11` and
  `h2g`, 1,978 on `h3g` (G4 added inputs) (MEASURED; the E16 measurer: 1,836, 0 fail for cand2).
- Token experiment (G11-files/tokexp.py, N=20,000; MEASURED `g11` and `head`): injected UUID 0 of 4,971 leak (HEAD 4,765), 10-digit
  phone 0 of 3,820 (HEAD 3,733), 11-digit 0 of 3,927 (HEAD 3,814); random base64url tokens: 11 readable per 80,000 per mode on both (6,
  2, 1, 2 by class: identical; no new leak). Re-run on `h2g`: section 11.
- Hostile written-back size (scratch blow.py; text: n runs `<HIGHENTROPY_1>_<UUID_1>` + a distinct letter suffix joined by spaces,
  `mapping={"<HIGHENTROPY_1>": ("Ab1" * L)[:L], "<UUID_1>": uuid}`; tracemalloc peak, `time.process_time`):

| L, n | HEAD | cand2 | G11 |
| --- | --- | --- | --- |
| 20,000, 1,000 | 0.54 s, 9 MB, 2 entries | 17.03 s, 86 MB, 1,002 | 0.44 s, 9 MB, 2 (over the cap: left) |
| 950, 1,000 | 0.11 s | - | 1.02 s, 6 MB, 1,002 |
| 950, 4,000 (114,889 chars) | 0.44 s, 1 MB | - | 4.15 s, 26 MB, 4,002 (linear in n: x4.07 for x4) |

  The 950 rows are the worst case the cap allows (each run stores about 1 KiB); it needs a caller map with a long HIGHENTROPY value AND
  that placeholder written in the input thousands of times (the producer's own output re-redacted, or a crafted text under the run's
  map). Stated, not a limit of the patterns: it is the E14 class (finder memory), far below E14's 1 GB.

## 8. Interplay with G9 and G4 (both in `4ea3a9d99`)
G9 (read-back keys, ENCODED). G9's read-back puts back every EXACT KEY of the map before looking for overlaps; the pass changes WHICH
keys a token gives (the whole token as HIGHENTROPY, plus `_place`'s piece entries) but adds no kind. The pass writes back only
UUID, PHONE and HIGHENTROPY values, never ENCODED (`<ENCODED_n>` is not in the run's placeholder group, and `<` ends a run, so a run
next to `<ENCODED_1>` stops there). MEASURED: G9's own files (`test_redact_settle_loop.py`, `test_model_gate.py`,
`test_runmap_enforce_map.py`, `test_redact_idempotent_property.py`: 2,261 passed, 1 skipped, the same as without G11, on a trial merge
`a60da3394` + `wip-g9` before G9 landed; on `h3g` in the subset row of "Late results"); on `h2g` and `h3g`: G8's tripwire `test_g9_read_back_follows_the_sweeps_joins` passes; `redact_many([tok, "see " + tok + " and " + uuid])`
gives `<HIGHENTROPY_1>` and `see <HIGHENTROPY_1> and <UUID_1>`; the gate `enforce_map("model says " + tok, map)` gives
`model says <HIGHENTROPY_1>` (HEAD leaves the tail readable there too); `redact("x<HIGHENTROPY_1>y " + tok, mapping=...)` keeps the
quoted `x<HIGHENTROPY_1>y` (no UUID/PHONE in that run). G9's `_read_back` reach (`SPELLED_READBACK_REACH`) bounds what it reads of a
long HIGHENTROPY value (BY READING), so G11-D3's 1 KiB values add nothing new to G9's work bound.
G4 (the base64 view, Phases 0-3). The view (`runmap._pass_one`) holds a unit whose text (padding stripped) is the original of a
secret-kind entry of pass 1 (`_b64_held`). With G11 a base64url token holding a UUID is ONE HIGHENTROPY whose original is the whole
token, so its unit is held and not decoded: the base's behaviour (at G8 the unit was not held: UUID is no secret kind), fewer decodes.
In a decoded view `find` runs too, so the pass runs there; a decoded token is then kept as HIGHENTROPY (secret kind: kept, L8) instead
of a UUID (also kept): the hit rule (`_held(after) > _held(seen)`) still counts one placeholder or more (BY READING). MEASURED through
`runmap.redact_text` on `h3` vs `h3g`: a bare token (changed as OL1); a one-line base64 blob of text holding the token, or a UUID (pass 1
masks it as HIGHENTROPY: held, `data <HIGHENTROPY_1> end` both); a base64url token glued to a UUID (`<HIGHENTROPY_1><UUID_1>` both);
the blob wrapped at 32 and at 36 (the view decodes it): `data:\n<ENCODED_1>\nend` both, kept entries `UUID_1` on `h3`, the token as
`HIGHENTROPY_1` (+ its piece) on `h3g`. So G11 changes what the view KEEPS, not what it replaces. G4 Phase 4 (HOSTNAME entries)
edits PATTERNS only: the pass is after the loop, so no textual overlap (BY READING); if Phase 4 merges first, apply by name (section 4).

## 9. Stated limits after G11, and SECURITY wording
L15 (narrowed) stays: a UUID or phone number inside a run of token characters is masked with the whole run when the run with the value
written back is one HIGHENTROPY would mask (40+ characters with upper, lower, digit); left as the patterns cut it: a run longer than
1,024 characters that way (OL14: only `Tok_` readable there, the long rest is a HIGHENTROPY of its own), a run holding a placeholder
the map does not hold (OL16), and a run that is not HIGHENTROPY-shaped (OL8, OL10-OL12: the base left those whole and readable, G8
masks the value). Proposed SECURITY text (through the security wording review): "A UUID or phone number inside a longer token (letters,
digits, `+/_-`) is masked together with the token when the token, value included, is 40 or more characters with upper case, lower case
and a digit, as for any such token. A token of over 1,024 characters that holds one is masked in parts, and the short parts beside the
value can stay readable."

## 10. Run list (builder; one commit per phase on `wip-g11`; every commit green) and stop rules
Phase 0 (no edit): on the tree of the day, `git log -1`; confirm G4 Phase 4's state; `patch -p1 --dry-run --fuzz=0` both appendices
(fails: section 4 by name). Run `pytest tests/test_redact_glued_rest.py -m "not perf"` and record (expect HEAD's 451/14/43 if nothing
else moved). Run G11-files rows.py (scratch copy) and tokexp.py N=20000 on the unpatched tree: the HEAD baseline.
Phase 1 (src + tests, one commit): apply A and B; `ruff format --check` and `ruff check` on src and tests; then:
1. `pytest tests/test_redact_glued_rest.py -m "not perf"` (expect 468 passed, 18 deselected, 37 xfailed) and `-m perf` (18 passed).
2. fail-before: the new test files on the Phase 0 src (a scratch copy): 17 failed, exactly the ids of section 5.
3. `python tests/g8_mutants.py` (49 of 49 good), then once each `python tests/redact_mutants.py`, `python tests/b64_mutants.py`,
   `python tests/gate_mutants.py` (results equal to their last recorded run on that tree).
4. rows.py + cmp.py against Phase 0: changed = OL1-OL7 only, 0 non-idempotent; prop.py; tokexp.py N=20000 (0 / 0 / 0 injected;
   random 11 per 80,000 per mode, equal to Phase 0); blow.py (Appendix C) with `950 4000` and `20000 1000`.
5. The whole suite `-m "not perf and not live"` and the perf group once; `python -m tests.g8_cost` compare; bandit `-ll` on redact.py.
Evidence: raw output to handover/core-c/evidence/G11-1.md, each figure with its label and the tree hash; notes to ESCALATIONS E16.
Then a fresh result review (design + codebase). No merge before it.
Stop rules (stop, record, ask core-c; never loosen a pin or a test to go on):
- any CASES / KEEP / FULL_STOP / AT_REST / UNTRUSTED / K-row / OPAQUE output other than section 5's; any change outside OL1-OL7 in rows.py;
- any non-idempotent record, any property-corpus failure or refusal, any injected leak, a random-token count above Phase 0's;
- a perf test red twice in a row (one re-run allowed, timing.py's note), or a ratio over 6.0 in g8_cost; a new `InputTooLarge` anywhere;
- a mutant not good (all four runners), or an `old` not found once;
- `find` no longer ending in the PATTERNS loop (section 4); a patch that needs more than the three places;
- a test outside the four named files changing result; three failed tries at the same fix.

## 11. Evidence (drafter) and what is NOT verified
MEASURED, `g11` (`a60da3394` + diffs, G8 only): every table above, the 49-mutant run, tokexp N=20,000, blow, perf, fail-before.
MEASURED, `h2g` (`e75871df3`, G8 + G9): patch, ruff, the G8 file incl. the perf group (18 passed), rows.py, prop.py, the G9 checks
of section 8, tokexp N=20,000 (0 / 0 / 0 injected, random 11 per mode: equal to `head`).
MEASURED, `h3g` (`4ea3a9d99`, G8 + G9 + G4 P0-3): patch `--fuzz=0`, ruff format and check clean (361 files), the G8 file not-perf counts,
rows.py (218 records, only OL1-OL7 changed vs `h3`, 0 non-idempotent), prop.py (1,978), the G4 checks of section 8, and the items
listed under "Late results" at the end.
NOT RUN by the drafter: g8_cost compare; bandit; redact_mutants / b64_mutants / gate_mutants with G11; G4 Phase 4 + G11 (not merged).
BY READING: the G9 reach bound (8), the hit rule (8), the equivalent / not-mutated items (6), the G4 Phase 4 overlap (8).

Late results (drafter, `h3g`): PENDING

## Appendix A: src/hadavin_sdk/guard/redact.py (diff against `4ea3a9d99`; `patch -p1 --fuzz=0`)
```diff
--- a/src/hadavin_sdk/guard/redact.py
+++ b/src/hadavin_sdk/guard/redact.py
@@ -27,8 +27,10 @@
 A value glued to a letter or `_` is masked with the glued text left outside the placeholder (`node_<IPV4_1>`, `<UUID_1>x`):
 an e-mail address, an IPv4 address, a UUID, a phone number that starts with `+`, a contiguous one beside `_` or straight
 after a phone word, and an IBAN beside `_` (with or without a short word: `iban_DE89...`, `DE89..._x`; not inside a longer
-token) (G8). A UUID or phone number set off by `_` inside a long opaque token is cut out and the rest of the token may stay
-readable (limit L15: tests/g8_cases.py OPAQUE_LIMITS).
+token) (G8). A UUID or phone number inside a run of token characters (`A-Za-z0-9+/_-`) is masked with the whole run as one
+HIGHENTROPY when the run, the value written back, is one HIGHENTROPY would mask (40 or more characters with upper case, lower
+case and a digit), as before G8 (G11). Limit L15 (narrowed by G11): a run longer than 1,024 characters that way, or one holding
+a placeholder the map does not hold, is left as the patterns cut it (tests/g8_cases.py OPAQUE_RUNS).
 A contiguous digit run glued to a letter is not read as a phone number (hashes and identifiers), and a letter or digit
 glued before an IBAN, or a digit before an IPv4 address, is not read as one.
 A copy of a known phone number is swept where a letter or `_` touches it (not a digit).
@@ -186,6 +188,12 @@
 # the key=value rule masks V. Over-redaction (an ARN segment that looks like `...token=`) is the accepted price.
 _KV_WORD = r"(?:password|passwd|pwd|secret|token|api[_\-]?key|apikey|access[_\-]?key|private[_\-]?key|credential|auth)"
 ARN_CHAR = r"(?:(?![\w.\-*+@]{0,40}?" + _KV_WORD + r"[\w.\-]{0,20}=)" + ARN_TAIL + ")"
+# (G11, E16) A run of token characters (HIGHENTROPY's own class, its `=` padding included) that holds a UUID, PHONE or HIGHENTROPY
+# placeholder. One linear scan: a placeholder starts with `<`, which no token character is, so each run is read once.
+_PH_RUN = re.compile(
+    r"(?<![A-Za-z0-9+/_\-])[A-Za-z0-9+/_\-]*(?:<(?:UUID|PHONE|HIGHENTROPY)_\d+>[A-Za-z0-9+/_\-]*)+={0,2}(?![A-Za-z0-9+/=_\-])"
+)
+_PH_RUN_CHARS = 1024  # (G11) a longer run (values written back) is left as the patterns cut it: bounds what one run stores
 PATTERNS: list[tuple[str, re.Pattern[str]]] = [
     # PuTTY FIRST (hadavin-sdk edit): its value runs to the end of the text, so a PuTTY block that starts inside a PEM block must be cut before the PEM
     # pattern shortens the text; the PEM pattern then masks the rest (its unterminated form runs to the end). The other order left the lines after the PEM END in clear.
@@ -1241,7 +1249,26 @@
                 out = self._sub_glued(pattern, label, out)
             else:
                 out = pattern.sub(lambda m, label=label: self._mask(m, label), out)
-        return out
+        return _PH_RUN.sub(self._remask_run, out) if "<" in out else out
+
+    def _remask_run(self, m: re.Match[str]) -> str:
+        """(G11, E16) A run of token characters that holds a UUID or PHONE placeholder and is, with the values written back, a run
+        HIGHENTROPY would mask (40 or more characters with upper case, lower case and a digit): masked whole, as the base did.
+        Left as it is: a run with no UUID or PHONE placeholder, one holding a placeholder the map does not hold (quoted text, a
+        fresh map over this redactor's output), and one longer than `_PH_RUN_CHARS` with the values written back."""
+        run = m.group(0)
+        if "<UUID_" not in run and "<PHONE_" not in run:
+            return run
+        keys = _PLACEHOLDER.findall(run)
+        if any(k not in self.mapping for k in keys):
+            return run
+        size = len(run) + sum(len(self.mapping[k]) - len(k) for k in keys)
+        if size < 40 or size > _PH_RUN_CHARS:
+            return run
+        full = _PLACEHOLDER.sub(lambda p: self.mapping[p.group(1)], run)
+        if not (re.search(r"[A-Z]", full) and re.search(r"[a-z]", full) and re.search(r"\d", full)):
+            return run
+        return self._mask(m, "HIGHENTROPY")
 
     def settle(self, originals: list[str], swept: list[str], known: int | None = None) -> list[str]:
         """The pattern passes after the first sweep, to a fixed point with a hard cap (G7; ORDER 020 MJ-B; fix round 3).
```

## Appendix B: tests/test_redact_glued_rest.py, tests/g8_cases.py, tests/g8_mutants.py (diff against `4ea3a9d99`; `patch -p1 --fuzz=0`)
```diff
--- a/tests/test_redact_glued_rest.py
+++ b/tests/test_redact_glued_rest.py
@@ -259,33 +259,27 @@
     assert out.text == "7<TENANT_1>32 y", f"G9 read-back digit: {out.text!r}"
 
 
-@pytest.mark.parametrize("o", [pytest.param(o, id=o[0]) for o in G.OPAQUE_LIMITS])
-def test_a_value_inside_an_opaque_token_is_a_stated_limit(o):
-    """Review round 1 (design Major), limit L15: a UUID or a phone number set off by `_` or a letter inside a long opaque
-    token is cut out by its own pattern and the remainder (under HIGHENTROPY's 40 characters) stays readable; the base masked
-    the token whole. Pinned as measured (`after`, and `base` for the record)."""
-    oid, shape, text, _tail, base, after = o
+@pytest.mark.parametrize("o", [pytest.param(o, id=o[0]) for o in G.OPAQUE_RUNS])
+def test_a_value_inside_an_opaque_token_is_masked_with_it(o):
+    """E16, ticket G11 (was limit L15): a UUID or a phone number inside a run of token characters is masked with the whole run as
+    one HIGHENTROPY when the run, the value written back, is a HIGHENTROPY run; OL8-OL16 pin each guard of the pass. The output
+    and the map keys are pinned as measured, and a second call (fresh map, and the same map) changes nothing."""
+    oid, shape, text, _tail, _base, _g8, after, keys = o
     out = redact(text)
-    assert out.text == after, f"OL {oid} ({shape}): {out.text!r}"
-    assert base != after  # the base output differed: this is a change G8 made
+    assert out.text == after, f"{oid} {shape}: {out.text!r}"
+    assert sorted(out.mapping) == keys, f"{oid} keys: {sorted(out.mapping)!r}"
+    again = (redact(after).text, redact(after, mapping=dict(out.mapping)).text)
+    assert again == (after, after), f"{oid} second call: {again!r}"
 
 
-@pytest.mark.parametrize(
-    "o",
-    [
-        pytest.param(
-            o,
-            id=o[0],
-            marks=pytest.mark.xfail(strict=True, reason="stated limit L15 (review round 1)"),
-        )
-        for o in G.OPAQUE_LIMITS
-        if G.leak("uuid", o[3], o[5])
-    ],
-)
+@pytest.mark.parametrize("o", [pytest.param(o, id=o[0]) for o in G.OPAQUE_RUNS if o[3] is not None])
 def test_opaque_token_tail_is_masked_with_it(o):
-    """The DESIRED behaviour (the base's): no 8-character run of the token's tail stays readable. Strict xfail."""
-    out = redact(o[2]).text
-    assert not G.leak("uuid", o[3], out), f"OL {o[0]} limit: {out!r}"
+    """The base's behaviour, back since G11 (was a strict xfail under L15): no 8-character run of the token's tail stays
+    readable, and a token masked whole maps to the whole token."""
+    out = redact(o[2])
+    assert not G.leak("uuid", o[3], out.text), f"{o[0]} tail: {out.text!r}"
+    if out.text.startswith("<HIGHENTROPY_") and out.text.endswith(">") and out.text.count("<") == 1:
+        assert out.mapping[out.text] == o[2], f"{o[0]} value: {out.mapping[out.text]!r}"
 
 
 @pytest.mark.parametrize(
@@ -338,7 +332,7 @@
         "changed": 3,
         "g4c": 2,
     }
-    assert len(G.OPAQUE_LIMITS) == 7
+    assert len(G.OPAQUE_RUNS) == 16
     assert sorted(LIMITS) == sorted(c["id"] for c in G.CASES if c["cls"] == "limit")
 
 
@@ -379,3 +373,30 @@
     small, large = best(65_536), best(262_144)
     assert large < 3.0, f"{name} {call}: {large:.2f} s"
     assert large / max(small, 1e-3) <= 6.0, f"{name} {call}: ratio {large / max(small, 1e-3):.2f}"
+
+
+OPAQUE_RUN_TEXTS = {  # ticket G11: placeholder-dense runs; the map holds every key, so the pass writes values back
+    "x<HIGHENTROPY_1>": "x<HIGHENTROPY_1>",
+    "X<UUID_1>": "X<UUID_1>",
+    "Xy_<UUID_1>_": "Xy_<UUID_1>_",
+    "tok_<UUID_1>_Ab1": "tok_<UUID_1>_" + "Ab1" * 10 + " ",
+}
+OPAQUE_RUN_MAP = {"<HIGHENTROPY_1>": "Ab1" * 20, "<UUID_1>": G.V["UUID"], "<PHONE_1>": G.P10}
+
+
+@pytest.mark.perf
+@pytest.mark.parametrize("name", sorted(OPAQUE_RUN_TEXTS))
+def test_opaque_run_pass_is_linear(name):
+    """Ticket G11: `redact()` with a map over 64 KiB and 128 KiB of a placeholder-dense run (`tests/fixtures/timing.py`: the
+    big run at most PER_SIZE x 2 the small one, best of 3)."""
+    from tests.fixtures import timing
+
+    def call(text: str) -> None:
+        redact(text, mapping=dict(OPAQUE_RUN_MAP))
+
+    small, big = timing.measure_sizes(
+        lambda t: timing.block_seconds(call, t), OPAQUE_RUN_TEXTS[name], 65_536, 131_072, repeats=3
+    )
+    assert not timing.grows_faster_than_size(small, big, 65_536, 131_072), (
+        f"{name}: {small:.3f} s -> {big:.3f} s"
+    )
--- a/tests/g8_cases.py
+++ b/tests/g8_cases.py
@@ -238,70 +238,56 @@
     return J(ALNUM[(7 * i + 3) % 62] for i in range(n))
 
 
-# Review round 1 (design Major): a UUID or a phone number set off by `_` (or a letter) INSIDE a long opaque token. The base masked
-# such a token whole as one HIGHENTROPY (`_` is no \\b boundary); the UUID and PHONE patterns now cut the value out first and the
-# remainder is under HIGHENTROPY's 40-character minimum, so up to 32 characters of the token stay readable. Stated limit L15, pinned as
-# measured (`after`, test_a_value_inside_an_opaque_token_is_a_stated_limit); the ideal (no 8-character run of `tail` readable) is a
-# strict xfail. (id, shape, text, tail, base, after): `base` is the output before G8 (a git archive of the parent of the G8 commits).
+# Review round 1 (design Major), E16, ticket G11: a UUID or a phone number INSIDE a run of token characters. The base masked such a
+# token whole as one HIGHENTROPY (`_` is no \\b boundary); G8's UUID and PHONE patterns cut the value out first and left a remainder
+# under HIGHENTROPY's 40 characters readable (limit L15). G11's pass in `_Redactor.find` masks the run whole again when, the value
+# written back, it is a HIGHENTROPY run (40+ characters, upper case, lower case, a digit). (id, shape, text, tail, base, g8, after,
+# keys): `tail` the token text that must not stay readable (None: nothing to check), `base` the output before G8 (None: not
+# recorded), `g8` the output after G8 and before G11, `after` G11's output, `keys` the sorted map keys after one call.
 _T32, _T40, _T20 = opaque(32), opaque(40)[::-1], opaque(20)[::-1]
-OPAQUE_LIMITS = [
-    (
-        "OL1",
-        "uuid _ before, 32 after",
-        "tok_" + V["UUID"] + "_" + _T32,
-        _T32,
-        "<HIGHENTROPY_1>",
-        "tok_<UUID_1>_DKRYfmt07ELSZgnu18FMTahov29GNUbi",
-    ),
-    (
-        "OL2",
-        "uuid _ before, 40 after",
-        "tok_" + V["UUID"] + "_" + _T40,
-        _T40,
-        "<HIGHENTROPY_1>",
-        "tok_<UUID_1><HIGHENTROPY_1>",
-    ),
-    (
-        "OL3",
-        "uuid _ after, 20 before",
-        _T20 + "_" + V["UUID"],
-        _T20,
-        "<HIGHENTROPY_1><ACCOUNTID_1>",
-        "MF81ungZSLE70tmfYRKD_<UUID_1>",
-    ),
-    (
-        "OL4",
-        "uuid letter before, 30 after",
-        "a" + V["UUID"] + opaque(30)[::-1],
-        opaque(30)[::-1],
-        "<HIGHENTROPY_1>",
-        "a<UUID_1>UNG92vohaTMF81ungZSLE70tmfYRKD",
-    ),
-    (
-        "OL5",
-        "phone _ before and after",
-        "tok_" + V["PHONE10"] + "_" + _T32,
-        _T32,
-        "<HIGHENTROPY_1>",
-        "tok_<PHONE_1>_DKRYfmt07ELSZgnu18FMTahov29GNUbi",
-    ),
-    (
-        "OL6",
-        "phone _ both sides, 20 + 20",
-        "tok_" + _T20 + "_" + V["PHONE10"] + "_" + _T20[::-1],
-        _T20,
-        "<HIGHENTROPY_1>",
-        "tok_MF81ungZSLE70tmfYRKD_<PHONE_1>_DKRYfmt07ELSZgnu18FM",
-    ),
-    (
-        "OL7",
-        "11 digits, _ after",
-        "tok_" + V["PHONE10"] + "1_" + _T32,
-        _T32,
-        "<HIGHENTROPY_1>",
-        "tok_<PHONE_1>_DKRYfmt07ELSZgnu18FMTahov29GNUbi",
-    ),
-]
+_U = V["UUID"]
+_UA = J(["abcdefab-", "cdef-abcd-", "efab-cdefabcdefab"])  # UUID-shaped, no digit
+OPAQUE_RUNS = [
+    ("OL1", "uuid _ before, 32 after", "tok_" + _U + "_" + _T32, _T32, "<HIGHENTROPY_1>",
+     "tok_<UUID_1>_" + _T32, "<HIGHENTROPY_1>", ["<HIGHENTROPY_1>", "<HIGHENTROPY_2>", "<UUID_1>"]),
+    # OL2: the 40 characters after the UUID were a HIGHENTROPY run of their own (G8: `tok_<UUID_1><HIGHENTROPY_1>`); the pass takes
+    # that placeholder into the run and masks the whole token as HIGHENTROPY_2. HIGHENTROPY_1 stays in the map, no longer in the
+    # text: kept on purpose (ticket G11, decision G11-D2), the same piece entry `_place` makes for OL1's tail (HIGHENTROPY_2 there).
+    ("OL2", "uuid _ before, 40 after", "tok_" + _U + "_" + _T40, _T40, "<HIGHENTROPY_1>",
+     "tok_<UUID_1><HIGHENTROPY_1>", "<HIGHENTROPY_2>", ["<HIGHENTROPY_1>", "<HIGHENTROPY_2>", "<UUID_1>"]),
+    ("OL3", "uuid _ after, 20 before", _T20 + "_" + _U, _T20, "<HIGHENTROPY_1><ACCOUNTID_1>",
+     _T20 + "_<UUID_1>", "<HIGHENTROPY_1>", ["<HIGHENTROPY_1>", "<HIGHENTROPY_2>", "<UUID_1>"]),
+    ("OL4", "uuid letter before, 30 after", "a" + _U + opaque(30)[::-1], opaque(30)[::-1], "<HIGHENTROPY_1>",
+     "a<UUID_1>" + opaque(30)[::-1], "<HIGHENTROPY_1>", ["<HIGHENTROPY_1>", "<HIGHENTROPY_2>", "<UUID_1>"]),
+    ("OL5", "phone _ before and after", "tok_" + V["PHONE10"] + "_" + _T32, _T32, "<HIGHENTROPY_1>",
+     "tok_<PHONE_1>_" + _T32, "<HIGHENTROPY_1>", ["<HIGHENTROPY_1>", "<HIGHENTROPY_2>", "<PHONE_1>"]),
+    ("OL6", "phone _ both sides, 20 + 20", "tok_" + _T20 + "_" + V["PHONE10"] + "_" + _T20[::-1], _T20, "<HIGHENTROPY_1>",
+     "tok_" + _T20 + "_<PHONE_1>_" + _T20[::-1], "<HIGHENTROPY_1>",
+     ["<HIGHENTROPY_1>", "<HIGHENTROPY_2>", "<HIGHENTROPY_3>", "<PHONE_1>"]),
+    ("OL7", "11 digits, _ after", "tok_" + V["PHONE10"] + "1_" + _T32, _T32, "<HIGHENTROPY_1>",
+     "tok_<PHONE_1>_" + _T32, "<HIGHENTROPY_1>", ["<HIGHENTROPY_1>", "<HIGHENTROPY_2>", "<PHONE_1>"]),
+    # OL8-OL16 (G11): the pass's own edges, one per guard (the mutants of tests/g8_mutants.py G11-*).
+    ("OL8", "uuid, 39 characters written back", "Tk_" + _U, None, None, "Tk_<UUID_1>", "Tk_<UUID_1>", ["<UUID_1>"]),
+    ("OL9", "uuid, 40 characters written back", "Tok_" + _U, None, None, "Tok_<UUID_1>", "<HIGHENTROPY_1>",
+     ["<HIGHENTROPY_1>", "<UUID_1>"]),
+    ("OL10", "no upper case", "tok_" + _U + "_abcdefghij0123456789", None, None, "tok_<UUID_1>_abcdefghij0123456789",
+     "tok_<UUID_1>_abcdefghij0123456789", ["<UUID_1>"]),
+    ("OL11", "no lower case", "TOK_" + _U.upper() + "_ABCDEFGHIJ0123456789", None, None,
+     "TOK_<UUID_1>_ABCDEFGHIJ0123456789", "TOK_<UUID_1>_ABCDEFGHIJ0123456789", ["<UUID_1>"]),
+    ("OL12", "no digit", "Tok_" + _UA + "_Wxyzabcdefghij", None, None, "Tok_<UUID_1>_Wxyzabcdefghij",
+     "Tok_<UUID_1>_Wxyzabcdefghij", ["<UUID_1>"]),
+    # OL13, OL14: `_PH_RUN_CHARS` (1,024 characters, the values written back). The 983 or 984 characters after the UUID are one
+    # HIGHENTROPY of their own (the 129+ entry takes any letters); a longer run is left as the patterns cut it (L15, narrowed).
+    ("OL13", "1,024 characters written back", "Tok_" + _U + "_" + "a" * 983, None, None, "Tok_<UUID_1><HIGHENTROPY_1>",
+     "<HIGHENTROPY_2>", ["<HIGHENTROPY_1>", "<HIGHENTROPY_2>", "<UUID_1>"]),
+    ("OL14", "1,025 characters written back", "Tok_" + _U + "_" + "a" * 984, None, None, "Tok_<UUID_1><HIGHENTROPY_1>",
+     "Tok_<UUID_1><HIGHENTROPY_1>", ["<HIGHENTROPY_1>", "<UUID_1>"]),
+    ("OL15", "uuid, = padding", "tok_" + _U + "_" + _T32 + "==", _T32, None, "tok_<UUID_1>_" + _T32 + "==", "<HIGHENTROPY_1>",
+     ["<HIGHENTROPY_1>", "<HIGHENTROPY_2>", "<UUID_1>"]),
+    # OL16: a placeholder the map does not hold (quoted text, or a fresh map over this redactor's output) is left as it is.
+    ("OL16", "a placeholder the map does not hold", "tok_<UUID_7>_" + _T32, None, None, "tok_<UUID_7>_" + _T32,
+     "tok_<UUID_7>_" + _T32, []),
+]  # fmt: skip
 
 
 # (id, text, now, after, verdict); None = the text itself. verdict: kept (nothing masked, before and after) | same (masked
--- a/tests/g8_mutants.py
+++ b/tests/g8_mutants.py
@@ -38,7 +38,14 @@
 
 def m(name, old, new, killer, expect, file=RD):
     # the pinned id names the parametrized case the expect names: "ROW 36 " -> [row36], "ROW K2 " / "OPAQUE K75" -> [K2] / [K75]
-    tag = expect.split()[1] if expect.startswith(("ROW ", "OPAQUE ", "UNTRUSTED ")) else ""
+    first = expect.split()[0]
+    tag = (
+        expect.split()[1]
+        if expect.startswith(("ROW ", "OPAQUE ", "UNTRUSTED "))
+        else first
+        if first[:2] == "OL" and first[2:].isdigit()  # G11: "OL9 " -> [OL9]
+        else ""
+    )
     case = "" if not tag else f"[row{tag}]" if tag.isdigit() else f"[{tag}]"
     return Mutant(
         name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer + case
@@ -52,6 +59,14 @@
 )
 OPQ = "test_an_iban_never_starts_inside_an_opaque_token"
 UNT = "test_untrusted_placeholder_literal_keeps_its_number"
+OPR = "test_a_value_inside_an_opaque_token_is_masked_with_it"  # G11
+G11G = "        if any(k not in self.mapping for k in keys):\n            return run\n"
+G11N = (
+    G11G
+    + "        size = len(run) + sum(len(self.mapping[k]) - len(k) for k in keys)\n"
+    + "        if size < 40 or size > _PH_RUN_CHARS:\n            return run\n"
+    + "        full = _PLACEHOLDER.sub(lambda p: self.mapping[p.group(1)], run)\n"
+)
 IS = '_IBAN_START\n            + r"(?:AD|AE'
 E7 = r'r"\d{10,16}(?![0-9A-Za-z.>›])"'
 # The names skip G8-P6 and G8-P7 on purpose: P6 (a 5-digit guard) was removed in v3 (ticket G8, L-D9 flipped), and P7 went when the
@@ -93,6 +108,20 @@
     m("G8-S4 IPV4 given digits", J5, '_JOINS = {"PHONE": frozenset(string.digits), "IPV4": frozenset(string.digits)}', SW, "SWEEP ipv4"),
     m("G8-S5 TENANT given digits", J5, '_JOINS = {"PHONE": frozenset(string.digits), "TENANT": frozenset(string.digits)}', SW, "SWEEP tenant"),
     m("G8-S6 PHONE copy beside a digit replaced too", J5, '_JOINS = {"PHONE": frozenset()}', SW, "SWEEP phone digit"),
+    m("G11-1 the opaque-run pass removed", 'return _PH_RUN.sub(self._remask_run, out) if "<" in out else out', "return out", OPR, "OL1 "),
+    m("G11-2 the run needs 41 characters", "if size < 40 or size > _PH_RUN_CHARS:", "if size < 41 or size > _PH_RUN_CHARS:", OPR, "OL9 "),
+    m("G11-3 the run needs 39 characters", "if size < 40 or size > _PH_RUN_CHARS:", "if size < 39 or size > _PH_RUN_CHARS:", OPR, "OL8 "),
+    m("G11-4 no upper case needed", r're.search(r"[A-Z]", full) and re.search(r"[a-z]", full)', r're.search(r"[a-z]", full)', OPR, "OL10 "),
+    m("G11-5 no lower case needed", r're.search(r"[a-z]", full) and re.search(r"\d", full)', r're.search(r"\d", full)', OPR, "OL11 "),
+    m("G11-6 no digit needed", r'full) and re.search(r"\d", full)', "full)", OPR, "OL12 "),
+    m("G11-7 the size counts the run as written", "size = len(run) + sum(len(self.mapping[k]) - len(k) for k in keys)", "size = len(run)", OPR, "OL2 "),
+    m("G11-8 the classes are read from the run as written", "full = _PLACEHOLDER.sub(lambda p: self.mapping[p.group(1)], run)", "full = run", OPR, "OL10 "),
+    m("G11-9 an unknown placeholder is written back as itself", G11N, G11N.replace(G11G, "").replace("self.mapping[k]", "self.mapping.get(k, k)").replace("self.mapping[p.group(1)]", "self.mapping.get(p.group(1), p.group(1))"), OPR, "OL16 "),
+    m("G11-10 the cap one lower", "_PH_RUN_CHARS = 1024", "_PH_RUN_CHARS = 1023", OPR, "OL13 "),
+    m("G11-11 the cap one higher", "_PH_RUN_CHARS = 1024", "_PH_RUN_CHARS = 1025", OPR, "OL14 "),
+    m("G11-12 the run without = padding", r')+={0,2}(?![A-Za-z0-9+/=_\-])"', r')+(?![A-Za-z0-9+/=_\-])"', OPR, "OL15 "),
+    m("G11-13 HIGHENTROPY placeholders not taken into a run", r"<(?:UUID|PHONE|HIGHENTROPY)_\d+>", r"<(?:UUID|PHONE)_\d+>", OPR, "OL2 "),
+    m("G11-14 the run's head without _", r'r"(?<![A-Za-z0-9+/_\-])[A-Za-z0-9+/_\-]*(?:<(?:UUID', r'r"(?<![A-Za-z0-9+/_\-])[A-Za-z0-9+/\-]*(?:<(?:UUID', OPR, "OL1 "),
     m("G8-S7 gate held-back sweep without joins", "segment, spelling, placeholder, _joins(placeholder)", "segment, spelling, placeholder", "test_gate_sweep_of_a_held_back_phone_value_uses_the_phone_joins", "SWEEP held", file=RM),
 ]  # fmt: skip
 
```

## Appendix C: blow.py (scratch; `cd TREE; PYTHONPATH=$PWD/src:$PWD .venv/bin/python blow.py L N`)
```python
import sys, time, tracemalloc
from hadavin_sdk.guard.redact import redact
L, n = int(sys.argv[1]), int(sys.argv[2])
m = {"<HIGHENTROPY_1>": ("Ab1" * L)[:L], "<UUID_1>": "123e4567-e89b-12d3-a456-426614174000"}
def suffix(i):  # a distinct all-letter suffix per run
    s = ""
    while True:
        s += "abcdefghij"[i % 10]; i //= 10
        if not i: return s
text = " ".join("<HIGHENTROPY_1>_<UUID_1>" + suffix(i) for i in range(n))
tracemalloc.start(); t0 = time.process_time()
r = redact(text, mapping=dict(m))
print(f"L={L} n={n} chars={len(text)} entries {len(r.mapping)} cpu {time.process_time() - t0:.2f}s "
      f"peak {tracemalloc.get_traced_memory()[1] / 1e6:.0f} MB")
```
