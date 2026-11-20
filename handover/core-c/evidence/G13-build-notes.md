# G13 build notes (gate net: secret piece beside a key, decoded forms; E19 M1 net, M2, N1-N3)

Branch wip-g13 on cloud/core-c d462a4c80. Code commit: "code G: G13 ..." (src, tests). Everything below was run on this tree.

## Baseline (before any edit), NOT G13's
test_e5b (TB-2.11) in tests/test_runmap_enforce_map.py; TB-2.8 (test_tie_break_keeps_the_order_of_different_originals) and TB-3.4
(test_no_run_no_extra_work) in tests/test_b64_scan.py. Same three after G13. reconciliation builder a40ba60b (wip-mix) owns them.

## Phase 0 (re-measured on this tree)
M1 exact input: `x <SECRET_1><SECRET_2> y` / `x <SECRET_2><SECRET_1> y` in both map orders, net False (closed by G9; pinned G13-1).
Net half open before: `x hunter2-<HOST_1> y` False, `x hunt<SECRET_2> y` False. M2 forms: all SENT before (red column below).

## Red before / green after
Red on the old src (tests only added): 22 failed (t7 x5, d7, r2_m2, G13-10 x6, G13-12, G13-13, G13-2..8 incl. 7); G13-1 and G13-11 green.
After: test_model_gate.py + test_runmap_enforce_map.py: 321 passed, 1 failed (e5b, baseline).

## Pins that changed by design (before -> after)
- t7 (5 params) `test_t7_stated_limit_a_hidden_spelling_of_a_known_value_is_not_replaced_by_the_gate`: document sent `is doc` ->
  `test_t7_a_hidden_spelling_of_a_known_secret_refuses_the_call_an_identifier_passes`: refused held_value_left, nothing sent; a
  full-width HOST still sent as written.
- d7 (UTF-16 as written, ~:1868) `..._a_copy_split_by_nul_utf16_or_an_ansi_sequence_is_not_replaced` -> `test_d7_a_copy_split_by_nul_or_utf16_refuses_the_call_an_ansi_split_copy_passes`:
  NUL-split message and UTF-16LE document refuse; ANSI-split copy still sent, whole copy beside it replaced.
- r2_m2 last line: `<SECRET_1>abcdef` sent -> refused held_value_left; `<SECRET_1> abc` sent.
- Module docstring of model_gate.py updated (t7, d7 ids renamed; G13 test ids added); test_d8 stays green.
- tests/contracts: no pin of "UTF-16 sent as written" found by grep; the suite cannot run here (no boto3), so NOT RUN.

## Mutants
12 new, named E19a..E19l (the names G13b-G13e were already taken by ProviderExhausted mutants), in tests/gate_mutants.py; G24 and R22
search texts re-anchored (their old text changed with the diff; G24 now drops the whole `or held_in_views` line; R22 drops the sweep AND the
piece call). MIN_MUTANTS 109 -> 121. All 14 (12 new + G24 + R22) run BY HAND against their killers: all killed, expect on the first failure line.
The runner (`python tests/gate_mutants.py`) was NOT run (baseline e5b red).

## Section 4 re-measured (2,000 planted values, 256 KB; this shared box)
ASCII 0.12 s; with %20 0.16; non-ASCII 0.70; 13,000 keys 0.24; hostile `Zq9x0<SECRET_n>` 0.26 (held_value_left); non-ASCII 600,000 chars 0.71;
2,000 held-back ASCII 0.25 / non-ASCII+% 0.50. No mask_budget_exceeded.
Property corpus (1,978 inputs, redact_text -> snapshot -> enforce -> net -> views on the producer output): 0 refused (HEAD 0). 1,262 inputs
have a secret kind in the map (ticket said 1,470: counting differs, unverified). Run on the RAW text instead of the producer output, 699 are
refused: correct (the raw text holds the spelled secret; it never reaches the gate unredacted).
test_redact_idempotent_property.py: 1984 passed.

## Lead decisions: DEFAULTS built (D1-D8 not approved)
D1 k1b replay with NO_MAP unchanged; D2 k1b echo unchanged; D3 extract.py unchanged; D4 base64 not read at the gate (docstring says so);
D5 middle pieces between two keys are a stated limit; D6 N1 = comment line only under ENFORCE_MAX_STEPS, no test; D7 r2_m2 flips to refuse;
D8 identifiers in decoded forms still pass as written.

## Not run
test_k5_round5/7 (need `cryptography`), test_k5_fixes1/2 and tests/contracts (no psycopg / boto3), the mutant runner, CI.

## Wider batch (28 files with model_gate/runmap/redact imports, one pytest run, no -n): 11 failed, 7169 passed, 23 xfailed
7 of the 11 were listed (tail of the output) and fail identically on the base d462a4c80 (missing services/fixtures, not G13):
test_k5_round9b live-deployment, test_k5_round10 live-postgres, test_k5_tools x3, test_p1d_a_rows PU1 card/model. The other 4 failure names
were cut off by the output tail and were NOT identified or compared with the base: a follow-up should rerun those files on both trees.
Individually green on G13: test_runmap_map_write 10, e15 15, own_output 27 + hardening 44, textnorm_siblings 22, gate_install_callers 10 (+5 xfail),
k1b_redaction_layers 14, redact_glued_rest 459, k5_fixes7 533, property 1984, test_b64_scan 53 (+2 baseline reds).
ruff format/check clean on all G13 files (one pre-existing SIM102 in src/hadavin_sdk/k1b/bundle.py:307, not touched); bandit -ll clean on runmap.py, model_gate.py.
