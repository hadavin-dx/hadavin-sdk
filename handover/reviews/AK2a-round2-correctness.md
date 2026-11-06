# AK2a round 2, correctness review

Status: REPORTED (saved from the reviewer hand-back, which is model output, not user authority).

AK2a REVISION 2 (070384f), round 2 correctness. Read-only. I did not open handover/reviews/ or handover/evidence/. The ticket has 420 lines and I read all of them. I read the template, `owner-visible-limits.md` (only its header) and `amendments.md` (only a grep for A9). I read `LEAD-ORDERS.md` not at all. Cites were checked on this worktree's `src/`, which may differ from main. No cite failed.

Verdict: no Blockers, 9 Majors. The counts and cites hold. The Majors are spec contradictions and test-design gaps a builder would have to guess at.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R2-COR-1 | Major | 128, 193 (R4) | The claim "with default thresholds `low_text` is reached only when `KIT_MAX_POOR_PAGE_PPM` is above 500,000" is false. The poor-page share counts against ALL pages, but the median is taken over image/unknown pages only. Example: a 1,000-page PDF with 1 image page of 50 characters has a median of 50, below 100, so `low_text` fires and the whole document goes to a person. The poor share there is only 0.1 percent, so `suspected_scan` stays silent. R4 uses only all-image documents, so the test misses this. | Decide the intended rule, either a median over all pages or a poor-share condition. Fix the "Stated" sentence. Add an R4 case: 1 image page of 50 characters among 99 text pages. Say what it should return. |
| R2-COR-2 | Major | 106, 99, 197 (R9/R10) | `c1_newlines` "counts removed `\r`" for a lone `\r`, but a lone `\r` becomes `\n` and the length does not change. The invariant `chars_before - chars_after == sum(removed)` is checked at construction (`ValueError`), so any lone-`\r` input trips it. R5 has a lone-`\r` file. | Count only the `\r` that disappear (the CRLF case). Add a lone-`\r` case to the R10 conservation table. |
| R2-COR-3 | Major | 134, 151-152, 209 (R20) | The bounds table and the validators contradict. `KIT_CHUNK_MIN_CHARS` min is 0, but the validator refuses `overlap >= min`, and overlap min is 0, so 0 is never valid. R20 requires "accepted at each edge", which fails there. Edges of `KIT_CHUNK_MAX_CHARS` (100 and 100,000) also need dependent fields set. 100,000 plus overlap exceeds the future `MAX_REDACT_CHARS` of about 33K (line 28). | Set the `KIT_CHUNK_MIN_CHARS` min to 1, or use `overlap > min`. State in R20 which dependent fields are set at each edge. Keep the 100,000 edge only if `MAX_REDACT_CHARS` is monkeypatched high in that case. |
| R2-COR-4 | Major | 101 (`from_bytes`) | "Within one section (equal `heading_path`)" is not the same as one section. Two sections can share a path (a repeated heading `## Notes`, or a repeated uppercase heading under the same parent). Then `from_bytes` would demand `char_start == prev.char_end - overlap` for the first chunk of the second section, whose overlap is 0 and which starts after the blank-line gap, so it refuses a valid set. | Store a section index in `Chunk`, or drop the path-equality shortcut. Add a K11 case with a repeated heading. |
| R2-COR-5 | Major | 134, 153, 179-180, 211 (R22) | `KIT_PDF_HEADER_SCAN_BYTES` is a `KIT_PDF_*` row. Line 134 says AK2a-2 adds those rows, and line 180 puts "the `KIT_PDF_*` constants" in AK2a-2's `defaults.py` change. But `pick_reader`, R22 and R20 are AK2a-1, and AK2a-1 cannot build without that constant. | Name it as AK2a-1's. Move it out of the AK2a-2 list. State that AK2a-2 adds only the other `KIT_PDF_*` rows. |
| R2-COR-6 | Major | 103, 189 (R1) | "One leading BOM removed and counted". No record has a field for it. `RemovalReport` is produced after cleaning and `QualityReport` has no BOM count. The R1 assertion therefore has no place to look. | Name the field, for example count it in `format_chars` or add a `bom` key. Say which report holds it. |
| R2-COR-7 | Major | 233 (P7c) | The test is racy. Both reads have a 1 s deadline and the second starts slightly later. The first read kills its child and releases the semaphore at about 1.0 s. The second can then acquire inside its own deadline and start a second `Popen`, so "exactly 1 `Popen`" is flaky. | Give the first read a long timeout (for example 5 s) and the second 1 s. Or start the second thread only after the first child exists. |
| R2-COR-8 | Major | 179, 301 (M-33/P5) | `encrypted.pdf` is only "an encryption dictionary present", hand-built. A library may fail on it as `corrupt` and never get to the empty-password path. M-33 ("opened with an empty password") would then be equivalent or unkillable, yet the ticket says nothing is equivalent. | Specify that the fixture is a valid empty-user-password file (generated with a proper key), or add a P5 precondition that the library opens it with `""`. |
| R2-COR-9 | Major | 198 (R10, third named example), 300 (M-60) | "A footer under a line ending `infor-` is removed and the word joined on the first `clean`" gives no input or expected output. With c4 before c3, removing the footer leaves `infor-` with nothing to join. With c3 first, a lowercase footer such as `page 1` would be joined to the word. M-60's killer needs an exact input and output. | Write the exact before and after strings, or drop the example and name another killer. |
| R2-COR-10 | Minor | 280 (M-29), 221 (K10), 325 | M-29's only killer is K10, which is marked `perf`. The AK2a-1 tests command uses `-m "not perf"`. The mutation runner's marker handling is UNVERIFIED (line 382). | Add a non-perf depth-cap case to K1, or state that the mutation run uses `-m perf` for M-29. |
| R2-COR-11 | Minor | 229 (P6) | The allowed codes are `memory`, `too_many_chars` and `timeout`. Exhausting the address-space limit inside a C extension can also give a signal exit, which is `worker_crash`. | Add `worker_crash` to the allowed set, still never `done`. |
| R2-COR-12 | Minor | 159 | The result-size overhead of 1 MiB is justified "for 2,000 pages", but `KIT_MAX_PAGES` goes up to 100,000. At about 11 bytes per page that is about 1.1 MB, over the 1 MiB. A valid result would be cut off as `too_many_chars`. | Make the overhead `+ 16 * KIT_MAX_PAGES + 65,536`, or cap the pages. |
| R2-COR-13 | Minor | 157, 134, 121 | The `KIT_PDF_CHILD_ENV` default differs by platform (`()` vs `("SYSTEMROOT",)`). It goes into `settings_fp`, so the same bytes give different chunk ids on Windows and Linux. This contradicts "same bytes ... give the same ids". `**settings` on a pydantic model also needs `model_dump()`. | Leave `KIT_PDF_CHILD_ENV` out of `settings_fp`, or state the cross-OS limit. Say `model_dump`. |
| R2-COR-14 | Minor | 199 (R11), 349 (PL2), 361 (V6) | Revision 2 (R11, line 114, V6) is internally consistent on 3 cleaning passes and stacked headers. Three or more stacked header lines still change on pass 3 and go to a person. But R11 tests only five and two stacked lines, not the boundary of exactly three. The owner wording in PENDING LEAD 2 and the "Problem" paragraph do not mention that cost, only the short-PDF-page cost. | Add a three-stacked case, and make it consistent with a pass-3 "removed something" over-clean. Add one sentence to PL2 on repeated headers and placeholder-shaped text going to a person. |
| R2-COR-15 | Nit | 26 | `Detector` is cited at `:19-20` and `_SQUASH` at `:34`. Both are correct. In the same cite group `injection_check` runs to about `:99+`. | Cite `:85-99`. |

**Verified (read in code or ticket text):**
- `config.py:311-313` is `Settings`, with `config_dir` only. `:316-317` is `Config.environment: Literal["dev","pilot","prod"]`. The ticket's claim (line 414 and line 31) that `environment` sits on `Config` is correct.
- The AUTH-1 arithmetic holds: overlap 150 is below minimum 200, and 200 is below maximum 2,000. Revision 1's 200 against 200 would have been refused by the `>=` validator. The defaults are accepted. The bounds issue (R2-COR-3) is separate.
- AUTH-2 (the JSON header line on stdin) is coherent. It is three integers, with no newline inside the JSON. The worker reads at most 256 bytes, applies the limit, then imports the library, then reads the rest.
- Other cites that match the code:
  - `guard/injection.py:19-20, 23-35, 38-58, 44-48`. The `_SQUASH` and squashed-phrase behaviour is as described.
  - `models.py:23-24, 27, 38-43` (no `default=`, `ensure_ascii=False`) and `:46-47`.
  - `defaults.py:31-33, 38, 41-44`.
  - `llm/common.py:86-100`, with `:92` and `:89-90`.
  - `k1b/bundle.py:181-183`.
  - `tests/test_lockin_guard.py:38, 68-77, 298, 303`.
  - `pyproject.toml` base dependencies, the test group (`:52`), `S101` (`:81`), and the perf marker (`:89`).
  - `ci.yml:94` runs perf in its own step.
  - `uv.lock` has 0 `pytest-timeout` hits.
  - `test_defaults_live_in_one_module` is at `test_no_hardcoded_values.py:153`.
  - `test_licences_are_proprietary` is at `test_repo_rules.py:117`.
  - `src/hadavin_sdk/__init__.py` has a docstring and `__version__` only.
  - `tests/test_k5_producers.py` exists, and the `scan` group holds bandit.
  - `kit-plan-v2.md:44` and `:67`.
  - `tickets/AK1.md` lines 92, 97 and 119. `unreadable`, `low_quality` and `invalid_input` appear in AK1's text.
  - `tickets/P4b1.md` and `tickets/P1.md` hits are present, but I read only grep lines.
- `tests/fixtures` has no `.pdf` files.
- Counts, recounted by listing ids:
  - 54 test rows: R 23 (R1, R1b, R2-R5, R7-R16, R16b, R17-R22), K 10 (K1-K8, K10, K11), P 21 (P1-P6, P6b, P7, P7b, P7c, P8, P8b-d, P9-P15).
  - 69 mutants: 49 in AK2a-1 (M-1 to M-29, M-31, M-32, M-43 to M-60) and 20 in AK2a-2 (M-33 to M-42, M-61 to M-70).
  - Every mutant names a killer row that exists. Apart from the cases in R2-COR-8, R2-COR-9 and R2-COR-10, each killer plausibly kills its mutant (M-3, M-6, M-11, M-33, M-38, M-42 and M-55 were traced by hand).
  - 11 INFORM (I1-I11), 4 PENDING LEAD, and V1-V16.
- The 17 template fields are all present in the template's order (lines 3-19 of the template map to the ticket's field bullets).
- The quality codes number 16: 1 ok, 5 poor and 10 unreadable. The ticket's list matches.
- `AK1.md:119` ("Escaping ... AK2a's reader and chunker") conflicts with I7. PENDING LEAD 4 correctly flags this.

**Not checked (UNVERIFIED):**
- `LEAD-ORDERS.md` (the order 20, 23 and 27 items quoted).
- `amendments.md` A9 F3 and F6 (only the grep hits for A9).
- The two round-1 reports, which I was told not to read, and the resolve file.
- `kit-plan-v2.md:37` and `:54`.
- `owner-visible-limits.md` entries (only the header).
- `AK1.md` lines 94, 96, 99, 110, 114, 159 and 294 beyond grep fragments. Those lines are over-long, so I only saw fragments.
- `AK0.md` D1, J1 and PENDING LEAD 1-7, and the `P1.md:72` mutation-runner cite beyond the grep hit.
- `tests/test_repo_rules.py` lines 167, 305 and 401 (they land on test functions, but whether they accept a new `ingest/` package is not checked).
- Behaviours that need a running build:
  - the `-I -m` child importing the installed package;
  - whether `ruff S603` is silent;
  - the RLIMIT values;
  - whether a hand-built PDF is accepted;
  - K10 timings.
- The AK2a-2 PDF library facts. AK0 has not named the library.