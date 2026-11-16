# T3 survivor triage (P2, P4, P10) - tree-T3 = main 61ded9e + patch 1 + patch 2

Uncertain / not done (first): I judged equivalence by reading code plus running the 16 tests on each mutant; I did not
write a proof tool beyond an AST comparison for P10. I ran only tests/test_desk_address_required.py (not the full suite).
No test patch was produced because no mutant is a real gap (no survivor_tests_T3.py, no survivor-tests-T3.patch).
Nothing failed. `git status --porcelain` of tree-T3 = 29 entries, same as at start (the private .tmp-run folder I
made inside the tree was removed).

| mutant | verdict | reason (file:line) | test | killed on mutant | passes on unmutated |
|---|---|---|---|---|---|
| P2 hubspot absent falls back to vendor | EQUIVALENT | src/lead_desk/crm_hubspot.py:183-188: the line 183 check refuses when the value is absent or blank (`.get(..., "").strip()` empty), so line 188 is only reached with a non-blank value; there `env.get(X) or VENDOR` returns exactly `env[X]`. The fallback arm cannot run. | none needed | no (16 passed, run-61ded9e-P2.log) | yes (16 passed, run-61ded9e-unmutated.log) |
| P4 live absent falls back to provider | EQUIVALENT | src/lead_desk/config.py:206-211: same shape; the check at 206 refuses absent/blank, so 211 sees a non-blank value and `e.get(X) or DEFAULT` equals `e[X]`. | none needed | no (16 passed, run-61ded9e-P4.log) | yes (same unmutated log) |
| P10 hubspot required check disabled | EQUIVALENT | muts2.json inserts `pass\n            raise SettingRefused(...)`. The raise stays at the same indentation (crm_hubspot.py:184), so it still runs; `pass` is a no-op. The AST of the mutated file equals the original once Pass nodes are dropped (printed True in run-61ded9e-P10.log). The check is NOT disabled, despite the mutant name. | none needed | no (16 passed, run-61ded9e-P10.log) | yes |

## The B2 question: why they survive singly but die when combined
Can the first check (crm_hubspot.py:183, config.py:206) be reached with the address absent? Yes: absent gives `""`
from `.get`, and the check refuses (tested by test_hubspot_from_env_refuses_an_address_that_is_not_named and the live
twin, both with absent and blank values). Because that check fires first, P2 and P4 only change an arm that cannot
run: two guards cover one case, the first always wins, so there is no observable change. When B2 removed the check
AND added the fallback (P2b/P4b), the fallback became reachable, and the tests caught it. So: the existing tests cover
the real case; singles are equivalent; the combined mutants are the real ones and are killed.
Side note: the fallback arms are dead code only in the mutant, not in the product, so nothing to fix in src.

## Commands (all in /home/user/build/rr6, TMPDIR=tree-T3/.tmp-run, PYTHONPATH=tree-T3/src, no network needed)
- package path check: printed .../tree-T3/src/lead_desk/__init__.py
- unmutated: venv312/bin/python -m pytest -q -p no:cacheprovider -rfs tests/test_desk_address_required.py -> 16 passed
- mutants: venv312/bin/python out/T3/plant.py <P2|P4|P10> tests/test_desk_address_required.py (asserts the old text
  occurs once, plants, runs, restores, checks the sha256 of the restored file). Logs: out/T3/run-61ded9e-*.log.
Run table: unmutated 16 passed / 0 failed; P2 16 passed; P4 16 passed; P10 16 passed; each under 1 s, no hang.
Not run: every other test file, the full suite, any lint tool. No processes left running.
