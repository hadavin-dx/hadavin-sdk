# usage: flaky.sh label ; run in cwd worktree
T=tests/test_mutation_runner.py::test_the_runner_wires_pinned_so_another_failing_test_is_other_test
echo "label=$1 HEAD=$(git rev-parse HEAD)"
for i in 1 2 3 4 5 6 7 8 9 10; do
  uv run --all-extras --group test pytest -q -p no:cacheprovider -rA "$T" > run$i.out 2>&1; rc=$?
  echo "run $i exit=$rc $(grep -E '^(PASSED|FAILED|ERROR)' run$i.out | head -1) | $(tail -n 1 run$i.out)"
  [ $rc -ne 0 ] && cp run$i.out /home/user/build/EV-A21a-1a7d202/logs/flaky-$1-run$i-fail.out
done
