# Ready-to-apply core patches (ORDER 012 item 2)

STATUS: tested on a scratch copy of commit `b4cce5b` on 2026-11-16 (commands and raw results in
`../fix-patchcopies1.md`). Gate run there: `ruff check`, `ruff format --check`, and the full test suite with the live
and timing tests left out. NOT run: `bandit -ll` (not installed in this container, no network), and the gate through `uv run`
(offline; the repository's own `.venv` was used instead). The studio head's session runs the full gate before any merge.

## Where the files are, and which commit they fit
- The files are in this folder: `handover/flows-audit/reviews-of-core-patches/patch-copies/` (`C-01.patch`, `A-01.patch`,
  `G5-wording.patch`, `DEAD-MAN-CHECK.md`).
- They fit commit `b4cce5b` (the base all line numbers below refer to) and nothing newer. Checked on 2026-11-16 with `git apply --check`:
  `A-01.patch` also fits `176a0cbe0` and the then-current head `ec65e4614`; `C-01.patch` and `G5-wording.patch` do NOT (exit code 1; the
  environment check in `config.py` and the head of `tests/warden_port/test_gate.py` changed). On a newer commit,
  rebuild those two from the text of the hunks; that was not done here. Line numbers at head `ec65e4614`: Route
  `config.py:64`, `refused = []` at `config.py:393`.

## Apply recipe (tested)
```
# 1. an empty folder with the base commit's files (run inside the repository that holds the git history)
mkdir /tmp/patch-test && git archive b4cce5b | tar -x -C /tmp/patch-test
cd /tmp/patch-test
# 2. check each patch on its own, then apply in this order: C-01, A-01, G5-wording
P=<path to this folder>
git apply --check "$P/C-01.patch"        # saw: exit 0, no output
git apply --check "$P/A-01.patch"        # saw: exit 0
git apply --check "$P/G5-wording.patch"  # saw: exit 0
git apply "$P/C-01.patch" && git apply "$P/A-01.patch" && git apply "$P/G5-wording.patch"   # saw: exit 0
```
(`git apply` works in a folder that is not a git repository; it needs no history.) Apply `A-01.patch` before using `DEAD-MAN-CHECK.md`.
The real change goes in as a branch and a pull request opened by the builder; nobody merges from here.

## How to prove it works (pass criterion)
Who runs it: the lead's session (the studio head's), on the patched copy or on the pull-request branch. An agent that builds the change holds
no approver credential and no executor credential: it opens the pull request and never merges.

| Gate command (from `CLAUDE.md`) | Pass means | Saw on the patched copy of `b4cce5b` (2026-11-16) |
|---|---|---|
| `uv run --all-extras --group test ruff check` | exit 0, "All checks passed!" | passed (run as `.venv/bin/ruff check src tests`) |
| `uv run --all-extras --group test ruff format --check` | exit 0, nothing "would be reformatted" | passed, 265 files already formatted |
| `uv run --all-extras --group test pytest` | exit 0, no failed test | see `../fix-patchcopies1.md` for the full-suite line |
| `bandit -ll` | exit 0, no medium or high finding | NOT RUN (UNVERIFIED: the tool is missing here) |

Gate on the exit code of each command itself, never on a `| tail` pipe.

Prove the new tests fail on the old code (run on an unpatched archive of `b4cce5b` with only the two new test files copied in):
```
git archive b4cce5b | tar -x -C /tmp/old-tree && cd /tmp/old-tree
cp <patched copy>/tests/test_a01_audit_reconcile.py <patched copy>/tests/test_c01_route_limits.py tests/
python -m pytest tests/test_a01_audit_reconcile.py tests/test_c01_route_limits.py -q     # with src on the path (PYTHONPATH=src)
```
Expected and seen: `14 failed, 18 passed`. The 14 failures are the 6 zero-or-negative price cases, the 2 `max_tokens` cases and the 6
audit-reconcile cases. The 18 that pass on old code are the controls: the priced route and the fake model still load, and the 16 NaN and
Infinity cases, which the existing pydantic field check already refuses (so they pin today's behaviour; they cannot fail on old code).

| Patch | Files | RUNG (tool ladder) | Tests added |
|---|---|---|---|
| `C-01.patch` | `config.py`, `defaults.py`, `tests/test_c01_route_limits.py` | existing code (the `Route` field and `Config` validator already exist) + one documented default in `defaults.py`; CODE-LAST holds: a safety guarantee (no spend limit may be bypassed by price 0) | 26 cases (6 zero or negative price, 16 NaN or Infinity price, 1 priced route, 1 fake model, 2 `max_tokens`) |
| `A-01.patch` | `runtime/tick.py`, `audit/chain.py`, `audit/local_dir.py`, `tests/test_a01_audit_reconcile.py`, `tests/test_p7_tick.py` | existing code (`reconcile()` exists on the audit Protocol, `audit/protocol.py:27`; nothing in `src` calls it) + a 9-line tick step and log lines | 6 new tests + 2 edits |
| `G5-wording.patch` | `guard/redact.py`, `approvals/gate.py`, `tests/warden_port/test_gate.py` | config / text only: comments and docstrings, no behaviour | none needed (see below) |
| `DEAD-MAN-CHECK.md` | none (a documented check) | existing code: `tick_state` rows already exist | negative test described and run on a throwaway Postgres 16 (see the file) |

`G5-wording.patch` is in this folder. It was copied byte for byte (same checksum) from the earlier working copy
`handover/core-hardening/patches-ready/G5-wording.patch` (a scratch folder outside the repository, from the run that made these patches).

## C-01: price above 0 at load, and a ceiling on `max_tokens`
- Price: for every route, `min(input, output) <= 0` is refused when `backends.llm.kind != "fake"` (the recorded fake never spends).
  Before: `Money` rejects floats only (`config.py` `Money` annotation), nothing refused 0 or a negative price.
  The replay path already had its own refusal (`k1b/replay.py:85-90`, called at :118); this closes the live path at the choke point.
- NaN and Infinity: a price such as `NaN`, `sNaN`, `Infinity` or `-Infinity` never reaches that check. The existing field check of the
  pydantic library refuses it first ("Input should be a finite number"), and `load_config` turns that into a `ConfigError`. Seen on pydantic 2.14.1
  for the live and the fake kind (16 cases in the test file). A new test pins it so a later library change cannot turn it into a raw `InvalidOperation`.
- `max_tokens`: `Field(gt=0, le=defaults.MAX_ROUTE_TOKENS)`; the ceiling is `200_000` in `defaults.py`, one place. The number is
  my choice and NEEDS the studio head's yes or a better value from the provider's page (not checked, no live lookup here).
  Existing fixtures use 64 and 1024, so none is affected (grep of `tests` only; `demos` not grepped).
- The test config for a live model is `{kind: anthropic, platform: api, api_key_secret_name: <name>}`; this matches `AnthropicSettings` in
  `backends/table.py:43-61` (platform `api` needs `api_key_secret_name`). `test_a_priced_live_route_still_loads` asserts those settings
  parsed, so a refusal elsewhere cannot hide behind the price rule. The fixture environment is `dev`, which the environment table does not refuse.
- Negative tests: price 0, 0.00 and -1 on input and on output are each refused for a live kind (6 cases); a priced live route
  loads; the fake kind with price 0 still loads (so the rule is not over-broad); max_tokens ceiling+1 and 0 are refused; the ceiling itself loads.
- Cites at b4cce5b: `config.py:55-60` (Route), `:316` (Config), `:365` (`refused = []`, where the check goes), `defaults.py:104`.

## A-01: the tick drains the audit outbox and says when a write failed
- New last step `audit_reconcile` (append-only, as the tick contract asks): calls `app.audit.reconcile()` when the kind has one and logs
  `audit_reconcile drained=<n>`. A kind without `reconcile` is skipped. The name fits the `tick_state` CHECK `^[a-z_]+$`
  (`0003_approvals_tick.sql:31`), so no migration is needed.
- `ChainAudit.write_outcome` and `LocalDirSink.write_outcome` log a WARNING when an outcome goes to the outbox (error type and event id
  only, never the body). Both also log an ERROR when even the outbox write fails (event held in memory only): the chain kind
  (`chain.py`) and, added in this version, the local-directory kind (`local_dir.py`), each with its own test.
- Open point I did not settle: `K1bAudit` has no `reconcile` (`k1b/audit_sink.py`), so the step skips it. Whether it needs one is a
  question for the lead; the step cannot drain what that kind keeps.
- Negative tests: drain count and empty outbox after the step; a kind without reconcile logs nothing; the log line holds type and id but not
  the error text or run id (chain kind); outbox failure logs the memory-only error (chain kind and local-directory kind); `test_p7_tick.py` now
  lists the new step and asserts it ran green.
- The tests assign `log._append`, `log._db.run` and `sink._write` on instances; they ran green (see `../fix-patchcopies1.md`).
- Cites at b4cce5b: `tick.py:177` (checkpoint, same pattern), `:249` (STEPS), `chain.py:215-231` (write_outcome), `:232` (reconcile),
  `local_dir.py:110-125`, `protocol.py:27`, `tests/test_p7_tick.py:81`.

## G5 wording drop (text and comments only)
- `guard/redact.py` docstring (b4cce5b lines 15-17) said G5 "re-runs them, independently, on everything that leaves". It now says there is NO
  independent second check, and G5 is not built here. `approvals/gate.py` header (:5-7) now says plainly that G5 and G2 are not built and the
  original notes below are design only. The test-file docstring line (`tests/warden_port/test_gate.py:3`) no longer claims a G5 test.
- The three guard-test files named in ORDER 009 are not touched. No behaviour changes, so there is no test; `git diff` shows only strings in docstrings.
- Remaining text I did not change: `gate.py:203` ("passed G5 and went out whole") is a history note about the original module.

## Not checked
`bandit -ll` was not run. No live model or network call. `K1bAudit` was not changed (open point above). The three patches were not
rebuilt for commits after `b4cce5b` (C-01 and G5-wording do not apply there).
