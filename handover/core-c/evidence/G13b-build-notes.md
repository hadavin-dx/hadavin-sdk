# G13b build notes (fix of the G13 result review round 1: design M-1, M-2, m-1, m-2, nits)

Branch wip-g13b on cloud/core-c (G13). Code commit "code G: G13b ..." (src, tests). Everything below was run on this tree.

## M-1 reproduced, before and after (BoundGate.chat, 3 calls with the same history, map holds the value)
Before: webhook value `https://hooks.slack.com/services/T0/B0/qqq...` + `see https://<HOST_1>/x ok`: held_value_left x3 (permanent);
`Bearer <KEY>` beside a value `Bearer abcdef...`: held_value_left x3; a value `https://x.example/zzzzzz9` + `go to https://<HOST_1>/x`: x3.
After: all three SENT x3; leak cases refused as before: `x hunter2-<HOST_1> y`, `x hunt<SECRET_2> y`, `<SECRET_1>abcdef` (G13-2/3/4/5/13 unchanged),
and `https://h<HOST_1>`, `Bearer a<HOST_1>` (one character past the public start) refused.
Rule chosen: a piece is not read when it is only separator characters, or when it is (a prefix of) the PUBLIC START of the value it
matches: a URL scheme `name://` or an auth word `Bearer `/`Basic `/`Token `/`Digest ` (`runmap._LEAD`; per value, the piece must go past it).
Why not the design's preferred rule (the key's own original must continue the value): G13-2/G13-4/G13-13 pin 4 to 8 characters beside an IDENTIFIER
key (`hunter2-<HOST_1>`, `hunt<HOST_1>`) whose original does not continue the secret, and the ticket keeps them refused: the continuation rule
would send them (leak cases). A length floor (max(8, half the value)) fails G13-4 (`hunt`) by construction. The smallest rule that keeps
G13-1..13 and removes the three false refusals is the public-start exemption. Stated limit (docstrings): a secret whose own first characters are
ordinary words still refuses text that starts so beside a key (a planted value of that kind refuses it for the run); not measurable as a leak.

## M-2 window bound
`_windows` overlap = min(10 x longest + 16, WINDOW_OVERLAP_MAX = VIEW_WINDOW // 4 = 16,384); no InputTooLarge for the overlap any more.
Full 10x overlap up to 1,636 characters; longer values (PEM, planted blob up to 65,536): their raw copy is found by `held_value_left` on the
WHOLE text (no windows), a decoded spelling of up to 16,384 characters across an edge is found, a longer one across an edge is a stated limit.
Tests: 4,000-char secret, 100,000-char non-ASCII document: clean SENT (was mask_budget_exceeded), full-width copy at 4 offsets (window edge) REFUSED;
65,000-char value: clean chunk sent. The 6 s / 8M budgets are untouched (each window's views are still spent and checked).
`longest` is cached in `snap.pieces` (no per-chunk scan of the values).

## m-1 stacked encodings: stated in the `held_in_views` and model_gate docstrings, "Not pinned".
## m-2 hostile 4-char head repeated between keys (14 x `hunt!` before each of 27,000 keys, 2.1 MB)
Before: 7,425,000 of the 8,000,000 characters of budget (0.47 s CPU); a slightly longer text is refused mask_budget_exceeded. After: 275 characters
(same 0.47 s: the cost is the text scan, the bisect was never the cost). A piece already looked up in the text is not looked up or charged again
(`seen`), a lookup charges at most 64, the deadline is read every 1,024 lookups. Distinct pieces are still charged (pinned: G13b-4). Test G13-6 had
the SAME piece 150 times (`huntXXXX<HOST_1>` x 150); it now uses 150 distinct pieces (`hunt0000`..), same intent (a lookup spends budget).
## Nits: N1 deadline read before each window's views are built (views built per window, not all first; test G13b-6, mutant E19s); N3 docstring
claims pinned (G13b-5: base64 copy, NUL-split identifier sent) or marked "Not pinned"; N4 `held_value_left`, `_chunk`, `_enforced`, `_touching_piece`
("shorter than or equal to") docstrings updated; N2: the runner command for the G13 mutants is `python tests/gate_mutants.py E19` (the name filter `G13`
selects only the four ProviderExhausted mutants). N5 stale ids in the SECURITY-README copies: not touched (the doc round).

## Mutants (all by hand: the runner cannot start while test_e5b is red)
7 new (E19m-s), 6 re-anchored (E19b, f, h, i, j, k: their lines changed). MIN_MUTANTS 121 -> 128. All 21 E19* + G24 + R22 run against their killers
in a temp copy: all KILLED, each on the intended message. test_gate_mutants_picked_up green (anchors once each).

## Tests run
tests/test_model_gate.py + test_runmap_enforce_map.py + test_gate_mutants_picked_up + test_gate_install_callers + test_k1b_redaction_layers +
test_runmap_map_write: 365 passed, 1 skipped, 5 xfailed, 1 failed (test_e5b TB-2.11, baseline). test_redact_idempotent_property: 1984 passed.
ruff check/format --check clean, bandit -ll clean on runmap.py, model_gate.py.

## The 4 unidentified failures of the G13 builder's batch
The 28-file list was not recorded; rerun on ALL 54 test files that mention runmap/model_gate (list: grep -lE "runmap|model_gate" tests/test_*.py),
`uv run --all-extras --group test pytest -q -n 2 --tb=no -rf -p no:cacheprovider`, on a `git archive` of d462a4c80 and on this tree:
- d462a4c80: 8 failed, 10608 passed (e5b; test_b64_scan TB-2.8, TB-3.4; test_k5_tools x1; test_p1d_a_rows PU1 card + model; glued_linear[hex and dashes];
  test_repo_rules::test_licences_are_proprietary: no .git in the archive).
- this tree: 14 failed: the same baseline reds, plus 6 in test_redact_own_output(+_hardening) that fail identically on cloud/core-c HEAD 8fa6b9a72
  (G12b commits; not G13/G13b; verified on a git archive of 8fa6b9a72), plus glued_linear[underscore digits] (a perf test under load: fails
  the same on 8fa6b9a72; a different param failed at d462a4c80), plus test_no_hardcoded_values (MINE: the docstring text `https://h` in
  runmap.py; reworded, 15 passed). So the "unidentified 4" of the G13 batch were most likely test_b64_scan x2, e5b and one glued_linear/perf
  param; none is G13's. After the fix the only reds attributable to this branch: none.
