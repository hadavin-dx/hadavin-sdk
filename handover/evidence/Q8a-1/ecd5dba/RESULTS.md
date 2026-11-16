# EVIDENCE Q8a-1, head ecd5dba1cd30c39994c4422a2edd90e97d7d7a9b (previous reviewed head 0b97d55a; base origin/main)
Runner: EVIDENCE RUNNER (records only, no judging). Date 2026-11-11 (UTC). Raw logs: /home/user/build/evidence-raw/Q8a1-ecd5dba/. Previous evidence: handover/evidence/Q8a-1/0b97d55/RESULTS.md.
Setup: detached worktree /home/user/build/EV-Q8a1-ecd5dba1 at origin/core/q8a-1-live-override-refusals after `git fetch` (head confirmed ecd5dba1cd30c39994c4422a2edd90e97d7d7a9b; 5 commits above origin/main); own venv; own Postgres 16.15 on 127.0.0.1:56293 (trust, UTF8, C.UTF-8, PGHOST/PGPORT/PGUSER set in the server's and the tests' environment, data dir deleted at the end). Every test command ran with the AWS, proxy-URL, GitHub, Google and Vault variables unset (`env -u ...`). The builder's worktree B-Q8a1 was not touched.

## Failed and not-run items first
- PERF STEP FAILED in the CI-style run: `-m perf` exit 1, 27 passed, 1 failed: tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in ("a quadratic function must be flagged", assert False). This is the known timing test. Re-run alone (3 runs at the head, 3 runs on the previous head's source 0b97d55a, plus one earlier alone run): head: fail, pass, pass, and one more alone run fail (so 2 failed, 2 passed in 4 alone runs); 0b97d55a source: fail, pass, fail. It fails on the old source too and the diff touches nothing of it (diff files listed in section 4), but I did NOT get a clean exit-0 perf step at this head. Not judged; the reviewer decides. Files: perf-failed-line.txt, perf-rerun-alone.log, perf-rerun-2.log.
- Full suite (non-perf): 0 failed, 0 errors, 1 skip (reason below). Not run: 28 tests marked `perf` are deselected in step 1 and run in step 2 (above). I did not run the `vault` contract suite (HADAVIN_TEST_VAULT_ADDR not set; no live service contacted). I did not re-run the vault/socket probe (e) of the previous round (not asked this round).
- Not run on the old source: stage_mutants.py (it is a script, not a pytest file; the fail-before counts below are for the two pytest files only).
- Probe f5 `environment: <secret-shaped value>` returned "duplicate key 'environment'" because the demo config already has that key; so that one row does not test the value echo for that field (the other four f5 rows do).
- Merge check with the sibling: exit 1, one conflict file (section 6).

## 1. Head
`git rev-parse HEAD` in the worktree -> ecd5dba1cd30c39994c4422a2edd90e97d7d7a9b.

## 2. Full suite (once, via /home/user/build/heavy.sh)
- `env -u ... uv run --all-extras --group test pytest -q -p no:cacheprovider -m "not live and not perf" --junitxml=... -rfEs` -> exit 0, 265.2 s. Counts from the XML: tests 10754, failures 0, errors 0, skipped 1; pytest line "10753 passed, 1 skipped, 28 deselected". Slot got 16:51:42Z, load 4.72 at slot.
- The one skip: tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[bedrock] ("Stubber refuses a malformed Converse shape before the kind sees it").
- Same slot, `-m perf` (CI's second step) -> exit 1, 27 passed, 1 failed (see first section), 54 s.
- Positive pilot tests, non-skipped, with the database: test_k3_pilot_env::test_k3_pilot_app_has_no_executor PASSED; test_k5_round8_postgres::test_the_app_deletes_evidence_only_through_the_purge_identity PASSED; test_q8a_live_overrides::test_a_live_build_with_no_test_keyword_is_not_refused PASSED for all 7 values (pilot, prod, staging, Demo, "demo ", "", None).

## 3. Lint, format, bandit, repo scan, mutants, suppressions, gitleaks
| Command | Exit | Result |
|---|---|---|
| `uv run --all-extras --group test ruff check` | 0 | All checks passed! |
| `ruff format --check` | 0 | 323 files already formatted |
| `uv run --with bandit bandit -ll -r src tools` | 0 | No issues identified; Low 12 (below the -ll level), Medium 0, High 0; 3 potential issues skipped by existing `nosec BXXX` |
| `python tools/scan_repo.py` | 0 | no output besides the uv warning |
| `python tests/stage_mutants.py` (clean worktree EV-Q8a1-ecd5dba-mut, same head, via heavy.sh, 71 s) | 0 | "75 of 75 good; problems: []" (75 lines, each KILLED with a named test) |
| `git diff origin/main...HEAD \| grep -nE '^\+.*(noqa\|nosec\|type: ignore\|pragma: no cover\|mark\.skip\|xfail)'` | 1 (no match) | 0 lines |
| `gitleaks git --redact --exit-code 0 --log-opts=origin/main..HEAD` (8.30.1) | 0 | 5 commits scanned, no leaks found |

## 4. Fail-before (head's changed test files over the source of 0b97d55a)
Worktree /home/user/build/EV-Q8a1-ecd5dba-fb at 0b97d55a, source untouched; overlaid from ecd5dba1 ONLY the files of `git diff --name-only 0b97d55a ecd5dba1 -- tests`: tests/stage_mutants.py, tests/test_q8a_live_overrides.py, tests/test_stage_names.py. Source files changed between the heads: app.py, config.py, runtime/tick.py (and CHANGELOG.md). Module path checked to be the old worktree's src.
`pytest -q -p no:cacheprovider -rfEs tests/test_q8a_live_overrides.py tests/test_stage_names.py` -> exit 1: 27 failed, 299 passed, 0 collection errors. Groups (fb-groups.txt):
- 21 test_a_step_refuses_an_object_that_says_it_is_a_tick_context_outside_demo (Failed: DID NOT RAISE ConfigError)
- 2 test_run_tick_refuses_a_step_name_used_twice_outside_demo (DID NOT RAISE ConfigError)
- 1 test_a_tick_context_cannot_be_subclassed (DID NOT RAISE TypeError)
- 1 test_a_config_error_never_shows_the_value_that_was_refused (the text held `input_value`)
- 1 test_stage_names::test_pilot_and_prod_refuse_a_tick_whose_step_list_lacks_a_built_in_step
- 1 test_stage_names::test_pilot_and_prod_refuse_a_time_or_a_step_list_handed_to_the_tick

## 5. Hostile probes on the head (made-up values; raw output only; scripts in /home/user/build/ev-q8a1c-scripts/)
Files: probes_f.txt (new this round), probes_a_c.txt and probes_d.txt (the earlier probes re-run on this head). Facts as printed:
- f1 `Mock(spec=TickContext)` and an object with a lying `__class__` (isinstance says True, `type(ctx) is TickContext` False), time today+500d, six step functions: pilot and prod: sweep, stuck, purge_evidence -> ConfigError "now= is for tests; it is refused in pilot and prod"; reconcile, checkpoint, reprobe_sources -> accepted (no exception; they take no time from the context). Purge calls reaching the store on pilot/prod: none; planted rows intact. Demo: all six accepted; purge_evidence deleted all planted rows.
- f2 subclass attempts (`class X(TickContext)`, frozen dataclass subclass, `types.new_class`) -> TypeError "TickContext cannot be subclassed: a subclass could hand a made-up time to a tick step".
- f3 `object.__setattr__(ctx, "now", today+500d)` on a real context, pilot and prod: all six steps accepted; purge_evidence made 4 purge calls and deleted every planted row (tool calls and maps). A context built with `TickContext.__new__` plus `object.__setattr__` also reaches the purge on pilot and prod and deleted all rows. (A fact; the code comment lists these as not covered.)
- f4 duplicate step names via patched `tick.STEPS`: demo: accepted, returns 0 (a second no-op "sweep" appended; a failing first sweep followed by a no-op sweep: one error line printed, tick state row exists). Pilot and prod: every duplicate shape (second sweep, second purge_evidence, failing sweep + no-op sweep, two custom "dup", three sweeps) -> ConfigError "a tick step name is used twice: <name>", nothing ran. `steps=[dup, dup]`: demo returns 0; pilot/prod ConfigError "steps= is for tests ...". Reordered STEPS (reversed) and a same-name no-op purge_evidence: accepted on demo, pilot and prod, return 0 (the no-op: planted rows intact).
- f5 config error text with a made-up secret-shaped value (built from parts) in executor_timeout_s (plain and quoted), together with a second bad field (retention), and in an unknown key: 4 rows, "secret value echoed: False"; texts are `N validation error(s) for Config / <field> / <message> [type=...]` without `input_value`. One row (environment key) hit the duplicate-key error, see first section.
- Timeouts, keyword (demo build `timeout_s=`) and config (`executor_timeout_s`) routes, same outcome: refused for 0.0009, 3600.0000001 (3600.1 class), 3601, nan, inf, True, 0, 0.0, -1, False, 1e-9, '5', [5], 10**400; accepted for 0.001, 0.5, 3600, 3600.0. Message: "timeout_s= must be an int or float between 0.001 and 3600" (keyword) and the same sentence inside the value-free pydantic text (config). int 3600 stays int by keyword, becomes 3600.0 by config. Decimal('2.5') by keyword refused (config route cannot carry a Decimal). The value 3600.1 itself was not a row; 3601 and 3600.0000001 were.
- c Pilot and prod app (MemoryStore, separate purge store): direct `store.purge_tool_calls(today+500d, keep_run_ids=frozenset())` returned 3 and deleted all three planted tool calls; `purge_redaction_maps(today+500d, keep_run_ids=frozenset(), keep_open=False)` returned 3 and deleted all three maps; no refusal on either. `app.approvals.sweep(at=today+500d)` and `resend_unsent(at=today+500d)` no exception, returned [] (no approvals existed).

## 6. Merge check with the sibling branch core/q8a-2-neutral-callback-and-guard (tip f6c2a3d9)
`git merge-tree --write-tree --name-only origin/core/q8a-2-neutral-callback-and-guard ecd5dba1` -> exit 1; conflicted file: CHANGELOG.md only (content conflict). src/hadavin_sdk/defaults.py and src/hadavin_sdk/runtime/tick.py auto-merged. Note: the sibling's tip is f6c2a3d9 now (the earlier round recorded 5f94f598), and I did not re-run the sibling's lock-in guard test this round (not asked).
