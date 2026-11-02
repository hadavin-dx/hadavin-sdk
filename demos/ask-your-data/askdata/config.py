"""The demo's own config (design 7.3): a strict pydantic model over a YAML file, safe-load only, unknown keys refused.

Paths in the file are resolved against the file's folder. Nothing here is a secret: database passwords come from the
environment (`PGPASSWORD`) or a connection string in `ASKDATA_DSN*`, model keys from the core secrets kinds.
"""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from askdata.meter import Meter
from askdata.pgsource import Limits as DbLimits
from askdata.pipeline import Settings
from askdata.settings import RUNTIME, MeterLimits, Sealed, Smoke
from hadavin_sdk.config import Route


class ConfigError(ValueError):
    pass


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Paths(_Strict):
    ledger_file: Path
    audit_dir: Path
    meter_file: Path
    kill_switch_file: Path
    eval_dir: Path
    runs_dir: Path
    recorded_dir: Path | None = None  # the scripted model's recordings (offline runs)


class RouteCfg(_Strict):
    name: str = "sql_generate"
    model_id: str
    input_usd_per_mtok: Decimal
    output_usd_per_mtok: Decimal
    max_tokens: int = Field(gt=0)


class Limits(_Strict):
    max_attempts: int = Field(RUNTIME.max_attempts, ge=1, le=RUNTIME.max_attempts)
    max_question_chars: int = Field(RUNTIME.max_question_chars, gt=0)
    # the input gate's score cut-off; the regex detector scores only 0.0 or 1.0, so any value in (0, 1] acts alike
    injection_threshold: float = Field(RUNTIME.injection_threshold, gt=0, le=1)


class Database(_Strict):
    """Where the read-only login's DSN comes from, and the client's limits. The defaults are the spike's (10 s watchdog,
    1,000,000 bytes); a client config overrides them (the design's client values are 5 s and 2,000,000 bytes)."""

    # read through the secrets kind; None: the ASKDATA_DSN environment variable; an empty string is refused
    dsn_secret_name: str | None = Field(None, min_length=1)
    # the second scoring database and the clean twin (eval only), through the same secrets kind
    dsn_secret_name_b: str | None = Field(None, min_length=1)
    dsn_secret_name_clean: str | None = Field(None, min_length=1)
    statement_timeout_s: float = Field(
        RUNTIME.statement_timeout_s, gt=0, le=RUNTIME.max_statement_timeout_s
    )
    max_rows: int = Field(RUNTIME.max_rows, gt=0)
    max_bytes: int = Field(RUNTIME.max_bytes, gt=0)

    def limits(self) -> DbLimits:
        return DbLimits(
            statement_timeout_s=self.statement_timeout_s,
            max_rows=self.max_rows,
            max_bytes=self.max_bytes,
        )


class AskdataConfig(_Strict):
    as_of: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    paths: Paths
    route: RouteCfg
    limits: Limits = Limits()
    restricted_terms: list[str] | None = None
    store_question: bool = True
    live: bool = True  # a paid route needs a fresh external_usd; the fake route never spends
    database: Database = Database()
    smoke: Smoke = Smoke()  # the live smoke run's abort rule (settings.py holds the defaults)
    sealed: Sealed = Sealed()  # sealed-set budget and count rules, written into lock.json at freeze
    meter: MeterLimits = MeterLimits()  # caps and timing of the shared spend meter
    # HMAC key (from the `secrets` kind) for the sealed-run chain and lock.json's seal; None: unkeyed, see sealed.py
    sealed_key_secret_name: str | None = Field(None, min_length=1)
    # Secret names of the keys the chain was under BEFORE sealed_key_secret_name, oldest first (key rotation)
    sealed_previous_key_secret_names: list[str] = Field(default_factory=list)
    # Core backend entries (`{kind: ..., ...}`), validated by `live.py` against the core table; never a secret value.
    secrets: dict[str, Any] | None = (
        None  # None: no provider; the DSN then comes from the environment only
    )
    llm: dict[str, Any] | None = (
        None  # None: the recorded (fake) route; e.g. {kind: anthropic, platform: api, ...}
    )

    def routes(self) -> dict[str, Route]:
        r = self.route
        return {
            r.name: Route(
                model_id=r.model_id,
                input_usd_per_mtok=r.input_usd_per_mtok,
                output_usd_per_mtok=r.output_usd_per_mtok,
                max_tokens=r.max_tokens,
            )
        }

    def meter_obj(self) -> Meter:
        m = self.meter
        return Meter(
            self.paths.meter_file,
            max_external_age=timedelta(hours=m.max_external_age_hours),
            stale_open_after=timedelta(minutes=m.stale_open_minutes),
        )

    def _llm_attempts(self) -> int:
        """Requests one live `chat()` may send: the LLM kind's `max_attempts` (3 unless set); 1 for the recorded model."""
        return int(self.llm.get("max_attempts", 3)) if self.llm else RUNTIME.recorded_llm_requests

    def settings(self) -> Settings:
        extra = {"restricted_terms": tuple(self.restricted_terms)} if self.restricted_terms else {}
        return Settings(
            route=self.route.name, max_attempts=self.limits.max_attempts, max_question_chars=self.limits.max_question_chars,
            injection_threshold=self.limits.injection_threshold,
            store_question=self.store_question, live=self.live, llm_max_attempts=self._llm_attempts(), **extra,
        )  # fmt: skip


def load_config(path: Path) -> AskdataConfig:
    path = Path(path).resolve()
    if path.suffix not in (".yaml", ".yml") or not path.is_file():
        raise ConfigError("the config must be an existing .yaml or .yml file")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        cfg = AskdataConfig.model_validate(raw)
    except (OSError, yaml.YAMLError, ValidationError, TypeError) as err:
        raise ConfigError(f"cannot load {path.name}: {type(err).__name__}") from None
    base = path.resolve().parent
    paths = {
        k: (base / v if v is not None and not Path(v).is_absolute() else v)
        for k, v in cfg.paths.model_dump().items()
    }
    return cfg.model_copy(update={"paths": Paths(**paths)})


def config_hash(cfg: AskdataConfig, prompt_sha256: str) -> str:
    """SHA-256 over the parsed config without paths, plus the prompt hash: stable across machines."""
    body = cfg.model_dump(mode="json", exclude={"paths"})
    text = json.dumps(
        {"config": body, "prompt_sha256": prompt_sha256}, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
