#!/bin/bash
# EVIDENCE RUNNER chain for PR77 core/P2d-1 8b2b716. Records, never judges.
H=/home/user/build/heavy.sh; W=/home/user/build/EV-P77-8b2b716/wt; L=/home/user/build/evid-out/P77/8b2b716; PORT=<pgport>
cd $W || exit 1
P=$L/progress.txt
echo "HEAD $(git rev-parse HEAD)" > $L/head.txt; git ls-remote origin core/P1a >> $L/head.txt 2>&1
echo "merged-P1a-parent $(git rev-parse HEAD^2)" >> $L/head.txt
export HADAVIN_TEST_PG_DSN="postgresql://postgres@127.0.0.1:$PORT/postgres" PGHOST=127.0.0.1 PGPORT=$PORT PGUSER=postgres
/home/user/build/pgstart.sh p77 $PORT >/dev/null 2>&1
echo "pg-start rc=$?" >> $P
V12=/home/user/build/venv-p77-312; V13=/home/user/build/venv-p77-313
UV_PROJECT_ENVIRONMENT=$V12 $H $L/sync312.txt uv sync --python /usr/bin/python3.12 --all-extras --group test
UV_PROJECT_ENVIRONMENT=$V13 $H $L/sync313.txt uv sync --python /usr/local/bin/python3.13 --all-extras --group test
run() { n=$1; shift; { echo "HEAD $(git rev-parse HEAD)"; echo "\$ $*"; } > $L/$n.txt; $H $L/$n.txt "$@"; echo "$n $(tail -1 $L/$n.txt) $(date -u +%T)" >> $P; }
B=$V13/bin
run ruff-check $B/ruff check src tests demos tools
run ruff-format $B/ruff format --check src tests demos tools
run scan-repo $B/python tools/scan_repo.py
run bandit $B/bandit -q -r src demos tools -ll
run gitleaks /tmp/gl/gitleaks git --redact --no-banner --exit-code 1 --config .gitleaks.toml .
pyt() { n=$1; Bn=$2; xml=$L/$n.xml
  { echo "HEAD $(git rev-parse HEAD)"; echo "\$ pytest -q -rA --tb=short -m 'not live and not perf'"; } > $L/$n.txt
  $H $L/$n.txt $Bn/python -X faulthandler -m pytest -q -rA --tb=short -p no:cacheprovider -m "not live and not perf" --junitxml=$xml
  rc=$(tail -1 $L/$n.txt | sed -n 's/^exit=//p')
  $Bn/python - "$xml" "$rc" >> $L/$n.txt <<'PY'
import sys, xml.etree.ElementTree as E
x, rc = sys.argv[1], sys.argv[2]
try:
    r = E.parse(x).getroot(); r = r if r.tag == "testsuite" else r[0]
    t, f, e, s = (int(r.get(k, 0)) for k in ("tests", "failures", "errors", "skipped"))
    print(f"SUMMARY tests={t} failed={f} errors={e} skipped={s} pytest_exit={rc}")
except Exception as exc:
    print(f"SUMMARY NONE (no junit file, {type(exc).__name__}) pytest_exit={rc}")
PY
  echo "$n $(tail -1 $L/$n.txt) $(date -u +%T)" >> $P; }
pyt full-313 $V13/bin
pyt full-312 $V12/bin
run perf-313 $B/python -m pytest -q -m perf -rs -p no:cacheprovider tests/test_redact_fold_budget.py tests/test_redact_fold.py tests/test_k5_perf.py tests/warden_port/test_redaction_review2.py tests/warden_port/test_redaction_bank.py
# fail-before: head tests against the P2d-1 parent's three source files, in a throwaway copy
OLD=/home/user/build/EV-P77-8b2b716/old
[ -d $OLD ] || git worktree add -f --detach $OLD 8b2b716 >/dev/null 2>&1
( cd $OLD && git checkout -q HEAD^1 -- src/hadavin_sdk/guard/redact.py src/hadavin_sdk/guard/runmap.py src/hadavin_sdk/defaults.py && git diff --stat HEAD -- src > $L/failbefore-srcdiff.txt )
( cd $OLD && { echo "HEAD(tests) $(git rev-parse HEAD) + src from parent $(git rev-parse HEAD^1)"; } > $L/failbefore.txt; $H $L/failbefore.txt $B/python -m pytest -q -rf --no-header -p no:cacheprovider tests/test_redact_fold.py tests/test_redact_fold_budget.py tests/test_redact_fold_property.py tests/test_redact_fold_seams.py tests/test_k5_round12_fuzz.py -m "not perf" ) 
echo "failbefore $(tail -1 $L/failbefore.txt)" >> $P
# mutants last, alone, in the main snapshot (rewrites files); git status before/after
{ echo "HEAD $(git rev-parse HEAD)"; echo "status-before:"; git status --porcelain; } > $L/mutants.txt
$H $L/mutants.txt $B/python tests/redact_mutants.py
{ echo "status-after:"; git status --porcelain; } >> $L/mutants.txt
echo "mutants $(tail -3 $L/mutants.txt | tr '\n' ' ') $(date -u +%T)" >> $P
/home/user/build/pgstop.sh p77 >/dev/null 2>&1
echo ALLDONE >> $P
