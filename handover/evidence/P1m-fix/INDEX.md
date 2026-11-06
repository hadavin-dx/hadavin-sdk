# P1m-fix evidence index

Head sha: 7442c0f4eb7b3df9504e23065314720892cc35a3 (branch core/P1m, PR 61; Linux only). Each file starts with the head sha. The build path is shown as `<build-dir>`; `<out-dir>` is a throwaway folder for the `uv build` output.
Covers lead orders 25 and 26: Windows-capable tests, the whole `tools` folder linted in CI, the review fixes, and the check that `tools/` is not in the wheel or the sdist.

| # | command | exit code | head sha | UTC time |
|---|---|---|---|---|
| 01 | `ruff check src tests demos tools` | 0 | 7442c0f4eb7b3df9504e23065314720892cc35a3 | 2026-11-06T03:53:26Z |
| 02 | `ruff format --check src tests demos tools` | 0 | 7442c0f4eb7b3df9504e23065314720892cc35a3 | 2026-11-06T03:53:26Z |
| 03 | `bandit -q -r src demos tools -ll` | 0 | 7442c0f4eb7b3df9504e23065314720892cc35a3 | 2026-11-06T03:53:26Z |
| 04 | `pytest tests/test_mutation_runner.py tests/test_mutation_runner_meta.py tests/test_mutation_runner_helpers.py -rs -rP -m 'not live and not perf' -p no:cacheprovider` | 0 | 7442c0f4eb7b3df9504e23065314720892cc35a3 | 2026-11-06T03:53:28Z |
| 05 | `python tests/mutation_runner_mutants.py` | 0 | 7442c0f4eb7b3df9504e23065314720892cc35a3 | 2026-11-06T03:53:47Z |
| 06 | `pytest -q -m 'not live and not perf' -rs -p no:cacheprovider` | 0 | 7442c0f4eb7b3df9504e23065314720892cc35a3 | 2026-11-06T03:55:01Z |
| 07 | `pytest -q -m perf -rs -p no:cacheprovider` | 0 | 7442c0f4eb7b3df9504e23065314720892cc35a3 | 2026-11-06T03:58:40Z |
| 08 | `python tools/scan_repo.py` | 0 | 7442c0f4eb7b3df9504e23065314720892cc35a3 | 2026-11-06T03:59:33Z |
| 09 | `uv build --out-dir <out-dir> && python -I -c "import sys,zipfile,tarfile,glob; w=zipfile.ZipFile(glob.glob(sys.argv[1]+'/*.whl')[0]).namelist(); s=tarfile.open(glob.glob(sys.argv[1]+'/*.tar.gz')[0]).getnames(); print('wheel files:',len(w)); print('sdist files:',len(s)); print('wheel entries under tools/:',[n for n in w if n.startswith('tools/')]); print('sdist entries under tools/:',[n for n in s if '/tools/' in n]); print('wheel has testing/mutation.py:',any(n.endswith('testing/mutation.py') for n in w))" <out-dir>` | 0 | 7442c0f4eb7b3df9504e23065314720892cc35a3 | 2026-11-06T03:59:33Z |

Results: 51 P1m tests pass, 0 skipped (04); 37 of 37 mutants good on Linux, 34 KILLED and 3 CRASH with the declared class (05); full suite 9605 passed, 454 skipped (database and Vault tests need the CI services), 26 deselected (06); perf 25 passed, 1 skipped (07); `tools/` is in neither the wheel nor the sdist (09).
Not run here: anything on Windows (the real ctypes calls of `_pid_alive`, the junction, `taskkill /T`, the symlink skip). The Windows branches are checked only with faked system calls in `tests/test_mutation_runner_helpers.py`.
