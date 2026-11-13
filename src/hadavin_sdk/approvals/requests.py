"""Approval requests and decisions. A timeout escalates and never approves; no model output decides."""

from __future__ import annotations

import logging
import weakref
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from types import FunctionType, MappingProxyType
from typing import Any

from hadavin_sdk import standins
from hadavin_sdk.approvals.channel import Channel, clean
from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.bindguard import config_services, held_services_found
from hadavin_sdk.config import Config
from hadavin_sdk.guard.injection import Detector, injection_check
from hadavin_sdk.guard.runmap import RedactionError
from hadavin_sdk.models import (
    ApprovalDecision,
    ApprovalRequest,
    AuditEvent,
    GateDecision,
    Plan,
    canonical_json,
    now,
)
from hadavin_sdk.registry import Registry
from hadavin_sdk.store.protocol import StaleState, Store

OnDecided = Callable[[str, str, ApprovalDecision | None], object]
_LOG = logging.getLogger("hadavin_sdk.approvals")
RESEND_AFTER = timedelta(seconds=60)  # more than 2x a channel call's timeout


def make_on_decided(holder: dict[str, Any]) -> OnDecided:
    """The one ``on_decided`` function the core builds (``build()`` uses it): it hands a recorded decision to the
    runtime kept in ``holder["rt"]``. The bind guard recognises it by its code, its closure (one cell, a plain dict)
    AND what the dict holds (see ``_holder_ok``): the factory is public, so a function made by it is believed only
    while its holder is empty or holds the core's own runtime; any other callable, or a holder with anything else
    in it, can reach anything, so it is counted as held."""

    def on_decided(run_id: str, status: str, decision: ApprovalDecision | None) -> object:
        return holder["rt"].on_decided(run_id, status, decision)

    return on_decided


_ON_DECIDED_CODE = make_on_decided({}).__code__


_RUNTIME_SERVICES = (
    "store",
    "llm",
    "detector",
)  # the attributes of a core ``Runtime`` that reach a service: each must be one of the core's own stand-ins

# The other members ``Runtime.__init__`` writes, each believed only while it is the very object ``build()`` put there
# (identity, taken at the end of ``build()`` by ``seal_runtime``). One line each: a member that is not listed is not
# compared, so every row of ``tests/bind_mutants.py`` that drops one line is killed by a test that replaces that member.
_RUNTIME_SEALED = (
    "registry",
    "audit",
    "limits",
    "agents",
    "hooks",
)

# runtime -> (instance keys, {member: object}, agents as a frozenset, the hooks' own (name, value) pairs, the hooks
# class). Weak: a runtime that is gone leaves nothing. Written by ``seal_runtime`` (``build()``) only.
_RUNTIME_SEALS: weakref.WeakKeyDictionary[object, tuple] = weakref.WeakKeyDictionary()


def seal_runtime(runtime: object) -> None:
    """Record what ``build()`` made a ``Runtime`` hold: the names its ``__init__`` wrote (its instance dictionary keys),
    the identity of every member in ``_RUNTIME_SEALED`` and of every field of its ``hooks``, and its agents. A runtime
    that is not sealed (made by hand) is never believed (``_runtime_ok``). Called by ``app.build`` once the runtime
    is complete."""
    own = object.__getattribute__(runtime, "__dict__")
    hooks = dict.get(own, "hooks")
    _RUNTIME_SEALS[runtime] = (
        frozenset(dict.keys(own)),
        {name: dict.get(own, name) for name in _RUNTIME_SEALED},
        frozenset(set.__iter__(dict.get(own, "agents"))),
        tuple(dict.items(object.__getattribute__(hooks, "__dict__"))),
        type(hooks),
    )


def _hooks_unchanged(hooks: object, sealed: tuple) -> bool:
    """The hooks are the very object ``build()`` made: exact class (pinned), the same fields holding the same objects
    (identity), so a ``hold_run_ids``, ``execute`` or ``post_card`` put in later is not the wiring ``build()`` made."""
    if type(hooks) is not sealed[4] or not standins.is_pinned_instance(hooks, standins.HOOKS):
        return False
    fields = object.__getattribute__(hooks, "__dict__")
    if type(fields) is not dict:
        return False
    now = tuple(dict.items(fields))
    if len(now) != len(sealed[3]):
        return False
    return all(
        type(k) is str and k == name and v is was
        for (k, v), (name, was) in zip(now, sealed[3], strict=True)
    )


def _runtime_ok(runtime: object, scan: standins.Scan | None = None) -> bool:
    """True only for a runtime ``build()`` made and sealed: an instance of exactly the core's ``Runtime`` class,
    unchanged since it was pinned (``standins.is_pinned_instance``, pinned when its module is loaded), whose instance
    dictionary holds exactly the names ``__init__`` wrote (an ``rt.on_decided = f`` or ``rt.tick = f`` on the instance
    would shadow the pinned class method: such a key, or a missing one, is refused), whose ``registry``, ``audit``,
    ``limits``, ``agents`` and ``hooks`` are the objects ``build()`` put there, and whose ``store``, ``llm`` and
    ``detector`` are each one of the core's own stand-ins (a runtime made by hand with a real store or model is real).
    ``scan`` is the request's one scan (see ``standins.Scan``). An ``Approvals`` made by hand does not get this belief
    at all (see ``_holder_ok``)."""
    try:
        if not standins.is_pinned_instance(runtime, standins.RUNTIME):
            return False
        own = object.__getattribute__(runtime, "__dict__")
        sealed = _RUNTIME_SEALS.get(runtime)
        if type(own) is not dict or sealed is None:
            return False
        keys = tuple(dict.keys(own))
        methods = vars(type(runtime))
        if (
            not all(type(k) is str and k not in methods for k in keys)
            or frozenset(keys) != sealed[0]
        ):
            return False
        members = sealed[1]
        if not all(dict.get(own, name) is members[name] for name in _RUNTIME_SEALED):
            return False
        agents = dict.get(own, "agents")
        if type(agents) is not set or not all(type(a) is str for a in set.__iter__(agents)):
            return False
        if frozenset(set.__iter__(agents)) != sealed[2]:
            return False
        if not _hooks_unchanged(dict.get(own, "hooks"), sealed):
            return False
        return all(standins.is_stand_in(dict.get(own, name), scan) for name in _RUNTIME_SERVICES)
    except Exception:  # noqa: BLE001 - anything unreadable is not the core's runtime
        return False


def _holder_ok(holder: object, built: bool, scan: standins.Scan | None = None) -> bool:
    """True only for a plain ``dict`` that is empty, or (only when the ``Approvals`` was made by ``build()``) whose one
    entry under ``rt`` is a runtime the core made (``_runtime_ok``). The one key is read with the builtin dict
    methods and compared as an exact ``str`` by identity of its type, never with ``==`` (a key that is a ``str``
    subclass with its own ``__eq__`` is foreign code); a one-entry dict under another key has no ``rt`` and is counted."""
    if type(holder) is not dict:
        return False
    size = dict.__len__(holder)
    if size == 0:
        return True
    if size != 1 or not built:
        return False
    key = next(dict.__iter__(holder))
    # ``key`` is an exact ``str`` there: its ``!=`` is the builtin one
    if type(key) is not str or key != "rt":
        return False
    return _runtime_ok(dict.__getitem__(holder, key), scan)


_NONE = object()  # the marker ``_one_cell`` answers when the function is not made from the code


def _one_cell(func: object, code: object) -> object:
    """The one closure cell's content of a function made from ``code`` (identity of the code), else the marker
    ``_NONE``. Never raises (an empty cell is a ``ValueError``)."""
    try:
        if type(func) is not FunctionType or func.__code__ is not code:
            return _NONE
        cells = func.__closure__
        if cells is None or len(cells) != 1:
            return _NONE
        return cells[0].cell_contents
    except Exception:  # noqa: BLE001 - anything unreadable is not the core's function
        return _NONE


def _is_core_on_decided(func: object, built: bool, scan: standins.Scan | None = None) -> bool:
    """True only for a function made by ``make_on_decided`` (identity of its code) whose holder is judged by
    ``_holder_ok`` (``built``: the ``Approvals`` was made by ``build()``)."""
    cell = _one_cell(func, _ON_DECIDED_CODE)
    return cell is not _NONE and _holder_ok(cell, built, scan)


def fixed_clock(moment: datetime) -> Callable[[], datetime]:
    """A clock that always answers ``moment`` (tests move time with it). The bind guard recognises it by its code
    and its closure (one cell, an exact ``datetime``), so a test can use a fake clock and still be served."""

    def clock() -> datetime:
        return moment

    return clock


# a moment only to make the factory's code object
_FIXED_CLOCK_CODE = fixed_clock(datetime.min.replace(tzinfo=UTC)).__code__
_NOW_CODE = (
    now.__code__
)  # ``models.now`` is the same function object after ``now.__code__ = ...``: its code is pinned
# the two names ``models.now`` reads from its module (``datetime.now(UTC)``): pinned by identity too, so a replaced
# ``models.datetime`` or ``models.UTC`` (foreign code run before the signature is checked) is seen. Read from the
# function's own globals dictionary with the builtin ``dict.get``.
_NOW_DATETIME = dict.get(now.__globals__, "datetime")
_NOW_UTC = dict.get(now.__globals__, "UTC")


def _is_core_clock(func: object) -> bool:
    """True only for ``models.now`` (its code unchanged since this module was imported) or a clock made by
    ``fixed_clock`` whose moment is a ``datetime`` ``standins.plain_datetime`` accepts (exact type, ``tzinfo`` None or
    ``datetime.UTC``: an aware moment calls ``tzinfo.utcoffset`` in ``receive``, so a ``tzinfo`` that is a class with
    its own code is not believed). Any other callable is run before the signature is checked and can hold anything,
    so it is counted."""
    if func is now:
        names = now.__globals__
        return (
            now.__code__ is _NOW_CODE
            and dict.get(names, "datetime") is _NOW_DATETIME
            and dict.get(names, "UTC") is _NOW_UTC
        )
    moment = _one_cell(func, _FIXED_CLOCK_CODE)
    return moment is not _NONE and standins.plain_datetime(moment)


# Only ``app.build`` holds this: an ``Approvals`` made with it counts as built by ``build()`` (its audit sink and
# registry are not named as held). Python cannot hide a module name from code in the same process; the point is that
# the claim is no longer a plain argument value (``overrides={}``) that any caller can write.
_BUILD_TOKEN = object()


WARNING = "WARNING: the inputs read like instructions to an AI. Check them before approving. "


def summary(plan: Plan, detector: Detector | None = None) -> str:
    """Template-built, never by the model; inputs redacted and link-free. Inputs that read like instructions
    (the model copied them from a document) get a warning so a person does not approve them on autopilot."""
    inputs = canonical_json(plan.inputs)
    flagged = detector is not None and injection_check(detector, inputs, "approval_summary").flagged
    try:
        return clean(
            f"{WARNING if flagged else ''}{plan.agent_id} asks to run {plan.action_id} "
            f"v{plan.action_version} ({plan.risk_class}) on {plan.target.system}. Inputs: {inputs}. "
            f"Expected: {plan.expected_outcome}. Plan {plan.hash()[:12]}."
        )
    except (
        RedactionError
    ):  # inputs too large to redact (or nested too deep): the approver still sees what and where
        return clean(
            f"{WARNING if flagged else ''}{plan.agent_id} asks to run {plan.action_id} "
            f"v{plan.action_version} ({plan.risk_class}) on {plan.target.system}. "
            f"Inputs: (too large to show here). Plan {plan.hash()[:12]}."
        )


class Approvals:
    """Decisions must come from a channel's verified parse (``receive``), never from caller-supplied fields:
    ``decide`` is the internal step after verification and the one tests drive with a trusted fake.

    Everything the object holds (``store``, ``audit``, ``registry``, ``channel``, ``on_decided``, ``detector``,
    ``config``, ``overrides``, and the frozen facts) is set once, when the object is made; only ``clock`` can be set
    again (tests move time). ``__setattr__`` refuses every other assignment (a plain ``a._channel = x``, a private
    slot name that is already set, ``a.__class__ = Other``, any new name) with an ``AttributeError``. The attributes
    are slots, so ``vars(a)`` raises ``TypeError`` and the object cannot be weakly referenced (``weakref.ref(a)``
    raises ``TypeError``: there is no ``__weakref__`` slot). ``del a._channel`` is refused too (``__delattr__``
    always raises). ``object.__setattr__(a, "_channel", x)`` and ``object.__delattr__(a, "_channel")`` are the ways left; they
    are caught by the receiver, which asks again at every request on a bind other computers can reach with no reason
    given: the exact class of ``a``, that the ``Approvals`` class is unchanged since it was pinned, and what it holds
    now (``real_now``; a missing slot is answered 503). A copy of an ``Approvals`` (``copy.copy``, ``copy.deepcopy``,
    pickle) is refused with a ``TypeError``: a copy would duplicate the frozen facts and the set-once objects."""

    __slots__ = (
        "_audit_sink",
        "_channel",
        "_clock",
        "_config",
        "_config_facts",
        "_detector",
        "_hand_built",
        "_on_decided",
        "_overrides",
        "_registry",
        "_store",
    )

    def __init__(
        self,
        store: Store,
        audit: AuditSink,
        registry: Registry,
        channel: Channel,
        on_decided: OnDecided,
        clock: Callable[[], datetime] = now,
        detector: Detector | None = None,
        config: Config | None = None,
        overrides: Mapping[str, object] | None = None,
        *,
        _built_by: object = None,
    ) -> None:
        self._store, self._audit_sink, self._registry, self._channel = (
            store,
            audit,
            registry,
            channel,
        )
        self._on_decided, self._clock, self._detector = on_decided, clock, detector
        # The deployment config these approvals were built from, and the objects ``build()`` was handed in place of
        # configured ones (name -> object). Both are set once and read-only (no setter): ``receiver.serve`` checks
        # the config is the one it was given and counts what the approvals really hold, so neither can be swapped
        # for a stand-in after construction (None: built by hand, never served). What the config reaches is read
        # NOW and kept (``_config_facts``): the containers of a ``Config`` can be changed after it is built.
        self._config = config
        self._overrides = MappingProxyType(dict(overrides or {}))
        self._config_facts = config_services(config) if config is not None else ()
        # only ``build()`` holds the token: an object made with ``overrides={}`` from outside is hand-built
        self._hand_built = _built_by is not _BUILD_TOKEN

    @property
    def store(self) -> Store:
        return self._store

    @property
    def channel(self) -> Channel:
        return self._channel

    @property
    def detector(self) -> Detector | None:
        return self._detector

    @property
    def audit(self) -> AuditSink:
        return self._audit_sink

    @property
    def registry(self) -> Registry:
        return self._registry

    @property
    def on_decided(self) -> OnDecided:
        return self._on_decided

    @property
    def clock(self) -> Callable[[], datetime]:
        return self._clock

    @clock.setter
    def clock(
        self, value: Callable[[], datetime]
    ) -> None:  # tests move time; the bind guard judges the clock it holds at every question
        object.__setattr__(self, "_clock", value)

    def __setattr__(self, name: str, value: object) -> None:
        """Set once: a private slot can be written only while it is still empty (the constructor), and ``clock`` is
        the one name that can be set again. ``__class__`` and every other name are refused."""
        if name == "clock":
            object.__setattr__(self, name, value)  # the property setter
            return
        if name in Approvals.__slots__:
            try:
                object.__getattribute__(self, name)
            except AttributeError:  # empty: this is the constructor writing it for the first time
                object.__setattr__(self, name, value)
                return
        raise AttributeError(
            f"an Approvals is set once: {name!r} cannot be set (only 'clock' can be set again)"
        )

    def __delattr__(self, name: str) -> None:
        """Nothing is ever deleted: ``del a._channel`` followed by a new assignment would undo the set-once rule."""
        raise AttributeError(f"an Approvals is set once: {name!r} cannot be deleted")

    @property
    def config(self) -> Config | None:
        return self._config

    @property
    def config_facts(self) -> tuple[str, ...]:
        """What the config reached that is real, read when the approvals were made (never read again)."""
        return self._config_facts

    @property
    def overrides(self) -> Mapping[str, object]:
        """The objects ``build()`` was handed in place of configured ones (read-only)."""
        return self._overrides

    def held_services(self, scan: standins.Scan | None = None) -> dict[str, object]:
        """What these approvals really hold that can reach a service, read when asked: the build overrides, and the
        channel, the detector and the store as they are now. The bind guard (``bindguard.held_services_found``)
        counts each one that is not one of the core's own stand-ins. Approvals made by hand (not by ``build()``)
        also name their audit sink and registry: nothing says those are stand-ins. ``on_decided`` is named unless it
        is the function ``make_on_decided`` builds with an empty holder or (approvals made by ``build()`` only) the core
        runtime in it (``_runtime_ok``), and ``clock`` is named unless it is ``models.now`` or a ``fixed_clock`` of a
        plain ``datetime`` (``standins.plain_datetime``). ``scan``: the one scan of a request (``real_now`` makes it), shared
        with ``bindguard.held_services_found`` so the store the runtime holds and the store named here are read once."""
        # read through the same accessors the runtime uses (``self.channel`` and so on), never through the private
        # slots: a replaced accessor and the slot behind it cannot give two answers
        held: dict[str, object] = dict(self.overrides)
        live = {"channel": self.channel, "detector": self.detector, "store": self.store}
        for name, obj in live.items():
            # a given object and a different one now in its place are both counted (neither hides the other)
            if name in held and held[name] is not obj:
                held[f"{name}_given_to_build"] = held[name]
            held[name] = obj
        if self._hand_built:
            held["audit"], held["registry"] = self.audit, self.registry
        if not _is_core_on_decided(
            self.on_decided, not self._hand_built, scan
        ):  # a callable run after a valid signature can hold anything
            held["on_decided"] = self.on_decided
        if not _is_core_clock(self.clock):  # ``receive`` runs it before the signature is checked
            held["clock"] = self.clock
        return held

    def real_now(self) -> tuple[str, ...]:
        """What these approvals reach that is real, now: the facts of the config frozen at construction, and the held
        objects as they are at this moment. The receiver asks this at every request on a bind other computers can
        reach with no reason given (called as ``Approvals.real_now(a)``, so a subclass cannot answer for itself)."""
        scan = (
            standins.Scan()
        )  # ONE budget for the whole request, and an object looked at twice is read once
        return self.config_facts + held_services_found(Approvals.held_services(self, scan), scan)

    def __deepcopy__(self, memo: object) -> object:
        raise TypeError("an Approvals cannot be copied: it holds set-once objects and frozen facts")

    def __reduce_ex__(self, protocol: object) -> object:
        raise TypeError(
            "an Approvals cannot be copied or pickled: it holds set-once objects and frozen facts"
        )

    def receive(
        self, headers: Mapping[str, str], body: bytes, *, record_only: bool = False
    ) -> tuple[bool, str]:
        """Entry point for a channel callback: the channel verifies the request and names the approver.
        The HTTP receiver passes ``record_only=True``: it records and answers fast; ``tick`` runs the plan."""
        # ORDER: ``self.clock()`` and ``.timestamp()`` run BEFORE the signature is checked, so on a bind other computers
        # can reach nothing may be called here that the guard did not judge: the receiver's per-request check
        # (``real_now``) refuses a clock that is not ``models.now`` or a ``fixed_clock`` of a plain ``datetime``
        d = self.channel.parse_decision(headers, body, self.clock().timestamp())
        if d is None:
            return False, "bad_signature"
        return self.decide(d, record_only=record_only)

    def _audit(self, req: ApprovalRequest, operation: str, principal: str, **kw) -> None:
        self.audit.write_outcome(
            AuditEvent(
                run_id=req.run_id,
                domain="approval",
                operation=operation,
                principal=principal,
                source=self.channel.name,
                object_ref=req.approval_id,
                inputs_hash=req.plan_hash,
                **kw,
            )
        )

    def request(self, plan: Plan, decision: GateDecision, requested_by: str) -> ApprovalRequest:
        chain = self.registry.chains[self.registry.contracts[plan.action_id].chain_id]
        req = ApprovalRequest(
            run_id=plan.run_id,
            plan_hash=decision.plan_hash,
            risk_class=plan.risk_class,
            chain_id=chain.id,
            steps=chain.steps,
            step_expires_at=self.clock() + timedelta(seconds=chain.steps[0].timeout_s),
            requested_by=requested_by,
            summary=summary(plan, self.detector),
        )
        self.store.save_approval_request(req)
        req = self._send(req, chain.steps[0].approver_ids)
        self._audit(req, "request", requested_by, result="PENDING")
        return req

    def _send(self, req: ApprovalRequest, approver_ids: list[str]) -> ApprovalRequest:
        """Send, then record `sent_at` and the channel's message id. A failed send leaves `sent_at` empty,
        the request stays PENDING and ``resend_unsent`` (a tick step) tries again."""
        try:
            ref = self.channel.send(req, approver_ids)
        except Exception as exc:  # noqa: BLE001 - any channel failure: keep the request, resend later
            _LOG.warning(
                "approval %s: channel send failed (%s); tick will resend",
                req.approval_id,
                type(exc).__name__,
            )
            return req
        sent = req.model_copy(update={"sent_at": self.clock(), "channel_ref": ref})
        try:
            self.store.update_approval_request(sent, req.status, req.current_step)
        except StaleState:  # decided or escalated meanwhile: the newer row wins
            return self.store.get_approval_request(req.approval_id)
        return sent

    def resend_unsent(self, at: datetime | None = None) -> list[str]:
        """PENDING requests whose send failed (`sent_at` empty) for at least RESEND_AFTER since their step
        began (a send still in flight is left alone): send them again. Returns approval ids."""
        at = at or self.clock()
        sent = []
        for req in self.store.list_approvals({"PENDING"}):
            step = req.steps[req.current_step]
            began = req.step_expires_at - timedelta(seconds=step.timeout_s)
            due = req.sent_at is None and at - began >= RESEND_AFTER
            if due and self._send(req, step.approver_ids).sent_at:
                sent.append(req.approval_id)
        # ponytail: a send that reached Slack but timed out on the reply is sent again (a duplicate message;
        # both carry the same valid buttons). An idempotency key needs the channel to support one.
        return sent

    def decide(self, d: ApprovalDecision, *, record_only: bool = False) -> tuple[bool, str]:
        """Check and record one decision. ``record_only``: leave running the plan to ``tick`` reconcile."""
        req = self.store.get_approval_request(d.approval_id)
        reason = None
        if req.status != "PENDING":
            reason = "not_pending"
        elif d.step != req.current_step:
            reason = "old_step"
        elif self.clock() >= req.step_expires_at:
            reason = "step_expired"  # the sweep escalates it; a late decision never runs the plan
        elif d.approver_id not in req.steps[req.current_step].approver_ids:
            reason = "not_an_approver_for_this_step"
        elif d.approver_id == req.requested_by:
            reason = "requester_cannot_approve"
        elif d.plan_hash != req.plan_hash:
            reason = "plan_hash_mismatch"
        if reason:
            self._audit(req, "decide", d.approver_id, decision=d.decision, error_code=reason)
            return False, reason
        status = "APPROVED" if d.decision == "approve" else "REJECTED"
        new = req.model_copy(update={"status": status})
        try:
            # One atomic write: the decision (one per approval step) and the status compare-and-set. Of two
            # racing clicks, or a click racing the sweep, exactly one is kept, and nothing of the loser.
            self.store.record_decision(d, new, "PENDING", req.current_step)
        except StaleState:
            return False, "stale"
        self._audit(req, "decide", d.approver_id, decision=d.decision, result=status)
        if (
            record_only
        ):  # the receiver must answer fast: tick reconcile updates the message and runs it
            return True, status.lower()
        self.update_message(new)
        self.on_decided(req.run_id, status, d)
        return True, status.lower()

    def update_message(self, req: ApprovalRequest) -> None:
        """Show the outcome in the channel; a failure is logged (the decision is already recorded)."""
        try:
            self.channel.update(req)
        except Exception as exc:  # noqa: BLE001 - a stale message is cosmetic
            _LOG.warning(
                "approval %s: channel update failed (%s)", req.approval_id, type(exc).__name__
            )

    def sweep(self, at: datetime | None = None) -> list[str]:
        """Escalate each due request one step; after the last step it expires. Returns approval ids touched."""
        at = at or self.clock()
        touched = []
        for req in self.store.list_due_approvals(at):
            nxt = req.current_step + 1
            if nxt < len(req.steps):
                new = req.model_copy(
                    update={
                        "current_step": nxt,
                        "step_expires_at": at + timedelta(seconds=req.steps[nxt].timeout_s),
                        "sent_at": None,  # the next step's approvers have not been asked yet
                    }
                )
                status = "PENDING"
            else:
                new = req.model_copy(update={"status": "EXPIRED"})
                status = "EXPIRED"
            try:
                self.store.update_approval_request(new, "PENDING", req.current_step)
            except StaleState:
                continue
            self._audit(req, "sweep", "system", result=status, decision=f"step{new.current_step}")
            if status == "PENDING":
                self._send(new, req.steps[nxt].approver_ids)
            else:
                self.update_message(new)
                try:
                    self.channel.notify(
                        req.requested_by,
                        f"Approval {req.approval_id} expired with no decision. Nothing was run.",
                    )
                    self.on_decided(req.run_id, "EXPIRED", None)
                except Exception as exc:  # noqa: BLE001 - tick reconcile ends the run if this failed
                    _LOG.warning(
                        "approval %s: expiry follow-up failed (%s)",
                        req.approval_id,
                        type(exc).__name__,
                    )
            touched.append(req.approval_id)
        return touched
