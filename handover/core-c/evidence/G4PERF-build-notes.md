# G4PERF (E22) build notes

Cause (cProfile, 262,144 chars of `_4155550132`): the text is one base64-alphabet run that decodes to text with a hit, so `_pass_one`
builds t2 = `<ENCODED_1>` (11 characters) and calls `redact` again with a map whose one entry has the 262,144-character original.
That call spends 0.70 s of 1.76 s in `_build` (compiling a finder around the huge original) to read back 11 characters. At 65,536
characters no second pass runs, hence the ratio jump (7.5 with, 4.5 without).

Fix (src/hadavin_sdk/guard/runmap.py `_pass_one`, helper `_only_encoded`): when t2 is only `<ENCODED_n>` placeholders (n <= 6 digits)
and every stored original is ASCII and does not occur inside t2, return t2 and the map as they are (what `redact` returns for it).

Measured (perf-test method, direct): ratio 5.7/6.6/6.3 before; 4.19/4.11/4.19 after; 262k: 1.64-1.74 s before, 0.97-1.09 s after.
Byte identity (sha256 over text + sorted map, before == after): 2,345 inputs (142 probe b64 rows + host/number/plain rows, g8 rows,
1,836 property corpus, hostile shapes at 4k/20k/65k) 81464a7bc732d907; 142 rows + 262k hostile (underscore, plus digits) fe1b74c95711c93f.
The shortcut fired 41 times in that set. Pre-existing failures, identical on HEAD: TB-3.4 and test_tie_break_keeps_the_order_of_different_originals
(test_b64_scan), test_e5b_a_conflict... (test_runmap_enforce_map). b64_mutants.py NOT RUN.
