#!/bin/bash
H=/home/user/build/heavy.sh; W=/home/user/build/EV-P77-8b2b716/wt; L=/home/user/build/evid-out/P77/8b2b716; P=$L/progress.txt
OLD=/home/user/build/EV-P77-8b2b716/old; B=/home/user/build/venv-p77-313/bin
export HADAVIN_TEST_PG_DSN="postgresql://postgres@127.0.0.1:<pgport>/postgres" PGHOST=127.0.0.1 PGPORT=<pgport> PGUSER=postgres
echo "chain3 start $(date -u +%T): perf and corrected fail-before (chain 2 lost perf: run() undefined; its fail-before used the wrong parent ec5ecd6)" >> $P
cd $W
{ echo "HEAD $(git rev-parse HEAD)"; echo "\$ pytest -q -m perf -rs (5 files)"; } > $L/perf-313.txt
$H $L/perf-313.txt $B/python -m pytest -q -m perf -rs -p no:cacheprovider tests/test_redact_fold_budget.py tests/test_redact_fold.py tests/test_k5_perf.py tests/warden_port/test_redaction_review2.py tests/warden_port/test_redaction_bank.py
echo "perf-313 $(tail -n 2 $L/perf-313.txt | tr '\n' ' ') $(date -u +%T)" >> $P
mv $L/failbefore.txt $L/failbefore-WRONG-parent-ec5ecd6.txt; mv $L/failbefore-srcdiff.txt $L/failbefore-WRONG-parent-srcdiff.txt
cd $OLD && git checkout -q --detach 8b2b716 && git checkout -q HEAD^2 -- src/hadavin_sdk/guard/redact.py src/hadavin_sdk/guard/runmap.py src/hadavin_sdk/defaults.py && git diff --stat 8b2b716 -- src > $L/failbefore-srcdiff.txt
{ echo "HEAD(tests) 8b2b716 + src (redact.py runmap.py defaults.py) from P1a parent $(git rev-parse HEAD^2)"; } > $L/failbefore.txt
$H $L/failbefore.txt $B/python -m pytest -q -rf --no-header -p no:cacheprovider tests/test_redact_fold.py tests/test_redact_fold_budget.py tests/test_redact_fold_property.py tests/test_redact_fold_seams.py tests/test_k5_round12_fuzz.py -m "not perf"
echo "failbefore $(tail -n 2 $L/failbefore.txt | tr '\n' ' ') $(date -u +%T)" >> $P
/home/user/build/pgstop.sh p77 >/dev/null 2>&1
echo ALLDONE3 >> $P
