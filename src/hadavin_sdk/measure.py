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

import csv
import hashlib
import io
import json
import logging
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
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

PROPOSAL_LABELS = ("agree", "partial", "wrong", "harmful")
ABSTAIN_LABELS = ("abstain_ok", "missed")
LABELS = PROPOSAL_LABELS + ABSTAIN_LABELS
BASELINE_FILE = "baseline.yaml"
PROMOTIONS_DIR = "promotions"
WRONG_WINDOW = timedelta(days=14)
WRONG_LIMIT = 3
HELD_MAPS_MAX_DAYS = (
    400  # redaction maps of held runs are purged at this age whatever the hold (kernel 6.3)
)
LATE_START_S = 600
IST = timezone(timedelta(hours=5, minutes=30))
_ALIASES = {
    "should_have_answered": "missed"
}  # the abstain button's value before K6 built its parser
_ID = re.compile(r"[A-Za-z0-9_.-]{1,100}")
_NAME = re.compile(r"[A-Za-z0-9_-]{1,100}")
_PLACEHOLDER = re.compile(r"<[^>]*>")


@dataclass(frozen=True)
class Thresholds:
    """Promotion shadow -> suggest, per (agent, action) (kernel 6.1; the owner confirms the numbers)."""

    min_labelled: int = 30
    min_agree: float = 0.70
    max_wrong_harmful: int = 1
    harmful_window_days: int = 28
    min_coverage: float = 0.80


DEFAULTS = Thresholds()


# --- parsing -----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedAction:
    kind: str  # "label" or "clear"
    args: tuple[str, ...]


def parse_action_value(value: str) -> ParsedAction | None:
    """A button value the measurement owns, or None (an approval value is not ours). The separator is ``|`` and the
    first field names the kind: ``label|<run_id>|<label>`` or ``clear|<agent_id>|<action_id>``. A ``:`` payload or
    an unknown label is refused."""
    parts = value.split("|")
    if len(parts) == 3 and parts[0] == "label":
        name = _ALIASES.get(
            parts[2], parts[2]
        )  # cards posted before K6 carried `should_have_answered`
        if _ID.fullmatch(parts[1]) and name in LABELS:
            return ParsedAction("label", (parts[1], name))
    if parts[0] == "clear" and len(parts) == 3 and all(_NAME.fullmatch(p) for p in parts[1:]):
        return ParsedAction("clear", (parts[1], parts[2]))
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


def load_baseline(root: Path) -> Ceiling:
    """``baseline.yaml`` ``ceiling`` (K0). Required: the pilot tooling refuses to start without a filled one."""
    path = Path(root) / BASELINE_FILE
    if not path.is_file():
        raise ConfigError(f"{BASELINE_FILE} is required in pilot and prod: {path} does not exist")
    from hadavin_sdk.config import load_yaml

    try:
        data = load_yaml(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001 - any parse failure is a refusal, naming the class only
        raise ConfigError(f"{BASELINE_FILE}: cannot be read ({type(exc).__name__})") from None
    raw = data.get("ceiling") if isinstance(data, dict) else None
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
    problems += [f"{where}: {path.name} {s}" for s in shortfalls(body.get("numbers") or {})]
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


@dataclass
class PromoteResult:
    ok: bool
    problems: list[str] = field(default_factory=list)
    path: Path | None = None
    numbers: Numbers | None = None


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
        thresholds: Thresholds = DEFAULTS,
        limits: Limits | None = None,
    ) -> None:
        self.limits = limits  # for the signed stop / reset; None: those clicks are ignored
        self.store, self.audit, self.registry, self.channel = store, audit, registry, channel
        self.ceiling, self.clock, self.th = ceiling, clock, thresholds
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
        try:
            self.audit.write_outcome(
                AuditEvent(
                    run_id=run_id,
                    ts=self.clock(),
                    domain="measure",
                    operation=operation,
                    principal=principal,
                    source=self.channel.name,
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
        return self.store.held_run_ids()

    # --- labels --------------------------------------------------------------------------------------------

    def _wrong_episode(self, agent_id: str, action_id: str, extra: Label | None) -> str | None:
        """The key of a "3 wrong in 14 days" episode for the action (the run of the newest wrong label), or None."""
        since = self.clock() - WRONG_WINDOW
        labels = self.store.list_labels_for(agent_id, action_id, since)
        if extra is not None:
            labels = [*labels, extra]
        # A run is wrong when its latest ELIGIBLE label is wrong, or when any unapproved csv row says wrong (that
        # label is not evidence, but it must not be overridable by an unapproved "agree": the safe direction).
        by_run: dict[str, Label] = {
            r: x for r, x in latest_labels(labels).items() if x.label == "wrong"
        }
        for x in labels:
            seen = by_run.get(x.run_id)
            newer = seen is None or (x.created_at, x.label_id) > (seen.created_at, seen.label_id)
            if not x.counts and x.label == "wrong" and newer:
                by_run[x.run_id] = x
        wrongs = sorted(
            (x for x in by_run.values() if x.created_at >= since),
            key=lambda x: (x.created_at, x.label_id),
        )
        return wrongs[-1].label_id if len(wrongs) >= WRONG_LIMIT else None

    def _demotion_for(self, label: Label, agent_id: str, action_id: str) -> LevelEvent | None:
        # Keyed by the label row, not the run: a harmful label after a clear is a new fact and demotes again.
        reason = None
        if label.label == "harmful":
            reason = f"harmful:{label.label_id}"
        elif label.label == "wrong" and (key := self._wrong_episode(agent_id, action_id, label)):
            reason = f"wrong_x{WRONG_LIMIT}:{key}"
        if reason is None or self._has_event(agent_id, action_id, reason):
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
        return any(
            e.agent_id == agent_id and e.action_id == action_id and e.reason == reason
            for e in self.store.list_level_events()
        )

    def _check(
        self, principal_id: str, run_id: str, label: str
    ) -> tuple[Plan | None, LabelResult | None]:
        """Who may label what: a known person, a known label, a run that exists, a label that fits the run (the
        four proposal labels need a plan, the two abstain labels none). Returns (plan, None) or (None, refusal)."""
        principal = self.registry.principals.get(principal_id)
        if principal is None or principal.kind != "person":
            return None, LabelResult(False, "unknown_principal")
        if label not in LABELS:
            return None, LabelResult(False, "unknown_label")
        if not _ID.fullmatch(run_id):
            return None, LabelResult(False, "unknown_run")
        try:
            self.store.get_run(run_id)
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
        transaction, then audit. Never raises."""
        plan, refusal = self._check(principal_id, run_id, label)
        if refusal is not None:
            return refusal
        may = self._may_lower_harmful(principal_id)
        try:
            lowers = label != "harmful" and may and self._latest_is_harmful(run_id)
            new = self._new_label(principal_id, run_id, label, channel, approved_by, label_id)
            demote = self._demotion_for(new, plan.agent_id, plan.action_id) if plan else None
            # The sticky check runs inside the store's transaction, serialised per run: two clicks cannot both pass.
            self.store.add_labels([(new, demote)], may_lower_harmful=may)
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
        self._after_commit(new, demote, lowers)
        return LabelResult(True, "recorded", demoted=demote is not None)

    def _after_commit(self, new: Label, demote: LevelEvent | None, lowers: bool) -> None:
        """Audit and announce what is already committed. Never raises: the label stands whatever the sink or the
        channel does."""
        self._audit(
            new.run_id,
            "label",
            new.principal_id,
            object_ref=new.label_id,
            decision=new.label,
            result="recorded",
            caught_by="human_label" if new.label in ("wrong", "harmful") else None,
        )
        if lowers:
            self._audit(
                new.run_id,
                "harmful_lowered",
                new.principal_id,
                object_ref=new.label_id,
                decision=new.label,
            )
        if demote is not None:
            try:
                self._announce(demote)
            except Exception as exc:  # noqa: BLE001
                _LOG.warning("demotion announcement failed (%s)", type(exc).__name__)

    def _announce(self, ev: LevelEvent) -> None:
        """Audit the demotion and post a card with a Clear button for the line owner."""
        from hadavin_sdk.approvals.cards import render_demotion

        self._audit(
            "-", "demote", ev.by, object_ref=f"{ev.agent_id}.{ev.action_id}", result=ev.reason
        )
        try:
            d = self.channel.post_card(render_demotion(ev.agent_id, ev.action_id, ev.reason))
            if not d.ok:
                self._notify(f"{ev.agent_id}.{ev.action_id} was demoted to shadow ({ev.reason}).")
        except Exception as exc:  # noqa: BLE001
            _LOG.warning("demotion card not delivered (%s)", type(exc).__name__)

    # --- signed channel clicks -----------------------------------------------------------------------------

    def handle_action(self, action: Action) -> tuple[int, str]:
        """A verified click that ``is_ours``: (HTTP status, reason). The user comes from the signed request."""
        parsed = parse_action_value(action.value)
        if parsed is None:
            return 200, "malformed"
        if action.nonce:
            # A signed request is good for 5 minutes, so a captured copy would replay. Each delivery is acted on once.
            try:
                fresh = self.store.claim_action(action.nonce, self.clock())
            except Exception as exc:  # noqa: BLE001
                _LOG.error("click refused: store error %s", type(exc).__name__)
                return 503, "store_unavailable"
            if not fresh:
                self._audit("-", parsed.kind, action.user, result="refused", error_code="replay")
                return 200, "replay"
        if parsed.kind == "label":
            res = self.record_label(action.user, *parsed.args)
            return res.status, res.reason
        if parsed.kind in ("stop", "reset"):
            return self.kill_switch(action.user, parsed.kind)
        if parsed.kind == "approve_import":
            return self.approve_import(action.user, parsed.args[0])
        return self.clear(action.user, *parsed.args)

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
            self.store.add_labels(items, may_lower_harmful=self._may_lower_harmful(author))
        except HarmfulSticky:
            return 200, "refused: harmful_is_sticky"
        except StaleState:
            return 200, "already_approved"
        except Exception as exc:  # noqa: BLE001
            _LOG.error("approve_import refused: store error %s", type(exc).__name__)
            return 503, "store_unavailable"
        for new, demote in items:
            self._after_commit(new, demote, False)
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

    def _clear_blocked(self, agent_id: str, action_id: str, last: LevelEvent) -> str | None:
        """Why a demotion may not be lifted now, or None. A demotion by the ceiling stays while the ceiling is
        breached (the breach notice says every action is shadow, and that must stay true). An action whose config
        level is ``suggest`` also needs the section 6.1 numbers to hold again, derived from the store now."""
        status = self.ceiling_status()
        breached = bool(status and status.breached)
        if breached and last.reason.startswith("ceiling:"):
            return "ceiling_breached"
        agent = self.registry.agents.get(agent_id)
        if agent is not None and (agent.levels or {}).get(action_id) == "suggest":
            if breached:
                return "ceiling_breached"
            fresh = numbers_for(
                self.store.list_labels_for(agent_id, action_id, None),
                self.store.count_proposals(agent_id, action_id, None),
                self.clock(),
                self.th,
            )
            if shortfalls(fresh.as_dict(), self.th):
                return "evidence_below_6_1"
        return None

    def clear(self, principal_id: str, agent_id: str, action_id: str) -> tuple[int, str]:
        """A line owner lifts a demotion. Needs the ``clear_override`` admin right."""
        if not self._admin(principal_id, "clear_override", "clear"):
            return 200, "not_authorised"
        try:
            # Look, decide, then write only if nothing changed since we looked (compare-and-set on the newest
            # level event): a demotion that lands between the check and the write must not be cleared unseen.
            events = [
                e
                for e in self.store.list_level_events()
                if (e.agent_id, e.action_id) == (agent_id, action_id)
            ]
            if not events or events[-1].kind != "demote":
                return 200, "not_demoted"
            why = self._clear_blocked(agent_id, action_id, events[-1])
            if why:
                self._audit(
                    "-", "clear", principal_id, object_ref=f"{agent_id}.{action_id}",
                    result="refused", error_code=why,
                )  # fmt: skip
                return 200, why
            lifted = LevelEvent(
                agent_id=agent_id,
                action_id=action_id,
                kind="clear",
                reason="line_owner_clear",
                by=principal_id,
                at=self.clock(),
            )
            if not self.store.clear_demotion(lifted, events[-1].seq or 0):
                self._audit(
                    "-", "clear", principal_id, object_ref=f"{agent_id}.{action_id}",
                    result="refused", error_code="changed_meanwhile",
                )  # fmt: skip
                return 200, "changed_meanwhile"
        except Exception as exc:  # noqa: BLE001
            _LOG.error("clear refused: store error %s", type(exc).__name__)
            return 503, "store_unavailable"
        self._audit(
            "-", "clear", principal_id, object_ref=f"{agent_id}.{action_id}", result="cleared"
        )
        return 200, "cleared"

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
            self.store.add_labels(items, may_lower_harmful=self._may_lower_harmful(by))
        except HarmfulSticky:
            return 0, ["harmful_is_sticky"]
        except StaleState:
            return 0, []  # the same file again: already stored
        except Exception as exc:  # noqa: BLE001
            _LOG.error("import refused: store error %s", type(exc).__name__)
            return 0, ["store_unavailable"]
        for new, demote in items:
            self._after_commit(new, demote, False)
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

    def enforce(self, at: datetime | None = None) -> list[LevelEvent]:
        """Idempotent: re-check the 3-wrong rule (two simultaneous labels can each miss the third) and the
        ceiling, and insert the demotions that are missing. A cleared episode is not demoted again."""
        at = at or self.clock()
        added: list[LevelEvent] = []
        existing = {(e.agent_id, e.action_id, e.reason) for e in self.store.list_level_events()}
        for agent_id, action_id in self._pairs():
            key = self._wrong_episode(agent_id, action_id, None)
            if key and (agent_id, action_id, f"wrong_x{WRONG_LIMIT}:{key}") not in existing:
                added.append(self._level(agent_id, action_id, f"wrong_x{WRONG_LIMIT}:{key}", at))
        status = self.ceiling_status(at)
        breach_notice = None
        if status and status.breached and status.latest_harmful_at is not None:
            reason = (
                f"ceiling:{status.latest_harmful_at.astimezone(UTC).isoformat(timespec='seconds')}"
            )
            fresh = [
                self._level(a, x, reason, at)
                for a, x in self._pairs()
                if (a, x, reason) not in existing
            ]
            added += fresh
            if fresh:
                breach_notice = status
        for ev in added:
            self.store.add_level_event(ev)
            self._audit(
                "-", "demote", ev.by, object_ref=f"{ev.agent_id}.{ev.action_id}", result=ev.reason
            )
        for ev in added:
            if not ev.reason.startswith("ceiling:"):
                self._announce_card(ev)
        if breach_notice:
            c = breach_notice
            self._notify(
                f"Ceiling breached: {c.harmful} of {c.labelled} labelled in the last "
                f"{c.ceiling.window_days} days counts against it ({', '.join(c.ceiling.counts)}; max {c.ceiling.max}). Every action is shadow. "
                "Promotion is blocked until the window clears or the sponsor changes the ceiling in writing."
            )
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

    def _announce_card(self, ev: LevelEvent) -> None:
        from hadavin_sdk.approvals.cards import render_demotion

        try:
            self.channel.post_card(render_demotion(ev.agent_id, ev.action_id, ev.reason))
        except Exception as exc:  # noqa: BLE001
            _LOG.warning("demotion card not delivered (%s)", type(exc).__name__)

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
                False, [f"{agent_id}.{action_id} is not an action of a known agent"]
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
        nm = numbers_for(
            self.store.list_labels_for(agent_id, action_id, None),
            self.store.count_proposals(agent_id, action_id, None),
            at,
            self.th,
        )
        problems += shortfalls(nm.as_dict(), self.th)
        record = replay_records.green_record(reg, agent_id)
        if record is None:
            problems.append(
                f"no green replay record (k >= 3) in {replay_records.FILE} for the current config hash, "
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
                fresh = numbers_for(
                    self.store.list_labels_for(agent.id, action, None),
                    self.store.count_proposals(agent.id, action, None),
                    self.clock(),
                    self.th,
                )
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
        when this call wrote it."""
        if self.ceiling is None:
            return None  # dev without baseline.yaml: nothing to report against
        at = at or self.clock()
        week = week_start(at) - timedelta(days=7)
        if self.store.get_report(week) is not None:
            return None
        body = self.render_report(week, at)
        # Tell the line owner first, store second: a notice that cannot be delivered leaves the week without a
        # report, so the next tick (the step runs hourly) renders and tries again instead of losing the notice.
        if self._notify(_summary(week, body)) == 0:
            raise RuntimeError("weekly report not announced: no line owner could be reached")
        if not self.store.put_report(week, body):
            return None  # another tick stored it between our check and now
        return body

    def render_report(self, week: date, at: datetime | None = None) -> str:
        at = at or self.clock()
        start = datetime(week.year, week.month, week.day, tzinfo=UTC)
        end = start + timedelta(days=7)
        pw, prev = self.store.pilot_week(week), self.store.pilot_week(week - timedelta(days=7))
        aw = self.store.approval_week(week)
        ist = at.astimezone(IST)
        out = [
            f"# Pilot report: week of {week.isoformat()} (Monday, UTC)",
            "",
            (
                f"Generated {at.astimezone(UTC):%Y-%m-%d %H:%M} UTC / {ist:%Y-%m-%d %H:%M} IST. Every number is counted "
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
        if pw.wrong + pw.harmful > prev.wrong + prev.harmful and pw.wrong > prev.wrong:
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
                f"coverage {nm.coverage:.0%}, agree {nm.agree_rate:.0%}."
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
        try:
            # Events that could not be written when they happened wait in the audit's outbox; bring them into the
            # log first so the counts below do not miss them.
            self.audit.reconcile()
            events = self.audit.events()
            counts = caught_week(events, week)
            out += [f"- {k}: {v}" for k, v in sorted(counts.items())] or ["- nothing was caught"]
        except Exception as exc:  # noqa: BLE001
            out.append(f"- the audit could not be read ({type(exc).__name__})")
        out.append(
            f'- Approvals decided: {aw.decisions}, "won\'t run": {aw.wont_run}, median {_secs(aw.median_s)}.'
        )
        out += ["", "## Ceiling"]
        status = self.ceiling_status(at)
        lowered = [e for e in events if e.operation == "harmful_lowered"]
        out.append(
            f"- harmful verdicts lowered by a line owner: {sum(iso_week(e.ts) == week for e in lowered)} this week, "
            f"{len(lowered)} in all. A lowered verdict leaves the ceiling count, so each one is listed:"
        )
        out += [
            f"  - {e.run_id}: lowered to {e.decision} by {e.principal} at {e.ts:%Y-%m-%d %H:%M} UTC"
            for e in lowered
        ] or ["  - none"]
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
        out += ["", "## Held runs"]
        held = sorted(self.store.held_run_ids())
        for run_id in held:
            try:
                made = self.store.get_run(run_id).created_at
                out.append(
                    f"- {run_id}: redaction map purged by "
                    f"{(made + timedelta(days=HELD_MAPS_MAX_DAYS)):%Y-%m-%d} (400 days from the run)"
                )
            except Exception:  # noqa: BLE001
                out.append(f"- {run_id}")
        if not held:
            out.append("- none")
        out += self._backlog_lines()
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

    def _backlog_lines(self) -> list[str]:
        """Only when the `backlog` step (K4) has written `tick_state.detail`; without K4 nothing is printed."""
        try:
            state: TickState | None = self.store.get_tick_state("backlog")
        except Exception:  # noqa: BLE001
            return []
        detail = state.detail if state else None
        if not detail:
            return []
        age = detail.get("max_oldest_received_age_s", detail.get("oldest_received_age_s"))
        late = detail.get("late_starts")
        out = ["", "## Backlog"]
        if age is not None:
            out.append(f"- Maximum oldest_received_age_s: {age}.")
        if late is not None:
            out.append(f"- Events started later than {LATE_START_S // 60} minutes: {late}.")
        return out


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
