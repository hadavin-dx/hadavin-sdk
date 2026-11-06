# P5b1 evidence (provider error plumbing), head b6fb1c2, stacked on P5a ea2d254

Placeholders: <repo> = the worktree <build-dir>/P5b1; <model-id> = (none used; no model call was made). No spend, no live call.

## 1. What did NOT happen or is weaker than it sounds (first)
- P4a R3 sub-row BLOCKED: UsageMissing / UnpricedUsage / P4a-P4d reserve methods exist only on core/P4a. Nothing invented; the test skips with that message.
- Postgres rows SKIPPED: no Postgres on this machine.
- Full suite 3.13 and 3.12 were run at af1e0df. The head b6fb1c2 differs by three TEST-ONLY commits (lazy import in tests/test_provider_errors_wire.py; mutant file list and expect fixes in tests/provider_mutants.py; pickle-rebuild fix in tests/test_provider_facts.py). Only the changed files were rerun after that (test_provider_facts.py 50 passed, 1 skipped; mutants M10/M38). Not a full final-head suite.
- The 45 mutants ran at fe15175 (43 good); M10 and M38 were WRONG_REASON there (test-side defects), fixed in b6fb1c2 and killed on rerun at b6fb1c2. The other 43 were not rerun at b6fb1c2 (the delta is two test files not used by them except test_provider_facts for some).
- Slips: the first fail-before run had a collection error (module-level import of a module absent on the base); the first mutant run aborted (a helper file was not in the runner's copy list); my first M10/M38 rerun ran on the wrong commit (a worktree HEAD mix-up); tool-name typo bash instead of Bash twice early on, no effect; a whole-file ruff reformat of a P5a-owned file was reverted by rebuilding from base; row HC-hostile_class-61's canary was too short for P5a's new canary-length test (found after the merge, fixed).
- S301 handling is weaker than a real unpickle: the test calls pickle.dumps and rebuilds from __reduce_ex__; pickle.loads is not called.
- R14: two strict xfails (a DEBUG logger leaks provider text; includes an httpx2 INFO line). R15 T-L ambiguity unresolved.
- The BLE001 decision is the lead's (order 93). Applied as ordered; retry.py:156 needs reviewer judgment.

## 2. Environment and import path
- 3.12: own env <build-dir>/P5b1-uvenv (UV_PROJECT_ENVIRONMENT), Python 3.12.13, ruff 0.17.1. 3.13: <build-dir>/venv313.
- Every run used PYTHONPATH=<repo>/src:. ; hadavin_sdk resolves to <repo>/src/hadavin_sdk/__init__.py (checked on both interpreters).
- Libraries: anthropic 2.1.0, botocore 1.43.122, httpx2 2.16.0.

## 3. Merge of P5a
Merged origin/core/P5a (ea2d254, replaces WIP 1a99a06). Two conflicts, both in P5a-owned test files, resolved as P5a head plus my additions: tests/data/c18a_hostile_corpus.py (P5a side was reformatting only; kept CORPUS_STEP="R1P", _add rid; then ruff-formatted) and tests/test_diagnostic.py (both sides added tests; kept both). Other P5a files auto-merged. P5a-owned test edits that remain: corpus 170 rows / 152 active with scenario rows excluded from diagnose-only tests (test_diagnostic_hostile.py), strict xfails HC-provider_attrs-04/-07 in test_diagnostics_old_writers.py (writers leak the canary today, P5b3 owns them), test_diagnostic_codes.py edits.

## 4. Gates
ruff check .:           All checks passed! | check exit=0
ruff format --check .:  346 files already formatted | format exit=0
bandit -ll -r src tools: exit 0, "No issues identified" (bandit.log)
Full suite 3.13 (af1e0df): 10839 passed, 456 skipped, 85 xfailed in 471.32s (0:07:51) | exit=0
Full suite 3.12 (af1e0df): 10839 passed, 456 skipped, 85 xfailed in 612.59s (0:10:12) | exit=0
Marker filter: not live and not postgres.

## 5. Fail-before (P5a base ea2d254 + the new/changed test files; 0 collection errors)
143 failed, 278 passed, 1 skipped, 1 xfailed, 1 warning in 6.37s
FAILED = FAIL-BEFORE (the new test fails on the old code). PASSED = regression pin (also passes on the base).
Per file (failed / passed): test_provider_errors_wire 71/6 (+1 xfail); test_provider_errors_failbefore 53/14; contracts/test_llm 12/53 (+1 skipped); test_diagnostic 3/27; test_diagnostic_hostile 3/155; test_llm_text_channels 1/18; demo_askdata/test_p5b1_booking 0/5 (all five regression pins: the booking holds on the base).
Per-row names: failbefore_rows.log. Outside the batch: tests/test_never_raise_guards.py and tests/test_provider_facts.py (they import new modules; ImportError on the base by construction).

## 6. Mutants (45, P1m runner, clean worktree, tests/provider_mutants.py)
Each line: verdict, mutant, the killing test. M10/M38 from the rerun at b6fb1c2, the rest from the run at fe15175.
ok  KILLED       M1 the message is built from str(exc) again  [test_r6_500_random_hostile_failures_keep_the_message_grammar]
ok  KILLED       M2 bedrock.facts uses the raw error code, not the closed table  [test_r16_every_modelled_converse_code[ThrottlingException]]
ok  KILLED       M3 the request-id shape check is removed  [test_r5_claude_request_ids['req_AAAAAAAAA]]
ok  KILLED       M4 the request-id check uses match, not fullmatch  [test_r5_claude_request_ids['req_AAAAAAAAA]]
ok  KILLED       M5 clean_status has no range check  [test_r3_a_wrong_type_or_range_becomes_none_and_never_raises[status-0]]
ok  KILLED       M6 safe_facts is bypassed (an adapter exception escapes)  [test_r5_hook_returning_the_wrong_type_or_a_subclass_or_raising_gives_n]
ok  KILLED       M7 retry_count is counted from 0  [test_r1_golden_wire_rows[row1-anthropic]]
ok  KILLED       M8 retryable is always True on a refusal  [test_r1_golden_wire_rows[row1-anthropic]]
ok  KILLED       M9 anthropic.facts measures a str body  [test_r4d_a_str_body_is_never_read_or_measured]
ok  KILLED       M10 pickling drops the attributes  [test_r3_pickle_and_copy_keep_the_attributes[ProviderError]]
ok  KILLED       M11 isinstance(body, dict) instead of the exact type  [test_r5_claude_body_cases[dict-subclass-body-401]]
ok  KILLED       M12 anthropic.facts reads exc.args  [test_r4a_direct_adapter_reads_only_its_allow_list[anthropic]]
ok  KILLED       M13 the constructor stores an unchecked error_type  [test_r3_a_wrong_type_or_range_becomes_none_and_never_raises[error_type]
ok  KILLED       M14 transient reads the status through clean_status  [test_r2_claude_library_777_is_retried_three_times]
ok  KILLED       M15 a failed HTTPError is not closed  [test_r8a_refused_at_once_closes_the_connection_without_a_read]
ok  KILLED       M16 the detail text hook is reintroduced  [test_r9_detail_hook_is_removed_everywhere]
ok  KILLED       M17 describe prints the class __name__  [test_r16_every_modelled_converse_code[ThrottlingException]]
ok  KILLED       M18 the Google refresh error becomes other  [test_r1_row10_vertex_refresh_error_is_authentication]
ok  KILLED       M19 bedrock.facts accepts any request-id shape  [test_r19_each_kind_accepts_only_its_own_request_id_shape]
ok  KILLED       M20 the guard around the wait computation is removed  [test_r10_a_wait_computation_that_raises_is_a_decision_failure[headers.]
ok  KILLED       M21 retry_count stays 1 across a retried refusal  [test_r1_golden_wire_rows[row29-anthropic]]
ok  KILLED       M22 the retry_count bound admits 1001  [test_r3_a_wrong_type_or_range_becomes_none_and_never_raises[retry_coun]
ok  KILLED       M23 the 408 row of the status table is dropped  [test_t_s_status_table_both_directions]
ok  KILLED       M24 the timeout_error row of the Claude table is dropped  [test_t_c_claude_table_both_directions]
ok  KILLED       M25 anthropic accepts a request id without req_  [test_r5_claude_request_ids['ABCDEFGHIJ']]
ok  KILLED       M27 a ProviderError raised in call is rebuilt  [test_r1_row28_a_provider_error_raised_in_call_passes_through_unchanged]
ok  KILLED       M28 safe_facts accepts a subclass  [test_r5_hook_returning_the_wrong_type_or_a_subclass_or_raising_gives_n]
ok  KILLED       M29 bedrock.facts accepts any str code of any length  [test_r5_bedrock_code_not_a_short_exact_string_gives_the_status_type[st]
ok  KILLED       M30 the length bound is removed from the Claude type lookup  [test_t_l_a_65_character_key_is_never_looked_up]
ok  KILLED       M31 the close step is not inside try/except  [test_r8c_a_close_that_raises_never_replaces_the_real_error]
ok  KILLED       M32 only the last failed HTTPError is closed  [test_r8b_three_retried_attempts_close_all_three]
ok  KILLED       M33 the connection test comes before the timeout test  [test_r1_stand_in_rows[row9]]
ok  KILLED       M35 the guard around the retry decision is removed  [test_r5_a_decision_that_crashed_is_the_billed_class[status_code-raises]
ok  KILLED       M37 a wait failure is swallowed as wait 0 and the loop goes on  [test_r10_a_wait_computation_that_raises_is_a_decision_failure[headers.]
ok  KILLED       M38 a kind adapter does not end in default_facts  [test_r19_bare_exceptions_give_the_class_based_types[bedrock]]
ok  KILLED       M39 the refusal is raised from the original error  [test_r17_the_traceback_never_prints_the_original_error_text[urlerror-r]
ok  KILLED       M40 default_facts reads the text of the reason  [test_r4a_direct_adapter_reads_only_its_allow_list[default]]
ok  KILLED       M41 a decision failure raises a plain ProviderError  [test_r5_a_decision_that_crashed_is_the_billed_class[status_code-raises]
ok  KILLED       M42 diagnose accepts any str as a request id  [test_provider_attributes_are_read_with_exact_types]
ok  KILLED       M43 the status rule is applied to ProviderExhausted  [test_provider_codes_follow_status_then_type]
ok  KILLED       M44 diagnose drops every provider fact when one fails  [test_provider_attributes_are_read_with_exact_types]
ok  KILLED       M45 the error type decides the code although a valid status is present  [test_provider_codes_follow_status_then_type]
ok  KILLED       M46 a decision failure uses max_attempts instead of the current attempt  [test_r5_attempt_two_hook_failure_is_billed_with_attempt_two]
ok  KILLED       M47 an unlisted Claude type falls through to the status table  [test_r5_claude_body_cases[type-injected-short-code]]
ok  KILLED       M48 the bool() around the retry decision is removed  [test_r5_a_decision_that_crashed_is_the_billed_class[bool-raises-BN1c]]
Notes: M42 mutates the SafeToken.request_id site (the double-guarded sites are equivalent mutants); M48's killer is the decision-crash test.

## 7. BLE001 sites (order 93)
P5b1 BLE001 sites (order 93). 9 sites, all with a same-line "never-raise guard: ..." reason, each calling neverraise.record(Site.<x>)
(a counter by closed site name; no exception text kept). No S110/S112, no per-file ignore, no contextlib.suppress.
Test for every site: tests/test_never_raise_guards.py (one test per file; each also proves KeyboardInterrupt/SystemExit propagate).
Line numbers are at the commit that adds this file; P5a's own sites (about 15 more in diagnostic.py) are P5a's and are untouched.

src/hadavin_sdk/guard/diagnostic.py:235  Site.diag_attrs_unreadable
  why it cannot be narrowed: vars(exc) on a hostile object runs arbitrary property/__getattr__ code that can raise any Exception.
  test: test_diagnostic_guards_catch_record_and_let_base_exceptions_through
src/hadavin_sdk/guard/diagnostic.py:480  Site.diag_provider_class_check
  why: cls.__module__ / __qualname__ on a hostile metaclass can raise any Exception.
  test: test_diagnostic_guards_catch_record_and_let_base_exceptions_through
src/hadavin_sdk/llm/provider_facts.py:86  Site.facts_safe_attr
  why: getattr on a provider error with a hostile property can raise any Exception.
  test: test_provider_facts_guards_catch_record_and_let_base_exceptions_through
src/hadavin_sdk/llm/provider_facts.py:103  Site.facts_adapter_hook
  why: an adapter hook (anthropic/bedrock/default facts) is foreign-shaped code reading foreign objects; any Exception is possible.
  test: test_provider_facts_guards_catch_record_and_let_base_exceptions_through
src/hadavin_sdk/llm/retry.py:122  Site.retry_class_text
  why: class_name_of is declared never-raise; this is the belt-and-braces fallback if that contract is ever broken (tested by replacing it).
  test: test_retry_guards_catch_record_and_let_base_exceptions_through
src/hadavin_sdk/llm/retry.py:138  Site.retry_close_failed_http
  why: HTTPError.close() on a subclass with hostile code can raise any Exception; it must never replace the real provider error.
  test: test_retry_guards_catch_record_and_let_base_exceptions_through
src/hadavin_sdk/llm/retry.py:156  Site.retry_classify   (REVIEWER JUDGMENT NEEDED)
  why: the call is foreign code and can raise anything; every failure must leave as a ProviderError. Every path out of this handler
  raises a ProviderError/ProviderExhausted or retries. A bare "raise"/"from exc" would change the deliberate "from None" (no provider text
  in __cause__). It records every absorbed call failure, so the counter counts failures, not bugs. It is a classifier more than a silent guard.
  test: test_retry_guards_catch_record_and_let_base_exceptions_through
src/hadavin_sdk/llm/retry.py:161  Site.retry_decision
  why: the transient/retryable test is foreign-shaped; a crash is booked as the billed class (the request was sent).
  test: test_retry_guards_catch_record_and_let_base_exceptions_through
src/hadavin_sdk/llm/retry.py:191  Site.retry_wait
  why: retry_after reads a foreign response header; a crash is booked as the billed class (no extra request).
  test: test_retry_guards_catch_record_and_let_base_exceptions_through

REMOVED instead of suppressed: the per-fact try/except blocks in diagnostic._provider_facts and _bounded_attr (4 sites). They guarded
only exact-type checks on values of an exact dict, which cannot raise; removing them changed no behaviour.

## 8. Other
- Attempts are counted by request count plus retry_count.
- Corpus mapping of the 8 provider_attrs rows: status 429 = R18(i); status 99 = R18(ii); plain-string error_type = R5/R18(ii); request_id not in a closed shape (underscored name, e-mail) = R10/R18(ii); retryable True = R18(i); retryable "yes" = R3 (dropped).
- The _billed tripwire accommodation: the booking test assigns the text before the return so a raw escape on the base is reported, not hidden.
- The filename of P5a's WIP differed from the ticket; resolved by the merge.
- P5a base lint debt (13 ruff errors / 6 unformatted files at WIP 1a99a06) is gone at P5a head ea2d254; P5b1 adds none.
- R-numbers cited: R1P, R3, R5, R10, R11c, R14, R15, R16, R18; ticket notes BN-3, BN-10, BN-11, BN-12.

## 9. Order 95 results (final head b6fb1c2338cb5168aef196ba962ecbf676c76c82)
Run from a fresh detached worktree at that exact SHA, one heavy.sh job at a time, PYTHONPATH=<worktree>/src:. ; each log header names the HEAD, cwd and command.
- order95_mutants_M10_M38.log: M10 KILLED, M38 KILLED, "2 of 2 good; problems: []", exit=0.
- order95_full313.log (python 3.13, -m "not live and not postgres"): 10839 passed, 456 skipped, 85 xfailed in 471.32s, exit=0. The elapsed time equals the earlier af1e0df run to the hundredth of a second; the start/end timestamps in the log (14:46:19Z to 14:54:12Z) show it was a fresh run, so I take it as coincidence.
- order95_full312.log (python 3.12, P5b1-uvenv): 10839 passed, 456 skipped, 85 xfailed in 619.87s, exit=0.
This closes the earlier caveat that the full suites ran at af1e0df rather than at the final head. Still true: the other 43 mutants were last run at fe15175, not re-run at b6fb1c2 (order 95 asked only for M10/M38). Postgres rows skipped; P4a R3 BLOCKED.
Order 95 item 3: origin/main (c709df3) is not an ancestor of origin/core/P5a, so main was not merged. PR 80 left as a draft. No new commits; nothing pushed.
