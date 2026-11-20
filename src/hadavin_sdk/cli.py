"""hadavin-sdk CLI.

  hadavin-sdk [--config DIR] gate <agent> [--k K] [--max-usd X]
                                                         exit 0 when green, 1 when below the threshold;
                                                         --k K runs each item K times (pass^k), default 1;
                                                         --max-usd X caps the cost of this invocation (needed in
                                                         pilot and prod; demo: the agent's daily budget);
                                                         cap reached or call refused: exit 2
  hadavin-sdk [--config DIR] limits stop|reset --by WHO  needs a shared store (postgres); memory: exit 2;
                                                         reset logs in as the reset role (the secret named by
                                                         backends.store.reset_credential_ref); pilot and prod
                                                         without it: exit 2
  hadavin-sdk [--config DIR] release-expired AGENT --day YYYY-MM-DD --by WHO
                                                         lower the EXPIRED spend holds of one agent and day (audited
                                                         first); logs in as the release role (the secret named by
                                                         backends.store.release_credential_ref); exit 0 done, 2
                                                         refused or rights missing, 3 audit unavailable, 4 store down
  hadavin-sdk [--config DIR] tick                       one pass of approvals sweep, reconcile, stuck runs,
                                                         audit checkpoint, evidence purge, source re-probe,
                                                         audit drain; exit 0 ok, 1 a step failed,
                                                         2 config error, 4 store unreachable
  hadavin-sdk [--config DIR] migrate [--runtime-role R] [--portal-role P] [--purge-role U] [--reset-role X]
                                                         [--release-role Y] [--accept-admin-role A ...] [--no-roles]
                                                         apply the postgres schema; the migration role's DSN
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
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from hadavin_sdk import evals
from hadavin_sdk.audit import AuditUnavailable
from hadavin_sdk.backends import platform_secrets
from hadavin_sdk.backends.factory import make
from hadavin_sdk.config import load_config
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.guard.injection import combine
from hadavin_sdk.guard.model_gate import GateRefused
from hadavin_sdk.limits import Limits, SpendRefused
from hadavin_sdk.models import AuditEvent, audit_code, new_id
from hadavin_sdk.registry import load_registry
from hadavin_sdk.secret_name import collides, path_form_problem
from hadavin_sdk.stages import is_live
from hadavin_sdk.store.protocol import StoreUnavailable, check_spend_cap, is_connectivity_error


def _num(x: float | None, places: int = 2) -> str:
    return "-" if x is None else f"{x:.{places}f}"


def _day(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a date YYYY-MM-DD: {text!r}") from None


def _positive(text: str) -> int:
    k = int(text)
    if k < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return k


def _cap(text: str) -> Decimal:
    """A spend cap: a finite number, 0 or more (the caps table accepts zero; a zero cap refuses every run)."""
    try:
        d = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError("must be a decimal number") from None
    try:
        return check_spend_cap(d)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def _money(text: str) -> Decimal:
    try:
        d = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError("must be a decimal number") from None
    if not d.is_finite() or d <= 0:
        raise argparse.ArgumentTypeError("must be a finite number above zero")
    return d


def _unreleased_range() -> str:
    try:  # migrate needs the postgres extra; the help must work without it
        from hadavin_sdk.store.migrate import UNRELEASED_MIGRATIONS
    except ImportError:
        return "the unreleased ones"

    nums = sorted(v[:4] for v in UNRELEASED_MIGRATIONS)
    return f"{nums[0]}-{nums[-1]}" if nums else "none now"


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
    g.add_argument(
        "--max-usd",
        type=_money,
        default=None,
        help="total cost cap for this invocation (needed in pilot and prod)",
    )
    lim = sub.add_parser("limits", help="kill switch and per-agent spend caps")
    lim_sub = lim.add_subparsers(dest="action", required=True)
    for action in ("stop", "reset"):  # unchanged: `limits stop|reset --by WHO`
        lim_sub.add_parser(action, help=f"kill switch: {action}").add_argument(
            "--by", required=True
        )
    sc_p = lim_sub.add_parser(
        "set-cap", help="write the day and month spend cap of one agent (reset login, audited)"
    )
    sc_p.add_argument("agent")
    sc_p.add_argument("--day", required=True, type=_cap, help="the daily cap in USD, 0 or more")
    sc_p.add_argument("--month", required=True, type=_cap, help="the monthly cap in USD, 0 or more")
    sc_p.add_argument("--by", required=True)
    sc_p.add_argument(
        "--yes", action="store_true", help="skip the confirmation (needed when not interactive)"
    )
    sy_p = lim_sub.add_parser(
        "sync-caps",
        help="write the registry caps of every live and draft agent into the caps table (reset login, audited)",
    )
    sy_p.add_argument("--by", required=True)
    sy_p.add_argument(
        "--yes", action="store_true", help="skip the confirmation (needed when not interactive)"
    )
    lim_sub.add_parser(
        "check-caps",
        help="exit 1 when a registry cap differs from the caps table or a row is missing",
    )
    rel = sub.add_parser(
        "release-expired", help="lower the expired spend holds of one agent and day (release role)"
    )
    rel.add_argument("agent")
    rel.add_argument("--day", required=True, type=_day, help="the booking day, YYYY-MM-DD")
    rel.add_argument("--by", required=True)
    sub.add_parser("tick", help="one pass of the housekeeping steps (run every 30-60 s)")
    mig = sub.add_parser("migrate", help="apply the postgres store schema (migration role)")
    mig.add_argument("--runtime-role", help="grant this database role what the runtime needs")
    mig.add_argument(
        "--no-roles",
        action="store_true",
        help="apply the schema naming no role (no role is granted or checked; do NOT use it on an existing deployment: old grants stay and nothing is checked); without it a migrate that names no role is refused",
    )
    mig.add_argument(
        "--purge-role",
        help="grant this database role the evidence purge (DELETE on tool_calls and redaction_maps) and nothing else",
    )
    mig.add_argument(
        "--release-role",
        help="grant this database role the release of expired spend holds (one function and the audit append) and nothing else",
    )
    mig.add_argument(
        "--portal-role", help="grant this database role SELECT on the portal's relations only"
    )
    mig.add_argument(
        "--reset-role",
        help="grant this database role the kill switch reset (clear stops, write the reset to the audit) and nothing else",
    )
    mig.add_argument(
        "--accept-admin-role",
        action="append",
        default=[],
        help="below PostgreSQL 16: a CREATEROLE role you vouch for (it cannot grant the reset role to itself); "
        "repeat for several; named in the output and logged; never excuses a grant on the stop tables",
    )
    mig.add_argument(
        "--accept-changed-draft",
        action="append",
        default=[],
        help=f"an UNRELEASED migration ({_unreleased_range()}) whose file changed but whose database already matches it: record "
        "the file's checksum; repeat for several",
    )
    mig.add_argument(
        "--reset-draft",
        help="an UNRELEASED migration: delete its ledger row and every later one, then apply again (drop what the "
        "draft made first); refused for a released migration",
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
    cfg = load_config()
    if args.cmd == "migrate":
        return _migrate(
            cfg,
            args.runtime_role,
            args.portal_role,
            args.purge_role,
            args.reset_role,
            args.release_role,
            args.no_roles,
            tuple(args.accept_admin_role),
            tuple(args.accept_changed_draft),
            args.reset_draft,
        )
    if args.cmd == "release-expired":  # its own path: it must never reach limits.reset below
        return release_expired_cmd(cfg, args.agent, args.day, args.by)
    if (
        args.cmd == "limits" and args.action in _CAP_ACTIONS
    ):  # reset login only, never the kill switch
        return caps_cmd(cfg, args)
    reg = load_registry(cfg)
    if args.cmd in (
        "replay",
        "score",
    ):  # before the memory-store refusal below: K1b needs no shared store
        return _k1b(cfg, reg, args)

    if args.cmd == "gate":
        b = cfg.backends
        try:
            run = evals.gate(
                reg,
                make("llm", b.llm, make("secrets", b.secrets), routes=cfg.routes),
                args.agent,
                k=args.k,
                max_usd=args.max_usd,
            )
        except (
            SpendRefused
        ) as exc:  # the cap (usd_cap) or an amount no meter books: no call was made
            print(f"gate stopped: {exc.reason}", file=sys.stderr)
            return 2
        except GateRefused as exc:
            print(f"gate stopped: {exc.code}", file=sys.stderr)
            return 2
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
    reset_ref = None
    if args.cmd == "limits" and args.action == "reset":
        reset_ref = getattr(b.store, "reset_credential_ref", None)
        if not reset_ref and is_live(cfg.environment):
            # Before any connection or write: in pilot and prod the runtime login must not be the one that resets.
            print(
                f"refused: limits reset in {cfg.environment} needs the reset role's login. Create the reset role, "
                "run hadavin-sdk migrate --reset-role <role>, then set backends.store.reset_credential_ref to the "
                "name of the secret that holds its DSN. The kill switch was not changed.",
                file=sys.stderr,
            )
            return 2
        if reset_ref and path_form_problem(reset_ref, _file_backed(b)):
            print(
                "refused: backends.store.reset_credential_ref is a path-shaped name (a '.' or '..' segment, or "
                "for a mounted_file folder a leading or trailing '/'), which cannot be compared with the runtime "
                "login. Write a plain secret name. The kill switch was not changed.",
                file=sys.stderr,
            )
            return 2
        if (
            reset_ref
            and b.store.dsn_secret_name
            and collides(reset_ref, [b.store.dsn_secret_name], file_backed=_file_backed(b))
        ):
            # Before any connection: the reset must not run on the runtime's own login.
            print(
                "refused: backends.store.reset_credential_ref names the same secret as "
                "backends.store.dsn_secret_name, so the reset would run on the runtime login. Point it at the "
                "secret that holds the reset role's DSN. The kill switch was not changed.",
                file=sys.stderr,
            )
            return 2
    try:
        secrets = make("secrets", b.secrets)
        if reset_ref and _same_login(secrets, reset_ref, [b.store.dsn_secret_name]):
            print(
                "refused: backends.store.reset_credential_ref holds the same login as "
                "backends.store.dsn_secret_name (two names, one DSN), so the reset would run on the runtime "
                "login. Point it at the secret that holds the reset role's own DSN. The kill switch was not changed.",
                file=sys.stderr,
            )
            return 2
        if reset_ref:
            # The reset role's own login for the store and the audit row. It signs and anchors nothing (it may
            # not write a checkpoint); the tick does that under the runtime login.
            as_reset = b.store.model_copy(
                update={"dsn_secret_name": reset_ref, "purge_dsn_secret_name": None}
            )
            platform_secrets.check(secrets, [as_reset, b.audit], set())
            as_reset._login_role = (
                "reset"  # the reset login is not held to the runtime's rights at start
            )
            store = make("store", as_reset, secrets)
            audit = make("audit", b.audit, secrets, store=store, signer=None, anchor=None)
        else:
            # Same start-up probe as app.build: a missing DSN is a clean ConfigError, not a KeyError mid-build.
            platform_secrets.check(secrets, [b.signer, b.anchor, b.store, b.audit], set())
            signer = make("signer", b.signer, secrets)
            anchor = make("anchor", b.anchor, secrets)
            own = b.store.model_copy()
            if args.cmd == "limits" and args.action == "reset":
                # Demo without a reset ref: the one configured login does the reset (whichever it is; a runtime
                # login is refused by the database). It is not held to the runtime's rights at start.
                own._login_role = "reset"
            store = make("store", own, secrets)
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
    from hadavin_sdk.runtime.agent_loop import qualified_agents
    from hadavin_sdk.runtime.tick import run_tick

    # The summary line and step errors go to stderr (the logger is otherwise silent below WARNING).
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(message)s")
    try:
        reg = load_registry(load_config())
        agents = qualified_agents(
            reg,
            lambda agent_id: print(
                f"tick: {agent_id} is not qualified; its new runs are refused", file=sys.stderr
            ),
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


def _say(text: str) -> None:
    """print to stdout for a name the terminal cannot encode (escaped) and for a stdout that is broken or closed:
    never an error, so exit codes stay 0 or 2."""
    enc = getattr(sys.stdout, "encoding", None) or "ascii"
    try:
        print(text.encode(enc, "backslashreplace").decode(enc))
    except (OSError, ValueError):  # broken pipe or closed stdout: the exit code stays 0 or 2
        pass


def _migrate(
    cfg,
    runtime_role: str | None,
    portal_role: str | None = None,
    purge_role: str | None = None,
    reset_role: str | None = None,
    release_role: str | None = None,
    no_roles: bool = False,
    accepted_admin_roles: tuple[str, ...] = (),
    accept_changed_draft: tuple[str, ...] = (),
    reset_draft: str | None = None,
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
    if not no_roles and not any((runtime_role, portal_role, purge_role, reset_role, release_role)):
        print(
            "refused: no role is named, so the check of who could clear a stop would be skipped; name the "
            "roles (--runtime-role ... --reset-role) in ONE command, or pass --no-roles to apply the schema only",
            file=sys.stderr,
        )
        return 2
    from hadavin_sdk.store.migrate import migrate
    from hadavin_sdk.store.postgres import ca_file

    ca = ca_file(store, make("secrets", cfg.backends.secrets).get)
    notes: list[str] = []
    try:
        applied = migrate(
            dsn,
            runtime_role=runtime_role,
            portal_role=portal_role,
            purge_role=purge_role,
            reset_role=reset_role,
            release_role=release_role,
            no_roles=no_roles,
            accepted_admin_roles=accepted_admin_roles,
            accept_changed_draft=accept_changed_draft,
            reset_draft=reset_draft,
            iam_auth=store.iam_auth,
            region=store.region,
            sslmode=store.sslmode,
            sslrootcert=ca,
            notes=notes,
            on_role_change=lambda note: print(f"changed: {note}", file=sys.stderr),
        )
    finally:  # printed on a refusal too: the CI log is the record of who vouched
        for note in notes:
            _say(note)
    _say(f"applied: {', '.join(applied) or 'nothing (up to date)'}")
    if applied and not runtime_role:
        print(
            "warning: new tables have no runtime grants; run again with --runtime-role <role>",
            file=sys.stderr,
        )
    if runtime_role and not reset_role:
        print(
            "warning: no reset role was named, so nobody but the owner can reset the kill switch; run again "
            "with --reset-role <role>",
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


def _file_backed(b) -> bool:
    """The secrets kind is mounted_file: a name is a path there."""
    return getattr(b.secrets, "kind", None) == "mounted_file"


def _same_login(secrets, ref: str, others) -> bool:
    """True when the secret ``ref`` holds the same value as one of ``others`` (two names, one login). A name that
    cannot be read is not the same: the start-up probe reports it with its own message."""
    try:
        mine = secrets.get(ref)
        return any(secrets.get(n) == mine for n in others if n)
    except Exception:  # noqa: BLE001 - an unreadable secret is reported by platform_secrets.check
        return False


def _kill_switch_store_down(what: str, exc: BaseException) -> int:
    """4 when the store cannot be reached; 2 when it answers but is not ready (missing table or grant)."""
    if is_connectivity_error(exc):
        # After the intent row was written the connection may drop at any point, so a reset may have landed.
        certain = (
            "Nothing was changed."
            if what != "reset"
            else "The connection was lost while the reset ran, so it may or may not have been applied: treat "
            "the kill switch as ON until a read shows OFF."
        )
        print(
            f"kill switch NOT {what}: the store is unreachable. {certain} "
            "Fix the store, then run the same command again.",
            file=sys.stderr,
        )
        return 4
    print(
        f"kill switch NOT {what}: the store answered with an error ({type(exc).__name__}); run "
        "hadavin-sdk migrate and check the runtime role's grants"
        + (
            " (a reset needs the reset role: migrate --reset-role and backends.store.reset_credential_ref)"
            if what == "reset"
            else ""
        )
        + ". Nothing was changed.",
        file=sys.stderr,
    )
    return 2


def release_expired_cmd(cfg, agent: str, day: date, by: str) -> int:
    """`release-expired`: lower the EXPIRED spend holds of one agent and one day, logged in as the release role.
    Its own function and its own exit codes; it shares nothing with `kill_switch`. Refusals come before any
    connection. Exit 0 done (also 0 rows), 2 refused (config, or the login lacks the right), 3 the audit store is
    unavailable (nothing changed), 4 the store is unreachable (nothing changed)."""
    b = cfg.backends
    if b.store.kind != "postgres":
        print(
            "refused: release-expired needs the postgres store (the memory store lives in one process)",
            file=sys.stderr,
        )
        return 2
    ref = getattr(b.store, "release_credential_ref", None)
    if not ref:
        print(
            "refused: release-expired needs the release role's login. Create the release role, run "
            "hadavin-sdk migrate --release-role <role>, then set backends.store.release_credential_ref to the "
            "name of the secret that holds its DSN. Nothing was changed.",
            file=sys.stderr,
        )
        return 2
    others_names = [
        n
        for n in (
            getattr(b.store, "dsn_secret_name", None),
            getattr(b.store, "reset_credential_ref", None),
            getattr(b.store, "purge_dsn_secret_name", None),
        )
        if n
    ]
    if path_form_problem(ref, _file_backed(b)):
        print(
            "refused: backends.store.release_credential_ref is a path-shaped name (a '.' or '..' segment, or for "
            "a mounted_file folder a leading or trailing '/'), which cannot be compared with the other logins. "
            "Write a plain secret name. Nothing was changed.",
            file=sys.stderr,
        )
        return 2
    if collides(ref, others_names, file_backed=_file_backed(b)):
        print(
            "refused: backends.store.release_credential_ref names the same secret as the runtime, reset or purge "
            "login. Point it at the secret that holds the release role's own DSN. Nothing was changed.",
            file=sys.stderr,
        )
        return 2
    try:
        secrets = make("secrets", b.secrets)
        if _same_login(secrets, ref, others_names):
            print(
                "refused: backends.store.release_credential_ref holds the same login as the runtime, reset or "
                "purge secret (two names, one DSN). Point it at the secret that holds the release role's own "
                "DSN. Nothing was changed.",
                file=sys.stderr,
            )
            return 2
        as_release = b.store.model_copy(
            update={"dsn_secret_name": ref, "purge_dsn_secret_name": None}
        )
        platform_secrets.check(secrets, [as_release, b.audit], set())
        store = make("store", as_release, secrets)
        audit = make("audit", b.audit, secrets, store=store, signer=None, anchor=None)
    except StoreUnavailable:
        print("release NOT run: the store is unreachable. Nothing was changed.", file=sys.stderr)
        return 4
    except (
        ConfigError
    ) as exc:  # e.g. the start-up rights self-check: the release login holds stop-table rights
        print(f"refused: {exc}. Nothing was changed.", file=sys.stderr)
        return 2
    release = getattr(store, "release_expired_spend", None)
    if release is None:
        print("refused: this store cannot release holds", file=sys.stderr)
        return 2
    try:
        done = release(agent, day, by, audit)
    except AuditUnavailable:
        print(
            "refused: the audit store is unavailable, so the release cannot be recorded. Nothing was changed.",
            file=sys.stderr,
        )
        return 3
    except Exception as exc:  # noqa: BLE001 - the class name only
        if is_connectivity_error(exc):
            print(
                "release NOT run: the store is unreachable. Nothing was changed.", file=sys.stderr
            )
            return 4
        print(
            f"release failed ({type(exc).__name__}); nothing was changed. Is this the release role's login "
            "(hadavin-sdk migrate --release-role)?",
            file=sys.stderr,
        )
        return 2
    print(
        f"released {done.reservations} expired hold(s) of {done.agent_id} on {done.day}: {done.released_usd} USD "
        f"requested, {done.applied_usd} USD applied to the day counter "
        f"(day counter now {done.day_usd}, month counter now {done.month_usd}) (by {by})"
    )
    if not done.outcome_audited:
        print(
            "released, but the outcome could NOT be audited: the money counters changed and the audit holds only "
            f"the intent row {done.intent_id}, which has no outcome. Record it by hand (see the runbook).",
            file=sys.stderr,
        )
        return 5
    return 0


_CAP_ACTIONS = ("set-cap", "sync-caps", "check-caps")


def _caps_refusals(cfg, what: str) -> int | None:
    """The refusals of the three cap commands that need no connection (nothing was changed): the postgres store,
    a `reset_credential_ref` (in every environment: the runtime login cannot write a cap, so there is no fallback
    to it), a plain name that is not the runtime, purge or release secret. 2 when refused, else None."""
    b = cfg.backends
    if b.store.kind != "postgres":
        print(
            f"refused: {what} needs the postgres store: this store has no cap table (the memory store compares "
            "the caps a caller passes). Nothing was changed.",
            file=sys.stderr,
        )
        return 2
    ref = getattr(b.store, "reset_credential_ref", None)
    if not ref:
        print(
            f"refused: {what} needs the reset role's login, in every environment. Create the reset role, run "
            "hadavin-sdk migrate --reset-role <role>, then set backends.store.reset_credential_ref to the name "
            "of the secret that holds its DSN. Nothing was changed.",
            file=sys.stderr,
        )
        return 2
    others_names = [
        n
        for n in (
            getattr(b.store, "dsn_secret_name", None),
            getattr(b.store, "purge_dsn_secret_name", None),
            getattr(b.store, "release_credential_ref", None),
        )
        if n
    ]
    if path_form_problem(ref, _file_backed(b)):
        print(
            "refused: backends.store.reset_credential_ref is a path-shaped name (a '.' or '..' segment, or for a "
            "mounted_file folder a leading or trailing '/'), which cannot be compared with the other logins. "
            "Write a plain secret name. Nothing was changed.",
            file=sys.stderr,
        )
        return 2
    if collides(ref, others_names, file_backed=_file_backed(b)):
        print(
            "refused: backends.store.reset_credential_ref names the same secret as the runtime, purge or release "
            "login. Point it at the secret that holds the reset role's own DSN. Nothing was changed.",
            file=sys.stderr,
        )
        return 2
    return None


def _caps_login(cfg, what: str):
    """The store and the audit of the RESET login for the three cap commands, or the exit code (an int) when the
    command is refused (`_caps_refusals` ran before). Returns `(store, audit_or_None)`."""
    b = cfg.backends
    ref = b.store.reset_credential_ref
    others_names = [
        n
        for n in (
            getattr(b.store, "dsn_secret_name", None),
            getattr(b.store, "purge_dsn_secret_name", None),
            getattr(b.store, "release_credential_ref", None),
        )
        if n
    ]
    try:
        secrets = make("secrets", b.secrets)
        if _same_login(secrets, ref, others_names):
            print(
                "refused: backends.store.reset_credential_ref holds the same login as the runtime, purge or "
                "release secret (two names, one DSN). Point it at the secret that holds the reset role's own "
                "DSN. Nothing was changed.",
                file=sys.stderr,
            )
            return 2
        as_reset = b.store.model_copy(
            update={"dsn_secret_name": ref, "purge_dsn_secret_name": None}
        )
        platform_secrets.check(secrets, [as_reset, b.audit], set())
        as_reset._login_role = (
            "reset"  # the reset login is not held to the runtime's rights at start
        )
        store = make("store", as_reset, secrets)
        audit = (
            None
            if what == "limits check-caps"  # read-only: no audit line
            else make("audit", b.audit, secrets, store=store, signer=None, anchor=None)
        )
    except StoreUnavailable:
        print(f"{what} NOT run: the store is unreachable. Nothing was changed.", file=sys.stderr)
        return 4
    except ConfigError as exc:
        print(f"refused: {exc}. Nothing was changed.", file=sys.stderr)
        return 2
    if getattr(store, "cap_matches", None) is None or getattr(store, "set_cap", None) is None:
        print(
            f"refused: {what}: this store has no cap table. Nothing was changed.", file=sys.stderr
        )
        return 2
    return store, audit


def _cap_event(by: str, agent: str, result: str, error: str | None = None) -> AuditEvent:
    return AuditEvent(
        run_id="-",
        domain="limits",
        operation="set_cap",
        principal=audit_code(by),
        source="cli",
        object_ref=audit_code(agent),
        result=audit_code(result),
        error_code=audit_code(error) if error is not None else None,
    )


def _set_one_cap(store, audit, agent: str, day: Decimal, month: Decimal, by: str) -> int:
    """One agent, the way `release_expired_spend` runs: the intent row first (if the audit is unavailable nothing
    changed: exit 3), then the write, then the outcome (a failed write gets a `set_cap_failed` outcome). 0 done,
    2 refused by the store, 3 audit unavailable, 4 store unreachable, 5 written but the outcome could not be
    audited (the table is changed; the intent row stands alone)."""
    try:
        audit.write_intent(_cap_event(by, agent, f"intent day_cap={day} month_cap={month}"))
    except AuditUnavailable:
        print(
            "refused: the audit store is unavailable, so the cap change cannot be recorded. Nothing was changed "
            f"(agent {agent}).",
            file=sys.stderr,
        )
        return 3
    try:
        store.set_cap(agent, day, month, by)
    except Exception as exc:  # noqa: BLE001 - the class name only
        try:
            audit.write_outcome(_cap_event(by, agent, "set_cap_failed", type(exc).__name__))
        except Exception:  # noqa: BLE001, S110 - the outcome contract is "never raises"; the exit code says it
            pass
        if is_connectivity_error(exc):
            print(f"cap of {agent} NOT set: the store is unreachable.", file=sys.stderr)
            return 4
        print(
            f"cap of {agent} NOT set ({type(exc).__name__}). Is this the reset role's login "
            "(hadavin-sdk migrate --reset-role)? Nothing was changed for this agent.",
            file=sys.stderr,
        )
        return 2
    try:
        key = audit.write_outcome(_cap_event(by, agent, f"set day_cap={day} month_cap={month}"))
    except Exception:  # noqa: BLE001
        key = None
    print(f"cap of {agent} set: day {day}, month {month} (by {by})")
    if key is None:
        print(
            f"set, but the outcome of {agent} could NOT be audited: the audit holds only the intent row. "
            "Record it by hand (see the runbook).",
            file=sys.stderr,
        )
        return 5
    return 0


def _confirm(args, what: str) -> bool:
    """`--yes`, or an interactive yes. A run that is neither is refused (the caller returns 2)."""
    if args.yes:
        return True
    if not sys.stdin.isatty():
        return False
    return input(f"{what} [y/N] ").strip().lower() in ("y", "yes")


def caps_cmd(cfg, args) -> int:
    """`limits set-cap`, `limits sync-caps`, `limits check-caps`: the spend caps live in a table the runtime login
    cannot write (migration 0011); these commands run under the reset login. Own function, own exit codes,
    nothing shared with `kill_switch`: 0 done (check-caps: every cap matches); 1 check-caps found a difference or a
    missing row; 2 refused; 3 the audit store is unavailable (nothing changed); 4 the store is unreachable; 5 set,
    but an outcome row could not be audited. Refusals come before any connection."""
    what = f"limits {args.action}"
    check = args.action == "check-caps"
    if not check and not args.yes and not sys.stdin.isatty():
        print(
            f"refused: {what} changes caps; pass --yes when it is not run interactively. Nothing was changed.",
            file=sys.stderr,
        )
        return 2
    refused = _caps_refusals(cfg, what)
    if refused is not None:
        return refused
    reg = load_registry(cfg)
    wanted = {a.id: a for a in reg.agents.values() if a.status != "retired"}
    if args.action == "set-cap":
        agent = reg.agents.get(args.agent)
        if agent is None or agent.status == "retired":
            print(
                f"refused: {args.agent!r} is not a live or draft agent of the registry. Nothing was changed.",
                file=sys.stderr,
            )
            return 2
    got = _caps_login(cfg, what)
    if isinstance(got, int):
        return got
    store, audit = got
    by = getattr(args, "by", None)
    if args.action == "set-cap":
        if not _confirm(
            args, f"set the caps of {args.agent} to day {args.day}, month {args.month}?"
        ):
            print("refused: not confirmed. Nothing was changed.", file=sys.stderr)
            return 2
        code = _set_one_cap(store, audit, args.agent, args.day, args.month, by)
        if code in (0, 5):
            rec = wanted[args.agent].budget_usd
            if (rec.daily, rec.monthly) != (args.day, args.month):
                print(
                    f"note: the registry holds other caps for {args.agent}; limits check-caps and the tick will "
                    "report the difference until the registry and the table agree."
                )
        return code
    states: dict[str, str] = {}
    try:
        for agent_id in sorted(wanted):
            rec = wanted[agent_id].budget_usd
            states[agent_id] = store.cap_matches(agent_id, rec.daily, rec.monthly)
    except Exception as exc:  # noqa: BLE001 - the class name only
        if is_connectivity_error(exc):
            print(f"{what}: the store is unreachable. Nothing was changed.", file=sys.stderr)
            return 4
        print(
            f"{what}: the store answered with an error ({type(exc).__name__}); run hadavin-sdk migrate and check "
            "the reset role's grants. Nothing was changed.",
            file=sys.stderr,
        )
        return 2
    for agent_id, state in states.items():
        print(f"{agent_id}: {state}")
    off = sorted(a for a, st in states.items() if st != "same")
    if check:
        if off:
            print(f"{len(off)} agent(s) differ from the caps table: run limits sync-caps")
        return 1 if off else 0
    if not off:
        print("nothing to change: every live and draft agent already has its registry caps")
        return 0
    if not _confirm(args, f"write the caps of {len(off)} agent(s)?"):
        print("refused: not confirmed. Nothing was changed.", file=sys.stderr)
        return 2
    for agent_id in off:  # one intent and one outcome per agent; stop at the first failure
        rec = wanted[agent_id].budget_usd
        code = _set_one_cap(store, audit, agent_id, rec.daily, rec.monthly, by)
        if code != 0:
            print(
                f"stopped at {agent_id}: the caps after it were not written. Fix the cause and run the same "
                "command again (it skips what is already equal).",
                file=sys.stderr,
            )
            return code
    print(f"synced {len(off)} agent(s), {len(states) - len(off)} already equal")
    return 0


def kill_switch(limits: Limits, action: str, by: str) -> int:
    """Run stop/reset for a caller (the CLI once a shared store exists, or an in-process admin hook).

    Exit codes: 0 done (for a reset: the state was read back and is OFF); 2 the store answered with an error (a
    reset by a login that is not the reset role lands here, with a `reset_failed` audit outcome) or the state
    still reads ON after the reset; 3 reset refused because the audit store is unavailable (the switch
    stays ON); 4 the store is unreachable (the switch was NOT changed).
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
        cleared = limits.reset(by)
    except AuditUnavailable:
        print(
            "refused: the audit store is unavailable, so the reset cannot be recorded. "
            "The kill switch stays ON. Fix the audit store, then try again.",
            file=sys.stderr,
        )
        return 3
    except Exception as exc:  # noqa: BLE001 - classified below
        return _kill_switch_store_down("reset", exc)
    try:  # report what the store reads now, not what was asked for
        state = limits.store.get_kill_switch()
    except Exception as exc:  # noqa: BLE001 - classified below
        print(
            f"reset written, but the kill switch could not be read back ({type(exc).__name__}): "
            "treat it as ON until a read succeeds.",
            file=sys.stderr,
        )
        return 4 if is_connectivity_error(exc) else 2
    if state.on:
        who = (
            f"set by {state.by!r} at {state.ts.isoformat()}"
            if state.by
            else "set by someone unknown"
        )
        try:  # name what was NOT cleared: these stops were set after the reset read the open stops
            left = limits.store.open_stops()
        except Exception:  # noqa: BLE001 - the line above is enough when the list cannot be read
            left = []
        shown = "".join(
            f"\n  not cleared: stop {s.id} by {s.by!r} at {s.ts.isoformat()}" for s in left[:20]
        ) + (f"\n  ... and {len(left) - 20} more" if len(left) > 20 else "")
        print(
            f"kill switch still ON ({who}): cleared {len(cleared)} stop(s), but a stop that was not in the list "
            "the reset showed is still open. A colleague may have just set it, or an older flag is on. Check the "
            "stop reason with them before resetting again: the next reset clears every stop it lists."
            + shown,
            file=sys.stderr,
        )
        return 2
    print(f"kill switch OFF (by {by}; cleared {len(cleared)} stop(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
