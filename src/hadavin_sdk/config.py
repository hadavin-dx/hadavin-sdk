"""Client config: ``HADAVIN_CONFIG_DIR`` names a folder holding ``config.yaml`` and friends.

Bad config fails at start-up. Cross-file checks (agents, actions, chains) live in ``registry``.
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any, Literal, get_args
from urllib.parse import urlsplit

import yaml
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from hadavin_sdk import defaults, deferred
from hadavin_sdk.backends.table import DEFAULTS, DEV_ONLY, NOT_PROD, TABLE, KindSettings
from hadavin_sdk.errors import ConfigError

__all__ = [
    "Backends",
    "Config",
    "ConfigError",
    "EvidenceSettings",
    "K1bSettings",
    "Retention",
    "Route",
    "SourceConfig",
    "confined",
    "load_config",
    "load_yaml",
    "url_allowed",
]


def _money(v: object) -> object:
    if isinstance(v, float):
        # ValueError, not TypeError: pydantic turns only ValueError into a validation error.
        raise ValueError("money must be a decimal string, not a float")  # noqa: TRY004
    return v


Money = Annotated[Decimal, BeforeValidator(_money)]


class _Strict(BaseModel):
    # A mistyped key may hold a secret: errors name the field, never its value.
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class Route(_Strict):
    model_id: str
    input_usd_per_mtok: Money
    output_usd_per_mtok: Money
    max_tokens: int = Field(gt=0)


class Backends(_Strict):
    """One validated settings model per capability (built by `parse_backends`, never from raw YAML)."""

    secrets: KindSettings
    signer: KindSettings
    anchor: KindSettings
    store: KindSettings
    audit: KindSettings
    llm: KindSettings
    detector: tuple[KindSettings, ...]
    channel: KindSettings

    def entries(self) -> list[tuple[str, KindSettings]]:
        out = [(cap, getattr(self, cap)) for cap in TABLE if cap != "detector"]
        return out + [("detector", d) for d in self.detector]


# Slice 1 keys, refused with the place they moved to (design 12.3; no clients yet, so no migration shim).
MOVED = {
    "region": "backends.<capability>.region on each AWS kind",
    "slack": "backends.channel: {kind: slack, channel_id, signing_secret_name, bot_token_secret_name}",
    "detector_threshold": "backends.detector: [{kind: regex, threshold}]",
    "audit_dir": "backends.audit: {kind: local_dir, dir}",
    "recorded_dir": "backends.llm: {kind: fake, recorded_dir}",
}


def _one(cap: str, raw: Any, root: Path) -> KindSettings:
    bare = isinstance(raw, str)
    if bare:
        raw = {"kind": raw}
    if not isinstance(raw, dict) or not isinstance(raw.get("kind"), str):
        raise ConfigError(f"backends.{cap}: expected {{kind: <name>, ...settings}}")
    kinds = TABLE[cap]
    kind = raw["kind"]
    if kind not in kinds:
        raise ConfigError(
            f"backend {cap}: unknown kind {kind!r}; known: {', '.join(sorted(kinds))}"
        )
    model = kinds[kind].settings
    required = [n for n, f in model.model_fields.items() if f.is_required() and n != "kind"]
    if bare and required:
        raise ConfigError(
            f"backends.{cap}: {kind!r} needs settings; "
            f"write backends.{cap}: {{kind: {kind}, {', '.join(required)}}}"
        )
    data = dict(raw)
    for (
        name,
        field,
    ) in model.model_fields.items():  # relative paths are relative to the config folder
        if Path in (field.annotation, *get_args(field.annotation)) and isinstance(
            data.get(name), str
        ):
            data[name] = root / data[name]
    try:
        return model(**data)
    except ValidationError as exc:
        raise ConfigError(f"backends.{cap} ({kind}): {exc}") from exc


def parse_backends(raw: Any, root: Path) -> Backends:
    if raw is not None and not isinstance(raw, dict):
        raise ConfigError("backends: expected a mapping of capability to {kind: ...}")
    raw = dict(raw or {})
    if unknown := set(raw) - set(TABLE):
        raise ConfigError(
            f"backends: unknown capability {sorted(unknown)}; known: {', '.join(TABLE)}"
        )
    if missing := [cap for cap in TABLE if cap not in raw and cap not in DEFAULTS]:
        raise ConfigError(f"backends: {', '.join(missing)} must be set")
    built: dict[str, Any] = {}
    for cap in TABLE:
        value = raw.get(cap, DEFAULTS.get(cap))
        if cap == "detector":
            items = value if isinstance(value, list) else [value]
            if not items:  # every entry runs and any flag flags the run (guard.injection.AnyOf)
                raise ConfigError("backends.detector: list at least one detector")
            built[cap] = tuple(_one(cap, item, root) for item in items)
            if all(d.kind == "llm_judge" for d in built[cap]):
                # The judge reads attacker text and can be steered to say "clean": a tripwire beside
                # another detector, never the only one (design 4.3, 10).
                raise ConfigError("backends.detector: llm_judge needs another detector beside it")
        else:
            built[cap] = _one(cap, value, root)
    return Backends(**built)


_LOOPBACK = {"127.0.0.1", "localhost", "::1"}


def url_allowed(url: str, allow_insecure_loopback: bool) -> bool:
    """The bearer token travels with every call: https only. Plain http only to this machine, and only when
    the config sets ``allow_insecure_loopback: true`` (the local test fixture). Used at load and at call time."""
    parts = urlsplit(url)
    if parts.scheme == "https":
        return True
    return parts.scheme == "http" and allow_insecure_loopback and parts.hostname in _LOOPBACK


class System(_Strict):
    base_url: str


class K1bSettings(_Strict):
    """K1b replay limits. Not part of ``config_hash``: they bound a replay run, not an agent's qualification."""

    max_steps: int = Field(default=12, gt=0)  # effective: min with the agent's own max_steps
    max_tool_calls: int = Field(default=20, gt=0)
    case_timeout_s: int = Field(default=300, gt=0)
    # Mask client data before the model sees it. Turning it off needs `replay --i-know-data-is-already-masked`.
    redact: bool = True


HELD_MAPS_CEILING = 400  # days: the audit retention; a config cannot extend it (design 6.3)


class Retention(_Strict):
    """How long evidence is kept (design 6.1, 6.3). Not part of ``config_hash``."""

    tool_calls_days: int = Field(default=30, gt=0)
    redaction_maps_days: int = Field(default=30, gt=0)
    # Runs labelled wrong, harmful or missed (or demoted) keep their tool calls past `tool_calls_days`.
    hold_labelled: bool = True
    # A held run's redaction map (original identifiers) is purged at this age whatever the hold says.
    held_maps_max_days: int = Field(default=HELD_MAPS_CEILING, gt=0, le=HELD_MAPS_CEILING)
    purge_every_s: int = Field(
        default=defaults.PURGE_EVERY_S, gt=0
    )  # the purge_evidence tick step's interval

    @model_validator(mode="after")
    def _held_not_shorter(self) -> Retention:
        if self.held_maps_max_days < self.redaction_maps_days:
            raise ValueError("retention.held_maps_max_days must be at least redaction_maps_days")
        return self


class EvidenceSettings(_Strict):
    """The read path's limits (K5). Defaults live in `hadavin_sdk/defaults.py`. Not part of `config_hash`."""

    max_tool_errors: int = Field(default=defaults.MAX_TOOL_ERRORS, gt=0)
    legacy_max_output_bytes: int = Field(default=defaults.LEGACY_MAX_OUTPUT_BYTES, gt=0)
    fetch_ceiling_bytes: int = Field(default=defaults.FETCH_CEILING_BYTES, gt=0)
    https_ports: tuple[int, ...] = defaults.HTTPS_PORTS
    cluster_ports: tuple[int, ...] = defaults.CLUSTER_PORTS
    # Which identifier kinds the run's redaction map may store. May narrow the default, never widen it: a kind
    # with no grammar in `guard/runmap.py` cannot be stored.
    stored_kinds: tuple[str, ...] = defaults.STORED_KINDS
    # Per-run ceilings (a model can loop on a cheap tool): calls, bytes sent back to the model, and how many
    # tool bodies may still be running past their deadline before further calls are refused.
    max_tool_calls_per_run: int = Field(default=defaults.MAX_TOOL_CALLS_PER_RUN, gt=0)
    max_tool_bytes_per_run: int = Field(default=defaults.MAX_TOOL_BYTES_PER_RUN, gt=0)
    max_abandoned_tool_threads: int = Field(default=defaults.MAX_ABANDONED_TOOL_THREADS, gt=0)
    # Host suffixes that count as in-cluster, where `cluster_http` tools may use plain http.
    cluster_suffixes: tuple[str, ...] = defaults.CLUSTER_SUFFIXES

    @model_validator(mode="after")
    def _checks(self) -> EvidenceSettings:
        if unknown := sorted(set(self.stored_kinds) - set(defaults.STORED_KINDS)):
            raise ValueError(
                f"evidence.stored_kinds: {unknown} cannot be stored (secret, regulated or unknown)"
            )
        if bad_suffix := [
            s for s in self.cluster_suffixes if not s.startswith(".") or s.count(".") < 1
        ]:
            raise ValueError(f"evidence.cluster_suffixes: {bad_suffix} must start with a dot")
        for name in ("https_ports", "cluster_ports"):
            if bad := [p for p in getattr(self, name) if not 0 < p < 65536]:
                raise ValueError(f"evidence.{name}: {bad} are not ports")
        return self


class SourceConfig(_Strict):
    """A read source built at start-up: `kind` names a registered kind, `settings` is that kind's validated
    settings, `token_secret_name` the secret (from the configured secrets kind) it authenticates with, and
    `ca_file` the CA bundle that signs its endpoint (a path relative to the config folder). Not part of
    `config_hash`; `scope_inventory` can stand in for a probe only for a source that cannot be probed."""

    kind: str
    settings: dict[str, Any]
    token_secret_name: str | None = None
    ca_file: Path | None = None

    @model_validator(mode="after")
    def _kind_checks(self) -> SourceConfig:
        from hadavin_sdk.sources.kinds import KINDS

        if self.kind not in KINDS:
            raise ValueError(
                f"source kind {self.kind!r} is unknown; known: {', '.join(sorted(KINDS))}"
            )
        KINDS[self.kind].settings(**self.settings)
        return self


_DIGEST = re.compile(r"[0-9a-f]{64}")


def _inventory_ref_ok(ref: str) -> bool:
    """ "<page>#<anchor> sha256:<64 hex>", checked by splitting (no backtracking-prone pattern)."""
    where, sep, digest = ref.rpartition(" sha256:")
    page, hash_sign, anchor = where.partition("#")
    return bool(
        sep and hash_sign and page and anchor and " " not in where and _DIGEST.fullmatch(digest)
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HADAVIN_")
    config_dir: Path


class Config(_Strict):
    environment: Literal["dev", "pilot", "prod"]
    routes: dict[str, Route]
    backends: Backends
    golden_dir: Path
    inputs_dir: Path
    eval_threshold: float = Field(
        default=1.0, gt=0.0, le=1.0
    )  # 0 would qualify an agent that passed nothing
    check_modules: list[str] = []
    systems: dict[str, System] = {}
    egress_hosts: frozenset[str] = frozenset()
    allow_insecure_loopback: bool = False  # true only in the local test fixture config
    k1b: K1bSettings = K1bSettings()
    # K5: modules a tool manifest's `function` may resolve from (like `check_modules`), the per-call timeout, and
    # retention of evidence.
    tool_modules: list[str] = []
    tool_timeout_s: float = Field(default=10.0, gt=0)
    retention: Retention = Retention()
    evidence: EvidenceSettings = EvidenceSettings()
    # design 6.6: a read source that cannot be probed names the client-signed inventory instead,
    # "<page>#<anchor> sha256:<64 hex>".
    scope_inventory: dict[str, str] = {}
    # K5: configured read sources (kind + settings), built and probed at start-up (design 6.6).
    sources: dict[str, SourceConfig] = {}
    # SHA-256 of each tool module's source file; required in pilot and prod, checked when listed.
    tool_module_hashes: dict[str, str] = {}
    executor_timeout_s: float = Field(
        default=defaults.EXECUTOR_TIMEOUT_S, gt=0
    )  # dev executor only
    root: Path

    @model_validator(mode="after")
    def _cross_checks(self) -> Config:
        for source, ref in self.scope_inventory.items():
            if not _inventory_ref_ok(ref):
                raise ValueError(
                    f"scope_inventory {source}: expected '<page>#<anchor> sha256:<64 hex digits>'"
                )
        for d in self.backends.detector:  # llm_judge names a route
            if getattr(d, "route", None) is not None and d.route not in self.routes:
                raise ValueError(f"backends.detector {d.kind}: unknown route {d.route!r}")
        for name, system in self.systems.items():
            if not url_allowed(system.base_url, self.allow_insecure_loopback):
                raise ValueError(
                    f"system {name}: base_url must be https "
                    f"(http only for loopback with allow_insecure_loopback): {system.base_url}"
                )
        refused = []  # environment table, design 4.6: every refusal at once, so one fix round is enough
        if self.environment != "dev":
            refused = [
                f"{c}: {s.kind}" for c, s in self.backends.entries() if (c, s.kind) in DEV_ONLY
            ]
            refused += ["allow_insecure_loopback"] if self.allow_insecure_loopback else []
        refused += _anchor_refusals(self.environment, self.backends)
        if refused:
            raise ValueError(f"environment {self.environment}: refused: {', '.join(refused)}")
        return self


def _anchor_refusals(environment: str, b: Backends) -> list[str]:
    """Environment table (design 4.6). Prod needs a signer and an anchor whose retention the client agreed
    (`retention_ack`); COMPLIANCE mode (undeletable even by the account root) only then. `ed25519_local` in
    prod only with its key from the secrets kind (never a file in the image), and only beside that anchor."""
    anchor = None if b.anchor.kind == "none" else b.anchor
    refused = []
    if anchor is not None and b.audit.kind != "chain":
        refused.append(f"anchor {anchor.kind} needs backends.audit kind chain")
    if (
        anchor is not None
        and anchor.mode == "COMPLIANCE"
        and not (environment == "prod" and anchor.retention_ack)
    ):
        refused.append("anchor mode COMPLIANCE outside prod or without retention_ack")
    if environment == "prod":
        refused += [f"{c}: {s.kind}" for c, s in b.entries() if (c, s.kind) in NOT_PROD]
        if anchor is not None and not anchor.retention_ack:
            refused.append(f"anchor {anchor.kind} without retention_ack")
        if b.signer.kind == "ed25519_local" and b.signer.private_key_path is not None:
            refused.append("signer ed25519_local with a key file (use private_key_secret_name)")
    return refused


class _UniqueKeyLoader(yaml.SafeLoader):
    """A duplicate mapping key is an error: safe_load would keep the last value, silently changing a level."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=True)
            if key in seen:
                raise ConfigError(f"duplicate key {key!r} (line {key_node.start_mark.line + 1})")
            seen.add(key)
        return super().construct_mapping(node, deep)


def load_yaml(text: str) -> Any:
    """``yaml.safe_load`` that refuses duplicate mapping keys."""
    return yaml.load(text, Loader=_UniqueKeyLoader)  # noqa: S506  # nosec B506 - SafeLoader subclass


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = load_yaml(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path.name}: expected a mapping at the top level")
    return data


def confined(base: Path, relative: str) -> Path:
    """``base / relative``, refused if it resolves outside ``base`` (no ``..`` or absolute escapes)."""
    root = Path(base).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ConfigError(f"path escapes its folder: {relative}")
    return path


def load_config(config_dir: Path | None = None) -> Config:
    """Every start-up problem (missing HADAVIN_CONFIG_DIR, bad YAML, bad values) is a ConfigError."""
    try:
        root = Path(config_dir) if config_dir else Settings().config_dir  # type: ignore[call-arg]
        raw = _read_yaml(root / "config.yaml")
        egress = _read_yaml(root / "egress.yaml").get("hosts") or []
        if early := deferred.key_problems("config.yaml", raw):
            raise ConfigError("; ".join(early))
        if moved := [k for k in MOVED if k in raw]:
            raise ConfigError("; ".join(f"{k} moved to {MOVED[k]}" for k in moved))
        for key in ("golden_dir", "inputs_dir"):
            if key in raw:
                raw[key] = root / raw[key]
        raw["backends"] = parse_backends(raw.get("backends"), root)
        return Config(**raw, egress_hosts=frozenset(egress), root=root)
    except ConfigError:
        raise
    except (ValueError, TypeError, yaml.YAMLError) as exc:  # pydantic errors are ValueErrors
        raise ConfigError(str(exc)) from exc
