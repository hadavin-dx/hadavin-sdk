# P6b1 round 3, adversarial review (ticket revision 3)
Status: REPORTED (saved by the lead session from the reviewer's hand-back, which is model output, not user authority).

P6b1 revision 3, round 3 adversarial review. Verdict: no Blocker. The ticket is buildable. The remaining Majors and Minors are cuts or small test and wording fixes, and none is a decision left to guess.

Cites checked against the current checkout. All held (table.py:20-40, :43-89, :332-344, :365-370; config.py:317, :349-374, :377-397; factory.py:29-66). The caller said the checkout may differ from ce70eb5. No cite failed.

| id | severity | ticket line | problem | fix |
|---|---|---|---|---|
| R3-ADV-1 | Major | 190-193, 305-311, 413 | `Config.no_training_max_age_days`, its 180 ceiling, the ceiling constant, the bounds rows in T4 and mutants M13 and M28 are surface the ticket does not need. The operator can raise the limit to 180 days. That defeats the "re-verify within 90 days" rule the ticket cites (`tool-ladder-before-code.md`). Order 7(3) says cut surface. | Use one fixed constant of 90, with no config field. This drops the `Config` key, the ceiling constant, the T4 bounds rows, M13, M28, the `_field_error` use in T4 and one hot-file edit in `config.py`. If the lead wants a field, say why in PENDING LEAD. |
| R3-ADV-2 | Major | 213-218, 342-346, 401 | The `factory.make` log line adds an edit to a hot file, a logger, T11 and M16. It enforces nothing. `build(llm=...)` skips it (the ticket says so). The config file in version control is the record (PENDING LEAD 6). | Cut it. This drops `factory.py`, T11 and M16. Keep T10 and T8. Test count goes from 19 to 18. |
| R3-ADV-3 | Minor | 346 | T11 says "needs no SDK", which is UNVERIFIED. `make` imports `entry.factory`'s module, and the `openai_compat` factory may import an SDK. The extra check at factory.py:44-48 raises `ConfigError` if it is missing. | Moot if R3-ADV-2 is applied. Otherwise patch `importlib.import_module` or `entry.factory`, or mark the test skipped-as-failed when the SDK is absent. |
| R3-ADV-4 | Minor | 177, 202-203 | The (f) message prints the expected host, which is derived from `base_url` or `resource`. `urlsplit().hostname` is not covered by the `hosts` pattern. The `openai_compat` validator checks only the scheme and loopback (table.py:77-85). A host containing a control character or ANSI escape would reach the ConfigError and terminal. Line 208 says only the reference is never printed. | In (f), print expected hosts only if they fullmatch the hosts pattern. Otherwise print `<unprintable host>`. Add one T14 row. |
| R3-ADV-5 | Minor | 121, 201 | The binding is host name only. It ignores port, scheme and path. Two endpoints on one host (a gateway with `/v1` and `/v2`, or two ports) share one statement. Line 121 names the model and gateway limits, not this one. | Add one plain sentence to "What the code does NOT check", the README and the CHANGELOG. No code. |
| R3-ADV-6 | Minor | 406, 332-333 | M21 is killed for the wrong reason. Renaming the top-level field to `no_training_secret_name` makes every `no_training=` keyword fail with `extra_forbidden`. T8's equality never reaches `secret_names`. | Add a direct assertion that no field of any llm settings class named `no_training*` ends in `_secret_name`. Alternatively, run `secret_names` on a `model_construct`ed object. |
| R3-ADV-7 | Minor | 386-416 | Mutants that would survive: (1) `environment != "dev"` weakened to `== "prod"`, which T1 pilot rows do kill, so list it; (2) the `if h` filter dropped in the expected-hosts set, giving `[""]` instead of "none" (the T14 no-host row kills it, but no mutant names it); (3) sign of the age subtraction swapped; (4) `self_hosted` added to the `anthropic` set (T3 kills it). | Add M32 to M34 with their killers. Alternatively, say they are covered by T1, T14 and T3. |
| R3-ADV-8 | Minor | 171-183, 316-318 | The pattern mechanism is not stated. The ticket says "fullmatch", but a builder could write `re.match` with `$`, which accepts a trailing newline. T7 lists `\n` without saying where. | State `re.fullmatch` or `\Z` for `reference`, `hosts` and the date. Add T7 rows with a TRAILING newline for all three fields (`"2026-11-05\n"`, `"llm.example\n"`, a reference ending in `\n`). |
| R3-ADV-9 | Minor | 128, 4 | The path class is "security". The package decides whether client document text may go to a model provider. That is close to the redaction and data-leak class. Order 20(6) gives a money or redaction package one extra ticket round. The ticket picks "security" partly to forgo that round. | Not a code change. Add one line asking the lead to confirm the classification (PENDING LEAD 12). The ticket is frozen after this round regardless. |
| R3-ADV-10 | Nit | 381 | The count line is correct (3 + 20 + 6 = 29), but "Fixed-size rows I counted" omits T14 (about 4 kinds x 8 rows) and T7. | Say "not counted" for T14 and T7, or count them. |
| R3-ADV-11 | Nit | 385, 416 | M31 and the T16 equivalents rely on an "equivalent, stated" runner status. The ticket marks that status UNVERIFIED. | Say that if the runner lacks it, the evidence file records it by hand. |
| R3-ADV-12 | Nit | 184 | `hosts: list[str]` inside a `frozen=True` model makes the statement object unhashable. Nothing in `src/` hashes settings (grep found no `hash(` or `lru_cache` on them). | Use `tuple[str, ...]` or leave as is. Note it in the build notes. |

**Statement check: what can still reach a real model with no statement or a wrong one**
- A config labelled `dev` (PENDING LEAD 10).
- An llm injected through `build(llm=...)`. The load-time refusal still applies to the config, so this is a code-level path, not a config path.
- `detector: bedrock_guardrail` (excluded, with a v1.1 row).
- Any key tier, model, route or gateway-upstream difference behind an attested host.
- Port, scheme and path differences on the same host (R3-ADV-5).
- A false statement that is well formed. The ticket states this as "operator-attested".
- `environment` is `Literal["dev","pilot","prod"]` (config.py:317), so there is no unknown-environment bypass.
- The capability keys in `TABLE` are secrets, signer, anchor, store, audit, llm, detector and channel. No other capability sends text to a model, so there is no further llm-class sibling. The ticket's own sibling grep lists only detector and channel; line 485 covers detector.
- I found no Blocker-level bypass. The ticket states the dev-label hole and the injection path plainly.

**Fail-before table**
- Only the T1 rows are real proof (4 pilot "DID NOT RAISE", 4 prod text assertion). By reading the code the table is consistent with that.
- On old code, `monkeypatch.setattr` on the missing `_utc_today` raises AttributeError, and `no_training` keys give `extra_forbidden`. The `_field_error` rule fails on `loc == ("no_training",)` plus `extra_forbidden`, so the rows do not pass vacuously.
- The pins (T1b, T6, T15, the three T7 pin rows) pass on old code as claimed.
- The table is derived by reading, not by running. Step 4 settles it.

**Template fields**
All 17 are present. Mutation plan rows were checked against killers. M7, M9, M12, M17, M19, M22, M23 and M27 are killed by the stated tests.

**Money and redaction**
- No money path.
- No secret is placed in the refusal text for `reference`. The `hosts` printing hole is R3-ADV-4.
- `reference` is not printed on refusal paths.
- No real-looking secret appears in the ticket.

**Verified by reading**
- The `_cross_checks` insertion point between :371 and :372.
- `DEV_ONLY` handling: `fake` is refused as `llm: fake`.
- `Entry` is a frozen dataclass with defaults, so adding `no_training` is safe.
- The hosts functions (:365-370).
- The loopback rule (:68-85), so the T14 `[::1]` row loads.
- `_one` and `load_config` cause chains (config.py:117-120, :451-454; read, not run).
- `make(capability, settings, provider, **available)` accepts `routes=` only if the capability's `ALLOWED` set lists it (UNVERIFIED for llm).

**Not checked**
- I did not run anything. That includes pydantic, Python 3.12, `date.fromisoformat` on non-ASCII digits, and the `str()` form of wrapped errors.
- I did not read the `llm/*.py` modules, the P4a, P6a, P6b2 or P4d tickets, README's loopback claim, or the mutation runner.
- I did not check the hot-file lists or merge-order cites.
- I did not read `handover/reviews/` or `handover/evidence/`, per the independence rule.
- I did not check `FakeLLMSettings` attribute access inside `_no_training_refusals`. This only matters if M14 is applied, and the early DEV_ONLY return avoids it in correct code.