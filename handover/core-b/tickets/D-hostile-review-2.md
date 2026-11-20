# D-config hostile review 2 (fresh reviewer, read only; nothing in src or tests edited)
Scope: config.py (TriggerSender/TriggerSettings/Config.triggers), secret_name.py, backends/platform_secrets.py (check_senders), app.py (_sender_secrets, check order, release/reset refs), defaults.py TRIGGER_*, tests/test_trigger_secret_names.py + test_trigger_secret_reader.py (110 passed here), requests/001.answer.md, D-config-review-1.md. Scratch scripts: /tmp/core-b-scratch-D/r1.py .. r4.py (run with .venv/bin/python from the repo root).
Result: 0 Blocker, 2 Medium, 4 Low, 1 Info.

## M1 Medium: mounted_file aliases with ".." inside a name get past the overlap check (the docstring says they must collide)
- src/hadavin_sdk/secret_name.py:11-16 (docstring claims "x", "./x" and "a/../x" collide); tests/test_trigger_secret_names.py:38 pins the opposite (`("a/../x", "a_x")`).
- Scenario: backend `*_secret_name` (or tool/source/executor name) is "a/../slack_token"; a sender lists "slack_token". `mounted_file` resolves both to `<dir>/slack_token` (the provider calls `confined()` which resolves ".."). canonical("a/../slack_token") is "a_slack_token", so `check_senders` does not refuse, and `app.trigger_secret("slack_token")` returns the backend's credential. Only the sender side is restricted (no "/" and no ".."); other_names is free text.
- Repro (/tmp/core-b-scratch-D/r3.py): `MountedFileProvider(d).get("a/../slack_token")` equals `.get("slack_token")`; `check_senders(P(), {"s":["slack_token"]}, {"a/../slack_token"})` returns with no error.
- Fix: for names on the "other" side, canonicalise by first normalising the path (posixpath.normpath, drop "." segments) or refuse any other-name containing ".." or "/" ; or compare with the provider's own resolver. Change the test at line 38 and the docstring either way.

## L1 Low (demo only): canonical form folds Unicode differently from the env provider
- secret_name.py:16 lower-cases first, then replaces. secrets_env.py:22 replaces every non-[A-Za-z0-9] character first, then upper-cases.
- Scenario: other name "slackİtoken" (Turkish dotted capital I) or "slackKtoken" (Kelvin sign) and sender "slack_token". Env variable for both is `P_SLACK_TOKEN`. canonical gives "slacki_token" / "slackktoken" vs "slack_token": no collision, check_senders passes, the sender reads the backend's secret. The same gap in the other direction (non-ASCII in a sender) is closed because the sender charset is ASCII.
- Repro: /tmp/core-b-scratch-D/r3.py first loop prints "NOT REFUSED (same env var)". Fuzz in r2.py also finds "İ" vs "." as an under-collision.
- Fix: `re.sub(r"[^A-Za-z0-9]+", "_", name).lower()` (replace first, then lower). Equivalent for ASCII, and every non-ASCII character becomes "_" as the env kind does. Add a test with İ and K. (env kind is demo-only, hence Low.)

## L2 Low: "the provider is not on the App" is not true for a Python caller; reader trusts `in` on a str subclass
- app.py:352-368. (a) `app.trigger_secret.__closure__` holds the frozenset and the whole provider: `[c.cell_contents for c in r.__closure__]` gave `['frozenset', 'P']` (r1.py). Any code holding App can read any secret. Same pattern as `_own_secrets`, so consistent, but the App comment and CHANGELOG line 347 state it as a guarantee. (b) A `str` subclass with `__eq__` returning True and a fixed `__hash__` passes `name in allowed` and the provider is then called with an unlisted name ("anything" reached the provider in r1.py). (c) An unhashable argument raises TypeError (known nit 9).
- Fix: `if type(name) is not str or name not in allowed`; keep the closure but word the comment as "not reachable through the normal API", or hold the provider in a small class with `__slots__` and no public attribute. All in-process, so Low.

## L3 Low: lower bounds accept values that make the endpoint useless
- config.py:385-401. Accepted (r1.py): max_body_bytes=1, ack_wait_s=1e-300 and 5e-324, max_running=1. Zero, negative, NaN, inf, bool, quoted, 2**80, 524289, 30.0000001 are all refused (checked). A config typo (ack_wait_s: 0.0005 meant 0.5, or max_body_bytes: 1) loads and every request then answers 503 or is refused.
- Fix: add a sensible floor (e.g. ack_wait_s >= 0.1, max_body_bytes >= 1024) in defaults.py with named constants.

## L4 Low: bad input is still reachable after load, and a bad id is echoed
- config.py:685 and load_config's `from exc` keep the pydantic ValidationError as `__cause__`; with hide_input_in_errors the str is clean, but `exc.__cause__.errors()` still carries the typed value (r4.py: "errors() has secret? True"; `include_input=False` is clean). Walking `__cause__` or a structured logger that dumps `.errors()` prints a mistyped secret_names entry. (Known nit 7; I confirm it with a repro.)
- A bad sender key or an extra key is printed in the location (r4.py: both True). Documented in DRAFT 3 but the CHANGELOG does not say so. A YAML syntax error near a secret_names line also prints that source line (yaml marks), pre-existing.
- Fix: in load_config raise `ConfigError(_validation_text(exc)) from None` for the triggers path, or `from exc.with_traceback(None)` after stripping input; document the location echo.

## L5 Low: CHANGELOG describes the old code
- CHANGELOG.md:334 still says secret names may contain "/" (dropped in round 2; charset is `A-Za-z0-9_.:-`, no "..", needs a letter or digit). Lines 329-347 do not mention: names compared in canonical form ("db-pass" = "DB_PASS" = "db.pass"), RuntimeError("sender secret unavailable"), the separate start step before the main secret check, or that a non-live agent refuses the whole start.
- defaults: no other hard-coded copy of 524288/4/64/5.0/30 in src or docs (grep); the "524288" appears only in a defaults.py comment and the CHANGELOG, both as text.

## Info (no action required, or worker/lead decision)
- I1: the reader is one allow-list over ALL senders' names (app.py:366-369 builds `{n for names in sender_names.values() ...}`). Sender A's code path can read sender B's secret if the worker passes B's name; isolation depends on the worker looking names up by sender id. State it in the worker ticket and add a worker test with two senders.
- I2: TriggerSettings is frozen but `senders` is a plain dict: `cfg.triggers.senders["x"] = TriggerSender(...)` after build adds a sender with no registry check; the reader's allow-list is a snapshot, so a name added later is refused (good). No config reload exists in src (grep "reload": none for config), so a reload means a new build and a new reader; an old App keeps its old allow-list.
- I3: `_trigger_problems` (registry.py:340) checks principal kind "service" only; a service principal with `rights` or `approver_of` entries can still be a sender. Decide if that is wanted.
- I4: when the provider fails, `read` raises after the handler with `from None` (checked: `__context__` None, `__cause__` None, suppress True; no logging calls carry a name in app.py or platform_secrets.check_senders; logging capture in r2.py was empty). It does keep an outer exception if the worker calls it inside its own `except` block (`__context__` = caller's KeyError); the worker should not call it from a handler. platform_secrets.check (not the sender path, platform_secrets.py:66-68) still prints the name and chains `from exc`; correct for non-sender names, but a sender name never gets there because check_senders runs first and only tests other names.

## Checked and held
- Sender names colliding with backend/tool/source/executor/restored-hash/reset/release names by case, "-" vs "_" vs ".", trailing "." or space, newline, double separators, "./x": all refused (r2.py). Two senders with "a-b"/"A_B", and the same name twice in one sender: refused (config.py:405-420), never printing a name.
- Odd reader arguments (unicode, NUL, newline, 100000 characters, case folds, dotless i, bytes, None, int): PermissionError with fixed text, provider never called; list gives TypeError with no name.
- Sender name charset: "\n", NUL, non-ASCII, fullwidth, zero-width, 129 characters, "..", ".", "-", ":" all refused with the value hidden; 128 characters accepted.
- Bounds: see L3 for what is accepted; everything else refused.
- tests: 110 passed (names + reader files).
