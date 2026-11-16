"""Settings for the intake service: ``config/service.json`` (validated), the backend switch, derived folders under ``HADAVIN_LOCAL`` and the
prices file. Nothing here caches prices, their date check or the project total: ``budget.current_cap`` (WP1) is the only function that computes the cap
and re-reads ``owner_sentence.txt`` on every reserve; this module only holds the paths and the pure ``load_prices`` helper.

Environment: ``HADAVIN_LOCAL`` (required, ``local_unset`` otherwise), ``INTAKE_MODEL_BACKEND`` (``fake`` default or ``anthropic``)."""

from __future__ import annotations

import re
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from json import dumps as _dumps  # private name: no `settings.json` module is exposed
from os import environ as _environ  # private name: no `settings.os` module is exposed to chains through this module
from pathlib import Path

from . import strictjson
from .codes import ConfigError, Refused

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
BACKENDS = ("fake", "anthropic")
PRICES_MAX_AGE_DAYS = 30
ORPHAN_AGE_S = 600  # a reservation older than this is an orphan; the call deadline is capped at half of it so a live call is never one
_EXAMPLE_DOMAINS = (".example.com", ".example.org", ".example.net")
_WINDOWS_DEVICES = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$", re.I)


def _bad(text: str) -> ConfigError:
    return ConfigError("bad_config", text)


def _section(d: dict, key: str) -> dict:
    v = d.get(key)
    if not isinstance(v, dict):
        raise _bad(f"service.json: section {key} missing")
    return v


def _int(d: dict, key: str, lo: int, hi: int) -> int:
    v = d.get(key)
    if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
        raise _bad(f"service.json: {key} must be an integer from {lo} to {hi}")
    return v


_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,100}$")
PURPOSES = ("calibration", "eval", "demo", "other")
TIER_KEYS = ("read", "fallback")


def _extra_body(d: dict) -> dict:
    """``model.extra_body`` is ``{"read": {...}, "fallback": {...}}``: exactly those two keys, each a plain JSON object of at most 512 bytes serialised
    (it is part of the priced body). The old flat form is refused. WHICH keys and values are valid for a model is the backend's rule
    (``model_anthropic.validate_extra_body``, called when the backend is built and again at the point of use), not this module's."""
    v = d.get("extra_body", {"read": {}, "fallback": {}})
    if not isinstance(v, dict) or set(v) != set(TIER_KEYS):
        raise _bad("service.json: extra_body must be an object with exactly the keys read and fallback")
    out: dict = {}
    for k in TIER_KEYS:
        one = v[k]
        if not isinstance(one, dict):
            raise _bad(f"service.json: extra_body.{k} must be an object")
        try:
            raw = _dumps(one, allow_nan=False, sort_keys=True)
        except (TypeError, ValueError):
            raise _bad(f"service.json: extra_body.{k} must be plain JSON") from None
        if len(raw.encode("utf-8")) > 512:
            raise _bad(f"service.json: extra_body.{k} is too large")
        out[k] = one
    return out


def _id_list(d: dict, key: str, default: tuple[str, ...] | None) -> tuple[str, ...]:
    """A list of model ids. ``default=None`` means the key is REQUIRED (absent or null is ``bad_config``: fail closed, no implicit model)."""
    v = d.get(key)
    if v is None:
        if default is None:
            raise _bad(f"service.json: {key} is required")
        return default
    if not isinstance(v, list) or len(v) > 8 or not all(isinstance(x, str) and _ID_RE.fullmatch(x) for x in v):
        raise _bad(f"service.json: {key} must be a list of at most 8 model ids")
    return tuple(v)


_FAMILIES = ("sonnet", "opus", "haiku", "fable")
_DISPLAY_RE = re.compile(r"[A-Za-z0-9 .()-]{1,60}", re.ASCII)


def _families(text: str) -> frozenset[str]:
    t = text.lower()
    return frozenset(f for f in _FAMILIES if f in t)


def _display_names(d: dict) -> dict:
    v = d.get("display_names", {})
    if not isinstance(v, dict) or len(v) > 16:
        raise _bad("service.json: display_names must be an object of at most 16 entries")
    for k, name in v.items():
        if not _ID_RE.fullmatch(k) or not isinstance(name, str) or not 1 <= len(name) <= 60:
            raise _bad("service.json: display_names holds a model id and a name of 1 to 60 characters")
        if not _DISPLAY_RE.fullmatch(
            name
        ):  # ASCII letters, digits, space, dot, parentheses and hyphen only: no homoglyphs, no markup, no format characters
            raise _bad("service.json: a display name may hold only ASCII letters, digits, spaces, dots, parentheses and hyphens")
        other_family = _families(name) != _families(
            k
        )  # the label names the same model families as the id (none in the id: none in the label)
        if other_family:  # mut:family_equal
            raise _bad("service.json: a display name names a different model family than its model id")
    return dict(v)


def _bool(d: dict, key: str, default: bool) -> bool:
    v = d.get(key, default)
    if not isinstance(v, bool):
        raise _bad(f"service.json: {key} must be true or false")
    return v


def _str(d: dict, key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise _bad(f"service.json: {key} must be a non-empty string")
    return v


@dataclass(frozen=True)
class ModelConfig:
    fake_replies_path: Path
    tier_read: str
    tier_fallback: str
    api_host: str
    max_tokens: int
    fake_total_cap_micro: int
    deadline_s: int
    response_cap_bytes: int
    overhead_tokens: int
    consent_prefix: str = ""  # the owner's literal consent sentence (config/service.json; the vendor name lives in config, not in code)
    breaker_failures: int = 3  # consecutive http_4xx / bad_reply / max_tokens live calls after which the guard halts
    extra_body: Mapping[str, dict] = field(
        default_factory=lambda: {"read": {}, "fallback": {}}
    )  # per tier; the backend validates it, priced with the body
    prose_streak_limit: int = (
        10  # documents in a row answered in text instead of a tool call after which the ledger halts (``prose_streak``)
    )
    hostile_streak_limit: int = (
        3  # max_tokens, wrong-shape or unlisted-stop replies in a row after which the ledger halts (``hostile_streak``)
    )
    transport_streak_limit: int = (
        5  # connection failures (calls) in a row inside the window after which the scan stops and a cooldown starts
    )
    transport_window_s: int = 900  # a pause longer than this since the last failure restarts the count
    transport_cooldown_s: int = 600  # new reserves are refused for this long after the limit
    fallback_wait_s: int = 2  # wait before the second try after an HTTP 429 or 5xx without a readable Retry-After
    fallback_wait_max_s: int = 10  # a Retry-After above this makes no second call
    display_names: Mapping[str, str] = field(default_factory=dict)  # model id -> name shown to the approver (display only)
    approved_read_models: tuple[
        str, ...
    ] = ()  # tiers.read must be one of these; REQUIRED in service.json (a change needs a dated evidence file and review)
    stronger_than_read: tuple[str, ...] = ()  # models a fallback tier may be besides the read model itself
    strict_tool: bool = False  # send ``strict`` on the tool definition (the schema subset rules are not recorded yet: keep false)


@dataclass(frozen=True)
class ServiceConfig:
    port: int
    scan_min_age_s: int
    scan_max_files: int
    max_file_bytes: int
    name_regex: str
    currencies: tuple[str, ...]


@dataclass(frozen=True)
class ReviewConfig:
    reason_min_chars: int
    reason_max_chars: int


@dataclass(frozen=True)
class NotifyConfig:
    smtp_host: str
    smtp_port: int
    sender: str
    to: str
    interval_s: int


@dataclass(frozen=True)
class Prices:
    """Integer micro-USD per million tokens (US$1 per million = 1000000)."""

    read_in: int
    read_out: int
    fallback_in: int
    fallback_out: int
    as_of: date
    anthropic_version: str
    read_model: str = ""  # the model ids the prices belong to (prices.json model_ids); budget.current_prices checks them against the tiers
    fallback_model: str = ""


@dataclass(frozen=True)
class Settings:
    model: ModelConfig
    service: ServiceConfig
    review: ReviewConfig
    notify: NotifyConfig
    tenant_id: str
    backend: str
    local: Path
    intake_home: Path
    spend_dir: Path
    run_dir: Path
    video_dir: Path
    owner_sentence_path: Path
    prices_path: Path
    purpose: str = "other"  # why this process runs (``INTAKE_PURPOSE``): calibration, eval, demo or other; logged with every call


def read_config(path: Path | None = None) -> dict:
    """The raw, validated-as-JSON service config (no environment needed)."""
    p = path or CONFIG / "service.json"
    try:
        raw = p.read_bytes()
        data = strictjson.loads(raw)
    except (OSError, ValueError) as e:
        raise _bad(f"service.json unreadable: {type(e).__name__}") from None
    if not isinstance(data, dict):
        raise _bad("service.json: top level must be an object")
    return data


def _parse_config(data: dict, root: Path) -> tuple[ModelConfig, ServiceConfig, ReviewConfig, NotifyConfig]:
    m = _section(data, "model")
    tiers = _section(m, "tiers")
    model = ModelConfig(
        fake_replies_path=root / _str(m, "fake_replies_path"),
        tier_read=_str(tiers, "read"),
        tier_fallback=_str(tiers, "fallback"),
        api_host=_str(m, "api_host"),
        max_tokens=_int(m, "max_tokens", 1, 100000),
        fake_total_cap_micro=_int(m, "fake_total_cap_micro", 1, 10**15),
        deadline_s=_int(m, "deadline_s", 1, ORPHAN_AGE_S // 2),
        response_cap_bytes=_int(m, "response_cap_bytes", 1024, 10**8),
        overhead_tokens=_int(m, "overhead_tokens", 0, 10**6),
        consent_prefix=_str(m, "consent_prefix"),
        breaker_failures=_int(m, "breaker_failures", 1, 100) if "breaker_failures" in m else 3,
        extra_body=_extra_body(m),
        prose_streak_limit=_int(m, "prose_streak_limit", 1, 1000) if "prose_streak_limit" in m else 10,
        hostile_streak_limit=_int(m, "hostile_streak_limit", 1, 100) if "hostile_streak_limit" in m else 3,
        transport_streak_limit=_int(m, "transport_streak_limit", 1, 100) if "transport_streak_limit" in m else 5,
        transport_window_s=_int(m, "transport_window_s", 1, 86400) if "transport_window_s" in m else 900,
        transport_cooldown_s=_int(m, "transport_cooldown_s", 0, 86400) if "transport_cooldown_s" in m else 600,
        fallback_wait_s=_int(m, "fallback_wait_s", 0, 30) if "fallback_wait_s" in m else 2,
        fallback_wait_max_s=_int(m, "fallback_wait_max_s", 0, 60) if "fallback_wait_max_s" in m else 10,
        display_names=_display_names(m),
        approved_read_models=_id_list(m, "approved_read_models", None),
        stronger_than_read=_id_list(m, "stronger_than_read", ()),
        strict_tool=_bool(m, "strict_tool", False),
    )
    if "send_temperature" in m:
        raise _bad("service.json: send_temperature was removed; the API rejects non-default sampling parameters")
    configured = {model.tier_read, model.tier_fallback, *model.approved_read_models, *model.stronger_than_read}
    if not set(model.display_names) <= configured:  # mut:names_configured
        raise _bad("service.json: display_names may only name configured models")
    if model.fallback_wait_s > model.fallback_wait_max_s:
        raise _bad("service.json: fallback_wait_s is above fallback_wait_max_s")
    if model.tier_read not in model.approved_read_models:
        raise _bad("service.json: tiers.read is not one of approved_read_models")
    if model.tier_fallback != model.tier_read and model.tier_fallback not in model.stronger_than_read:
        raise _bad("service.json: tiers.fallback must be the read model or listed in stronger_than_read")
    s = _section(data, "service")
    cur = s.get("currencies")
    if not isinstance(cur, list) or not cur or not all(isinstance(c, str) and re.fullmatch(r"[A-Z]{3}", c) for c in cur):
        raise _bad("service.json: currencies must be a list of three-letter upper-case codes")
    name_regex = _str(s, "name_regex")
    try:
        re.compile(name_regex)
    except re.error:
        raise _bad("service.json: name_regex does not compile") from None
    service = ServiceConfig(
        port=_int(s, "port", 1024, 65535),
        scan_min_age_s=_int(s, "scan_min_age_s", 0, 3600),
        scan_max_files=_int(s, "scan_max_files", 1, 100),
        max_file_bytes=_int(s, "max_file_bytes", 1, 10**8),
        name_regex=name_regex,
        currencies=tuple(cur),
    )
    r = _section(data, "review")
    review = ReviewConfig(_int(r, "reason_min_chars", 1, 1000), _int(r, "reason_max_chars", 1, 10000))
    if review.reason_min_chars > review.reason_max_chars:
        raise _bad("service.json: reason_min_chars is above reason_max_chars")
    n = _section(data, "notify")
    notify = NotifyConfig(
        _str(n, "smtp_host"), _int(n, "smtp_port", 1, 65535), _str(n, "from"), _str(n, "to"), _int(n, "interval_s", 1, 3600)
    )
    require_example = n.get("require_example_domain", True)
    if not isinstance(require_example, bool):
        raise _bad("service.json: notify.require_example_domain must be true or false")
    for addr in (notify.sender, notify.to):
        if "@" not in addr:
            raise _bad("service.json: notify addresses must be e-mail addresses")
        if require_example and not addr.split("@", 1)[1].endswith(_EXAMPLE_DOMAINS):  # the demo rule; a client build sets the flag to false
            raise _bad("service.json: notify addresses must be on a reserved example domain")
    return model, service, review, notify


def read_model_id(path: Path | None = None, *, settings: Settings | None = None) -> str:
    """The read-tier model id: from the loaded ``settings`` when given (no second file read), else from ``service.json``. Raises ``bad_config`` when unreadable."""
    if settings is not None:
        return settings.model.tier_read
    tiers = _section(_section(read_config(path), "model"), "tiers")
    return _str(tiers, "read")


def display_name(model_id: str, path: Path | None = None, *, settings: Settings | None = None) -> str:
    """The configured display name of a model id (from the loaded ``settings`` when given, else from ``service.json``); an unknown id or any failure
    returns the id itself (display only, never raises)."""
    try:
        names = settings.model.display_names if settings is not None else _display_names(_section(read_config(path), "model"))
        return names.get(model_id, model_id)
    except (ConfigError, TypeError, AttributeError, ValueError):
        return model_id


def _raw_policy() -> dict:
    try:
        data = strictjson.load_path(CONFIG / "policy.json")
    except (OSError, ValueError) as e:
        raise _bad(f"policy.json unreadable: {type(e).__name__}") from None
    if not isinstance(data, dict):
        raise _bad("policy.json: top level must be an object")
    return data


def read_kill_switch() -> bool:
    """``executor.kill_switch`` read as raw JSON from ``config/policy.json`` at EVERY call (the exporter calls it per export; never cached).
    Fail closed INSIDE the function: anything other than the JSON value ``false`` (true, a string, a number, a missing key) and any failure to read
    the policy file means the switch is engaged (it never raises)."""
    try:
        ex = _raw_policy().get("executor")
    except Exception:  # noqa: BLE001 (fail closed: whatever goes wrong, the switch counts as engaged)
        return True
    return not (isinstance(ex, dict) and ex.get("kill_switch") is False)


def read_policy_value(key: str):
    """One top-level value of ``config/policy.json`` (the single source for limits such as ``max_lines_per_draft``)."""
    d = _raw_policy()
    if key not in d:
        raise _bad(f"policy.json: {key} missing")
    return d[key]


LOG_LEVELS = ("normal", "verbose")


def read_log_level(env: dict | None = None) -> str:
    """``INTAKE_LOG`` (the one reader, errata 51.3): ``normal`` (default when unset or empty) or ``verbose``; anything else is ``bad_config``."""
    env = _environ if env is None else env
    v = env.get("INTAKE_LOG", "") or "normal"
    if v not in LOG_LEVELS:
        raise ConfigError("bad_config", "INTAKE_LOG must be normal or verbose")
    return v


def read_tenant_id() -> str:
    """``client_id`` from ``config/policy.json`` (never from a request)."""
    v = _raw_policy().get("client_id")
    if not isinstance(v, str) or not v.strip():
        raise _bad("policy.json: client_id missing")
    return v


def require_anthropic_version(prices: Prices) -> str:
    """The Anthropic backend (WP1) calls this before any network call: an empty ``anthropic_version`` is refused (``prices_missing``). The version is
    optional in ``load_prices`` so that another provider's prices file loads."""
    if not isinstance(prices.anthropic_version, str) or not prices.anthropic_version.strip():
        raise Refused("prices_missing", "anthropic_version is empty")
    return prices.anthropic_version


def utc_today() -> date:
    """The one clock seam for the price-age rule: tests (and the WP1 budget tests) replace it to move time inside a running process."""
    return datetime.now(UTC).date()


_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def load_prices(path: Path, today: date | None = None, *, clock=None) -> Prices:
    """Re-reads the file on every call (the caller never caches the result). Raises ``Refused('prices_missing')`` for a missing or unreadable file, a
    zero or non-integer price, a date that is not strictly ``YYYY-MM-DD``, a future date or a date older than 30 days."""
    today = today or (clock or utc_today)()  # looked up at CALL time, so monkeypatching ``utc_today`` takes effect
    try:
        d = strictjson.load_path(path)
        p = d["prices_micro_usd_per_million_tokens"]
        vals = [p["read"]["in"], p["read"]["out"], p["fallback"]["in"], p["fallback"]["out"]]
        if not _DATE_RE.fullmatch(d["prices_as_of"]):
            raise ValueError("date shape")
        as_of = date.fromisoformat(d["prices_as_of"])
        ver = d.get("anthropic_version", "")
        ids = d.get("model_ids") or {}
        read_model, fallback_model = ids.get("read", ""), ids.get("fallback", "")
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        raise Refused("prices_missing", "prices.json missing or unreadable") from None
    if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in vals):
        raise Refused("prices_missing", "prices must be positive integers")
    if not isinstance(ver, str):
        raise Refused(
            "prices_missing", "anthropic_version must be a string"
        )  # optional here: the Anthropic backend (WP1) refuses an empty value
    if as_of > today or today - as_of > timedelta(days=PRICES_MAX_AGE_DAYS):
        raise Refused("prices_missing", "prices_as_of is in the future or older than 30 days")
    if not (isinstance(read_model, str) and isinstance(fallback_model, str)):
        raise Refused("prices_missing", "model_ids must be strings")
    return Prices(vals[0], vals[1], vals[2], vals[3], as_of, ver, read_model, fallback_model)


def load(env: dict | None = None) -> Settings:
    """Build the settings. ``env`` defaults to the process environment (tests pass a dict). Missing ``HADAVIN_LOCAL`` or a bad config is exit 3."""
    env = _environ if env is None else env
    local_raw = env.get("HADAVIN_LOCAL", "")
    if not local_raw.strip():
        raise ConfigError("local_unset", "HADAVIN_LOCAL is not set")
    backend = env.get("INTAKE_MODEL_BACKEND", "fake") or "fake"
    if backend not in BACKENDS:
        raise ConfigError("bad_backend", "INTAKE_MODEL_BACKEND must be fake or anthropic")
    model, service, review, notify = _parse_config(read_config(), ROOT)
    local = Path(local_raw)
    if not local.is_absolute():
        raise ConfigError("bad_config", "HADAVIN_LOCAL must be an absolute path")
    home = local / "intake"
    purpose = env.get("INTAKE_PURPOSE", "") or "other"
    if purpose not in PURPOSES:
        raise ConfigError("bad_config", "INTAKE_PURPOSE must be calibration, eval, demo or other")
    return Settings(
        model=model,
        service=service,
        review=review,
        notify=notify,
        tenant_id=read_tenant_id(),
        backend=backend,
        local=local,
        intake_home=home,
        spend_dir=local / "spend",
        run_dir=local / "run",
        video_dir=local / "video",
        owner_sentence_path=home / "owner_sentence.txt",
        prices_path=home / "prices.json",
        purpose=purpose,
    )


def is_name_allowed(name: str, regex: str) -> bool:
    """Item-name rule: ``name_regex`` and, for the part of the stem before its first dot, not a Windows device name."""
    if not re.fullmatch(regex, name):
        return False
    return not _WINDOWS_DEVICES.match(name.split(".", 1)[0])


def under_temp_folder(local: Path) -> bool:
    tmp = Path(tempfile.gettempdir()).resolve()
    here = Path(local).resolve()
    if here == tmp:  # the temporary root is shared with every other program: only a folder below it counts
        return False
    try:
        here.relative_to(tmp)
    except ValueError:
        return False
    return True


_HASH_LINE = re.compile(r"[0-9a-f]{64}")


def load_hash_list(path: Path) -> frozenset[str]:
    """The ONE reader of ``synthetic_hashes.txt`` (``check`` and the WP1 data gate both use it): UTF-8 with an optional BOM, one lowercase 64-hex hash
    per line, surrounding whitespace ignored, blank and malformed lines ignored; a missing or unreadable file is the empty set (= STOP)."""
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except (OSError, ValueError):
        return frozenset()
    return frozenset(ln.strip() for ln in text.splitlines() if _HASH_LINE.fullmatch(ln.strip()))


def require_safe_backend(s: Settings) -> None:
    """The backend factory (``model.make_backend``, WP1) is the ONLY caller (errata 6); ``serve`` and ``extract`` reach it through the factory: the fake backend is refused on a ``HADAVIN_LOCAL`` outside the operating system's temporary folder,
    so a forgotten default never pollutes the real queue and spend ledger."""
    if s.backend == "fake" and not under_temp_folder(s.local):
        raise Refused("fake_on_real_folder", "the fake backend runs only in a temporary folder")
