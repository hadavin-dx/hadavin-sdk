Package Q8a-1 (live override refusals; security path), head 3f3d4b6c, round 6, persona: design critic.

Verdict: M1 is not fully closed. One real path echoes a configured value (credentials included) in a config error, one YAML path bypasses the sanitiser, and the CHANGELOG sentence is wider than the code. I did not run anything; all findings are from reading the snapshot.

### [D1] Major - a URL with non-ASCII look-alike characters echoes the whole netloc, login included, in a config error
Where: `config.py:180-187` (`url_has_login`), `config.py:414-421`; also `backends/table.py:79` (OpenAICompat `base_url`) and `backends/table.py:317` (Vault `address`). The text reaches the user through `config.py:499-506` (`_value_free_text`, which prints `e['msg']`), `config.py:134` and `config.py:562`.
What: `url_has_login` swallows `ValueError` from `urlsplit` and returns False. The next call, `url_allowed` (config.py:193), calls `urlsplit` again and lets the `ValueError` escape. For a non-ASCII netloc that changes under NFKC into one containing `/ ? # @ :`, CPython's `urlsplit` raises `ValueError("netloc '<the whole netloc>' contains invalid characters under NFKC normalization")`. This is from memory of the standard library; I did not run it. The netloc includes `user:pw@host`.
Pydantic wraps this as `Value error, netloc '...'`, and `_value_free_text` keeps `msg` as is. The `include_input=False` setting does not remove text that is already inside the message. The `table.py` validators have the same shape (bare `urlsplit(self.address)` / `urlsplit(self.base_url)`).
Why it matters (concrete input -> wrong output): `systems: {crm: {base_url: "https://svc<fullwidth @ or :>pw@host"}}` makes `load_config` raise a `ConfigError` whose text contains the pasted login. The CHANGELOG (line 15) and the `config_error_text` docstring promise "never the value that was refused", and that a login in a `base_url` is not shown. A login written this way is exactly the shape of secret the r5 item named. The r5 plan also asked for a test with a credential in `base_url`. A grep of the tests shows no non-ASCII netloc case, so this path is untested.
Suggested fix: in `url_has_login`, treat `ValueError` as refusal ("base_url is not a valid URL", no text). Do the same, with a fixed sentence, around the `urlsplit` calls in `url_allowed`'s callers and in `table.py:79` and `table.py:317`. As a class fix, `config_error_text` and `_value_free_text` could replace the `msg` of any `value_error` whose origin is not our own validators with the type name only. Add a test with fullwidth `@` and `:` in the netloc for `systems`, the OpenAICompat `base_url` and the Vault `address`. It must fail on 3f3d4b6c.

### [D2] Major - `tools/<agent>.yaml` YAML errors escape unsanitised
Where: `registry.py:261` (`parse_manifest(_yaml(path), where)` inside `_load_tools`), called from `registry.py:234` outside any `try`.
What: the `try` blocks at `registry.py:210-216` and `registry.py:222-230` cover agents, actions, principals and chains. The per-agent tools manifest is read later and is not covered. A malformed `tools/<agent>.yaml` raises a raw `yaml.YAMLError`. Its `str()` quotes the offending source line with a caret, and the line can hold a token (for example a pasted header value). It is not a `ConfigError`, so it bypasses `config_error_text` and `from None`. The CLI at `cli.py:304` prints only `ConfigError`, so the exception surfaces as an uncaught traceback with the quoted line. I read `cli.py:301-304` in the base checkout, which the head did not change.
Why it matters: bad YAML in a tools manifest -> traceback text that includes the line. The CHANGELOG sentence "what `load_registry` raises ... a YAML error with its line and column only" is false for this file.
Suggested fix: wrap `_yaml(path)` at line 261 the same way as lines 215-216 (`except yaml.YAMLError as exc: raise ConfigError(config_error_text(exc)) from None`), or put the whole `_load_tools` call in the existing handler. Add a test with a made-up credential on a broken YAML line in `tools/<agent>.yaml`.

### [D3] Minor - the "value-free" claim is wider than the code for registry cross-check messages
Where: `registry.py:348`, `registry.py:349`, `registry.py:384`, `registry.py:386`, `registry.py:380`; `registry.py:251` and `registry.py:302` (file name and operation); also base `tools.py:113` (`key {key!r}`).
What: these messages print values taken from config files: the `model_route` value, a `verify_check` / `rollback` reference, a `target_system`, a `chain_id`, and a manifest key. They are identifiers, not secrets, and the CHANGELOG says "names of fields, kinds and items are shown". Even so, the sentence at CHANGELOG line 15 says "does not cover the names of fields, kinds and items" but the text `unknown model_route <value>` shows a value, not a name.
Also, dict keys are echoed through `loc` in validation errors: an unknown top-level key, a key under `systems`, a key under `routes`, `scope_inventory <source>` at `config.py:409`, and `system {name}` at `config.py:416` and `config.py:419`. `_Strict` comment (config.py:60) says "a mistyped key may hold a secret: errors name the field". A secret pasted as a key name is therefore still shown.
Suggested fix: either say in the CHANGELOG that identifier values and mapping keys are shown by design (the most honest option), or drop the value from these texts. Do not claim more than the code keeps.

### Checks on the r5 fixes
- M1, `str(exc)` and `__cause__` (r5 item 1): fixed for the paths it named. `config_error_text` (config.py:509-522) returns a layout without the value, YAML errors keep line and column only, other errors keep the type only. All `load_config` handlers (config.py:559-564), `_one` (config.py:134) and `registry.py:216` and `registry.py:230` use `from None`. See D1 and D2 for the gaps.
- Line 465 duplicate key: now the line number only. OK. Unknown kind (config.py:114) and unknown capability (config.py:143): now names or counts only. OK.
- `base_url` with a login (config.py:415-416): refused without the URL for the normal case. OK, except D1.
- `_validation_text` (config.py:525-541): both branches value-free (the rename branch uses fixed sentences plus `msg`).
- `include_url=False`, `include_context=False`, `include_input=False` are all set in `_value_free_text`.
- Item 7, STEPS copy: `tick.py:458-460` takes one copy and the loop at 478 uses it. OK. The `steps is None` branch is fine because a given `steps` is refused when live.
- Items 3 and 4, `replace()` message and subclass ban: `tick.py:57-60` and `tick.py:84-87`, with the CHANGELOG upgrade sentence at line 13. OK.
- Item 8: the CHANGELOG now says "measured at ecd5dba1" with the evidence path.
- Item 9, IMPOSSIBLE-NOW: the wording is plain and names the three probes and the purge identity (CHANGELOG line 17-22; docstrings at `tick.py:79-82`). I agree with the "impossible in-process" classification for `object.__setattr__` and direct store purge. The control named is least privilege; the test cited is not re-run by me.
- App refusals (`app.py:132-179`): the order is `_static_vault_tokens` before any backend, then the two old refusals, then the six overrides with `is not None`, then the timeout check. Error texts contain only fixed names plus the parameter name. `app.py:376` (`the CA {ca_file or ca_secret_name!r}`) prints a configured path or secret name, a name rather than a secret value. `app.py:356` and `app.py:400` print names only.
- Logging: `tick.py:133` and the `_safe_log` calls log the exception type only. `app.py:214` logs only the inventory key name, same class as D3.

### Checked and found fine
- Refusal message texts and first-given ordering (`app.py:165-174`).
- `clock` default None and `now if clock is None else clock` (`app.py:179`).
- `VaultConnection` public rename (`table.py`) and use by `_static_vault_tokens`.
- `TickContext` live-given-time refusal, exact type check `_now` (`tick.py:100-107`).
- The duplicate-name and missing-built-in checks (`tick.py:461-464`).
- `executor_timeout_ok` bool, NaN and infinity handling (`config.py:171-177`).

### Not checked
- I ran no tests, no mutants and no Postgres runs. I did not re-run the evidence runner.
- I did not read the full test files (`test_q8a_live_overrides.py` is about 1000 lines; I only grepped it for value-echo assertions and found one at line 753).
- I did not verify the NFKC raise by execution. It relies on the CPython `urlsplit` behaviour (`_checknetloc`) as I remember it; the caller should confirm with one line of Python before fixing.
- Backend connection-time errors (for example Vault HTTP failures) and `deferred.key_problems` texts: out of the diff, not read in full.
- `_static_vault_tokens` body and `stage_mutants.py` kill coverage (D1 to D3 would need new mutants for any fix).