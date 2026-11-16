# P5a round 1 disposition: ticket revision 1 to revision 2

Written 2026-11-06 about 02:45 UTC (08:15 IST) by the ticket-revision agent (Sonnet 5.5). Input: `P5a-round1-resolve.md` (the decisions), `P5a-round1-adversarial.md` (ADV-A1..A16) and `P5a-round1-correctness.md` (COR-C1..C11). Output: `handover/tickets/P5a.md` revision 2. Text only.

Result: 27 findings, 27 applied (5 of them narrowed exactly as the resolve narrowed them), 0 contested, 0 declined. Each ticket location below is a field name or section of revision 2.

Re-verification of cites: I read each cite that revision 2 keeps against `src/` (equal to `ce70eb5`; `git diff --stat ce70eb5 HEAD -- src tests` is empty). Confirmed by reading: the 22 class positions, `extract.py:58`, `tick.py` lines 284/289/292/316/317/324/335, `injection.py:96`, `cli.py:75/205/301/304`, `runmap.py` lines 38/42/53/417/485, `tools.py` raise sites 503-601/521/620/1030/1130/1137/1148/1150/1180, `llm/protocol.py:10-14`, `store/protocol.py:25/29/41/45`, `llm/fake.py:47`, the four foreign `ConfigError` sites, `ci.yml:42/88/94`, `pyproject.toml` pins, `tests/test_lockin_guard.py` lines 69-71 and 520. Probed with `python -I` on the project `.venv` (scratch, not evidence): pydantic 2.14.1 `loc` for a discriminated union and a `RootModel[dict]`; `ErrorType` has 111 names; psycopg 3.3.6 IS installed in the `.venv` (revision 1 said it was not, because it probed the system Python): `InvalidPassword.sqlstate == "28P01"`, a refused connection has `sqlstate None` and no cause. NOT re-read, marked UNVERIFIED in the ticket: `guard/producers.py` rows, `tickets/P2a.md` class names, `tests/test_repo_rules.py` and `tests/test_no_reference_material.py` names, `k1b/diagnosis.py`, the P1b `scan_keyset` substring reading, the `Mutant` signature, every estimate.

Two facts that changed the ticket beyond the resolve (found while re-verifying): (1) P1 is now FROZEN at revision 16, which cut `scan_hit`, `line_view` and `id_key`; the oracle is rewritten on `scan_keyset` with a local fallback (ADV-A7 row). (2) `pyproject.toml` pins `pydantic==2.14.1` exactly, so the "lowest and highest pydantic" run (ADV-A11) cannot exist; the ticket says so and adds a v1.1 row.

| id | sev | outcome | revision 2 location |
|---|---|---|---|
| ADV-A1 | BLOCKER | applied (cut) | "What revision 2 changed"; Interface (no `detail`, config error = `code=config_invalid` + closed facts); Security notes (a); corpus class `config_detail` 10 to 4 (name must NOT leak); table row "detail, t1, safe_value" |
| ADV-A2 | BLOCKER | applied, narrowed (SlackError/SourceError keep `provider_http`) | Interface `OWN_CODES` (nested key `module:Outer.Inner`, rename rule, `NOT_SCANNABLE`); Tests `test_every_own_exception_class_resolves_to_a_code` (AST, never an import, nothing skipped), `test_every_row_key_is_found_by_the_scan`; Decisions 14; table row `external_http` |
| ADV-A3 | MAJOR | applied, narrowed | Interface (`phase` = sqlstate class only); T3-T5 golden (frozen only from real output, else UNVERIFIED); table row "phase beyond sqlstate" |
| ADV-A4 | MAJOR | applied | Interface "Locator and library frame" (innermost 32 of at most 2000 links, `realpath`/`normcase`, `type(name) is str`); `test_locator_on_installed_layout`; Evidence (wheel run, else UNVERIFIED); Security notes (realpath reads metadata) |
| ADV-A5 | MAJOR | applied, narrowed (frozen allow-list, no dynamic list) | Interface "Kind and chain identity" (`FOREIGN_PACKAGES_OK`); corpus class `foreign_name` 3; mutant in Appendix B |
| ADV-A6 | MAJOR | applied | Tests "The checker, split in two"; `test_every_active_row_has_teeth` (read-path subjects: notes, filename, doc, msg, `repr(e.args)`, `format_exception`); `hostile_class` canary in every attribute; `test_reverse_check_fails_90_percent` as a hard gate |
| ADV-A7 | MAJOR | applied | Depends on (P1a, P1b, P1m only; names frozen against P1 revision 16; no P1c text anywhere); `OWN_CODES` note; local fallback oracle `leaks_literal`; evidence runner re-checks the names |
| ADV-A8 | MAJOR | applied (cut) | "What revision 2 changed"; Interface (kept: `Code`, `OWN_CODES`, `diagnose`, `render` Grammar A, `validation_text`, `class_name_of`, `SafeToken`, corpus, `CORPUS_STEP`); "Later and v1.1 rows"; Package id (one PR) |
| ADV-A9 | MAJOR | applied | Interface (rows P5c and P5b1 add are named and moved to those tickets; P1c class names dropped); Files "Hot files" (`codes.py` hot for P5a, P5b1, P5b3, P5c; `errors.py` claim corrected, cite A9 F6); table row `FactKey.reason`; Decisions 1, 10, 15 |
| ADV-A10 | MAJOR | applied (superseded by the cut) | `safe_value` deleted; table row records the fixed order (type, 1 MiB length cap, charset, redactor) and the pin rows for the day it returns |
| ADV-A11 | MAJOR | applied, narrowed | Interface `validation_text` (closed fixed text only; no `loc`); two canary rows (discriminated union, `RootModel[dict]` key) in `pydantic_input` and `test_union_tag_and_rootmodel_dict_key_never_shown`; one pydantic version only (exact pin), v1.1 row |
| ADV-A12 | MAJOR | applied | Interface `diagnose` (`Exception` only; a `BaseException` from a hostile `__getattr__` propagates by design); `test_baseexception_from_hostile_getattr_propagates`; `hostile_class` row |
| ADV-A13 | MAJOR | applied | Tests "The FAIL-BEFORE test": real `extract.extract` and `runtime.tick.run_tick` (public paths), no hand-written shim; worktree stated; collection must succeed first |
| ADV-A14 | MINOR | applied (budget dropped, bounds asserted) | Constants (13; `DIAG_TIME_BUDGET_S` and `DIAG_MAX_B_CHARS` removed; `DIAG_TB_STEPS` 2000 and `DIAG_MAX_FRAMES` 32 named with a reason); `size_time` rows assert counters, no `perf` marker |
| ADV-A15 | NIT | applied, narrowed (no new rows) | Corpus "minimums per mechanism"; `fact_bounds` class cut (duplicates `test_facts_bounds_table`); unique-`(factory,args)` meta-test allows a `variant_of=` row |
| ADV-A16 | NIT | applied | "Existing core code reused" (`k1b/redaction`, `k1b/atomic`, `stats` read and listed as not reusable); ledger mapping moved to Appendix A, mutants to Appendix B |
| COR-C1 | MAJOR | applied | Fail-before worktree = `ce70eb5` + P1a/P1b files + real `codes.py`; acceptance check on collection |
| COR-C2 | MAJOR | applied | `grammar_ok` and `leaks` split; teeth, fail-before and reverse check assert on `leaks()` alone; `validation_text` grammar `V` defined; expected passes on today's code restated |
| COR-C3 | MAJOR | applied | `RecursionError, MemoryError` removed from the `diagnose` spec; equivalent mutant deleted (Appendix B) |
| COR-C4 | MINOR | applied | Depends on and "Existing core code reused": P1m is a hard dependency of the mutation run; the files are not existing code |
| COR-C5 | MINOR | applied | `Code` rationale reworded: all `ToolRefused` map to `tool_refused`; the raise sites listed (verified); `test_all_toolrefused_sites_map_to_tool_refused` |
| COR-C6 | MINOR | applied | T10 reason corrected (pytest puts the test file in `sys.modules`; only `locator` is `-`); `type(name) is str` rule and a non-`str` `__name__` row |
| COR-C7 | MINOR | applied | Same edit as ADV-A7: P1c class names and waiting text deleted |
| COR-C8 | MINOR | applied | Killer tests listed with content in Tests; killers that go with cut features removed; Appendix B |
| COR-C9 | MINOR | applied | T8 uses a hand-built `socket.gaierror(-2, "x")` and asserts `code=os_error` plus an in-range `gai` (a probe gave -2 on Linux here; no resolver can give -3) |
| COR-C10 | MINOR | applied | Tick cites corrected and re-read: `:292` the `_message` producer, writers `:316`, `:317`, `:324` |
| COR-C11 | NIT | applied | `errors.py` hot-file claim corrected with cite F6; step names now include `purge_evidence` and `reprobe_sources` (`tick.py:249-263`); `ansi_c1` minimum 7 for 7 items. The `llm/fake.py:47` item: re-read, `raise UnknownRecording(path.name)` prints a recording file name, so `UnknownRecording` stays `config_invalid` and nothing is printed from it (no text is printed at all) |

## Counts, old to new
- Findings: 27 (2 blockers, 14 majors, 8 minors, 3 nits); applied 27, contested 0, declined 0.
- Resolve open points: 15 (13 from revision 1 plus 2 new); all taken as the resolve recommends. PENDING LEAD items 13 to 15 (items 14 and 15 are new: `external_http` split with a v1.1 row; P5b1 owns the `guard/diagnostic.py` follow-on).
- Hostile rows: 169 (151 active, 16 later, 2 not applicable) to 158 (140 active, 16 later, 2 not applicable): `fact_bounds` -12, `config_detail` -6, `ansi_c1` +1, `hostile_class` +2, `locator_frames` +1, `foreign_name` +3.
- Source files to create: 4 to 2 (`t1.py` and `diagnostic_schema.py` cut). Test files: 7 to 7 (`test_diagnostic_schema.py` becomes `test_diagnostic_validation.py`).
- `defaults.py` constants: 16 to 13. `Code` members: 21 to 21. `FactKey`: 20 to 20.
- Cut items with a later-package row: 12 rows in "Later and v1.1 rows".
- Ticket length: 132 lines to 153 lines (the lines are shorter in count but the cut text is replaced by appendices and the table; no size claim beyond that).

## Honest notes
- I did not run any test, suite or evidence; every cite I kept was read, the rest is marked UNVERIFIED in the ticket.
- Revision 1's claim "psycopg is not installed in this environment" was wrong for the project `.venv` (3.3.6 is there); the system `python3` lacks it. I corrected the ticket and still left the golden lines to the evidence runner.
- The oracle's substring reading of P1b key-sets is my reading of a frozen ticket, not of code. If P1b's contract differs, the fallback oracle keeps the corpus usable and the evidence runner reports which oracle ran.
- Nothing here needed the owner. No conflict between the resolve and the orders was found (orders 16, 17 and 20 item 3 change how many review rounds and when a build-start review happens; the Done line now defers to them instead of restating the withdrawn "two clean rounds" rule).
