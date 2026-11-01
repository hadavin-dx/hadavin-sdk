"""K6 measurement: labels, demotion, promotion evidence, the ceiling and the weekly report.

A mistake the pilot makes is only worth something if it is counted on the client's own incidents. This module
turns a person's click (``agree | partial | wrong | harmful`` on a shadow card, ``abstain_ok | missed`` on an
abstain card) into rows, lowers an action's level when the rules say so, computes the numbers a promotion needs,
and writes the weekly report. Pure policy over the ``Store`` Protocol, the ``AuditSink`` and the ``Channel``: no
vendor name, no SQL (the same numbers come from the views, ``v_pilot_week`` and friends, and a contract test
checks both agree).

Rules that matter (kernel design K6, section 6.1):

* A label comes from a person known to ``principals.yaml``, on a run that exists, and fits the run: the four
  proposal labels need a plan, the two abstain labels need none. The latest eligible label of a run is its label.
* A ``harmful`` label, or 3 ``wrong`` labels for one action in 14 days, demotes that action (append-only
  ``level_events``; a line owner's signed ``clear`` is the only way back). The demotion row and the label are one
  transaction: if either cannot be stored the label is refused and nothing changes.
* The effective level never rises above the config level, and a store that cannot be read means ``shadow``.
* A chat label counts as evidence; a csv label counts only after a line owner approves the import.
* ``promote-check`` writes ``promotions/<agent>.<action>.json`` only when every number is met, a green replay
  record exists for the current config hash and the ceiling is not breached. The loader refuses ``suggest``
  without a matching file.
* The ceiling (``baseline.yaml``) counts ``harmful`` labels in a rolling window. A breach demotes every action once
  per breach, tells the line owner and blocks every promotion until the window clears or the sponsor changes
  ``max`` in writing.
"""

from __future__ import annotations

import contextvars
import csv
import hashlib
import io
import json
import logging
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from hadavin_sdk import replay_records
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import (
    AuditEvent,
    Label,
    LevelEvent,
    Plan,
    TickState,
    iso_week,
    label_order,
    latest_labels,
    now,
)
from hadavin_sdk.stats import upper_error_bound
from hadavin_sdk.store.protocol import HarmfulSticky, NotFound, StaleState

if TYPE_CHECKING:
    from hadavin_sdk.approvals.channel import Channel
    from hadavin_sdk.approvals.hmac_v0 import Action
    from hadavin_sdk.audit.protocol import AuditSink
    from hadavin_sdk.limits import Limits
    from hadavin_sdk.registry import Registry
    from hadavin_sdk.store.protocol import Store

_LOG = logging.getLogger("hadavin_sdk.measure")
# (team id, action_ts) of the signed click being handled: every audit row written while it runs carries both
_CLICK: contextvars.ContextVar[tuple[str, str]] = contextvars.ContextVar(
    "measure_click", default=("", "")
)

PROPOSAL_LABELS = ("agree", "partial", "wrong", "harmful")
ABSTAIN_LABELS = ("abstain_ok", "missed")
LABELS = PROPOSAL_LABELS + ABSTAIN_LABELS
BASELINE_FILE = "baseline.yaml"
PROMOTIONS_DIR = "promotions"
WRONGS_KIND = (
    "wrongs"  # the reason prefix of a recent-wrongs demotion; the numbers behind it are in `Policy`
)
_ALIASES = {
    "should_have_answered": "missed"
}  # the abstain button's value before K6 built its parser
_ID = re.compile(r"[A-Za-z0-9_.-]{1,100}")
_NAME = re.compile(r"[A-Za-z0-9_-]{1,100}")
_PLACEHOLDER = re.compile(r"<[^>]*>")


@dataclass(frozen=True)
class Thresholds:
    """Promotion shadow -> suggest, per (agent, action) (kernel 6.1). Built from the `Policy`."""

    min_labelled: int
    min_agree: float
    max_wrong_harmful: int
    harmful_window_days: int
    min_coverage: float
    min_labellers: int


@dataclass(frozen=True)
class Policy:
    """Every number of the measurement that is policy, in ONE place, with its documented default. A client signs
    these with the rest of ``baseline.yaml`` (an optional ``policy:`` mapping; omit a key to take the default; an
    unknown key or an out-of-range value refuses to start). The code reads nothing else: no number below appears
    anywhere else in the measurement."""

    # promotion shadow -> suggest (kernel 6.1; the owner confirms the numbers per engagement)
    promotion_min_labelled: int = 30
    promotion_min_agree: float = 0.70
    promotion_max_wrong_harmful: int = 1
    promotion_harmful_window_days: int = 28
    promotion_min_coverage: float = 0.80
    # distinct people whose labels the evidence rests on (one person cannot supply all of it)
    promotion_min_labellers: int = 2
    # automatic demotion: this many `wrong` runs inside this many days (a harmful label always demotes at once)
    wrong_limit: int = 3
    wrong_window_days: int = 14
    # the weekly report flags a rise in wrong labels of at least this many over the week before
    wrong_rise_flag_min: int = 1
    # a harmful demotion cannot be cleared sooner than this many hours after it, even by a second person
    harmful_clear_min_age_h: int = 24
    # the one team (workspace) id whose signed clicks are acted on; "" = not checked. Set per client in baseline.yaml
    allowed_team_id: str = ""
    # The numbers above may not be weaker than the spec's (the defaults here) unless this is true, which is then
    # printed in every report and written into every promotion file.
    allow_weaker_than_spec: bool = False
    # how the report shows local time beside UTC (studio convention: UTC and IST)
    report_local_offset_minutes: int = 330
    report_local_label: str = "IST"
    # tick cadence: the demotion/ceiling re-check (also retries unannounced cards and notices; at most 300) and the
    # click-nonce purge
    enforce_every_s: int = 300
    purge_every_s: int = 300
    # how long a click nonce is kept; at least three times the signature window (the window itself is the channel
    # protocol's, `approvals.hmac_v0.MAX_AGE_S`, not policy)
    seen_actions_keep_s: int = 900

    def thresholds(self) -> Thresholds:
        return Thresholds(
            self.promotion_min_labelled,
            self.promotion_min_agree,
            self.promotion_max_wrong_harmful,
            self.promotion_harmful_window_days,
            self.promotion_min_coverage,
            self.promotion_min_labellers,
        )

    @property
    def wrong_window(self) -> timedelta:
        return timedelta(days=self.wrong_window_days)

    @property
    def local_tz(self) -> timezone:
        return timezone(timedelta(minutes=self.report_local_offset_minutes))


DEFAULT_POLICY = Policy()
DEFAULTS = DEFAULT_POLICY.thresholds()


def _policy_from(raw: Any) -> Policy:
    """Validate a ``policy:`` mapping from baseline.yaml. Strict: unknown keys, wrong types and out-of-range
    numbers are all refused, naming the key."""
    from hadavin_sdk.approvals.hmac_v0 import MAX_AGE_S

    if raw is None:
        return DEFAULT_POLICY
    if not isinstance(raw, dict):
        raise ConfigError(f"{BASELINE_FILE}: `policy` must be a mapping")
    fields = Policy.__dataclass_fields__
    if unknown := sorted(set(raw) - set(fields)):
        raise ConfigError(f"{BASELINE_FILE}: policy has unknown keys: {', '.join(unknown)}")
    default = DEFAULT_POLICY
    out: dict[str, Any] = {}
    for key, value in raw.items():
        want = type(getattr(default, key))
        ok = isinstance(value, want) and (want is bool or not isinstance(value, bool))
        if want is float:
            ok = isinstance(value, int | float) and not isinstance(value, bool)
        if not ok:
            raise ConfigError(f"{BASELINE_FILE}: policy.{key} must be a {want.__name__}")
        out[key] = float(value) if want is float else value
    p = replace(default, **out)
    bounds = {
        "promotion_min_labelled": (1, 10**6),
        "promotion_max_wrong_harmful": (0, 10**6),
        "promotion_harmful_window_days": (1, 3650),
        "wrong_limit": (1, 1000),
        "wrong_window_days": (1, 3650),
        "promotion_min_labellers": (1, 1000),
        "wrong_rise_flag_min": (1, 10**6),
        "harmful_clear_min_age_h": (0, 8760),
        "report_local_offset_minutes": (-720, 840),
        "enforce_every_s": (1, 300),
        "purge_every_s": (0, 86400),
        "seen_actions_keep_s": (3 * MAX_AGE_S, 10**7),
    }
    for key, (low, high) in bounds.items():
        if not low <= getattr(p, key) <= high:
            raise ConfigError(f"{BASELINE_FILE}: policy.{key} must be between {low} and {high}")
    for key in ("promotion_min_agree", "promotion_min_coverage"):
        if not 0 < getattr(p, key) <= 1:
            raise ConfigError(f"{BASELINE_FILE}: policy.{key} must be above 0 and at most 1")
    if not p.allow_weaker_than_spec:
        spec = DEFAULT_POLICY
        weaker = [
            k
            for k, bad in {
                "promotion_min_labelled": p.promotion_min_labelled < spec.promotion_min_labelled,
                "promotion_min_agree": p.promotion_min_agree < spec.promotion_min_agree,
                "promotion_max_wrong_harmful": p.promotion_max_wrong_harmful
                > spec.promotion_max_wrong_harmful,
                "promotion_harmful_window_days": p.promotion_harmful_window_days
                < spec.promotion_harmful_window_days,
                "promotion_min_coverage": p.promotion_min_coverage < spec.promotion_min_coverage,
                "promotion_min_labellers": p.promotion_min_labellers < spec.promotion_min_labellers,
                "wrong_limit": p.wrong_limit > spec.wrong_limit,
                "wrong_window_days": p.wrong_window_days < spec.wrong_window_days,
                "harmful_clear_min_age_h": p.harmful_clear_min_age_h < spec.harmful_clear_min_age_h,
            }.items()
            if bad
        ]
        if weaker:
            raise ConfigError(
                f"{BASELINE_FILE}: policy.{', '.join(weaker)} is weaker than the spec's number; "
                "set policy.allow_weaker_than_spec: true to say so on purpose (it is printed in every report)"
            )
    if p.allowed_team_id and not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", p.allowed_team_id):
        raise ConfigError(f"{BASELINE_FILE}: policy.allowed_team_id must be a plain id")
    if not re.fullmatch(r"[A-Za-z0-9+:_-]{1,12}", p.report_local_label):
        raise ConfigError(f"{BASELINE_FILE}: policy.report_local_label must be a short plain label")
    return p


# --- parsing -----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedAction:
    kind: str  # "label" or "clear"
    args: tuple[str, ...]


def parse_action_value(value: str) -> ParsedAction | None:
    """A button value the measurement owns, or None (an approval value is not ours). The separator is ``|`` and the
    first field names the kind: ``label|<run_id>|<label>`` or ``clear|<agent_id>|<action_id>|<seq>``. A ``:`` payload or
    an unknown label is refused."""
    parts = value.split("|")
    if len(parts) == 3 and parts[0] == "label":
        name = _ALIASES.get(
            parts[2], parts[2]
        )  # cards posted before K6 carried `should_have_answered`
        if _ID.fullmatch(parts[1]) and name in LABELS:
            return ParsedAction("label", (parts[1], name))
    if (
        parts[0] == "clear"
        and len(parts) == 4
        and all(_NAME.fullmatch(p) for p in parts[1:3])
        and parts[3].isdigit()
    ):
        return ParsedAction(
            "clear", (parts[1], parts[2], parts[3])
        )  # the demotion's seq binds the button
    if parts[0] in ("stop", "reset") and len(parts) == 1:  # the kill switch, by a signed action
        return ParsedAction(parts[0], ())
    if parts[0] == "approve_import" and len(parts) == 2 and re.fullmatch(r"[0-9a-f]{64}", parts[1]):
        return ParsedAction("approve_import", (parts[1],))
    return None


def is_ours(value: str) -> bool:
    """First field decides whether this click is a measurement click (even a malformed one: it is refused here,
    never read as an approval)."""
    return re.split(r"[|:]", value, maxsplit=1)[0] in (
        "label",
        "clear",
        "stop",
        "reset",
        "approve_import",
    )


# --- baseline and ceiling ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Ceiling:
    metric: str
    max: int
    window_days: int
    source: str
    # The label classes that count against the ceiling. `load_baseline` requires it in baseline.yaml (no default:
    # what counts as the costliest failure is the sponsor's written choice) and always includes `harmful`. The
    # default here is only for code that builds a Ceiling by hand.
    counts: tuple[str, ...] = ("harmful",)


@dataclass(frozen=True)
class CeilingStatus:
    ceiling: Ceiling
    harmful: int  # X: runs whose latest label is in `ceiling.counts`, labelled inside the window
    labelled: int  # Y: runs labelled inside the window
    breached: bool
    latest_harmful_at: (
        datetime | None
    )  # the newest harmful label while breached: one breach episode per label


_CEILING_HELP = (
    "Copy metric, counts, max, window_days and source from scoping.md `## Success metric and ceiling` "
    "(the sponsor sets them in writing; nothing here has a default)."
)


def _read_baseline(root: Path) -> dict:
    path = Path(root) / BASELINE_FILE
    if not path.is_file():
        raise ConfigError(f"{BASELINE_FILE} is required in pilot and prod: {path} does not exist")
    from hadavin_sdk.config import load_yaml

    try:
        data = load_yaml(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001 - any parse failure is a refusal, naming the class only
        raise ConfigError(f"{BASELINE_FILE}: cannot be read ({type(exc).__name__})") from None
    return data if isinstance(data, dict) else {}


def load_policy(root: Path) -> Policy:
    """The optional ``policy:`` mapping of baseline.yaml; the documented defaults when there is none (or no file:
    dev without a baseline)."""
    if not (Path(root) / BASELINE_FILE).is_file():
        return DEFAULT_POLICY
    return _policy_from(_read_baseline(root).get("policy"))


def load_baseline(root: Path) -> Ceiling:
    """``baseline.yaml`` ``ceiling`` (K0). Required: the pilot tooling refuses to start without a filled one."""
    data = _read_baseline(root)
    raw = data.get("ceiling")
    if not isinstance(raw, dict):
        raise ConfigError(f"{BASELINE_FILE}: `ceiling` is required. {_CEILING_HELP}")
    for key in ("metric", "max", "window_days", "source"):
        value = "" if raw.get(key) is None else str(raw[key]).strip()
        if not value or _PLACEHOLDER.search(value):
            raise ConfigError(
                f"{BASELINE_FILE}: ceiling.{key} is missing, empty or still a <placeholder>. {_CEILING_HELP}"
            )
    counts = raw.get("counts")
    if not isinstance(counts, list) or not counts or not all(isinstance(c, str) for c in counts):
        raise ConfigError(
            f"{BASELINE_FILE}: ceiling.counts is required (a list of label classes, for example "
            f"[harmful]); there is no default. {_CEILING_HELP}"
        )
    unknown = sorted(set(counts) - set(LABELS))
    if unknown:
        raise ConfigError(
            f"{BASELINE_FILE}: ceiling.counts names unknown labels: {', '.join(unknown)}"
        )
    if "harmful" not in counts:
        raise ConfigError(
            f"{BASELINE_FILE}: ceiling.counts must include harmful: a harmful verdict always counts "
            "against the ceiling and config cannot take it out"
        )
    try:
        ceil_max = int(str(raw["max"]).strip())
        window = int(str(raw["window_days"]).strip())
    except ValueError:
        raise ConfigError(
            f"{BASELINE_FILE}: ceiling.max and ceiling.window_days must be whole numbers"
        ) from None
    if ceil_max < 0 or window < 1:
        raise ConfigError(f"{BASELINE_FILE}: ceiling.max must be >= 0 and window_days >= 1")
    return Ceiling(
        str(raw["metric"]).strip(),
        ceil_max,
        window,
        str(raw["source"]).strip(),
        tuple(dict.fromkeys(counts)),
    )


# --- numbers -----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Numbers:
    proposals: int
    labelled: int
    agree: int
    partial: int
    wrong: int
    harmful: int
    harmful_recent: int
    coverage: float
    agree_rate: float
    upper_bound: float | None  # 95 % upper bound on the wrong-or-harmful rate
    labellers: int = 0  # distinct people behind the labels
    top_labeller_share: float = 0.0  # the busiest labeller's share of the labels

    def as_dict(self) -> dict[str, Any]:
        return {
            "proposals": self.proposals,
            "labelled": self.labelled,
            "agree": self.agree,
            "partial": self.partial,
            "wrong": self.wrong,
            "harmful": self.harmful,
            "harmful_recent": self.harmful_recent,
            "coverage": round(self.coverage, 4),
            "agree_rate": round(self.agree_rate, 4),
            "upper_bound": None if self.upper_bound is None else round(self.upper_bound, 4),
            "labellers": self.labellers,
            "top_labeller_share": round(self.top_labeller_share, 4),
        }


def numbers_for(
    labels: list[Label], proposals: int, at: datetime, th: Thresholds = DEFAULTS
) -> Numbers:
    """The promotion numbers from the labels of one action. One label per run (the latest eligible one), only the
    four proposal labels; an unapproved csv label is not here at all."""
    mine = {r: x for r, x in latest_labels(labels).items() if x.label in PROPOSAL_LABELS}
    count = Counter(x.label for x in mine.values())
    n = len(mine)
    cutoff = at - timedelta(days=th.harmful_window_days)
    recent = sum(1 for x in mine.values() if x.label == "harmful" and x.created_at >= cutoff)
    bad = count["wrong"] + count["harmful"]
    people = Counter(x.principal_id for x in mine.values())
    return Numbers(
        proposals=proposals,
        labelled=n,
        agree=count["agree"],
        partial=count["partial"],
        wrong=count["wrong"],
        harmful=count["harmful"],
        harmful_recent=recent,
        coverage=(n / proposals) if proposals else 0.0,
        agree_rate=(count["agree"] / n) if n else 0.0,
        upper_bound=upper_error_bound(bad, n),
        labellers=len(people),
        top_labeller_share=(max(people.values()) / n) if n else 0.0,
    )


def shortfalls(nm: dict[str, Any], th: Thresholds = DEFAULTS) -> list[str]:
    """Each §6.1 number that is not met, from a numbers mapping (``Numbers.as_dict`` or a promotion file)."""
    out = []
    try:
        if nm["labelled"] < th.min_labelled:
            out.append(f"labelled {nm['labelled']} < {th.min_labelled}")
        if nm["agree_rate"] < th.min_agree:
            out.append(f"agree {nm['agree_rate']:.0%} < {th.min_agree:.0%}")
        if nm["wrong"] + nm["harmful"] > th.max_wrong_harmful:
            out.append(f"wrong + harmful {nm['wrong'] + nm['harmful']} > {th.max_wrong_harmful}")
        if nm["harmful_recent"] > 0:
            out.append(f"{nm['harmful_recent']} harmful in the last {th.harmful_window_days} days")
        if nm["coverage"] < th.min_coverage:
            out.append(f"label coverage {nm['coverage']:.0%} < {th.min_coverage:.0%}")
        if nm["labellers"] < th.min_labellers:
            out.append(f"labelled by {nm['labellers']} distinct people < {th.min_labellers}")
    except (KeyError, TypeError):
        out.append("numbers are missing or malformed")
    return out


def csv_import_id(text: str) -> str:
    """The id of a csv import: the file's full SHA-256 (what the approval click names; a short prefix of text
    someone else supplies could be made to collide)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def week_start(moment: datetime) -> date:
    return iso_week(moment)


def caught_week(events: list[AuditEvent], week: date) -> dict[str, int]:
    """Audit events carrying ``caught_by``, counted by value for one ISO week (the python twin of v_caught_week)."""
    seen = {(e.caught_by, e.run_id) for e in events if e.caught_by and iso_week(e.ts) == week}
    return dict(
        Counter(by for by, _ in seen)
    )  # one per run: relabelling a run does not count it twice


# --- promotion files ---------------------------------------------------------------------------------------


def promotion_path(root: Path, agent_id: str, action_id: str) -> Path:
    return Path(root) / PROMOTIONS_DIR / f"{agent_id}.{action_id}.json"


def _json(obj: Any) -> str:
    """Stable text for a promotion file (floats are fine here: the file is evidence, not money)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _file_sha(body: dict[str, Any]) -> str:
    rest = {k: v for k, v in body.items() if k != "sha256"}
    return hashlib.sha256(_json(rest).encode()).hexdigest()


def promotion_problems(reg: Registry, agent_id: str, action_id: str) -> list[str]:
    """Why ``suggest`` for (agent, action) may not load: the evidence file is missing, was edited, belongs to another
    config hash, model or prompt, or holds a number below §6.1. The config hash excludes ``levels``, so the file
    still matches after the promotion PR flips the level."""
    where = f"agent {agent_id}: suggest for {action_id}"
    if not (_NAME.fullmatch(agent_id) and _NAME.fullmatch(action_id)):
        return [f"{where} has an id that cannot name a promotion file"]
    path = promotion_path(reg.config.root, agent_id, action_id)
    if not path.is_file():
        return [f"{where} needs {PROMOTIONS_DIR}/{path.name} (run `hadavin-sdk promote-check`)"]
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return [f"{where}: {path.name} is not valid JSON"]
    if not isinstance(body, dict):
        return [f"{where}: {path.name} is not a JSON object"]
    if body.get("sha256") != _file_sha(body):
        return [f"{where}: {path.name} was edited (its SHA-256 does not match)"]
    agent = reg.agents[agent_id]
    want = {
        "agent_id": agent_id,
        "action_id": action_id,
        "config_hash": reg.config_hash(agent_id),
        "model_id": reg.config.routes[agent.model_route].model_id,
        "prompt_sha256": reg.prompt_sha256(agent_id),
    }
    problems = [
        f"{where}: {path.name} {k} does not match the current config"
        for k, v in want.items()
        if body.get(k) != v
    ]
    file_th, why = _file_thresholds(body)
    if file_th is None:
        problems.append(f"{where}: {path.name} {why}")
    else:
        # judged by the thresholds the file was written under, which may not be weaker than the spec's unless the file
        # says (and the report printed) that the client signed weaker ones on purpose
        problems += [
            f"{where}: {path.name} {s}" for s in shortfalls(body.get("numbers") or {}, file_th)
        ]
    if (body.get("ceiling") or {}).get("breached") is not False:
        problems.append(f"{where}: {path.name} was written with the ceiling breached")
    # The SHA-256 is unkeyed: anyone who can write the file can re-seal it. So the replay record the file names
    # must exist in replay-records.jsonl for the current config, and (at start-up, `Measure.promotion_store_problems`)
    # the numbers are derived again from the store.
    named = (body.get("replay_record") or {}).get("bundle_sha256")
    if named not in {r.bundle_sha256 for r in replay_records.green_records(reg, agent_id)}:
        problems.append(
            f"{where}: {path.name} names a replay record that {replay_records.FILE} does not hold "
            "as green for the current config"
        )
    return problems


def _file_thresholds(body: dict[str, Any]) -> tuple[Thresholds | None, str]:
    """The thresholds a promotion file was written under, and whether they are allowed: never weaker than the spec's
    unless the file records `weaker_allowed`."""
    raw = body.get("thresholds")
    keys = set(Thresholds.__dataclass_fields__)
    if not isinstance(raw, dict) or set(raw) != keys:
        return None, "does not record the thresholds it was written under"
    try:
        th = Thresholds(**raw)
    except TypeError:
        return None, "records malformed thresholds"
    spec = DEFAULTS
    weaker = (
        th.min_labelled < spec.min_labelled
        or th.min_agree < spec.min_agree
        or th.max_wrong_harmful > spec.max_wrong_harmful
        or th.harmful_window_days < spec.harmful_window_days
        or th.min_coverage < spec.min_coverage
        or th.min_labellers < spec.min_labellers
    )
    if weaker and body.get("weaker_allowed") is not True:
        return None, "was written under thresholds weaker than the spec's without saying so"
    return th, ""


@dataclass
class PromoteResult:
    ok: bool
    problems: list[str] = field(default_factory=list)
    path: Path | None = None
    numbers: Numbers | None = None
    refused: bool = (
        False  # not a shortfall: the question itself was invalid (unknown agent or action)
    )


# --- the measurement service -------------------------------------------------------------------------------


@dataclass
class LabelResult:
    ok: bool
    reason: str  # recorded, or why it was refused
    status: int = 200  # HTTP status for a channel callback: non-2xx only when the store failed
    demoted: bool = False


class Measure:
    """Everything K6 does at run time. Built by ``app.build`` and handed to the receiver, the tick steps and the CLI."""

    def __init__(
        self,
        store: Store,
        audit: AuditSink,
        registry: Registry,
        channel: Channel,
        *,
        ceiling: Ceiling | None = None,
        clock: Callable[[], datetime] = now,
        has_evidence: Callable[[str], bool] | None = None,
        policy: Policy = DEFAULT_POLICY,
        limits: Limits | None = None,
    ) -> None:
        self.limits = limits  # for the signed stop / reset; None: those clicks are ignored
        self.store, self.audit, self.registry, self.channel = store, audit, registry, channel
        self.ceiling, self.clock, self.policy = ceiling, clock, policy
        self.th = policy.thresholds()
        self._has_evidence = has_evidence

    # --- who and what --------------------------------------------------------------------------------------

    def _pairs(self) -> list[tuple[str, str]]:
        return [
            (a.id, x)
            for a in self.registry.agents.values()
            if a.status != "retired"
            for x in a.scope_allowed
        ]

    def line_owners(self) -> list[str]:
        """The people who hold ``clear_override``: they get the notices and the demotion cards."""
        return [
            p.id
            for p in self.registry.principals.values()
            if p.kind == "person" and "clear_override" in p.admin_rights
        ]

    def _audit(self, run_id: str, operation: str, principal: str, **kw: Any) -> None:
        """Write an audit outcome. Never raises: a sink that fails is a log line, so a committed label is never
        reported as failed and a receiver always answers."""
        team, action_ts = _CLICK.get()
        try:
            self.audit.write_outcome(
                AuditEvent(
                    run_id=run_id,
                    ts=self.clock(),
                    domain="measure",
                    operation=operation,
                    principal=principal,
                    source=self.channel.name,
                    team_id=team or None,
                    action_ts=action_ts or None,
                    **kw,
                )
            )
        except Exception as exc:  # noqa: BLE001
            _LOG.error("measure audit not written (%s)", type(exc).__name__)

    def _notify(self, text: str) -> int:
        """Tell every line owner; returns how many were reached. A failing channel is a log line, never an error
        in the rule that was just applied. Nobody to tell (no person holds ``clear_override``; ``build`` refuses
        that in pilot and prod) is logged loudly and returns 0."""
        owners = self.line_owners()
        if not owners:
            _LOG.error("measure notice has no recipient: no person holds clear_override")
        reached = 0
        for who in owners:
            try:
                self.channel.notify(who, text)
                reached += 1
            except Exception as exc:  # noqa: BLE001
                _LOG.warning("measure notice not delivered (%s)", type(exc).__name__)
        return reached

    # --- the level override the runtime reads --------------------------------------------------------------

    def level_override(self, agent_id: str, action_id: str) -> str | None:
        """``Hooks.level_override``: ``shadow`` for a demoted action, and ``shadow`` when the store cannot be
        read (the runtime only ever lowers a level with it)."""
        try:
            return "shadow" if (agent_id, action_id) in self.store.current_overrides() else None
        except Exception as exc:  # noqa: BLE001 - fail closed
            _LOG.warning("level override unreadable (%s): treated as shadow", type(exc).__name__)
            return "shadow"

    def hold_run_ids(self) -> set[str]:
        """``Hooks.hold_run_ids`` (K5): runs labelled wrong, harmful or missed. A demotion is always caused by such
        labels, so its runs are in this set too."""
        retention = getattr(
            self.registry.config, "retention", None
        )  # K5-core's retention config, when it exists
        if retention is not None and getattr(retention, "hold_labelled", True) is False:
            return set()
        return self.store.held_run_ids()

    # --- labels --------------------------------------------------------------------------------------------

    def _recent_wrongs(self, agent_id: str, action_id: str, extra: Label | None) -> list[Label]:
        """The runs that count as wrong inside the 14-day window, newest last (by insertion order, never by time:
        two labels can share an instant). A run is wrong when its latest ELIGIBLE label is wrong, or when any
        unapproved csv row says wrong (that label is not evidence, but an unapproved "agree" must not hide it:
        the safe direction). After an owner's clear these still count: a pattern of recent wrongs is not erased by
        a clear, so one new wrong re-demotes at once while two older ones remain in the window."""
        since = self.clock() - self.policy.wrong_window
        labels = self.store.list_labels_for(agent_id, action_id, since)
        if extra is not None:
            labels = [*labels, extra]
        by_run: dict[str, Label] = {
            r: x for r, x in latest_labels(labels).items() if x.label == "wrong"
        }
        for x in labels:
            seen = by_run.get(x.run_id)
            newer = seen is None or label_order(x) > label_order(seen)
            if not x.counts and x.label == "wrong" and newer:
                by_run[x.run_id] = x
        return sorted((x for x in by_run.values() if x.created_at >= since), key=label_order)

    def _wrong_episode(self, agent_id: str, action_id: str, extra: Label | None) -> str | None:
        """The key of a "3 wrong in 14 days" episode (the newest wrong label's id), or None."""
        wrongs = self._recent_wrongs(agent_id, action_id, extra)
        return wrongs[-1].label_id if len(wrongs) >= self.policy.wrong_limit else None

    def _pair_events(self, agent_id: str, action_id: str) -> list[LevelEvent]:
        return [
            e
            for e in self.store.list_level_events()
            if (e.agent_id, e.action_id) == (agent_id, action_id)
        ]

    def _uncleared(self, agent_id: str, action_id: str, kind: str) -> bool:
        """A demotion of this kind (`harmful`, `wrong_x3`, `ceiling`) exists since the action's last clear: a
        further label of that kind adds no second row, no second audit entry and no second card."""
        events = self._pair_events(agent_id, action_id)
        after_clear = events[
            max((i + 1 for i, e in enumerate(events) if e.kind == "clear"), default=0) :
        ]
        return any(e.kind == "demote" and e.reason.startswith(f"{kind}:") for e in after_clear)

    def _demotion_for(self, label: Label, agent_id: str, action_id: str) -> LevelEvent | None:
        """The demotion a label causes, or None. Keyed by the label row (a csv row by its import row, so the
        import and its later approval are ONE verdict): a harmful label after a clear is a new fact and demotes
        again; a second label of the same kind while a demotion of that kind is uncleared adds nothing."""
        if label.label == "harmful":
            kind, reason = "harmful", f"harmful:{_verdict_key(label.label_id)}"
        elif label.label == "wrong" and (key := self._wrong_episode(agent_id, action_id, label)):
            kind, reason = WRONGS_KIND, f"{WRONGS_KIND}:{key}"
        else:
            return None
        if self._has_event(agent_id, action_id, reason) or self._uncleared(
            agent_id, action_id, kind
        ):
            return None
        return LevelEvent(
            agent_id=agent_id,
            action_id=action_id,
            kind="demote",
            reason=reason,
            by=f"system:measure({label.principal_id})",
            at=label.created_at,
        )

    def _has_event(self, agent_id: str, action_id: str, reason: str) -> bool:
        return any(e.reason == reason for e in self._pair_events(agent_id, action_id))

    def _may_label(self, principal: Any, agent_id: str) -> bool:
        """A labeller is named per agent (`Principal.label_agents`, an agent id or "*"). Not stated: allowed in dev,
        refused in pilot and prod, where who may label is a decision someone wrote down."""
        allowed = principal.label_agents
        if allowed is None:
            from hadavin_sdk.deferred import LIVE

            return self.registry.config.environment not in LIVE
        return "*" in allowed or agent_id in allowed

    def _check(
        self, principal_id: str, run_id: str, label: str
    ) -> tuple[Plan | None, LabelResult | None]:
        """Who may label what: a known person allowed to label this agent, a known label, a run that exists, a
        label that fits the run (the four proposal labels need a plan, the two abstain labels none), and a proposal
        whose card was delivered. Returns (plan, None) or (None, refusal)."""
        principal = self.registry.principals.get(principal_id)
        if principal is None or principal.kind != "person":
            return None, LabelResult(False, "unknown_principal")
        if label not in LABELS:
            return None, LabelResult(False, "unknown_label")
        if not _ID.fullmatch(run_id):
            return None, LabelResult(False, "unknown_run")
        try:
            run = self.store.get_run(run_id)
        except NotFound:
            return None, LabelResult(False, "unknown_run")
        except Exception:  # noqa: BLE001 - store down: nothing changes
            return None, LabelResult(False, "store_unavailable", 503)
        try:
            plan: Plan | None = self.store.get_plan(run_id)
        except NotFound:
            plan = None
        except Exception:  # noqa: BLE001
            return None, LabelResult(False, "store_unavailable", 503)
        if (plan is None) != (label in ABSTAIN_LABELS):
            return None, LabelResult(False, "label_does_not_fit_run")
        if not self._may_label(principal, run.agent_id):
            return None, LabelResult(False, "not_a_labeller_for_this_agent")
        if plan is not None and run.reason_code == "shadow_undelivered":
            return None, LabelResult(False, "card_not_delivered")  # nobody was shown this proposal
        return plan, None

    def _may_lower_harmful(self, principal_id: str) -> bool:
        p = self.registry.principals.get(principal_id)
        return p is not None and p.kind == "person" and "clear_override" in p.admin_rights

    def _latest_is_harmful(self, run_id: str) -> bool:
        """The run's LATEST eligible label is harmful (a lowered verdict leaves the run free again)."""
        cur = latest_labels(self.store.list_labels(run_id)).get(run_id)
        return cur is not None and cur.label == "harmful"

    def _new_label(
        self, principal_id: str, run_id: str, label: str, channel: str, approved_by, label_id
    ) -> Label:
        return Label(
            run_id=run_id,
            label=label,  # type: ignore[arg-type]  # checked by _check
            principal_id=principal_id,
            channel=channel,  # type: ignore[arg-type]
            approved_by=approved_by,
            created_at=self.clock(),
            **({"label_id": label_id} if label_id else {}),
        )

    def record_label(
        self,
        principal_id: str,
        run_id: str,
        label: str,
        *,
        channel: str = "chat",
        approved_by: str | None = None,
        label_id: str | None = None,
    ) -> LabelResult:
        """Validate, decide the demotion, store label and demotion (and the sticky-harmful check) in one
        transaction, then audit. Never raises.

        TRUST: ``principal_id`` is taken as given. This is an in-process method with no caller authentication; the
        only production caller passes the user of a signature-verified channel click (``handle_action``), and a repo
        test confines every other caller (the dev-only CLI import). A new caller must pass a verified identity."""
        plan, refusal = self._check(principal_id, run_id, label)
        if refusal is not None:
            return refusal
        may = self._may_lower_harmful(principal_id)
        try:
            prev = latest_labels(self.store.list_labels(run_id)).get(run_id)
            new = self._new_label(principal_id, run_id, label, channel, approved_by, label_id)
            demote = self._demotion_for(new, plan.agent_id, plan.action_id) if plan else None
            # The sticky check runs inside the store's transaction, serialised per run: two clicks cannot both pass.
            inserted = self.store.add_labels([(new, demote)], may_lower_harmful=may)
        except HarmfulSticky:
            self._audit(
                run_id, "label", principal_id, decision=label, result="refused",
                error_code="harmful_is_sticky",
            )  # fmt: skip
            return LabelResult(False, "harmful_is_sticky")
        except StaleState:
            return LabelResult(False, "duplicate")
        except Exception as exc:  # noqa: BLE001 - the label is refused, nothing was stored
            _LOG.error("label refused: store error %s", type(exc).__name__)
            return LabelResult(False, "store_unavailable", 503)
        self._after_commit(new, demote if inserted else None, prev)
        if new.label in ("wrong", "harmful"):
            self._safe_enforce()  # the ceiling and the wrong rule are checked now, not at the next tick
        return LabelResult(True, "recorded", demoted=bool(inserted))

    def _after_commit(
        self, new: Label, demote: LevelEvent | None, prev: Label | None = None
    ) -> None:
        """Audit and tell about what is already committed. Never raises: the label stands whatever the sink or the
        channel does. A verdict of wrong or harmful that is replaced by something milder is audited with who and when,
        and the line owners are told at once (the weekly report lists them too)."""
        self._audit(
            new.run_id,
            "label",
            new.principal_id,
            object_ref=new.label_id,
            decision=new.label,
            result="recorded",
            caught_by="human_label" if new.label in ("wrong", "harmful") else None,
        )
        if (
            prev is not None
            and prev.label in ("wrong", "harmful")
            and new.label not in ("wrong", "harmful")
        ):
            self._audit(
                new.run_id,
                "label_downgraded",
                new.principal_id,
                object_ref=new.label_id,
                decision=new.label,
                result=prev.label,
            )
            if prev.label == "harmful":
                self._audit(
                    new.run_id,
                    "harmful_lowered",
                    new.principal_id,
                    object_ref=new.label_id,
                    decision=new.label,
                )
            self._notify(
                f"{new.principal_id} changed run {new.run_id} from {prev.label} to {new.label}"
                + (
                    " (a harmful verdict leaves the ceiling count)."
                    if prev.label == "harmful"
                    else "."
                )
            )
        if demote is not None:
            self._audit_demotion(demote)
            self._announce_pending()

    def _audit_demotion(self, ev: LevelEvent) -> None:
        self._audit(
            "-", "demote", ev.by, object_ref=f"{ev.agent_id}.{ev.action_id}", result=ev.reason
        )

    def _announce_pending(self) -> None:
        """Tell the line owner about every demotion row and every ceiling breach not yet delivered, and record each
        delivery. Inserting a row and announcing it are separate facts: an undelivered card or notice is tried again
        on the next pass (every `enforce_every_s`), not lost. Never raises."""
        from hadavin_sdk.approvals.cards import render_demotion

        try:
            events = self.store.list_level_events()
            status = self.ceiling_status()
        except Exception as exc:  # noqa: BLE001
            _LOG.warning("announcements skipped (%s)", type(exc).__name__)
            return
        for ev in events:
            if ev.kind != "demote" or ev.reason.startswith("ceiling:"):
                continue
            key = f"demote/{ev.agent_id}/{ev.action_id}/{ev.reason}"
            try:
                if self.store.is_announced(key):
                    continue
                card = render_demotion(
                    ev.agent_id,
                    ev.action_id,
                    ev.reason,
                    self._wrongs_note(ev.agent_id, ev.action_id),
                    ev.seq,
                )
                ok = self.channel.post_card(card).ok or (
                    self._notify(
                        f"{ev.agent_id}.{ev.action_id} was demoted to shadow ({ev.reason})."
                    )
                    > 0
                )
                if ok:
                    self.store.mark_announced(key, self.clock())
            except Exception as exc:  # noqa: BLE001
                _LOG.warning("demotion card not delivered (%s)", type(exc).__name__)
        # One notice per breach (its reason is the newest counted label's time), however many rows it demoted.
        if status and status.breached and status.latest_harmful_at is not None:
            reason = _ceiling_reason(status.latest_harmful_at)
            key = f"breach/{reason}"
            try:
                if not self.store.is_announced(key):
                    c = status
                    rows = any(e.reason == reason for e in events)
                    reached = self._notify(
                        f"Ceiling breached: {c.harmful} of {c.labelled} labelled in the last "
                        f"{c.ceiling.window_days} days counts against it ({', '.join(c.ceiling.counts)}; max "
                        f"{c.ceiling.max}). "
                        + ("Every action at suggest is shadow. " if rows else "")
                        + "Promotion is blocked until the window clears or the sponsor changes the ceiling in writing."
                    )
                    if reached:
                        self.store.mark_announced(key, self.clock())
            except Exception as exc:  # noqa: BLE001
                _LOG.warning("breach notice not delivered (%s)", type(exc).__name__)

    def _wrongs_note(self, agent_id: str, action_id: str) -> str | None:
        """ "Recent wrongs still count until <date>": after a clear, one new wrong re-demotes at once while two older
        wrongs remain in the 14-day window, which lasts until the second-newest of them ages out."""
        try:
            wrongs = self._recent_wrongs(agent_id, action_id, None)
        except Exception:  # noqa: BLE001 - a note is never worth a failure
            return None
        need = self.policy.wrong_limit - 1  # older wrongs that, with one new one, re-demote
        if need < 1 or len(wrongs) < need:
            return None
        until = wrongs[-need].created_at + self.policy.wrong_window
        return (
            f"Recent wrongs still count until {until:%Y-%m-%d} UTC: clearing this does not erase them, so one "
            "new wrong before then demotes it again."
        )

    # --- signed channel clicks -----------------------------------------------------------------------------

    def handle_action(self, action: Action) -> tuple[int, str]:
        """A verified click that ``is_ours``: (HTTP status, reason). The user comes from the signed request."""
        parsed = parse_action_value(action.value)
        if parsed is None:
            return 200, "malformed"
        token = _CLICK.set((action.team, action.action_ts))
        try:
            return self._handle(action, parsed)
        finally:
            _CLICK.reset(token)

    def _handle(self, action: Action, parsed: ParsedAction) -> tuple[int, str]:
        team = self.policy.allowed_team_id
        if team and action.team != team:
            self._audit("-", parsed.kind, action.user, result="refused", error_code="wrong_team")
            return 200, "wrong_team"
        claimed = False
        if action.nonce:
            # A signed request is good for 5 minutes, so a captured copy would replay. Each delivery is acted on once.
            # The workspace id and the click's own timestamp are stored with the nonce.
            try:
                claimed = self.store.claim_action(
                    action.nonce, self.clock(), action.team, action.action_ts
                )
            except Exception as exc:  # noqa: BLE001
                _LOG.error("click refused: store error %s", type(exc).__name__)
                return 503, "store_unavailable"
            if not claimed:
                self._audit("-", parsed.kind, action.user, result="refused", error_code="replay")
                return 200, "replay"
        try:
            status, reason = self._dispatch(action.user, parsed)
        except Exception:
            self._release(action.nonce if claimed else "")
            raise
        if status >= 500 and claimed:
            self._release(
                action.nonce
            )  # it did not take effect: the same signed request may be delivered again
        return status, reason

    def _release(self, nonce: str) -> None:
        if not nonce:
            return
        try:
            self.store.release_action(nonce)
        except Exception as exc:  # noqa: BLE001 - the click stays spent; a new click works
            _LOG.error("nonce not released (%s)", type(exc).__name__)

    def _dispatch(self, user: str, parsed: ParsedAction) -> tuple[int, str]:
        if parsed.kind == "label":
            res = self.record_label(user, *parsed.args)
            return res.status, res.reason
        if parsed.kind in ("stop", "reset"):
            return self.kill_switch(user, parsed.kind)
        if parsed.kind == "approve_import":
            return self.approve_import(user, parsed.args[0])
        agent_id, action_id, seq = parsed.args
        return self.clear(user, agent_id, action_id, int(seq))

    def purge_seen(self, at: datetime | None = None) -> int:
        """Delete click nonces older than twice the signature window: they can never be replayed (the signature
        itself would be refused), and the table would otherwise grow forever. Also gives back a stuck claim."""
        at = at or self.clock()
        return self.store.purge_actions(at - timedelta(seconds=self.policy.seen_actions_keep_s))

    def approve_import(self, principal_id: str, import_id: str) -> tuple[int, str]:
        """A line owner approves a pending csv import (a signed click). Nobody approves their own import. The rows
        are appended again as approved ones in ONE transaction (``labels`` has no UPDATE): if any row is refused
        nothing is approved, the import stays pending, and the reason says which row and why."""
        if not self._admin(principal_id, "approve_label_import", "approve_import"):
            return 200, "not_authorised"
        try:
            pending = [
                x for x in self.store.list_csv_import(import_id) if x.label_id.endswith("-p")
            ]
        except Exception as exc:  # noqa: BLE001
            _LOG.error("approve_import refused: store error %s", type(exc).__name__)
            return 503, "store_unavailable"
        if not pending:
            return 200, "unknown_import"
        if any(x.principal_id == principal_id for x in pending):
            self._audit(
                "-", "approve_import", principal_id, result="refused", error_code="own_import"
            )
            return 200, "cannot_approve_own_import"
        author = pending[0].principal_id
        items, problems = [], []
        for i, x in enumerate(pending, 1):
            plan, refusal = self._check(x.principal_id, x.run_id, x.label)
            if refusal is None and self._sticky_blocked(x.principal_id, x.run_id, x.label):
                refusal = LabelResult(False, "harmful_is_sticky")
            if refusal is not None:
                problems.append(f"row {i}: {refusal.reason}")
                continue
            new = self._new_label(
                x.principal_id, x.run_id, x.label, "csv", principal_id, x.label_id[:-1] + "a"
            )
            items.append(
                (new, self._demotion_for(new, plan.agent_id, plan.action_id) if plan else None)
            )
        if problems:
            self._audit(
                "-", "approve_import", principal_id, object_ref=import_id, result="refused",
                error_code="; ".join(problems)[:200],
            )  # fmt: skip
            return 200, "refused: " + "; ".join(problems)
        try:
            inserted = self.store.add_labels(
                items, may_lower_harmful=self._may_lower_harmful(author)
            )
        except HarmfulSticky:
            return 200, "refused: harmful_is_sticky"
        except StaleState:
            return 200, "already_approved"
        except Exception as exc:  # noqa: BLE001
            _LOG.error("approve_import refused: store error %s", type(exc).__name__)
            return 503, "store_unavailable"
        for new, demote in items:
            self._after_commit(new, demote if demote in inserted else None)
        self._audit(
            "-",
            "approve_import",
            principal_id,
            object_ref=import_id,
            result=f"approved:{len(items)}",
        )
        self._safe_enforce()
        return 200, f"approved:{len(items)}"

    def _sticky_blocked(self, principal_id: str, run_id: str, label: str) -> bool:
        """Would this label lower a harmful verdict that its author may not lower?"""
        return (
            label != "harmful"
            and not self._may_lower_harmful(principal_id)
            and self._latest_is_harmful(run_id)
        )

    def _safe_enforce(self) -> None:
        """Re-check the demotion rules after a batch (a batch can complete a 3-wrong episode no row saw)."""
        try:
            self.enforce()
        except Exception as exc:  # noqa: BLE001 - the tick step is the backstop
            _LOG.warning("enforce after a batch failed (%s)", type(exc).__name__)

    def _admin(self, principal_id: str, right: str, operation: str) -> bool:
        """True when the person holds the admin right; a refusal is audited."""
        principal = self.registry.principals.get(principal_id)
        if principal is not None and principal.kind == "person" and right in principal.admin_rights:
            return True
        self._audit("-", operation, principal_id, result="refused", error_code="not_authorised")
        return False

    def kill_switch(self, principal_id: str, which: str) -> tuple[int, str]:
        """A signed ``stop`` or ``reset`` of the kill switch; needs that admin right. ``Limits`` audits it."""
        from hadavin_sdk.audit.protocol import AuditUnavailable

        if self.limits is None:
            return 200, "no_limits"
        if not self._admin(principal_id, which, which):
            return 200, "not_authorised"
        try:
            (self.limits.stop if which == "stop" else self.limits.reset)(principal_id)
        except AuditUnavailable:
            return 503, "audit_unavailable"  # a reset that cannot be recorded does not happen
        except Exception as exc:  # noqa: BLE001
            _LOG.error("%s refused: store error %s", which, type(exc).__name__)
            return 503, "store_unavailable"
        return 200, which

    def _clear_blocked(self, agent_id: str, action_id: str, events: list[LevelEvent]) -> str | None:
        """Why a demotion may not be lifted now, or None. While the ceiling is breached, an action whose demotion
        since its last clear includes a `ceiling:` one stays down, whatever demoted it afterwards (the breach notice
        says every action is shadow, and that must stay true). An action configured at ``suggest`` also needs the
        section 6.1 numbers to hold again, derived from the store now."""
        status = self.ceiling_status()
        breached = bool(status and status.breached)
        if breached and self._uncleared_in(events, "ceiling"):
            return "ceiling_breached"
        agent = self.registry.agents.get(agent_id)
        if agent is not None and (agent.levels or {}).get(action_id) == "suggest":
            if breached:
                return "ceiling_breached"
            fresh = self._evidence_numbers(agent_id, action_id, self.clock())
            if shortfalls(fresh.as_dict(), self.th):
                return "evidence_below_6_1"
        return None

    @staticmethod
    def _uncleared_in(events: list[LevelEvent], kind: str) -> bool:
        after_clear = events[
            max((i + 1 for i, e in enumerate(events) if e.kind == "clear"), default=0) :
        ]
        return any(e.kind == "demote" and e.reason.startswith(f"{kind}:") for e in after_clear)

    def clear(
        self, principal_id: str, agent_id: str, action_id: str, expect_seq: int | None = None
    ) -> tuple[int, str]:
        """A line owner lifts a demotion. Needs the ``clear_override`` admin right. The button names the demotion it
        was posted for (`expect_seq`): a click on an older card is stale. A harmful demotion is cleared by someone
        other than the person whose label caused it. Every clear is told to the line owners."""
        if not self._admin(principal_id, "clear_override", "clear"):
            return 200, "not_authorised"
        try:
            # Look, decide, then write only if nothing changed since we looked (compare-and-set on the newest
            # level event): a demotion that lands between the check and the write must not be cleared unseen.
            events = self._pair_events(agent_id, action_id)
            if not events or events[-1].kind != "demote":
                return 200, "not_demoted"
            if expect_seq is not None and events[-1].seq != expect_seq:
                return self._refuse_clear(principal_id, agent_id, action_id, "stale_button")
            why = (
                self._clear_blocked(agent_id, action_id, events)
                or self._same_person(principal_id, events[-1])
                or self._too_soon(events[-1])
            )
            if why:
                return self._refuse_clear(principal_id, agent_id, action_id, why)
            lifted = LevelEvent(
                agent_id=agent_id,
                action_id=action_id,
                kind="clear",
                reason="line_owner_clear",
                by=principal_id,
                at=self.clock(),
            )
            if not self.store.clear_demotion(lifted, events[-1].seq or 0):
                return self._refuse_clear(principal_id, agent_id, action_id, "changed_meanwhile")
        except Exception as exc:  # noqa: BLE001
            _LOG.error("clear refused: store error %s", type(exc).__name__)
            return 503, "store_unavailable"
        self._audit(
            "-", "clear", principal_id, object_ref=f"{agent_id}.{action_id}", result="cleared"
        )
        self._notify(f"{principal_id} cleared the demotion of {agent_id}.{action_id}.")
        return 200, "cleared"

    def _refuse_clear(
        self, principal_id: str, agent_id: str, action_id: str, why: str
    ) -> tuple[int, str]:
        self._audit(
            "-",
            "clear",
            principal_id,
            object_ref=f"{agent_id}.{action_id}",
            result="refused",
            error_code=why,
        )
        return 200, why

    @staticmethod
    def _same_person(principal_id: str, last: LevelEvent) -> str | None:
        """A demotion caused by a harmful label is not cleared by the person who gave that label."""
        if last.reason.startswith("harmful:") and last.by == f"system:measure({principal_id})":
            return "second_person_needed"
        return None

    def _too_soon(self, last: LevelEvent) -> str | None:
        """A harmful demotion stays at least ``policy.harmful_clear_min_age_h`` hours, whoever clicks."""
        hours = self.policy.harmful_clear_min_age_h
        if (
            hours
            and last.reason.startswith("harmful:")
            and self.clock() - last.at < timedelta(hours=hours)
        ):
            return "too_soon"
        return None

    # --- csv import ----------------------------------------------------------------------------------------

    def import_csv(
        self, text: str, by: str, approved_by: str | None = None
    ) -> tuple[int, list[str]]:
        """Record labels from a csv with the columns ``run_id,label``, ALL or NOTHING: every row is checked first
        (including the sticky-harmful rule) and the whole import is one transaction. Rows are ``channel = 'csv'``
        and count as evidence only once approved (``approved_by``, or a signed approval). Returns (rows stored,
        problems)."""
        if approved_by is not None:
            approver = self.registry.principals.get(approved_by)
            if (
                approver is None
                or approver.kind != "person"
                or "approve_label_import" not in approver.admin_rights
            ):
                return 0, [f"{approved_by} does not hold the approve_label_import admin right"]
            if approved_by.casefold() == by.casefold():
                return 0, ["an import cannot be approved by the person who made it"]
        text = text.removeprefix(
            "\ufeff"
        )  # a spreadsheet's UTF-8 byte order mark is not part of the header
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None or set(reader.fieldnames) != {"run_id", "label"}:
            return 0, ["the csv header must be exactly: run_id,label"]
        # A short row leaves the missing field None: it becomes a refused row, not a crash.
        rows = [((r["run_id"] or "").strip(), (r["label"] or "").strip()) for r in reader]
        sha = csv_import_id(text)
        tag = "a" if approved_by else "p"
        items, problems = [], []
        for i, (run_id, label) in enumerate(rows, 1):
            plan, refusal = self._check(by, run_id, label)
            if refusal is None and self._sticky_blocked(by, run_id, label):
                refusal = LabelResult(False, "harmful_is_sticky")
            if refusal is not None:
                problems.append(f"row {i}: {refusal.reason}")
                continue
            new = self._new_label(by, run_id, label, "csv", approved_by, f"csv-{sha}-{i}-{tag}")
            items.append(
                (new, self._demotion_for(new, plan.agent_id, plan.action_id) if plan else None)
            )
        if problems or not rows:
            return 0, problems or ["the csv has no rows"]
        try:
            inserted = self.store.add_labels(items, may_lower_harmful=self._may_lower_harmful(by))
        except HarmfulSticky:
            return 0, ["harmful_is_sticky"]
        except StaleState:
            return 0, []  # the same file again: already stored
        except Exception as exc:  # noqa: BLE001
            _LOG.error("import refused: store error %s", type(exc).__name__)
            return 0, ["store_unavailable"]
        for new, demote in items:
            self._after_commit(new, demote if demote in inserted else None)
        if approved_by is None:
            self._announce_import(sha, len(items))
        self._safe_enforce()
        return len(items), []

    def note_cli_import(
        self, by: str, approved_by: str | None, os_user: str, import_id: str
    ) -> None:
        """Audit a dev-only CLI import with the operating-system user who ran it (the names are asserted)."""
        self._audit(
            "-",
            "cli_import",
            by,
            object_ref=import_id,
            decision=approved_by,
            result=f"os_user:{os_user}",
        )

    def _announce_import(self, import_id: str, n: int) -> None:
        """Post the card whose button is the line owner's signed approval of this import."""
        from hadavin_sdk.approvals.cards import render_import

        try:
            self.channel.post_card(render_import(import_id, n))
        except Exception as exc:  # noqa: BLE001
            _LOG.warning("import card not delivered (%s)", type(exc).__name__)

    # --- enforcement (tick) --------------------------------------------------------------------------------

    def ceiling_status(self, at: datetime | None = None) -> CeilingStatus | None:
        """X harmful of Y labelled in the rolling window, or None without a ceiling (dev only)."""
        if self.ceiling is None:
            return None
        at = at or self.clock()
        since = at - timedelta(days=self.ceiling.window_days)
        # Every label in the window, whatever agent or action it was for: a retired agent or a dropped action
        # does not make its harmful labels disappear from the ceiling.
        labels = self.store.list_labels_between(since, at + timedelta(seconds=1))
        # The latest eligible label of each run; the classes in `ceiling.counts` count against the ceiling.
        mine = [x for x in latest_labels(labels).values() if x.created_at >= since]
        harmful = sorted(
            (x for x in mine if x.label in self.ceiling.counts), key=lambda x: x.created_at
        )
        breached = len(harmful) > self.ceiling.max
        return CeilingStatus(
            self.ceiling,
            len(harmful),
            len(mine),
            breached,
            harmful[-1].created_at if breached else None,
        )

    def _at_suggest(self) -> list[tuple[str, str]]:
        """The (agent, action) pairs configured at suggest: the only ones a ceiling breach has anything to demote.
        A shadow-only pilot breaches the ceiling without writing a single demotion row."""
        return [
            (a.id, x)
            for a in self.registry.agents.values()
            if a.status != "retired"
            for x, level in (a.levels or {}).items()
            if level == "suggest"
        ]

    def enforce(self, at: datetime | None = None) -> list[LevelEvent]:
        """Idempotent and safe to run twice at once: re-check the wrong rule (two simultaneous labels can each miss
        the limit) and the ceiling, insert the demotions that are missing, then (re)try every announcement not yet
        delivered. What was really inserted (the store says; a demotion that already exists is a no-op) is what gets
        audited and returned."""
        at = at or self.clock()
        wanted: list[LevelEvent] = []
        for agent_id, action_id in self._pairs():
            key = self._wrong_episode(agent_id, action_id, None)
            reason = f"{WRONGS_KIND}:{key}"
            if key and not self._uncleared(agent_id, action_id, WRONGS_KIND):
                wanted.append(self._level(agent_id, action_id, reason, at))
        status = self.ceiling_status(at)
        ceiling_events: list[LevelEvent] = []
        if status and status.breached and status.latest_harmful_at is not None:
            reason = _ceiling_reason(status.latest_harmful_at)
            ceiling_events = [self._level(a, x, reason, at) for a, x in self._at_suggest()]
        added: list[LevelEvent] = []
        for ev in [*wanted, *ceiling_events]:
            if self.store.add_level_event(ev):
                added.append(ev)
                self._audit_demotion(ev)
        self._announce_pending()
        return added

    @staticmethod
    def _level(agent_id: str, action_id: str, reason: str, at: datetime) -> LevelEvent:
        return LevelEvent(
            agent_id=agent_id,
            action_id=action_id,
            kind="demote",
            reason=reason,
            by="system:measure",
            at=at,
        )

    # --- promotion -----------------------------------------------------------------------------------------

    def promote_check(
        self, agent_id: str, action_id: str, at: datetime | None = None
    ) -> PromoteResult:
        """Compute the §6.1 numbers from the store and write ``promotions/<agent>.<action>.json`` when every one is
        met. On any shortfall nothing is written."""
        from hadavin_sdk.k1b.atomic import atomic_write

        reg, at = self.registry, at or self.clock()
        if agent_id not in reg.agents or action_id not in reg.agents[agent_id].scope_allowed:
            return PromoteResult(
                False, [f"{agent_id}.{action_id} is not an action of a known agent"], refused=True
            )
        if self.ceiling is None:
            raise ConfigError(
                f"{BASELINE_FILE} is required: the ceiling blocks promotion when breached"
            )
        problems: list[str] = []
        contract = reg.contracts.get(action_id)
        if contract is not None and contract.executor.kind == "none":
            problems.append("the action is a none contract and can never be suggest (R1)")
        if (agent_id, action_id) in self.store.current_overrides():
            problems.append("the action is demoted: a line owner's clear is needed first")
        nm = self._evidence_numbers(agent_id, action_id, at)
        problems += shortfalls(nm.as_dict(), self.th)
        record = replay_records.green_record(reg, agent_id)
        if record is None:
            problems.append(
                f"no green replay record (k >= {replay_records.MIN_K}) in {replay_records.FILE} for the current config hash, "
                "model and prompt"
            )
        status = self.ceiling_status(at)
        if status and status.breached:
            problems.append(
                f"ceiling breached: {status.harmful} harmful of {status.labelled} in the last "
                f"{status.ceiling.window_days} days (max {status.ceiling.max})"
            )
        if problems or record is None or status is None:
            return PromoteResult(False, problems, None, nm)
        agent = reg.agents[agent_id]
        body: dict[str, Any] = {
            "schema_version": 1,
            "agent_id": agent_id,
            "action_id": action_id,
            "config_hash": reg.config_hash(agent_id),
            "model_id": reg.config.routes[agent.model_route].model_id,
            "prompt_sha256": reg.prompt_sha256(agent_id),
            "generated_at": at.astimezone(UTC).isoformat(timespec="seconds"),
            "numbers": nm.as_dict(),
            "thresholds": {k: getattr(self.th, k) for k in self.th.__dataclass_fields__},
            "weaker_allowed": self.policy.allow_weaker_than_spec,
            "policy": asdict(self.policy),
            "replay_record": {
                "bundle_sha256": record.bundle_sha256,
                "k": record.k,
                "pass_k": record.pass_k,
                "ts": record.ts.astimezone(UTC).isoformat(timespec="seconds"),
            },
            "ceiling": {"harmful": status.harmful, "labelled": status.labelled, "breached": False},
        }
        body["sha256"] = _file_sha(body)
        path = promotion_path(reg.config.root, agent_id, action_id)
        path.parent.mkdir(exist_ok=True)
        atomic_write(path, _json(body) + "\n")
        return PromoteResult(True, [], path, nm)

    def _evidence_numbers(self, agent_id: str, action_id: str, at: datetime) -> Numbers:
        """The §6.1 numbers for one action, from proposals made under the agent's CURRENT config hash only: labels
        on an older prompt or model say nothing about this one."""
        h = self.registry.config_hash(agent_id)
        return numbers_for(
            self.store.list_labels_for(agent_id, action_id, None, h),
            self.store.count_proposals(agent_id, action_id, None, h),
            at,
            self.th,
        )

    def promotion_store_problems(self) -> list[str]:
        """Start-up check for every action configured at ``suggest``: its promotion file must load, and the numbers
        derived again from the store must still meet §6.1 (a re-sealed file with invented numbers fails here)."""
        out: list[str] = []
        # A demoted action is checked too: the config still says suggest, and a clear (or a PR that removes the
        # demotion's cause) would lift it again. The config must not claim a level the evidence no longer supports.
        for agent in self.registry.agents.values():
            for action, level in (agent.levels or {}).items():
                if level != "suggest":
                    continue
                out += promotion_problems(self.registry, agent.id, action)
                where = f"agent {agent.id}: suggest for {action}"
                # The store leg re-checks what the file only claims: the replay leg, the ceiling, and that the file
                # was not written under looser thresholds than the policy now in force.
                if replay_records.green_record(self.registry, agent.id) is None:
                    out.append(f"{where}: no green replay record for the current config")
                status = self.ceiling_status()
                if status and status.breached:
                    out.append(f"{where}: the ceiling is breached now")
                body = _read_promotion(self.registry, agent.id, action)
                file_th, _why = _file_thresholds(body) if body else (None, "")
                if file_th is not None and _weaker_than(file_th, self.th):
                    out.append(
                        f"{where}: the file was written under looser thresholds than the policy in force"
                    )
                fresh = self._evidence_numbers(agent.id, action, self.clock())
                out += [
                    f"agent {agent.id}: suggest for {action}: the store now says {s}"
                    for s in shortfalls(fresh.as_dict(), self.th)
                ]
        return out

    # --- golden candidates and holds -----------------------------------------------------------------------

    def _evidence(self, run_id: str) -> bool:
        if self._has_evidence is not None:
            return self._has_evidence(run_id)
        lister = getattr(self.store, "list_tool_calls", None)  # K5-core; before it, nothing is held
        return bool(lister and lister(run_id))

    def golden_candidates(self, start: datetime, end: datetime) -> list[str]:
        """Runs labelled wrong or missed in [start, end) whose evidence is held (K5): what `golden add --from-label`
        can turn into a golden item."""
        seen: dict[str, None] = {}
        for lab in latest_labels(self.store.list_labels_between(start, end)).values():
            if lab.label in ("wrong", "missed") and self._evidence(lab.run_id):
                seen[lab.run_id] = None
        return list(seen)

    # --- the weekly report ---------------------------------------------------------------------------------

    def weekly_report(self, at: datetime | None = None) -> str | None:
        """Write and announce the report for the last complete ISO week when there is none yet. Returns the body
        when this call wrote it. Two ticks that overlap announce once: the week is claimed first (a row in the
        click-nonce table, which expires and is purged), the line owner is told, the report is stored, and the
        claim is given back; if the owner cannot be told the claim is given back too and the next tick retries."""
        if self.ceiling is None:
            return None  # dev without baseline.yaml: nothing to report against
        at = at or self.clock()
        week = week_start(at) - timedelta(days=7)
        if self.store.get_report(week) is not None:
            return None
        claim = f"report/{week.isoformat()}"
        if not self.store.claim_action(claim, at):
            return None  # another tick is announcing this week (or crashed: the claim expires and is purged)
        try:
            if self.store.get_report(week) is not None:  # finished between our check and our claim
                return None
            body = self.render_report(week, at)
            if self._notify(_summary(week, body)) == 0:
                raise RuntimeError("weekly report not announced: no line owner could be reached")
            return body if self.store.put_report(week, body) else None
        finally:
            self._release(claim)

    def render_report(self, week: date, at: datetime | None = None) -> str:
        at = at or self.clock()
        start = datetime(week.year, week.month, week.day, tzinfo=UTC)
        end = start + timedelta(days=7)
        pw, prev = self.store.pilot_week(week), self.store.pilot_week(week - timedelta(days=7))
        aw = self.store.approval_week(week)
        local = at.astimezone(self.policy.local_tz)
        out = [
            f"# Pilot report: week of {week.isoformat()} (Monday, UTC)",
            "",
            (
                f"Generated {at.astimezone(UTC):%Y-%m-%d %H:%M} UTC / {local:%Y-%m-%d %H:%M} {self.policy.report_local_label}. Every number is counted "
                "from the client's own runs and labels; a week with no labels says so."
            ),
            "",
            "## Counts",
            (
                f"- Runs: {pw.runs}. Proposals: {pw.proposals}. Shadow cards: {pw.shadow_cards}. "
                f"Cards not delivered: {pw.cards_not_delivered}."
            ),
            f"- Abstained: {pw.abstained}. Fixes verified: {pw.fixes_verified}.",
            (
                f"- Median time to a proposal: {_secs(pw.median_s_to_proposal)}. "
                f"Average cost per run: {_usd(pw.avg_cost_usd)}."
            ),
            "",
            "## Labels and the two error rates (never blended)",
        ]
        labelled = pw.agree + pw.partial + pw.wrong + pw.harmful
        out += [
            (
                f"- Proposals labelled: {labelled} of {pw.proposals}: agree {pw.agree}, partial {pw.partial}, "
                f"wrong {pw.wrong}, harmful {pw.harmful}."
            ),
            f"- Wrong rate on proposals: {_rate(pw.wrong + pw.harmful, labelled)}.",
            (
                f"- Miss rate on abstentions: {_rate(pw.missed, pw.missed + pw.abstain_ok)} "
                f"(abstentions labelled: fine {pw.abstain_ok}, should have answered {pw.missed})."
            ),
        ]
        if pw.proposals and labelled / pw.proposals < self.th.min_coverage:
            out.append(
                f"- FLAG: label coverage {labelled / pw.proposals:.0%} is below {self.th.min_coverage:.0%}."
            )
        if pw.wrong - prev.wrong >= self.policy.wrong_rise_flag_min:
            out.append(f"- FLAG: wrong labels rose from {prev.wrong} to {pw.wrong}.")
        out += ["", "## Per action (all time): n and the 95 % upper bound"]
        for agent_id, action_id in self._pairs():
            nm = numbers_for(
                self.store.list_labels_for(agent_id, action_id, None),
                self.store.count_proposals(agent_id, action_id, None),
                at,
                self.th,
            )
            bound = "n/a" if nm.upper_bound is None else f"{nm.upper_bound:.1%}"
            out.append(
                f"- {agent_id}.{action_id}: labelled n={nm.labelled}, wrong + harmful "
                f"{nm.wrong + nm.harmful}, upper bound on the wrong rate {bound}; "
                f"coverage {nm.coverage:.0%}, agree {nm.agree_rate:.0%}; labelled by {nm.labellers} "
                f"people, the busiest gave {nm.top_labeller_share:.0%} of the labels."
            )
        out += ["", "## Every wrong and harmful label this week"]
        labels = [
            x
            for x in latest_labels(self.store.list_labels_between(start, end)).values()
            if x.label in ("wrong", "harmful")
        ]  # eligible and latest per run, like every other number here
        out += [f"- {x.run_id}: {x.label} (by {x.principal_id}, {x.channel})" for x in labels] or [
            "- none"
        ]
        out += ["", "## Caught, and by what"]
        events: list[AuditEvent] = []
        audit_ok = False
        try:
            # Events that could not be written when they happened wait in the audit's outbox; bring them into the
            # log first so the counts below do not miss them.
            self.audit.reconcile()
            events = self.audit.events()
            audit_ok = True
            counts = caught_week(events, week)
            out += [f"- {k}: {v}" for k, v in sorted(counts.items())] or ["- nothing was caught"]
        except Exception as exc:  # noqa: BLE001
            out.append(f"- the audit could not be read ({type(exc).__name__})")
        out.append(
            f'- Approvals decided: {aw.decisions}, "won\'t run": {aw.wont_run}, median {_secs(aw.median_s)}.'
        )
        out += ["", "## Ceiling"]
        status = self.ceiling_status(
            min(at, end)
        )  # as it stood when the week ended, not when this was run
        lowered = [e for e in events if e.operation == "harmful_lowered"]
        if audit_ok:
            out.append(
                f"- harmful verdicts lowered by a line owner: {sum(iso_week(e.ts) == week for e in lowered)} this "
                f"week, {len(lowered)} in all. A lowered verdict leaves the ceiling count, so each one is listed:"
            )
            out += [
                f"  - {e.run_id}: lowered to {e.decision} by {e.principal} at {e.ts:%Y-%m-%d %H:%M} UTC"
                for e in lowered
            ] or ["  - none"]
        else:  # an unknown is not a zero
            out.append(
                "- harmful verdicts lowered by a line owner: COULD NOT BE READ (the audit was unreadable); do not "
                "assume there were none."
            )
        downgraded = [e for e in events if e.operation == "label_downgraded"]
        if audit_ok:
            out.append(
                f"- wrong or harmful verdicts replaced by something milder: "
                f"{sum(iso_week(e.ts) == week for e in downgraded)} this week, {len(downgraded)} in all:"
            )
            out += [
                f"  - {e.run_id}: {e.result} -> {e.decision} by {e.principal} at {e.ts:%Y-%m-%d %H:%M} UTC"
                for e in downgraded
            ] or ["  - none"]
        else:
            out.append("- downgraded verdicts: COULD NOT BE READ (the audit was unreadable).")
        if status:
            c = status.ceiling
            out += [
                (
                    f"- ceiling: {status.harmful} of {status.labelled} in the last {c.window_days} days, "
                    f"breached {'yes' if status.breached else 'no'} (max {c.max}; counting: "
                    f"{', '.join(c.counts)}; metric: {c.metric})."
                ),
                f"- counted by the ceiling this week: {pw.count_of(c.counts)} ({', '.join(c.counts)}).",
                *(
                    [
                        "- Promotion is blocked until the window clears or the sponsor changes max in writing."
                    ]
                    if status.breached
                    else []
                ),
            ]
        out += ["", "## Golden set"]
        cands = self.golden_candidates(start, end)  # runs, not agents: one list for the deployment
        for agent_id in sorted(
            a.id for a in self.registry.agents.values() if a.status != "retired"
        ):
            n, version = self._golden(agent_id)
            out.append(
                f"- {agent_id}: golden set: {n} items, version {version}, candidates this week: {len(cands)}"
            )
        out += [f"  - {r}" for r in cands]
        out += ["", "## Held runs (as of when this report was generated)"]
        held = sorted(self.hold_run_ids())
        out += [f"- {run_id}" for run_id in held] or ["- none"]
        out.append(
            "  (The evidence of a held run is kept until the client's retention rule or a request; its redaction map is "
            "purged at the retention maximum by the evidence purge, which owns those dates.)"
        )
        out += ["", "## Current overrides (as of when this report was generated)"]
        try:
            down = self.store.current_overrides()
            events = self.store.list_level_events()
            for agent_id, action_id in sorted(down):
                last = [
                    e
                    for e in events
                    if (e.agent_id, e.action_id) == (agent_id, action_id) and e.kind == "demote"
                ][-1]
                out.append(
                    f"- {agent_id}.{action_id}: shadow since {last.at:%Y-%m-%d %H:%M} UTC ({last.reason.split(':')[0]})"
                )
            if not down:
                out.append("- none: every action is at its configured level")
        except Exception as exc:  # noqa: BLE001
            out.append(f"- COULD NOT BE READ ({type(exc).__name__})")
        out += ["", "## Policy in force"]
        pol, spec = self.policy, DEFAULT_POLICY
        out.append(
            f"- promotion: {pol.promotion_min_labelled} labelled, {pol.promotion_min_agree:.0%} agree, at most "
            f"{pol.promotion_max_wrong_harmful} wrong + harmful, no harmful in {pol.promotion_harmful_window_days} days, "
            f"{pol.promotion_min_coverage:.0%} coverage, {pol.promotion_min_labellers} distinct labellers."
        )
        out.append(
            f"- demotion: {pol.wrong_limit} wrong runs inside {pol.wrong_window_days} days, or one harmful; "
            f"re-check every {pol.enforce_every_s} s; a harmful demotion is cleared by a second person, "
            f"at least {pol.harmful_clear_min_age_h} h after it."
        )
        if pol.allow_weaker_than_spec:
            out.append(
                "- WEAKER THAN THE SPEC'S NUMBERS ARE ALLOWED here (policy.allow_weaker_than_spec), signed by the client."
            )
        elif pol != spec:
            out.append(
                "- some policy numbers differ from the defaults, none weaker than the spec's."
            )
        out += [
            "",
            "> Held runs, golden counts and current overrides are the state when this report was generated; the counts and the ceiling are the week's own.",
        ]
        out += self._backlog_lines(week)
        out += [
            "",
            "## Not in this release",
            "- Failed events (intake, K4) and the config commit SHAs seen at start-up (K7) are not recorded yet.",
            "- The owner adds the written review (`weekly-review.md`).",
        ]
        return "\n".join(out) + "\n"

    def _golden(self, agent_id: str) -> tuple[int, str]:
        try:
            path = self.registry.golden_path(agent_id)
            n = sum(1 for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip())
            return n, self.registry.golden_sha256(agent_id)[:8] or "none"
        except Exception:  # noqa: BLE001 - no golden file: say so
            return 0, "none"

    def _backlog_lines(self, week: date) -> list[str]:
        """Only when the `backlog` step (K4) has written `tick_state.detail`; without K4 nothing is printed. K4 writes
        these keys verbatim, for the ISO week named in `week` (the Monday, YYYY-MM-DD): `week`,
        `max_oldest_received_age_s`, `late_starts`, `late_threshold_s` (the threshold K4 counted `late_starts`
        against), and also `events_received_count` for the heartbeat. A row for another week is not this week's."""
        try:
            state: TickState | None = self.store.get_tick_state("backlog")
        except Exception:  # noqa: BLE001
            return []
        detail = state.detail if state else None
        if not detail:
            return []
        out = ["", "## Backlog"]
        if detail.get("week") != week.isoformat():
            out.append(
                f"- Backlog numbers for the week of {week.isoformat()} were not recorded (the latest row is for "
                f"{detail.get('week', 'no week')})."
            )
            return out
        out.append(
            f"- Maximum oldest_received_age_s: {detail.get('max_oldest_received_age_s', 'not recorded')}."
        )
        threshold = detail.get("late_threshold_s")
        out.append(
            f"- Events started later than {threshold // 60 if isinstance(threshold, int) else '?'} minutes "
            f"(K4's threshold): {detail.get('late_starts', 'not recorded')}."
        )
        return out


def _ceiling_reason(latest: datetime) -> str:
    return f"ceiling:{latest.astimezone(UTC).isoformat(timespec='seconds')}"


def _read_promotion(reg: Registry, agent_id: str, action_id: str) -> dict[str, Any] | None:
    try:
        body = json.loads(
            promotion_path(reg.config.root, agent_id, action_id).read_text(encoding="utf-8")
        )
    except (ValueError, OSError):
        return None
    return body if isinstance(body, dict) else None


def _weaker_than(a: Thresholds, b: Thresholds) -> bool:
    """`a` asks for less than `b` on any number."""
    return (
        a.min_labelled < b.min_labelled
        or a.min_agree < b.min_agree
        or a.max_wrong_harmful > b.max_wrong_harmful
        or a.harmful_window_days < b.harmful_window_days
        or a.min_coverage < b.min_coverage
        or a.min_labellers < b.min_labellers
    )


def _verdict_key(label_id: str) -> str:
    """A csv row is one verdict whether it is pending (`-p`) or approved (`-a`): the demotion it causes is keyed by
    the row, so approving an import never demotes (or announces) a second time."""
    return re.sub(r"^(csv-[0-9a-f]{64}-\d+)-[pa]$", r"\1", label_id)


def _rate(k: int, n: int) -> str:
    if n == 0:
        return "n/a (nothing labelled)"
    bound = upper_error_bound(k, n)
    return (
        f"{k} of {n} ({k / n:.0%}), 95% upper bound {bound:.0%}"
        if bound is not None
        else f"{k} of {n}"
    )


def _secs(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.0f} s"


def _usd(x: Any) -> str:
    return "n/a" if x is None else f"${float(x):.4f}"


def _summary(week: date, body: str) -> str:
    keep = [
        ln
        for ln in body.splitlines()
        if ln.startswith(
            ("- Runs", "- Proposals labelled", "- Wrong rate", "- Miss rate", "- FLAG", "- ceiling")
        )
    ]
    return f"Pilot report for the week of {week.isoformat()} is ready.\n" + "\n".join(keep)
