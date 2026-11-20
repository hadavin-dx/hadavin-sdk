# A3/A4 review 1 (hostile reviewer)

Scope: fb5b37f98 (audit_code), 632e774f6 (allowlist), 9fa4db16e (pattern + _TS_SHAPE). Verified by running audit_code against AuditEvent and the regex against the PG test DB (55439). No test files were run beyond those probes.

## Blocker
none.

## Major

1. **audit_code lets through characters the AuditEvent pattern refuses** - src/hadavin_sdk/models.py:233 (`_AUDIT_BAD`) vs :221 (pydantic pattern, Rust regex).
   Python `\w` (str, Unicode) matches `isalnum()` characters such as `²`, `½`, `①`, `ª`-class No/No-like code points. Pydantic's Rust `\w` does not. Probed: `audit_code("a²b")`, `"½"`, `"①"` come back unchanged and `AuditEvent(principal=...)` raises ValidationError. Effect: a hostile or merely odd stop reason, tool error or user string still raises. `_note` falls back, but the fallback itself uses `audit_code(run.principal_id)` and (for principal `²`) raises again, so the run dies. Paths with no fallback (approvals/requests.py:88-92 principal from an approver, cli.py `_cap_event`, k1b/audit_sink.py, limits.py:236/251, tick.py:143) raise outright.
   Fix: compile `_AUDIT_BAD` with `re.ASCII` (`[^\w.:@/+=#~, -]` then means ASCII only, strictly narrower than the pydantic pattern); add `²`, `½`, `①` to test_audit_code_shapes.

2. **Feb 29 of a leap year sorts last in the outbox drain** - src/hadavin_sdk/audit/chain.py:241-252 (`_TS_SHAPE`, `02-(0[1-9]|1[0-9]|2[0-8])`).
   Verified on PG: `2028-02-29T10:00:00.123456Z ~ _TS_SHAPE` is False (so the cast is skipped, ts is NULL). These are not foreign rows: `now()` produces exactly this shape for every event the system writes on 29 Feb 2028 (and 2032...). Every such row is ordered after every later-dated outbox row, and rows sharing NULL sort by event_id only, not ts. A backlog (outbox outage across 29 Feb/1 Mar) drains 1 Mar rows into the chain before the 29 Feb rows, and with a steady inflow the 29 Feb rows are served last (starve behind new rows within a batch limit). The comment says "never an error", but it is a wrong order, not harmless.
   Fix: allow `02-29` only for leap years in the regex: year alternation `([0-9]{2}(0[48]|[2468][048]|[13579][26])|([02468][048]|[13579][26])00)` before `-02-29` (0000 is excluded anyway); add a test with 2028-02-29 sorting between 02-28 and 03-01 and a test that 2100-02-29 is NULL.

3. **_note fallback discards the original event's content and hides why** - src/hadavin_sdk/runtime/agent_loop.py:271-283.
   On any exception from `_event` the substitute row keeps only run_id/domain/operation/principal/result and sets `error_code="audit_event_refused"`: the real `error_code`, `object_ref`, `rule_id`, `inputs_hash`, `decision`, `caught_by`, `rows`, `output_hash` are lost (a tool-call row loses its inputs_hash/output_hash, which is exactly what the chain verifies against `tool_calls`), and nothing is logged (no `_LOG.warning` with the exception type or the failing field). A real defect in a caller (wrong type, unknown kwarg like the `bogus_field` test) becomes a quiet, uniform row. Also `kw["result"]` non-str is passed to audit_code unconditionally, and a failing `str()` gives "unknown", masking.
   Fix: build the fallback from `kw` with each known field passed through `audit_code`/kept if hash-typed (only drop what fails), keep original error_code in `error_code` and put `audit_event_refused` in `rule_id`, and `_LOG.warning("audit event refused error_kind=%s", type(exc).__name__)`.

## Minor

4. **Unsanitised AuditEvent constructions remain (not outside text today, but unguarded)**: src/hadavin_sdk/store/postgres.py:1078 `_release_event` (actor guarded by `check_store_id`, error is `type(exc).__name__`, result is built from Decimals: fine now, but a Decimal in exponent form like `1E+3` or a future change is not covered; wrap result with `audit_code`); demos/ask-your-data/askdata/audit.py:41,61,79 (principal, rule_id, error_code, decision unsanitised; `claimed:<name>` principal is the user's claim, and `error_code=reason` comes from the pipeline). Demo is outside src, but the principal is explicitly "claimed", i.e. outside text. tick.py:165 uses constants (clean). `decision`, `caught_by` in `_event` and `Approvals` free-str fields are unpatterned by the model, so no refusal, but not sanitised either (only an issue if outside text reaches them: today enum values).

5. **Sanitising collides and truncates** - models.py:240. `a\nb`, `a_b`, `a<b` all map to `a_b`; strings over 128 chars collapse to the same prefix (verified: 200 x and 129 x equal); `""`/None/unfittable map to `unknown`, equal to a genuine `unknown`. For `error_code`/`result` this is acceptable (a code, not a key), but not for `run_id`/`object_ref` which a verifier joins on (agent_loop.py:263 `run_id=audit_code(run.run_id)`; approvals requests.py:88 `object_ref=audit_code(approval_id)`): if an id ever had a char that changes, the chain row no longer matches the store row and no event is dropped but the join is silent. Suggest for ids: when `audit_code(x) != x`, use `audit_ref(x)`-style `sha256:` form (unique) instead of `_`. Not reachable today if ids are generated.

6. **Log-line forgery surface widened by 9fa4db16e** - models.py:221. Space, `=`, `,`, `:` are now all allowed together, so a value like `ok principal=admin result=released` is a valid audit field and reads as extra key=value pairs in any logfmt or text rendering of rows (e.g. a release result `released rows=1 requested_usd=...` is by design of that change). Newlines, CR, NUL, U+2028/2029, tabs and quotes ARE stripped (verified). No `_LOG` call in src currently formats these fields, so not exploitable today. If the space is only needed for the release result, allow it for `result` only.

7. **audit_ref trailing-newline quirk** - models.py:228. `_AUDIT_TOKEN.match("abc\n")` succeeds because Python `$` accepts a trailing newline, so `audit_ref` returns the text with the newline, which pydantic refuses. Masked in `_note` by `audit_code` afterwards, not in other callers. Fix: `fullmatch` / `\Z`.

8. tests/test_audit_isolation_pg.py (in the allowlist commit, unrelated to it): the test ALTERs the role default isolation database-wide and resets it in `finally`; a crash between leaves the role on repeatable read for the other PG tests. Acceptable, mention only.

## Checked and clean
- Allowlist (llm/anthropic.py:84,95): `platform` in backends/table.py:44 is a required `Literal["api","vertex","foundry"]` with no default, and a validator requires per-platform fields, so None/'' cannot reach `make()` from config; "api" is the only direct-API value and the allowlist is intended (narrow for everything else). Tests constructing settings by hand with another value get the narrow list, which is the safe direction.
- Offset forms (`Z`, `+hh`, `+hhmm`, `+hh:mm`, up to 15:59), space or `T`, 1-9 fraction digits, all verified True and cast OK on PG. Leap second `:60` is NULL by the regex (PG would cast it to next-day 00:00:00, so skipping is the safer choice; datetime never produces it). Zone names (`UTC`), lower-case `t`, `+0530` after a space, 10 fraction digits, invalid dates (04-31) are NULL; 04-31 would raise on cast, so the regex does protect the batch read. Year 0000 excluded.
- `substring(body ... "ts":"...")` cannot be spoofed by field values: quotes are not in the audit pattern and JSON escapes them.
- `audit_code` strips newline, CR, NUL, tab, quotes, backslash, `<>`, U+2028/2029 and all control characters (ASCII-wise; see Major 1 for non-ASCII digits).
