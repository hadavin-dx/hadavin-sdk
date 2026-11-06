# P5a round 3, adversarial review (ticket revision 3)

Status: REPORTED (saved by the lead session from the reviewer's hand-back, which is model output, not user authority).

Reviewer type: egm:egm-design. Read-only.

P5a revision 3, round 3 adversarial review. Read-only. I had no shell, so I ran no probe and no test.

**Counts:** 5 Majors, 0 Blockers.
- Order 20 item 6 allows a round 4 only if round 3 has at most 2 Majors. By my rating that condition fails: either the lead reclassifies some of R3-ADV-1 to R3-ADV-5, or the ticket freezes after one fix batch.
- All five fixes are small and mechanical.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-ADV-1 | Major | 146 (`chain` 3 later rows), 185, 222 (PENDING LEAD 24) | The author recommends option (b) but writes option (a). The three `chain` rows have `owner_step="R1P"`, so `test_later_rows_are_not_overdue` forces P5b1 to build the cause chain. P5b1's own resolve declined that, and order 7(3) says to cut surface. A builder cannot freeze this: the corpus total (163 or 160) depends on the lead's answer. | Write (b) now. Drop the 3 `chain` rows (later 24, total 160). Make the v1.1 row owner "none". Say in the changelog that the lead may reverse it. |
| R3-ADV-2 | Major | 121 (strict-xfail marks), 120 (adapter table) | `xfail(strict=True)` has no `raises=`. Any exception counts as the expected failure, not only the leak assertion. A wrong `App` fixture, a factory error or a `run_tick` adapter bug makes the row XFAIL silently. The "today's code leaks" proof then holds for rows where nothing was run. Also: `OLD_WRITER_LEAKS` is written from the evidence run, and nothing checks that a marked row actually reached the writer. | Use `xfail(strict=True, raises=AssertionError, reason=...)`. Have the adapter assert, before the leak assertion, that the writer produced a non-empty `last_error` or log record, so a setup error is a plain failure. The `app` fixture exists (`tests/test_p7_tick.py:81` uses `app` and `caplog`); say the new file reuses it. |
| R3-ADV-3 | Major | 146 (`hostile_class`: "a `__getattr__` raising a `BaseException`"), 97, 147 (teeth subjects) | The row is `active` and goes through `test_active_rows_hold_on_new_code`, but line 56 says `diagnose` lets such a `BaseException` propagate. It would abort the pytest session. The teeth subjects (`getattr(e, "filename", "")` and others) and the reverse-check `diagnose` hit the same `__getattr__` unguarded. The row's `expect` is never stated, and `except Exception` cannot catch `KeyboardInterrupt` or `CancelledError`. | Move this row out of the generic active-row test into `test_baseexception_from_hostile_getattr_propagates`. Mark it `expect="propagates"` and exempt it from the teeth test, the reverse check and the superset test. Wrap the subjects in the corpus-level helper with `except BaseException`. |
| R3-ADV-4 | Major | 106, 234 (mutant "`include_*` left True, or a key other than `"type"` read") | The mutant has no behavioural killer. The output is the same whether `loc`, `msg` or `input` are requested or read and then ignored. The recording subclass probably cannot exist, because `pydantic_core.ValidationError` is, as I recall, not subclassable (UNVERIFIED). The fallback AST check, "only attribute uses", does not see keyword arguments or the subscript key, and the spec leaves the choice open. | Decide now: an AST test of `guard/diagnostic.py` that every `.errors(...)` call has exactly the keywords `include_url`, `include_context` and `include_input`, each constant `False`. It also checks that every subscript on the returned entries is the constant `"type"`. Name that test as the killer. |
| R3-ADV-5 | Major | 74 (kind identity), 146 (`own_class_spoof`, `foreign_name`) | The kind rule says "own classes print the bare qualname" but never says how a class counts as own. Rule 1's identity check is for the code only. A class with `__module__="hadavin_sdk.x"` and a document-shaped `__name__` (for example from `type()`) is not own by identity. The text does not say whether it prints its name or `dynamic_class`. That is exactly the leak vector. No corpus row covers a fake class in an own module. | Say: a class prints its bare qualname only if it passes the rule 1 identity check (found in `sys.modules[...].__dict__` by walking the qualname) AND matches `^[A-Za-z0-9_.]{1,80}$`. Otherwise it prints `dynamic_class`. Add an `own_class_spoof` golden row for the kind. |
| R3-ADV-6 | Minor | 60 | A wrong-type `facts=` value raises `TypeError` from `diagnose`. P5b3 will call `diagnose` inside `except` handlers (for example `_run_step`, `tick.py:315-317`). A float `duration_ms` there skips `save_tick_state` and escapes `run_tick`. | Drop and count, or at least state that P5b3 must wrap the call in the handler. |
| R3-ADV-7 | Minor | 145 (`leaks_literal` fallback) | The fallback oracle is used "if `scan_keyset` cannot be imported". P1b is a hard dependency, so a broken import would silently weaken every redaction row. The run only prints which oracle ran. | In CI (`CI` set), importing the fallback must fail the build. Allow the fallback only locally. |
| R3-ADV-8 | Minor | 47-50, 63, 70 | The closed sets behind the `type` and `phase` facts have no named type. `Fact` is "a member of a closed enum", but only `Code`, `ProviderErrorType` and `Where` exist. A builder must guess how `phase=auth` or `type=missing` is stored and checked. | Name them (a `Phase` StrEnum and the 26 `type` names as a frozenset passed to `SafeToken.of`). Add them to the Interface and to the frozen-literal test. |
| R3-ADV-9 | Minor | 93 (`test_all_toolrefused_sites_map_to_tool_refused`) | One class means one table row, so the test can only fail if the row is removed, and `test_pinned_code_per_class` already covers that. Driving six `tools.py` raise kinds is a lot of unspecified setup. The cited lines 503-1188 are right on this tree (verified). Line 7 says only `tools.py` lines up to 831 are unchanged on `origin/main`, so the cites past 831 are UNVERIFIED there. | Cut this test, or reduce it to one parametrised construct-and-diagnose row for `ToolRefused`. |
| R3-ADV-10 | Minor | 146 (`size_time`), 77 | No row has a ValidationError with a huge error count. `errors()` builds all entries (the ticket admits `loc` and `msg` are built), so a million-error input does O(n) work and memory in the error path. `error_count()` is bounded only afterwards. | Add a `size_time` row, such as a list model with 100000 bad items, with an algorithmic counter. Or state that the cost is accepted. |
| R3-ADV-11 | Minor | 146 (`locator_frames`), 104 | Rows that `exec` into `vars(real_module)` define names in live package modules, and one flips `__name__` temporarily. That can leak into other tests or into mutation runs. | Run the code under a throwaway function name and `del` it in `finally`. Restore `__name__` in `finally`, as already stated for that one case. |
| R3-ADV-12 | Minor | 97 | The hostile-`__getattr__` propagation test relies on `winerror` being absent on Linux. On Windows the attribute exists, `__getattr__` is never reached, and the test fails. | Mark it Linux-only, or use an attribute `diagnose` reads on every platform (`exc.exceptions` of a group subclass). |
| R3-ADV-13 | Nit | 36 | The "Problem in plain words" field is about 9 long sentences. The template asks for 3 to 5. | Trim it. |
| R3-ADV-14 | Nit | 64 | `SafeToken.shape(value, name)` accepts exactly one name, so the `name` parameter is surplus surface. | Make it `SafeToken.sqlstate(value)`. |

## Verified (read on this tree)
- All 17 template fields are present in the template's order.
- **Corpus counts add up:**
  - 18 active classes sum to 134.
  - Locator frames: 7 + 4 = 11.
  - Later classes: 6+5+3+2+8+3 = 27.
  - 134+27+2 = 163.
  - Appendix A: 33 base + 16 later + 2 not applicable = 51.
- **Reachable and reserved codes:** 16 reachable plus 5 reserved = 21 `Code` members.
- **Facts:** 11 number keys in `FACT_BOUNDS`. The 8+8+4 split of the 20 facts matches. The `validation_text` bound of 108 characters matches the longest closed name (`union_tag_invalid`, 17).
- **22 own exception classes** exist at the cited files. Their lines match, including `ConfigError(ValueError)`, `StoreUnavailable(ConfigError)` and `EgressRefused(PermissionError)`.
- **Writers in `tick.py`:**
  - The `STEPS` tuple at 249-266 holds exactly the six names.
  - `_DRIVERS` is at 284 and `_message` at 287-292.
  - The writers are at 316, 317 and 324, and `run_tick` is at 335.
  - `_message` withholds OSError and driver text, so those old-writer rows should land as regression pins.
- **Other cites that hold:** `extract.py:58`, `stats.py:16`, `secrets_vault.py:37/91/93/117/119/133`, `config.py:120/454`, `runmap.py:38/42/53/417/485`, and all `tools.py` `ToolRefused` sites.
- **Config and CI cites that hold:**
  - `pyproject.toml` lines 6, 16, 27 and 81.
  - `test_lockin_guard.py:68-69` and `:520`.
  - CI trust authentication at `ci.yml:42` and Python 3.13.
  - No `hypothesis` dependency.
- `codes.py`, `guard/diagnostic.py`, `tests/data/`, `tools/` and `testing/` do not exist yet, as the ticket says.
- No real-looking secrets appear in the ticket text.

## Not checked
- **No probe or test ran:** `FALLBACK_FP` `2a1e659d`, T10 `fp` `ed342ffb`, psycopg instance `.sqlstate`, and the pydantic, gaierror and `sys.modules` probes are UNVERIFIED by me.
- **Files I did not read:**
  - `design-v3.md`, `ledger-seed.md` and `tickets/P1.md`.
  - The `P5b1`, `P5b2`, `P5b3` and `P1m` tickets, so the couplings are taken from this ticket's text only.
  - Nothing under `reviews/` or `evidence/`, as ordered.
- **Cites not checked on `origin/main` `397ec97`:** `tools.py` past line 831, and `guard/runmap.py`. P2a, P4a and P4d additions and the `scan_keyset` key-set semantics (superset test) are also unchecked.
- **Not decidable without running:** whether `tests/test_no_hardcoded_values.py` accepts `FACT_BOUNDS` and `TICK_STEPS`, and whether the hostile corpus passes the CI secret scan.
