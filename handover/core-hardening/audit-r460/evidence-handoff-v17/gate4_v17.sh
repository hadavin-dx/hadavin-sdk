#!/bin/sh
# gate4.sh v17 copy (differs from the v16 copy only in the output folder; NOT re-run in v17).
# usage: sh gate4.sh <prefix>      (start it from any folder; it finds the repository root itself)
# Repository root = four folders above this script's own folder (evidence-handoff-v17 -> audit-r460 -> core-hardening -> handover -> root).
# Outputs go into THIS script's folder (the evidence folder) as <prefix>-<name>.txt; each file ends with its own rc=<exit code>.
# The gate is each command's own exit code, never a pipe. Nothing here changes a source file. The timing step runs alone, last but one.
#
# What CI does that this script does NOT do (so a green run here is weaker than CI; the lead's CI run is the gate):
#   - CI sets HADAVIN_TEST_PG_DSN and HADAVIN_TEST_VAULT_ADDR for the test step (ci.yml lines 86-87) and HADAVIN_TEST_PG_DSN for the
#     timing step (ci.yml line 93). This script sets neither (repo rule: tests run with no cloud settings), so the database and vault
#     tests SKIP here and the -rs flag lists them.
#   - CI installs the locked environment (ci.yml line 77) and checks `psql --version` (ci.yml line 83); here uv builds the environment.
#   - The CI security job (pip-audit, Semgrep, zizmor, gitleaks) and CodeQL, SonarCloud and CodeRabbit are not repeated.
# The lint and test commands run through `uv run --all-extras --group test` (rule verify-tests-and-evals); bandit lives in the scan group.
set -u
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 2
root=$(CDPATH= cd -- "$here/../../../.." && pwd) || exit 2
[ $# -eq 1 ] || { echo "usage: sh gate4.sh <prefix>" >&2; exit 2; }
p="$here/$1"
cd "$root" || exit 2
uv run --all-extras --group test ruff check src tests demos > "$p-ruff.txt" 2>&1; echo "rc=$?" >> "$p-ruff.txt"
uv run --all-extras --group test ruff format --check src tests demos > "$p-format.txt" 2>&1; echo "rc=$?" >> "$p-format.txt"
uv run --all-extras --group test pytest -q -m "not live and not perf" -rs > "$p-pytest.txt" 2>&1; echo "rc=$?" >> "$p-pytest.txt"
uv run --all-extras --group test pytest -q -m perf -rs > "$p-perf.txt" 2>&1; echo "rc=$?" >> "$p-perf.txt"
uv run --all-extras --group scan bandit -q -r src demos -ll > "$p-bandit.txt" 2>&1; echo "rc=$?" >> "$p-bandit.txt"
tail -n 1 "$p-ruff.txt" "$p-format.txt" "$p-pytest.txt" "$p-perf.txt" "$p-bandit.txt"
bad=0
for n in ruff format pytest perf bandit; do
  [ "$(tail -n 1 "$p-$n.txt")" = "rc=0" ] || bad=1
done
exit $bad
