# Mutant plan for the v2 patches (C8c prep). NOT RUN.

**Status (read first).** The original 104 mutants have not been run on a test suite; only 8 were run once: the 7 added after review 3 (C2-52, C2-53, A2-54..A2-58) and C2-16 (which was already in the list of 104), in a scratch copy, to settle their classification (results in their sections; `raw/V2C-*`, `raw/V2A-*`). The full C8c run is still the lead's. The v2 patches are still being built; this plan is based on `patches-ready/v2/C-01.patch` and `A-01.patch` as they were on 2026-11-16 (sha256 below). If a patch changes, regenerate with `python3 make_mutants_v2.py <fresh archive + patches tree> mutants-v2.json` (it re-checks every `old` text and prints the count of problems).
What WAS checked: a fresh `git archive b4cce5b` extract, `patch -p1` of `C-01.patch`, `A-01.patch` and `G5-wording.patch` in that order (all three applied without error), and for each of the 111 mutants the `old` text occurs exactly once in the named file of that extract (script output: `111 mutants; 0 problems`; the raw line is in `raw/mutants-v2-dry-check.txt`). What was NOT checked: that any mutant is killed or survives; the "expected killer" column is my reading of the v2 tests, not a result. A mutant marked `SURVIVE?` is my guess that no v2 test kills it; the run decides.

```
4bf200518a205445c3417b4fb9dda47ed3aec73891eed319914ed3d920478256  ../patches-ready/v2/C-01.patch
085bcfdc81638b5d2a06765e2c158e1202ef301dabfc83278fd273cd74f978e1  ../patches-ready/v2/A-01.patch
```

## Why these mutants (answers review-2 M1)
The v1 lane tested the v1 patches. v2 changed the code (new `_price_ok`, `_finite`, `_route_refusals`, `keyless_loopback`, `max_route_tokens`, `audit_drain`, `backlog`, `last_corrupt`), so the v1 mutants no longer apply as written. This list covers every gap review 2 named: NaN/Infinity price (C2-01..05), `_finite` / `is_finite` flip (C2-02, 03, 05), `>` vs `>=` (C2-06, 29), `zero_ok` and/or (C2-08, 09, 11, 15, 16), `local_free` inverted (C2-12..14), `keyless_loopback` terms (C2-46..51), price boundaries: negative zero (C2-52 killed by the `-0` cases; C2-53 under the flag), tiny positive, one field zero (C2-07, 10, 19..21), `max_tokens` literals 1 / 0 / -1 / 200_001 / 199_999 / 2_000_000 (C2-40..45), last-route-only and first-route-only (C2-24..26), drain `ORDER BY` removed and swapped (A2-20, 21), `except` reorder (A2-31) and removal (A2-29, 30, 44), failed `DELETE` after the append (A2-22..24), `DuplicateEvent` swallowed or not (A2-25, 29..31, 44, 48), the failing-step rule (A2-04..08), backlog exception swallowed (A2-07), `last_corrupt` not reset (A2-13, 14) and the corrupt-row `continue` removed (A2-15). It also carries over the v1 survivors (memory-only drain, logging level, leak of error text) because v2 may have fixed them or not.

## Expected outcome (my prediction, to be checked by the run)
- 87 of 111 expected KILLED by the patch's own tests (86 + C2-52).
- 24 expected to SURVIVE (or equivalent): the 18 earlier ones, C2-53 and the five except-widening mutants A2-54..A2-58. Each is a candidate gap in the v2 tests; a survivor gets a proposed test, proven failing on the mutant and passing on the clean tree (as in section 4 of REPORT.md).

| id | expected | one-line description |
|---|---|---|
| C2-01 | SURVIVE (double cover: README says pydantic's Money already  | Route._finite validator removed (NaN/Infinity price accepted by the route itself) |
| C2-16 | SURVIVE (equivalent: see its section) | zero_ok: loopback term dropped (the flag alone decides whether price 0 is allowed) |
| C2-24 | SURVIVE? (the second route in the at-once test has a good pr | price check only on the route named default (route-position gap) |
| C2-27 | SURVIVE (equivalent) | routes not sorted (message order only) |
| C2-34 | SURVIVE? (only 0 is tested) | ceiling field gt=0 -> gt=1 (a ceiling of 1 refused) |
| C2-51 | SURVIVE? (no test uses a remote host in the set) | loopback set widened by one remote host (also widens the existing http check at line ~80: only the new route-price use is the target here) |
| C2-53 | SURVIVE? (no test sets the flag with a price of -0) | negative zero refused even when the flag allows a zero price (0 passes, -0 does not) |
| A2-13 | SURVIVE? (no test reconciles twice, first with a bad row, th | chain: last_corrupt not reset at the start of reconcile |
| A2-14 | SURVIVE? (same gap) | local_dir: last_corrupt not reset at the start of reconcile |
| A2-20 | SURVIVE? (tests do not assert the drain order of two or more | drain: ORDER BY removed |
| A2-21 | SURVIVE? (same) | drain: order swapped (descending) |
| A2-27 | SURVIVE? (no v2 test drains _pending successfully) | chain: drained memory event never removed (re-counted every run) |
| A2-28 | SURVIVE? (same gap) | chain: memory events never drained |
| A2-40 | SURVIVE? (no test asserts this line) | chain: unreadable-table warning removed |
| A2-45 | SURVIVE? (no v2 test makes the outbox unusable) | local_dir: event dropped when the outbox folder is also unusable |
| A2-46 | SURVIVE? (same gap) | local_dir reconcile: drained memory event never removed |
| A2-48 | SURVIVE? (no test puts an already-written event in the outbo | local_dir reconcile: DuplicateEvent on an outbox file no longer absorbed (file stays forever) |
| A2-49 | SURVIVE? (no local_dir test holds events only in memory) | local_dir backlog: memory events not counted |
| A2-52 | SURVIVE? (the test uses caplog at INFO and asserts the count | local_dir: corrupt-file ERROR downgraded to DEBUG |
| A2-54 | SURVIVE? (a write that raises BaseException is not tested) | chain write_outcome: except widened to BaseException (a Ctrl-C or exit during the write is swallowed and sent to the outbox) |
| A2-55 | SURVIVE? (a write that raises BaseException is not tested) | chain _drain: except widened to BaseException (an interrupt during a drain is swallowed and the event stays queued) |
| A2-56 | SURVIVE? (a write that raises BaseException is not tested) | local_dir write_outcome: except widened to BaseException |
| A2-57 | SURVIVE? (a write that raises BaseException is not tested) | local_dir reconcile (memory events): except widened to BaseException |
| A2-58 | SURVIVE? (a write that raises BaseException is not tested) | local_dir reconcile (outbox files): except widened to BaseException |

## How to run (when the v2 patches are final)
1. Build two scratch trees OUTSIDE the repository (run.py refuses any folder with a `.git` entry in it or above it): `git archive <sha> | tar -x` into a new folder, then `patch -p1 -i patches-ready/v2/C-01.patch` (tree C) and `A-01.patch` (tree A); symlink or create the `.venv` there. Do not use the real repository. The dry check above (`111 mutants; 0 problems`) used all three patches in ONE tree; the recipe builds two trees with one patch each, so it was checked again on those: every C2 `old` text occurs once in the C-01-only tree and in the C-01 + G5-wording tree, every A2 `old` text once in the A-01-only tree and in the A-01 + G5-wording tree (`raw/mutants-v2-split-dry-check-r2.txt`). Pass every patch applied to a tree as `--patch` to run.py, so its reference tree matches.
2. Split `mutants-v2.json` by id prefix (C2 to tree C with `tests/test_c01_route_limits.py`; A2 to tree A with the 4-file set `tests/test_a01_audit_reconcile.py tests/test_p7_tick.py tests/test_s2_audit.py tests/test_p3b_neutral_audit.py`; C2-46..51 live in `backends/table.py` and use the C test file).
3. `python3 run.py --root <tree> --sha <sha> --patch <patch file> --prefix <C-01v2|A-01v2> --raw raw-v2 --control --list <split json> -- <tests>` (the runner refuses a dirty tree, the real repository, a second run, test options that move the root (`--basetemp`, `--rootdir`, `--junitxml`, `--confcutdir`, ...), and a scratch environment whose tests would import a target file from another folder; it restores on SIGTERM/SIGINT/SIGHUP and writes the tree check at the end). If an editable install or `.pth` file points at another tree, the import check refuses; give `--pythonpath <tree>/src` (recorded in every raw file) or fix the environment.
4. One pytest process at a time per tree; two trees may run side by side. Raw output and the exact command stay in `raw-v2/`.
5. Every survivor: write a killing test, show it fails on the mutant and passes unmutated (`raw-proof-v2/`), and hand the test to the patch owner. Equivalent mutants (C2-16, C2-27, and C2-01 if pydantic already refuses NaN) are named, with the reason, never counted as killed.

## The mutants (exact text; `old` must occur once, `new` replaces it)

### C2-01 - Route._finite validator removed (NaN/Infinity price accepted by the route itself)
- file: `src/hadavin_sdk/config.py`
- expected: SURVIVE (double cover: README says pydantic's Money already refuses NaN/Infinity; confirm by run)
- expected killer: tests/test_c01_route_limits.py::test_nan_and_infinity_are_a_clean_config_error_never_a_crash[...] only if pydantic stops refusing

old:
```text
        if not v.is_finite():
            raise ValueError("a price must be a finite number")
        return v
```
new:
```text
        return v
```

### C2-02 - v2 _finite flipped: every finite price refused
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_priced_live_route_still_loads (and most of the file)

old:
```text
        if not v.is_finite():
```
new:
```text
        if v.is_finite():
```

### C2-03 - _price_ok: is_finite and -> or (NaN raises, Infinity passes)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_price_predicate_is_total_even_where_pydantic_is_bypassed

old:
```text
    return price.is_finite() and (price > 0
```
new:
```text
    return price.is_finite() or (price > 0
```

### C2-04 - _price_ok: is_finite term dropped (NaN raises InvalidOperation, Infinity passes)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_price_predicate_is_total_even_where_pydantic_is_bypassed

old:
```text
    return price.is_finite() and (price > 0
```
new:
```text
    return (price > 0
```

### C2-05 - _price_ok: is_finite negated
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_priced_live_route_still_loads

old:
```text
    return price.is_finite() and (price > 0
```
new:
```text
    return not price.is_finite() and (price > 0
```

### C2-06 - price > 0 became >= 0 (price 0 always allowed)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-*]

old:
```text
price > 0 or (zero_ok and price == 0))
```
new:
```text
price >= 0 or (zero_ok and price == 0))
```

### C2-07 - price floor 1 (tiny positive price refused)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_tiny_positive_price_is_accepted_on_purpose

old:
```text
price > 0 or (zero_ok and price == 0))
```
new:
```text
price > 1 or (zero_ok and price == 0))
```

### C2-08 - zero_ok and -> or (price 0 always allowed)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-*]

old:
```text
price > 0 or (zero_ok and price == 0))
```
new:
```text
price > 0 or (zero_ok or price == 0))
```

### C2-09 - or -> and (nothing passes)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_priced_live_route_still_loads

old:
```text
price > 0 or (zero_ok and price == 0))
```
new:
```text
price > 0 and (zero_ok and price == 0))
```

### C2-10 - zero_ok branch allows negative prices
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_flag_never_lets_a_negative_or_non_finite_price_through

old:
```text
price > 0 or (zero_ok and price == 0))
```
new:
```text
price > 0 or (zero_ok and price >= 0))
```

### C2-11 - zero_ok ignored: price 0 always allowed
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-*]

old:
```text
price > 0 or (zero_ok and price == 0))
```
new:
```text
price > 0 or (price == 0))
```

### C2-12 - local_free inverted
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_zero_by_design_works_only_on_a_keyless_loopback_model; test_the_flag_is_refused_when_the_model_is_not_keyless_loopback[*]

old:
```text
    local_free = bool(getattr(llm, "keyless_loopback", False))
```
new:
```text
    local_free = not bool(getattr(llm, "keyless_loopback", False))
```

### C2-13 - local_free default True for kinds without the property (anthropic)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_flag_is_refused_when_the_model_is_not_keyless_loopback[llm0]

old:
```text
    local_free = bool(getattr(llm, "keyless_loopback", False))
```
new:
```text
    local_free = bool(getattr(llm, "keyless_loopback", True))
```

### C2-14 - local_free always true
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_flag_is_refused_when_the_model_is_not_keyless_loopback[*]

old:
```text
    local_free = bool(getattr(llm, "keyless_loopback", False))
```
new:
```text
    local_free = True
```

### C2-15 - zero_ok: flag and loopback -> or (a local model priced 0 with no flag passes)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_local_model_with_price_0_but_no_flag_is_refused

old:
```text
            zero_ok = r.price_is_zero_by_design and local_free
```
new:
```text
            zero_ok = r.price_is_zero_by_design or local_free
```

### C2-16 - zero_ok: loopback term dropped (the flag alone decides whether price 0 is allowed)
- file: `src/hadavin_sdk/config.py`
- expected: SURVIVE (equivalent). Classification settled in one place (`C2_16_WHY` in `make_mutants_v2.py`, also in `mutants-v2.json`): earlier text called it a gap; that was wrong.
- why equivalent: with the flag on a live model that is not keyless loopback, the check right above (`price_is_zero_by_design needs a keyless loopback model`) always adds a refusal, so the load fails with or without the loopback term. The mutant only drops the second message line (`a live model needs a price above 0`) for that one input. No config is accepted that the clean code refuses. A test for the missing line would pin message wording, not behaviour.
- evidence: scratch run `raw/V2C-C2-16.txt`: SURVIVED with the 43 route tests (baseline 43 passed). A survivor that is equivalent gets no new test.

old:
```text
            zero_ok = r.price_is_zero_by_design and local_free
```
new:
```text
            zero_ok = r.price_is_zero_by_design
```

### C2-17 - flag refusal condition inverted
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_flag_is_refused_when_the_model_is_not_keyless_loopback[*]

old:
```text
            if r.price_is_zero_by_design and not local_free:
```
new:
```text
            if r.price_is_zero_by_design and local_free:
```

### C2-18 - flag-on-wrong-kind refusal removed
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_flag_is_refused_when_the_model_is_not_keyless_loopback[*]

old:
```text
            if r.price_is_zero_by_design and not local_free:
```
new:
```text
            if False:
```

### C2-19 - one field zero is enough to pass (and -> or)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-*] (one field zero each)

old:
```text
                _price_ok(r.input_usd_per_mtok, zero_ok=zero_ok)
                and _price_ok(r.output_usd_per_mtok, zero_ok=zero_ok)
```
new:
```text
                _price_ok(r.input_usd_per_mtok, zero_ok=zero_ok)
                or _price_ok(r.output_usd_per_mtok, zero_ok=zero_ok)
```

### C2-20 - output price no longer checked (input checked twice)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-output_usd_per_mtok]

old:
```text
                _price_ok(r.input_usd_per_mtok, zero_ok=zero_ok)
                and _price_ok(r.output_usd_per_mtok, zero_ok=zero_ok)
```
new:
```text
                _price_ok(r.input_usd_per_mtok, zero_ok=zero_ok)
                and _price_ok(r.input_usd_per_mtok, zero_ok=zero_ok)
```

### C2-21 - input price no longer checked
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[0-input_usd_per_mtok]

old:
```text
                _price_ok(r.input_usd_per_mtok, zero_ok=zero_ok)
                and _price_ok(r.output_usd_per_mtok, zero_ok=zero_ok)
```
new:
```text
                _price_ok(r.output_usd_per_mtok, zero_ok=zero_ok)
                and _price_ok(r.output_usd_per_mtok, zero_ok=zero_ok)
```

### C2-22 - live inverted
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[*]; test_the_fake_model_may_cost_nothing

old:
```text
    live = llm.kind != "fake"
```
new:
```text
    live = llm.kind == "fake"
```

### C2-23 - price check also on the fake kind
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_fake_model_may_cost_nothing

old:
```text
    live = llm.kind != "fake"
```
new:
```text
    live = True
```

### C2-24 - price check only on the route named default (route-position gap)
- file: `src/hadavin_sdk/config.py`
- expected: SURVIVE? (the second route in the at-once test has a good price)
- expected killer: none known; proposed: route 'zcheap' priced 0 expects refusal naming it

old:
```text
        if live:
            zero_ok
```
new:
```text
        if live and name == "default":
            zero_ok
```

### C2-25 - only the LAST route (sorted) checked
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_every_route_refusal_is_reported_at_once (default lost)

old:
```text
    for name, r in sorted(routes.items()):
```
new:
```text
    for name, r in sorted(routes.items())[-1:]:
```

### C2-26 - only the FIRST route (sorted) checked
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_every_route_refusal_is_reported_at_once (route second lost)

old:
```text
    for name, r in sorted(routes.items()):
```
new:
```text
    for name, r in sorted(routes.items())[:1]:
```

### C2-27 - routes not sorted (message order only)
- file: `src/hadavin_sdk/config.py`
- expected: SURVIVE (equivalent)
- expected killer: none: only the order of the refusal lines changes; the tests use `in text`

old:
```text
    for name, r in sorted(routes.items()):
```
new:
```text
    for name, r in routes.items():
```

### C2-28 - route name dropped from the price message
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_every_route_refusal_is_reported_at_once

old:
```text
                out.append(f"route {name}: a live model needs a price above 0")
```
new:
```text
                out.append("a live model needs a price above 0")
```

### C2-29 - max_tokens > became >= (ceiling value refused)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_max_tokens_at_the_ceiling_loads

old:
```text
        if r.max_tokens > max_route_tokens:
```
new:
```text
        if r.max_tokens >= max_route_tokens:
```

### C2-30 - max_tokens ceiling off by one (200_001 loads)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_max_tokens_above_the_ceiling_is_refused[200001]

old:
```text
        if r.max_tokens > max_route_tokens:
```
new:
```text
        if r.max_tokens > max_route_tokens + 1:
```

### C2-31 - max_tokens comparison reversed
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_max_tokens_at_the_ceiling_loads; test_max_tokens_above_the_ceiling_is_refused[*]

old:
```text
        if r.max_tokens > max_route_tokens:
```
new:
```text
        if r.max_tokens < max_route_tokens:
```

### C2-32 - configured max_route_tokens ignored (default used)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_ceiling_is_a_config_field_and_can_be_lowered

old:
```text
refused = _route_refusals(self.routes, self.backends.llm, self.max_route_tokens)
```
new:
```text
refused = _route_refusals(self.routes, self.backends.llm, defaults.MAX_ROUTE_TOKENS)
```

### C2-33 - route refusals not collected at all
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::most tests

old:
```text
refused = _route_refusals(self.routes, self.backends.llm, self.max_route_tokens)
```
new:
```text
refused = []
```

### C2-34 - ceiling field gt=0 -> gt=1 (a ceiling of 1 refused)
- file: `src/hadavin_sdk/config.py`
- expected: SURVIVE? (only 0 is tested)
- expected killer: none known; proposed: max_route_tokens=1 with max_tokens=1 loads

old:
```text
    max_route_tokens: int = Field(default=defaults.MAX_ROUTE_TOKENS, gt=0)
```
new:
```text
    max_route_tokens: int = Field(default=defaults.MAX_ROUTE_TOKENS, gt=1)
```

### C2-35 - ceiling field gt=0 -> ge=0 (0 allowed)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_ceiling_field_itself_must_be_above_zero

old:
```text
    max_route_tokens: int = Field(default=defaults.MAX_ROUTE_TOKENS, gt=0)
```
new:
```text
    max_route_tokens: int = Field(default=defaults.MAX_ROUTE_TOKENS, ge=0)
```

### C2-36 - route max_tokens gt=0 -> gt=1
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_max_tokens_boundary_at_the_bottom

old:
```text
    max_tokens: int = Field(gt=0)
```
new:
```text
    max_tokens: int = Field(gt=1)
```

### C2-37 - route max_tokens gt=0 -> ge=0 (0 allowed)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_max_tokens_boundary_at_the_bottom

old:
```text
    max_tokens: int = Field(gt=0)
```
new:
```text
    max_tokens: int = Field(ge=0)
```

### C2-38 - route max_tokens lower bound removed (0 and -1 allowed)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_max_tokens_boundary_at_the_bottom

old:
```text
    max_tokens: int = Field(gt=0)
```
new:
```text
    max_tokens: int
```

### C2-39 - flag defaults to true
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_flag_defaults_to_false_and_does_not_change_the_agent_hash_input; test_a_local_model_with_price_0_but_no_flag_is_refused

old:
```text
    price_is_zero_by_design: bool = False
```
new:
```text
    price_is_zero_by_design: bool = True
```

### C2-40 - ceiling literal 1
- file: `src/hadavin_sdk/defaults.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_max_tokens_at_the_ceiling_loads

old:
```text
MAX_ROUTE_TOKENS = 200_000
```
new:
```text
MAX_ROUTE_TOKENS = 1
```

### C2-41 - ceiling literal 0 (every route refused)
- file: `src/hadavin_sdk/defaults.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_max_tokens_at_the_ceiling_loads

old:
```text
MAX_ROUTE_TOKENS = 200_000
```
new:
```text
MAX_ROUTE_TOKENS = 0
```

### C2-42 - ceiling literal -1
- file: `src/hadavin_sdk/defaults.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_max_tokens_at_the_ceiling_loads

old:
```text
MAX_ROUTE_TOKENS = 200_000
```
new:
```text
MAX_ROUTE_TOKENS = -1
```

### C2-43 - ceiling literal 200_001
- file: `src/hadavin_sdk/defaults.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_max_tokens_above_the_ceiling_is_refused[200001]

old:
```text
MAX_ROUTE_TOKENS = 200_000
```
new:
```text
MAX_ROUTE_TOKENS = 200_001
```

### C2-44 - ceiling literal 199_999
- file: `src/hadavin_sdk/defaults.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_max_tokens_at_the_ceiling_loads

old:
```text
MAX_ROUTE_TOKENS = 200_000
```
new:
```text
MAX_ROUTE_TOKENS = 199_999
```

### C2-45 - ceiling literal 2_000_000 (the extra-zero typo it guards)
- file: `src/hadavin_sdk/defaults.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_max_tokens_above_the_ceiling_is_refused[*]

old:
```text
MAX_ROUTE_TOKENS = 200_000
```
new:
```text
MAX_ROUTE_TOKENS = 2_000_000
```

### C2-46 - keyless_loopback: key term dropped (a loopback model WITH a key counts as free)
- file: `src/hadavin_sdk/backends/table.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_flag_is_refused_when_the_model_is_not_keyless_loopback[llm1] (LOCAL_WITH_KEY)

old:
```text
        return not self.api_key_secret_name and urlsplit(self.base_url).hostname in _LOOPBACK
```
new:
```text
        return urlsplit(self.base_url).hostname in _LOOPBACK
```

### C2-47 - keyless_loopback: host term dropped (any keyless host counts as local)
- file: `src/hadavin_sdk/backends/table.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_the_flag_is_refused_when_the_model_is_not_keyless_loopback[llm2] (REMOTE_NO_KEY)

old:
```text
        return not self.api_key_secret_name and urlsplit(self.base_url).hostname in _LOOPBACK
```
new:
```text
        return not self.api_key_secret_name
```

### C2-48 - keyless_loopback: and -> or
- file: `src/hadavin_sdk/backends/table.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::llm1 and llm2 cases

old:
```text
        return not self.api_key_secret_name and urlsplit(self.base_url).hostname in _LOOPBACK
```
new:
```text
        return not self.api_key_secret_name or urlsplit(self.base_url).hostname in _LOOPBACK
```

### C2-49 - keyless_loopback: host test inverted
- file: `src/hadavin_sdk/backends/table.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_zero_by_design_works_only_on_a_keyless_loopback_model

old:
```text
        return not self.api_key_secret_name and urlsplit(self.base_url).hostname in _LOOPBACK
```
new:
```text
        return not self.api_key_secret_name and urlsplit(self.base_url).hostname not in _LOOPBACK
```

### C2-50 - keyless_loopback: key test inverted
- file: `src/hadavin_sdk/backends/table.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_zero_by_design_works_only_on_a_keyless_loopback_model

old:
```text
        return not self.api_key_secret_name and urlsplit(self.base_url).hostname in _LOOPBACK
```
new:
```text
        return bool(self.api_key_secret_name) and urlsplit(self.base_url).hostname in _LOOPBACK
```

### C2-51 - loopback set widened by one remote host (also widens the existing http check at line ~80: only the new route-price use is the target here)
- file: `src/hadavin_sdk/backends/table.py`
- expected: SURVIVE? (no test uses a remote host in the set)
- expected killer: none known; equivalent for the tests, real for the rule; proposed: a keyless route to a non-loopback host is refused (REMOTE_NO_KEY covers example.com only through the host name `models.example.com`, which is not in the set)

old:
```text
_LOOPBACK = {"127.0.0.1", "localhost", "::1"}
```
new:
```text
_LOOPBACK = {"127.0.0.1", "localhost", "::1", "example.com"}
```

### A2-01 - step interval 0 -> 3600 (not every tick)
- file: `src/hadavin_sdk/runtime/tick.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_the_step_entry_points_at_the_right_function_and_runs_every_tick

old:
```text
    TickStep("audit_drain", 0, audit_drain),
```
new:
```text
    TickStep("audit_drain", 3600, audit_drain),
```

### A2-02 - STEPS entry points at the approvals reconcile
- file: `src/hadavin_sdk/runtime/tick.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_the_step_entry_points_at_the_right_function_and_runs_every_tick

old:
```text
    TickStep("audit_drain", 0, audit_drain),
```
new:
```text
    TickStep("audit_drain", 0, reconcile),
```

### A2-03 - step removed from STEPS
- file: `src/hadavin_sdk/runtime/tick.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_the_step_entry_points_at_the_right_function_and_runs_every_tick; tests/test_p7_tick.py::the step-order list test

old:
```text
    TickStep("audit_drain", 0, audit_drain),

```
new:
```text
(empty: the old text is deleted)
```

### A2-04 - failing rule: remaining > 0 -> >= 0 (always fails)
- file: `src/hadavin_sdk/runtime/tick.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_an_empty_outbox_is_green_and_says_zero

old:
```text
    if remaining > 0:
```
new:
```text
    if remaining >= 0:
```

### A2-05 - failing rule: remaining > 0 -> > 1 (one waiting event is green)
- file: `src/hadavin_sdk/runtime/tick.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_database_that_stays_down_leaves_the_step_failing

old:
```text
    if remaining > 0:
```
new:
```text
    if remaining > 1:
```

### A2-06 - failing rule: raise removed
- file: `src/hadavin_sdk/runtime/tick.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_damaged_row_fails_the_step_every_tick_but_never_blocks_the_rows_behind_it; test_a_stuck_outbox_stops_last_ok_at_from_advancing_and_exits_1

old:
```text
        raise RuntimeError(f"audit events still waiting: {remaining} (corrupt {corrupt})")
```
new:
```text
        return
```

### A2-07 - backlog() exception swallowed (unknown looks like empty)
- file: `src/hadavin_sdk/runtime/tick.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_an_unreadable_outbox_table_fails_the_step_not_a_green_zero

old:
```text
    remaining = backlog() if backlog is not None else 0
```
new:
```text
    try:
        remaining = backlog() if backlog is not None else 0
    except Exception:
        remaining = 0
```

### A2-08 - remaining forced to 0
- file: `src/hadavin_sdk/runtime/tick.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_database_that_stays_down_leaves_the_step_failing

old:
```text
    remaining = backlog() if backlog is not None else 0
```
new:
```text
    remaining = 0
```

### A2-09 - corrupt count not read
- file: `src/hadavin_sdk/runtime/tick.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_damaged_row_fails_the_step_every_tick_but_never_blocks_the_rows_behind_it; test_local_dir_corrupt_outbox_file_is_moved_aside_counted_and_logged

old:
```text
    corrupt = getattr(audit, "last_corrupt", 0)
```
new:
```text
    corrupt = 0
```

### A2-10 - drained count logged as 0
- file: `src/hadavin_sdk/runtime/tick.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_the_step_drains_the_outbox_and_logs_the_counts

old:
```text
    _LOG.info("audit_drain drained=%d remaining=%d corrupt=%d", drained, remaining, corrupt)
```
new:
```text
    _LOG.info("audit_drain drained=%d remaining=%d corrupt=%d", 0, remaining, corrupt)
```

### A2-11 - missing-reconcile guard removed
- file: `src/hadavin_sdk/runtime/tick.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_kind_without_reconcile_logs_one_line_and_passes

old:
```text
    if fn is None:
        _LOG.info(
```
new:
```text
    if False:
        _LOG.info(
```

### A2-12 - reconcile never called
- file: `src/hadavin_sdk/runtime/tick.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_the_step_drains_the_outbox_and_logs_the_counts

old:
```text
    drained = fn()
```
new:
```text
    drained = 0
```

### A2-13 - chain: last_corrupt not reset at the start of reconcile
- file: `src/hadavin_sdk/audit/chain.py`
- expected: SURVIVE? (no test reconciles twice, first with a bad row, then clean)
- expected killer: none known; proposed: reconcile twice, second run has no bad row, expect last_corrupt == 0

old:
```text
        self.last_corrupt = 0
        done = 0
        for event in list(self._pending):
            if self._drain(event):
```
new:
```text
        done = 0
        for event in list(self._pending):
            if self._drain(event):
```

### A2-14 - local_dir: last_corrupt not reset at the start of reconcile
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: SURVIVE? (same gap)
- expected killer: none known; same proposed test for LocalDirSink

old:
```text
        self.last_corrupt = 0
        done = 0
```
new:
```text
        done = 0
```

### A2-15 - chain: corrupt-row continue removed (the bad row falls through to the drain with a stale or unbound event)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_bad_row_is_skipped_logged_counted_and_the_good_row_behind_it_is_drained

old:
```text
                    event_id,
                )
                continue
            if self._drain(event):
```
new:
```text
                    event_id,
                )
            if self._drain(event):
```

### A2-16 - chain: corrupt rows not counted
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_bad_row_is_skipped_...(last_corrupt == 1)

old:
```text
                self.last_corrupt += 1
```
new:
```text
                pass
```

### A2-17 - local_dir: corrupt files not counted
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_local_dir_corrupt_outbox_file_is_moved_aside_counted_and_logged

old:
```text
                self.last_corrupt += 1
```
new:
```text
                pass
```

### A2-18 - chain: damaged row no longer caught (blocks the rows behind it)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_bad_row_is_skipped_...

old:
```text
            except ValueError as exc:
                self.last_corrupt += 1
```
new:
```text
            except KeyError as exc:
                self.last_corrupt += 1
```

### A2-19 - local_dir: corrupt file not moved aside
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_local_dir_corrupt_outbox_file_is_moved_aside_counted_and_logged

old:
```text
                os.replace(path, self.outbox / "corrupt" / path.name)
```
new:
```text
                pass
```

### A2-20 - drain: ORDER BY removed
- file: `src/hadavin_sdk/audit/chain.py`
- expected: SURVIVE? (tests do not assert the drain order of two or more rows)
- expected killer: none known; proposed: three outbox rows inserted out of order, assert the chain order equals the agreed order

old:
```text
ORDER BY event_id")
```
new:
```text
")
```

### A2-21 - drain: order swapped (descending)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: SURVIVE? (same)
- expected killer: same proposed test

old:
```text
ORDER BY event_id")
```
new:
```text
ORDER BY event_id DESC")
```

### A2-22 - chain: a failed DELETE is counted as drained (continue removed)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_row_that_was_written_but_cannot_be_deleted_is_not_counted_and_stays_waiting

old:
```text
                    continue
                done += 1
        return done

    def backlog
```
new:
```text
                    pass
                done += 1
        return done

    def backlog
```

### A2-23 - chain: DELETE never runs after the append (outbox never shrinks)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_the_step_drains_the_outbox_and_logs_the_counts

old:
```text
                    self._db.run("DELETE FROM audit_outbox WHERE event_id = ?", (event_id,))
```
new:
```text
                    pass
```

### A2-24 - chain: failed DELETE no longer caught (reconcile raises)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_row_that_was_written_but_cannot_be_deleted_is_not_counted_and_stays_waiting

old:
```text
                    self._db.run("DELETE FROM audit_outbox WHERE event_id = ?", (event_id,))
                except Exception as exc:
```
new:
```text
                    self._db.run("DELETE FROM audit_outbox WHERE event_id = ?", (event_id,))
                except KeyError as exc:
```

### A2-25 - chain _drain: DuplicateEvent swallow removed (a duplicate stays in the outbox forever)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_row_that_was_written_but_cannot_be_deleted_... (second reconcile == 2)

old:
```text
        except DuplicateEvent:
            pass
        except Exception:  # noqa: BLE001 - stays queued, retried next time
            return False
```
new:
```text
        except Exception:  # noqa: BLE001 - stays queued, retried next time
            return False
```

### A2-26 - chain _drain: failure reported as success (event dropped from the outbox)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_database_that_stays_down_leaves_the_step_failing

old:
```text
        except Exception:  # noqa: BLE001 - stays queued, retried next time
            return False
        return True
```
new:
```text
        except Exception:  # noqa: BLE001 - stays queued, retried next time
            return True
        return True
```

### A2-27 - chain: drained memory event never removed (re-counted every run)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: SURVIVE? (no v2 test drains _pending successfully)
- expected killer: none known; proposed (from the v1 proof tests): test_chain_reconcile_drains_memory_only_events_once

old:
```text
            if self._drain(event):
                self._pending.remove(event)
                done += 1
```
new:
```text
            if self._drain(event):
                done += 1
```

### A2-28 - chain: memory events never drained
- file: `src/hadavin_sdk/audit/chain.py`
- expected: SURVIVE? (same gap)
- expected killer: same proposed test

old:
```text
            if self._drain(event):
                self._pending.remove(event)
                done += 1
```
new:
```text
            if False:
                self._pending.remove(event)
                done += 1
```

### A2-29 - chain write_outcome: DuplicateEvent except removed (a duplicate goes to the outbox)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_duplicate_outcome_returns_the_event_id_and_logs_nothing

old:
```text
        except DuplicateEvent:
            return event.event_id
        except Exception as exc:  # noqa: BLE001 - the contract is "never raises"
```
new:
```text
        except KeyError:
            return event.event_id
        except Exception as exc:  # noqa: BLE001 - the contract is "never raises"
```

### A2-30 - chain write_outcome: duplicate returns None
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_duplicate_outcome_returns_the_event_id_and_logs_nothing

old:
```text
        except DuplicateEvent:
            return event.event_id
        except Exception as exc:  # noqa: BLE001 - the contract is "never raises"
```
new:
```text
        except DuplicateEvent:
            return None
        except Exception as exc:  # noqa: BLE001 - the contract is "never raises"
```

### A2-31 - chain write_outcome: `except Exception` placed BEFORE `except DuplicateEvent` (the duplicate branch is dead; a duplicate goes to the outbox)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_duplicate_outcome_returns_the_event_id_and_logs_nothing

old:
```text
        except DuplicateEvent:
            return event.event_id
        except Exception as exc:  # noqa: BLE001 - the contract is "never raises"
            # A line a person can alert on (audit A-01): the error type and the event id only, never the body.
            _LOG.warning(
                "audit outcome not appended (%s): event %s goes to the outbox",
                type(exc).__name__,
                event.event_id,
            )
            try:
                self._db.run(
                    "INSERT INTO audit_outbox (event_id, body) VALUES (?, ?) "
                    "ON CONFLICT (event_id) DO NOTHING",
                    (event.event_id, event.model_dump_json()),
                )
            except Exception as exc2:  # noqa: BLE001
                _LOG.error(
                    "audit outbox not written (%s): event %s is held in memory only",
                    type(exc2).__name__,
                    event.event_id,
                )
                self._pending.append(event)
            return None

```
new:
```text
        except Exception as exc:  # noqa: BLE001 - the contract is "never raises"
            # A line a person can alert on (audit A-01): the error type and the event id only, never the body.
            _LOG.warning(
                "audit outcome not appended (%s): event %s goes to the outbox",
                type(exc).__name__,
                event.event_id,
            )
            try:
                self._db.run(
                    "INSERT INTO audit_outbox (event_id, body) VALUES (?, ?) "
                    "ON CONFLICT (event_id) DO NOTHING",
                    (event.event_id, event.model_dump_json()),
                )
            except Exception as exc2:  # noqa: BLE001
                _LOG.error(
                    "audit outbox not written (%s): event %s is held in memory only",
                    type(exc2).__name__,
                    event.event_id,
                )
                self._pending.append(event)
            return None
        except DuplicateEvent:
            return event.event_id

```

### A2-32 - chain: outbox warning removed
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_failed_outcome_write_logs_type_and_id_but_never_the_body

old:
```text
            _LOG.warning(
                "audit outcome not appended (%s): event %s goes to the outbox",
                type(exc).__name__,
                event.event_id,
            )

```
new:
```text
(empty: the old text is deleted)
```

### A2-33 - chain: outbox warning downgraded to DEBUG
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_failed_outcome_write_logs_type_and_id_but_never_the_body

old:
```text
_LOG.warning(
                "audit outcome not appended
```
new:
```text
_LOG.debug(
                "audit outcome not appended
```

### A2-34 - chain: warning leaks the error text
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_failed_outcome_write_logs_type_and_id_but_never_the_body

old:
```text
"audit outcome not appended (%s): event %s goes to the outbox",
                type(exc).__name__,
```
new:
```text
"audit outcome not appended (%s): event %s goes to the outbox",
                exc,
```

### A2-35 - chain: warning logs the run id instead of the event id
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_failed_outcome_write_logs_type_and_id_but_never_the_body

old:
```text
goes to the outbox",
                type(exc).__name__,
                event.event_id,
```
new:
```text
goes to the outbox",
                type(exc).__name__,
                event.run_id,
```

### A2-36 - chain: memory-only ERROR downgraded to DEBUG
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_when_the_outbox_table_also_fails_an_error_line_is_logged

old:
```text
_LOG.error(
                    "audit outbox not written
```
new:
```text
_LOG.debug(
                    "audit outbox not written
```

### A2-37 - chain: event no longer kept in memory when the outbox write also fails (audit loss)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_when_the_outbox_table_also_fails_an_error_line_is_logged (len(_pending) == 1)

old:
```text
                self._pending.append(event)
            return None

```
new:
```text
            return None

```

### A2-38 - chain backlog: memory events not counted
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_events_held_in_memory_count_as_remaining

old:
```text
        return len(self._pending) + int(rows[0][0])
```
new:
```text
        return int(rows[0][0])
```

### A2-39 - chain backlog: table rows not counted
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_database_that_stays_down_leaves_the_step_failing

old:
```text
        return len(self._pending) + int(rows[0][0])
```
new:
```text
        return len(self._pending)
```

### A2-40 - chain: unreadable-table warning removed
- file: `src/hadavin_sdk/audit/chain.py`
- expected: SURVIVE? (no test asserts this line)
- expected killer: none known; proposed: caplog on a failing SELECT expects one WARNING with the type only

old:
```text
            _LOG.warning("audit outbox not readable (%s): retried next tick", type(exc).__name__)
            return done
```
new:
```text
            return done
```

### A2-41 - local_dir: outbox warning removed
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_the_local_dir_kind_logs_one_warning_with_type_and_id_never_the_error_text

old:
```text
            _LOG.warning(
                "audit outcome not written (%s): event %s goes to the outbox",
                type(exc).__name__,
                event.event_id,
            )

```
new:
```text
(empty: the old text is deleted)
```

### A2-42 - local_dir: warning downgraded to DEBUG
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_the_local_dir_kind_logs_one_warning_...

old:
```text
_LOG.warning(
                "audit outcome not written
```
new:
```text
_LOG.debug(
                "audit outcome not written
```

### A2-43 - local_dir: warning leaks the error text
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_the_local_dir_kind_logs_one_warning_...

old:
```text
"audit outcome not written (%s): event %s goes to the outbox",
                type(exc).__name__,
```
new:
```text
"audit outcome not written (%s): event %s goes to the outbox",
                exc,
```

### A2-44 - local_dir write_outcome: DuplicateEvent except removed
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_the_local_dir_duplicate_path_logs_nothing

old:
```text
        except DuplicateEvent:
            return f"{event.event_id}.json"
        except Exception as exc:
```
new:
```text
        except KeyError:
            return f"{event.event_id}.json"
        except Exception as exc:
```

### A2-45 - local_dir: event dropped when the outbox folder is also unusable
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: SURVIVE? (no v2 test makes the outbox unusable)
- expected killer: none known; proposed (v1 proof test): test_local_dir_reconcile_drains_memory_only_events_once

old:
```text
            except Exception:  # noqa: BLE001
                self._pending.append(event)
            return None
```
new:
```text
            except Exception:  # noqa: BLE001
                pass
            return None
```

### A2-46 - local_dir reconcile: drained memory event never removed
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: SURVIVE? (same gap)
- expected killer: same proposed test

old:
```text
            self._pending.remove(event)
            done += 1
        if not self.outbox.exists():
```
new:
```text
            done += 1
        if not self.outbox.exists():
```

### A2-47 - local_dir reconcile: outbox file never deleted after a successful write
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_the_real_local_dir_kind_drains_through_the_tick_step (outbox empty)

old:
```text
            path.unlink()
            done += 1
```
new:
```text
            done += 1
```

### A2-48 - local_dir reconcile: DuplicateEvent on an outbox file no longer absorbed (file stays forever)
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: SURVIVE? (no test puts an already-written event in the outbox folder)
- expected killer: none known; proposed: write the event, copy it into outbox/, reconcile expects the file gone

old:
```text
            except DuplicateEvent:
                pass
            except Exception:  # noqa: BLE001, S112 - safe to swallow: the file is not unlinked
```
new:
```text
            except Exception:  # noqa: BLE001, S112 - safe to swallow: the file is not unlinked
```

### A2-49 - local_dir backlog: memory events not counted
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: SURVIVE? (no local_dir test holds events only in memory)
- expected killer: none known; proposed: _pending with unusable outbox, backlog() == 1

old:
```text
        return len(self._pending) + waiting
```
new:
```text
        return waiting
```

### A2-50 - local_dir backlog: counts everything in outbox (the corrupt/ folder, temp files)
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_local_dir_corrupt_outbox_file_is_moved_aside_counted_and_logged (corrupt/ would count as 1)

old:
```text
        waiting = len(list(self.outbox.glob("*.json"))) if self.outbox.exists() else 0
```
new:
```text
        waiting = len(list(self.outbox.glob("*"))) if self.outbox.exists() else 0
```

### A2-51 - local_dir backlog: files never counted
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_stuck_outbox_stops_last_ok_at_from_advancing_and_exits_1

old:
```text
        waiting = len(list(self.outbox.glob("*.json"))) if self.outbox.exists() else 0
```
new:
```text
        waiting = 0
```

### A2-52 - local_dir: corrupt-file ERROR downgraded to DEBUG
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: SURVIVE? (the test uses caplog at INFO and asserts the counts, not this line)
- expected killer: none known; proposed: caplog at ERROR expects the file name and type only

old:
```text
                _LOG.error(
                    "audit outbox file not readable
```
new:
```text
                _LOG.debug(
                    "audit outbox file not readable
```

### A2-53 - chain: corrupt-row ERROR downgraded to DEBUG
- file: `src/hadavin_sdk/audit/chain.py`
- expected: KILLED
- expected killer: tests/test_a01_audit_reconcile.py::test_a_bad_row_is_skipped_logged_counted_... (asserts ValidationError and the id in caplog.text at INFO; DEBUG is not captured at INFO)

old:
```text
                _LOG.error(
                    "audit outbox row not readable
```
new:
```text
                _LOG.debug(
                    "audit outbox row not readable
```

### C2-52 - negative zero accepted as a price without the flag (only -0 passes; 0 and -1 still refused)
- file: `src/hadavin_sdk/config.py`
- expected: KILLED
- expected killer: tests/test_c01_route_limits.py::test_a_zero_or_negative_price_is_refused_for_a_live_model[-0-input_usd_per_mtok] and [-0-output_usd_per_mtok]

old:
```text
price > 0 or (zero_ok and price == 0))
```
new:
```text
price > 0 or (price.is_zero() and price.is_signed()) or (zero_ok and price == 0))
```

### C2-53 - negative zero refused even when the flag allows a zero price (0 passes, -0 does not)
- file: `src/hadavin_sdk/config.py`
- expected: SURVIVE? (no test sets the flag with a price of -0)
- expected killer: none known; proposed: LOCAL_LLM + price_is_zero_by_design + price '-0' loads (decimal -0 equals 0, so the flag allows it)

old:
```text
price > 0 or (zero_ok and price == 0))
```
new:
```text
price > 0 or (zero_ok and price == 0 and not price.is_signed()))
```

### A2-54 - chain write_outcome: except widened to BaseException (a Ctrl-C or exit during the write is swallowed and sent to the outbox)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: SURVIVE? (no test makes the write raise something other than Exception, so widening to BaseException is not seen)
- expected killer: none known; proposed: a fake table or folder whose write raises KeyboardInterrupt; the call must propagate it and nothing may reach the outbox

old:
```text
        except Exception as exc:  # noqa: BLE001 - the contract is "never raises"
```
new:
```text
        except BaseException as exc:  # noqa: BLE001 - the contract is "never raises"
```

### A2-55 - chain _drain: except widened to BaseException (an interrupt during a drain is swallowed and the event stays queued)
- file: `src/hadavin_sdk/audit/chain.py`
- expected: SURVIVE? (no test makes the write raise something other than Exception, so widening to BaseException is not seen)
- expected killer: none known; proposed: a fake table or folder whose write raises KeyboardInterrupt; the call must propagate it and nothing may reach the outbox

old:
```text
        except Exception:  # noqa: BLE001 - stays queued, retried next time
```
new:
```text
        except BaseException:  # noqa: BLE001 - stays queued, retried next time
```

### A2-56 - local_dir write_outcome: except widened to BaseException
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: SURVIVE? (no test makes the write raise something other than Exception, so widening to BaseException is not seen)
- expected killer: none known; proposed: a fake table or folder whose write raises KeyboardInterrupt; the call must propagate it and nothing may reach the outbox

old:
```text
        except Exception as exc:  # noqa: BLE001 - disk errors, a corrupt index line: the contract is "never raises"
```
new:
```text
        except BaseException as exc:  # noqa: BLE001 - disk errors, a corrupt index line: the contract is "never raises"
```

### A2-57 - local_dir reconcile (memory events): except widened to BaseException
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: SURVIVE? (no test makes the write raise something other than Exception, so widening to BaseException is not seen)
- expected killer: none known; proposed: a fake table or folder whose write raises KeyboardInterrupt; the call must propagate it and nothing may reach the outbox

old:
```text
            except Exception:  # noqa: BLE001, S112 - safe to swallow: the event is still in memory
```
new:
```text
            except BaseException:  # noqa: BLE001, S112 - safe to swallow: the event is still in memory
```

### A2-58 - local_dir reconcile (outbox files): except widened to BaseException
- file: `src/hadavin_sdk/audit/local_dir.py`
- expected: SURVIVE? (no test makes the write raise something other than Exception, so widening to BaseException is not seen)
- expected killer: none known; proposed: a fake table or folder whose write raises KeyboardInterrupt; the call must propagate it and nothing may reach the outbox

old:
```text
            except Exception:  # noqa: BLE001, S112 - safe to swallow: the file is not unlinked
```
new:
```text
            except BaseException:  # noqa: BLE001, S112 - safe to swallow: the file is not unlinked
```

Except-widening (review 3 M-F): A2-54..A2-58 change `except Exception` to `except BaseException` at the four places the review named (chain write_outcome, chain _drain, local_dir write_outcome, local_dir reconcile twice). Scratch run result: all five SURVIVED (`raw/V2A-A2-54.txt` .. `V2A-A2-58.txt`), so this is a real test gap, now listed for the lead; the proposed test is in each section.

## Not covered by this list (honest gaps of the plan itself)
- Mutants of the test files, of `reprobe_sources`, `K1bAudit` (no `reconcile`: the step logs one line) and of the Postgres path (the dead-man query was never run; Postgres tests are skipped here).
- Mutants in `tests/test_p7_tick.py` beyond the step-list entry, the G5 wording patch (text only), and any behaviour of `max_route_tokens` outside `Config` validation.
- The list is hand-made. A tool-made set (for example a mutation tool run on only the changed lines) would be a second opinion; not tried here (tool ladder rung 1: our own runner exists and is reused).
- Two mutants change shared text: C2-51 widens `_LOOPBACK`, which the existing plain-http check also uses; read its result with that in mind.
