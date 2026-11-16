Mon Nov 16 09:01:11 UTC 2026

# Evidence 13: core patches C-01, A-01, G5-wording (raw; EVIDENCE RUNNER, no judgement)

## Setup (commands, versions)
- python3 --version: Python 3.13.18; uv 0.11.32
- Env: AWS_* and ANTHROPIC_BASE_URL were present in the shell; every command run with env -u for AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID, AWS_CA_BUNDLE, ANTHROPIC_BASE_URL. No live model calls, no spend.
- cd /tmp/core-b4p; UV_PROJECT_ENVIRONMENT=/tmp/core-venv uv sync --all-extras --group test --group scan --no-install-project  -> rc=0 (this created /tmp/core-b4p/uv.lock; no src touched)
- Package itself NOT installed; tests run with PYTHONPATH=src and /tmp/core-venv/bin on PATH. Tool versions: pytest 9.1.1, ruff 0.17.1, bandit 1.9.4, moto 5.2.4, pglast 8.7

## Gaps in the scratch trees (affect every pytest run)
- Trees hold only src, tests, pyproject.toml: no demos/, README.md, CHANGELOG.md, docs/, .gitleaks.toml, .git, (uv.lock only in AFTER, from my sync).
- First AFTER pytest run (plain `pytest`): rc=2, 22 collection errors (20x ModuleNotFoundError askdata, 2x FileNotFoundError) all under tests/demo_askdata. Then reran with --ignore=tests/demo_askdata. So tests/demo_askdata was NOT run in any tree.

## 2. AFTER (/tmp/core-b4p)
- pytest -p no:cacheprovider --ignore=tests/demo_askdata -q : rc=1 ; 5 failed, 8580 passed, 62 skipped in 236.44s
  failed: test_k1b_cli::test_report_and_runbook_line_exist (README.md missing); test_k5_fixes4::test_the_changelog_merge_order_names_the_four_prs (CHANGELOG.md missing); test_k5_round11::test_the_gitleaks_header_chain_regex... (.gitleaks.toml missing); test_p7_tick::test_slack_app_manifest_is_least_privilege (docs/slack-app-manifest.yaml missing); test_repo_rules::test_licences_are_proprietary (git ls-files exit 128, no .git)
- ruff check: rc=0 "All checks passed!"
- ruff format --check: rc=0 "265 files already formatted"
- bandit -ll -r src: rc=0; Low 6, Medium 0, High 0 (displayed counts are all severities incl. low; -ll filters to medium+)

## 3. New tests against OLD src (/tmp/core-b4t = BEFORE + 4 test files from AFTER)
- pytest of the 4 files: rc=1; 15 failed, 55 passed in 17.19s
- FAILED (15): test_c01_route_limits: price param x6 (0/0.00/-1 on input and output), test_max_tokens_above_the_ceiling_is_refused, test_max_tokens_at_the_ceiling_loads_and_zero_is_still_refused; test_a01_audit_reconcile: test_the_step_is_in_the_tick_list, test_the_step_drains_the_outbox_and_logs_the_count, test_a_kind_without_reconcile_is_skipped, test_a_failed_outcome_write_logs_type_and_id_but_never_the_body, test_when_the_outbox_table_also_fails_an_error_line_is_logged; test_p7_tick: test_steps_order_and_summary_line_is_not_a_step, test_slack_app_manifest_is_least_privilege (the last one fails for the missing docs file, same as AFTER)
- tests/warden_port/test_gate.py (G5 docstring edit) and the C-01 "fake kind / priced route loads" cases PASS on old src.
- First-failure messages (pytest --tb=short -x per group, first 15 lines):
    === tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model
    F
    =================================== FAILURES ===================================
    _ test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok] _
    tests/test_c01_route_limits.py:28: in test_a_zero_or_negative_price_is_refused_for_a_live_model
        with pytest.raises(ConfigError, match="zero or negative price"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    E   Failed: DID NOT RAISE ConfigError
    =========================== short test summary info ============================
    FAILED tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok]
    !!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
    1 failed in 5.51s
    === tests/test_c01_route_limits.py::test_max_tokens_above_the_ceiling_is_refused
    F
    =================================== FAILURES ===================================
    _________________ test_max_tokens_above_the_ceiling_is_refused _________________
    tests/test_c01_route_limits.py:45: in test_max_tokens_above_the_ceiling_is_refused
        _load(cfg_dir, max_tokens=defaults.MAX_ROUTE_TOKENS + 1)
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^
    E   AttributeError: module 'hadavin_sdk.defaults' has no attribute 'MAX_ROUTE_TOKENS'
    =========================== short test summary info ============================
    FAILED tests/test_c01_route_limits.py::test_max_tokens_above_the_ceiling_is_refused
    !!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
    1 failed in 0.42s
    === tests/test_c01_route_limits.py::test_max_tokens_at_the_ceiling_loads_and_zero_is_still_refused
    F
    =================================== FAILURES ===================================
    ________ test_max_tokens_at_the_ceiling_loads_and_zero_is_still_refused ________
    tests/test_c01_route_limits.py:49: in test_max_tokens_at_the_ceiling_loads_and_zero_is_still_refused
        assert _load(cfg_dir, max_tokens=defaults.MAX_ROUTE_TOKENS).routes["default"].max_tokens == (
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^
    E   AttributeError: module 'hadavin_sdk.defaults' has no attribute 'MAX_ROUTE_TOKENS'
    =========================== short test summary info ============================
    FAILED tests/test_c01_route_limits.py::test_max_tokens_at_the_ceiling_loads_and_zero_is_still_refused
    !!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
    1 failed in 5.13s
    === tests/test_a01_audit_reconcile.py
    F
    =================================== FAILURES ===================================
    ______________________ test_the_step_is_in_the_tick_list _______________________
    tests/test_a01_audit_reconcile.py:31: in test_the_step_is_in_the_tick_list
        assert "audit_reconcile" in [s.name for s in tick.STEPS]
    E   AssertionError: assert 'audit_reconcile' in ['sweep', 'reconcile', 'stuck', 'checkpoint', 'purge_evidence', 'reprobe_sources']
    =========================== short test summary info ============================
    FAILED tests/test_a01_audit_reconcile.py::test_the_step_is_in_the_tick_list
    !!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
    1 failed in 0.08s
    === tests/test_p7_tick.py::test_steps_order_and_summary_line_is_not_a_step
    F
    =================================== FAILURES ===================================
    _______________ test_steps_order_and_summary_line_is_not_a_step ________________
    tests/test_p7_tick.py:82: in test_steps_order_and_summary_line_is_not_a_step
        assert [s.name for s in tick.STEPS] == [
    E   AssertionError: assert ['sweep', 're...robe_sources'] == ['sweep', 're...sources', ...]
    E     
    E     Right contains one more item: 'audit_reconcile'
    E     Use -v to get more diff
    =========================== short test summary info ============================
    FAILED tests/test_p7_tick.py::test_steps_order_and_summary_line_is_not_a_step
    !!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
    1 failed in 0.76s

## 4. Baseline BEFORE (/tmp/core-b4), same flags
- rc=1; 6 failed, 8564 passed, 62 skipped in 244.85s. The 5 failures above plus test_k1b_cli::test_uv_lock_version_matches_the_package (uv.lock absent in BEFORE; present in AFTER only because my uv sync created it).
- Passed count difference 8580 - 8564 = 16; failed difference 5 vs 6. Arithmetic fits 15 new test cases (10 C-01 + 5 A-01) + the uv-lock test now passing; not itemised per test by me.

## 5. Mutation spot checks (/tmp/core-b4m, copy of AFTER; src restored after each, final diff -r vs AFTER: identical)
- Baseline of copy (3 test files): 1 failed (slack manifest, missing file), 55 passed
- (a) price check never fires (<= 0 replaced by < -10**9): test_c01_route_limits 6 failed, 4 passed (all 6 price cases fail)
- (a2) only input price checked: 3 failed (the 3 output-price cases), 7 passed
- (b1) le -> lt on max_tokens ceiling: 1 failed (test_max_tokens_at_the_ceiling_loads_and_zero_is_still_refused), 9 passed
- (b2) ceiling removed (Field(gt=0)): 1 failed (test_max_tokens_above_the_ceiling_is_refused), 9 passed
- (c) audit_reconcile TickStep line removed from STEPS: test_the_step_is_in_the_tick_list and test_steps_order_and_summary_line_is_not_a_step failed (+ the slack manifest one, missing file); the drain/skip/log tests call the function directly and did not fail (43 passed)

## 6. Patch application (fresh copies of BEFORE src+tests+pyproject.toml, git init, no commits)
- git apply --check C-01 alone rc=0; A-01 alone rc=0; G5-wording alone rc=0
- in order (check then apply): C-01 rc=0, A-01 rc=0, G5-wording rc=0
- Result tree vs /tmp/core-b4p: identical (excluding .ruff_cache)
- Diff stat AFTER vs BEFORE (added/removed lines, via diff -ruN): gate.py +4/-1; audit/chain.py +13/-2; audit/local_dir.py +8/-1; config.py +10/-1; defaults.py +1/-0; guard/redact.py +4/-3; runtime/tick.py +10/-1; tests/test_a01_audit_reconcile.py +55 (new); tests/test_c01_route_limits.py +37 (new); tests/test_p7_tick.py +2/-0; tests/warden_port/test_gate.py +1/-1. 11 files.

## Not run / not checked
- tests/demo_askdata (no demos/ dir); the 5 tests that need repo files not in the scratch trees; CI-only steps (CodeQL, SonarCloud, perf split step not separated); no live or cloud tests.
- Raw logs left in /tmp: after-pytest.log, after-pytest2.log, after-ruff.log, after-fmt.log, after-bandit.log, b4t.log, b4t-msgs.log, b4-full.log.
