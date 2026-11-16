#!/bin/sh
# The four gate commands of CI as one script. usage: sh gate4.sh <prefix>   (run in the repository root)
# Each command writes <prefix>-<name>.txt with its own exit code on the last line; the gate is the exit code,
# never a pipe. Nothing here changes a source file.
p="$1"
uv run --all-extras --group test ruff check > "$p-ruff.txt" 2>&1; echo "rc=$?" >> "$p-ruff.txt"
uv run --all-extras --group test ruff format --check > "$p-format.txt" 2>&1; echo "rc=$?" >> "$p-format.txt"
uv run --all-extras --group test pytest > "$p-pytest.txt" 2>&1; echo "rc=$?" >> "$p-pytest.txt"
bandit -q -r src demos -ll > "$p-bandit.txt" 2>&1; echo "rc=$?" >> "$p-bandit.txt"
tail -n 1 "$p"-ruff.txt "$p"-format.txt "$p"-pytest.txt "$p"-bandit.txt
