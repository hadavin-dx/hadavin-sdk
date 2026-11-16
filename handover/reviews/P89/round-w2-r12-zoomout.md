# PR89 zoom-out review (ORDER 236 point 1), head b855a8f51cdaef0eee5aa9e58bcdd1d3afe4d750
VERDICT: PARTLY. Nothing was run; every claim is from reading. Saved by the cloud session from the reviewer's inline report (condensed).
Coverage: tools/mutation_runner.py 1,360 of 1,360; test_mutation_runner_keywords.py about 220 of 2,751 (other 134 test names seen only as a grep list); mutation_runner_mutants.py about 20 of 510; NOTES 15 of 15; DIFF.patch, CHANGELOG, conftest, manifest not read; pytest source and testing.mutation not available.

## Surface
The child's stdout/stderr go to DEVNULL (mutation_runner.py:886). Only text copied from the JUnit file and passed through `_masked` can carry a secret: first `E` line (_row 1157, 1161, 1166, 1176), failing test id (1180), baseline skip message (1127). "Never echo env-derived values" is already the surface; the question is how to hide the value inside those strings.

## The literal simple rule S (drop the line holding the skeleton: the secret minus backslashes and quotes) does NOT hold
1. Cut text. Password `Zq9xK2mP7wRt4vNb8LcY3` at the end of `host=db.internal.example.org port=5432 dbname=mutants user=svc password=Zq9xK2mP7wRt4vNb8LcY3` (about 93 chars); pytest prints head...tail: `E   assert 'host=db.inte...7wRt4vNb8LcY3' == 'other'`; the tail shows 13 of 21 characters, the full skeleton is absent, S keeps the line. Code that stops it today: _edge_patterns (542-564, used 622-631), _fragment_spans (656-681). Verified by reading; pytest's real cut sizes (12/13, 69-char threshold) are the builder's observation only.
2. Non-ASCII or control characters. Secret `Zq9x` + e-acute + NBSP, printed by repr then json.dumps: the line shows `u00e9xa0` once stripped; S's skeleton misses it, and even the six whole-text encoders (_WHOLE_ENCODERS 331-338) miss the mix; only the per-character table _char_looks (459-464) catches it. Verified by Python semantics, not executed.
Smaller: a quote-only secret has an empty skeleton so naive S drops every line; a short skeleton such as `test` over-drops.

## What DOES hold: refuse odd secrets up front, then match plain text only
At the start of `_secret_values`, raise ValueError if any base (whole value, password, decoded password) holds a quote, backslash, control or non-ASCII character. Then every base is printable ASCII without quotes or backslashes, and plain `find` finds it at any print depth. One single-pass re.sub over the longest-first alternation of bases (no `hit` bytearray, no MAX_MATCHES), plus the existing _fragment_spans for head/tail pieces beside `...` with MAX_FRAGMENT_HITS kept. Masking the matched span stays (keeps `AssertionError: assert`).
Cost: a DSN with a quote, backslash, control or non-ASCII character in a value, or in a percent-decoded password (%27, %C3%A9), becomes a clear refusal before anything runs. The repo fixture DSN is plain (tests/test_mutation_runner.py:433). NOT verified: whether any caller outside the snapshot has such a DSN.

## What it deletes (estimates, tests/mutants not read in detail)
Code: _WHOLE_ENCODERS, _printed_again, _written_forms, _char_looks, _any_of, _nested, _starts_of, _stripped_pattern, _run_pattern, _edge_patterns, _view_with_places, _widened, _stripped_spans, _HEAVY_RUN, _RUN, _DROPPED, FRAGMENT_MIN, QUOTE_RUN_MIN, MAX_MATCHES, the _BACKSLASH_ESCAPE libpq read and the quote branch of the password pieces, _SecretSet.bases, the lru caches and _forget_secrets. About 250 lines. Tests: about 45-55 of 134 (ranges 533-575, 650-666, 1440-1462, 1647-1705, 1725, 1831-2155, 2161-2347, 2374-2570, 2628-2640); mutants: about 40-50 of the 59 masking mutants. Stay: 376-399, 421, 433, 464, 496, 515, 594, 723, 733, 755, 1473, 1485, 2436, plus one new refusal test.

## Rung table
Exact forms (_written_forms 354-372): plain find; CUT under the refuse rule. Stripped pattern (494-503): CUT under refuse rule (without it KEEP; it is S made right). Run pattern (506-538): CUT under refuse rule (`p'w` password). Quote-only (_HEAVY_RUN): CUT (refused). Edge patterns (542-564): CUT under refuse rule; the builder's claim that the stripped edge layer cannot see a cut inside an escape is contradicted by _nested/_starts_of (477-491). _fragment_spans (656-681): FOLD or KEEP as the survivor; equivalence not proven, needs a differential run. FRAGMENT_MIN CUT, EDGE_MIN=2 KEEP. MAX_MATCHES CUT. MAX_FRAGMENT_HITS KEEP (a hostile line of 1,000,000 `...` costs about 1e8 steps). _widened/_view_with_places CUT.

## Variants
Drop the line on any N-char piece: over-drops generic parts of a DSN (localh, postgr, mutants); KEEP adjacency to `...`, CUT this variant. Mask matched span: prefer. Fail fast (blank the message on any hit): same blind spot (the cut line has no hit), loses the message; worse. Blank the message whenever pass_env is set: smallest, but removes the message on every DB-backed run; only if the lead values zero machinery over diagnostics. Remove the cause of the cut (pytest `-o verbosity_assertions=2`): not verified, does not cover other `...` sources.

## Builder's failing inputs (NOTES rows 9-13)
Verified by reading: e-acute input (row 10); quote-only empty skeleton (row 11). Wrong or imprecise: row 11 (`a'b` makes S drop lines holding `ab` adjacent, not "in order"); row 12 (secret of 21 chars is below pytest's cut; use the DSN-with-password-last input); row 13 (the stripped edge layer does handle cuts inside an escape; _fragment_spans looks redundant).

## Findings
1 Minor (design; no defect, no leak found): about 250 lines of any-depth, any-encoding masking defend a shape the allowlist does not need (only a throwaway DB address, PASS_ENV_ALLOWED :236). Lead decision r11-05. 2 Minor: _fragment_spans and _edge_patterns do the same job two ways; keep one. 3 Nit: docstring lines 88-93 ("only the host, only the user name" not covered) contradict masking of DSN head/tail beside `...`. 4 Nit: NOTES row 12 example does not match the documented 12/13 cut.
No leak the current code lets through that the simpler design would fix; nothing fixed.
