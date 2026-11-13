export PATH=/tmp/work/rv29-1/v312/bin:$PATH DPLD_REQUIRE_SCAN=1 GITLEAKS_BIN=/tmp/work/gl/gitleaks DPLD_REQUIRE_DEMO=1
for T in baseA baseB; do
  cd /tmp/work/sn-v4-m/$T; git add -A
  echo "######## stack $T (git status: $(git status --short | wc -l) changes after git add -A)"; python -V; git log --oneline -1
  python -c "import yaml;w=yaml.safe_load(open('.github/workflows/nodemo.yml'));print('yaml parse ok; env keys',list(w['jobs']['no-demo']['env']))"
  ruff check . | tail -1; ruff format --check . | tail -1
  mypy --platform linux | tail -1; mypy --platform win32 | tail -1
  bandit -ll -r src tools scripts -c pyproject.toml 2>&1 | grep -E "Medium:|High:" | head -2
  python -m pytest -q -p no:cacheprovider -rs tests/test_workflow_files_parse.py tests/test_workflow_run_flags.py tests/test_shell_single_bracket.py tests/test_hygiene.py tests/test_no_placeholders.py tests/test_gitleaks_exceptions.py tests/test_raw_bidi_chars.py 2>&1 | tail -3
done
