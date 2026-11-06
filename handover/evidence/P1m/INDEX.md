# P1m evidence index

Head sha: 657b20b413db1fa66d974c59e62c796c1fef84a4 (branch core/P1m, merged with origin/main 4ec3616). Each file starts with the head sha.

| # | command | exit code | head sha | UTC time |
|---|---|---|---|---|
| 01 | `ruff check src tests demos tools` | 0 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:21:47Z |
| 02 | `ruff format --check src tests demos tools` | 0 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:21:47Z |
| 03 | `bandit -q -r src demos tools -ll` | 0 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:21:49Z |
| 04 | `pytest tests/test_mutation_runner.py tests/test_mutation_runner_meta.py -rs -rP -m 'not live and not perf' -p no:cacheprovider` | 0 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:22:35Z |
| 05 | `pytest tests/test_mutation_runner_meta.py -q -rP -p no:cacheprovider` | 0 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:22:36Z |
| 06 | `python tests/mutation_runner_mutants.py` | 0 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:24:26Z |
| 07 | `python -I -c "import sys; sys.path.insert(0,'.'); import tests.mutation_runner_mutants as m; [print(i,x.name,x.file,'allow_crash=',x.allow_crash,'crash_type=',x.crash_type or '-','test_file=',x.test_file,'only_test=',x.only_test) for i,x in enumerate(m.M,1)]; print(len(m.M),'mutants;',sum(x.allow_crash for x in m.M),'allow_crash')"` | 0 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:24:26Z |
| 08 | `cd /tmp/claude-0/-home-user/203f6188-e1bc-5eda-aaab-325ff81324d2/scratchpad/oldtree && /home/user/build/P1m/.venv/bin/python -m pytest tests/test_mutation_runner.py tests/test_mutation_runner_meta.py -q -p no:cacheprovider` | 2 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:24:27Z |
| 09 | `pytest -q -m 'not live and not perf' -rs -p no:cacheprovider` | 0 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:28:37Z |
| 10 | `pytest -q -m perf -rs -p no:cacheprovider` | 0 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:29:32Z |
| 11 | `cd /tmp/claude-0/-home-user/203f6188-e1bc-5eda-aaab-325ff81324d2/scratchpad/nosup && /home/user/build/P1m/.venv/bin/ruff check --config /home/user/build/P1m/pyproject.toml --output-format concise src tools` | 1 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:24:27Z |
| 12 | `cd /tmp/claude-0/-home-user/203f6188-e1bc-5eda-aaab-325ff81324d2/scratchpad/nosup && /home/user/build/P1m/.venv/bin/bandit -q -r src tools -ll` | 1 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:24:27Z |
| 13 | `python tools/scan_repo.py` | 0 | 657b20b413db1fa66d974c59e62c796c1fef84a4 | 2026-11-06T03:24:28Z |

Expected non-zero: 08 (exit 2, fail-before on old code: ModuleNotFoundError for tools); 11 and 12 (exit 1: the same code with the three noqa/nosec removed fails ruff S603 x2 and S314, and bandit B314).
