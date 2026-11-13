Status: resolved

# Goldfish Annotated Review Report, PD Part 6 (mode banner and demo-only guard), round 11

**Target:** `/home/user/build/snap/pdbanner-06ed4b4c/DIFF.patch` (full), head `06ed4b4cd59041c3ab4f2c8c59a841faccc7ac36`, mode-safety path (no round cap).
**Inputs:** `pdbanner-06ed4b4c-design-r11.md` (0 Blocker, 3 Major, 7 Minor, 4 Nit) and `pdbanner-06ed4b4c-codebase-r11.md` (0 Blocker, 3 Major, 5 Nit). Both reviewers read code only; nothing was run by them. Runner a2432ae7 has not reported; its findings are an addendum for the builder.
**Method:** every finding checked against what the reviewers could read; none contested. 28 findings and the lead's suppression count merge into 8 issues. Settled from r10 stays settled (seal compares by identity, masker equals main, `is_stand_in` not called, deepcopy raises, row count 317).
**Binding decisions applied:** Part 6 does not call `is_stand_in` until Part 2 merges; masker equals main (BEARER 12+, BASIC 8+); fake credentials built from parts; no suppressions; builders never commit under `handover/`.
**No fail-open and no Blocker was found.** The remaining work is labels, a table check, one unsealed value, suppressions and wording. Because these sit on the mode-safety path and the batch touches code, a fresh round is still required.

## Handoff counts

- PROPOSE FIX accepted: 7 issues. DECLINE: 1 (N7, issue 8). CONTEST 0.
- ESCALATE: 1 (issue 4, the lead decides which suppressions the design truly needs; list below).
- Remaining unaddressed: 0. **Round 12 is REQUIRED** (3 Major plus a suppressions Major on a mode-safety path, no cap).

## Decisions made here

1. **Reference head for labels: dd827d79** (the r10 decision). `test_pin_*` passes on dd827d79. A test not named pin must fail on dd827d79 for BEHAVIOUR. A failure caused only by importing a helper that does not exist on the old code does not count.
2. **N7 (public `services_in` name): declined.** The "one public entry" decision stands (`test_mode_banner.py:~390` asserts no `services_in` on `mode_banner`); `app.py:40` imports the private `_services_in` on purpose. The reviewers agree.

## Prioritized findings

### Issue 1, Major, class PIN-LABELS / HELPER-IMPORT (codebase M1, design M1, M2, M3, m5)
`_given()` (`test_mode_banner.py:2143-2160`) imports `_Given`, a new name, so every test through `_given`, `_sealed_app`, `_sealed_with` (about 30, e.g. `:2531-3496`) fails on dd827d79 and cdbe1445 only by missing name; several were true pins in r10 and were renamed with a false "proof" label. Seven `test_pin_*` tests fail on dd827d79 (45-link chain; masker scheme word and token of bearer and basic; 11-character bearer; unconfirmed banner painted with names; page and Python agree on missing/null; real app lists every container entry; banner error logged once). `test_a_copy_keeps_the_file_mode_where_os_has_no_fchmod` (`test_demo_only_guard.py:~2356`) passes on both old heads and is not a pin. The "logged once" test (`:3398-3425`) never asserts `len == 1`.
PROPOSE FIX: make `_given` tolerant (`getattr(app_mod, "_Given", tuple)` and call the old `_seal` form when absent) so old-code results reflect behaviour; re-run the whole new and changed test set against dd827d79 with raw lines; set every label and name from that run (fails there for behaviour: plain name and the header says "fails on dd827d79 because ..."; passes there: `test_pin_*`). Rename the fchmod test `test_pin_*` with a correct comment (R10F2 keeps it as a killer). Assert `len(records) == 1` in the once test. Fix names that overclaim (m5): masker bounded-reads (counts only the pair step: say so), time test (a 5 s bound), missing/null test (only for demo and quiet; Python missing is a TypeError), the not-connectivity reasons test (assert the full text).

### Issue 2, Major, class SEAL-COMPLETE (design m3)
`config.environment` is a plain `str` (`_PLAIN`), not compared, and it drives the banner mode and tag; a forced `object.__setattr__` pilot-to-demo change would leave DEMO beside real services.
PROPOSE FIX: add `environment` (value) to the sealed tuple and compare it in `_known_overrides`; test: forced change reads unconfirmed (fails on 06ed4b4c); mutant row for dropping the comparison.

### Issue 3, Major, class MUTANT-KILLER (codebase M2, M3, design m4)
`expectation_nowhere_in_killer` (`test_banner_mutant_table.py:~340-370`) accepts a row if its `expect` is in the whole killer FILE, any f-string in the killer or its callees, or a six-character overlap. No row covers the `toolbox is not a dict` TypeError (`app.py:213-215`), the non-mapping per-agent `members` raise, or the `_UNREADABLE` check in `_known_overrides` (`app.py:254`; probably equivalent).
PROPOSE FIX: restrict the check to the killer's own function text and its direct helpers; drop the blanket f-string pass; keep the planted tests (one that a fragment no string can make is reported). Add rows and killers for the two raises; for `_UNREADABLE` either add a killer that fails when the check is removed (a string `sealed[0]` must not reach `tuple(self.overridden) !=`) or record the equivalence reason in the table and test that every EQUIVALENT entry has a reason.

### Issue 4, Major, class SUPPRESSIONS (design m7; lead count)
The diff vs origin/main adds (counted from added lines): `noqa: BLE001` 14 (one with S110), `noqa: S603`/`S607` about 22 (tests that start node, setpriv and git), `noqa: S311` 4, `noqa: S102` 1, `noqa: F401` 1, `type: ignore[...]` 15 (call-arg 7, attr-defined 2, assignment 2, list-item, dict-item, call-overload, arg-type), `fmt: skip` 11, `pragma: no cover` 1. The project rule is no suppressions. Earlier rounds did not count these; that is a miss on my side and is fixed here.
PROPOSE FIX (builder, all except ESCALATE items): remove every `fmt: skip` (reformat), every `type: ignore` (fix the typing: a Protocol or `cast`, typed fakes, correct call signatures), `S311` (use a seeded `random.Random` helper only if S311 is not triggered, else `secrets` or a deterministic counter), `F401` (use or remove the import), `S102` (no `exec`: load the module with `importlib`), `pragma: no cover` (add a test or delete the branch). Subprocess lines (`S603`, `S607`): call tools by absolute path found with `shutil.which` and a list argument, so the rule does not fire; if the rule still fires, escalate. For `BLE001`: narrow to named exception tuples wherever the code knows what can fail.
**ESCALATE (lead decision):** the broad `except Exception` sites that the mode-safety design needs, so that any failure reads as "unknown" and shows the unconfirmed banner: `mode_banner.py` (about 4 sites near `:514, :964, :1142, :1155`), `app.py` (`:268, :285`, `_known_overrides` and the banner read) and the masker/tick fallbacks if any remain. The builder must list each site with the exact exceptions it can name; any site that cannot be narrowed is reported to the lead (options: a project-level ruff rule for this one module with the reason written in `pyproject.toml`, or a narrower named tuple plus a test that a surprise error still gives the unconfirmed banner). No inline suppression stays silently.

### Issue 5, Minor, class SEAL-TEST (design m1, m2)
The three-shapes test (`test_mode_banner.py:3332-3379`): the "reads unconfirmed" half cannot fail because the apps pass `channel=` and `secrets=`. The `_Given` type is not an identity token (documented).
PROPOSE FIX: seal the three config shapes with `_given()` as well so the unreadable-to-unconfirmed step is proved for each shape; keep the CHANGELOG sentence that `_seal` is callable from Python and add to it exactly what is and is not guaranteed.

### Issue 6, Minor, class CHANGELOG-TRUTH (codebase N1, N3, design m6, nit)
"Three equal plus one superset": the count is a literal tuple, not derived from the listing test; the decision text cited at `test_demo_only_guard.py:1959` is only partly in `CHANGELOG.md:226`. "Logs one warning line" is once per process and error type. "Nothing that worked before stops working" for deepcopy rests on one fake app and conflicts with the repo test at `:2656` (a plain App could be deep-copied before). "4627 on 3.14" is checked only against the formula with 3627 typed by hand. The CHANGELOG calls the fourth masker pass "address"; the code calls it URL.
PROPOSE FIX: derive the listing count from the listing test's own table; put the decision text in the CHANGELOG; fix each sentence; label the 3.14 figure "from the formula; CI runs 3.12 and 3.13"; say deepcopy of an App now raises on purpose (a behaviour change, listed as such) and drop the "nothing stops working" line; use "URL".

### Issue 7, Minor, class TEXT / FLAKE (codebase N2, N5, design nits)
`app.py:146` and `:125-136` long lines; `_connected_parts` docstring does not name the new `TypeError`; `test_mode_banner.py:2834` and `:2850` call `_paint` without `@needs_node`.
PROPOSE FIX: wrap and correct; add the decorator.

### Issue 8, Nit, DECLINE (N7)
Public `services_in` name left undone; see decision 2.

## ONE FIX BRIEF (single small builder, batch 12; fast-forward only onto `wip/cloud-pd-banner`)

Rules: `PYTHONPATH=<worktree>/src` and print `hadavin_sdk.__file__` before any run; cloud limits (no full suite, focused tests and focused rows only, at most 2 heavy processes); real fail-before runs in `git worktree` at dd827d79 with raw lines; no suppressions; fake credentials built from parts; never commit under `handover/`; NEVER answer y/yes to a start or confirm prompt of a script that can reach a network or send mail (loopback only; a prompt means STOP and report).

| # | Class | File and change | Test | Mutant row | Fail-before |
|---|---|---|---|---|---|
| A | PIN-LABELS / HELPER-IMPORT | tolerant `_given`; relabel and rename from a real dd827d79 run; fchmod test pin; once test asserts 1 | the relabelled set | rows follow renames | raw lines on dd827d79 |
| B | SEAL-COMPLETE | `app.py` seal and compare `config.environment` | forced change reads unconfirmed | drop-comparison row | fails on 06ed4b4c |
| C | MUTANT-KILLER | narrow `expectation_nowhere_in_killer`; rows or reasons for toolbox-not-dict, non-mapping per-agent, `_UNREADABLE` | planted tests; killers | rows for the two raises | fail when `expect` is wrong |
| D | SUPPRESSIONS | remove all 69 inline suppressions as listed; list the ESCALATE sites | ruff, type check, existing tests green; grep of added lines shows none | none | n/a |
| E | SEAL-TEST | seal three shapes with `_given()` | shapes read unconfirmed | existing rows | fails if seal skipped |
| F | CHANGELOG-TRUTH | issue 6 | derived-count test; claim tests | none | wrong claim fails |
| G | TEXT / FLAKE | issue 7 | none (read check, `@needs_node`) | none | n/a |

Builder reports once when ALL of A-G are done: new head sha, raw fail-before lines, grep result for suppressions on added lines, the ESCALATE list with exact sites, anything not done and why.

## Round 12 and evidence for the final head

- **Round 12 is required.** Fresh design and codebase reviewers on a new snapshot; the reviewers must be told to count suppression markers on added lines.
- **Cloud evidence (runner, records only):** focused tests on Python 3.12 and 3.13; new, re-pointed and renamed mutant rows plus a 60-row sample; fail-before on dd827d79 with raw lines; suppression grep.
- **RUN ON LAPTOP (Linux Docker, final head only, after a fresh round finds 0 Blocker and 0 Major):** hadavin-sdk `<final sha>` full pytest plus the complete banner_mutants (317+ rows) and stage_mutants tables, py313 and py312, Postgres, CI flags. Windows is not valid evidence.
- Ledger rows PDBANNER-r11-1..6 exist; the caller adds rows for issues 5-7 if wanted.
