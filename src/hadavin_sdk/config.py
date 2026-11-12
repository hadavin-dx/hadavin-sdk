"""Client config: ``HADAVIN_CONFIG_DIR`` names a folder holding ``config.yaml`` and friends.

Bad config fails at start-up. Cross-file checks (agents, actions, chains) live in ``registry``.
"""

from __future__ import annotations

import ipaddress
import re
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any, Literal, get_args

import yaml
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from hadavin_sdk import defaults, deferred
from hadavin_sdk.backends.table import DEFAULTS, DEMO_ONLY, NOT_PROD, TABLE, KindSettings
from hadavin_sdk.config_url import ConfigUrl
from hadavin_sdk.errors import (
    ConfigError,
    ConfigValueError,
    error_where,
    is_digest,
    read_configured,
    shown_name,
)
from hadavin_sdk.hidden_input import HiddenInputModel, is_rebuilt, without_input
from hadavin_sdk.safe_url import (
    InvalidUrl,
    safe_urlsplit,
)
from hadavin_sdk.scrub_settings import ScrubSettings
from hadavin_sdk.stages import STAGES, is_live, is_prod

__all__ = [
    "Backends",
    "Config",
    "ConfigError",
    "EvidenceSettings",
    "K1bSettings",
    "Retention",
    "Route",
    "ScrubSettings",
    "SourceConfig",
    "confined",
    "load_config",
    "load_yaml",
    "url_allowed",
]


def _money(v: object) -> object:
    if isinstance(v, float):
        # ValueError, not TypeError: pydantic turns only ValueError into a validation error.
        raise ConfigValueError("money must be a decimal string, not a float")
    return v


Money = Annotated[Decimal, BeforeValidator(_money)]


def _no_key_shaped_run(value: str) -> str:
    """A run of 32 or more letters and digits is the shape of a pasted key (the regex engine of pydantic has no
    look-ahead, so this is a validator). The message does not hold the value."""
    if re.search(r"[A-Za-z0-9]{32}", value):
        raise ConfigValueError(
            "a model id has no run of 32 or more letters and digits (the shape of a pasted key); "
            "write the model's short name or version, not an immutable hash pin"
        )
    return value


# `BaseModel` is named too so the linter knows the class is a pydantic model
class _Strict(HiddenInputModel, BaseModel):
    # A mistyped key may hold a secret: an error names the field (an unknown key shows as `<unknown key>`), never the
    # value; `config_error_text` is the one place that decides what text of a problem is shown.
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class Route(_Strict):
    # a model id is a short token (`claude-sonnet-5-5`, `us.anthropic.claude-...-v1:0`, `claude-...@20250514`); it
    # is written into the replay report. Refused at load: a sentence (a space), any other character, more than 128
    # characters, and a run of 32 or more letters and digits (a pasted key has one; a real id has runs of at most 12).
    # NOT refused: a key cut into short pieces by `-`, `.` or `_` (every piece under 32 characters).
    # An immutable pin (`model@sha256:<64 hex>`, `org/model@<40 hex>`) is refused on purpose: a 40 or 64 digit hex run cannot be
    # told from a pasted hex key. The refusal says so; write the short name or version instead (Round 15, Issue 5).
    model_id: Annotated[
        str,
        Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}$"),
        AfterValidator(_no_key_shaped_run),
    ]
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


_OLD_STAGE = "dev"


class _RenamedStage(ConfigValueError):
    """The old first stage name was written: carries the whole sentence the reader should see."""


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
        raise ConfigError(f"backend {cap}: unknown kind; known: {', '.join(sorted(kinds))}")
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
        raise ConfigError(f"backends.{cap} ({kind}): {config_error_text(exc)}") from None


def parse_backends(raw: Any, root: Path) -> Backends:
    if raw is not None and not isinstance(raw, dict):
        raise ConfigError("backends: expected a mapping of capability to {kind: ...}")
    raw = dict(raw or {})
    if unknown := set(raw) - set(TABLE):
        raise ConfigError(
            f"backends: {len(unknown)} unknown capability name(s); known: {', '.join(TABLE)}"
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

# The one rule for the demo executor's per-call timeout in seconds, used by the config field `executor_timeout_s`
# and by the `timeout_s=` keyword of `app.build`. The sentence is the tail of both refusal messages.
EXECUTOR_TIMEOUT_RULE = f"must be an int or float between {defaults.EXECUTOR_TIMEOUT_MIN_S} and {defaults.EXECUTOR_TIMEOUT_MAX_S}"


def executor_timeout_ok(value: object) -> bool:
    """An int or a float (True and False are not numbers here; text, Decimal, Fraction and other number types are
    refused) from `defaults.EXECUTOR_TIMEOUT_MIN_S` to `defaults.EXECUTOR_TIMEOUT_MAX_S`, both included.
    Not-a-number and infinity fail the comparison."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return False
    return defaults.EXECUTOR_TIMEOUT_MIN_S <= value <= defaults.EXECUTOR_TIMEOUT_MAX_S


def url_allowed(url: str, allow_insecure_loopback: bool) -> bool:
    """The bearer token travels with every call: https only. Plain http only to this machine, and only when
    the config sets ``allow_insecure_loopback: true`` (the local test fixture). Used at load and at call time.
    A URL that cannot be read is not allowed (False)."""
    try:
        parts = safe_urlsplit(url)
    except InvalidUrl:
        return False
    if parts.scheme == "https":
        return True
    return parts.scheme == "http" and allow_insecure_loopback and parts.hostname in _LOOPBACK


class System(_Strict):
    base_url: ConfigUrl  # a login or a look-alike host is refused by the one URL type, as in every other URL field


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
    # Tool calls of held runs are kept past `tool_calls_days`, but not forever.
    held_tool_calls_max_days: int = Field(default=HELD_MAPS_CEILING, gt=0, le=HELD_MAPS_CEILING)
    purge_every_s: int = Field(
        default=defaults.PURGE_EVERY_S, gt=0
    )  # the purge_evidence tick step's interval

    @model_validator(mode="after")
    def _held_not_shorter(self) -> Retention:
        if self.held_maps_max_days < self.redaction_maps_days:
            raise ConfigValueError(
                "retention.held_maps_max_days must be at least redaction_maps_days"
            )
        return self


class EvidenceSettings(_Strict):
    """The read path's limits (K5). Defaults live in `hadavin_sdk/defaults.py`. Not part of `config_hash`."""

    scrub: ScrubSettings = ScrubSettings()

    max_tool_errors: int = Field(default=defaults.MAX_TOOL_ERRORS, gt=0)
    legacy_max_output_bytes: int = Field(
        default=defaults.LEGACY_MAX_OUTPUT_BYTES, gt=0, le=defaults.MAX_REDACT_CHARS
    )
    fetch_ceiling_bytes: int = Field(default=defaults.FETCH_CEILING_BYTES, gt=0)
    https_ports: tuple[int, ...] = defaults.HTTPS_PORTS
    cluster_ports: tuple[int, ...] = defaults.CLUSTER_PORTS
    # Which identifier kinds the run's redaction map may store. May narrow the default, never widen it: a kind
    # with no grammar in `guard/runmap.py` cannot be stored.
    stored_kinds: tuple[str, ...] = defaults.STORED_KINDS
    # Per-run ceilings (a model can loop on a cheap tool): calls, bytes sent back to the model, and how many
    # tool bodies may still be running past their deadline before further calls are refused.
    max_tool_calls_per_run: int = Field(default=defaults.MAX_TOOL_CALLS_PER_RUN, gt=0)
    # A run whose document or tool results plant more distinct values than this ends `document_too_complex`:
    # building the redactor over a bigger map is CPU the client's text should not be able to spend.
    max_map_entries: int = Field(default=defaults.MAX_MAP_ENTRIES, gt=0)
    max_tool_bytes_per_run: int = Field(default=defaults.MAX_TOOL_BYTES_PER_RUN, gt=0)
    max_abandoned_tool_threads: int = Field(default=defaults.MAX_ABANDONED_TOOL_THREADS, gt=0)
    # What the agent can do to the client's systems: at most this many reads at once and per minute, whatever
    # the model asks (it cannot raise the production-side load, R372).
    max_concurrent_tool_calls: int = Field(default=defaults.MAX_CONCURRENT_TOOL_CALLS, gt=0)
    max_tool_calls_per_minute: int = Field(default=defaults.MAX_TOOL_CALLS_PER_MINUTE, gt=0)
    # Host suffixes that count as in-cluster, where `cluster_http` tools may use plain http.
    cluster_suffixes: tuple[str, ...] = defaults.CLUSTER_SUFFIXES
    # The largest document a run takes; a bigger one is refused (`document_too_large`), never half-read.
    # Never above the redactor's own cap (`defaults.MAX_REDACT_CHARS`): a larger value would pass the size check
    # and then be refused by the redactor.
    max_document_bytes: int = Field(
        default=defaults.MAX_DOCUMENT_BYTES, gt=0, le=defaults.MAX_REDACT_CHARS
    )
    # Target systems (a contract's `target_system`) whose names are case-insensitive, so grounding folds case
    # for them. Every other target is compared exactly: `Admin` is not `admin`.
    case_insensitive_targets: tuple[str, ...] = ()
    # The secret (in the secrets kind) that keys the HMAC of the restored inputs on the gate's audit event, so
    # an audit reader cannot confirm a guessed identifier offline. Required in pilot and prod.
    restored_hash_key_secret_name: str | None = None
    # Operation ids a tool module may bind to a method other than GET (a review or a query is a POST that
    # reads). A tool's READ_OPERATIONS declares the binding; this list is the deployment's permission for it.
    post_read_operations: tuple[str, ...] = ()
    # How often a configured source's scope is probed again while the process runs (RBAC can widen).
    source_reprobe_s: int = Field(default=defaults.SOURCE_REPROBE_S, gt=0)

    @model_validator(mode="after")
    def _checks(self) -> EvidenceSettings:
        if bad := [
            t for t in self.case_insensitive_targets if not re.fullmatch(r"[a-z0-9_-]{1,40}", t)
        ]:
            raise ConfigValueError(
                f"evidence.case_insensitive_targets: {len(bad)} entries are not target_system labels"
            )
        if unknown := sorted(set(self.stored_kinds) - set(defaults.STORED_KINDS)):
            raise ConfigValueError(
                f"evidence.stored_kinds: {len(unknown)} entries cannot be stored (secret, regulated or unknown)"
            )
        if bad_suffix := [
            s
            for s in self.cluster_suffixes
            if not s.startswith(".") or s.rsplit(".", 1)[-1] not in defaults.PRIVATE_SUFFIX_LABELS
        ]:
            raise ConfigValueError(
                f"evidence.cluster_suffixes: {len(bad_suffix)} entries must start with a dot and end in a private label "
                f"({', '.join(sorted(defaults.PRIVATE_SUFFIX_LABELS))}); a public suffix such as .com would "
                "allow plain http to the internet"
            )
        for name in ("https_ports", "cluster_ports"):
            if bad := [p for p in getattr(self, name) if not 0 < p < 65536]:
                raise ConfigValueError(f"evidence.{name}: {len(bad)} entries are not ports")
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
            raise ConfigValueError(f"source kind is unknown; known: {', '.join(sorted(KINDS))}")
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


class Settings(HiddenInputModel, BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HADAVIN_")
    config_dir: Path


class Config(_Strict):
    environment: Literal["demo", "pilot", "prod"]  # the same three as STAGES (a test pins it)
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
    # design 6.6: a read source that cannot be probed names an operator-attested inventory instead (the reference
    # is format-checked and logged; its hash is NOT compared with the page and nobody is verified to have signed),
    # "<page>#<anchor> sha256:<64 hex>".
    scope_inventory: dict[str, str] = {}
    # K5: configured read sources (kind + settings), built and probed at start-up (design 6.6).
    sources: dict[str, SourceConfig] = {}
    # SHA-256 of each tool module's source file; required in pilot and prod, checked when listed.
    tool_module_hashes: dict[str, str] = {}
    # Demo executor only (pilot and prod build no executor). ONE rule, `executor_timeout_ok`, for this field and for
    # the `timeout_s=` keyword of `app.build` (the validator below runs before pydantic turns `true` or '5' into a
    # number).
    executor_timeout_s: float = defaults.EXECUTOR_TIMEOUT_S
    root: Path

    @field_validator("tool_module_hashes", mode="after")
    @classmethod
    def _pins_are_digests(cls, value: dict[str, str]) -> dict[str, str]:
        """A pin is a SHA-256: 64 lower-case hex digits. Anything else (a credential pasted in the wrong place) is
        refused here with a fixed sentence, by position, so no part of it is ever printed."""
        if bad := [i for i, pin in enumerate(value.values(), start=1) if not is_digest(pin)]:
            raise ConfigValueError(
                f"tool_module_hashes: entry {', '.join(str(i) for i in bad)} (counted from 1) is not a SHA-256 (64 lower-case hex digits)"
            )
        return value

    @field_validator("executor_timeout_s", mode="before")
    @classmethod
    def _executor_timeout(cls, value: object) -> object:
        if not executor_timeout_ok(value):
            raise ConfigValueError(EXECUTOR_TIMEOUT_RULE)
        return value

    @field_validator("environment", mode="before")
    @classmethod
    def _renamed_stage(cls, value: object) -> object:
        """The old first stage name, in any case or with spaces round it, is refused with the rename sentence (a hint
        only: every other value is refused by the allowed-values rule, and nothing is ever tidied into a stage)."""
        if isinstance(value, str) and value.strip().casefold() == _OLD_STAGE:
            raise _RenamedStage(
                f"environment: {_OLD_STAGE} was renamed to {STAGES[0]}; write environment: {STAGES[0]} "
                f"(allowed values: {', '.join(STAGES)})"
            )
        return value

    @model_validator(mode="after")
    def _cross_checks(self) -> Config:
        for source, ref in self.scope_inventory.items():
            if not _inventory_ref_ok(ref):
                raise ConfigValueError(
                    f"scope_inventory {shown_name(source, self.sources)}: expected '<page>#<anchor> sha256:<64 hex digits>'"
                )
        for d in self.backends.detector:  # llm_judge names a route
            if getattr(d, "route", None) is not None and d.route not in self.routes:
                raise ConfigValueError(f"backends.detector {d.kind}: its route is not in routes")
        for name, system in self.systems.items():
            if not url_allowed(system.base_url, self.allow_insecure_loopback):
                raise ConfigValueError(
                    f"system {shown_name(name, self.systems)}: base_url must be https "
                    "(http only for loopback with allow_insecure_loopback)"
                )
        refused = []  # environment table, design 4.6: every refusal at once, so one fix round is enough
        if is_live(self.environment):
            refused = [
                f"{c}: {s.kind}" for c, s in self.backends.entries() if (c, s.kind) in DEMO_ONLY
            ]
            refused += ["allow_insecure_loopback"] if self.allow_insecure_loopback else []
        refused += _anchor_refusals(self.environment, self.backends)
        if refused:
            raise ConfigValueError(f"environment {self.environment}: refused: {', '.join(refused)}")
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
        and not (environment in STAGES and is_prod(environment) and anchor.retention_ack)
    ):
        refused.append("anchor mode COMPLIANCE outside prod or without retention_ack")
    if is_prod(environment):
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
            try:
                duplicate = key in seen
            except TypeError:  # a list or mapping used as a key cannot be hashed
                raise ConfigError(
                    f"a mapping key must be a plain value (line {key_node.start_mark.line + 1})"
                ) from None
            if duplicate:
                raise ConfigError(f"duplicate key (line {key_node.start_mark.line + 1})")
            seen.add(key)
        return super().construct_mapping(node, deep)


def load_yaml(text: str) -> Any:
    """``yaml.safe_load`` that refuses duplicate mapping keys. THE one YAML reader: a YAML error leaves it as a
    `ConfigError` that names the line and column only (the error's own text quotes the offending line, which can hold
    a secret), with no cause, so every caller, present and future, gets a value-free error."""
    try:
        return yaml.load(text, Loader=_UniqueKeyLoader)  # noqa: S506  # nosec B506 - SafeLoader subclass
    except yaml.YAMLError as exc:
        raise ConfigError(config_error_text(exc)) from None


_CONFIG_FILES = (
    "config.yaml",
    "egress.yaml",
)  # the two files `_read_yaml` reads: names written in code, so shown


def _read_yaml(path: Path) -> dict:
    """A file of the configuration folder, `{}` only when it does not exist. One that exists but cannot be read (a
    folder, a loop of links, no permission, not UTF-8 text) is a `ConfigError` with a fixed sentence: reading it as
    empty could drop restrictions. This is the only place that guards the read (`errors.read_configured`)."""
    what = shown_name(path.name, _CONFIG_FILES)
    text = read_configured(path, what, missing_ok=True)
    if text is None:
        return {}
    data = load_yaml(text) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"{what}: expected a mapping at the top level")
    return data


def _bare_host(host: object) -> bool:
    """A host name or an IP address and nothing else: no scheme, port, path, login or space (such an entry would
    never match a call, and the call would be refused: a typo that silently narrows, so it is refused at load)."""
    if not isinstance(host, str) or not host.strip() or host != host.strip():
        return False
    if any(c in host for c in "/@?#\\%") or any(c.isspace() for c in host):
        return False
    if ":" in host:
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return False
    return True


def _egress_hosts(raw: dict) -> list[str]:
    """The `hosts` of `egress.yaml`. The only key is `hosts` (another key is a typo that would leave the list empty
    and block every call), and every entry must be a bare host. Neither refusal quotes the file."""
    if extra := set(raw) - {"hosts"}:
        raise ConfigError(f"egress.yaml: {len(extra)} unknown key(s); the only key is hosts")
    hosts = raw.get("hosts") or []
    if not isinstance(hosts, list) or not all(_bare_host(h) for h in hosts):
        raise ConfigError("egress.yaml: hosts must be a list of bare host names or IP addresses")
    return hosts


def confined(base: Path, relative: str) -> Path:
    """``base / relative``, refused if it resolves outside ``base`` (no ``..`` or absolute escapes)."""
    try:
        root = Path(base).resolve()
        path = (root / relative).resolve()
    except (
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
    ):  # a loop of links, a name too long, a null byte
        raise ConfigError("path cannot be resolved") from None
    if not path.is_relative_to(root):
        raise ConfigError("path escapes its folder")
    return path


# The pydantic problem types whose message is a fixed sentence about the SHAPE the field must have, never the value
# that was refused (checked against pydantic_core 2.x on 2026-11-11: each message names the rule, a bound or the
# allowed values, all written by the code). Every other type, and every type a later pydantic adds, gets the fixed
# sentence below, because its message may quote the value (`union_tag_invalid` quotes the typed tag).
_FIXED_SENTENCE_TYPES = frozenset(
    {
        "missing",
        "extra_forbidden",
        "literal_error",
        "enum",
        "string_type",
        "int_type",
        "float_type",
        "bool_type",
        "dict_type",
        "list_type",
        "tuple_type",
        "set_type",
        "frozen_set_type",
        "bytes_type",
        "model_type",
        "model_attributes_type",
        "int_parsing",
        "int_parsing_size",
        "int_from_float",
        "float_parsing",
        "bool_parsing",
        "decimal_type",
        "decimal_parsing",
        "greater_than",
        "greater_than_equal",
        "less_than",
        "less_than_equal",
        "multiple_of",
        "finite_number",
        "too_short",
        "too_long",
        "string_too_short",
        "string_too_long",
        "string_pattern_mismatch",
        "none_required",
        "frozen_instance",
    }
)


def _what(e: Any) -> str:
    """The sentence of one problem. Shown as pydantic wrote it only for the types in `_FIXED_SENTENCE_TYPES`; a
    `value_error` keeps its sentence only when its cause is `ConfigValueError` (Hadavin wrote it); a bad choice of
    kind (`union_tag_invalid`, `union_tag_not_found`) says so with the allowed kinds and never the typed one; anything
    else is `a value was refused (<type>)`. The type name is pydantic's, not the file's."""
    kind = e["type"]
    if kind in _FIXED_SENTENCE_TYPES:
        return e["msg"]
    if kind == "value_error":
        if isinstance(e.get("ctx", {}).get("error"), ConfigValueError):
            return e["msg"]
        return "a value was refused (ValueError)"
    if kind in ("union_tag_invalid", "union_tag_not_found"):
        allowed = e.get("ctx", {}).get("expected_tags")
        tail = (
            f"; allowed: {allowed}"
            if kind == "union_tag_invalid" and isinstance(allowed, str)
            else ""
        )
        return f"the kind is missing or not one of the known kinds{tail}"
    return f"a value was refused ({kind})"


def _rebuilt(exc: ValidationError) -> ValidationError:
    """`exc` when `hidden_input.without_input` made it (it carries a private mark, so its place line holds only names written in
    code or ids of loaded things; an error whose inputs merely read `<hidden>` is not trusted, batch 20 A2), else the same problems rebuilt that way: `error_where(cleaned=True)`
    shows any word-like name, which is safe only for a rebuilt error (batch 19, Issue 7). A plain pydantic model that reaches
    `config_error_text` is rebuilt here, with no code words (a field name is then `<not shown>`)."""
    if is_rebuilt(exc):
        return exc
    return without_input(exc)


def _pairs(exc: ValidationError) -> list[tuple[Any, Any]]:
    """Each problem twice: the rebuilt one (its place line is safe to show) and the original (its context says whether Hadavin
    wrote the sentence: the rebuilt one holds a fixed sentence there, which would be taken for ours). The rebuilt error has the
    same problems in the same order."""
    rebuilt = _rebuilt(exc).errors(include_url=False, include_input=False)
    original = exc.errors(include_url=False, include_input=False)
    if len(rebuilt) != len(original):  # cannot happen: the rebuild keeps every problem
        raise ConfigError("a refused value could not be described")
    return list(zip(rebuilt, original, strict=True))


def _error_line(where_error: Any, what_error: Any) -> str:
    """One problem as `where: what` (used beside the rename sentence)."""
    where = error_where(where_error, cleaned=True)
    return f"{where}: {_what(what_error)}" if where else _what(what_error)


def _value_free_text(exc: ValidationError) -> str:
    """pydantic's own layout (`N validation errors for Config`, then `where`, then `  what [type=...]`), without the
    refused value (`input_value=...`, which could be a secret written into the wrong field) and without the link.
    The place keeps field names and position numbers; an unknown key is `<unknown key>` and a mapping key is shown
    only if it is a plain identifier (`shown_name`). A `ValueError` that a library raised shows its type only."""
    pairs = _pairs(exc)
    lines = [f"{len(pairs)} validation error{'s' if len(pairs) != 1 else ''} for {exc.title}"]
    for shown, original in pairs:
        lines += [
            error_where(shown, cleaned=True),
            f"  {_what(original)} [type={original['type']}]",
        ]
    return "\n".join(lines)


def config_error_text(exc: BaseException) -> str:
    """THE one way an exception from reading or checking configuration becomes error text: it names the problem and
    where it is, never the value that was refused (a mistyped key or a pasted login can be a secret). A pydantic
    error keeps its own layout without `input_value`, the link and the context; the place shows field names and
    positions, an unknown key as `<unknown key>` and any other name from the file only if `errors.shown_name` allows
    it; the sentence of a `value_error` is kept only when it was raised as `ConfigValueError` (the class that means
    "Hadavin wrote this sentence"; any other `ValueError` may quote the value, so its type only is shown). A YAML error keeps its line and column only (its own text
    quotes the offending line); any other error keeps its type only. Callers raise with `from None`, so the cause
    (whose text may carry the value) is not shown either. Not covered: names of fields and kinds, an `id`
    that has the plain shape and describes the thing itself, and the errors that a backend raises after the build
    (names inside `app.build` go through `shown_name`, see the CHANGELOG for the exact list)."""
    if isinstance(exc, ValidationError):
        return _value_free_text(exc)
    if isinstance(exc, yaml.MarkedYAMLError) and exc.problem_mark is not None:
        mark = exc.problem_mark
        return f"not valid YAML (line {mark.line + 1}, column {mark.column + 1})"
    if isinstance(exc, yaml.YAMLError):
        return "not valid YAML"
    return f"a value was refused ({type(exc).__name__})"


def _validation_text(exc: ValidationError) -> str:
    """pydantic's text without the refused values (see `_value_free_text`), except that the rename sentence is shown
    as written, without pydantic's wrapper, beside the other problems found in the same file (one fix round is
    enough)."""
    renamed = [
        e["ctx"]["error"]
        for e in exc.errors()
        if isinstance(e.get("ctx", {}).get("error"), _RenamedStage)
    ]
    if not renamed:
        return _value_free_text(exc)
    others = [
        _error_line(shown, original)
        for shown, original in _pairs(exc)
        if not isinstance(original.get("ctx", {}).get("error"), _RenamedStage)
    ]
    return "; ".join([*(str(r) for r in renamed), *others])


def load_config(config_dir: Path | None = None) -> Config:
    """Every start-up problem (missing HADAVIN_CONFIG_DIR, bad YAML, bad values) is a ConfigError."""
    try:
        root = Path(config_dir) if config_dir else Settings().config_dir  # type: ignore[call-arg]
        raw = _read_yaml(root / "config.yaml")
        egress = _egress_hosts(_read_yaml(root / "egress.yaml"))
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
    except ValidationError as exc:
        raise ConfigError(_validation_text(exc)) from None
    except (ArithmeticError, ValueError, TypeError, yaml.YAMLError) as exc:
        # ArithmeticError holds `decimal.InvalidOperation` (a validator's `Decimal(value)`), which pydantic does not
        # turn into a validation error. A validator's own ValueError is a fixed sentence by `config_error_text`.
        # No `OSError` here: every file read goes through `read_configured`, which refuses with its own sentence.
        raise ConfigError(config_error_text(exc)) from None
