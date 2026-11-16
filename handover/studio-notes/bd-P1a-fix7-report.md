# bd-P1a-fix7 report (builder, Sonnet 5.5), PR 63 branch core/P1a

New head: 27ae996 (pushed normally to origin/core/P1a; was bf955e9; c9fa644 is the commit the full suite ran on, 27ae996 only changes one test so the mutation copy passes). Evidence files: handover/evidence/PR63/c9fa644/builder-*.txt (not committed).

## FAILED / UNCERTAIN / NOT RUN (first)
- NOT RUN: NO mutant has been run on the new list. Attempt 1 was killed by its own 1500 s timeout while waiting for a heavy slot. Attempt 2 (08:27) failed in the baseline with "the unmutated copy does not pass its tests": my new docstring test read CHANGELOG.md, which the mutation copy lacks. Fixed in 27ae996 (verified only by running the three test files in a hand-made copy of that shape: 658 passed, 9 xfailed). The mutant run itself was not repeated (4 min baseline plus mutants, past my time box). The killers are derived by reading assertions, not seen killing: the 8+2 kill claim is UNVERIFIED. Evidence runner: run `python tests/textnorm_mutants.py` (all 138) once.
- Full suite (10620 passed) ran on c9fa644, not on 27ae996 (one test file changed after; that file ran: the docstring test passes, ruff clean).
- NOT RUN: perf rows (`-m perf`, must run alone), including the new row and the before/after ratio against bf955e9. Not done.
- NOT RUN: py3.12 full suite. Run on 3.12: only tests/test_textnorm_differential.py (536 passed, 9 xfailed; golden 15.0.0 section is genuine, made on system Python 3.12.3). 3.12 packages were installed with `uv pip install --target` outside the repo.
- IMPOSSIBLE NOW (F-R8, third party): the Unicode 18.0.0 look-alike counts need unicode.org, which the proxy refuses (403); no newer Python. Next step: someone with access runs the count and fills the CHANGELOG line (recorded there).
- Ticket deviation 1 (F6-1b): the gate `_without_spacing_marks(raw) != raw` is NOT equivalent to no gate: 61 code points (for example U+0149, U+1B06, U+0B94) hold no spacing mark but decompose into one under NFKD. I made the gate test the raw text and its NFKD text. The F6-1b test proves gated == ungated for every code point and every name; the ticket's own gate failed that on the old probe. Stated in CHANGELOG.
- Ticket deviation 2 (F6-5): corpus row r085 became an unexpected pass; handled with DENY_FAILS_CLOSED = {"r085"} in tests/test_textnorm_differential.py (strict xfails: 9 now, was 10).
- Mutant split is NOT 8+2 over the whole list: derived over all 138 it is 131 behaviour and 7 wording-only (5 older ones are wording by tree). The 10 new ones are 8 behaviour and 2 wording-only, as the ticket says.
- Fail-before (builder-fail-before.txt, tests of c9fa644 against src/pyproject/ci.yml of bf955e9): 11 of 20 selected tests fail as intended. 9 PASS on old code, honestly: test_no_approval_code_names_the_deny_check (guard, no approval names the check today), test_every_key_and_view_of_seeded_multi_character_texts_is_within_the_weight (a bound, holds on old), test_no_code_file_hides_the_ban... (old tree has no noqa), the 138-count meta test and 5 differential tests (unmoved hashes). The T6-5 config and CI tests fail on old code.

## CHECKED BY ME (command, output)
- `uv run --all-extras --group test ruff check src tests demos tools`: All checks passed; `ruff format --check`: 332 files already formatted (run before the commit; CHANGELOG-only edit after).
- `uvx bandit -ll` on textnorm.py and defaults.py: No issues identified (bandit is not in the uv group, so uvx).
- Full suite on 3.13 at c9fa644 via heavy.sh: 10620 passed, 454 skipped, 38 deselected (perf), 9 xfailed, exit 0 (builder-full-313.txt).
- tests/test_textnorm.py + tests/test_textnorm_meta.py: 128 passed. meta + differential + notices: 554 passed, 9 xfailed.
- TID251: `ruff check --select TID251 --ignore-noqa src demos tools` passes (ruff 0.16.9 on PATH here; CI uses 0.17.1, NOT checked on 0.17.1); CI step B command gives exactly 6 reports on the fixture folder (also 0.16.9).
- Golden: only the identity_keys hash changed in both sections (15.0.0 on py3.12, 15.1.0 on py3.13); alg stays fold4. Manifest and CHANGELOG hash of textnorm.py updated to 8a6da030...c6697.

## Done (ticket items)
F6-1 (DENY check reads marks-dropped text, max 6 names), F6-1b (gate in `_keys` only), F6-2 (`has_mixed_script`: Sk removed, Mc keeps a word whole, rule (b)), F6-3, F6-4 ban table in pyproject (`fold`, `squeeze`, `identity_key`; tests/** exempt), F6-5 (fail closed on Cn/Co/Cs), T6-5 (CI steps A and B after the Lint step, tests/fixtures/tid251_forms/ with 6 files, three pure-Python pytest checks, no subprocess, no new noqa), F-R2, F-R3, F-R5 (`defaults.TEXTNORM_PINNED_PYTHON`), F-R6 test of the weight bound, F-R9 (`could_be_same_person` wired into no approval check; stated in module docstring, function docstring, CHANGELOG, plus a test that greps approvals). 138 mutants, split derived in `split_counts`, one stale mutant re-pointed (mixed script never true), `_keys` tag mutant and the invisible-characters mutant re-pointed. F-R1 is the evidence runner's job.

## Not committed on purpose
The handover branch; no GitHub setting changed; nothing merged; no spend.

## Files changed (12): .github/workflows/ci.yml, CHANGELOG.md, pyproject.toml, src/hadavin_sdk/defaults.py, src/hadavin_sdk/guard/textnorm.py, tests/test_textnorm.py, tests/test_textnorm_differential.py, tests/test_textnorm_meta.py, tests/test_textnorm_perf.py, tests/textnorm_mutants.py, tests/fixtures/textnorm_golden.json, tests/fixtures/textnorm_manifest.json, plus tests/fixtures/tid251_forms/ (6 files).

R-numbers: followed R448 rung rule only as the ticket states it (ban is config, glue only); least privilege / no new identity; cited from the ticket, not re-read from the bible (bible file not opened by me: NOT CHECKED).

Agents/shells: none left running (queued mutant job timed out; the failed attempt exited).
