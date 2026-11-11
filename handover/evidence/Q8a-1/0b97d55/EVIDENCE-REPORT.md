<!-- full hand-back report of sub-agent a55ad3b3, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

EVIDENCE Q8a-1 head 0b97d55a: no failures in steps 1-4 and 6. Step 5: the sibling branch's tests/test_lockin_guard.py gives 20 failed / 138 passed against this head, and the identical 20 fail against a clean origin/main (no new ones from the head). The merge-tree check against the sibling exits 1 with one conflict, CHANGELOG.md.

NOT RUN / FLAGGED
- The 28 `perf` tests are deselected by the CI marker (`-m "not live and not perf"`). I ran them in CI's own second step: 28 passed.
- No live Vault or network service was contacted. HADAVIN_TEST_VAULT_ADDR was not set. The only skip in the full run is tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[bedrock] (Stubber refuses a malformed Converse shape).
- The known flaky timing test did not fail, so no reruns were needed.
- Evidence-file slip: my first full-junit-summary.txt listed every passed test name. Some test names carry made-up secret-shaped strings, and gitleaks flagged 7 findings in that file. I replaced it with counts and the one skip. The rescan is clean.
- The stage_mutants overlay was not run on the old head (not asked).

COUNTS AND EXIT CODES
1. Full suite via heavy.sh, `-m "not live and not perf"`, `-p no:cacheprovider --junitxml -rfEs`: exit 0, 288 s, 10729 tests = 10728 passed, 0 failed, 0 errors, 1 skipped (XML counts). Own Postgres 16.15 on port 56192. Slot got 3 min after queueing. `-m perf` step: exit 0, 28 passed, 57 s.
   The two positive pilot tests ran non-skipped and passed: test_k3_pilot_app_has_no_executor and test_the_app_deletes_evidence_only_through_the_purge_identity.
2. ruff check exit 0. ruff format --check exit 0 (323 files formatted). bandit -ll -r src tools exit 0 (no issues; Low 12, Medium 0, High 0). scan_repo.py exit 0. stage_mutants.py via heavy.sh (clean separate worktree, same head) exit 0, 68 s: "71 of 71 good; problems: []", all KILLED by their named tests. Suppression grep on `git diff origin/main...0b97d55a`: 0 lines.
3. Fail-before on fcd77a68, source untouched, with only the head's six changed test files overlaid (stage_mutants.py, test_k3_pilot_env, test_k5_round8_postgres, test_k5_round9b, test_q8a_live_overrides, test_stage_names), with the database: 86 failed / 290 passed, 0 collection errors (the one ImportError happens inside a test). Groups by first assertion line:
   - 48 `DID NOT RAISE ConfigError`
   - 28 old timeout message "between 0 (not included) and 3600" vs "between 0.001 and 3600"
   - 4 `TickContext.__init__() missing 'now'`
   - 2 "clock was asked although a time was given"
   - 1 ImportError `executor_timeout_ok`
   - 1 demo accepted timeout_s=0
   - 1 a live tick step took a handed time
   - 1 a live tick ran without a built-in step
4. Probes on the head (verbatim in probes-a-c.txt, probes-d.txt, probes-e.txt):
   (a) TickContext(app, time): demo accepts; pilot and prod refuse with "now= is for tests; it is refused in pilot and prod". TickContext(app) takes the app's clock everywhere. `ctx.now = ...` raises FrozenInstanceError. dataclasses.replace with a time is refused in pilot and prod. `object.__setattr__(ctx, 'now', ...)` still changes the time on all stages (recorded as a fact).
       Stand-in context on pilot and prod: sweep, stuck and purge_evidence are refused. reconcile, checkpoint and reprobe_sources are accepted. No purge call reached the store and no planted row was deleted. A stand-in carrying the app's own clock time is refused the same way for the three steps that read the time.
   (b) run_tick steps= on pilot and prod: every non-None shape is refused with "steps= is for tests; it is refused in pilot and prod", including [], (), '', 0, False, a generator and tick.STEPS. steps=None returns 0. In demo, steps=0 and steps=False raise TypeError (not iterable), and the other shapes return 0. now= (alone or with steps) is refused on pilot and prod and accepted in demo.
       With STEPS patched: on pilot and prod each of the six built-in steps removed gives "a built-in tick step is missing: <name>" and nothing runs. An appended step runs after the six. A reordered STEPS, or purge_evidence replaced by a no-op with the same name, is accepted and returns 0.
   (c) Store methods called directly on pilot and prod apps with a time 500 days ahead: purge_tool_calls and purge_redaction_maps each deleted all 3 planted rows (no refusal). Approvals.sweep(at=) and resend_unsent(at=) ran without exception and returned [] (no approvals existed).
   (d) Timeout, keyword vs config route: identical outcome on both. Refused: 0, 0.0, -1, True, False, 1e-9, 5e-324, 0.0009, 3600.0000001, 3601, 10**400, inf, nan, '5', [5], Fraction/'5/2' text. Accepted: 0.001, 0.5, 3600, 3600.0. Differences: Decimal('2.5') keyword is refused, but the config route cannot carry a Decimal (YAML 2.5 is a float) and accepted it as 2.5; int 3600 stays an int via the keyword and becomes 3600.0 via config. The pilot keyword is refused with "timeout_s= is for tests; it is refused in pilot and prod".
   (e) 8 pilot/prod builds (vault secrets and vault_transit signer, auth token written and omitted), both Vault variables set to made-up values, proxies at 127.0.0.1:9: all 8 refused with "environment <stage>: refused: <capability>: <kind> auth token (the default; set auth: kubernetes (recommended) or auth: approle)". Socket recorder: 0 connects and 0 name lookups during the builds. Recorder self-check and an approle control build each logged connect ('127.0.0.1', 9), so the recorder works. The made-up values appear in no output (0 hits).
5. merge-tree: exit 1, conflict in CHANGELOG.md only; defaults.py and tick.py auto-merged. Sibling lock-in guard test (tip 5f94f598) against the head's source: 20 failed / 138 passed. The identical 20 fail against a clean origin/main. Problem lines reported: approvals.gate '_AWS_READ_PREFIXES' and '_SLACK' (:102); approvals.receiver 'handle_slack_action' and '/slack/actions' (:18); backends.table 'GcsRetentionLockSettings', 'OpenAICompatSettings', 'gcs_retention_lock'; config bare 'slack'; guard.producers 'guard/bedrock_guardrail.py'; llm.openai_compat model-id regex, 'OpenAICompatLLM', 'openai_compat'; store.postgres 'auth_aws'; tools '.metadata.google.internal' and 'metadata.google.internal'.
6. gitleaks 8.30.1: git scan of origin/main..0b97d55a exit 0, 4 commits, no leaks. Dir scan of the evidence folder exit 0, no leaks (after the replacement above).

CLEANUP: Postgres stopped, my five temp worktrees, two venvs and pgdata removed, no commits or pushes. The remaining heavy.sh processes belong to other agents and were left alone.

FILES
Evidence folder /home/user/hadavin-sdk/handover/evidence/Q8a-1/0b97d55/: RESULTS.md, full-junit-summary.txt, full-meta.txt, fb-fails.txt, fb-groups.txt, probes-a-c.txt, probes-d.txt, probes-e.txt, sockrec-e.log, mutants.log, mutants-meta.txt, merge-tree.txt, lockin-sibling-failed.txt, lockin-sibling-problem-lines.txt, lockin-sibling-summary.txt, bandit-summary.txt, suppressions.txt, gitleaks-git.log, gitleaks-dir.log.
Raw logs: /home/user/build/evidence-raw/Q8a1-0b97d55/. Probe scripts: /home/user/build/ev-q8a1r4-scripts/. Checkpoint note: /home/user/build/EV-Q8a1-r4-checkpoint.md. Model: Sonnet 5.5.
