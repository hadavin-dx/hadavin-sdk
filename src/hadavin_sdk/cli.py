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
from hadavin_sdk.backends import make, platform_secrets
from hadavin_sdk.config import load_config
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.guard.injection import combine
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import new_id
from hadavin_sdk.registry import load_registry
from hadavin_sdk.store.protocol import StoreUnavailable, is_connectivity_error


def _num(x: float | None, places: int = 2) -> str:
    return "-" if x is None else f"{x:.{places}f}"


def _positive(text: str) -> int:
    k = int(text)
    if k < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return k


def _day(text: str):
    from datetime import date

    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a date, YYYY-MM-DD") from None


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
    lim.add_argument("action", choices=["stop", "reset"])
    lim.add_argument("--by", required=True)
    sub.add_parser("tick", help="one pass of the housekeeping steps (run every 30-60 s)")
    mig = sub.add_parser("migrate", help="apply the postgres store schema (migration role)")
    mig.add_argument("--runtime-role", help="grant this database role what the runtime needs")
    mig.add_argument(
        "--maintenance-role",
        help="grant this database role DELETE and UPDATE (usd) on the spend counters only (prune-runs, release-reservation)",
    )
    mig.add_argument(
        "--portal-role", help="grant this database role SELECT on the portal's relations only"
    )
    prn = sub.add_parser(
        "prune-runs",
        help="delete old per-run spend counters (maintenance role; HADAVIN_MAINTENANCE_DSN)",
    )
    prn.add_argument("--keep-days", type=_positive, default=7)
    rel = sub.add_parser(
        "release-reservation",
        help="take a stranded reservation back from one agent's day and month counters (maintenance role)",
    )
    rel.add_argument("--agent", required=True, help="the agent id")
    rel.add_argument(
        "--day", required=True, type=_day, help="the day it was booked, YYYY-MM-DD (UTC)"
    )
    rel.add_argument("--amount", required=True, type=_money, help="USD to take back")
    rel.add_argument("--dry-run", action="store_true", help="only show the totals")
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
    cfg = load_config()
    if args.cmd == "migrate":
        return _migrate(cfg, args.runtime_role, args.portal_role, args.maintenance_role)
    if args.cmd == "prune-runs":
        return _prune_runs(cfg, args.keep_days)
    if args.cmd == "release-reservation":
        return _release_reservation(cfg, args)
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
    return kill_switch(Limits(store, audit, reg), args.action, args.by)


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


def _release_reservation(cfg, args) -> int:
    store = cfg.backends.store
    dsn = os.environ.get("HADAVIN_MAINTENANCE_DSN")
    if store.kind != "postgres" or not dsn:
        print(
            "refused: release-reservation needs the postgres store and HADAVIN_MAINTENANCE_DSN "
            "(the maintenance role's DSN, never the runtime's)",
            file=sys.stderr,
        )
        return 2
    from hadavin_sdk.store.migrate import release_reservation
    from hadavin_sdk.store.postgres import ca_file

    ca = ca_file(store, make("secrets", cfg.backends.secrets).get)
    try:
        before, after = release_reservation(
            dsn,
            args.agent,
            args.day,
            args.amount,
            tenant=cfg.tenant,
            dry_run=args.dry_run,
            iam_auth=store.iam_auth,
            region=store.region,
            sslmode=store.sslmode,
            sslrootcert=ca,
        )
    except StoreUnavailable:
        print(
            "failed: StoreUnavailable. If the maintenance role was created before this release it lacks "
            "UPDATE (usd) on the spend tables: re-run `hadavin-sdk migrate --maintenance-role <role>` "
            "(set HADAVIN_DEBUG=1 for the traceback)",
            file=sys.stderr,
        )
        if os.environ.get("HADAVIN_DEBUG") == "1":
            traceback.print_exc()
        return 3
    verb = "would release" if args.dry_run else "released"
    print(
        f"{verb} up to {args.amount} USD for {args.agent} on {args.day}: "
        f"day {before[0]} -> {after[0]}, month {before[1]} -> {after[1]}"
    )
    return 0


def _prune_runs(cfg, keep_days: int) -> int:
    store = cfg.backends.store
    dsn = os.environ.get("HADAVIN_MAINTENANCE_DSN")
    if store.kind != "postgres" or not dsn:
        print(
            "refused: prune-runs needs the postgres store and HADAVIN_MAINTENANCE_DSN "
            "(the maintenance role's DSN, never the runtime's)",
            file=sys.stderr,
        )
        return 2
    from hadavin_sdk.store.migrate import prune_run_counters
    from hadavin_sdk.store.postgres import ca_file

    ca = ca_file(store, make("secrets", cfg.backends.secrets).get)
    n = prune_run_counters(
        dsn,
        keep_days,
        iam_auth=store.iam_auth,
        region=store.region,
        sslmode=store.sslmode,
        sslrootcert=ca,
    )
    print(f"pruned: {n} run counter rows")
    return 0


def _migrate(
    cfg,
    runtime_role: str | None,
    portal_role: str | None = None,
    maintenance_role: str | None = None,
) -> int:
    store = cfg.backends.store
    if store.kind != "postgres":
        print(
            f"refused: migrate is for the postgres store; this config uses {store.kind!r}",
            file=sys.stderr,
        )
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
        maintenance_role=maintenance_role,
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
    """4 when the store cannot be reached; 2 when it answers but is not ready (missing table or grant)."""
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


def kill_switch(limits: Limits, action: str, by: str) -> int:
    """Run stop/reset for a caller (the CLI once a shared store exists, or an in-process admin hook).

    Exit codes: 0 done; 3 reset refused because the audit store is unavailable (the switch stays ON); 4 the
    store is unreachable (the switch was NOT changed).
    """
    if action == "stop":
        try:
            limits.stop(by)
        except AuditUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001 - classified below
            return _kill_switch_store_down("set", exc)
        print(f"kill switch ON (by {by})")
        return 0
    try:
        limits.reset(by)
    except AuditUnavailable:
        print(
            "refused: the audit store is unavailable, so the reset cannot be recorded. "
            "The kill switch stays ON. Fix the audit store, then try again.",
            file=sys.stderr,
        )
        return 3
    except Exception as exc:  # noqa: BLE001 - classified below
        return _kill_switch_store_down("reset", exc)
    print(f"kill switch OFF (by {by})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
