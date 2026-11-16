# Evidence r6 for run.py (file name run.py r6) and safety-tests.sh

EVIDENCE RUNNER report. I ran the checks and saved the raw output. I do not judge. All work was on COPIES in the scratchpad /tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/ (w/, s1..s4, s2run, s2run-r5, venv). Nothing was run against /home/user/hadavin-sdk/src. No secrets, no spend, made-up toy files only.

## Failures, gaps and things that did not go as briefed (first)
1. ruff check reports 2 findings: S603 (subprocess call) at run.py lines 513 and 1266, when run with the repo's rule set (copy of pyproject.toml with only the `handover` exclusion removed, line length 100). This is the known item in REPORT-runpy7.md (no suppression by lead answer). Raw: ruff-check-repoconfig.txt. Note: ruff with its DEFAULT settings (no repo config) says "All checks passed" but `ruff format --check` then wants many reformats (line length 88); that run used the wrong config and is not evidence, I did not keep its file. With the repo config, format check passes.
2. Check 3: 33 of 38 new tests FAIL on the r5 copy. The 5 that pass are T64a, T67f, T67g, T69c, T74c. This matches the builder's "33 of 38". Observation only: T66e and T67e are labelled "guard" in their text but they FAIL on r5 (their wording or exit 5 / summary needs the r6 code).
3. Check 2 (T47a alone) was not a stock script option: safety-tests.sh has no switch to run one test. I built a derived script (header lines 1-47 of safety-tests.sh + lines 399-437 = the T47 block + a summary line); copy saved as t47a-only-derived.sh. Same for T63-T75: header + lines 690-930 (derived: t63-75-derived.sh). Neither edits run.py or safety-tests.sh. Header definitions are the same; if a later T-number needed state set by T36-T62 it would show as a FAIL on the r6 control, and it showed 0 FAIL (38 of 38 pass), so the extract is sound.
4. The full run used the real T35 (writes to the shared /tmp folder; I did not set SKIP_T35). The full output contains the text "RESTORE FAILED m1" inside the T52 section: that is a line printed by a test scenario, followed by PASS lines, not a failing check.
5. Another agent shares this repo: `git status` shows changes in handover/core-hardening/lead-repin, steps-edits and five untracked wheel files at the repo root. None are mine except files under evidence-r6/. One file, evidence-r6/T47a-alone-run-r5.txt, shows as "M" (tracked), so someone committed part of this folder while I worked. My own "before" snapshot of git status was unusable (the shared scratchpad file was overwritten by something else), so I compared by path instead: nothing under src/ or tests/ is changed (count 0).

## Result table
| check | command | result | raw file |
|---|---|---|---|
| hashes | `sha256sum run.py safety-tests.sh` | match: run.py b095825c...2892c, safety-tests.sh 4d74116c...dce1; the copies are byte-identical (cmp) | hashes.txt, cleanup-check.txt |
| 1 full safety run on copy of run.py r6 | `RUN=<copy>/run.py SCRATCH=<s1> VENV=<venv with pytest 9.2.0> bash safety-tests.sh` (Python 3.13.18, Linux) | `FAILED CHECKS: 0 (of 317 checks run; skipped: none)`, 317 PASS lines, 0 FAIL lines, exit 0. T47a PASS in this run. About 7 min | full-run.txt |
| 2 T47a alone, r6 code | derived script, T47 block only | `102 cases (signal x window); 0 bad: []`, PASS, `FAILED CHECKS: 0 (of 1)` | T47a-alone-run.txt |
| 2b T47a alone, r5 code | same on run-r5.py | same result, 0 bad, PASS | T47a-alone-run-r5.txt |
| 3 T63-T75 on r5 code | derived script, RUN=run-r5.py (sha copy of raw/.codecopies/run-r5.py) | `FAILED CHECKS: 33 (of 38)`. Passing on r5: T64a, T67f, T67g, T69c, T74c. Failing: T63a x2, T63b x2, T63c, T64b, T65 x2, T66a-f, T67a-e, T68, T69a-b, T70 x2, T71a-b, T72 x3, T73, T74a-b, T75 | T63-75-on-r5.txt |
| 3b control: same tests on r6 code | same derived script, RUN=run.py | `FAILED CHECKS: 0 (of 38)` | T63-75-on-r6-control.txt |
| 4a py_compile | `python3 -m py_compile run.py` | ok (my first compile wrote a __pycache__ in the repo folder; I removed run.* from it; folder now holds no run.*.pyc) | cleanup-check.txt |
| 4b bash -n | `bash -n safety-tests.sh` | ok | (printed only) |
| 4c ruff check | ruff 0.16.9, repo rules (extend-select B DTZ I S TID UP, line length 100) on a copy | FAIL: 2 x S603 (lines 513, 1266), "Found 2 errors" | ruff-check-repoconfig.txt |
| 4d ruff format --check | same config | `1 file already formatted` | ruff-format-repoconfig.txt |
| 5 cleanup | find markers/backups, grep planted text, pgrep, git status | 0 `*.planted.json`/`*.backup`/control markers in scratch state folders; 0 files with planted `return 2` in all 7 toy trees (each mod.py ends `return 1`); 0 stray pytest/run.py/sleep processes; no changed file under src/ or tests/ in the repo; originals' sha256 unchanged | cleanup-check.txt |

## Not checked
- A real old Python 3.11.4 (only Python 3.13.18 here; T73 simulates the old version).
- A real SEGV/BUS/FPE/ILL fault (T64a only checks the signal-handler hang as the builder's tests define it; a real memory fault was not produced).
- Windows and WSL (Linux only; run.py refuses non-Linux).
- Whether the tests are good tests (mutation of run.py itself, review of T-test quality, parallel runs, timing-flake repeats: each run was done once).
- The old-code raw files in raw/ were not re-hashed against this run beyond the two script/run copies.
- Slot rule: one heavy job at a time was respected (full run finished before T47a and T63-75 runs). Agents/shells I started: all finished; none left running.
