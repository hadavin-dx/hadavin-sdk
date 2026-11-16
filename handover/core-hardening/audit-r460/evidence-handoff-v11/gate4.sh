#!/bin/sh
# The CI gate commands (.github/workflows/ci.yml lines 79, 81, 88, 94, 119) as one script. Not run by the author.
# usage: sh gate4.sh <prefix>   (run in the repository root, with no cloud settings in the environment)
# Each command writes <prefix>-<name>.txt with its own exit code on the last line; the gate is the exit code, never a pipe.
# Nothing here changes a source file. The perf step runs alone, after the main tests (ci.yml:94).
p="$1"
ruff check src tests demos > "$p-ruff.txt" 2>&1; echo "rc=$?" >> "$p-ruff.txt"
ruff format --check src tests demos > "$p-format.txt" 2>&1; echo "rc=$?" >> "$p-format.txt"
pytest -q -m "not live and not perf" -rs > "$p-pytest.txt" 2>&1; echo "rc=$?" >> "$p-pytest.txt"
pytest -q -m perf -rs > "$p-perf.txt" 2>&1; echo "rc=$?" >> "$p-perf.txt"
bandit -q -r src demos -ll > "$p-bandit.txt" 2>&1; echo "rc=$?" >> "$p-bandit.txt"
tail -n 1 "$p"-ruff.txt "$p"-format.txt "$p"-pytest.txt "$p"-perf.txt "$p"-bandit.txt
