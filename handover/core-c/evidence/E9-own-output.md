# E9(2): `_OWN_OUTPUT` restricted to SECRET tokens (lead ORDER 023)

Change (src/hadavin_sdk/guard/redact.py, `_OWN_TOKEN`/`_OWN_OUTPUT` + comment; `_decide` unchanged, it still uses `_OWN_OUTPUT.fullmatch`):
the exemption names `<SECRET_n>` and the escaped look-alike `U+2039 SECRET_n U+203A` only; a trailing cut-off opening is only of a SECRET token
(`<SECRET_n`, `<SECRET_`, `<SECRET`, `<SECR`..`<S`). The older rule (a value of genuine placeholders of any kind) is untouched.
Purpose, as far as it holds: a tool error redacted twice makes no junk map entry for the escaped `password=U+2039SECRET_1U+203a` (a SECRET token the first pass wrote). It does NOT hold for the tokens of other kinds the first pass writes after a key (`token=<JWT_1>`, `api_key=<APIKEY_1>`, `password=<EMAIL_1>`): their escaped spelling is masked, one junk entry per distinct token. Accepted trade-off, option (a) (E9 result review round 1, Major 1); the lead's option (b) is the alternative. Pinned by tests (E9(2) fix round).

## Shapes (SECRET value after `password=` unless noted)
| shape | before | after |
|---|---|---|
| `‹EMAIL_1›` (the value in `password=‹EMAIL_1› host`: the pattern stops at the space), `‹IPV4_1›` | unmasked | masked whole |
| `<EMA`, `<EMAIL_`, `<EMAIL_1`, `<I`, `<IPV4_12` | unmasked | masked whole |
| `‹SECRET_1›<EMA` | unmasked | masked whole |
| `‹SECRET_1›<UUID_3>‹SECRET_1›`, `‹SECRET_1›<UUID_3>‹IPV4_1›` | unmasked | masked whole |
| `Cookie: ‹SECRET_1›; ‹IPV4_1›, ‹SECRET_1›` | unmasked | masked whole |
| `‹SECRET_1›`, `<SEC`, `<SECRET_`, `<SECRET_1`, `‹SECRET_1›; ‹SECRET_2›, ‹SECRET_1›` | unmasked | unmasked (unchanged) |
| `<EMAIL_1> <IPV4_1>` (+ tab, `;`, `,`, `<EMAIL_1> <SEC`) | unmasked (older rule) | unmasked (unchanged) |

## Fail-before (new tests run against `git show HEAD:...redact.py` in a scratch copy: 17 fail, all pass after)
- tests/test_redact_own_output.py::test_a_genuine_placeholder_of_another_kind_beside_a_lookalike_is_masked_whole
- ::test_a_lookalike_of_another_kind_in_a_secret_value_is_masked_whole
- ::test_a_cookie_run_with_a_lookalike_of_another_kind_is_masked_whole
- tests/test_redact_own_output_hardening.py::test_e9_a_cut_off_opening_or_lookalike_of_another_kind_is_masked (7 params)
- ::test_e9_a_secret_token_followed_by_a_cut_off_opening_of_another_kind_is_masked
- ::test_e9_a_cut_off_opening_of_another_kind_alone_is_masked, ::test_e9_a_lookalike_of_another_kind_alone_is_masked
- tests/test_redact_context_after_sweep.py::test_e9_a_secret_value_spelled_like_a_token_of_another_kind_is_masked (4 params)

## Mutants (tests/redact_mutants.py, contiguous block at the end; `python tests/redact_mutants.py E9`): 3 of 3 KILLED
- E9-1 any kind again -> test_e9_a_lookalike_of_another_kind_alone_is_masked
- E9-2 cut-off opening of any kind -> test_e9_a_cut_off_opening_of_another_kind_alone_is_masked
- E9-3 escaped alternative removed -> test_redact_untrusted_twice_adds_nothing

## README wording (SECURITY-README-v5.md; owner: core-c drafter)
K43 and decision 7 already say only `‹SECRET_n›` (ASCII digits) is exempt: the code now matches, no change needed there. Possible additions:
K43 could state that a cut-off SECRET opening (`<SEC`, `<SECRET_`) is exempt too (not mentioned now), and that look-alikes of other kinds
(`‹EMAIL_1›`) and cut-off openings of other kinds (`<EMA`) are masked.

## Result review round 1 of E9(2) (fresh sonnet reviewer, 09:47Z; snapshot refs/e9 = e8ff6de2b; read only, nothing run)
Verdict: the regex is sound and leaks nothing new; no Blocker; 2 Majors, 4 Nits.
- MAJOR 1 The purpose "no junk map entry on the tools error path" holds only for SECRET-kind tokens (redact.py:878-880 "The redactor only writes a SECRET token after a secret key" is FALSE; E9-own-output.md line 6 "Purpose kept" is wrong): PATTERNS runs EMAIL, IPV4, APIKEY, JWT, URLCRED, HIGHENTROPY and PHONE before the SECRET key=value pattern (which runs last): `tools.error_reason` (tools.py:1005) runs `redact_bounded(msg, {}, neutralise_untrusted)` and the first pass writes `api_key=<APIKEY_1>`; `prepare_output` then calls `redact_layered` -> `redact_untrusted` with the run map (tools.py:967, 982); `escape_placeholders` (runmap.py:354-359, `_LOOKALIKE` matches every kind in any case) rewrites `<APIKEY_1>` to `‹APIKEY_1›`; the SECRET value `‹APIKEY_1›` is not a genuine placeholder, `_OWN_OUTPUT.fullmatch` fails and it is masked: the run map gains `<SECRET_n>` = `‹APIKEY_1›`, the model sees `api_key=<SECRET_n>`. Before E9(2) no entry was made. Every error text with a masked JWT, key, e-mail or IP after a credential key now makes one junk SECRET entry per distinct escaped token (swept from every later text); a cut-off opening (`password=<EMA` when the 160-character cut of `error_reason` lands inside `password=<EMAIL_1>`) is also a junk entry. Not a leak, no new abuse (a typed `password=<anything>` already makes one entry per distinct value; MAX_MAP_ENTRIES bounds as before); harm: map growth and noise, and the model loses the kind of a masked value. The same holds for k1b (it calls `tools.redact_layered`). Tests cover only SECRET-kind first-pass output. Fix options: (a) state the trade-off honestly ("the first pass writes other kinds' tokens after a key too; their escaped spelling is masked, a junk entry per token, accepted to close the hole") and add a test pinning the error-path behaviour for `token=<JWT>` and `password=a@b.co`; (b) keep the purpose by exempting escaped tokens of the kinds the first pass can write after a key, only on the tools path (flag from `neutralise_untrusted`). core-c DEFAULT: (a) (security first, the lead's order); the lead may ask for (b).
- MAJOR 2 Stale documents contradict the code: ESCALATIONS.md:79-80 (E9 "tokens of any kind", "NOT fixed yet"); tickets/G7-context-after-sweep.md:83-84, :149 and :262-264; tickets/G4-P1c-redactor-gaps-v5.md:64, :377-378, :704 (TB-2.2 `test_encoded_kind_own_output` would fail), :1131 (a draft in progress: the drafter is told); SECURITY-README-v5.md:586 (K43) is correct but omits the cut-off SECRET openings `<SEC`, `<SECRET_` and the `;` `,` separators.
- NIT 1 the stated limit omits the cut-off openings (`<S`, `<SE` ... `<SECRET_12`): a real 2-character password `<S` or a 4-character `<SEC` stays in clear with no map entry; pinned by tests (hardening.py:111-114, after_sweep.py:492-493); add "or a cut-off start of one" to the limit sentence and K43. NIT 2 `_NEEDS_OWN_OUTPUT` and the comment at after_sweep.py:524-526 are accurate. NIT 3 the evidence row `‹EMAIL_1› host` gives the value as `‹EMAIL_1› host`; the key=value pattern stops at the space so the value is `‹EMAIL_1›` (the test asserts `password=<SECRET_1> host`). NIT 4 CHANGELOG.md has no E9 entry.
- Regex attack results: `_OWN_OUTPUT` anchored with `fullmatch`, case-sensitive (`‹secret_1›`, `<Secret_1>`, `‹SECRET_١›` masked: hardening.py:56-68); no ReDoS (separators and tokens have disjoint first characters); the `.strip(" \t;,")` guard fine; remaining leaks all stated (a real credential spelled `<SECRET_1>`/`‹SECRET_1›`, a run of them, or a cut-off start; the older genuine-placeholders rule for a typed `password=<EMAIL_1> <IPV4_1>`); idempotence and settle: `password=‹EMAIL_1› host` -> `password=<SECRET_1> host` with map `{<SECRET_1>: ‹EMAIL_1›}`; a second redact sees a placeholders-only value (`_decide` returns None at line 1664 before `_OWN_OUTPUT`); restore gives the original back; settle at a fixed point; `_place` registers no `_spell` form.
- Claims: 17 fail-before ids VERIFIED as a count (3 + 7 + 1 + 1 + 1 + 4), the run UNVERIFIABLE (no raw output in S); mutants E9-1..3: block and wiring VERIFIED (last block in `M`; search texts unique at redact.py:883 and :885; killers by reading), result UNVERIFIABLE; "4039 passed" UNVERIFIABLE (not in S); "140 passed" DIFFERS (the only hit in S is F-G0-1.md:24, an older file); `# noqa: S105` justified (ruff selects S; precedent backends/table.py:257, 259; optional rename `_OWN_TOKEN` -> `_OWN_PLACEHOLDER`).
- Not read: redact.py beyond 1-987 and 1620-1740, most of runmap.py, agent_loop.py and k1b (grep only), tools.py beyond 930-1015, the rest of the suite, the CHANGELOG body; one ripgrep look-around failed so other tests using look-alikes of other kinds after a key were not confirmed.

## E9(2) fix round (review round 1: Major 1, Major 2, Nits 1, 3, 4)
- Major 1: option (a), core-c's default. Comment above `_OWN_TOKEN`/`_OWN_OUTPUT` rewritten (comments only, no code change): the false sentence "The redactor only writes a SECRET token after a secret key" is gone; the trade-off and the limit (now naming the cut-off SECRET openings `<S` .. `<SECRET_12`) are stated.
- Measured through `tools.error_reason` then `tools.prepare_output` (run map empty before): `token=<JWT_1>` -> `token=<SECRET_1>`, map `{<SECRET_1>: ‹JWT_1›}`; `api_key=<APIKEY_1>` -> map `{<SECRET_1>: ‹APIKEY_1›}`; `password=<EMAIL_1>` -> map `{<SECRET_1>: ‹EMAIL_1›}`; a 160-character cut `password=<EMA` -> map `{<SECRET_1>: <EMA}`. A third pass adds no entry (it only escapes `<SECRET_1>` to `‹SECRET_1›`). Restore gives nothing back for a SECRET kind.
- New tests (5, pin the accepted trade-off; each docstring names option (b)): tests/test_redact_own_output_hardening.py::test_e9_error_path_token_of_another_kind_after_a_key_makes_one_junk_entry[jwt|apikey|email], ::test_e9_error_path_cut_off_opening_of_another_kind_makes_one_junk_entry; tests/test_redact_own_output.py::test_e9_redact_untrusted_twice_with_an_address_value_makes_one_junk_entry.
- Major 2: ESCALATIONS.md E9 and tickets/G7-context-after-sweep.md lines corrected (SECRET only, new limit). G4 ticket and SECURITY-README-v5.md K43 not touched here (other owners): G4 :64, :377-378, :704, :1131 and K43 (add cut-off SECRET openings and the `;` `,` separators) still to be fixed by their owners.
- Nit 3: evidence row fixed. Nit 4: CHANGELOG.md entry added. Nit 1: in the comment and G7 ticket; K43 pending (owner: drafter).
- Run now (09:49Z, worktree, `pytest -n 3`, files tests/test_redact_own_output.py, tests/test_redact_own_output_hardening.py, tests/test_redact_context_after_sweep.py): `145 passed in 19.51s` (140 before the 5 new tests; the earlier "140 passed" was not from a run recorded in this file).
- Batch (those three plus tests/test_k5_tools.py, test_k5_layers.py, test_k1b_redaction.py, test_k1b_redaction_layers.py, test_runmap*.py): `422 passed in 79.96s (0:01:19)`.
