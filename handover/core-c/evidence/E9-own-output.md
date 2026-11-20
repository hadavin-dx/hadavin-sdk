# E9(2): `_OWN_OUTPUT` restricted to SECRET tokens (lead ORDER 023)

Change (src/hadavin_sdk/guard/redact.py, `_OWN_TOKEN`/`_OWN_OUTPUT` + comment; `_decide` unchanged, it still uses `_OWN_OUTPUT.fullmatch`):
the exemption names `<SECRET_n>` and the escaped look-alike `U+2039 SECRET_n U+203A` only; a trailing cut-off opening is only of a SECRET token
(`<SECRET_n`, `<SECRET_`, `<SECRET`, `<SECR`..`<S`). The older rule (a value of genuine placeholders of any kind) is untouched.
Purpose kept: a tool error redacted twice makes no junk map entry for the escaped `password=U+2039SECRET_1U+203a`.

## Shapes (SECRET value after `password=` unless noted)
| shape | before | after |
|---|---|---|
| `‹EMAIL_1› host`, `‹IPV4_1›`, `‹EMAIL_1›` | unmasked | masked whole |
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
