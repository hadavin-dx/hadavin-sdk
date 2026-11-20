# TW-order020 (test-writer, ORDER 020; new tests only, nothing existing edited)

## Files
1. tests/test_gate_install_callers.py (MJ-C). AST scan of src for `.chat(` / `.apply_guardrail(`, `ModelGate(`, `.bind(`, `NO_MAP`.
   Tables inside the test: INSTALLED (evals.py, guard/judge.py, k1b/loop.py, runtime/agent_loop.py -> binder module) and BYPASS (guard/bedrock_guardrail.py vendor detector; guard/model_gate.py the gate itself; extract.py until F-install deletes it).
   Plain (pass today): a new caller in neither table fails; every table entry exists and still calls a model; NO_MAP named only in evals.py / k1b/replay.py (the install draft names only these two, not cli.py); no `bind(mapping=None)`; no `ModelGate(` with enforce= or a lambda worst_case= (plus a self-test of the checker); the gate module has no stage word or stage argument (so pilot/prod refusal is an install-time check).
   Strict xfail (reason: core-b has not installed the gate yet: requests/3-bind-mapping-required.md): every caller has a `bind(..., mapping=)` in its binder module; both command lines name NO_MAP; the module that builds the gate looks at pilot/prod and passes no non-default enforce/worst_case. When core-b installs, they XPASS(strict) = failure: remove the marker.
2. tests/test_textnorm_mixed_script_micro.py (m-4). Micro + Latin: False. Micro + Latin + Cyrillic a: True (Latin and Cyrillic, rule (a); sign dropped first; docstring "removed BEFORE the analysis"). Micro + Cyrillic only: False (docstring "not flagged by this function"). Greek mu / Omega + Latin: True. Ohm cases. Post-15.1.0 code points (U+1C89, U+1C8A, U+10D4A): script None, neutral. Script not Script_Extensions: U+0640 tatweel (Common) next to Latin: False.
3. tests/test_gate_mutants_picked_up.py (m-6). Cheap always-on checks (imports, count >= 66, search text exactly once, expect fragment, killer named and present); full run behind HADAVIN_RUN_MUTANTS=1 (the repo has no slow marker: CI deselects only `live` and `perf`), asserts last line "N of N good; problems: []".

## Measured answer: Han / Hiragana / Katakana / Hangul / Bopomofo code points with a Latin look-alike entry in _confusables.TABLE (852 entries, Unicode 15.1.0)
Count 1: U+3007 IDEOGRAPHIC NUMBER ZERO (Han) -> "O". Hiragana 0, Katakana 0, Hangul 0, Bopomofo 0.
A Latin word with U+3007 ("pay"+U+3007+"al") is NOT flagged by has_mixed_script (Han exempt). Pinned as `test_limit_han_ideographic_zero_in_a_latin_word_passes_as_not_mixed` (not an xfail); a completeness test fails if a regenerated table adds more.

## Results
- ruff check: All checks passed. ruff format --check: 3 files already formatted.
- pytest -n 2 on the 3 files: 1 failed, 30 passed, 1 skipped, 3 xfailed.
- THE FAILURE IS REAL, not a test bug: `test_every_mutant_search_text_is_in_its_file_exactly_once` lists 24 mutants of tests/gate_mutants.py whose search text is in guard/model_gate.py or guard/runmap.py 0 times (R10: 2 times) in the current tree (G3a, G3e, G3b, G4a, G4b, G5, G6c/d/f, G7a, G7f-k, G8b, G14, G21, O2, O5, R4, R7, R9, R10). Other agents are editing model_gate.py and runmap.py; the mutants must be re-synced after they finish (the script itself exits 2 on this). Not weakened.
- Full mutant run with HADAVIN_RUN_MUTANTS=1: exits 2 at once (same stale search texts), so no full-run time could be measured. NOT RUN to completion; re-run `HADAVIN_RUN_MUTANTS=1 pytest tests/test_gate_mutants_picked_up.py` after the mutants are re-synced and record the time.
## NOT RUN
Full mutant run; the rest of the suite.
