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
from hadavin_sdk.actions.secrets import SecretProvider
from hadavin_sdk.backends import make
from hadavin_sdk.backends.table import TABLE, KindSettings
from hadavin_sdk.errors import ConfigError as CoreConfigError
from hadavin_sdk.llm.protocol import LLM

DSN_ENV = "ASKDATA_DSN"

# Smoke abort rule (amendments A-03, step 1): checked after every question of a live smoke run.
SMOKE_MAX_COST_PER_QUESTION = Decimal("0.035")
SMOKE_MAX_SCHEMA_VIOLATION_RATE = Decimal("0.10")


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


def resolve_dsn(
    cfg: AskdataConfig | None,
    provider: SecretProvider | None = None,
    environ: Mapping[str, str] = os.environ,
) -> str | None:
    """`provider.get(dsn_secret_name)` when the config names a secret; otherwise (documented fallback) the
    ASKDATA_DSN environment variable. A named secret that cannot be read is an error, never a silent fallback."""
    name = cfg.database.dsn_secret_name if cfg else None
    if not name:
        return environ.get(DSN_ENV) or None
    provider = provider or (make_provider(cfg) if cfg else None)
    if provider is None:
        raise ConfigError("database.dsn_secret_name is set but the config has no `secrets` entry")
    try:
        return provider.get(name)
    except Exception:  # noqa: BLE001 - any provider failure is a startup failure; the message may name the secret path
        raise ConfigError("the database DSN secret cannot be read") from None


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
    provider = provider or make_provider(cfg)
    try:
        return make("llm", _kind("llm", cfg.llm), provider, routes=cfg.routes())
    except CoreConfigError as err:
        raise ConfigError(f"llm: {err}") from None


def smoke_breach(
    spent: Decimal, questions: int, attempts: int, schema_violations: int
) -> str | None:
    """The abort reason once the smoke run is over the line, else None: cost per question above US$0.035, or more
    than 10 % of the model attempts returning an unusable (schema-violating) answer."""
    if questions and spent / questions > SMOKE_MAX_COST_PER_QUESTION:
        return "smoke_cost"
    if attempts and Decimal(schema_violations) / attempts > SMOKE_MAX_SCHEMA_VIOLATION_RATE:
        return "smoke_schema"
    return None
