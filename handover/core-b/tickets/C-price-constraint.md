# TICKET C: price constraint (owner core-b SPINE). Written 2026-11-20 from the lead's draft (inputs/draft-tickets-C-D.md), checked by core-b against origin/main 51c9fc4 and origin/core/P4a 4a0976f.
- Package: step C of plan-v4-final B1. Path class: money. Extended review: no. Migration: none. Ticket review: one EGM round.
- Depends on: nothing merged first. Read-only input: PR #78 core/P4a (two validators, commits c31f336 and 781b8ba).
- S = src/hadavin_sdk. Stages are demo, pilot, prod. Tests are written by a different agent than the builder.
- The code below was tried on a scratch copy of main with pydantic 2.14.1 / pydantic-core 2.50.1 (the versions pinned in uv.lock:1662-1679): results are quoted under "Checked". No test suite was run.

## Problem in plain words
The cost of a model call is tokens times the price written on the route in config.yaml (S/llm/common.py:166-169, S/llm/fake.py:50-53). If that price is zero or negative, every call costs nothing or less, so no spending cap can ever fire. Today a config with such a price loads without complaint; only the replay command refuses a zero price, and only for the one route of the one agent it runs (S/k1b/replay.py:85-90). Nobody can tell from a config how old its prices are. After C a bad price is refused when the config loads, and a pilot or prod config must state the day its prices were read.

## Checked: the draft's citations on main
| Citation | Result |
|---|---|
| S/config.py:57-64 Money, no bounds | CONFIRMED |
| S/config.py:72-76 Route, both prices required | CONFIRMED |
| S/config.py:398-400 detector route must exist | CONFIRMED |
| S/config.py:407-430 the refuse-everything-at-once list | CONFIRMED (`_cross_checks` starts at 391-392; list 407-430) |
| S/config.py:409-412 demo-only kinds refused in pilot and prod | CONFIRMED |
| S/registry.py:116-119, 125, 135 Route is inside config_hash | CONFIRMED (dump 116-119 uses exclude_defaults; judge route 125; agent route 135) |
| S/registry.py:342-343 unknown model_route refused | CONFIRMED |
| S/llm/common.py:166-169 cost | CONFIRMED |
| S/llm/fake.py:51-52 cost | CONFIRMED (whole expression is 50-53) |
| S/k1b/replay.py:85-90, 118 | CONFIRMED |
| S/backends/table.py:593-595 (llm, fake) is demo-only | CONFIRMED |
| tests/test_k3_pilot_env.py:47 | CORRECTED: 47 is the price line inside `pilot_cfg` (35-87); the new key goes after line 43 (`"environment": env,`) |
| tests/test_k1b_replay.py:382 model_copy to zero | CONFIRMED (helper 381-385) |

## Checked: the draft's UNVERIFIED items
- NaN / Infinity: RESOLVED. pydantic 2.14.1 refuses "NaN", "sNaN", "Infinity", "-Infinity" and Decimal("NaN") for a Decimal field by itself (error type finite_number), with or without the Money wrapper. bool is refused (decimal_type); float is refused by `_money`. "-1" and "-0" LOAD on main.
- `Field(ge=0)` with the `Money` Annotated type: it WORKS ("-1" refused, type greater_than_equal) but it lets "-0" through, and the draft's own edge list had "-0" loading. Minus zero is a signed value that prices as zero; the P4a validator refuses it. `Field(ge=0)` is therefore NOT used.
- Pilot/prod fixtures that need `prices_as_of`: ONE edit. Every pilot or prod config that loads successfully in tests/ comes from `pilot_cfg` (tests/test_k3_pilot_env.py:35-87). Its users: tests/test_k3_pilot_env.py, test_client_profile.py (also `prod_cfg`, 43-54), test_k5_round5.py, test_k5_round8_postgres.py, test_k5_round9b.py, test_k5_round10.py, test_k5_tools.py. The other pilot/prod tests need no change: they expect a refusal and match a substring (test_p1b_backends.py:82-95, test_p3b_neutral_audit.py:249-262, test_p4_secrets.py:115-118, test_stage_names.py:194-201, 233-260), or set the stage with model_copy, which skips validation (test_stage_names.py:271-275, 287-296), or call `_anchor_refusals` directly (warden_port/test_audit_chain.py:544-562). No YAML or doc file in the repo says environment pilot or prod. No fixture has a zero, negative, over-6-decimal or huge price (all are 2, 3.00, 10, 15.00).
- config_hash: UNCHANGED. It is built from the agent, its route dump (model_id, two prices, max_tokens), the action contracts, the llm kind and six llm settings, judge routes, tool pins, tools and the gate bar (S/registry.py:107-165). A validator on Route adds no field; `prices_as_of` is on Config and is not read by config_hash. Tried: the fixture agent's hash is 3ac5b7c3...f1be9e on main, with the change, and with `prices_as_of` set.

## NEEDED-CHECK
ONE-PLACE-PER-JOB: sign, finiteness, ceiling and decimals of a price are checked in one place, `Route._price`; "zero only for fake in demo" and the price date in one place, `_price_refusals`, joined into the one refused list of `Config._cross_checks`. The replay check (S/k1b/replay.py:85-90) is not a second copy: it guards what load cannot see (the `llm_kind` override at replay.py:118 and configs changed by model_copy). Verdict: NEEDED, small, own code.

## RUNG TABLE (CODE-LAST v1; scale of 2026-11-06: 1 no-code tools, 2 our core modules, 3 existing free tools, 4 free libraries, 5 own code)
| Component | Need | Rung tried | Evidence (2026-11-20) | What only our code gives | Verdict |
|---|---|---|---|---|---|
| Negative / non-finite price refused | no cap-defeating price loads | 4 pydantic | 2.14.1 refuses non-finite by itself; `Field(ge=0)` refuses "-1" but passes "-0" (tried) | minus zero, ceiling, 6 decimals, our own error text | KEEP-CODE (14 lines, taken from P4a) |
| Zero only for fake in demo | zero price cannot reach a real model | 2 core: `_cross_checks` list, `is_live`, DEMO_ONLY | list exists (config.py:407-430); no price rule in it | the rule itself (depends on kind and stage; no library knows them) | KEEP-CODE as glue in the existing list |
| Price date | operator states price age | 4 pydantic date type | lax date also reads whole-day timestamps and datetime text (tried) | required-in-pilot-and-prod, not-in-future, plain-date-only | KEEP-CODE |
| Rungs 1 and 3 | n/a | n8n, MCP, model features | a config load check runs before any tool or model exists | n/a | not applicable |

## INVARIANTS
1. No config loads with a price that is negative, minus zero, not finite, above 1,000,000 USD per million tokens, or with more than 6 decimals; any stage, any kind.
2. A zero price loads only when backends.llm.kind is fake AND environment is demo. Both conditions are tested in the code, not inferred from the demo-only table.
3. The rules cover every entry of `routes`, including judge routes and routes no agent uses, and both price fields.
4. Every refusal names route and field (`routes.<name>.<field>`), never the value. Zero-price and date refusals join the existing refused list, so they appear beside the other environment refusals in one error. Route-level refusals (invariant 1) are pydantic field errors: all of them appear together, but before the refused list (limit: a config with a negative price AND a zero price needs two fix rounds).
5. `prices_as_of` is required in pilot and prod; it is a date or the text YYYY-MM-DD; it is not later than today in UTC; an old date is not refused this round.
6. config_hash of every existing agent is unchanged. Lines 407-416 of S/config.py keep their exact text (tests/stage_mutants.py:66, 90 pin them).

## Decision: P4a's validators versus the draft's lines
`Route._price` is taken VERBATIM from core/P4a (S/config.py there, commit c31f336), with its constant. Reasons: it refuses minus zero (the draft's `Field(ge=0)` does not), a later merge of P4a material in step F sees identical text, and tests/test_route_prices.py on P4a can be reused. It brings two rules the draft did not ask for (ceiling 10**6, at most 6 decimals); no fixture breaks; see open question 1.
`Config._priced_routes_for_real_backends` from P4a (commit 781b8ba) is NOT taken. Quoted:
```python
    @model_validator(mode="after")
    def _priced_routes_for_real_backends(self) -> Config:
        if self.backends.llm.kind != "fake":
            zero = [name for name, r in self.routes.items()
                    if r.input_usd_per_mtok == 0 or r.output_usd_per_mtok == 0]
            if zero:
                raise ValueError(f"routes with a zero input or output price need the fake llm kind: {', '.join(sorted(zero))}")
        return self
```
What it lacks against the plan ("zero allowed ONLY for kind fake AND stage demo"): (a) no stage test: fake with a zero price is let through in any stage, and it is safe today only because another line (config.py:409-412) happens to refuse fake in pilot and prod; (b) it raises on its own before `_cross_checks`, so the operator sees it without the other refusals and its text ("need the fake llm kind") is wrong advice in pilot; (c) it names the route but not the field; (d) no price date. The replacement keeps its comparison (`== 0`) and its idea, as a helper feeding the refused list.

## Files
Create: tests/test_price_constraint.py (by a different agent). Delete: nothing.
Modify S/defaults.py, append after line 131 (verbatim from P4a defaults.py:135-137):
```python
# The most one model price may be, in USD per million tokens. 10**6 is one dollar per token, far above any list price
# known to the author; it is not read from a provider's price list (UNVERIFIED), so a lead may lower it.
MAX_ROUTE_PRICE_USD_PER_MTOK = 10**6
```
Modify S/config.py (line numbers of main):
(a) after line 8 (`import re`): `from datetime import UTC, date, datetime`
(b) after line 76, inside Route (verbatim from P4a; `field_validator` is already imported, line 22):
```python
    @field_validator("input_usd_per_mtok", "output_usd_per_mtok")
    @classmethod
    def _price(cls, v: Decimal) -> Decimal:
        """Finite (pydantic already refuses non-finite Decimals; kept as a second line), not negative or minus zero,
        at most `defaults.MAX_ROUTE_PRICE_USD_PER_MTOK`, at most 6 decimals (checked last, so a huge exponent cannot
        make `quantize` raise)."""
        if not v.is_finite():
            raise ValueError("a price must be a finite number")
        if v.is_signed():
            raise ValueError("a price must not be negative")
        if v > defaults.MAX_ROUTE_PRICE_USD_PER_MTOK:
            raise ValueError(f"a price may be at most {defaults.MAX_ROUTE_PRICE_USD_PER_MTOK}")
        if v != v.quantize(Decimal("1E-6")):
            raise ValueError("a price may have at most 6 decimal places")
        return v
```
(c) between line 376 (`made_up_data_only`) and 377 (`root: Path`) the field, and after 377 the validator:
```python
    # The day the route prices were read from the provider's price list (UTC), YYYY-MM-DD; required in pilot and prod.
    # On Config, not on Route: a route is inside config_hash, so a date there would un-qualify agents at every refresh.
    prices_as_of: date | None = None
    root: Path

    @field_validator("prices_as_of", mode="before")
    @classmethod
    def _plain_date(cls, v: object) -> object:
        """A date, or the text YYYY-MM-DD; nothing else (pydantic alone would also read whole-day timestamps)."""
        text = isinstance(v, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", v)
        if v is not None and not text and (not isinstance(v, date) or isinstance(v, datetime)):
            raise ValueError("prices_as_of must be a date written YYYY-MM-DD")
        return v
```
(d) after line 421 (`refused += _anchor_refusals(...)`): `        refused += _price_refusals(self)`
(e) before `_anchor_refusals` (line 446), two module-level functions:
```python
def _today() -> date:
    return datetime.now(UTC).date()  # a function, so a test can set the day


def _price_refusals(cfg: Config) -> list[str]:
    """A zero price makes every reply cost 0, so no spend cap could fire: only the fake llm kind in demo may have one
    (negative and non-finite prices are refused on Route). Names route and field, never the price."""
    live = is_live(cfg.environment)
    out = []
    if live or cfg.backends.llm.kind != "fake":
        out = [
            f"routes.{name}.{field}: a zero price is allowed only for the fake llm kind in demo"
            for name, route in sorted(cfg.routes.items())
            for field in ("input_usd_per_mtok", "output_usd_per_mtok")
            if getattr(route, field) == 0
        ]
    if live and cfg.prices_as_of is None:
        out.append("prices_as_of is required in pilot and prod (the day the route prices were read)")
    if cfg.prices_as_of is not None and cfg.prices_as_of > _today():
        out.append("prices_as_of is in the future (UTC)")
    return out
```
Modify tests/test_k3_pilot_env.py: after line 43 add `"prices_as_of": "2026-11-01",` (a fixed past day; placed here, away from the lines P4a changes at 58 and 74).
Not touched: S/k1b/replay.py, S/registry.py, README, SECURITY, CHANGELOG (the capped-spend sentence of plan B3 enters only with step F).

## Signatures and the new config field
- `Route._price(cls, v: Decimal) -> Decimal` (field validator, raises ValueError).
- `Config._plain_date(cls, v: object) -> object` (before-validator, raises ValueError).
- `config._today() -> date`; `config._price_refusals(cfg: Config) -> list[str]` (private; not in `__all__`).
- `defaults.MAX_ROUTE_PRICE_USD_PER_MTOK = 10**6`.
- New config.yaml key, top level: `prices_as_of: 2026-11-01` (quoted or not; YAML reads the unquoted form as a date). Optional in demo, required in pilot and prod. Every failure surfaces from `load_config` as ConfigError (config.py:540-543), from direct `Config(...)` as pydantic ValidationError.

## Interfaces
Offered: the guarantee "a loaded Config has every route price > 0, or exactly 0 only with fake in demo"; step F's meter may rely on it, but only for configs built by validation (model_copy and model_construct skip it, which is why the replay check stays). Needed: nothing from other steps.

## Tests (tests/test_price_constraint.py)
Helpers that exist: fixture `cfg_dir` and `make_cfg(tmp_path)` (tests/conftest.py:39, 74) give a demo config with llm fake and prices 3.00 / 15.00; `pilot_cfg(tmp_path, env=..., config={...})` (tests/test_k3_pilot_env.py:35) gives a pilot config with real kinds (llm openai_compat). Edit config.yaml with yaml.safe_load / safe_dump. "Real kind in demo" = set backends.llm to `{"kind": "openai_compat", "base_url": "https://llm.example/v1"}` and `made_up_data_only: true`. Set the day with `monkeypatch.setattr(config, "_today", lambda: date(2026, 11, 20))`. Expected result is ConfigError from `load_config` unless marked LOADS.
Normal:
- N1 demo, fake, 3.00 / 15.00: LOADS, `prices_as_of` is None.
- N2 pilot_cfg as shipped (real kind, with the date): LOADS; the same with env prod through `prod_cfg`: LOADS.
- N3 demo, real kind, 3.00 / 15.00, no date: LOADS.
Edge:
- E1 demo + fake with price "0", "0.00", "0E-10", integer 0, each on input and on output: LOADS.
- E2 demo + real kind with each E1 value: refused; message contains `routes.default.<field>` and "zero price".
- E3 zero on input only, on output only, and on a second route no agent uses (real kind): each refused and the right route and field named; zero on a judge route (detector llm_judge naming it): refused.
- E4 pilot + fake + zero price (fixture config with environment set to pilot): the one error contains "llm: fake" AND `routes.default.input_usd_per_mtok` AND "prices_as_of is required".
- E5 pilot_cfg with `prices_as_of` removed: refused, "prices_as_of is required"; pilot_cfg with input price "0": refused.
- E6 date equal to today: LOADS; today plus one day: refused "in the future"; three years old: LOADS; unquoted YAML date: LOADS.
- E7 prices "0.000001" and "1000000": LOAD. "1000000.000001", "1E+30", "0.0000001", "1E-30": refused.
- E8 config_hash: load the fixture registry, record `config_hash("test-agent")`; add `prices_as_of`; the hash is equal. Also assert the fixed value 3ac5b7c34e7a0d7750a75adcd4642364be70af601e8078ee6b46c0dfb0f1be9e only if the test agent finds the same value on main (else pin equality only).
Hostile:
- H1 prices "-1", "-0", "-0.00", "NaN", "sNaN", "Infinity", "-Infinity", float 0.0, float 3.0, bool true, with fake in demo: each refused (this pins pydantic's own NaN refusal against a later upgrade).
- H2 the error text for a refused price "-123.456789" contains neither "123" nor "456789"; for a zero refusal it contains the route name and no price.
- H3 two routes with negative prices: both `routes.<name>.<field>` in one error. Two routes with zero (real kind): all zero fields in one error, sorted by route name.
- H4 `prices_as_of` given as 0, 1700006400, "1700006400", true, "", "20/11/2026", "2026-11-20T00:00:00", "2026-02-30", a datetime, "٢٠٢٦-١١-٢٠" (non-ASCII digits): each refused.
- H5 `Config.model_copy(update=...)` to a zero price still loads nothing new: the replay check refuses it (existing tests/test_k1b_replay.py:381-391 stays green, not rewritten).
- H6 `prices_as_of` nested under a route is refused (Route forbids extra keys).
FAIL-BEFORE (fails on today's main by assertion "DID NOT RAISE", not by import error; it must not use `_today`): demo + real kind + `made_up_data_only: true` + input price "0" must raise ConfigError; same for price "-1" with fake. On main both configs load.
Regression run (existing files, unchanged except the one fixture line): tests/test_k3_pilot_env.py, test_client_profile.py, test_stage_names.py, test_p1b_backends.py, test_k1b_replay.py, test_k5_tools.py, test_k5_round5.py, test_k5_round9b.py, test_k5_round10.py, warden_port/test_audit_chain.py.

## Mutation plan
| Mutant | Killed by |
|---|---|
| M1 drop the stage test (`if live or` removed) | E4, E5 (pilot zero) |
| M2 drop the kind test (`if live:` only) | E2 |
| M3 `== 0` to `< 0` in `_price_refusals` | E2 |
| M4 only the input field checked | E3 output-only |
| M5 `is_signed()` branch removed | H1 "-1", "-0" |
| M6 ceiling or decimals branch removed | E7 |
| M7 `live and` removed from the required-date rule | N1, N3 |
| M8 required-date rule removed | E5 |
| M9 `>` to `>=` in the future rule | E6 today |
| M10 `_plain_date` returns v unchecked | H4 (0, timestamps, datetime text) |
| M11 `refused += _price_refusals(self)` removed | E2, E5 |

## Evidence commands (raw output saved under handover/core-b/evidence/C/)
- `git stash; uv run --all-extras --group test pytest tests/test_price_constraint.py` on main: the FAIL-BEFORE tests fail (save as fail-before.txt); `git stash pop`.
- `uv run --all-extras --group test pytest tests/test_price_constraint.py`
- `uv run --all-extras --group test pytest tests/test_k3_pilot_env.py tests/test_client_profile.py tests/test_stage_names.py tests/test_p1b_backends.py tests/test_k1b_replay.py tests/test_k5_tools.py tests/warden_port/test_audit_chain.py`
- `uv run --all-extras --group test ruff check src tests` and `ruff format --check src tests`; the mutant run with the list above; then the full suite once.

## Rollback
Tag `pre-C`. No migration, no stored data, no hash change: reverting the commit restores the old behaviour completely. After a revert a config that carries `prices_as_of` no longer loads (extra keys are forbidden), so operators remove the key or keep the commit.

## What stays out
Refusing an old price date (plan B3 says so in words); a price floor above zero; looking prices up at a vendor; a separate price table; bounds on Budget (S/registry.py:34-37); reserve and settle (step F); changing or deleting the replay check; the README / SECURITY / CHANGELOG capped-spend sentence (with step F); "unknown model refused" from plan row C needs no code (S/registry.py:342-343 and S/config.py:398-400 already do it).

## Open questions with recommended answers
1. Keep P4a's ceiling and 6-decimal rules in this step? Recommended YES: verbatim reuse, no fixture breaks; it changes the draft's answer on tiny prices: 1E-30 is now refused, the smallest positive price is 0.000001.
2. "Today" in UTC with no slack? Recommended YES: an operator east of UTC writing the local day in the first hours of that day is refused once and writes the UTC day; the message says UTC. A host clock set far back refuses start, which is the safer side.
3. Future-date rule also in demo when a date is given? Recommended YES (one rule, no stage branch).
4. Negative-price and zero-price refusals arrive in two fix rounds when both are present (invariant 4). Accept? Recommended YES; merging them would move sign checks out of Route.
5. Does #78 add a price table or price date? NO (notes/heads-stop-audit-price.md C.4.5); price stays on the route.
6. fake in demo with an injected real model double and zero prices: out of scope here; step F meters it.

## Size
About 50 source lines including comments and docstrings (27 statements; the draft said 20 and did not count `_price` or the plain-date guard), 3 lines in defaults.py, 1 fixture line, about 150 test lines.

## Done
The plan's stop rule for C, plus all gates green: tests, ruff, bandit, guard tests, CodeQL, SonarCloud, CodeRabbit. Reviewers: correctness and adversarial, fresh agents, given the diff, this ticket and the evidence only.
