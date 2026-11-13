# Docs and comments: make every number and promise match what the code and tests show

## What this changes

Text only, apart from three small code changes listed below. A read-through of the public text (README, SECURITY, versions.md, contract.md, docs/*.md, workflow comments, and the docstrings that make a promise) listed each sentence that states a number, a guarantee or a result, with the file or test that backs it. This change fixes the sentences that did not match.

| Kind of change | Rows (the authors' own counts, by the builders of each part) |
|---|---|
| Sentences that were false or out of date, rewritten to what the code does | about 16 in the first pass, plus the stale test counts |
| README, SECURITY and versions.md sentences with no backing: softened or given a source | 24 |
| docs/tests, limits, settings and portal sentences with no backing: softened or given a source | about 48 |
| contract.md, n8n-recipe, hubspot-probe, real-services, why-this-code, workflow comments and code docstrings: sourced, softened or labelled | about 94 |
| Sentences about tests ("no test ...", "not tested", "tests/x.py checks ..."): every one searched against tests/; 25 were wrong or too strong and are corrected (for example a denial of a test that exists) | 103 sentences searched, 25 corrected |
| Final recount of the test count in versions.md | 1 sentence: 92 files, 3883 tests listed by `python -m pytest --collect-only -q` |

"Softened or labelled" means: where a number comes from a run the author did and no log is in the repository, the text now says "the author's own run; no log is shipped" instead of reading like a result of this commit. Counts of earlier runs stay as dated history.

## The three code changes (nothing else changes behaviour)

1. `scripts/start_all.ps1`: an empty `DESK_LEADFLOW_FILE` is now treated like the shell script does (same condition as `start_all.sh`).
2. `tests/test_input_edge_cases.py`: one assertion tightened from `in (1, 2)` to `== 1` model calls, with its docstring; `tests/test_ai_after_claim.py` also checks it.
3. `.github/workflows/lint.yml` and `sonar.yml`: the time-limit comment now says the same thing in the same words in both.

(`src/lead_desk/loader.py` also has one docstring wrapped to fit the line limit.)

## What was NOT done

* No code behaviour changed apart from item 1. The `.py` files in this change differ from main only in docstrings and comments, except the one assertion above (proof below).
* Sentences that rest on the author's own runs are still labelled as such; no logs were added.
* The owner questions (security contact, private reporting, rule-pack permission) were answered by the repository owner and are written as such; the licence terms of the Semgrep rule packs were not read.
* Not re-run on the combined tree: the full test suite (see Checks).

## Checks

* **Text-only proof.** For each `.py` file touched, the parsed syntax tree was compared before and after with docstrings and comments ignored: identical for 12 of 13; the 13th (`tests/test_input_edge_cases.py`) differs only by the one assertion in item 2. For each of the four workflow files, `yaml.safe_load` before and after is equal.
* On the combined tree (main f3c39cf8 plus eleven commits): `ruff check` and `ruff format --check` pass; `gitleaks dir` with the repository config: no leaks; `gitleaks git` over the eleven new commits: no leaks; `tests/test_hygiene.py` with `DPLD_REQUIRE_SCAN=1`: passed.
* Full suite: run on main f3c39cf8 and on main plus the FIRST FIVE patches of this series (v1, code-fix-v1, v1b, v2, v2b): 3683 passed, 200 skipped, 0 failed on both (so no test changed outcome). It was NOT run on the full eleven-commit tree: the later six commits are text-only apart from the proof above, but that is a reading, not a run. The 200 skips are the same on both (no Playwright, no gitleaks on that machine, Windows-only and similar).
* Test count: `python -m pytest --collect-only -q` lists 92 test files and 3883 tests on this tree.

🤖 Generated with [Claude Code](https://claude.ai/code)
