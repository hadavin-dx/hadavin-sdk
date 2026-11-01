"""The live wiring: the secrets kind, the DSN, the model route and the smoke abort rule.

Everything external goes through the core backend table (`hadavin_sdk.backends`), so no vendor SDK is imported here:
the secrets kind (`env`, `aws_secrets_manager`, `vault`, ...) and the LLM kind (`anthropic`, `bedrock`, ...) are
config entries. Building the model route constructs the client but sends nothing; the first network call happens at
`chat()`, and nothing in the tests makes one.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

from askdata.config import AskdataConfig, ConfigError, load_config
from askdata.pgsource import Limits
from askdata.settings import Smoke
from hadavin_sdk.actions.secrets import SecretProvider
from hadavin_sdk.backends import make
from hadavin_sdk.backends.table import TABLE, KindSettings
from hadavin_sdk.errors import ConfigError as CoreConfigError
from hadavin_sdk.llm.protocol import LLM

DSN_ENV = "ASKDATA_DSN"

# Smoke abort rule (amendments A-03, step 1): checked after every question of a live smoke run.


def _kind(capability: str, raw: Mapping[str, Any]) -> KindSettings:
    kinds = TABLE[capability]
    name = raw.get("kind")
    if name not in kinds:
        raise ConfigError(f"{capability}: kind must be one of {sorted(kinds)}")
    try:
        return kinds[name].settings(**raw)
    except ValueError:  # a pydantic error: the field names are in the type, a value may be a secret
        raise ConfigError(f"{capability}: invalid settings for kind {name!r}") from None


def make_provider(cfg: AskdataConfig) -> SecretProvider | None:
    """The secrets kind named in the config, or None when the config names none."""
    if cfg.secrets is None:
        return None
    try:
        return make("secrets", _kind("secrets", cfg.secrets))
    except CoreConfigError as err:
        raise ConfigError(f"secrets: {err}") from None


DSN_VARS = {"a": "ASKDATA_DSN", "b": "ASKDATA_DSN_B", "clean": "ASKDATA_DSN_CLEAN"}
_SECRET_FIELDS = {
    "a": "dsn_secret_name",
    "b": "dsn_secret_name_b",
    "clean": "dsn_secret_name_clean",
}


def resolve_dsn(
    cfg: AskdataConfig | None,
    provider: SecretProvider | None = None,
    environ: Mapping[str, str] = os.environ,
    which: str = "a",
) -> str | None:
    """`provider.get(<secret name>)` when the config names a secret for database `which` ("a", "b" or "clean");
    otherwise (documented fallback) that database's environment variable (ASKDATA_DSN, ASKDATA_DSN_B,
    ASKDATA_DSN_CLEAN). A named secret that cannot be read is an error, never a silent fallback."""
    field = _SECRET_FIELDS[which]
    name = getattr(cfg.database, field) if cfg else None
    if not name:
        return environ.get(DSN_VARS[which]) or None
    provider = provider or (make_provider(cfg) if cfg else None)
    if provider is None:
        raise ConfigError(f"database.{field} is set but the config has no `secrets` entry")
    try:
        return provider.get(name)
    except Exception:  # noqa: BLE001 - any provider failure is a startup failure; the message may name the secret path
        raise ConfigError(f"the DSN secret database.{field} cannot be read") from None


def source_args(
    config_path: str | None, environ: Mapping[str, str] = os.environ
) -> tuple[str | None, Limits | None]:
    """(dsn, limits) for the read-only login: from the config when one is given, else from the environment."""
    if not config_path:
        return environ.get(DSN_ENV) or None, None
    cfg = load_config(Path(config_path))
    return resolve_dsn(cfg, environ=environ), cfg.database.limits()


def make_llm(cfg: AskdataConfig, provider: SecretProvider | None = None) -> LLM:
    """The live model route: the core LLM kind named in `cfg.llm`, over the config's routes. Sends nothing."""
    if cfg.llm is None:
        raise ConfigError("no live model: the config has no `llm` entry")
    r = cfg.route
    if not all(p.is_finite() and p > 0 for p in (r.input_usd_per_mtok, r.output_usd_per_mtok)):
        raise ConfigError(
            "route: a live model needs positive input and output prices (the meter prices every call from them)"
        )
    provider = provider or make_provider(cfg)
    try:
        return make("llm", _kind("llm", cfg.llm), provider, routes=cfg.routes())
    except CoreConfigError as err:
        raise ConfigError(f"llm: {err}") from None


def smoke_breach(
    spent: Decimal,
    questions: int,
    attempts: int,
    schema_violations: int,
    last_cost: Decimal = Decimal(0),
    limits: Smoke | None = None,
) -> str | None:
    """The abort reason once the smoke run is over the line, else None. Numbers: `settings.Smoke` (config `smoke:`).

    From question 1: one question costing more than `hard_cap_per_question_usd` aborts at once. From `min_questions`
    on: cost per question above `max_cost_per_question_usd` (strictly more), or more than `max_schema_violation_rate`
    of the model attempts returning an unusable (schema-violating) answer."""
    lim = limits or Smoke()
    if last_cost > lim.hard_cap_per_question_usd:
        return "smoke_cost"
    if questions < lim.min_questions:
        return None
    if spent / questions > lim.max_cost_per_question_usd:
        return "smoke_cost"
    if attempts and Decimal(schema_violations) / attempts > lim.max_schema_violation_rate:
        return "smoke_schema"
    return None
