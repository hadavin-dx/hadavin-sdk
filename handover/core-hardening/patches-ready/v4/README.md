# Core patches for the take, v4 (C5 v4, 2026-11-16)

v4 replaces v3 for the lead's use. v3 stays unchanged next to it (`../v3/`, with its raw files). Nothing was committed or
pushed. Words: "the take" = the one real-v5 video run.

## What the lead can do NOW, what is DEFERRED, what is CUT
| Item | State | What to do |
|---|---|---|
| `G5-wording.patch` (text and comments only, 3 files, no behaviour change) | **APPLY NOW** | `patch -p1 < handover/core-hardening/patches-ready/v4/G5-wording.patch` from the repo root. Same file as v3 (hash in `SHA256SUMS.txt`). |
| `DEAD-MAN-CHECK.md` (a note, no code) | **NOTE, nothing to apply** | Static text, never run. It lists `audit_drain` among the steps to watch; that step exists only if A-01 is applied, so with A-01 deferred remove that name from the list. |
| `C-01-MINIMAL.patch` (new in v4) | **OPTIONAL, only if the take's model program loads `Route` config** (unverified, not in the video path) | Refuses, in pilot and prod, a live model price of 0 or below and a `max_tokens` above a ceiling. Details below. If the take does not load `Route` config, apply nothing. |
| `DEFERRED-A-01.patch` (audit events waiting in the outbox) | **DEFERRED (decision 4)** | Do not apply or extend now. Appendix A. |
| `CUT-C-01-FULL-NOT-FOR-THE-TAKE.patch` (v3 C-01 with its extras) | **CUT (decision 4)** | Do not apply. Appendix B. |

## What failed, what is uncertain, what was NOT checked (read first)
- **Not run:** the 455 Postgres tests (skipped in every full run; no Postgres here); the dead-man query; any negative test that
  the audit database identity cannot UPDATE or DELETE `audit_entries`; the repo guard tests on the REAL repository (they ran on
  a git-initialised copy with `handover/` removed); any live model, cloud or network call. The full suite was NOT re-run on the
  cut or deferred patches in v4 (they are unchanged from v3 except one word, see Appendix B); their v3 suite result is in `../v3/raw/`.
- **Whether the take loads `Route` config is unknown.** If it does not, `C-01-MINIMAL.patch` changes nothing the take can see.
- **`C-01-MINIMAL.patch` only guards `pilot` and `prod`.** `dev` still loads a zero price and any `max_tokens`. A local model with
  no key and price 0 is refused in pilot and prod by this patch (v3 had a flag for it; it was cut). The `200_000` ceiling is a
  typo guard I chose; no provider page was looked up (no live lookup here); the studio head must confirm it or give a dated figure.
  In the prod test fixture the config is refused for an unrelated reason (a key file), so the prod "good route" test only shows the
  route adds no refusal; a prod config that loads end to end was not run.
- **Not covered by a test:** the `fake` model exempt from the price rule cannot be reached in pilot or prod (`fake` is dev-only and refused
  there first), so that exemption is code that no pilot/prod test can observe; mutants M4 and M7 are killed only because the test
  config uses a live kind.
- First mutation run (v3) was on an EARLIER tree than the final one: see "Mutation count" below.

## Findings of round 3 and what v4 did
| Finding (reviewer file) | Fixed where |
|---|---|
| design 1: C-01 still holds all extras; no minimal patch; the "`refused +=` matters" claim misleading | `C-01-MINIMAL.patch` built (no flag, no loopback, no replay change, no NaN branch, one dated config value). The `refused +=` sentence is corrected in Appendix B. |
| design 2: README still read as a live apply guide; no DEFERRED / CUT markers | Top table above; A-01 and C-01 full text moved to the appendices with their own labels and apply notes; v3 owner-decision items on memory-only audit and zero-price model removed as moot (they belong to deferred or cut work; they live on only in `../v3/README.md`). |
| design 3 / codebase 1: "54 mutants" vs raw | Corrected to 53 distinct ids; command in "Mutation count". |
| codebase 2: first mutation run not on the final tree | Stated plainly below; nothing is claimed "killed on the final tree" beyond what the raw shows. |
| design 4: 32 fail on pristine is partly stub failures; v2 tree not confirmed real v2 | Reworded in Appendix B: behaviour proof of the `refused =` bug is `../v3/raw/v2-fails-pilot-prod-tests.txt` and I cannot confirm that tree was the real v2 (its file is named `test_v3_pilot_only.py`). The minimal patch has its own proof: 18 of its 22 tests fail on the pristine tree (`raw/c01min-tests-on-pristine.txt`). |
| design 5 / codebase 4: product name in docstring; weak prod control | Word replaced by "a local model server" in the NEW copy of the cut patch only (v3 untouched); the minimal patch has no such text. Prod "good route" test is labelled for what it shows (see above). |
| design 6: `audit_drain` makes the tick exit non-zero until a person acts | One sentence in Appendix A. |
| codebase 3 / 4: "applied tree equals work tree", "any order works", `git apply` never run | Claims removed from the v3 text. For the minimal patch, what was run is in `raw/apply-check.txt`: `patch --dry-run -p1` plus apply, `git apply --check` plus apply, each on a fresh extract of `b4cce5b`, and `cmp` of the three changed files against the scratch work tree (identical). Order of the other patches against each other was NOT tested in v4. |
| codebase 5: test docstring cites "survivors 12 to 14" | Inside the cut patch text only; not edited (a deferred or cut patch is not reworked). |
| codebase 6: `_hold` catches only OSError, docstring says "never raises" | Inside the deferred A-01 text; not edited. Noted in Appendix A. |

## C-01-MINIMAL.patch (3 files: `config.py`, `defaults.py`, new `tests/test_c01_minimal_route_limits.py`)
- New `_route_refusals(routes, llm_kind, max_route_tokens)` in `config.py`; `Config.max_route_tokens` (default
  `defaults.MAX_ROUTE_TOKENS = 200_000`, reason and date written there). In `Config._cross_checks` the call sits in the `environment != "dev"`
  block as `refused += _route_refusals(...)`, so one load error lists the route problems together with the other pilot/prod refusals.
- Rule: for any llm kind except `fake`, both prices must be above 0; `max_tokens` may not exceed `max_route_tokens`. Pydantic already
  refuses NaN and Infinity (`../v3/raw/nan-probe-*.txt`: pydantic 2.14.1), so there is no extra branch for them; a test pins that.
- Ladder rung 1 (existing `Route`/`Config` validation extended); rung 7 for the rule itself. No lower rung checks our config.
- Least privilege, no secrets, no hardcoding: no new permission, no secret, the one number is a dated default in `defaults.py`.
- Tests (22 cases): zero, 0.00 and negative prices for both fields in pilot and prod; ceiling 200 001 and 2 000 000 refused (pilot, prod);
  200 000 and a tiny price load; ceiling read from config (5000 loads, 5001 refused); a route problem and `allow_insecure_loopback`
  reported in the SAME error; dev unchanged; NaN and Infinity still refused by pydantic.

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
