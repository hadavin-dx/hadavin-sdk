"""Command line: verify-readonly, ask, setup, demo. Every printed value passes `clean()` (A-11).

Operator commands (`audit`, `meter`, `killswitch`, `eval`) are in opscli.py and evalcli.py.
Exit codes: the single table in `policy.py` (0 ok; 1 usage; 3 the validator rejected, the database failed the statement,
the SQL hash did not match or a read-only check is red, here as in `verify-readonly`; 4 startup: no DSN, cannot connect,
cannot run the checks, or the server refused the login (SQLSTATE 28xxx); 7 the model abstained).
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess  # runs psql with a fixed argument list, never a shell
import sys
from pathlib import Path

from askdata import live
from askdata.config import ConfigError
from askdata.pgsource import HashMismatch, PgError, PgSource, RunResult
from askdata.policy import (
    EXIT_ABSTAINED,
    EXIT_FAILED,
    EXIT_OK,
    EXIT_REFUSED,
    EXIT_STARTUP,
    EXIT_USAGE,
)
from askdata.safe_text import clean
from askdata.scripted import Model, ScriptedModel, questions
from askdata.validate import Rejected, assert_all_rules_on, validate

ROOT = Path(__file__).resolve().parent.parent
BANNER = "Staged on synthetic data. Scripted model, no network. No accuracy claim is made."


def out(text: str = "") -> None:
    print(clean(text))


def table(columns: list[str], rows: list[tuple]) -> None:
    cells = [[clean(c, cell=True) for c in columns]] + [
        [clean(v, cell=True) for v in r] for r in rows
    ]
    widths = [max(len(r[i]) for r in cells) for i in range(len(columns))]
    for n, r in enumerate(cells):
        print(" | ".join(v.ljust(w) for v, w in zip(r, widths, strict=True)).rstrip())
        if n == 0:
            print("-+-".join("-" * w for w in widths))


def _source() -> PgSource | None:
    """The read-only login. With ASKDATA_CONFIG set: the DSN secret and the client limits come from the config;
    otherwise (and as the documented fallback when the config names no secret) the DSN is ASKDATA_DSN."""
    try:
        dsn, limits = live.source_args(os.environ.get("ASKDATA_CONFIG"))
    except ConfigError as err:
        out(f"startup: {err}")
        return None
    if not dsn:
        out(
            "startup: set ASKDATA_DSN to the connection string of the read-only login (password via PGPASSWORD)"
        )
        return None
    return PgSource(dsn, limits=limits)


def cmd_verify(source: PgSource, *, banner: bool = True) -> int:
    if banner:
        out(BANNER)
    try:
        checks = source.verify_readonly()
    except PgError as err:
        out(f"startup: cannot run the checks: {err}")
        return 4
    table(["check", "ok", "detail"], [(c.check, "ok" if c.ok else "RED", c.detail) for c in checks])
    red = [c for c in checks if not c.ok]
    out(
        f"verify-readonly: {'RED, ' + str(len(red)) + ' check(s) failed' if red else 'all checks green'}"
    )
    return 3 if red else 0


def gate(source: PgSource) -> int:
    """G7: `ask` does not start unless every read-only check is green. Prints only on failure; returns 0, 3 (a check is red) or 4 (cannot run them)."""
    try:
        red = [c for c in source.verify_readonly() if not c.ok]
    except PgError as err:
        out(f"startup: cannot run the read-only checks: {err}")
        return 4
    if red:
        out(
            f"startup: refusing to run, {len(red)} read-only check(s) are red (run verify-readonly):"
        )
        for c in red:
            out(f"  RED {c.check}: {c.detail}")
        return EXIT_FAILED  # a red check is 3 here exactly as in verify-readonly
    return 0


def cmd_ask(source: PgSource, sql: str, *, who: str, question: str | None = None) -> int:
    if question:
        out(f"question : {question}")
    out(f"source   : {who}")
    try:
        ok = validate(sql)
    except Rejected as err:
        out(f"rejected {err.rule}: {err.detail}  (nothing was sent to the database)")
        # a write attempt is a refusal, exactly as the pipeline reports it (reason write_request, exit 2)
        return EXIT_REFUSED if err.rule == "V03" else EXIT_FAILED
    out(f"canonical: {ok.canonical_sql}")
    out(f"sha256   : {ok.sha256}")
    try:
        result: RunResult = source.run(ok.canonical_sql, sql_sha256=ok.sha256)
    except PgError as err:
        out(f"failed   : {err}")
        if isinstance(err, HashMismatch):  # an alarm about the SQL itself, not a startup problem
            return EXIT_FAILED
        # No SQLSTATE (connection) and 28xxx (invalid authorization) are startup problems, never retried (A-14).
        return (
            EXIT_STARTUP if err.sqlstate is None or err.sqlstate.startswith("28") else EXIT_FAILED
        )
    table(result.columns, result.rows)
    out(
        f"{len(result.rows)} row(s){', TRUNCATED at the row or byte cap' if result.truncated else ''}; "
        f"result sha256 {result.result_sha256}"
    )
    return 0


def _psql() -> str | None:
    return os.environ.get("PSQL") or shutil.which("psql")


def _roles_input(password: str) -> str:
    """psql input that sets the password variable and then runs roles.sql, so it never appears in argv."""
    bs = chr(92)
    quoted = "'" + password.replace(bs, bs * 2).replace("'", "''") + "'"
    nl = chr(10)
    db = (
        ROOT / "db"
    )  # \ir inside roles.sql resolves against the current directory when read from stdin
    return f"{bs}cd '{db.as_posix()}'{nl}{bs}set ro_password {quoted}{nl}{bs}i roles.sql{nl}"


def cmd_setup(accept_loss: bool) -> int:
    """Apply schema, seed, views and roles to the dedicated database named by ASKDATA_ADMIN_DSN (psql)."""
    admin, password, psql = (
        os.environ.get("ASKDATA_ADMIN_DSN"),
        os.environ.get("ASKDATA_RO_PASSWORD"),
        _psql(),
    )
    if password and any(c in password for c in (chr(13), chr(10))):
        out("startup: ASKDATA_RO_PASSWORD must be a single line")
        return 4
    if not (admin and password and psql):
        out(
            "startup: set ASKDATA_ADMIN_DSN (a DEDICATED throwaway database), ASKDATA_RO_PASSWORD, and have psql on PATH or in PSQL"
        )
        return 4
    spec = importlib.util.spec_from_file_location("askdata_seed", ROOT / "db" / "seed.py")
    assert spec and spec.loader  # noqa: S101
    seed = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed)
    base = [
        psql,
        "-w",
        "-X",
        "-q",
        "-v",
        "ON_ERROR_STOP=1",
    ]  # options first: the connection string must come last
    steps = [
        ("schema", ["-f", str(ROOT / "db" / "schema.sql")], None),
        ("seed", ["-f", "-"], "\n".join(seed.sql_statements())),
        ("views", ["-f", str(ROOT / "db" / "views.sql")], None),
        (
            "roles",
            [
                "-v",
                "confirm_dedicated=yes",
                "-v",
                f"accept_loss={'yes' if accept_loss else 'no'}",
                "-f",
                "-",
            ],
            _roles_input(password),
        ),
    ]
    for name, args, stdin in steps:
        # The admin DSN comes from the operator's own environment and goes to psql as one argument, never a shell.
        cmd = [*base, *args, admin]
        done = subprocess.run(  # noqa: S603
            cmd,  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-tainted-env-args.dangerous-subprocess-use-tainted-env-args
            input=stdin,
            text=True,
            capture_output=True,
            check=False,
            **({} if stdin is not None else {"stdin": subprocess.DEVNULL}),
        )
        if done.returncode != 0:
            out(f"setup: step {name} failed (exit {done.returncode}):")
            out((done.stdout + done.stderr).strip()[-1500:].replace(password, "***"))
            # roles.sql refuses with psql exit 3 (not dedicated / others would lose access): pass it through
            return EXIT_FAILED if name == "roles" and done.returncode == 3 else EXIT_STARTUP
        out(f"setup: {name} done")
    return 0


def cmd_demo(source: PgSource, model: Model) -> int:
    out(BANNER)
    out("== 1. The promise: this login cannot write ==")
    worst = cmd_verify(source, banner=False)
    out("\n== 2. A normal question (answered by the offline scripted model; no API call) ==")
    worst = max(
        worst,
        cmd_ask(
            source,
            model.complete("How many orders per country?") or "",
            who=model.name,
            question="How many orders per country?",
        ),
    )
    out("\n== 3. Refusals by design ==")
    for q in ("Delete all cancelled orders", "List every customer email"):
        code = cmd_ask(source, model.complete(q) or "", who=model.name, question=q)
        worst = worst if code in (EXIT_REFUSED, EXIT_FAILED) else 4  # these two MUST be rejected
        out("")
    out("== 4. Proof at the database: run the psql step of the README as the read-only login ==")
    return 0 if worst == 0 else worst


def _operator(argv: list[str]) -> int | None:
    """`[--config PATH] audit|meter|killswitch|eval ...` live in their own modules (no database login needed)."""
    pre = argv[:2] if argv[:1] == ["--config"] and len(argv) >= 2 else []
    rest = argv[len(pre) :]
    if rest[:1] in (["audit"], ["meter"], ["killswitch"]):
        from askdata import opscli

        return opscli.main(argv)
    if rest[:1] == ["eval"]:
        from askdata import evalcli

        return evalcli.main([*pre, *rest[1:]])
    return None


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        assert_all_rules_on()  # every validator rule is on, always, outside the mutation test
    except RuntimeError as err:
        out(f"startup: {err}")
        return EXIT_STARTUP
    code = _operator(argv)
    if code is not None:
        return code
    ap = argparse.ArgumentParser(
        prog="askdata", description="Ask your data: staged synthetic-data demo"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify-readonly", help="run the read-only checks over the app's own connection")
    ask = sub.add_parser(
        "ask", help="validate and run one SELECT; a question uses the offline scripted model"
    )
    ask.add_argument("question", nargs="?", help="a question the scripted model knows")
    ask.add_argument("--sql", help="SQL typed by the presenter (the model step is not shown)")
    st = sub.add_parser(
        "setup", help="apply schema, seed, views and roles (admin DSN from the environment)"
    )
    st.add_argument("--accept-loss", action="store_true", help="pass accept_loss=yes to roles.sql")
    dm = sub.add_parser("demo", help="the offline demo: verify, one question, two refusals")
    dm.add_argument("--setup", action="store_true", help="run setup first")
    dm.add_argument("--accept-loss", action="store_true", help="with --setup: pass accept_loss=yes")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:  # argparse exits 2 (= refused in the table) on a usage error
        return EXIT_OK if exc.code in (0, None) else EXIT_USAGE

    if (
        args.cmd == "ask" and not args.sql and not args.question
    ):  # a usage error, whatever the environment lacks
        out("ask: give a question or --sql. Questions the offline model knows:")
        for q in questions():
            out(f"  {q}")
        return EXIT_USAGE
    if args.cmd == "setup" or (args.cmd == "demo" and args.setup):
        code = cmd_setup(getattr(args, "accept_loss", False))
        if code or args.cmd == "setup":
            return code
    source = _source()
    if source is None:
        return 4
    if args.cmd == "verify-readonly":
        return cmd_verify(source)
    if args.cmd == "demo":
        if code := gate(source):
            return code
        return cmd_demo(source, ScriptedModel())
    if code := gate(source):
        return code
    if args.sql:
        return cmd_ask(source, args.sql, who="SQL typed by the presenter; model step not shown")
    if not args.question:
        out("ask: give a question or --sql. Questions the offline model knows:")
        for q in questions():
            out(f"  {q}")
        return EXIT_USAGE
    sql = ScriptedModel().complete(args.question)
    if sql is None:
        out("the scripted model has no answer for that question (it abstains)")
        return EXIT_ABSTAINED
    return cmd_ask(source, sql, who=ScriptedModel.name, question=args.question)


if __name__ == "__main__":
    sys.exit(main())
