#!/bin/sh
# Issue 6: each control test is run against a planted bad copy of the real file; it must FAIL. Raw output below.
cd /home/user/build/b10-plant || exit 2
run() { uv run --all-extras --group test pytest -p no:cacheprovider -q "$@" 2>&1 | grep -E "^E  |passed|failed" | head -4; echo "exit=$?"; }
cp CHANGELOG.md /tmp/CHANGELOG.orig; cp .github/workflows/ci.yml /tmp/ci.orig
echo "== 1 CI step control: the policy_page --check step removed from ci.yml"
grep -v "tools/policy_page.py --check" /tmp/ci.orig > .github/workflows/ci.yml
run tests/test_policy_docs.py::test_ci_runs_the_policy_page_check_right_after_the_policy_mutants
cp /tmp/ci.orig .github/workflows/ci.yml
echo "== 3 changelog reminder control: the reminder sentence removed"
python3 -c "import re;t=open('/tmp/CHANGELOG.orig').read();n=re.subn(r'is\s+a\s+reminder,\s+not\s+a\s+check',r'is a check, not a check',t);print('planted',n[1]);open('CHANGELOG.md','w').write(n[0])"
run tests/test_policy_docs.py::test_the_changelog_names_the_start_of_the_date_guard_by_rule_and_calls_it_a_reminder
cp /tmp/CHANGELOG.orig CHANGELOG.md
echo "== 3b changelog control: a start day of the names guard written as text"
sed 's/review by the earliest review date,/review by 2026-12-12,/' /tmp/CHANGELOG.orig > CHANGELOG.md
run tests/test_policy_docs.py::test_the_changelog_names_the_start_of_the_date_guard_by_rule_and_calls_it_a_reminder tests/test_policy_changelog.py::test_the_changelog_entry_for_the_page_writes_no_day_but_the_kinds_days_read_from_the_list tests/test_policy_changelog.py::test_the_changelog_entry_for_the_page_names_no_review_by_day_as_text
cp /tmp/CHANGELOG.orig CHANGELOG.md
echo "== 5 changelog control: 'review date 2026-12-11' written in the entry"
sed 's/review by the earliest review date,/review date 2026-12-11,/' /tmp/CHANGELOG.orig > CHANGELOG.md
run tests/test_policy_changelog.py::test_the_changelog_entry_for_the_page_writes_no_day_but_the_kinds_days_read_from_the_list
cp /tmp/CHANGELOG.orig CHANGELOG.md
echo "== 2/4 plant tests of the rule functions: the rule functions refuse the wrong inputs (direct call)"
uv run --all-extras --group test python - <<'PY'
from tests.test_policy_docs import _check_step_problem, _date_guard_sentence_problem
from tests.test_policy_changelog import kinds_sentence, stray_days
m, c = "python tests/policy_mutants.py", "python tools/policy_page.py --check"
print("ci wrong lists:", [bool(_check_step_problem(x)) for x in ([m], [c, m], [m, "a", c], [m, c])])
good = "fail from the day after the earliest `review_by` and is a reminder, not a check that anyone re-read the names, and " + kinds_sentence()
print("changelog wrong texts:", [bool(_date_guard_sentence_problem(t)) for t in (good.replace("the earliest", "a"), good.replace("is a reminder", "is"), good + " from 2026-12-12 on", good)])
print("stray rows:", [stray_days(good + r, kinds_sentence()) for r in (" review date 2026-12-11", " from 2026-12-12", " tool says 2027-03-03")])
PY
