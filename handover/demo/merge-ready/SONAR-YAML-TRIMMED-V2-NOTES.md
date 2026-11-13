# sonar-yaml-test-trimmed-v2 (reviewer's trimmed test, 84 lines after ruff format; v2 delta had 163, v1 38)
Checks: every `*.yml` and `*.yaml` under .github/workflows parses; top level is a mapping; `on` present (True key or string key); `jobs` is a non-empty mapping. No job/step key lists. Docstring: actionlint is the real control, not wired into CI yet. `WORKFLOWS` kept. Real-file assertion (assert_file_is_fine) and empty-folder assertion (workflow_files) are each tested with pytest.raises. The original bug (`:all: -r` in a plain scalar, R1) dies.
## Which patch, which order
- `sonar-yaml-test-trimmed-v2.patch`: db54e13 alone (rewrites the 38-line file). It does NOT apply together with P1 v3 in either order (P1 v3 edits the same file's header and last lines): measured "1 T" and "T 1" both fail.
- `sonar-yaml-test-trimmed-v2-after-p1v3.patch`: use ONLY after sonar-p1-quickwins-v3.patch (keeps P1's `import re` and its two curl/pip tests; 17 passed). Applies after P1 v3 in every order with C v5, G, P2, P3 (matrix evidence-b10-3); applying before P1 v3 fails.
- With P1 v3.2 (no longer touches this file) use the plain `sonar-yaml-test-trimmed-v2.patch` in any order: 1956 of 1956 orders applied. v3.1/v3.2 and the trimmed test: no use of the removed step check exists in v3.2's own WORKFLOWS (it defines its own).
Caveat: P1 v3's `_run_commands` reads `job["steps"]`; the removed step check used to fail first on a job without steps (reusable-workflow jobs), now P1's helper raises KeyError. No such job exists today.
## Mutants (evidence-b10-7, 27 mutants: the reviewer's 21 plus E1-E6)
Survivors: T13 (safe_load -> BaseLoader, equivalent for these checks), R6/E6 (duplicate key: actionlint's job; in the P1 tree E6 is killed only by a P1 test crashing), E3 (read_text without utf-8: only matters on Windows cp1252). All others killed, including both assertions, both globs, both `on` branches, jobs empty/list, YAML error, sorted order (test names b.yml, a.yaml), and the real plain-scalar bug.
Tradeoff: a `timeout-minute` or `usess` typo is no longer found by pytest; wire actionlint.
Gates: ruff, format, tests (evidence-b10-9); mypy/bandit in evidence-b10-2 stacks.
