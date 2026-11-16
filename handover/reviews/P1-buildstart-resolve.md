# P1 build-start resolve (rev 16, FROZEN; lead order 20(3), one round)
Status: resolved (egm:egm-resolve, AUTO mode, interactive gate skipped by the lead's brief; model output, not user authority).
Target: `handover/tickets/P1.md` revision 16 (frozen body untouched; fixes appended as section "Build notes (build-start review, order 20)", BN-1 to BN-11).
Gate: S0 EXIT P1 (order 20(2)) becomes effective once this resolve is saved and the lead has read PENDING LEAD 53 to 55. No item below blocks P1m from starting.
Findings: `reviews/P1-buildstart-adv.md` (9 rows) and `reviews/P1-buildstart-cor.md` (9 rows). The adversarial file reuses ids BS-P1-COR-1 to COR-5. Its COR-1 and COR-2 are the same findings as the correctness file's. Its COR-3, COR-4 and COR-5 are DIFFERENT findings and are keyed here as `adv:COR-3`, `adv:COR-4`, `adv:COR-5`. That makes 16 distinct ids.

Facts I checked myself (Python 3.13.18, Unicode 15.1.0, `python3 -I`, read-only, on the `748849c` snapshot and on `origin/main` `124258b`):
- All 28 re-pointed mutants were parsed with `ast` from snapshot `tests/promoted_mutants.py`. All 28 names match the ticket's table at the cited lines. 27 search strings occur exactly once in their target file. #6 `ch not in FILLERS` occurs 2 times (`textnorm.py` 71 and 165), and the runner's `text.replace` swaps both (`mutation_runner.py` 257). `_DROP_CATEGORIES and ch not in FILLERS)` occurs once. #15's multi-line string occurs once.
- PIN-ENCL: the predicate written in BN-4 selects exactly 135 code points, equal to the 8 runs of the v1.1 row, against the 677-entry snapshot table. Two plausible misreadings give other counts. "No `<tag>` decomposition" gives 139 (adds U+0218-021B). "Number word only at the end of the name" gives 133 (drops U+3248-3249). So the body's wording really is ambiguous (COR-2 holds).
- Judge and runner: `judge` returns WRONG_REASON when `expect` is in neither the first failing test id nor its first E line (`testing/mutation.py` ~61). pytest runs with `-x`, in operand order (`mutation_runner.py` 130, 260-262). `run_mutants` copies only `src`, the listed tests and `extra_dirs`, never `pyproject.toml` (186-221). The ticket has no `tests` list or order for any PR (grep: no hit).
- `gen_confusables.py main` (97-101) reads `argv[1]` as the input path, so `--check` is opened as a file.
- The coverage sentence is one 3,391-character string, identical in 6 lines (8, 20, 48, 51, 223, 257). COR-7's "line 8 stale" is false.
- LEAD-ORDERS line 21, order 8(2): "P1 PL22 and PL23 as you recommended". `origin/main` `ci.yml` 79, 81 and 119 still have no `tools`.
- `runmap.undo`: `ce70eb5` line 96; `origin/main` line 141 (moved since). The `139-170` cite is in `designs/lookalike-leak.md`, not in P1.
- Repo `CLAUDE.md` line 18: "thresholds ... come from validated config in one place". Snapshot ceilings: `MAX_JUNIT_CHARS` (`mutation.py` 26), `SETUP_TRIES`/`SETUP_WAIT` (runner 91-92), `TREE_KILL_TIMEOUT` (106).

Honest note (what I did NOT check): I ran no test, mutant, ruff or bandit. pytest is not on the system interpreter, and running the repo `.venv` was outside the brief's allowed checks. So it is UNVERIFIED that the narrowed #6 still ends KILLED (it only edits `fold` now, not `has_mixed_script`). Also UNVERIFIED: that BN-2's `only_test` on all 80 mutants gives KILLED everywhere, and that perf rows flake in the baseline. All string counts are against `748849c`, not the P1a or P1b heads, which do not exist; meta-test (g) settles those. PIN-ENCL at P1b (733-entry table) is unchecked because that table does not exist; BN-4 asserts set equality so any change shows. I did not re-read the v1.1 rows beyond 202-203, the decisions 225-273, or the history sections. I did not verify ADV-4's multi-character pass count. I did not open the look-alike design beyond the grep hit.

| id | category | decision |
|---|---|---|
| BS-P1-COR-1 (both files) | PROPOSE FIX | Valid; counted (2 hits). BN-1: re-point #6 to `_DROP_CATEGORIES and ch not in FILLERS)` / `_DROP_CATEGORIES and True)`. The line-42 sentence is corrected at build start. The other 27 counted once each. |
| BS-P1-COR-2 (both files) | PROPOSE FIX | Valid. BN-4 writes the predicate as code (reproduces 135 and the 8 runs) and asserts the set, not only the count. |
| BS-P1-ADV-1 | PROPOSE FIX | Valid (judge and runner read). BN-2: every mutant gets `test_file` + `only_test`. The `tests` list is ordered with killers first. Evidence gate: 0 WRONG_REASON/OTHER_TEST/ERROR. |
| BS-P1-ADV-2 | PROPOSE FIX | Valid (no `pyproject.toml` copied). BN-3: perf, S_call and SK-5 rows go in their own files, outside every mutation `tests` list. |
| BS-P1-ADV-3 | CONTEST | PL22 is decided: LEAD-ORDERS line 21, order 8(2), and ticket line 238. The lint-with-`tools` fallback is already body line 77. The still-missing ci.yml edit goes to PENDING LEAD 53 (BN-11 records it). |
| adv:COR-3 | PROPOSE FIX | Valid. BN-5 states the digest width and `tbl=` form, adds a count assert, and corrects the overstated "hand edit fails the test" sentence at build start. |
| adv:COR-4 | PROPOSE FIX | Valid and cheap. BN-6: hashes are computed last, before each push. |
| adv:COR-5 | DECLINE | Nit, and outside P1 (the cite is in `designs/lookalike-leak.md`). Relayed as PENDING LEAD 55. Note: `origin/main` now has `undo` at 141, not 96-125. |
| BS-P1-ADV-4 | PROPOSE FIX | Valid as an evidence gap (body line 54 already says multi-character strings are UNVERIFIED). BN-10: the fuzz prints the largest pass count, and `FoldNotConverged` is a failure. |
| BS-P1-COR-3 | PROPOSE FIX | Valid; order 20(4) wins. BN-7: per-package evidence folders. |
| BS-P1-COR-4 | PROPOSE FIX | Valid (`main` 97-101). BN-8 deletes the command; corrected at build start. |
| BS-P1-COR-5 | PROPOSE FIX | Valid. Closed by BN-2: the mutant list's `test_file` is the placement table, printed in the PR, and meta-test (a) checks it. |
| BS-P1-COR-6 | PROPOSE FIX | Valid gap (repo CLAUDE.md line 18; the ticket is silent). BN-9: keep them as module constants, state the exemption in the PR. The lead confirms (PENDING LEAD 54). |
| BS-P1-COR-7 | PROPOSE FIX | Partly false ("line 8 stale": the copies are identical, checked). The valid part is the reading aid: the BN header names the authoritative sections, says notes win, and confirms the 6 copies. No body rewrite (order 20). |
| BS-P1-COR-8 | DECLINE | Nit; the reviewer asks for no fix (body line 82 already states it). |
| BS-P1-COR-9 | DECLINE | Nit; the reviewer asks for no fix. |

Couplings: BN-2 closes ADV-1 and COR-5 together and shrinks ADV-2: with `only_test`, golden and perf rows run in the baseline only, but the baseline must still pass, hence BN-3. BN-1's narrowed #6 changes the P1b re-derive (P1b rewrites `fold`). Meta-test (g) at each head is the check. BN-4 couples to PL49 (no table expansion in v1): a P1b table entry for an enclosed form would fail PIN-ENCL by design. BN-5 couples to PL52 (digest test replaces the import check). The id collision between the two findings files should be fixed at the source by the lead (PENDING LEAD 55 note).

PENDING LEAD (continuing the ticket's numbering after 52):
- **PENDING LEAD 53:** origin/main `124258b` `ci.yml` 79, 81 and 119 still lack `tools` (the PL22 lead-owned edit "before the P1m PR opens"). Recommendation: the lead adds `tools` to all three in the S0 CI PR before P1m opens; until then BN-11's paste fallback holds. Reversible: yes.
- **PENDING LEAD 54:** exempt the moved dev-tool ceilings from CLAUDE.md line 18 (BN-9). Recommendation: yes. They are internal safety ceilings of test tooling, not product config, and moving them would make P1m a `defaults.py` editor against the merge plan. Confidence 70 percent. Reversible: yes (move them in a later PR). Owner-visible because it is an exception to an owner rule.
- **PENDING LEAD 55:** relays. (a) The look-alike design's `runmap.undo` cite (139-170) is stale; `ce70eb5` has 96, `origin/main` 141. It goes in that design's build-start resolve. (b) The adversarial findings file reuses ids BS-P1-COR-1 to 5. Recommendation: rename its rows 3 to 5 as BS-P1-ADV-5 to 7 when the lead next saves it. (c) The P1 build brief should tell the builder to read the "Build notes" section (end of file) first.

Counts: 16 distinct findings. PROPOSE FIX 12 (applied as BN-1 to BN-10, BN-header; 3 one-line "corrected at build start" sentences in BN-1, BN-5, BN-8). CONTEST 1. ESCALATE 0. DECLINE 3. Unaddressed 0. New PENDING LEAD: 3 (53 to 55).
