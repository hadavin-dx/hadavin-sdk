<!-- full hand-back report of sub-agent a517cf42, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

# Q8b plan review, round 1 (implementation readiness)

**Verdict: NOT READY.** One blocker and nine majors. Nothing was run: every "passes on main" or "fails on main" statement below is derived from reading the code and needs a run by the author.

Read in full: the ticket, the persona file, `CLAUDE.md`, both rule files, `k1b/redaction.py`, `approvals/channel.py`, `guard/producers.py`, `ci.yml`, `tests/stage_mutants.py`, `tools/scan_repo.py`, `tests/test_k5_producers.py`. Read in part: `gate.py` 90-379, `slack_channel.py` 1-110, `runmap.py` 24-53 and 395-543, `redact.py` 476-615, `agent_loop.py` 260-295, `requests.py` 28-55, several test files.

## Blocker

**B1. Section 1b: the quoted spelling does not work for every credential key.**
- `k1b/redaction.py:89` (`SENSITIVE_KEY`) accepts `authorization`, `private_key`, `bearer` and `passphrase`.
- The redactor's quoted-value rules (`guard/redact.py:577-590`) list only `password|passwd|pwd|pass|secret|token|api_key|apikey|credential|session`.
- For `private_key="correct horse battery staple"` the only matching rule is the general one at `redact.py:598-614`, which takes an optional opening quote and stops at white space. So `correct` is planted in the map, which is the fragment 1b says it removes.
- For `authorization`, `redact.py:488` takes one optional word and then one token of 8 or more characters.
- The quoted rules also cap the value at 256 characters (`[^"]{0,255}`), so a longer multi-word value falls to the general rule in the same way.
- Consequences: "this also closes F5b for credential keys" and the CHANGELOG line "The whole value is also masked where it is repeated" are false for these keys and lengths. P1 ("random credential keys … including a second record that repeats the value") would fail on the branch, and so would N3 with those keys.
- The fix cannot be in `redact.py` (forbidden), so the ticket must decide. Proposed text for 1b, to be confirmed by a prototype run:

  > "A value that is not plain is never written under its real key. It is written once as `FALLBACK_KEY + '="' + value + '"'` (or with `'`), and the value part is what follows `FALLBACK_KEY + "="`. A spelling longer than 256 characters that is not plain is not tried and gets `MASKED` (limit stated in `LIMITS` and CHANGELOG beside the both-quotes limit). The author's run for the keys `authorization`, `private_key`, `privateKey`, `bearer`, `passphrase` and for a 300-character multi-word value is pasted here: …"

## Majors

**M1. Mutants M1, M2 and M3 are probably not killed by the tests named for them.**
- After 1b, every N1 input that leaked on main is either masked whole by the quoted rule or never tried. The partial-result branches of rule 1a are then not reached by those inputs.
  - M2 (`fullmatch` to `match`) with `AKIA… and the rest`: quoted, result is one placeholder, both accept.
  - M3 (key rewritten) with `a b`: the result starts with `key=`, so the branch is not entered.
  - M1: the same reasoning applies.
- `_pair(key, value, f)` takes the redactor as a parameter, so add direct tests with a stub. Text to add:

  > "N1b, direct tests of `_pair` with a stub `f` (must fail on main): (i) `f` returns `key + '=<SECRET_1> tail'`, expect `MASKED` (kills M1 and M2); (ii) `f` returns `'p<SECRET_1>ssword=<SECRET_1>'`, expect `MASKED` (kills M3); (iii) `f` returns `key + '=<SECRET_1><EMAIL_2>'`, expect that text back. Also add the real-redactor case `{'password': 'a'}` (plain one-letter value)."

**M2. Three "must fail on main" tests can pass on main with the assertion as written.**
- **N4 percent and entity spellings.** On main the hook brackets the decoded view before the patterns see it, so no view finds the address and the encoded input comes back (`bob%2Esmith%40example%2Ecom`; the entity form as `bob.smith&amp;#64;example[.]com`). "Neither the address nor its bracketed spelling" holds there.
- **N4 "bracketed spelling" has two forms on main.** The ticket's own F6 output shows `bob[.]smith@example[.]com` in the angle-bracket case. Text to add:

  > "Assertion for N4, N5, N7 and P2(a): let `flat = runmap.undo(result).replace('[.]', '.')`; assert the address is not in `flat`, and that `smith` and `example` are not in `result`."

- **N6 `10.0.0.5.evil.com`.** `_DOMAIN` (`gate.py:112`) matches the whole string on main and brackets every dot, so "no bare `evil.com`" passes. Add: "also assert `10[.]0[.]0[.]5` and `10.0.0.5` are absent".
- **N2 password case.** On main the copy becomes `login with <SECRET_1> horse battery staple failed`, so "value not in text" passes. Add: "assert `horse`, `battery` and `staple` are each absent from the log line; the value must be multi-word".

**M3. Section 1c does not say how `_walk` carries the flag.**
- `_walk` line 144 recurses with `secret_data=True`, and line 146 passes `sens` in the same parameter. So `secret_data` already means both "Secret data" and "nested under a credential key", and `_pair` is called at line 131 where the two cannot be told apart.
- Text to add:

  > "`_walk` gains a fourth parameter `known_secret: bool = False`. Line 144 passes `known_secret=True`. Lines 149 and 151 (list, tuple) pass it on. Line 146 passes it on unchanged (so a dict nested under `data` keeps it, and a dict under a credential key does not get it). Line 131 calls `_pair(key, obj, f, known_secret=known_secret)`. Line 142 (env form) does not pass it."

- Also give the exact loop: the order of real key and `FALLBACK_KEY` per spelling, and that the value-part check uses the key actually written.

**M4. `defang_domains`: the after-placeholder rule has no pattern and `gate.py` has no placeholder definition.**
- `gate.py` imports only `guard.redact.strip_ansi` (line 74). `_LT` at line 142 holds a second hand-written placeholder shape.
- State the import and paste the prototype's pattern. Proposed, not run:

  > "`from hadavin_sdk.guard import runmap`; `_AFTER_PLACEHOLDER = re.compile(rf'({runmap.PLACEHOLDER.pattern})((?i:(?:\.[\w-]+)*\.(?:{_TLDS})))(?![\w@-])')`; every `.` of the tail group becomes `[.]`. It runs on the same outside-inline-code parts, after `_DOMAIN`."

- Name the helpers the split of `_defang_outside_code` produces.
- Make the new argument keyword-only (`sanitise_text(text, *, defang=True)`), otherwise N8's check for `defang=False` misses `sanitise_text(t, False)`.

**M5. N9 is in the wrong list and its fallback is a design choice left to the builder.**
- The ticket says `channel.py:37` is "NOT proved safe", yet N9 sits under "pass on main too".
- "Return the candidate only when it also hides every original of the first map" does not say what is returned otherwise.
- A likely counter-case by reading: a tag between an IP address and a digit plus a markup-split secret. The joined view is returned and contains the first candidate's IP as a substring.
- The author should run N9 on main and on prototype E, then write the outcome and the exact rule (for example: "else return `out`").

**M6. The mutant list does not yet fit the runner.**
- `tools/mutation_runner.py:155-170`: each `Mutant` needs `expect` (4 or more characters of the killer's assertion message), one `pinned` test id, `only_test` and `test_file`. The ticket gives no test file names, no function names and no assertion messages.
- M11 names two killers. Its revert also leaves `_neutralise` unimported, so N5 would die with `NameError` (a crash is not a kill without `allow_crash`).
- Text to add: "every new assertion carries a message; M11 is pinned to N8 only (static check)", plus a table of mutant, test file, test function and `expect`.
- Fix the new test file names, for example `tests/test_q8b_pair.py`, `tests/test_q8b_cards.py`, `tests/test_q8b_fuzz.py`.

**M7. P1 and P2 are under-specified.**
- No seed value for P1, no alphabet, no run-time bound, and P2's generator lives outside the repository (`/home/user/build/q8b-author/probe_f6_prop.py`).
- The repository convention is in `tests/test_k5_round12_fuzz.py:19-26`: `SEED`, `CASES`, a rare-letter alphabet `qxzjkwvy` so fragments cannot collide with keys or schema words, and an `ENDS` list with Unicode white space.
- Text to add:

  > "P1: `SEED = <number>`, `CASES = 3000`; words from `ALPHA = 'qxzjkwvy'` plus digits; separators from that file's `ENDS`; values at most 200 characters; a both-quotes value is asserted separately; measured run time on the branch: … s (limit …)."
  > "P2: the generator is pasted into the test (7 identifiers listed here: …), `SEED = 8`, `CASES = 4000`, `redact_text(text, {})`; 'outside code' means not in a closed backtick fence body per `gate._closed_fences(result)` and not in an `_INLINE_CODE` span of a line without a double backtick."

- "White space" in 1b must be defined as `str.isspace()`, as `runmap.py:449` does. ASCII-only would let `\x85` and `\x1c` count as plain.

**M8. The edit to `tests/test_k5_round11.py:136` does not do what the ticket says.**
- `allowed` there is `{gate.py, channel.py, slack_channel.py}`. Adding `defang_domains` to the name set still lets `slack_channel.py` call it, so "only `channel.py` may call it" is false.
- Text to add: "add a second loop: a call of `defang_domains` anywhere but `approvals/channel.py` is listed as bad".

**M9. The three open decisions are still open.**
- A builder cannot start 1b and 1c (decision 1) or 1d (decision 3) until the lead writes the answers into the ticket body.

## Minors

**Citations**
- `agent_loop.py:269-284`: the statement is in lines 280-290. It says the real values are for "the executor and the card command", not only the executor.
- `requests.py:35`: the phrase is on line 34.
- `channel.py` "docstring 19-26": the docstring is 19-21 and the sentence to rewrite is a comment on line 25. Line 21, "then ONE redaction, last", also needs rewording.
- N8 is listed under "pass on main too", but it cannot pass on main because `redact_for_people` does not exist there.

**Secret scan**
- The rule (`tools/scan_repo.py:33`) fires only on `password`, an optional quote, `=` or `:`, a quote, then 8 or more characters with no white space or quote, then the closing quote. It is case-insensitive and also fires on `DB_PASSWORD="…"`.
- It does not fire on `"correct horse battery staple"`. It does fire on `hunter2secretXYZ`, the `\t` literal and `ab12;cd34,ef56&gh78`.
- `tests/test_k1b_redaction_layers.py` is already exempt (`tools/scan_allowlist.txt:3`).
- Text to add: "in new files write `PW_KEY = 'pass' + 'word'` and build dicts with it; do not add to `scan_allowlist.txt`; keep such literals out of docstrings in `src/`".
- `AKIAIOSFODNN7EXAMPLE` is allowed by this scan (`scan_repo.py:96`); building it from two parts matches existing tests.

**CI step**
- Write it out:

  > "Job `check`, directly after line 94: `- name: Q8b masking mutants (each reverted guard must be killed by its named test) (blocks)` / `run: python tests/q8b_mutants.py`."

- The golden file of `tests/test_ci_gitleaks_scope.py` covers the security job's steps only, so no regeneration is needed.
- Consider a cheap "old text still present" test like `tests/test_migration_numbers_guards.py:544`, because the F1-F4 rebase can break `old` strings.

**Other**
- CHANGELOG: `## Unreleased` has `### Upgrade steps` (line 5), `### Added` (233) and `### Changed` (277), with no "Fixed" heading. Say which heading each bullet goes under, and whether the approver-visible change needs an Upgrade steps entry.
- `slack_channel.py`: the ticket writes `channel.redact_for_people(...)` and also "line 19 imports it". Pick `from …channel import clean, redact_for_people` and call `redact_for_people(withheld, seeded)`.
- State the type of `_VALUE_BREAK` (`frozenset(';&,"\'')`).
- The guard "plants nothing in the map" cannot read the map, because `redact_bundle` drops it. Say: "assert the returned Counter is empty and `svc` stays readable in a second record".
- `tests/test_k5_producers.py:147` `REDACTORS` does not list `redact_for_people`. Decide whether to add it.
- Gates say Postgres 16; CI uses 17.10.
- `clean(clean(x)) == clean(x)` is listed as passing on main with no run shown.

## Numbered steps for the new `clean()` (to paste into Behaviour 2)

1. `text = text.replace("\x00", "")`.
2. `mapping = _seeded(text)`.
3. `out = redact_for_people(text, mapping)`, which is:
   - 3a. `runmap.redact_text(text, mapping, neutralise=_neutralise)`, where `_neutralise(t) = withhold_commands(sanitise_text(t, defang=False))` runs inside `redact_text` on the text and on each decoded view before the patterns.
   - 3b. `defang_domains(...)` on what 3a returned.
4. `joined = _TAGS.sub("", text)`; if `joined == text`, return `out`.
5. `joined_map = _seeded(joined)`; `alt = redact_for_people(joined, joined_map)`.
6. Return `alt` if `_assignment_originals(joined_map) - _assignment_originals(mapping)` is not empty (plus the M5 rule), else `out`.
7. Nothing runs after step 6.

## Forbidden files

- No edit of `runmap.py` or `tools.py` is needed.
- B1 is the one place where the stated behaviour cannot be reached without changing `redact.py` or the design.
- The `_VALUE_BREAK` test reads the private `runmap._VALUE_END` (line 421), which the F1-F4 builder may rename. This is a merge-order coupling to note beside the `gate.py` merge risk.

## Checked and correct

- All `gate.py` line numbers: 112, 177, 229-238, 241, 264, 267, 272, 308, 312, 327, 328, 332, 339, 344, 350.
- `k1b/redaction.py`: 86, 103-117, 128, 143-144, 188.
- `slack_channel.py`: 19, 74-81, 197.
- `producers.py`: 38, 44-51.
- `runmap.py`: 31, 517, 533-535.
- `ci.yml`: 94.
- `cards.py:59`, and `channel.py` 29, 36, 37, 47-48, 104, 111.
- No test monkeypatches `_neutralise`, `_clean_line`, `_clean_prose` or `_defang_outside_code`.
- `tests/test_k5_round9.py:204` keys on the row name, which does not change.

## Not checked

- Nothing was executed: no test, prototype, redactor call or mutant.
- The author's scripts, logs and prototype under `/home/user/build/q8b-author/`.
- Whether the tests tree at `EV-P89-db0d9eb` is identical to main.
- `reviews/Q8/redaction-sweep.md`.
- `guard/redact.py` outside lines 476-615, including pattern order.
- The `handover/` start-of-session files and `.claude/rules/README.md`.
- Whether gitleaks, Semgrep `p/secrets` or Trivy flag the new test strings.
- Docs that describe card text.
- `cards.render_shadow` and the Slack fake transport.
- The CWE titles and the test counts (487, 1,469, 10,193).
