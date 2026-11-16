# Ready-to-apply core patches (ORDER 012 item 2)

STATUS: UNVERIFIED. Nothing here was run as a test. What WAS done: each patch was made on a scratch copy of `b4cce5b`
(`git archive b4cce5b src tests`), and `git apply --check` passed for each patch ALONE and for the three in order
C-01, A-01, G5-wording on fresh copies. Every touched Python file compiled with `py_compile`. `pytest`, `ruff`
and `bandit` were NOT run (no project environment in this container). The lead runs the gate.

Apply (from a checkout at b4cce5b or later with unchanged files): `git apply handover/core-hardening/patches-ready/<name>.patch`.
Nothing from the "before an executor is added" gate is included. These replace the older partial
`patches/C-01-and-A-02.patch` (that file lacked the max_tokens bound, the tests and the RUNG lines).

| Patch | Files | RUNG (tool ladder) | Tests added |
|---|---|---|---|
| `C-01.patch` | `config.py`, `defaults.py`, `tests/test_c01_route_limits.py` | existing code (the `Route` field and `Config` validator already exist) + one documented default in `defaults.py`; CODE-LAST holds: a safety guarantee (no spend limit may be bypassed by price 0) | 10 cases (6 price, 4 other) |
| `A-01.patch` | `runtime/tick.py`, `audit/chain.py`, `audit/local_dir.py`, `tests/test_a01_audit_reconcile.py`, `tests/test_p7_tick.py` | existing code (`reconcile()` exists on the audit Protocol, `audit/protocol.py:27`; nothing in `src` calls it) + a 9-line tick step and log lines | 5 new tests + 2 edits |
| `G5-wording.patch` | `guard/redact.py`, `approvals/gate.py`, `tests/warden_port/test_gate.py` | config / text only: comments and docstrings, no behaviour | none needed (see below) |
| `DEAD-MAN-CHECK.md` | none (a documented check) | existing code: `tick_state` rows already exist | negative test described, run when set up |

## C-01: price above 0 at load, and a ceiling on `max_tokens`
- Price: for every route, `min(input, output) <= 0` is refused when `backends.llm.kind != "fake"` (the recorded fake never spends).
  Before: `Money` rejects floats only (`config.py` `Money` annotation), nothing refused 0 or a negative price.
  The replay path already had its own refusal (`k1b/replay.py:85-90`, called at :118); this closes the live path at the choke point.
- `max_tokens`: `Field(gt=0, le=defaults.MAX_ROUTE_TOKENS)`; the ceiling is `200_000` in `defaults.py`, one place. The number is
  my choice and NEEDS the studio head's yes or a better value from the provider's page (not checked, no live lookup here).
  Existing fixtures use 64 and 1024, so none is affected (grep of `tests` only; `demos` not grepped).
- Negative tests: price 0, 0.00 and -1 on input and on output are each refused for a live kind (6 cases); a priced live route
  loads; the fake kind with price 0 still loads (so the rule is not over-broad); max_tokens ceiling+1 and 0 are refused; the ceiling itself loads.
- Prove-fail-on-old-code: on `b4cce5b` the first two groups fail (no check exists). Not run here.
- Cites at b4cce5b: `config.py:55-60` (Route), `:316` (Config), `:365` (`refused = []`, where the check goes), `defaults.py:104`.

## A-01: the tick drains the audit outbox and says when a write failed
- New last step `audit_reconcile` (append-only, as the tick contract asks): calls `app.audit.reconcile()` when the kind has one and logs
  `audit_reconcile drained=<n>`. A kind without `reconcile` is skipped. The name fits the `tick_state` CHECK `^[a-z_]+$`
  (`0003_approvals_tick.sql:31`), so no migration is needed.
- `ChainAudit.write_outcome` and `LocalDirSink.write_outcome` log a WARNING when an outcome goes to the outbox (error type and event id
  only, never the body) and the chain kind logs an ERROR when even the outbox write fails (event held in memory only).
- Open point I did not settle: `K1bAudit` has no `reconcile` (`k1b/audit_sink.py`), so the step skips it. Whether it needs one is a
  question for the lead; the step cannot drain what that kind keeps.
- Negative tests: drain count and empty outbox after the step; a kind without reconcile logs nothing; the log line holds type and id but not
  the error text or run id; outbox failure logs the memory-only error; `test_p7_tick.py` now lists the new step and asserts it ran green.
- RISK I could not check: `test_a01_audit_reconcile.py` assigns `log._append` and `log._db.run` on instances. `ChainAudit` and `_Db` are plain classes
  (read in `audit/chain.py:93-105`, :152-), and an existing test does the same with `monkeypatch.setattr(log, "_append", ...)`.
- Cites at b4cce5b: `tick.py:177` (checkpoint, same pattern), `:249` (STEPS), `chain.py:215-231` (write_outcome), `:232` (reconcile),
  `local_dir.py:110-125`, `protocol.py:27`, `tests/test_p7_tick.py:81`.

## G5 wording drop (text and comments only)
- `guard/redact.py` docstring (b4cce5b lines 15-17) said G5 "re-runs them, independently, on everything that leaves". It now says there is NO
  independent second check, and G5 is not built here. `approvals/gate.py` header (:5-7) now says plainly that G5 and G2 are not built and the
  original notes below are design only. The test-file docstring line (`tests/warden_port/test_gate.py:3`) no longer claims a G5 test.
- The three guard-test files named in ORDER 009 are not touched. No behaviour changes, so there is no test; `git diff` shows only strings in docstrings.
- Remaining text I did not change: `gate.py:203` ("passed G5 and went out whole") is a history note about the original module.

## Not checked
No test, lint or bandit run. No live model or network call. I did not check how `Money` handles a string such as "0.00" beyond reading the code
(`BeforeValidator(_money)`), so the three price strings in the test are the likeliest place for a first failure.
