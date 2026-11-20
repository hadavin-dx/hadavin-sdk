# B review 5: E5b fixes (commit 21e2de4b8 code, 0387ad4d3 docs) against hostile review 1 Major 4, Major 5, Nits 11 and 15

Reviewer: fresh, read-only on source. Branch cloud/core-b at 012299c50. Result: **CLEAN** (0 Blocker, 0 Major, 0 Medium, 5 Minor). Major 5 is closed for the message but one part of the reviewer's smallest fix (the audit outcome event) was not built; see m1.

## Run
`HADAVIN_TEST_PG_DSN=... uv run --all-extras --group test pytest -q -p no:cacheprovider tests/test_step_b_e5b_reset_ref.py tests/test_cuj.py tests/test_stop_state_unit.py`: 63 passed, 10 s, no workers.
tests/test_stop_state_roles.py (needs PostgreSQL, not in the requested run) was read, not run; its one adjusted assertion (still ON) and its reset-ref cases (lines 833-884, 1670-1690) are consistent with the new code by reading (the b4 test still refuses by name before any `make`; line 879 holds no `pg-dsn`, so `_same_login` reads False and the database refusal is still what the test sees).

## Old-code check (scratch worktree /tmp/core-b-scratch-B5/old at 21e2de4b8~1 = 90e896789, new test file copied in with `collides` shimmed; worktree removed afterwards)
7 of 13 fail on the old code, 6 pass. Both tests the builder never ran against old code DO fail there, for the right reason:
- `..._stops_the_start[_llm_key]`: "DID NOT RAISE ConfigError" (the backend names were not in the old set; `_channel` fails the same way).
- `test_a_release_ref_holding_the_runtime_login_under_another_name_is_refused`: "Failed: built a store" (the old code went on to build the store on a runtime DSN).
- also fail on old code, as intended: the two still-ON tests, the lost-connection test, the reset same-login test.
- pass on old code (already covered by the earlier `canonical_secret_name` check): `_restored`, `_tool`, `_sender`, executor, unrelated ref, `collides` unit. Not a defect; they guard against regression only.

## Q1: does `runtime_names` hold EVERY secret the runtime resolves? Yes.
Grepped every `*_secret_name` / `secret_names` / `*_ref` in src (config.py, backends/table.py, platform_secrets.py, tools.py, actions/contract.py, llm/*, audit/signer.py, approvals/slack_channel.py, store/postgres.py, backends/builtin.py, app.py). `runtime_names` (app.py:195-200) = `extra_secret_names` (tool `secret_names`, tool `ca_secret_name`, source `token_secret_name`, `evidence.restored_hash_key_secret_name`) + `executor_names` (http executor `secret_name`) + `secret_names()` of every `b.entries()` settings (config.py:126: every capability plus every detector; so store `dsn_secret_name`, `purge_dsn_secret_name`, `sslrootcert_secret_name`, llm/judge/anchor/signer/channel/secrets-kind fields) + all sender `secret_names`. The only secret-bearing fields that do not end in `_secret_name` are the two refs themselves (by design; they are what is being kept out). Nothing is left out. The fold is `canonical_secret_name` on both sides (secret_name.py:19-24), so it is the same fold the old checks used. The error text names no secret (app.py:206-209).

## Q2: can `_same_login` leak a value? No.
cli.py:462-468. The values live in two locals; the compare is a plain `==`; the result is a bool. Both refusals (cli.py:251-257, 541-548) print fixed text and no name or value; the test asserts the DSN is not in stderr. Any provider error is swallowed by `except Exception` and nothing is logged, chained or put in argv or the environment, so there is no error text, `__context__` or process-list path. Not constant-time, which does not matter for a local compare in the operator's own process.

## Q3: does the still-ON message leak the setter's name where it should not? No new exposure.
cli.py:635-647 prints `state.by!r` (repr, so control characters are escaped) and `state.ts` to the operator running reset, who already had `by` printed in the old message and who holds the reset login. `KillSwitch.ts` always has a value (models.py:259), so `state.ts.isoformat()` cannot raise when `by` is set. It goes to stderr only, not to an audit row or a log.

## Q4: did the four adjusted tests keep what they protected? Yes; none weakened.
- tests/test_cuj.py:295-297: `"Nothing was changed" in err` is now asserted `is (action == "stop")`: stronger (stop keeps the claim, reset must not make it); the exit 4, "NOT" and "unreachable" asserts stay.
- tests/test_stop_state_unit.py:226: swaps the "Nothing was changed." sentence for "The connection was lost"; exit 4, "OFF" absent and the two audit kinds stay. The negative claim is now in the new file (test_a_connection_lost...).
- tests/test_stop_state_unit.py:256-257: "Run limits reset again" replaced by `"reset again" not in err` plus "Check the stop reason"; exit 2, "OFF" absent, audit kinds and read count stay.
- tests/test_stop_state_unit.py:286-297: the fake now gives the reset ref a different value (needed, or the new same-login refusal would fire first) and the "Nothing was changed" assert is kept; that path is the pre-write StoreUnavailable, where the claim is true.
- tests/test_stop_state_roles.py:1613-1614: "(by 'ops:during')" becomes "(set by 'ops:during' at "; "reset again" absent; "written, not failed" kinds assert stays.

## Findings (all Minor)

**m1. Major 5 closed in text only; the audit outcome event and exit code were not built.** cli.py:635-650. Hostile review 1 asked for "one outcome event limits.reset_incomplete" and noted "no audit row says it stayed ON" and "exit 2 like refused". The tests pin `audit.kinds() == ["limits.reset"]` (unit:259) and the exit stays 2. The operator no longer steers into a blind second reset, which was the harm; but the audit log still shows only `limits.reset`, with no row that the switch stayed ON. Decide: accept and say so in the ticket addendum, or add the event (the reset login may not write checkpoints but does write `limits.reset*` rows, so it can).

**m2. `_same_login` widens what each operator process reads, and fails open.** cli.py:462-468, 251, 541. The reset command now reads the runtime DSN secret; release-expired now reads the runtime, reset and purge DSN secrets, if the operator's provider lets it. The runbook says the reset secret lives on the operator's machine only; the reverse (an operator identity that can read the runtime secret) was not a precondition before. Where the provider denies it, the read raises, `_same_login` returns False and the check is skipped (fail-open by design, documented in the docstring); the database still refuses a login without the right, so no stop is cleared wrongly. Suggest one runbook sentence: the check compares values only where the operator's identity can read both.

**m3. Value check is narrower than the name check.** (a) reset compares only against `dsn_secret_name` (cli.py:251), release against runtime, reset and purge: a reset ref that holds the purge DSN, or that equals `release_credential_ref`, passes (the DB refuses a login without the right; in the second case release-expired does refuse). (b) Whole-string compare: the same role in a DSN with another option or host string is "different". Both are defence in depth in front of a database check, hence Minor; the runbook's "the same DSN" wording is accurate.

**m4. Test gaps.** tests/test_step_b_e5b_reset_ref.py: `_tool_ca` (line ~107) and `_executor` (line ~111) are defined and never used in the parametrize list (`_executor` is a no-op); no case for a source `token_secret_name`, a store `purge_dsn_secret_name`, a signer or `sslrootcert` name, or for `release_credential_ref` at build; the `_sender` case is stopped earlier by `check_senders` (platform_secrets.py:78-85, which already holds both refs), so the sender arm of `runtime_names` is not what the test exercises. Dropping the sender arm or the source-token arm would not fail a test. The `_with_ref` helper sets the attribute on the store settings class with `raising=False`, so the build check is tested on a fake store, not a Postgres one; acceptable.

**m5. Docs.** docs/stop-state-runbook.md is accurate against the code (build refusal, still-ON text, exit 4 row, release checked "the same way"). It does not mention m2 (what the operator identity needs to be able to read).

## Verdict
CLEAN: nothing above Minor. m1 is the only one worth a decision before B is called done.
