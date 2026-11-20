# G4d build notes (builder, G4c result review 1 majors M1-M3), branch `wip/cloud-core-c/g4d`

Base: `origin/cloud/core-c` 5464b1033. Edits: HOSTNAME/HOSTKEY patterns in `src/hadavin_sdk/guard/redact.py` (and the comment above them), `tests/test_host_names.py`, `tests/b64_mutants.py`. Defaults only.

## Leak reproduced first (TESTED, direct, base tree through `runmap.redact_text`)
`db01.corp例`, `db01.local例`, `db01.local-x例`, `例host=db01-7`, `host=db01-7例` all came back unchanged (readable). `db01.corp.example例` was already masked (a label can absorb the glue).
Controls already fine: `jdk.internal.reflect`, `threading.local()`, `host=db01-7`.

## Change (TESTED)
- New `_HOST_END = r"(?![A-Za-z0-9_-])"` used after the tail suffix, after the hyphen rest of the bare suffix, and in the bare alternative (was `(?![\w-])`). The bare-alternative code guard `(?!DOT\w|\()` is untouched, so `jdk.internal.reflect` and `local()` stay kept.
- HOSTKEY: look-behind `(?<![\w-])` -> `(?<![A-Za-z0-9_-])`; trailing `(?![\w\-/@])` -> `(?![A-Za-z0-9_\-/@])`. The `_HOST_ARCH` guard `(?![\w-])` is unchanged (a CPU name followed by CJK stays kept; not in scope).
- After: all five leaking inputs masked; the controls unchanged. `db01.corp_例` stays readable on purpose: `_` is an ASCII label character, so `corp_` is a label, not the suffix (ASCII glue, as before).
- M3: `dbé01.corp.example` is in fact fully masked here (the fold scan turns é into e first), so the review's partial-leak example does not reproduce. A CJK letter inside a label does leak the part before it: `db例01.corp.example` -> `db例<HOSTNAME_1>`. Pinned as xfail `test_host_non_ascii_inside_a_label_is_masked` (TB-4.14, strict, id L-H5) and stated in the redact.py comment (labels are ASCII, L11).

## Tests and mutants (TESTED, venv python, PYTHONPATH=src, serial)
- TB-4.13: `test_host_starts_after_a_non_ascii_word_character` now pins the first case by equality (`x 例db01.corp.example y` -> `x 例<HOSTNAME_1> y`, so the over-mask length is exact); new `test_host_ends_before_a_non_ascii_word_character` (trailing glue, 5 rows plus the `local()` and `internal.reflect` guards) and `test_host_key_glued_to_a_non_ascii_word_character` (HOSTKEY before and after).
- Mutants: 4 new (suffix lookahead, bare lookahead, HOSTKEY look-behind, HOSTKEY look-ahead, each back to `\w`), all KILLED by the TB-4.13 rows. The TB-4.6 ("v3 start look-behind") mutant keeps the full start literal; the TB-4.13 start mutant now anchors on the first two look-behinds only; "plain ASCII look-behind" anchors on the third look-behind only: three different anchors. Anchors of the older host mutants re-pointed at the `_HOST_END` source (ruff format splits the longer lines).
- Run (TESTED): `tests/test_host_names.py tests/test_p1c_gaps.py tests/test_p1d_a_*.py tests/test_redact_glued_rest.py tests/test_redact_g3_port.py tests/test_redact_idempotent_property.py -m ""`: 3497 passed, 46 xfailed.
- `tests/b64_mutants.py` WHOLE: 62 of 62 KILLED (58 + 4), exit 0. `tests/g8_mutants.py` WHOLE: `43 of 43 good; problems: []`. `tests/p1d_a_mutants.py` WHOLE: 50 of 51 KILLED, A15 SURVIVED (as at the base, known), exit 1.
- ruff check and ruff format clean on src tests tools (TESTED).
- Important: pytest from a worktree must set `PYTHONPATH=src`; without it the editable install resolves to the main checkout and the new tests fail against old code (this happened once, then was corrected).

## Linear time (TESTED, `findall`, 40-80k characters, seconds before / after, HOSTNAME | HOSTKEY)
Inputs: `a[.]`, `a.-_`, `a-`*+`.corp`, `a.`, `ab-cd.`, `例-_a.`, `é.a`, `host=a`, `host=例a-`, `a.corp例`, `host=a-1例`, `a`*60000+`.corp`, `host=`+`a`*60000, `a.local-`+`-`*60000, `例host=`.
Before: every run 0.0005-0.0089 s. After: 0.0005-0.0089 s (largest `a.` 0.0085 -> 0.0089); the new matches (`a.corp例` 10,000 hits, `host=a-1例` 8,000 hits) cost 0.004 s. No growth beyond noise; the checked-in TB-4.10 (perf marker, run with `-m ""`) passes.

## Delta over the property corpus (TESTED)
`tests/test_redact_idempotent_property.py::CORPUS`, 1,978 inputs, `runmap.redact_text` at base vs now: outputs identical in all 1,978 rows (placeholder count 41,298 both). No fewer masks. (The corpus holds no non-ASCII-glued host, so no row changes; the new behaviour is covered by TB-4.13.)

## NOT RUN
Full suite, `-m perf` beyond the files above, other mutant files (redact, gate, stage, textnorm), CI, SECURITY.md/CHANGELOG.md (docs pass), the p1d texts delta of G4c (only the property corpus was re-measured).
