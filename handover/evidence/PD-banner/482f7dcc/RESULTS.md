# PD part 6 banner, evidence on head 482f7dcc (EVIDENCE RUNNER, records only)

## Not run / deviations (first)
- NOT RUN YET: item 1 full pytest, item 2 stage_mutants (expect 37), item 3 banner_mutants (expect 98 of 98). They are queued behind other agents' runs in heavy.sh (all 3 slots were busy for the whole time I waited; my waiter pid 5188). Chain script /home/user/build/ER-pdbanner-b3-run.sh then ER-pdbanner-b3-mut.sh (mutants wait for pytest, so no file is rewritten during the pytest run). Results will appear as full-pytest.rc/.log, stage_mutants.rc/.log, banner_mutants.rc/.log in /home/user/build/evidence-raw/pdbanner-482f7dcc/. The timing-harness rerun rule was not reached.
- `uv sync --locked --no-build` fails for the editable project (no binary distribution); I used `uv sync --locked --all-extras --group test` (rc 0).
- The brief says `banner_for`; the function in the head is `banner_from_config`; probes use that.
- Python 3.13.18. Own Postgres 16.15 UTF8, PGHOST=127.0.0.1 PGPORT=56733 (server and tests; HADAVIN_TEST_PG_DSN set). Left running for the queued pytest.
- Fail-before ran only 4 changed test files (test_demo_only_guard_ci.py equals the round 2 file).

## Table
| item | command | exit | last line |
|---|---|---|---|
| diff list | git diff --name-only origin/main...HEAD | 0 | 13 files (raw: diff-names.txt) |
| ruff check | src tests demos tools | 0 | All checks passed! |
| ruff format --check | same | 0 | 325 files already formatted |
| bandit -ll | bandit -q -r src demos tools -ll | 0 | only nosec B102 warnings in tools.py |
| scan_repo.py | | 0 | no output |
| demo_only_guard.py | | 0 | no output |
| gitleaks origin/main..HEAD | | 0 | no leaks found |
| fail-before (17d7ec3c old src + new tests) | pytest of 4 files, --continue-on-collection-errors | 1 | 3 failed, 64 passed, 1 collection error |
| full pytest / stage_mutants / banner_mutants | heavy.sh | NOT RUN | queued |

Fail-before detail: test_mode_banner.py fails at collection (mode_banner has no EXTERNAL_SYSTEMS). Failed in test_demo_only_guard.py: ..listed_phrase_is_matched_in_its_own_case_and_not_beside_a_dash, ..text_file_renamed_to_a_binary_ending_is_read_but_a_real_binary_is_skipped, ..submodule_under_a_product_root_is_a_hit_and_one_outside_is_not. The other 64 pass on old code (lists in fail-before-passed.txt; entries named test_needs_folder there are inner captured pytest output, not outer tests).

## Probes
- 6a (probe_a.log): 17 cases, 0 violations. Bare hosts without a scheme ("127.0.0.1", "::1", "[::1]:80", "::ffff:127.0.0.1"), "", None, 5, "localhost.example.test", userinfo urls all give tone real, listing external-systems. With a scheme, http://127.0.0.1, [::1], localhost, [::ffff:127.0.0.1] give demo (made-up). Egress public or public+loopback: real; loopback only: demo. Unreadable or bad-settings source: real; loopback k8s source: demo.
- 6b (probe_b.log): 8 trees, each with head guard+toml. Submodule under src: exit 1 submodule-in-product-root. Submodule outside roots: exit 0. Text file named .png with folder name: exit 1. Real PNG header with NUL: exit 0. DEMO_ONLY-x, x-DEMO_ONLY, lowercase variants: exit 1. Control tree: exit 0. Output is path:line:rule only, no matched text.
- 6c (probe_c.log): 8 odd objects under node, HADAVIN_REQUIRE_NODE=1, all rc 0, htmlWrites empty, no throw. Script tags in text/standins painted as plain text; null, array, {}, missing fields, wrong tone/mode combos, string/object lists paint the UNCONFIRMED banner.

Raw logs: /home/user/build/evidence-raw/pdbanner-482f7dcc/

## Update after report: full pytest finished
full pytest exit 0; last line: 10640 passed, 1 skipped, 28 deselected in 264.52s (0:04:24)
stage_mutants and banner_mutants still pending at this write (see raw logs).

Items 2 and 3 (stage_mutants, banner_mutants) were not run to the end because head 482f7dcc was superseded (round 3 found a Blocker); this is not a failure. The stage_mutants run was stopped part-way and the worktree restored with git checkout (status clean). Postgres and the chain were stopped and removed.
