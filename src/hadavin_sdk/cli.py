"""hadavin-sdk CLI.

  hadavin-sdk [--config DIR] gate <agent> [--k K]        exit 0 when green, 1 when below the threshold;
                                                         --k K runs each item K times (pass^k), default 1
  hadavin-sdk [--config DIR] limits stop|reset --by WHO  needs a shared store (postgres); memory: exit 2
  hadavin-sdk [--config DIR] tick                       one pass of approvals sweep, reconcile, stuck runs,
                                                         audit checkpoint; exit 0 ok, 1 a step failed,
                                                         2 config error, 4 store unreachable
  hadavin-sdk [--config DIR] migrate [--runtime-role R] [--portal-role P]  apply the postgres schema; the migration role's DSN
                                                         comes from the HADAVIN_MIGRATE_DSN environment variable
  hadavin-sdk [--config DIR] audit verify                exit 0 intact, 1 not, 2 refused, 3 unreadable
  hadavin-sdk [--config DIR] replay AGENT --bundles D --cause-list D --max-usd X --out OUT [--k K]
                                                         K1b-lite: run recorded incidents through the agent;
                                                         exit 0 complete, 1 aborted or USD cap, 2 refused, 3 failure
  hadavin-sdk [--config DIR] score --outputs OUT --answers F --cause-list D --bundles D
                                                         K1b-lite: count the replay's results into score/score-report.md;
                                                         exit 0 report produced, 2 refused, 3 failure (no verdict)

Every command is wrapped by ``main``: a ``ConfigError`` exits 2, any other uncaught error exits 3, so a crash never
looks like a red gate (exit 1).

``--config`` goes before the subcommand and overrides ``HADAVIN_CONFIG_DIR``. From a source checkout use ``uv run python -m hadavin_sdk.cli`` so
the current folder (and its check modules) is importable.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import traceback
from decimal import Decimal, InvalidOperation
from pathlib import Path

from hadavin_sdk import evals
from hadavin_sdk.audit import AuditUnavailable
from hadavin_sdk.backends import platform_secrets
from hadavin_sdk.backends.factory import make
from hadavin_sdk.config import load_config
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.guard.injection import combine
from hadavin_sdk.limits import Limits, StopNotPermitted, SwitchChanged
from hadavin_sdk.models import new_id
from hadavin_sdk.registry import load_registry
from hadavin_sdk.store.protocol import (
    NotMigrated,
    StoreBusy,
    StoreUnavailable,
    is_connectivity_error,
)


def _num(x: float | None, places: int = 2) -> str:
    return "-" if x is None else f"{x:.{places}f}"


def _positive(text: str) -> int:
    k = int(text)
    if k < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return k


def _money(text: str) -> Decimal:
    try:
        d = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError("must be a decimal number") from None
    if not d.is_finite() or d <= 0:
        raise argparse.ArgumentTypeError("must be a finite number above zero")
    return d


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. ConfigError exits 2 and any other uncaught exception exits 3 (never Python's crash code 1)."""
    try:
        return _main(argv)
    except ConfigError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - the class name only: a message could carry a secret
        print(
            f"failed: {type(exc).__name__} (set HADAVIN_DEBUG=1 for the traceback)", file=sys.stderr
        )
        if os.environ.get("HADAVIN_DEBUG") == "1":
            traceback.print_exc()
        return 3


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="hadavin-sdk")
    p.add_argument("--config", help="client config folder (overrides HADAVIN_CONFIG_DIR)")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gate", help="run an agent's golden set")
    g.add_argument("agent")
    g.add_argument("--k", type=_positive, default=1, help="runs per golden item (pass^k)")
    lim = sub.add_parser("limits", help="kill switch")
    lim.add_argument("action", choices=["stop", "reset", "status", "whois", "check"])
    lim.add_argument("name", nargs="?", help="whois: the name to turn into its label")
    lim.add_argument("--by", help="stop and reset: who is acting (stored only as a keyed label)")
    lim.add_argument(
        "--expect-version", type=int, help="reset: the version that `limits status` printed"
    )
    lim.add_argument(
        "--expect-open", type=int, help="reset: the open_requests that `limits status` printed"
    )
    sub.add_parser("tick", help="one pass of the housekeeping steps (run every 30-60 s)")
    mig = sub.add_parser("migrate", help="apply the postgres store schema (migration role)")
    mig.add_argument("--runtime-role", help="grant this database role what the runtime needs")
    mig.add_argument(
        "--purge-role",
        help="grant this database role the evidence purge (DELETE on tool_calls and redaction_maps) and nothing else",
    )
    mig.add_argument(
        "--reset-role",
        help="the NOLOGIN database role whose members may reset the kill switch (default: limits.reset_group)",
    )
    mig.add_argument(
        "--stop-role",
        help="the database login of the operator's stop (it may only call the stop function)",
    )
    mig.add_argument(
        "--portal-role", help="grant this database role SELECT on the portal's relations only"
    )
    aud = sub.add_parser("audit", help="check the chain audit")
    aud.add_argument("action", choices=["verify"])
    rep = sub.add_parser(
        "replay", help="K1b-lite: run recorded incidents through an agent (report only)"
    )
    rep.add_argument("agent")
    rep.add_argument("--bundles", required=True, type=Path)
    rep.add_argument("--cause-list", required=True, type=Path)
    rep.add_argument("--k", type=_positive, default=1, help="runs of the whole set")
    rep.add_argument(
        "--max-usd", required=True, type=_money, help="total cost cap for this invocation"
    )
    rep.add_argument("--out", required=True, type=Path)
    rep.add_argument(
        "--i-know-data-is-already-masked",
        action="store_true",
        help="needed only when config k1b.redact is false (the run records that you said so)",
    )
    sc = sub.add_parser(
        "score", help="K1b-lite: count a replay's results (report only, no verdict)"
    )
    sc.add_argument("--outputs", required=True, type=Path)
    sc.add_argument("--answers", required=True, type=Path)
    sc.add_argument("--cause-list", required=True, type=Path)
    sc.add_argument("--bundles", required=True, type=Path)
    args = p.parse_args(argv)
    if args.config:
        os.environ["HADAVIN_CONFIG_DIR"] = args.config
    if args.cmd == "tick":
        return _tick()
    if args.cmd == "limits":
        if args.action in ("stop", "reset") and not args.by:
            p.error(f"limits {args.action} needs --by")
        if args.action == "whois" and not args.name:
            p.error("limits whois needs a NAME")
    cfg = load_config()
    if args.cmd == "migrate":
        return _migrate(
            cfg,
            args.runtime_role,
            args.portal_role,
            args.purge_role,
            reset_role=args.reset_role,
            stop_role=args.stop_role,
        )
    reg = load_registry(cfg)
    if args.cmd in (
        "replay",
        "score",
    ):  # before the memory-store refusal below: K1b needs no shared store
        return _k1b(cfg, reg, args)

    if args.cmd == "gate":
        b = cfg.backends
        run = evals.gate(
            reg,
            make("llm", b.llm, make("secrets", b.secrets), routes=cfg.routes),
            args.agent,
            k=args.k,
        )
        # k == 1: today's "passed/n" line. k > 1: the fraction behind pass@1, (item, run) pairs passed / n*k;
        # the item count passing all k runs is pass^k below.
        pairs = run.n * run.k
        frac = f"{run.passed}/{run.n}" if run.k == 1 else f"{round(run.pass_rate * pairs)}/{pairs}"
        print(
            f"{run.agent_id}: {frac} = {run.pass_rate:.2f} "
            f"(threshold {run.threshold:.2f}) -> {'GREEN' if run.green else 'RED'}"
            f", pass^k={_num(run.pass_k)}, abstain={_num(run.abstain_rate)}"
            f", bound={_num(run.upper_error_bound, 3)}"
        )
        return 0 if run.green else 1

    b = cfg.backends
    if args.cmd == "audit" and b.audit.kind != "chain":
        print(
            "refused: audit verify reads a chain audit (backends.audit.kind: chain)",
            file=sys.stderr,
        )
        return 2
    if b.store.kind == "memory":
        # The memory store lives inside one running process; a separate CLI process cannot reach it, so
        # claiming "stopped" here would be a lie. Use App.limits.stop() in-process until Postgres arrives.
        what = "audit verify" if args.cmd == "audit" else "the kill switch"
        print(
            f"refused: {what} needs a shared store (Postgres). With the memory store, "
            "use the running process's app (app.limits, app.audit).",
            file=sys.stderr,
        )
        return 2
    try:
        secrets = make("secrets", b.secrets)
        # Same start-up probe as app.build: a missing DSN is a clean ConfigError, not a KeyError mid-build.
        platform_secrets.check(secrets, [b.signer, b.anchor, b.store, b.audit], set())
        signer = make("signer", b.signer, secrets)
        anchor = make("anchor", b.anchor, secrets)
        store = make("store", b.store, secrets)
        audit = make("audit", b.audit, secrets, store=store, signer=signer, anchor=anchor)
    except StoreUnavailable:
        if args.cmd == "audit":
            print("could not verify: the store is unreachable", file=sys.stderr)
            return 3
        print(
            f"kill switch NOT {'set' if args.action == 'stop' else 'reset'}: the store is unreachable. "
            "Nothing was changed. Fix the store, then run the same command again.",
            file=sys.stderr,
        )
        return 4
    except ConfigError as exc:
        if args.cmd != "audit":
            raise
        # An unreachable or un-migrated store is not evidence of tampering: never exit 1 for it.
        print(f"could not verify: {exc}", file=sys.stderr)
        return 3
    if args.cmd == "audit":
        return audit_verify(audit)
    return _limits(cfg, reg, secrets, store, audit, args)


def _limits(cfg, reg, secrets, store, audit, args) -> int:
    """`limits stop|reset|status|whois`. The stop goes through the stopper login and the reset through the reset
    login, each resolved here and nowhere else; the runtime never reads those two credential names."""
    b, lim = cfg.backends, cfg.limits
    label_key = None
    if lim.label_key_secret_name:
        try:
            label_key = secrets.get(lim.label_key_secret_name).encode("utf-8")
        except Exception:  # noqa: BLE001 - a stop must work without the key (it falls back to a fixed label)
            label_key = b""
    elif cfg.environment != "dev":
        # No key name configured outside dev: the stop still works (fixed "actor not identified" label); reset and
        # whois refuse because the key is unusable. `Limits` would otherwise raise here, outside the exit codes.
        label_key = b""

    def on_login(ref: str):
        return make("store", b.store.model_copy(update={"dsn_secret_name": ref}), secrets)

    stop_store = reset_store = None
    try:
        if args.action == "stop":
            if b.store.stop_credential_ref:
                stop_store = on_login(b.store.stop_credential_ref)
            else:
                print(
                    "warning: store.stop_credential_ref is not set; stopping through the runtime login",
                    file=sys.stderr,
                )
        elif args.action in ("reset", "check") and b.store.reset_credential_ref:
            reset_store = on_login(b.store.reset_credential_ref)
    except StoreUnavailable as exc:
        return _kill_switch_store_down(args.action, exc)
    limits = Limits(
        store,
        audit,
        reg,
        environment=cfg.environment,
        stop_store=stop_store,
        reset_store=reset_store,
        reset_names=lim.reset_names,
        label_key=label_key,
        key_id=lim.key_id,
    )
    if args.action == "check":
        return _limits_check(cfg, reset_store)
    return kill_switch(
        limits,
        args.action,
        args.by if args.action != "whois" else args.name,
        expect_version=args.expect_version,
        expect_open=args.expect_open,
    )


def _limits_check(cfg, store) -> int:
    """`limits check`: the full guard report for the configured roles, read through the reset login. Exit 0 no
    findings, 10 findings, 7 the database was busy (nothing known)."""
    from hadavin_sdk.runtime import stop_state

    if store is None:
        print(
            "check needs store.reset_credential_ref (the operator's reset login)", file=sys.stderr
        )
        return 2
    lim = cfg.limits
    result = stop_state.probe(
        store,
        environment=cfg.environment,
        runtime_role=lim.runtime_role,
        stop_role=lim.stop_role,
        reset_group=lim.reset_group,
    )
    if result.status == stop_state.INCONCLUSIVE:
        print(
            "check inconclusive: the store is busy. Nothing is known; run it again.",
            file=sys.stderr,
        )
        return 7
    for problem in result.problems:
        print(f"problem: {problem}")
    print(
        "guard OK"
        if result.status == stop_state.OK
        else f"guard FAILED: {len(result.problems)} problem(s)"
    )
    return 0 if result.status == stop_state.OK else 10


def _k1b(cfg, reg, args) -> int:
    from hadavin_sdk.k1b.audit_sink import build_audit

    secrets = make("secrets", cfg.backends.secrets)
    audit, warnings = build_audit(cfg, secrets)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if args.cmd == "score":
        return score_cmd(audit, args)
    llm = make("llm", cfg.backends.llm, secrets, routes=cfg.routes)
    detector = combine([make("detector", d, secrets, llm=llm) for d in cfg.backends.detector])
    return replay_cmd(reg, llm, detector, audit, args)


def replay_cmd(reg, llm, detector, audit, args) -> int:
    """Body of ``replay`` (takes the audit so tests can pass their own). Returns the exit code."""
    from hadavin_sdk.k1b.replay import replay

    res = replay(
        reg,
        llm,
        detector,
        audit,
        agent_id=args.agent,
        bundles_dir=args.bundles,
        cause_list_dir=args.cause_list,
        k=args.k,
        max_usd=args.max_usd,
        out=args.out,
        llm_kind=reg.config.backends.llm.kind,
        acknowledge_masked=getattr(args, "i_know_data_is_already_masked", False),
    )
    print(f"replay {res.result}: outputs in {res.out} (see replay-report.md)")
    return res.exit_code


def score_cmd(audit, args) -> int:
    """Body of ``score``. Order: intent event (a failed append writes nothing), the report file, then
    ``written`` and one ``score_run`` per run. A report that cannot be written leaves ``score_report`` ``started`` followed by
    ``score_report`` ``failed``; a crash leaves ``started`` alone."""
    from hadavin_sdk.k1b.atomic import atomic_write
    from hadavin_sdk.k1b.report import render_score_report
    from hadavin_sdk.k1b.score import REPORT_DIR, audit_result, score

    report_dir = Path(args.outputs) / REPORT_DIR
    if report_dir.exists() and (not report_dir.is_dir() or any(report_dir.iterdir())):
        raise ConfigError("score report folder exists and is not empty")
    res = score(args.outputs, args.answers, args.cause_list, args.bundles)
    run_id = new_id("k1b")
    ref = {"object_ref": res.answers_sha256, "inputs_hash": res.outputs_digest}
    audit.emit("score_report", run_id, **ref, result="started")
    try:
        # NOSONAR S8707: the operator's own --outputs folder; a CLI argument is not attacker input
        report_dir.mkdir(exist_ok=True)  # NOSONAR
        atomic_write(report_dir / "score-report.md", render_score_report(res))
    except Exception as exc:
        audit.emit_outcome(
            "score_report", run_id, **ref, result="failed", error_code=type(exc).__name__
        )
        raise
    # Raising appends: a lost event is a failed command (exit 3), with the report already on disk.
    audit.emit("score_report", run_id, **ref, result="written")
    for run in res.runs:
        audit.emit("score_run", run_id, **ref, decision="-", result=audit_result(run))
    print(f"score report written: {report_dir / 'score-report.md'}")
    return 0


def _tick() -> int:
    """Build the app with every qualified agent (an unqualified one must not stop approvals expiring)."""
    from hadavin_sdk.app import build
    from hadavin_sdk.runtime.agent_loop import Unqualified, assert_qualified
    from hadavin_sdk.runtime.tick import run_tick

    # The summary line and step errors go to stderr (the logger is otherwise silent below WARNING).
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(message)s")
    try:
        reg = load_registry(load_config())
        agents = []
        for agent_id in reg.agents:
            try:
                assert_qualified(reg, agent_id)
                agents.append(agent_id)
            except Unqualified:
                print(
                    f"tick: {agent_id} is not qualified; its new runs are refused", file=sys.stderr
                )
        app = build(None, agents)
    except StoreUnavailable as exc:
        print(f"tick: {exc}", file=sys.stderr)
        return 4
    except ConfigError as exc:
        print(f"tick: config error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - any other start-up failure is a config error, never "1"
        print(f"tick: config error: {type(exc).__name__}", file=sys.stderr)
        return 2
    return run_tick(app)


def _migrate(
    cfg,
    runtime_role: str | None,
    portal_role: str | None = None,
    purge_role: str | None = None,
    *,
    reset_role: str | None = None,
    stop_role: str | None = None,
) -> int:
    store = cfg.backends.store
    if store.kind != "postgres":
        print(
            f"refused: migrate is for the postgres store; this config uses {store.kind!r}",
            file=sys.stderr,
        )
        return 2
    group = cfg.limits.reset_group
    if reset_role and group and reset_role != group:
        print(
            f"refused: --reset-role {reset_role!r} differs from limits.reset_group {group!r}; config is the one source",
            file=sys.stderr,
        )
        return 2
    reset_role = reset_role or group
    if not reset_role:
        print("refused: give --reset-role or set limits.reset_group", file=sys.stderr)
        return 2
    dsn = os.environ.get("HADAVIN_MIGRATE_DSN")
    if not dsn:
        print("refused: set HADAVIN_MIGRATE_DSN to the migration role's DSN", file=sys.stderr)
        return 2
    from hadavin_sdk.store.migrate import migrate
    from hadavin_sdk.store.postgres import ca_file

    ca = ca_file(store, make("secrets", cfg.backends.secrets).get)
    applied = migrate(
        dsn,
        runtime_role=runtime_role,
        portal_role=portal_role,
        purge_role=purge_role,
        reset_role=reset_role,
        stop_role=stop_role,
        max_open_stop_requests=cfg.limits.max_open_stop_requests,
        lock_timeout_ms=cfg.limits.migrate_lock_timeout_ms,
        iam_auth=store.iam_auth,
        region=store.region,
        sslmode=store.sslmode,
        sslrootcert=ca,
    )
    print(f"applied: {', '.join(applied) or 'nothing (up to date)'}")
    if applied and not runtime_role:
        print(
            "warning: new tables have no runtime grants; run again with --runtime-role <role>",
            file=sys.stderr,
        )
    return 0


def audit_verify(audit) -> int:
    """Recompute the chain, every checkpoint signature and every anchor. Exit 0 intact, 1 not intact,
    3 when the audit or its anchors cannot be read (an outage is not evidence of tampering)."""
    result = audit.verify()
    if result.unreadable:
        print(f"could not verify: {'; '.join(result.problems)}")
        return 3
    print(
        f"{result.rows} rows, signed through row {result.signed_through} "
        f"({result.unsigned_tail} not signed yet)"
    )
    for problem in result.problems:
        print(f"PROBLEM: {problem}")
    print("intact" if result.ok else "NOT intact")
    return 0 if result.ok else 1


def _kill_switch_store_down(what: str, exc: BaseException) -> int:
    """4 when the store cannot be reached; 7 when it is busy (NOT done, retry); 2 when it answers but is not ready
    (missing table or grant)."""
    if isinstance(exc, StoreBusy):
        verb = {"set": "stop", "reset": "reset"}.get(what, what)
        print(
            f"{verb} NOT done: the store is busy (a lock or statement timeout, a deadlock or the connection limit). "
            "Nothing was changed. Run the same command again; if it keeps failing, use the database "
            "administrator recipe in docs/stop-state-runbook.md.",
            file=sys.stderr,
        )
        return 7
    if is_connectivity_error(exc):
        print(
            f"kill switch NOT {what}: the store is unreachable. Nothing was changed. "
            "Fix the store, then run the same command again.",
            file=sys.stderr,
        )
        return 4
    print(
        f"kill switch NOT {what}: the store answered with an error ({type(exc).__name__}); run "
        "hadavin-sdk migrate and check the runtime role's grants. Nothing was changed.",
        file=sys.stderr,
    )
    return 2


def _print_status(state) -> None:
    print(
        f"kill switch {'ON' if state.on else 'OFF'} (by {state.by}) since {state.ts.isoformat()}; "
        f"version {state.version}, open_requests {state.open_requests}"
    )


def kill_switch(
    limits: Limits,
    action: str,
    by: str,
    *,
    expect_version: int | None = None,
    expect_open: int | None = None,
) -> int:
    """Run stop/reset/status/whois for a caller (the CLI once a shared store exists, or an in-process admin hook).

    Exit codes: 0 done; 2 usage; 3 reset refused because the audit store is unavailable (the switch stays ON);
    4 the store is unreachable (the switch was NOT changed); 7 the store is busy (NOT done); 10 `check` found problems; 5 not permitted (the name, the credential or the
    database refused); 6 the stops changed since they were read, or the switch row is missing; 9 the database is
    not migrated.
    """
    if action == "whois":
        try:
            print(limits.label(by))
        except StopNotPermitted as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 5
        return 0
    if action == "status":
        try:
            _print_status(limits.status())
        except Exception as exc:  # noqa: BLE001 - classified below
            return _kill_switch_store_down("read", exc)
        return 0
    if action == "stop":
        try:
            state = limits.stop(by)
        except AuditUnavailable:
            raise
        except NotMigrated:
            print(
                "database not migrated; use the DBA stop recipe (docs/stop-state-runbook.md)",
                file=sys.stderr,
            )
            return 9
        except Exception as exc:  # noqa: BLE001 - classified below
            return _kill_switch_store_down("set", exc)
        print(f"kill switch ON (by {state.by})")
        return 0
    if expect_version is None or expect_open is None:
        print(
            "reset needs --expect-version and --expect-open (read them with `limits status`)",
            file=sys.stderr,
        )
        return 2
    try:
        state = limits.reset(by, expect_version=expect_version, expect_open=expect_open)
    except AuditUnavailable:
        print(
            "refused: the audit store is unavailable, so the reset cannot be recorded. "
            "The kill switch stays ON. Fix the audit store, then try again.",
            file=sys.stderr,
        )
        return 3
    except StopNotPermitted as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 5
    except SwitchChanged as exc:
        print(f"reset NOT done: {exc}", file=sys.stderr)
        return 6
    except NotMigrated:
        print(
            "database not migrated; use the DBA stop recipe (docs/stop-state-runbook.md)",
            file=sys.stderr,
        )
        return 9
    except Exception as exc:  # noqa: BLE001 - classified below
        return _kill_switch_store_down("reset", exc)
    try:  # a stop can land while the reset commits: read once more and say so
        now_state = limits.status()
    except Exception:  # noqa: BLE001 - the reset happened; only the second read failed
        print(f"reset done (version {state.version}); the status could not be read again")
        return 0
    if now_state.on:
        print(
            f"reset done (version {state.version}); the switch is still ON: "
            f"{now_state.open_requests} stop request(s) arrived during the reset"
        )
    else:
        print(f"kill switch OFF (version {state.version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
