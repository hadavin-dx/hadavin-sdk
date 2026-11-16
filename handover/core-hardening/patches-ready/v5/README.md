# Core patches for the take, v5 (C5 round 3, 2026-11-16)

v5 replaces v4 for the lead's use. v3 and v4 stay unchanged next to it (`../v3/`, `../v4/`, with their raw files). Nothing was committed or
pushed. Words: "the take" = the one real-v5 video run.

## What the lead can do NOW, what is DEFERRED, what is CUT
| Item | State | What to do |
|---|---|---|
| `G5-wording.patch` (text and comments only, 3 files, no behaviour change) | **APPLY NOW** | `patch -p1 < handover/core-hardening/patches-ready/v5/G5-wording.patch` from the repo root. Same bytes as v3 and v4 (hash in `SHA256SUMS.txt`). |
| `DEAD-MAN-CHECK.md` (a note, no code) | **NOTE, nothing to apply** | Static text, never run. v5 is edited for deferred A-01: it watches FOUR steps (`sweep`, `reconcile`, `stuck`, `checkpoint`). A broken audit write path (audit events piling up in the outbox) is marked **UNCOVERED** while A-01 is deferred. |
| `C-01-MINIMAL.patch` (v5 rebuilt) | **OPTIONAL, only if the take's model program loads `Route` config** (unverified, not in the video path) | Refuses a live model price of 0 or below (pilot and prod at config load, and in the replay command) and a `max_tokens` above a ceiling (pilot and prod). Details below. **How to check, one line, from the repo root:** `grep -rnE "Route\(|routes:|load_config" <the take's model program folder>`. A hit that builds `Route` or calls `load_config` means it loads Route config: apply `C-01-MINIMAL.patch`. No hit: apply nothing (it changes nothing the take can see). If the program sets `max_tokens` above 200_000, do not raise the default: set `max_route_tokens` in its config file to the number it needs. |
| `DEFERRED-A-01.patch` (audit events waiting in the outbox) | **DEFERRED (decision 4)** | Do not apply or extend now. Appendix A. |
| `CUT-C-01-FULL-NOT-FOR-THE-TAKE.patch` (v3 C-01 with its extras) | **CUT (decision 4)** | Do not apply. Appendix B. |

## What failed, what is uncertain, what was NOT checked (read first)
- **Not run:** the 455 Postgres tests (skipped in every full run; no Postgres here); the dead-man query; any negative test that
  the audit database identity cannot UPDATE or DELETE `audit_entries`; the repo guard tests on the REAL repository (they ran on
  a git-initialised copy with `handover/` removed); any live model, cloud or network call. The full suite was NOT re-run on the
  cut or deferred patches in v4 (they are unchanged from v3 except one word, see Appendix B); their v3 suite result is in `../v3/raw/`.
- **Whether the take loads `Route` config is unknown.** If it does not, `C-01-MINIMAL.patch` changes nothing the take can see. Use the grep line in the table above.
- **`C-01-MINIMAL.patch` guards `pilot` and `prod` at config load; `dev` still loads a zero price and any `max_tokens`** (a test now asserts the loaded values). A local model with
  no key and price 0 is refused in pilot and prod. The replay command (`k1b/replay.py`) refuses a price of 0 or below in every environment unless the model kind is `fake`.
- **The `200_000` ceiling is a typo guard, not a provider limit.** No provider page was looked up. It is still a hard load-time refusal built on that unverified number: a take that
  needs more must set `max_route_tokens` in its config. Decision 4 calls the ceiling "moot while C-01 is cut"; it is NOT moot for this minimal patch, because the minimal patch reintroduces it (the studio head confirms the number or gives a dated figure).
- **In the prod test fixture the config is refused for an unrelated reason (a key file).** Prod price and ceiling tests pass on the patched tree only because the route text joins that refusal in one error (mutant M6 kills `+=` turned into `=`). No prod config that loads end to end was run.
- **Open siblings of the same bug class, NOT fixed here (outside decision 4; each needs a decision):** `registry.py:35-36` `Budget.daily`/`Budget.monthly` and `registry.py:53` `max_run_usd` are bare `Money` with no above-0 check, so a zero or negative cap never fires; `deferred.py:62` only checks "not None". Fix later at one shared choke point with the same kind of test; listed so they are not forgotten (exception 2(b): needs the lead's scope decision, next step = lead says go, then one predicate in `registry.py`).
- First mutation run (v3) was on an EARLIER tree than the final one: see "Mutation count" below.

## Findings of round 4 (v4 reviews) and what v5 did
| Finding | Fixed where |
|---|---|
| design M1: v4 `DEAD-MAN-CHECK.md` was the unedited v3 text (five names, "now FAILS the audit_drain step") | `DEAD-MAN-CHECK.md` v5: four steps, audit-outbox gap marked UNCOVERED while A-01 is deferred, the last sentence and the `audit_drain` negative test removed. |
| design M2: "18 of 22 fail on pristine" overstated | Headline below: 11 of the 19 failing new tests are pilot-side or rule-level and prove the rule is missing; 8 are prod cases that fail on the old tree only because of the unrelated key-file refusal. |
| codebase M1: `k1b/replay.py:85-90` is a second copy of the price rule (`== 0`, negative passes) | ONE shared predicate `route_prices_above_zero` in `config.py`, called by `_route_refusals` and by `replay.py`. Replay now also refuses a negative price. Tests: 4 replay cases (zero and -1, both fields). Mutants M10, M11, M12. |
| codebase M1 (open siblings) | Listed above (`registry.py` Budget and `max_run_usd`; `deferred.py:62`). |
| codebase nit 2: dead `fake` exemption | Removed from the config rule (`fake` is dev-only, refused in pilot and prod first). Replay keeps its own `fake` exemption (a real path: replay in dev with the recorded model). |
| codebase nit 3: dev test could pass without asserting | `test_dev_is_not_changed` loads a dev config and asserts the values; mutant M8 (rule applied in dev) is killed by it. |
| codebase nit 4: mutation gaps | Mutants M4 (only the -1 case kills), M8 (rule in dev), M9 (ceiling from the constant). Script and raw saved. |
| design nit 1 / nit 2 | Grep line and remedy in the table; ceiling note above. |
| design nit 3 | `raw/mutate-c01min.py` (the 12 edits) next to `raw/mutation-c01min.txt`. |
| design nit 4 / codebase nit 5: apply check from a missing path | `raw/apply-check.txt` re-run with absolute paths: G5 then MINIMAL, and MINIMAL then G5, both rc 0 and the whole trees identical. |
| nit 5 / codebase nit 6: counts rely on unopened raw | Counts in this file are from v5 raw files only; the pristine full-suite figure is quoted from `../v3/raw/pristine-full-suite.txt` and was not re-run. |
| `SHA256SUMS.txt` | Regenerated with `sha256sum`, checked with `sha256sum -c` (`raw/sha256-check.txt`). |

### Decision on the shared predicate (replay.py)
Done as ONE shared predicate: the function is 2 lines, `replay.py` already imports `hadavin_sdk.config` in sibling modules (`k1b/loop.py`, `bundle.py`, `audit_sink.py`), so no import cycle or new dependency, and tests prove both callers. One behaviour change in replay: a negative price is now refused (before, only 0). The error text changed from "a zero input or output price" to "a zero or negative input or output price"; the existing test matches on "zero" and still passes.

## C-01-MINIMAL.patch (5 files: `config.py`, `defaults.py`, `k1b/replay.py`, new `tests/test_c01_minimal_route_limits.py`, `tests/test_k1b_replay.py`)
- New shared `route_prices_above_zero(route)` and `_route_refusals(routes, max_route_tokens)` in `config.py`; `Config.max_route_tokens` (default
  `defaults.MAX_ROUTE_TOKENS = 200_000`, reason and date written there). In `Config._cross_checks` the call sits in the `environment != "dev"`
  block as `refused += _route_refusals(...)`, so one load error lists the route problems together with the other pilot/prod refusals.
- Rule: both prices must be above 0 (in `replay.py`: for any llm kind except `fake`); `max_tokens` may not exceed `max_route_tokens`. Pydantic already
  refuses NaN and Infinity (`../v3/raw/nan-probe-*.txt`: pydantic 2.14.1), so there is no extra branch for them; a test pins that.
- Ladder rung 1 (existing `Route`/`Config` validation extended); rung 7 for the rule itself. No lower rung checks our config.
- Least privilege, no secrets, no hardcoding: no new permission, no secret, the one number is a dated default in `defaults.py`.
- Tests (23 in the new file, plus 4 replay cases): zero, 0.00 and negative prices for both fields in pilot and prod; ceiling 200 001 and 2 000 000 refused (pilot, prod);
  200 000 and a tiny price load; ceiling read from config (5000 loads, 5001 refused); a route problem and `allow_insecure_loopback`
  reported in the SAME error; dev unchanged (values asserted); the shared predicate on zero and negative prices; NaN and Infinity still refused by pydantic; replay refuses zero and -1 on both fields.

### Evidence (scratch copy: `git archive b4cce5b`, git init, `handover/` removed; raw files in `raw/`)
| Check | Result |
|---|---|
| New tests on the PRISTINE tree (`raw/c01min-tests-on-pristine.txt`) | **18 failed, 4 passed.** The 4 that pass are guards only (loads at the ceiling, good prod route, dev unchanged, pydantic NaN). |
| New tests on the patched tree | 22 passed |
| Full suite on the patched tree, one run (`raw/full-suite-c01min.txt`) | **9413 passed, 455 skipped, 0 failed, 236 s, rc 0** (pristine 9391 + 22 new; pristine figure is v3's `../v3/raw/pristine-full-suite.txt`, same command) |
| `ruff check`, `ruff format --check` on the 3 touched files (`raw/lint-c01min.txt`) | clean, rc 0 |
| `bandit -ll` on the 2 touched source files | rc 0, no findings (two parser warnings about comment text only) |
| 8 hand-made mutants (`raw/mutation-c01min.txt`, first failing test named): price `>0` to `>=0` on each field, ceiling `>` to `>=`, fake-exempt turned off and inverted, route refusals dropped, `refused +=` turned into `=`, default ceiling 2 000 000 | all 8 killed, on the final tree of this patch |
| Apply checks (`raw/apply-check.txt`) | `patch -p1` and `git apply` both rc 0 on fresh extracts, files identical to the work tree |
No suppressions added (no `noqa`, `nosec`, skip or weakened test).

## Mutation count (v3's lane, corrected)
Command (run from `patches-ready/`): `grep -oE '^(C01|A01|K1B|SP)-[0-9]+' v3/raw/mutation-v3.txt | sort -u | wc -l` gives **53**
distinct ids (67 result lines because re-runs repeat ids). `C01-10` has no line, so v3's "54" was wrong. The first run
was on an earlier tree: the killing test named for A01-14 in the first run does not exist in the final A-01 text. Re-run on the final tree
and killed: A01-10, A01-14 (relabelled "chain outbox DELETE removed" in the re-run), A01-16, A01-17, SP-01 to SP-09. NOT re-run on the final tree:
all C01-*, the other A01-*, K1B-01 to K1B-03. All of C-01 and A-01 is cut or deferred, so this only matters if they are un-cut later (then re-run first).

## Appendix A: DEFERRED (decision 4), `DEFERRED-A-01.patch`, NOT for the take
- What it is: new last tick step `audit_drain`: asks the audit kind for its backlog, drains waiting events into the chain, and fails the step when
  anything remains. **Plain consequence: the tick exits non-zero (and `last_ok_at` stops advancing) until a person acts on a waiting or damaged
  audit event; nobody has examined how often that would alert.** Also adds `backlog()`/`reconcile` plumbing in `chain.py`, `local_dir.py`,
  `protocol.py`, `k1b/audit_sink.py` and an opt-in spill folder (`audit/spill.py`).
- Tested in v3 only (suite 9491 passed with C-01 full + A-01 + G5 together; A-01 alone was not suite-run). Postgres paths and the dead-man query were not run.
- Known text issue not fixed: in the chain kind `_hold` catches only `OSError`, narrower than its "never raises" docstring.
- Apply (later, after a decision): from a `b4cce5b` checkout `patch --dry-run -p1 < DEFERRED-A-01.patch` first. In v3 its `table.py` hunk applied with a
  5-line offset after C-01; against a tree without C-01 that was not run in v4. Read `../v3/README.md` sections "A-01" and "Owner decisions" first:
  the memory-only audit question (spill folder, fail closed, or written acceptance) is open there and is only moot while A-01 stays deferred.
- Nothing may be written as "an audit event cannot be lost": it is not true in any option.

## Appendix B: CUT (decision 4), `CUT-C-01-FULL-NOT-FOR-THE-TAKE.patch`, do NOT apply
- v3's C-01 with its extras: `price_is_zero_by_design`, `keyless_loopback`, `max_route_tokens` plus `defaults.MAX_ROUTE_TOKENS`, NaN-safe predicate, shared
  `price_problems` rule and replay rewiring (5 replay tests). The only change from v3 is one word in a docstring (a product name replaced by "a local
  model server"); ruff check and format check pass on the touched file with it (`raw/cut-c01-docstring-check.txt`), dry-run applies on `b4cce5b` (rc 0).
  The full suite was not re-run for this one-word change.
- About the `refused +=` fix of v3: it matters ONLY because this full patch adds route refusals before the environment block. On the pristine tree
  the double assignment is harmless. So it is not a standalone fix; the minimal patch above avoids the issue by joining with `+=` inside the block.
- Behaviour evidence of the v2 bug is v3's `raw/v2-fails-pilot-prod-tests.txt` (9 fail, 2 control pass); I cannot confirm that tree was the real v2.
  The 61-case file passed against the old tree as 32 fail / 29 pass, but part of those failures are missing names, so they prove less than they look.

## Files
`README.md`, `REPORT-v4.md`, `SHA256SUMS.txt`, `checkpoint.md`, `G5-wording.patch`, `C-01-MINIMAL.patch`, `DEAD-MAN-CHECK.md`,
`DEFERRED-A-01.patch`, `CUT-C-01-FULL-NOT-FOR-THE-TAKE.patch`, `raw/`.
