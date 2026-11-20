# ABC-H2 review 1 (hostile reviewer, M1 M3 N2 N3)

Run: tests/test_audit_outbox_order.py + tests/test_audit_event_fields.py = 79 passed (PG dsn set).
tests/test_release_expired_spend_pg.py: run was denied by the sandbox classifier; the verdict below is from a direct
AuditEvent construction (reproduced) not from that test.

## Blocker

B1. N2 pattern rejects result strings with spaces that live callers build. src/hadavin_sdk/models.py:221-222,
`result: AuditToken`. Callers:
- src/hadavin_sdk/store/postgres.py:1029-1033 `f"released rows={n} requested_usd={x} applied_usd={y}"` (spaces).
  Built AFTER the release transaction committed and as an argument outside `_write_outcome`'s try, so
  `release_expired_spend` raises pydantic ValidationError with the money released and no outcome row in the audit.
  tests/test_release_expired_spend_pg.py:223 asserts exactly this string, so it must now fail (not run, see above).
- src/hadavin_sdk/cli.py:836 `f"intent day_cap={day} month_cap={month}"` (spaces): `limits set-caps` raises
  ValidationError before the intent row (nothing changes, the command is dead). cli.py:861 `f"set day_cap=..."`:
  the same, inside a bare except, so a cap that WAS written is reported "could NOT be audited".
Repro: `AuditEvent(run_id='-',domain='limits',operation='x',principal='a',source='cli',result='released rows=1 x=2')`
-> ValidationError. Fix: emit space-free results (`released:rows=2,requested_usd=3.00,applied_usd=3.00`,
`intent:day_cap=..,month_cap=..`) and update the two tests that pin the old text, or allow a single space in
AUDIT_FIELD_PATTERN. Also add a test that builds every AuditEvent( site in src (cli, postgres, limits, tick) once.

## Major

M-1. N3 PostgreSQL cast can raise, contradicting the comment "a malformed one is NULL, never an error".
src/hadavin_sdk/audit/chain.py:480-486. The regex checks shape only, so `2026-02-30T00:00:00Z`,
`2026-01-01T25:00:00Z`, `0000-01-01T00:00:00Z`, `...+99` pass it and `::timestamptz` raises (verified in psql:
"date/time field value out of range"). One such row in audit_outbox makes the batch SELECT fail every pass
(`select_error`), blocking the whole drain; before, text order never failed and the row was just "unreadable"
(AuditEvent validation would reject it). The outbox is writable by the runtime login, so a hostile or corrupt body
is enough. Fix: make the cast safe (a plpgsql/SQL function with exception handler, or validate ranges in the regex
month 01-12, day 01-31, hour 00-23, min/sec 00-59, offset hh<=15) and add a PG test row `2026-02-30T00:00:00Z`.
(Also `\d` in PG regex can match non-ASCII digits; use `[0-9]`.)

## Minor

m1. tests/test_audit_isolation_pg.py:45-93 (M1): the behavioural test cannot fail without the new pin.
connect() already runs `SET SESSION CHARACTERISTICS ... READ COMMITTED` (postgres.py:~181, present at 7da7e9211), so
`SHOW transaction_isolation` is read committed with or without the _SESSION_PINS entry; only the tuple-membership
test (line 38) is sensitive to the change. The change itself is correct (adds a read-back). Fix: add a case where
the session SET is neutralised (monkeypatch connect's SET SESSION CHARACTERISTICS away) or accept that it is a
read-back test and say so in the docstring.

m2. N3 SQLite: julianday resolves to milliseconds, so rows less than 1 ms apart tie and fall back to event_id;
the in-Python sort (chain.py _drain_pass) re-sorts only within one page, so across a page boundary a sub-ms
earlier event with a larger event_id can drain after its neighbour. Negligible in practice; PG is microsecond-exact.
The test rows differ by >= 250 ms so it does not cover this.

m3. tests/test_refused_before_response.py: the removed `test_the_gate_reads_the_mark_on_provider_exhausted`
(and the INERT docstring test) were the only guard that the gate honours rule 2. The docstring now says
"NOT YET CONSUMED", so the removal is consistent, but nothing now fails when the gate starts or stops reading it.

## Checked and clean

- M3 direction: narrowing is the safe direction (fewer marks, so the worst case stays booked; never an under-count).
  Class default {401,403,404}; widened only by make() for platforms other than vertex/foundry, whose client is
  hard-wired to https://api.anthropic.com (client(), anthropic.py:~61). Direct constructors default to narrow.
  Tests cover all six codes for direct, three narrow for gateway, make() per platform.
- N2 other callers: principal values (run.principal_id, "system:tick", approver_id like "slack:U1", `by`
  validated by check_store_id), object_ref (plan_id, approval_id, case_id, agent id, `agent:day`), error_codes
  (reason codes, `http_NNN`, exception class names), rule_ids all fit. `by` from `--by` with a space (e.g.
  "Jane Doe") is rejected by AuditEvent and check_store_id may not have caught it earlier: see B1 cap events.
- audit_ref hashing: used only for the `cited` list (ids are recoverable from the run's tool_calls table) and
  `external_ref` (kept verbatim when it fits; only a long or spaced ref becomes `sha256:<32 hex>`; a verifier
  can recompute from the executor result but the audit row alone no longer names the external object in that
  case; acceptable but note it in the runbook). `RunResult.external_ref` int ids are already rejected by pydantic.
- N3 injection: the regex and the `"ts":"([^"]*)"` pattern are constants, row data is only the subject; no
  interpolation. Offsets, `Z`, no-offset (session TZ pinned UTC at postgres.py:179), ties (event_id) and the
  OFFSET paging are consistent with the SQL order.
