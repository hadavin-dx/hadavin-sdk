# Hostile review 2, step C (price constraint), branch cloud/core-b
Reviewer: fresh, read-only (no source or test edits). 2026-11-20. Scratch repros: /tmp/core-b-scratch-C/p1.py, p2.py, p3.py (run with `uv run --all-extras --group test python <file>`). The two C test files pass (256 passed). No Blocker found; the stated invariants hold for every value I tried through `load_config`. Findings below are gaps around them.

## Probed and HELD (no finding)
Zero, "-0", negative, "NaN", "inf", "-inf", "1e-7", "1e-400", "1e-999999999", "1e999999999", 1000000.000001, 999999.9999999, "0x10", float 1e-07 (refused by `_money`), bool, None, list, in demo and pilot, both fields. Zero in pilot/prod and in demo with a real kind: refused, names route and field only. Secrets typed into price, date, max_tokens or a list: never echoed (hide_input_in_errors works). prices_as_of: future (UTC), 2026-02-30, year 0000, "2026-1-1", int, "", True, 1.5, timestamp text, full-width digits: all refused; missing/None in pilot: refused. config_hash untouched. fake llm in pilot/prod: refused by DEMO_ONLY (config.py:~527) and also by the zero rule.

## Findings

### H1 (Medium) Stale price table is accepted forever; the date is attestation only
config.py:583-584 refuses only a FUTURE date. Repro p2.py: pilot with prices_as_of 1970-01-01, 2000-01-01, 0001-01-01 and 2019-01-01 all LOAD. Nothing reads `prices_as_of` after load (grep: only config.py), so it is neither logged, audited, nor in config_hash. Scenario: provider raises prices, nobody touches the key, caps fire late or never; or an operator writes 1970-01-01 to get past the "required" rule. The ticket says "old date not refused this round" (inv. 5), so this is a known limit, but it should be recorded as an accepted risk with an owner, and the date should at least be emitted at start-up / in the audit start event so a reviewer can see it. Fix: a max age in defaults (warn or refuse), or surface the date.

### H2 (Medium) Low Decimal context precision makes `Route._price` raise a raw InvalidOperation out of `load_config`
config.py:95 `v.quantize(Decimal("1E-6"))` uses the thread's Decimal context. Repro p3.py: with `localcontext().prec = 6`, a legal price "123456.123456" raises `decimal.InvalidOperation` (an ArithmeticError, not ValueError), which pydantic does not convert and `load_config` (config.py:682-685) does not catch: a traceback instead of ConfigError. The docstring claims a huge exponent cannot make quantize raise; a small context precision can. Same context also silently rounds the cost arithmetic in llm/common.py:98-101, 266-268 and llm/fake.py:51-52, so a host that sets a low global precision gets wrong costs without error. Fix: do the 6-decimal test without context (`v.as_tuple().exponent` / `v == v.quantize(..., context=Context(prec=60))`), and have the cost sites use an explicit context. Likelihood low (needs a host that changes the context); impact is fail-loud at load, wrong cost at runtime.

### H3 (Low) Price text is read more loosely than "a decimal string"
config.py:67 `Money` passes pydantic's lax string-to-Decimal. Repro p1.py: "5_0" loads as 50, " 5 " and "5\n" load as 5, Arabic-Indic "١٢" and full-width "１２" load as 12, "0.1e1" as 1, int 5 loads. A typo `1_5` becomes 15 and `2_000` becomes 2000 without notice, and a mixed-script string can hide a digit in review. Not cap-defeating, but a money field should be ASCII `[0-9.]` only. Fix: regex check in `_money` for str input (and say whether ints are allowed).

### H4 (Low) Smallest legal price is practically zero for a real model
config.py:96 allows 0.000001 USD per Mtok in pilot/prod (loads, p1.py/p3.py). 100k input + 4k output tokens cost 1.04e-7 USD, so any cap above a cent never fires, which is the same failure the zero rule exists to stop. There is a ceiling but no floor. Fix: a floor for non-fake routes (for example 0.01 per Mtok), or state it as accepted.

### H5 (Low) Route names are echoed unescaped into the error
config.py:571-573 puts the route NAME in the refusal text. Repro p2.py: a route named "sk-SECRET\nX" appears (newline included) in the ConfigError. The name is operator-written config, not a price value, so the "never the value" claim holds, but a name can carry a secret by mistake or a newline into logs. Use `{name!r}`.

### H6 (Low, known, restate) Paths that skip validation
`Route.model_construct(...input_usd_per_mtok=-1...)` and `model_copy(update={"input_usd_per_mtok": "-1"})` (p2.py) produce a Route with a negative (even str) price and no check; `Config.model_copy` skips `_price_refusals` too (the C tests use this to set the stage). Runtime sites (llm/common.py:98, 266; llm/fake.py:51; k1b/loop.py:106) trust the price and have no second check, so a str price would raise TypeError mid-call rather than be refused. Only replay re-checks zero (k1b/replay.py:85-90). The demo's own loader (demos/ask-your-data/askdata/config.py:40-65, fixtures.py:24) builds Route directly: zero loads there (review-1 cb-1, still open); negative gives a raw ValidationError. Demo with kind fake + injected real client prices at 0 (cb-2), left to step F. Nothing new, but there is no runtime assertion at the gate (`worst_case_for`, llm/common.py:~118) that a route price is positive when the client is not the fake; that is the cheap closing line for step F.

### H7 (Nit) Config reload
`load_config` is called once per start (app.py:116, cli.py:171, 368); no hot reload exists, so a reload cannot re-introduce a bad price except through H6 paths. A new process re-validates. Nothing to fix.

## Not run
No live model calls, no pilot service start, no store. Decimal-vs-float: floats are refused at the YAML edge (`_money`), so float precision does not enter; Decimal ceiling arithmetic at default precision (28) stays exact up to the worst-case 12-place quantize (see H2 for non-default contexts).
