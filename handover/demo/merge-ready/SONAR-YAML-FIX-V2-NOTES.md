# sonar-yaml-fix-v2.patch (base 2db3926; sonar.yml run block fix + tests/test_workflow_files_parse.py, 11 tests)
Adds to v1: top-level `on` (also True, as PyYAML reads it); each job `runs-on` or `uses`; each step exactly one of run/uses
and only the 11 known step keys; the rules are a function `problems(doc)` tested with 6 in-memory typo cases.
Measured (evidence-b3-5): runs-on->run-on and uses->use on the real sonar.yml now fail; the unpatched colon bug fails.
`if:` `==`->`=` and `runner.os`->`runnr.os` still pass the test; actionlint 1.7.12 reports both; the test docstring says so.
Gates clean (ruff, format, mypy linux+win32, bandit exit 0, no line >120).
