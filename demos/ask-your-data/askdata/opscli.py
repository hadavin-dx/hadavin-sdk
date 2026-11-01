"""Operator commands: `audit list|show|verify|export`, `meter`, `killswitch on|off|status`.

Every printed value passes `clean()`. Exit codes: 0 ok; 1 usage; 3 `audit verify` found a problem; 4 startup (bad
config, unreadable file); 5 the audit sink refused a kill-switch change (nothing changed).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from askdata import audit as audit_mod
from askdata.config import ConfigError, load_config
from askdata.htmlexport import render_ledger, write_stdout
from askdata.ledger import QueryLedger
from askdata.meter import KillSwitch, Meter, MeterError, fmt_usd
from askdata.safe_text import clean
from hadavin_sdk.audit.protocol import AuditUnavailable

TEXT_KEYS = frozenset({"question", "sql_text", "canonical_sql"})
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def out(text: object = "") -> None:
    print(clean(text))


def _guard_cell(value: object) -> str:
    """CSV formula guard: a cell that starts like a formula gets a leading single quote."""
    text = clean(value, cell=True)
    return "'" + text if text.startswith(FORMULA_START) else text


def _redact(obj: object) -> object:
    if isinstance(obj, dict):
        return {
            k: (
                {"sha256": hashlib.sha256(v.encode()).hexdigest(), "length": len(v)}
                if k in TEXT_KEYS and isinstance(v, str)
                else _redact(v)
            )
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj


def _lines(cfg):
    return QueryLedger(cfg.paths.ledger_file).read()


def cmd_list(cfg, last: int) -> int:
    res = _lines(cfg)
    for item in res.items[-last:] if last else res.items:
        ln = item.line
        out(
            f"{ln.query_id[:12]}  {ln.ts}  {ln.asker:<24}  {ln.outcome:<9}  {ln.reason_code or '-':<20}  {ln.cost_usd}"
        )
    out(
        f"{len(res.items)} ledger line(s)"
        + (f"; {len(res.bad)} torn or invalid" if res.bad else "")
    )
    return 0


def cmd_show(cfg, prefix: str, sink) -> int:
    hits = [i for i in _lines(cfg).items if i.line.query_id.startswith(prefix)]
    if len(hits) != 1:
        out(f"audit show: {len(hits)} ledger lines start with that id")
        return 1
    item = hits[0]
    out(json.dumps(json.loads(item.line.model_dump_json(by_alias=True)), indent=2, sort_keys=True))
    out(f"ledger line sha256 {item.sha256}")
    for e in sink.events(item.line.query_id):
        out(
            f"event {e.event_id}  {e.operation:<10} decision={e.decision} rule={e.rule_id} error={e.error_code} object={e.object_ref} result={e.result}"
        )
    return 0


def cmd_export(cfg, fmt: str, include_text: bool, dest: Path | None) -> int:
    rows = [json.loads(i.line.model_dump_json(by_alias=True)) for i in _lines(cfg).items]
    if not include_text:
        rows = [_redact(r) for r in rows]  # type: ignore[misc]
    if fmt == "json":
        text = json.dumps(rows, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    elif fmt == "html":
        text = render_ledger(rows, redacted=not include_text)  # type: ignore[arg-type]
    else:
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(
            [
                "query_id",
                "ts",
                "asker",
                "question",
                "outcome",
                "reason_code",
                "rule_id",
                "canonical_sql",
                "row_count",
                "cost_usd",
                "latency_ms",
                "alarm",
            ]
        )
        for r in rows:
            fin = r.get("final") or {}
            w.writerow([_guard_cell(v) for v in (
                r["query_id"], r["ts"], r["asker"], _flat(r.get("question")), r["outcome"], r.get("reason_code") or "", r.get("rule_id") or "",
                _flat(fin.get("canonical_sql")), fin.get("row_count", ""), r["cost_usd"], r["latency_ms"], ";".join(r["alarm"]),
            )])  # fmt: skip
        text = buf.getvalue()
    if dest:
        dest = dest.resolve()
        if Path.cwd().resolve() not in (dest, *dest.parents):
            out("export: --out must be inside the current folder")
            return 1
        dest.write_text(text, encoding="utf-8", newline="\n")
        out(
            f"wrote {len(rows)} line(s) to {dest.name}"
            + ("" if include_text else " (question and SQL text redacted to sha256 and length)")
        )
    else:
        if fmt == "html":
            write_stdout(clean(text))
        else:
            sys.stdout.write(clean(text))
    return 0


def _flat(v: object) -> str:
    if isinstance(v, dict):
        return f"sha256:{v['sha256']} length:{v['length']}"
    return "" if v is None else str(v)


def cmd_meter(cfg, set_external: str | None, init: bool = False, clear_open: bool = False) -> int:
    m = cfg.meter_obj()
    if init:  # the shared file is created once; an existing one (with the other program's spend) is never overwritten
        if m.path.exists():
            out("meter: the file already exists; not overwritten")
            return 4
        L = cfg.meter
        Meter.create(
            m.path,
            total_cap=str(L.total_cap_usd),
            reserve=str(L.reserve_usd),
            demo_cap=str(L.demo_cap_usd),
        )
        out(
            f"meter: created with total cap {L.total_cap_usd}, reserve {L.reserve_usd}, demo cap {L.demo_cap_usd}"
        )
    try:
        if clear_open:
            out(
                f"meter: forgot {m.clear_open()} open reservation(s); the money stays booked as spent"
            )
        if set_external is not None:
            m.set_external(Decimal(set_external))
        s = m.snapshot()
    except (MeterError, InvalidOperation) as err:
        out(f"meter: {err}")
        return 4
    out(f"spent by askdata   : {fmt_usd(s['askdata_spent'])} of {fmt_usd(s['demo_cap'])}")  # type: ignore[arg-type]
    out(f"external (typed in): {fmt_usd(s['external_usd'])}  set {s['external_updated_at']}")  # type: ignore[arg-type]
    out(
        f"remaining          : {fmt_usd(s['remaining'])}  (demo room {fmt_usd(s['demo_room'])}, shared room {fmt_usd(s['shared_room'])})"
    )  # type: ignore[arg-type]
    if s["open"]:
        out(
            f"open reservations : {s['open']} (a call in flight, or a process that died before it settled)"
        )
    return 0


def cmd_killswitch(cfg, action: str, sink) -> int:
    ks = KillSwitch(cfg.paths.kill_switch_file)
    if action == "status":
        out("killswitch: ON (the tool is switched off)" if ks.is_on() else "killswitch: off")
        return 0
    audit = audit_mod.AskAudit(sink, principal="claimed:operator")
    if action == "on":  # switching the tool OFF must never depend on the audit being up
        ks.on()
        try:
            audit.switch("on")
        except AuditUnavailable:
            out("killswitch: ON, but the audit event could not be written")
            return 5
        out("killswitch: on")
        return 0
    try:
        audit.switch("off")  # turning it back on-line is audited first
    except AuditUnavailable:
        out("killswitch: audit unavailable, nothing changed")
        return 5
    ks.off()
    out("killswitch: off")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="askdata", description="Ask your data: operator commands")
    ap.add_argument("--config", default=None, help="askdata config file (env ASKDATA_CONFIG)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    au = sub.add_parser("audit", help="list, show, verify or export the query ledger")
    asub = au.add_subparsers(dest="what", required=True)
    ls = asub.add_parser("list")
    ls.add_argument("--last", type=int, default=0)
    asub.add_parser("show").add_argument("query_id")
    asub.add_parser("verify")
    ex = asub.add_parser("export")
    ex.add_argument("--format", choices=["json", "csv", "html"], default="json")
    ex.add_argument(
        "--include-text", action="store_true", help="keep question and SQL text (default: redacted)"
    )
    ex.add_argument("--out", type=Path)
    me = sub.add_parser("meter", help="show the cost meter")
    me.add_argument(
        "--init",
        action="store_true",
        help="create the meter file (10.00 total, 1.00 reserve, 8.00 demo)",
    )
    me.add_argument(
        "--clear-open",
        action="store_true",
        help="forget unsettled reservations (after checking the provider console)",
    )
    me.add_argument(
        "--set-external", metavar="USD", help="type in what other programs spent (provider console)"
    )
    ks = sub.add_parser("killswitch")
    ks.add_argument("action", choices=["on", "off", "status"])
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code in (0, None) else 1  # a usage error is exit 1
    path = args.config or os.environ.get("ASKDATA_CONFIG")
    if not path:
        out("startup: give --config or set ASKDATA_CONFIG")
        return 4
    try:
        cfg = load_config(Path(path))
    except ConfigError as err:
        out(f"startup: {err}")
        return 4
    sink = audit_mod.local_dir_sink(cfg.paths.audit_dir)
    if args.cmd == "audit":
        if args.what == "list":
            return cmd_list(cfg, args.last)
        if args.what == "show":
            return cmd_show(cfg, args.query_id, sink)
        if args.what == "verify":
            rep = audit_mod.verify(QueryLedger(cfg.paths.ledger_file), sink)
            out(rep.text())
            return 0 if rep.ok else 3
        return cmd_export(cfg, args.format, args.include_text, args.out)
    if args.cmd == "meter":
        return cmd_meter(cfg, args.set_external, args.init, args.clear_open)
    return cmd_killswitch(cfg, args.action, sink)
