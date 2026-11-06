# P8a revision 3, round 3 (last): correctness review

Target: `tickets/P8a.md` revision 3 (4beab9e). Reviewer: egm-codebase-details, read-only, no shell (no git, no hashes), did not open reviews/ or evidence/. Verdict: 0 Blocker, 4 Major, 6 Minor, 3 Nit. Saved from the hand-back, condensed.

| id | sev | ticket line | problem | fix |
|---|---|---|---|---|
| R3-COR-1 | Major | 102, 66 (T8, refunds :280), 147 | rewritten refunds test asserts `src/refunds/core_copy/` does not exist; a run leaves untracked `__pycache__`, so the test fails depending on clone state | assert no `*.py` under it (or no tracked file), or `git clean -fdx` before R3 and write that into R3 |
| R3-COR-2 | Major | 171-172 (M14), 191, 149 (R10) | M14 killer cannot kill the plant: renaming only the import alias leaves `return _core.fold_key(s)` (refunds/textnorm.py:98) so the regex count in mutants_review12.py:35 stays 1 and the module just raises NameError | killer is R3 (AST asname `_core`), R6 second; if R10 stays, plant renames every use of `_core` |
| R3-COR-3 | Major | 138 (R1c), 173, 190 (M13) | R1c is "a printed pair must agree": no command, no exit code; M13 depends only on it; second half (hadavin-sdk in dependencies) has no command | give a `python -I` script (tomllib plus the line-97 git grep) that exits non-zero both ways |
| R3-COR-4 | Major | 120, 171 (M11), 155 | the one ALLOW site (dealdesk guards.py:84-90) has an R13 rule but no mutant; M11 plants only a DENY path | add M15 (dealdesk only): make `verdict` always EQUAL at guards.py:84; killer R13 ALLOW rule; cells 47, dealdesk 14; update Counts, line 193, Done |
| R3-COR-5 | Minor | 149 | R10 cites wrong: apexc mutation_check.py:511 is `t.replace(o,n)`, presence test :507, no `.count`; dealdesk :1138 uses `.count(old)`; refunds :531-533 is `re.subn(...count=1)`, n != 1 | state R10 as the lead's script with the right cites |
| R3-COR-6 | Minor | 97, 106, 65 | apexc tests that read rewritten docs missing from the must-hold list: test_v10.py:300, :308; test_v11.py:241 (bans owner, lead, studio, handoff, R\d{2,3} in README/acceptance/CORE_COPIES) | add the three tests; rewritten prose avoids those words |
| R3-COR-7 | Minor | 157, 123 | R14 cite `textnorm.py:13, 22` should be :14; nothing says whether dealdesk `views()` maps TextnormError to Malformed; `injection_flags` (warn-only) and intake `item_row_id` ("never raises") now can raise | fix cite; per entry either adapter converts or "loud raise accepted" and reword the docstrings |
| R3-COR-8 | Minor | 87, 90, 96 | stale prose after the swap not listed: intake textfold.py:5, coreredact.py:5, refunds textnorm.py:18, apexc normalise.py:9 | add to S12, S15, S11, S1 |
| R3-COR-9 | Minor | 128, 158 | pin-only run edits pyproject/uv.lock before "edits"; not said it runs in a discarded clone | say so; real change set starts from the unmodified head |
| R3-COR-10 | Minor | 170, 188 | M11 plants one fold function per demo; mixed_script (refunds writegate.py:197, apexc egress_text.py:429), apexc fold_key (:352,:415), intake egress.py:19 unplanted | add plants or state in Done they rest on R13 and the adversarial reader |
| R3-COR-11 | Nit | 197 | rollback tag `pre-repin` vs template `pre-<package>` | cite plan-v3 line 193 |
| R3-COR-12 | Nit | 108 | "no `source=`": `source="cli"` exists at limits.py:39 | reword: no `source` parameter on stop/reset; no is_stopped |
| R3-COR-13 | Nit | 259 | "26 rows plus 1 author row" vs 27 table rows | "27 table rows (26 decisions + 1 author row)" |

Verified: all 17 fields; counts (20 R rows; 14 mutants; 46 applicable and 10 N/A cells; T1-T8; S1-S16; 9 fold-site rows; 16 PENDING LEAD; 27 CHANGELOG rows; copies 17 to 7); R7 29 lines in 21 files over all snapshots, 25 on the a12 set; R7b 15 / 12; R9 values; pin lines; T4 mechanics; a long list of demo cites; P1 cites; orders 20/21/24 text.
Not checked: git/hash facts, live demo heads and configs, core_sync_check.py, P1 at FINAL, the weight formula behind R14, P2a cites, other snapshots, apexc fakes.py entry points.
