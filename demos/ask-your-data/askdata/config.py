"""The demo's own config (design 7.3): a strict pydantic model over a YAML file, safe-load only, unknown keys refused.

Paths in the file are resolved against the file's folder. Nothing here is a secret: database passwords come from the
environment (`PGPASSWORD`) or a connection string in `ASKDATA_DSN*`, model keys from the core secrets kinds.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from askdata.pipeline import Settings
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
    max_attempts: int = Field(3, ge=1, le=3)
    max_question_chars: int = Field(500, gt=0)


class AskdataConfig(_Strict):
    as_of: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    paths: Paths
    route: RouteCfg
    limits: Limits = Limits()
    restricted_terms: list[str] | None = None
    store_question: bool = True
    live: bool = True  # a paid route needs a fresh external_usd; the fake route never spends

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

    def settings(self) -> Settings:
        extra = {"restricted_terms": tuple(self.restricted_terms)} if self.restricted_terms else {}
        return Settings(
            route=self.route.name, max_attempts=self.limits.max_attempts, max_question_chars=self.limits.max_question_chars,
            store_question=self.store_question, live=self.live, **extra,
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
