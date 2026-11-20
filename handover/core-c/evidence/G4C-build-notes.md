# G4c build notes (builder, ticket G4 v8, Phase 4/5: HOSTNAME / HOSTKEY patterns), branch `wip-g4c`

Base: `cloud/core-c` bf7af9358 (G4 Phases 0-3, G9, G12/b, G13/b, E14, G8 ...). Source: the earlier build `dc85a5310` (branch `wip-g4-p4`) cherry-picked;
two conflicts only (the `redact.py` module docstring: both paragraphs kept; `tests/test_b64_scan.py` TB-3.4: HEAD's reference-`_pass_one` form kept, the
`NO_RUN_WORK` literal stays removed).

## The STOP, reproduced (direct, on this tree)
With the v8 start look-behind `(?<![\w-])(?<![\w-]\.)(?<![\w-]\[\.\])`, `tests/test_p1d_a_paths.py::test_property_no_linkable_host_on_the_card_and_the_card_reads_the_same_twice`
fails on `www.evil.digitaldocs.example.com(anna.m@example.org_9例-_db-7.corp.internal_é例`: shown `...<EMAIL_1>_9例-_db-7[.]corp[.]internal_é例`.
Cause as written in G4-build-notes.md: `\w` holds CJK, so `-_db-7` after `例` has no allowed start (`d` after `_`, `_` after `-`, `-` after `例`).

## The rule found (measured, one change)
The three start look-behinds name ASCII label characters instead of `\w`: `(?<![A-Za-z0-9_-])(?<![A-Za-z0-9_-]\.)(?<![A-Za-z0-9_-]\[\.\])`.
A name still never starts inside an ASCII label run (so the quadratic case of ticket 5.2 point 1 stays closed), but a name glued after a non-ASCII
letter starts at its first ASCII label character (`-` here: the match is `-_db-7.corp.internal_`; the `-_` go into the placeholder, an over-mask by two characters).
Labels stay ASCII (L11, TB-4.11 unchanged); `(?![\w-])` after the suffix is unchanged (a name followed by `é` is still a name).
Linear: findall on 40,000-80,000 characters of `a.-_`, `é.a`, `例-_a.`, `a[.]`, `例a.a`, `é-_a-`+`.corp`, `a.é`, `é.-`, `-_a.é`, `é[.]a`: 0.002-0.005 s each, within 3x of the `\w` form.
No candidate was needed beyond this one (1 try).

## Results (exact; venv python, serial, no xdist on this tree)
- Phase 4 STOP test: green. p1d_a: `tests/test_p1d_a_*.py`, `test_p1c_gaps.py` (OPEN_ROWS empty: the 19 host rows are ordinary tests), `test_host_names.py`, `test_redact_idempotent_property.py` (1,978 inputs), `test_b64_scan.py`: 2992 passed, 6 xfailed (L-H4, L-B1/2/4/5/8). Then `test_host_names.py` + `test_redact_glued_rest.py` (G4C_MERGED = True: rows 64/71 plain tests, `after_g4c` rows 60/61/62/66) + `test_redact_g3_port.py`: 575 passed, 45 xfailed.
- New: TB-4.13 `test_host_starts_after_a_non_ascii_word_character` (the failing input, a CJK glue, an accented glue) and mutant `host start look-behind on Unicode word characters` (the v8 `\w` form back): KILLED by TB-4.13. Mutant anchors for "host v3 start look-behind" / "host plain ASCII look-behind" re-pointed at the new literal.
- `python tests/b64_mutants.py` WHOLE: 58 of 58 KILLED and good (44 base64 + 13 host + 1 new), exit 0.
- `python tests/g8_mutants.py` WHOLE: `43 of 43 good; problems: []`.
- `python tests/p1d_a_mutants.py` WHOLE: 50 of 51 good, A15 SURVIVED (as at the base, known).
- Delta vs HEAD (bf7af9358) through `runmap.redact_text`, 8,189 inputs (property corpus 1,978 + g8 case texts + 6,000 p1d TXT-A/TXT-B/EH texts + K5 units): outside p1d the outputs differ in exactly 27 rows, all host rows (privacy-masked 26/27, p1c-gap2 19 rows, g8 60/61/62/64/66/71 `text`), each a placeholder that now covers the whole name; every other row identical. In the 6,000 p1d texts 2,740 differ (the whole name is masked, placeholder numbering shifts); readable `db01.corp.example` / `db-7.corp.internal` in outputs: 79 rows at HEAD, 0 now; masks 67,150 -> 67,314 (over-mask, never a new leak: no row has a host readable that was masked at HEAD).
- After `ruff format` of the pattern (a line split only), `b64_mutants.py host` re-run: 14 of 14 KILLED; `test_host_names.py` + `test_p1d_a_paths.py`: 53 passed, 1 xfailed. ruff check and format --check clean on src tests tools; bandit -ll on redact.py: no findings.
- NOT RUN: the full suite, `-m perf`, other mutant files (redact, gate, stage, textnorm), CI.

## Deviations
1. `python` on this machine without the venv lacks no module, but `tools/mutation_runner.py` sets `PYTHONNOUSERSITE=1`: the mutant runners must be run with `/home/user/hadavin-sdk/.venv/bin/python` (the first b64 run with the system python failed its unmutated baseline for that reason, not a code reason).
2. Count pins: b64 mutants 44 -> 58 (13 host + 1 mine); g8 mutants 43 (unchanged); `tests/b64_mutants.py` docstring line about `host` selecting nothing is now stale (left; docs pass).
3. SECURITY.md and CHANGELOG.md not edited (docs pass).

Correction (G4d, 2026-11-20): the line "`(?![\w-])` after the suffix is unchanged (a name followed by `é` is still a name)" above is wrong for a CJK or other
non-ASCII glue that no label can absorb: `db01.corp例`, `db01.local例`, `host=db01-7例` and `例host=db01-7` stayed readable at this tag. Fixed in G4d
(see G4d-build-notes.md). The deviation 2 line "the `tests/b64_mutants.py` docstring ... is now stale (left; docs pass)" is also wrong: the patch had already removed it.
