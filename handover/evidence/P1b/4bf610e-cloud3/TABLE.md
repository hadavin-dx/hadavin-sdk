# A7 evidence, P1b head 4bf610e (cloud3). RAW, no verdict. Runner: EVIDENCE RUNNER, time box 60 min reached.
Setup: copy EV-A7 (cp -r, .git dropped, then a throwaway local `git init` + 1 commit because scan_repo and tests call `git ls-files`; not in hadavin-sdk). venvs: 3.12.3 (unicodedata 15.0.0) and 3.13.18 (15.1.0), `uv sync --locked --all-extras --group test` (without --no-build: editable project needs a build). Postgres 16 shared cluster 127.0.0.1:55400, db a7_ev, HADAVIN_TEST_PG_DSN set. dblink socket /var/run/postgresql not available (ENV).
Changed since 0d843b4 (2 commits: 2034512, 4bf610e), 17 files: CHANGELOG.md, defaults.py, guard/injection.py, guard/runmap.py, guard/textnorm.py, runtime/evidence.py, tests/fixtures/textnorm_manifest.json, tests/test_textnorm_{callers,fixbatch,meta,order137,perf,round1(new),round2(new),scan,siblings}.py, tests/textnorm_mutants.py.

| command | python | inner rc | counts | log |
|---|---|---|---|---|
| ruff check src tests demos tools | 3.13 | 0 | All checks passed | ruff-check.txt |
| ruff format --check src tests demos tools | 3.13 | 0 | 335 files already formatted | ruff-format.txt |
| tools/scan_repo.py | 3.13 | 0 | no output | scan_repo.txt |
| bandit==1.9.4 -q -r src demos tools -ll | 3.13 | 0 | no findings (only nosec warnings) | bandit.txt |
| pytest -m "not live and not perf", group 5 (files in collection order, last 56 files) | 3.13 | 0 | 2262 passed, 5 deselected | pytest313-g5.txt |
| pytest same, group 4 (21 files) | 3.13 | 0 | 2462 passed, 9 deselected | pytest313-g4.txt |

NOT RUN (the shared heavy slots, 3 machine-wide, were held by other agents for the whole box; my jobs waited in the queue and I stopped them at the box end):
- pytest groups 1 (51 files) and 3 (9 files) on 3.13; all 4 groups on 3.12 (groups 1,3,4,5). Group split: /home/user/build/chunks/A7/groups.txt (group 2 is empty). Together groups 1,3,4,5 cover all 137 test files (11306 tests collected).
- pytest -m perf (3.12, 3.13); tests/textnorm_mutants.py; tests/stage_mutants.py; tests/mutation_runner_mutants.py (3.13). Wrapper to resume: /home/user/build/chunks/A7/mut.sh (runs the three in order in copy EV-A7m with venv-a7m-313, writes mut-<name>.done).
- fail-before, hygiene, PG17, semgrep, pip-audit, zizmor, gitleaks, trivy (not asked / not in this container).

Anomaly (not explained): two attempts at one full `pytest -q -m "not live and not perf"` run on 3.13 ended silently with inner rc 0 and NO summary line, at about 12% (attempt1, 1427 dots) and at 85% (attempt2, 9612 tests passed, after test_review_pr3_round2.py::test_server_error_after_create_is_looked_up[408]), each after about 9 minutes. Logs kept: pytest313-attempt1-TRUNCATED-exit0.txt, pytest313-attempt2-TRUNCATED-exit0.txt (attempt 1 was started under a tool call that was later moved to background; cause unknown; file groups of the same tests ran clean when isolated: tests/demo_askdata (killed by me at 69%, no failure seen), test_review_pr3_round2.py 37 passed, test_verify_readonly+test_wire+test_cuj 39 passed). Switched to chunked runs (chunk.sh, one retry if no summary line).
