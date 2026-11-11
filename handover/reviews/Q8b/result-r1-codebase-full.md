<!-- full hand-back report of sub-agent acd34384, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

RESULT REVIEW round 1, Q8b, head be53718 (snapshot /home/user/build/snap/q8b-be53718/). I read the code and tests by hand. Nothing was run.

VERDICT: CHANGES REQUIRED. Blocker 0, Major 2, Minor 12.
- The redaction logic is mostly sound. I found no ReDoS, no Blocker leak, and the 26 mutant `old` strings match the built code.
- Two items must be fixed before approval: one fail-open path (F1) and one false shipped sentence (F2).

## Major

**F1. `k1b/redaction.py:276-282` (`_named`) misses a credential entry when `name` and `key` both exist.**
- `nk = next(k for k in obj if k.lower() in ("name","key"))` takes the first of the two in dict order. `vk` takes the first `value` spelling.
- Failure scenario: `{"name":"db","key":"password","value":"<secret>"}`.
  - `nk` is "name", whose value is `db` and is not sensitive, so `_named` returns (None, None).
  - The value is then walked under the key `value`, which is not a credential key, so it is shown as written.
  - The key `key` (new in this ticket) is shadowed. Entries of the shape name/key/value are common (config stores, Vault, Consul-like exports).
  - No test covers it. Only `{"key":..,"value":..}` is tested (N1 row "M2 key/value").
- Fix: collect every name-like key (`name` or `key`, any case) and treat the entry as named when ANY of their values is sensitive. Do the same for several `value` spellings. Add one N1 row and a mutant for it.

**F2. `k1b/redaction.py:44` (`LIMITS`, printed in reports) contradicts the code.**
- It says "A value under a key that names a credential, and every entry of a Kubernetes Secret, is always masked under its own key."
- `_walk` lines 325-327 return a string that is exactly a UTC timestamp unmasked, even inside a Secret's `data`. A setting-key value is also shown (line 323), and bool and None fall through (lines 331-339).
- Only the `_pair` docstring names the timestamp. The ticket mandates the LIMITS text, so the fix is on the ticket side.
- Fix: add "except a text that is exactly a UTC time" to the sentence, or drop the exception. State the same in the CHANGELOG.

## Minor

- **F3. `redaction.py:159,162-181`: the `sensitive` docstring and the T1 claim "a key the older rule accepted is still accepted" is not true for all keys.**
  - Main's `re.IGNORECASE` also matches U+017F (ſ), U+0130 (İ) and U+0131 (ı) against s and i. Python's re docs say this for character classes. I believe it holds for literals too and did not run it. `.lower()` does not fold ſ.
  - So a key such as `paſsword` is a credential key on main and not on the branch. That is fail-open on an exotic spelling.
  - The 200,000-key check and the T1 test use ASCII only.
  - Fix: NFKC then casefold before splitting, and add ſ to T1.
- **F4. `redaction.py:124-127` (`GLUED_ENDINGS`) still drifts from the redactor's key list at `guard/redact.py:599-606`.**
  - The redactor allows glued spellings: `account[_-]?key`, `key[_-]?data`, `cert(ificate)?[_-]?data`.
  - `sensitive("accountkey")`, `"keydata"`, `"certdata"` and `"certificatedata"` are False on the branch. The ticket says "none is left out".
  - No test ties the two lists, which is the stated bug class "key rule and value rule drifted apart".
  - Fix: add those four endings and a T1 row. Better, add a drift test that feeds each alternative of the redactor's key list through `sensitive`.
- **F5. `redaction.py:201-203` comment and the CHANGELOG line 8 say entries past 256 "get the fixed mask" / "are masked under their key only".**
  - That holds only for entries under non-credential keys.
  - An entry past the cap under a credential key (`DB_PASSWORD`) still goes through `_pair` with `credential=True` and is registered, because `known_secret` False does not stop that path.
  - G10 uses `k{i}` keys, so the claim is untested for credential keys.
  - Fix: reword both texts, or add a test for the credential-key case.
- **F6. `redaction.py:241-252` (`_pair` docstring) says "One exception to the masking is made before this function".**
  - There are two: timestamps, and values under a setting key (line 323).
  - The module docstring line 14 ("every number" kept) is stale: numbers under credential keys are masked.
  - Fix: reword both.
- **F7. `tests/test_q8b_credential_keys.py:245-246` (T1 docstring) says "34,410 made-up keys".**
  - 37 words give at most 37 + 37×5×37 + 2×37×5 = 7,252 distinct keys.
  - The test only asserts `> 3000`. Correct the number.
- **F8. `tests/test_q8b_random.py:25-26` (`SeededData(random.Random)`) is a suppression in disguise.**
  - Ruff S311 (selected via `"S"` in pyproject) flags the call `random.Random(seed)`. A subclass declaration is not a call, so the rule goes quiet for the whole file.
  - The repo convention is a visible `rng = random.Random(SEED)  # noqa: S311 - a seeded test generator` (six sites, e.g. `test_k5_layers.py:147`).
  - The subclass hides the use from a `noqa: S311` audit and from any later misuse. Its docstring "never used for a secret" is the only guard.
  - Fix: delete the class and put the noqa with a reason on the three construction lines (118, 272, 345).
- **F9. Test oracle shares code with the code under test, and is duplicated.**
  - `test_q8b_random.py:4-5` says the oracle "shares no pattern with `approvals/gate.py`". Yet `outside_code` (lines 199-210) and `bare_domains` (`test_q8b_card_text.py:421-442`) call `gate._closed_fences` and `gate._INLINE_CODE`.
  - A bug in the fence or inline-code decision is invisible to P2(b) and N7.
  - The same oracle is pasted twice: `bare_domain_tokens` at lines 213-243 and `bare_domains`.
  - `ONLY_PLACEHOLDERS` is copied three times: `redaction.py:207`, `test_q8b_credential_keys.py:37`, `test_q8b_random.py:31`.
  - The fence/code-line set logic is copied in `gate.defang_domains` (lines 273-278) and in both tests.
  - Fix: one shared test helper that imports `R._ONLY_PLACEHOLDERS`, and drop the "shares no pattern" claim or write an independent fence reader.
- **F10. `test_q8b_random.py:144` (P1 property b) cannot fail on its own.**
  - If (a) holds, the shown value is only placeholders or the fixed mask. Those contain no run of 4 or more characters from `qxzjkwvy` and digits, so (b) holds too.
  - `test_p1_no_run_of_the_value_is_readable_under_its_key` therefore only fails when (a) fails. It is a redundant duplicate; no mutant is pinned to it.
- **F11. Loops replace per-row tests.**
  - Affected: `test_n4`, `test_n6_a_domain_after_a_placeholder`, `test_n1_a_value_under_a_setting_key_is_masked`, `test_n6_f6c`.
  - The first failing row hides the others. For the mutant killers this is fine, because every message carries the row label.
  - The cost is that fail-on-base evidence shows one row of many. Use `parametrize` with ids, as already done for N1/N2/G6.
- **F12. Mutant list gaps (rows M1-M23 are fine; builder added M11b, M12b, M20b).**
  - Unpinned behaviours: the 256 cap (G10 asserts it but no mutant removes it), `text.isdigit()` and `_ONE_LOWER_WORD` in `_attempts`, `WORD_PAIRS`, `COUNT_WORDS_BEFORE_TOKENS`, the timestamp branch of `_setting_value`, the `>` alternative of `_ANY_NAME_DOT`, `_fold_dots`.
  - Whether each named killer really fails could not be checked by running. By trace (M1-M10, M12b, M13-M16, M19-M21, M23), the killers should kill.
  - Two killers depend on redactor behaviour I could not run: M7 (`test_n3_no_fragment_for_an_esc_value`) and M22 (the N9 case).
- **F13. Over-masking and duplication I could not call defects.**
  - Over-masking: `sensitive` (lines 137-139, 179) treats `reasoning_tokens`, `cache_read_tokens`, `audio_tokens` as credential keys, because `COUNT_WORDS_BEFORE_TOKENS` is a short allowlist. Their numeric values become `<SECRET_REDACTED>` (cost, not a leak). It should be named in the docstring cost list.
  - Duplication: `slack_channel.py:75-80` rebuilds the seeded `RunMap` that `channel._seeded` (lines 61-65) already builds. Consider letting `redact_for_people` seed its own map.
  - Cost: `_pair` makes up to 4 calls plus the final one per value. That is a 5x worst-case amplification of the `total` char counter in `mask` for credential values that are refused. G10 measures only the non-plain Secret path.
- **F14. Cosmetic: `approvals/channel.py:23-28` comment reflow.** The edited sentence leaves one over-long line (about 128 characters) and a broken wrap. Ruff does not enforce this (E501 is not selected).

## Checks that came out clean

- **ReDoS.** None of the new patterns has a nested quantifier:
  - `_ONLY_PLACEHOLDERS` is `(?:<[A-Z][A-Z0-9]*_[0-9]+>)+` fullmatch; `[A-Z0-9]*` cannot contain `_`, so it is linear.
  - `_ANY_NAME_DOT` has single-character look-behind alternatives and a fixed 2-character lookahead.
  - `_SAFE_KEY`, `_SPLIT`, `_CAMEL`, `SETTING_VALUE` are linear.
  - `_TRAILING_DIGITS` `(?<=[a-z])[0-9]+$` is linear, since a digit run's interior fails the look-behind.
  - The old `_DOMAIN` and `_NON_ASCII_HOST` patterns are unchanged, and they now run once, on the final text.
  - The new code calls `sensitive` up to 3 times per string, with no cache.
- **`SENSITIVE_KEY` removal.**
  - In the snapshot, the only mention is `CHANGELOG.md:7`, which announces the removal and points to `sensitive(key)`.
  - In `/home/user/build/q8a2-dryrun/main-2a8c2aa/src`, the only other mention is its own definition at `k1b/redaction.py:88,100`.
  - Other users of the module are `report.py:49` (`KINDS_NOTE`, `LIMITS`), `replay.py:31` (`SCHEME`, `redact_bundle`) and tests.
  - I found no reference in the tests, demos, docs or tools of the snapshot. No alias is kept; the CHANGELOG states this.
- **`LIMITS` text** equals the ticket's 1g string.
- **Producers and rounds.**
  - `guard/producers.py:38,51` carry the two data rows.
  - `tests/test_k5_round11.py:150-162` adds the second loop. It is additive: the first loop and the test at line 113 are untouched.
  - `tests/test_k5_producers.py:155` adds `redact_for_people` to `REDACTORS`.
  - I saw no weakening.
- **Mutant plumbing.**
  - `q8b_mutants.py` matches the runner's `Mutant` fields (`test_file`, `only_test`, `pinned`).
  - Every killer is a non-parametrized function, as `only_test` needs.
  - The CI step is placed after the stage mutants step (`ci.yml:95-96`).
- **Idempotence of the new `[.]`.** `_ANY_NAME_DOT` skips a dot after `[` and `at-` is not matched by `_MENTION`, so the last step is idempotent by reading.

## Not checked or not verifiable

- **Nothing was run:** no pytest, ruff, `ruff format --check`, bandit, mutants or perf step. The ruff and format state is by eye only.
- **Evidence missing:** the evidence file `RESULTS.md` is absent; only `01-head.txt` exists at the path.
- **Existing tests not diffed:** main's tests are not in `/home/user/build/q8a2-dryrun/main-2a8c2aa/`, so I could not diff the existing tests, only read their snapshot state.
- **Unverified claims:** the ſ/İ/ı matching in F3, the redactor behaviours behind M7 and M22, and every measured number in the appendix (A2-A5).
- **Not read:** `cards.render_shadow` and `requests.summary`, so N5 and G8 were not traced. Also the Postgres tests, the CI perf step and the existing perf-marked tests.
- **No perf test:** the branch adds no `perf`-marked test for `defang_domains`, `_ANY_NAME_DOT` or `sensitive` on long keys. The new P1 (3,000 cases, 24-39 s) and P2/N9 run unmarked in the default suite. I found no existing perf test that reaches `defang_domains` (only `test_g4_parity.py` mentions `clean`/`sanitise_text`, which I did not read further).
- **No PR77 rebase:** nothing here tests the rebase coupling.
