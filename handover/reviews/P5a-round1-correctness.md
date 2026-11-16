# P5a ticket, round 1, CORRECTNESS review
- Reviewer: egm:egm-codebase-details (fresh, read-only, Sonnet 5.5). Ticket tickets/P5a.md rev 1 (def2d2a). Nothing run.
- Result: BLOCKER 0, MAJOR 3, MINOR 7, NIT 1 (C1-C11). Stop rule NOT met.
- Saved by the lead 2026-11-05, CONDENSED (evidence dropped). The author re-checks every claim in the code. Ledger BL-core-p5a-r1-cor-*.

| id | sev | problem / fix |
|---|---|---|
| C1 | MAJOR | Shim fail-before cannot run: throwaway ce70eb5 + shim `guard/diagnostic.py` still lacks `hadavin_sdk.codes` (`Code`) and P1 `guard/textnorm.py` (`scan_hit`/`line_view`, the oracle): collection ImportError proves nothing. State worktree = ce70eb5 + P1a/P1b (or files) + real `codes.py` + shim; or a full stub set; acceptance check that collection succeeds before any row result is claimed. |
| C2 | MAJOR | `leaks()` requires `re.fullmatch` of Grammar A/B, so the shim output and all five leaky subjects fail the GRAMMAR, never the leak: (a) "rows safe_head masks already pass on the shim" is false, (b) teeth test is vacuous (the very ledger row 018 it answers), (c) the 90% reverse check tests something else, (d) `validation_text` has no grammar. Split into `grammar_ok(output, kind)` and `leaks(output, canaries)`; teeth and shim fail-before assert on `leaks()` alone; define the `validation_text` grammar; restate expected shim passes. |
| C3 | MAJOR | Mutant "`RecursionError` not caught -> 100000 brackets" is equivalent: `RecursionError`, `MemoryError` are `Exception` subclasses, and `diagnose` walks iteratively. Drop the names from the spec, or add a hostile object whose `__class__`/`__mro__`/traceback access raises RecursionError inside `diagnose`; mutate a narrower clause and name the killer. |
| C4 | MINOR | `tools/mutation_runner.py`, `testing/mutation.py`, `Mutant(name,file,old,new,expect,...)` listed as "existing core code reused (checked)" but do not exist on ce70eb5 (only under handover/promotion-inputs); they arrive with P1m; signature unverified. P1m is a hard dependency of the mutation run. |
| C5 | MINOR | `tool_refused` rationale ("broke its own manifest") is only the `tools.py:67` docstring; `ToolRefused` also raised for timeout (`tools.py:521, 1130`), rate/concurrency (1030, 1148, 1150), HTTP status (620), tool raised (1137), unresolved argument (1180). Reword "all ToolRefused" or add the alternative (`egress_refused`/`timeout`) to item 2. |
| C6 | MINOR | T10 reason wrong: pytest imports `tests/test_*.py` into `sys.modules` so the frame check holds and `lib_frame` shows the test file; only `locator` is `-`. A frame whose `__name__` is non-str/unhashable makes `sys.modules.get` raise and drops to the fallback: add `type(name) is str` check and a row. |
| C7 | MINOR | Stale vs order 7(3): P1c waiting/classes (`MalformedStoredKey, FoldVersionMismatch, SaltMismatch`) still listed; dependency is P1a, P1b, P1m only; re-check names against P1 rev 5. |
| C8 | MINOR | Killers named in the mutation plan missing from Tests: `test_extra_forbidden_*`, `test_loc_rendering`, `test_every_ledger_id_is_covered`, json_reason table test, `test_family_order_timeout_before_os_error`. List them with content. |
| C9 | MINOR | T8 `socket.gaierror` on `.invalid` giving `gai=-2` is not marked UNVERIFIED; no resolver can give EAI_AGAIN (-3). Assert `code=os_error` + in-range gai, or hand-build the gaierror. |
| C10 | MINOR | Tick writers cited `tick.py:292`/`:324`; 292 is the `_message` producer, the writes are 316 (error string), 317 (log), 324 (`last_error`). |
| C11 | NIT | A4/F6 lists `errors.py` hot for P5a, ticket deviates (cite F6); `ConfigError` OR rule only adds `VaultError`/`UnknownRecording` (`llm/fake.py:47` prints a recording file name); step names omit `purge_evidence`/`reprobe_sources`; `ansi_c1` minimum 6 but 7 items. |

Verified: 22 exception classes at the cited positions, line cites (runmap 417/485, tick 284/289, protocol:29, writer sites, foreign ConfigError sites), 21/20/12/26 counts, ledger ids 001-051 all covered (33+16+2), 151+16+2=169, P1 names exist in P1 rev 4, 16 template fields present.
Model used: Sonnet 5.5 (set by the lead).
