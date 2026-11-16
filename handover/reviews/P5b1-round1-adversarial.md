# P5b1 ticket, round 1, ADVERSARIAL review
- Reviewer: egm:egm-design (fresh, read-only, Sonnet 5.5). Ticket tickets/P5b1.md rev 1 (30fd0e8). Nothing run.
- Result: BLOCKER 0, MAJOR 6 (A1-A6), MINOR 12 (A7-A18). Stop rule NOT met.
- Saved by the lead 2026-11-05, CONDENSED to one short line per finding (evidence dropped; the full text was delivered to the lead in chat). The author re-checks every claim in the code. Ledger BL-core-p5b1-r1-adv-*.

| id | sev | problem / fix |
|---|---|---|
| A1 | MAJOR | `describe` prints `type(exc).__name__` behind a shape check only; botocore creates a class per modelled error named like the code (verify), so `AccessDeniedException 403 permission` appears: the rewritten r16:68 assertion fails by design, the CHANGELOG sentence is false for nine modelled codes, conflicts with D3/D16/D11 and P5a `class_name_of` (P5a.md:39). Fix: use `class_name_of` or an explicit closed modelled-name set; fix r16 and CHANGELOG; Stubber wire test; tell P5b3. |
| A2 | MAJOR | Ticket says P5a not on disk, but P5a.md exists and differs: `diagnose` reads only `status`, `error_type`, `request_id`, `retryable` (no `retry_count`); code derivation by status only (the table here also maps `error_type`, golden rows 10/17/24); request-id shape defined in both P5a (`SafeToken.shape`) and here (`REQUEST_ID_SHAPE`). Fix: replace "PENDING P5a" with real names; add PENDING LEAD for `retry_count` and `error_type` codes; one home for the shape. |
| A3 | MAJOR | Hot files: P4b2 edits `llm/protocol.py`, `retry.py`, `common.py`, `bedrock.py` (new `status_of` hook duplicates `facts.status`); no ticket orders P4b2 vs P5b1; P6b1 touches no llm module so item 2 is moot. Fix: add P4b2 to the hot-file lists with order P4a, P5b1, P4b2 (decided); `status_of` reads `facts.status`; P5b1 depends on P4a hard. |
| A4 | MAJOR | R4 tripwire cannot fail: adapters read via `safe_attr`/`safe_facts` which swallow `Exception`; `__getattribute__` does not intercept `str(exc)`/`repr(exc)`; recording proxies fail `isinstance`. Fix: record names read and assert on the record; define `__str__`/`__repr__` on the class; raise a `BaseException` subclass; subclass the library error with recording. |
| A5 | MAJOR | Library loggers omitted: httpx logs reason phrase at INFO, botocore headers/body at DEBUG (verify); R14 may fail and P5b1 cannot fix it; Stubber skips HTTP layers. Fix: add the row, record pinned versions/logger names, R14 as strict xfail naming P5b4 where logs are real, keep Stubber out. |
| A6 | MAJOR | "Adapter can raise nothing" true only for the facts adapters: `transient()` -> `_chain` (`getattr(e,"reason")` unguarded), kind `retryable` hooks (`bedrock.retryable` AttributeError on non-dict `response`), `retry_after` runs `getattr(exc,"headers")` outside `try`: R5 "response as a list" still escapes `with_retry` raw. Fix: guard `transient`/`retryable`/`_chain`, move getattr into the `try`, R5 end to end through `with_retry`. |
| A7 | MINOR | "Identical for every input" not exact: raising `status_code` property used to escape, now a plain `ProviderError` that `askdata/pipeline.py:163` counts as refused/free (money class). State it; ask the lead refused vs exhausted. |
| A8 | MINOR | `default_facts` precedence unstated: `URLError(TimeoutError())`; say any `TimeoutError` in the chain wins, then `OSError`/`SSLError`; rows. |
| A9 | MINOR | Kind adapters with no library class fall to `status_error_type(status)` only; end each with `return default_facts(exc)`. |
| A10 | MINOR | Surviving mutants: `retry_count` after retried refusal, neutral status table edges, added table rows, Claude request_id without `req_` (8-40), 100-char `describe` name, `ProviderError` pass-through (row 28 no mutant), `safe_facts` isinstance vs exact. One table-driven test per table + rows. |
| A11 | MINOR | R6 grammar accepts any `( [a-z_]+)?`; enumerate `ProviderErrorType` values. |
| A12 | MINOR | R7 guard flags `with_retry`'s own f-string; name sanitiser functions, one plant each; P5b3's guard supersedes. |
| A13 | MINOR | Reason for the vendor-table deviation from D5 overstated (rule c has no vendor error codes); reword, keep as a lead decision. |
| A14 | MINOR | `HADAVIN_DEBUG=1` (`cli.py:79-82`) prints raw cause; D1 puts it in P5b3; consider a closed `cause_kind` fact and `raise ... from None`. |
| A15 | MINOR | Status 777 retried/billed and unbounded success-body read are lead decisions; P4b2.md does not carry them; add pointer. |
| A16 | MINOR | `exc.close()` only on the raise path; retried `HTTPError` keeps a body open; extend R8. |
| A17 | MINOR | Jargon ("zone T2", "tripwire", "R1P", "mutant") unexplained; Problem field over 5 sentences. |
| A18 | MINOR | Stale statements (P4a/P5a "not present", P6b1 touches every backend). Update on rev 2. |

Not checked: library internals (from memory), any test run.
Model used: Sonnet 5.5 (set by the lead).
