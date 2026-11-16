# P5a round 3 resolve report (egm:egm-resolve logic)

Status: resolved (categorised; ticket NOT edited here). **No round 4.** Round 3 found 0 Blockers and 6 Majors (R3-ADV-1..5, R3-COR-1), so order 20 item 6 (one more round only if the last round has no Blocker and at most 2 Majors) does not allow a fourth round. Revision 3 freezes. Every fix below goes into a new last section of revision 3, "Build notes (build-start review, order 20)", plus a banner under the ticket's status line. The next step is the one build-start review of order 19 A / order 20 item 3; its defects also go into the build notes, not into a revision 4.
Target: `tickets/P5a.md` revision 3 (241 lines, read in full). Inputs: `reviews/P5a-round3-adversarial.md` (R3-ADV-1..14: 5 Major, 7 Minor, 2 Nit) and `reviews/P5a-round3-correctness.md` (R3-COR-1..9: 1 Major, 5 Minor, 3 Nit). Layout copied from `reviews/P5a-round2-resolve.md`. I merged ADV-2 with COR-2 (same defect: strict xfail without `raises=`) and ADV-3 with ADV-12 (one changed row closes both).
Gate: AUTO mode. The skill's interactive gate and its `goldfish_review_report.md` are replaced by this file. Nothing is escalated to the owner. New open points are PENDING LEAD 25-30 below, each with one recommendation. Under order 6(g) the recommended answers are final unless the lead replies. The lead may reverse PL25 (R3-ADV-1) at any time; the build note says what changes if it does.

Facts I checked myself (2026-11-06, this worktree, project `.venv`, `python -I`, scratch probes only, not evidence):
- **Installed libraries:** `site-packages` holds `anthropic` 2.1.0, `botocore` 1.43.122, `urllib3` 2.8.0, `psycopg` 3.3.6 and `pydantic_core` 2.50.1. It does NOT hold `openai`, `sqlalchemy` or `httpx`. There is an `httpx2` 2.16.0, which `anthropic` requires (`httpx2<3,>=2.0.0`); it is not `httpx`. `pyproject.toml` extras are `anthropic, aws, signer, pg, askdata, azure, gcp`. No extra installs `openai`, `sqlalchemy` or `httpx`. This confirms R3-COR-1.
- **pydantic:** `class R(pydantic_core.ValidationError): pass` works. `R.from_exception_data("t", [{"type": "missing", "loc": ("a",), "input": {}}])` returns an `R`. So R3-ADV-4's premise ("probably not subclassable") is wrong. Its conclusion still holds: no killer was decided, and the AST test is the cheaper and surer one (decision below).
- **Traceback:** a chain of 2001 `types.TracebackType(tb_next, frame, 0, 1)` links can be built by hand (counted 2001). This closes R3-COR-6.
- **`co_filename`:** `code.replace(co_filename=v)` raises `TypeError` for `int`, `bytes` and `None`. A frame with a non-`str` `co_filename` cannot be built this way, so the `type(co_filename) is str` check has no killer (R3-COR-9).
- **Attribute that `diagnose` reads on every platform:** an `OSError` subclass with an `errno` property that raises `KeyboardInterrupt` shadows the built-in attribute. `getattr(e, "errno", None)` does not swallow it. On Linux `OSError(1, "x")` has no `winerror`, so revision 3's `__getattr__` row depends on the platform (R3-ADV-12 holds).
- **Code read:**
  - `runtime/tick.py:289`: `_message` calls `type(exc).__module__.split(".")`, and `:292` calls `str(exc)`. Both run inside the `except` handler at `:315-317`, outside any `try`. `run_tick` calls `_run_step` unguarded (about `:352`). So a hostile exception can crash `run_tick` (R3-COR-2 holds; read, not run).
  - `config.py:50-52`: `_Strict` is at line 50 and its `model_config` (`extra="forbid"`) at 52 (R3-COR-7 holds).
  - `tests/test_p7_tick.py:36` defines the `app` fixture inside that test module. `live_cfg_dir` and `fake_system` are in `tests/conftest.py:79, :89`. So a new test file cannot simply reuse `app`; it needs its own fixture.
  - `tests/test_lockin_guard.py:21, :118, :599`: the guard scans `src/` only. Vendor names in `tests/` are not checked by rule c, and `openai`/`httpx`/`sqlalchemy` already appear in five test files.
- **Lead orders read:** `LEAD-ORDERS.md` orders 7(1), 8(1), 19 A, 20 items 3 and 6, 21 item 17.

Honest note (what I did NOT check):
- I ran no repository test and wrote no code. I did not re-run the revision 3 probes (`FALLBACK_FP`, T10 `fp`, psycopg sqlstates).
- I did not measure the cost of `errors()` on a large `ValidationError` (R3-ADV-10). The decision there is an argument, not a measurement.
- Not checked:
  - whether `tests/test_repo_rules.py` accepts hand-built classes whose `__module__` is `"openai"` or `"sqlalchemy"` in `tests/data/` (likely, since five test files already use those strings; UNVERIFIED);
  - the P5b1 and P5b3 tickets beyond what revision 3 cites.
- Two of the reviewers' suggested fixes are wrong as written, and I wrote different ones:
  - R3-ADV-12's alternative, "use `exc.exceptions` of a group subclass": `exceptions` is a class attribute, so `__getattr__` is never reached.
  - R3-ADV-3's "wrap the subjects in `except BaseException`": catching `KeyboardInterrupt` in a test helper is worse than leaving the row out of those tests.
- Five Majors are real. R3-ADV-1 was the author's own open point (PENDING LEAD 24), written the other way round from its recommendation.
- Six findings are closed by cutting surface (order 7(3), order 8(1)): the `chain` rows, the `TypeError` raise, the fallback oracle swap, the `ToolRefused` sites test, `SafeToken.shape`'s `name` parameter, and the NUL row.

| id(s) | category | decision (build note) |
|---|---|---|
| R3-ADV-1 (Major) | PROPOSE FIX (cut) | Option (b) of PENDING LEAD 24 is written as a build note. The 3 `chain` later rows leave the corpus. The v1.1 row "cause chain kinds..." names owner **none**. Later 27 to 24; with this change alone the total is 163 to 160 (other notes change it again, see BN-15). P5b1 builds no cause chain. The lead may reverse it (PL25); then BN-1 is struck out and the rows return with `owner_step="R1P"`. BN-1. |
| R3-ADV-2 + R3-COR-2 (Major/Minor) | PROPOSE FIX | Every mark becomes `xfail(strict=True, raises=AssertionError, reason=...)`. The adapter builds the row's exception BEFORE `run_tick` (so a factory error is a plain error) and checks that the writer ran before checking for a leak; that check raises `AdapterError(RuntimeError)`, which `raises=AssertionError` does not accept, so the row FAILS. A writer crash that escapes `run_tick` is its own outcome `crashed`, pinned by type name in `OLD_WRITER_CRASHES`. The new file defines its own `app` fixture the way `test_p7_tick.py:36` does, from conftest's `live_cfg_dir` and `fake_system`. BN-2. |
| R3-ADV-3 + R3-ADV-12 (Major/Minor) | PROPOSE FIX | The `BaseException` row becomes a platform-free form: an `OSError` subclass whose `errno` property raises `KeyboardInterrupt` (probed). It gets the new `expect="propagates"` and is listed in a frozen `PROPAGATES_ROWS`. It leaves `test_active_rows_hold_on_new_code`, the teeth test, the reverse check and the superset test, and is run only by the renamed `test_baseexception_from_hostile_attribute_propagates`. Every other teeth subject runs in `try/except Exception` (a subject that raises gives `""`). No test helper catches `BaseException`. BN-3. |
| R3-ADV-4 (Major) | PROPOSE FIX (premise contested) | The killer is an AST test, `test_pydantic_error_reads_are_closed_ast`, on one helper `_error_types(exc)` that is the only caller of `.errors(` and `.error_count(` in `guard/diagnostic.py`. The probe shows a recording subclass IS possible, but it is not required. BN-4. |
| R3-ADV-5 (Major) | PROPOSE FIX | Own-class identity rule for the kind: a bare qualname is printed only if the class passes rule 1's identity walk, its module is `hadavin_sdk` or under it, and the text matches `^[A-Za-z0-9_.]{1,80}$`; otherwise `dynamic_class`. Add an `own_class_spoof` golden row (`own_module_dynamic_kind`): `type("Jane_Doe_Invoice", (ConfigError,), {"__module__": "hadavin_sdk.errors"})` gives kind `dynamic_class` and `code=config_invalid` (its real base). Plus a mutant and killer. BN-5. |
| R3-COR-1 (Major) | PROPOSE FIX (split) | `foreign_driver` 8 rows = 5 REAL classes (`psycopg.errors`, `urllib3`, `botocore`, `anthropic`, `pydantic_core`; all installed by `--all-extras` or the base, probed) + 3 HAND-BUILT classes for `httpx`, `openai` and `sqlalchemy`, labelled "not the real class" in `why`, which give kind `dynamic_class`. Only the 5 real rows fall under "a skip is a failed evidence run"; the 3 hand-built rows never skip. No new dependency. BN-6. |
| R3-ADV-6 (Minor) | PROPOSE FIX (cut) | Remove the only raise: a caller `facts=` value of the wrong type is DROPPED silently, like an out-of-bounds value. `diagnose` then never raises an `Exception`, so P5b3 can call it inside `except` handlers without a wrapper. `test_facts_bounds_table` asserts "dropped" where it asserted `TypeError`. PL26. BN-7. |
| R3-ADV-7 (Minor) | PROPOSE FIX (cut) | Cut the fallback swap. If `scan_keyset` cannot be imported, collection fails, locally and in CI. `leaks_literal` stays only as the lower bound in `test_strict_oracle_is_a_superset`. Cut `test_fallback_oracle_agrees_on_plain_canaries` and "the run prints which oracle ran". PL29. BN-8. |
| R3-ADV-8 (Minor) | PROPOSE FIX | Name the closed sets in `codes.py`: `Phase(StrEnum)` = `auth, connect, query, unknown`; `VALIDATION_TYPES: Final[frozenset[str]]` = the 26 names; `VALIDATION_OTHER: Final = "other"`. `Fact = int \| bool \| ProviderErrorType \| Phase \| SafeToken`. Two literal tests. BN-9. |
| R3-ADV-9 (Minor) | PROPOSE FIX (cut) | Delete `test_all_toolrefused_sites_map_to_tool_refused`; `test_pinned_code_per_class` pins the one row. The `tools.py` line cites stay informative. BN-10. |
| R3-ADV-10 (Minor) | PROPOSE FIX (statement, no row) | Accept the cost, with the reason written in: a `ValidationError` with n line errors already holds n entries, built during validation. `errors()` copies them at the same order of cost. `diagnose` and `validation_text` read at most 5 entries plus `error_count()`. No new row; UNVERIFIED (not measured). BN-11. |
| R3-ADV-11 (Minor) | PROPOSE FIX | Rows that run code in a real own module's namespace use the fixed module `hadavin_sdk.stats`, define only names starting `_p5a_probe_`, and delete them in `finally`. A meta-test checks that `vars(hadavin_sdk.stats)` has the same keys before and after the `locator_frames` rows. The `__name__` swap is restored in `finally`. BN-12. |
| R3-ADV-13 (Nit) | PROPOSE FIX | Replacement text for "Problem in plain words", 5 sentences. BN-13. |
| R3-ADV-14 (Nit) | PROPOSE FIX (cut) | `SafeToken.shape(value, name)` becomes `SafeToken.sqlstate(value)`. BN-14. |
| R3-COR-4 (Minor) | PROPOSE FIX | Align each class minimum with its list: `hostile_class` 14 to 16, `secret_shapes` 8 to 6, `pii_encoded` 8 to 9 (the 9 named). With BN-1, BN-5 and BN-16: active 134 to **135**, later 27 to **24**, not applicable 2, total **161**. The meta-test computes the sum; the numbers in the text are informative. BN-15. |
| R3-COR-3 (Minor) | PROPOSE FIX | Add `test_fact_priority_order_is_the_d9_literal` (the 20 names as one literal tuple) and the mutant "two adjacent `FACT_PRIORITY` keys swapped". BN-17. |
| R3-COR-5 (Minor) | PROPOSE FIX | Wording: more than `DIAG_TB_STEPS` (2000) links gives `at=-` and `foreign_exception`; 33 to 2000 links keeps the innermost 32 frames and has a locator. BN-18. |
| R3-COR-6 (Minor) | PROPOSE FIX | The long-traceback case is a hand-built chain of 2001 `types.TracebackType` links (probed). BN-18. |
| R3-COR-7 (Nit) | PROPOSE FIX | `config.py:52` becomes `config.py:50-52` (verified). BN-19. |
| R3-COR-8 (Nit) | PROPOSE FIX | One sentence: a group's facts are those read from the group itself (none in P5a), never its member's. BN-19. |
| R3-COR-9 (Nit) | PROPOSE FIX (cut) | Cut the NUL `co_filename` row (it guarded the NUL raise that the `realpath` cut removed). Add the `type(co_filename) is str` check to "Equivalent, stated and not run" (probe: `code.replace` refuses a non-`str` `co_filename`). `locator_frames` 11 to 10. BN-16. |

## Banner (exact text, one line directly under the ticket's line 3)
> **BUILD NOTES WIN.** Revision 3 is FROZEN after round 3 (0 Blockers, 6 Majors; order 20 item 6 allows no round 4). The section "Build notes (build-start review, order 20)" at the end of this ticket replaces any text above that it names. Where a build note and the text above disagree, the build note is right. Source: `reviews/P5a-round3-resolve.md`.

## Build notes (exact text of the new last section of revision 3)
The ticket gets a new section headed `## Build notes (build-start review, order 20)`, opened by: "Written from `reviews/P5a-round3-resolve.md`. Each note says what it replaces. The build-start review (order 19 A) appends its own notes below these, numbered on." Then:

- **BN-1 (R3-ADV-1; PENDING LEAD 24 answered (b), PL25).** Replaces: the `chain` part of line 146, the `chain` sentence in line 148, the v1.1 row "Cause chain kinds..." (line 185), the P5b1 coupling sentence on the chain (line 170) and the changelog totals. New text:
  - Line 146 later list: "**Later (24; ...):** `ast_taint` 6 (kind `source`, owner R3c), `logging_layer` 5 (kind `scenario`, owner R2), `writer_wiring` 3 (kind `scenario`, owner R3c), `classification` 2 (kind `source`, owner R3a), `provider_attrs` 8 (kind `exception`, owner R1P: P5b1 activates them by id and rewrites their `spec` to its factories). There is no `chain` class: the cause chain is cut, and no package owns it in v1."
  - Line 148: "16 of the 51 ledger rows, plus 8 design rows (`provider_attrs`), have an input recorded..."
  - v1.1 row: "| Cause chain kinds and facts merged from causes (`cause_kind`, the design's T3 `phase=connect` from a wrapped `OSError`, `lib_frame`) | none (both the P5a and the P5b1 resolves cut it; PENDING LEAD 24 answered (b)) | an operator needs the underlying cause kind |"
  - Couplings, P5b1: "The cause chain, `cause_kind` and any chain rows are NOT P5b1's: PENDING LEAD 24 was answered (b). `cause_kind` stays a `FactKey` member with no producer."
  - If the lead reverses PL25: strike BN-1; the 3 rows return with `owner_step="R1P"`; later becomes 27 and the total in BN-15 becomes 164.
- **BN-2 (R3-ADV-2, R3-COR-2).** Replaces line 120 (adapter table) and the "Marks" bullet (line 121). New text:
  - "**Adapter (exception rows).** The test builds the row's exception FIRST, outside `run_tick` (`e = FACTORIES[f](*args)`; a factory error is a plain test error). It then calls `run_tick(app, now, steps=[TickStep("x", 0, fn)])`, where `fn` only does `raise e`. `app` is a fixture defined in this file the same way `tests/test_p7_tick.py:36` defines it, from `live_cfg_dir` and `fake_system` (`tests/conftest.py:79, :89`).
  - "**Outcome.** The adapter returns one of four outcomes:
    - `crashed`, if an exception escapes `run_tick`. Today `_message` (`tick.py:289`, `:292`) runs inside the step handler outside any `try`, so a non-`str` `__module__` or a raising `__str__` can escape.
    - `leaked`, if the writer ran and `leaks(...)` is True on `tick_state.last_error` or on the log record.
    - `clean`, if the writer ran and nothing leaked.
    - `no_path`, for `validation` rows listed in `NO_OLD_WRITER_PATH`.
  - "**Writer-ran check.** Before any leak check, the adapter requires that `tick_state.last_error` for step `x` is a non-empty `str` and that one log record with `step=x` exists. Otherwise it raises `AdapterError(RuntimeError)`, defined in this file.
  - "**Marks.** Each row asserts `outcome == "clean"`. A row in `OLD_WRITER_LEAKS` or in `OLD_WRITER_CRASHES` gets `pytest.mark.xfail(strict=True, raises=AssertionError, reason="later: R3c (P5b3) wires the writers; outcome=<leaked|crashed>")` and names its `writer_wiring` row by id. `AdapterError` and any other non-`AssertionError` make the row FAIL, never XFAIL.
  - "**Crash pin.** `OLD_WRITER_CRASHES: Final[Mapping[str, str]]` maps a row id to the exception type name that escapes `run_tick`. The adapter checks that the escaping type equals the listed one, and raises `AdapterError` otherwise.
  - "**Who fills the lists.** The evidence run fills both lists, `OLD_WRITER_LEAKS` and `OLD_WRITER_CRASHES`. Done (line 166) also requires `OLD_WRITER_CRASHES` to be empty at P8b."
- **BN-3 (R3-ADV-3, R3-ADV-12).** Replaces the last item of the `hostile_class` list (line 146), the test at line 97, the `Row.expect` Literal (line 139), and the Appendix B line "`diagnose` catches `BaseException`". New text:
  - `Row.expect: Literal["no_canary", "grammar", "bounded", "golden", "propagates"]`.
  - Corpus row: "an `OSError` subclass whose `errno` is a property that raises `KeyboardInterrupt` (`diagnose` reads `errno` on every platform), `expect="propagates"`; its id is the only member of the frozen tuple `PROPAGATES_ROWS`."
  - Tests: "`test_baseexception_from_hostile_attribute_propagates`: an `OSError` subclass whose `errno` property raises `KeyboardInterrupt`, `GeneratorExit` or `asyncio.CancelledError` lets that `BaseException` propagate out of `diagnose` (checked with `pytest.raises(<that class>)`). The same property raising `ValueError` gives the fixed fallback. It also runs every row in `PROPAGATES_ROWS`."
  - Exclusions: "Rows with `expect="propagates"` are excluded, by the field, from `test_active_rows_hold_on_new_code`, `test_every_active_row_has_teeth`, `test_reverse_check_fails_90_percent` (both numerator and denominator) and `test_strict_oracle_is_a_superset`. A meta-test fails if the set of such rows differs from `PROPAGATES_ROWS`. The teeth exemption cap (15) counts only `bounded` and `grammar` rows."
  - Teeth subjects: "Each teeth subject is evaluated inside `try/except Exception`; a subject that raises gives `""` for that subject. No test helper catches `BaseException`."
  - Appendix B: "`diagnose` catches `BaseException`: `test_baseexception_from_hostile_attribute_propagates`."
- **BN-4 (R3-ADV-4).** Replaces line 106 and the Appendix B entry "pydantic `errors()` called with an `include_*` left True...". New text:
  - "`guard/diagnostic.py` has ONE helper, `_error_types(exc) -> tuple[int, tuple[str, ...]]`, which returns `error_count()` and the first `DIAG_MAX_ERRORS` `"type"` values. `diagnose` and `validation_text` both use it.
  - "**`test_pydantic_error_reads_are_closed_ast`** (the killer) parses `guard/diagnostic.py` and fails unless all of the following hold:
    - (1) `.errors(` and `.error_count(` are called only inside `_error_types`;
    - (2) each `.errors(` call has no positional argument and no `**`, and has exactly the keywords `include_url`, `include_context` and `include_input`, each `ast.Constant(False)`;
    - (3) the result of `.errors(` is bound to one name, which is used only in a slice with constant bounds or as the iterable of one `for`;
    - (4) each entry is used only as `entry["type"]` (an `ast.Subscript` whose slice is `ast.Constant("type")`): no `.get`, no other key, no `**`, no passing the entry to a call.
  - "A recording subclass of `pydantic_core.ValidationError` is possible (probed: subclassing and `from_exception_data` work) but is not required."
  - Appendix B: "`include_*` left True, a key other than `"type"` read, or `.errors(` called outside the helper: `test_pydantic_error_reads_are_closed_ast`."
- **BN-5 (R3-ADV-5).** Replaces the first clause of line 74 ("own classes print the bare qualname"). New text:
  - "An own class prints its bare qualname only if all three hold:
    - (a) it passes rule 1's identity walk (the object reached by walking `sys.modules[cls.__module__].__dict__` along the qualname is the class itself, with the `type(name) is str` checks first);
    - (b) its module is `hadavin_sdk` or starts with `hadavin_sdk.`;
    - (c) the qualname matches `^[A-Za-z0-9_.]{1,80}$`.
  - "Otherwise the kind is `dynamic_class`. The code still comes from rule 1's MRO walk, so a dynamic subclass of a real own class keeps its base's code."
  - New `own_class_spoof` row (golden), `own_module_dynamic_kind`: `type("Jane_Doe_Invoice", (ConfigError,), {"__module__": "hadavin_sdk.errors"})` = `dynamic_class: diag_v=1 code=config_invalid step=other at=- fp=<8 hex>`; the canary is `Jane_Doe`.
  - Appendix B: "Own-kind identity check removed (bare qualname printed for any class whose `__module__` starts with `hadavin_sdk`): the `own_module_dynamic_kind` golden row."
- **BN-6 (R3-COR-1).** Replaces the `foreign_driver` item in line 146 and the parenthesis "(a skipped T4, T5 or `foreign_driver` row is a FAILED evidence run...)" in line 164. New text:
  - "`foreign_driver` 8: 5 REAL classes, raised with a host and a user in the message: `psycopg.errors.OperationalError` (`pg` extra), `urllib3.exceptions.NewConnectionError` (installed with `botocore`, `aws` extra), `botocore.exceptions.EndpointConnectionError` (`aws` extra), `anthropic.APIConnectionError` (`anthropic` extra), and a `pydantic_core` `ValidationError` (base). Plus 3 HAND-BUILT classes, made in the corpus module with `__module__` set to `"httpx"`, `"openai"` and `"sqlalchemy.exc"`, each with `why` starting "not the real class:". No extra installs those libraries, and P5a adds no dependency.
  - "The hand-built rows expect kind `dynamic_class` (identity test (a) fails) and no canary."
  - "Line 164: (a skipped T4 or T5, or a skipped REAL `foreign_driver` row, is a FAILED evidence run under `--all-extras`; the 3 hand-built rows never skip)."
  - The real class names are informative (probed: `anthropic.APIConnectionError` and `botocore.exceptions` import). The builder may pick another class of the same library and records the pick.
- **BN-7 (R3-ADV-6, PL26).** Replaces line 60 and the `TypeError` parts of lines 99 and 235. New text:
  - "`facts=`: a value of the wrong type for its key (a `str`, a `str` subclass that is not a member of the expected enum, a `bool` for a number key, a `float`) is DROPPED silently, exactly like a value out of bounds. `diagnose` never raises an `Exception`; only a non-`Exception` `BaseException` raised inside it propagates."
  - `test_facts_bounds_table`: "...a `bool` for a number key and a `str` fact are dropped (no `TypeError`)."
  - Appendix B: "`bool` accepted as a number, `str` fact accepted...: `test_facts_bounds_table` (the fact must be absent)."
- **BN-8 (R3-ADV-7, PL29).** Replaces the "Local fallback" sentences in line 145 and "(or of the fallback fold)". New text:
  - "`leaks_literal(output, canaries)` (NFKD, case fold, letters and digits only, plain substring; standard library only) is used ONLY as the lower bound in `test_strict_oracle_is_a_superset`. It never replaces `leaks()`. If `scan_keyset` cannot be imported, collecting `tests/data/c18a_oracle.py` fails, locally and in CI (P1b is a hard dependency)."
  - Cut: `test_fallback_oracle_agrees_on_plain_canaries`, "the run prints which oracle ran", and the evidence item "which oracle ran".
  - `test_canaries_are_long_enough` checks the keys of `scan_keyset(canary)` only.
- **BN-9 (R3-ADV-8).** Adds to the `codes.py` Interface:
  - "`Phase(StrEnum)`: `auth, connect, query, unknown` (the `phase` fact).
  - "`VALIDATION_TYPES: Final[frozenset[str]]`: the 26 closed names of `validation_text`. `VALIDATION_OTHER: Final = "other"`. The `type` fact is `SafeToken.of(v, VALIDATION_TYPES)`, or `SafeToken.of(VALIDATION_OTHER, frozenset({VALIDATION_OTHER}))` when that returns `None`.
  - "`Fact = int | bool | ProviderErrorType | Phase | SafeToken`."
  - Tests in `tests/test_diagnostic_codes.py`: `test_phase_is_the_frozen_list` and `test_validation_types_are_the_frozen_list` (literals). The `ErrorType` subset test reads `VALIDATION_TYPES`.
- **BN-10 (R3-ADV-9).** Delete `test_all_toolrefused_sites_map_to_tool_refused` from line 93. The `ToolRefused` row is pinned by `test_pinned_code_per_class`. The `tools.py` line cites in line 43 are informative.
- **BN-11 (R3-ADV-10).** Add to line 77: "Cost of a huge `ValidationError`: accepted. The exception already holds its n line errors, built during validation, and `errors()` copies them at the same order of cost. `_error_types` reads `error_count()` and at most `DIAG_MAX_ERRORS` entries. No `size_time` row; not measured (UNVERIFIED)."
- **BN-12 (R3-ADV-11).** Add to line 146 (`locator_frames`) and line 104:
  - "Every row that runs code in a real own module's namespace uses `hadavin_sdk.stats`. It defines only names starting `_p5a_probe_` and deletes them in `finally`. The temporary `__name__` swap is restored in `finally`.
  - "`test_locator_rows_leave_no_trace` checks that `set(vars(hadavin_sdk.stats))` is equal before and after those rows."
- **BN-13 (R3-ADV-13).** Replace the "Problem in plain words" field with: "When something fails, the core writes an error message that often holds text it did not write: a library's message, a model's wrong answer, a line of the customer's document. That text goes to the log, to stored error fields and to the screen after a pattern cleaner (`safe_head`) has masked what it recognises, and a pattern cleaner cannot recognise a person's name or an invoice line (a revision 1 probe left a name, an invoice line, an `=40` e-mail and a lower-case IBAN in clear). The earlier design that tried to clean harder collected 51 review findings (`BL-core-c18a-001..051`) and was replaced (owner decision, 2026-11-05). The replacement never prints foreign text at all. P5a builds its base: closed lists, the function that turns any exception into a diagnostic, the function that renders it, closed validation text, and a hostile corpus that proves nothing else gets through."
- **BN-14 (R3-ADV-14).** Replaces `SafeToken.shape(value, name)` in line 64 and `SafeToken.shape(exc.sqlstate, "sqlstate")` in line 70 with `SafeToken.sqlstate(value) -> SafeToken | None` (pattern `^[0-9A-Z]{5}$` through `re.fullmatch`). Couplings: P5b1 adds its own named constructor for `request_id`; P5b3 adds one for `token40`.
- **BN-15 (R3-COR-4).** Replaces the minimums in line 146 and the totals in the changelog:
  - `hostile_class` **16**, the 16 listed situations, the last one per BN-3.
  - `secret_shapes` **6**: AWS example key, `sk-` shape, JWT shape, PEM block, `password="` unterminated quote, GitHub-token shape.
  - `pii_encoded` **9**: HTML entity with `;`, HTML entity without `;`, HTML entity with padding, `%40`, `%2540`, `\x40`, `&#64;`, `=40`, `%u0040`.
  - `own_class_spoof` **7** (BN-5).
  - `locator_frames` **10** (BN-16).
  - "**Active (135)** ... **Later (24)** ... **Not applicable (2)** ... **Total minimum 161**. The meta-test `test_class_minimums` computes the sums; the numbers in this text are informative." Without BN-1, the total is 164.
- **BN-16 (R3-COR-9).** Delete the `locator_frames` row "a frame whose `co_filename` is `"a\x00b"`" (line 146). Add to Appendix B "Equivalent, stated and not run": "removing `type(frame.f_code.co_filename) is str` from rule (c): no frame with a non-`str` `co_filename` can be built (`code.replace` raises `TypeError` for `int`, `bytes` and `None`, probed); the check stays as cheap defence."
- **BN-17 (R3-COR-3).** Add to line 93: "`test_fact_priority_order_is_the_d9_literal` (the 20 names, in order, as one literal tuple)." Add to Appendix B, under "Families and facts": "Two adjacent `FACT_PRIORITY` keys swapped: `test_fact_priority_order_is_the_d9_literal`." Line 51 becomes: "The two frozen `FACT_PRIORITY` tests (set and order) are changed only by P5b3 or P5c, when one of them adds `reason` (D8)."
- **BN-18 (R3-COR-5, R3-COR-6).** Replaces the parenthesis in line 75 with: "(a traceback of more than `DIAG_TB_STEPS` (2000) links gives locator `-` and, under rule 4, `foreign_exception`. A traceback of 33 to 2000 links keeps its innermost 32 frames and has a locator. Both numbers are author choices, UNVERIFIED as best values.)" Add to line 104's long-traceback case and to Appendix B's `DIAG_TB_STEPS` entry: "built by hand as a chain of 2001 `types.TracebackType(tb_next, frame, 0, line)` links over one real frame (probed: constructible), because the default recursion limit (1000) cannot produce it."
- **BN-19 (R3-COR-7, R3-COR-8).** Line 114: `config.py:52` becomes `config.py:50-52`. Line 71 gains: "A group's facts are read from the group itself (none in P5a), never from its first member; so a group whose first member is an `OSError` gets `code=os_error` and no `errno`."

## Positions (where I disagree with a reviewer, with evidence)
- **R3-ADV-4 premise:** `pydantic_core.ValidationError` CAN be subclassed, and `from_exception_data` returns the subclass (probed). The finding stands for another reason: the ticket left the killer undecided. The AST killer is chosen because it checks the call shape directly and does not depend on how the family check treats subclasses.
- **R3-ADV-12 alternative fix:** using `exc.exceptions` of a group subclass would not reach `__getattr__`, because `exceptions` is found on the class. A property on `errno` is used instead (probed).
- **R3-ADV-3 helper wrapping:** "wrap the subjects with `except BaseException`" is not taken. Excluding the one row by its `expect` field is narrower and does not teach a helper to swallow `KeyboardInterrupt`.
- **R3-ADV-10:** no new row. The cost is that of an object that already exists (argument, not measured).
- **R3-ADV-6:** the reviewer offered "drop and count" or "state that P5b3 wraps". I took a third option, drop without a count: `dropped_facts` was cut in revision 3, and a raise-free `diagnose` removes the wrapper duty from every caller (fix at the choke point).

## Couplings (relays for the lead; the other tickets are not edited here)
- **P5b1:**
  - Does NOT get the cause chain, `cause_kind` or any chain row (BN-1, PL25; this matches its own round-2 resolve item 18). If the lead reverses PL25, P5b1 gets the 3 rows back with `owner_step="R1P"`.
  - Its `request_id` shape is its own named constructor (`SafeToken.request_id`-style), because `SafeToken.shape` no longer exists (BN-14).
  - `diagnose` never raises on bad `facts=` (BN-7), so P5b1's provider facts are dropped, not raised, on a wrong type.
  - The `Phase` enum lives in `codes.py`; P5b1's "phase beyond sqlstate" row (with T3) extends `Phase` with a reviewed literal-test change.
- **P5b3:**
  - Flips both `OLD_WRITER_LEAKS` and `OLD_WRITER_CRASHES` rows (BN-2); its wiring must make the `crashed` rows `clean`. The crash is a defect in today's code: `run_tick` can be broken by a hostile exception through `_message` (`tick.py:289`, `:292`; read, not run). P5b3's replacement of `_message` must have a row for it.
  - Can call `diagnose` inside `except` handlers without a wrapper (BN-7).
  - Imports `leaks`/`grammar_ok` from `tests/data/c18a_oracle.py`; there is no fallback oracle (BN-8).
  - Adds its own `token40` constructor (BN-14).
- **P5c:** unchanged.
- **Every package merged before P5a's build:** unchanged (first-step scan, `OWN_CODES` rows).

## PENDING LEAD (continuing the ticket's numbering after PL24; recommended answers are final under order 6(g) unless the lead replies)
25. **PL24 answered (b) by build note BN-1:** the 3 `chain` rows leave the corpus and the cause chain has no owner in v1. Recommend: yes. This was the author's own recommendation, both resolves cut the chain, and order 7(3) says to cut surface. Reversible: strike BN-1.
26. **`diagnose` never raises on bad caller `facts=`** (wrong type = dropped; changes revision 3 line 60, "the only raise"). Recommend: yes. It removes an escape path out of P5b3's `except` handlers at the one choke point.
27. **No round 4.** Revision 3 freezes with build notes BN-1..BN-19; the one build-start review (order 19 A / 20 item 3) is next and appends its notes. Recommend: yes; the cap rule leaves no other option. The lead may also relabel some Majors, but I do not recommend it: they are real, and the fixes are small enough for build notes.
28. **`foreign_driver` split: 5 real classes and 3 hand-built** (no `openai`, `sqlalchemy` or `httpx` dependency). Recommend: yes. Adding those libraries would break the pinned-dependency policy and no-single-dependency for a test-only reason.
29. **Fallback oracle cut:** a missing `scan_keyset` fails collection everywhere. Recommend: yes, since P1b is a hard dependency.
30. **Writer crash pin (`OLD_WRITER_CRASHES`) and the `run_tick` crash.** Recording today's crash of `run_tick` on a hostile exception as a pinned, strict-xfail outcome is not a fix. The fix is P5b3's, which replaces `_message`. Recommend: yes, plus one line in the P5b3 ticket that the crash rows must become `clean`. Alternative: a two-line hardening of `_message` now (a `try` around it), which would break P5a's "changes no existing behaviour" rule; not recommended.

## Counts
- **Findings:** 23 ids (0 Blocker, 6 Major, 12 Minor, 5 Nit), merged into 21 decisions (ADV-2 with COR-2; ADV-3 with ADV-12).
- **By id:** PROPOSE FIX 23. Of them, 6 are closed by a cut (ADV-1, ADV-6, ADV-7, ADV-9, ADV-14, COR-9); 1 is a split (COR-1); 1 is a statement with no row (ADV-10); 1 has its premise contested and its fix kept (ADV-4). CONTEST 0, ESCALATE 0, DECLINE 0.
- **Build notes:** 19 (BN-1..BN-19) plus 1 banner.
- **Corpus:** active 134 to 135, later 27 to 24, not applicable 2, total 163 to 161 (160 from BN-1 alone; 164 if the lead reverses PL25).
- **Tests:** added `test_pydantic_error_reads_are_closed_ast`, `test_phase_is_the_frozen_list`, `test_validation_types_are_the_frozen_list`, `test_fact_priority_order_is_the_d9_literal`, `test_locator_rows_leave_no_trace`; renamed `test_baseexception_from_hostile_getattr_propagates` to `..._attribute_propagates`; cut `test_all_toolrefused_sites_map_to_tool_refused` and `test_fallback_oracle_agrees_on_plain_canaries`.
- **New PENDING LEAD items:** 6 (25-30). Round 4: none (order 20 item 6). Remaining unaddressed: 0.
