"""Fakes server (separate process; contract.md, HTTP table section, the paragraph that starts "Fakes server").
Demo-only code.
Run: python -m demo_only.fakes_server --outbox keyed|blind [--crm keyed|blind] [--port 8766]
Default host and port come from lead_desk.config.Config. Tests start it in a thread with make_fakes_server(port=0)."""

from __future__ import annotations

import json
import threading
import time
from typing import Any

from demo_only.bad_request import AnswersBadRequests, QuietServer, require_loopback_host
from lead_desk.config import Config
from lead_desk.constants import (
    EXIT_REFUSED,
    FAKE_SOCKET_TIMEOUT_SECONDS,
    HTTP_BAD_REQUEST,
    HTTP_NOT_FOUND,
    HTTP_OK,
    HTTP_UNPROCESSABLE,
    LOAD_TOTAL_MAX,
    NUDGE_KEY_PREFIX,
    PORT_MAX,
)
from scripts.http_guard import loads_bounded, read_request_body
from tools.refusing_args import RefusingParser, bounded_int, listen_refusal, refusal

FAIL_MODES = ("none", "refuse", "drop", "record_then_drop", "store_then_delay")
MODES = ("keyed", "blind")
TARGETS = ("outbox", "crm")


class FakesState:
    """All counters and controls. Tests read/flip these directly when the server runs in their process."""

    def __init__(self, outbox_mode: str = "keyed", crm_mode: str = "keyed") -> None:
        if outbox_mode not in MODES or crm_mode not in MODES:
            raise ValueError("mode must be keyed or blind")
        self.lock = threading.Lock()
        self.outbox_mode = outbox_mode
        self.crm_mode = crm_mode
        self.reset()

    def reset(self) -> None:
        with self.lock:
            self.outbox: list[dict[str, str]] = []
            self.crm: list[dict[str, Any]] = []
            self.crm_fields: dict[str, dict[str, str]] = {}  # lead_id -> {"owner_id", "status"}
            # one-shot control per target ("outbox" or "crm"): [fail_next, delay_ms]
            self.control: dict[str, list[Any]] = {"outbox": ["none", 0], "crm": ["none", 0]}


class _Handler(AnswersBadRequests):
    server_version = "fakes"
    timeout = FAKE_SOCKET_TIMEOUT_SECONDS  # a sender that stops sending is cut off, not waited for for ever
    state: FakesState  # set on the subclass by make_fakes_server

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return None

    # -- helpers
    def _send_bad_request(self) -> None:
        self._reply(HTTP_BAD_REQUEST, {"error": "bad_request"})

    def _reply(self, status: int, obj: Any) -> None:
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()
        self.close_connection = True

    @staticmethod
    def _parse(raw: bytes) -> Any:
        try:
            return loads_bounded(raw.decode("utf-8"))
        except ValueError:
            return None

    def _hang_up(self) -> None:
        self.close_connection = True  # no reply at all: the client sees the connection closed

    def _limit(self) -> int:
        """`?limit=N` (a whole number, 0 to LOAD_TOTAL_MAX) cuts the LIST of a view to N entries; no (or any other)
        value: the whole list. The totals in the reply are always for the whole list."""
        _, _, query = self.path.partition("?")
        for part in query.split("&"):
            name, _, value = part.partition("=")
            if name == "limit" and value.isascii() and value.isdigit() and int(value) <= LOAD_TOTAL_MAX:
                return int(value)
        return LOAD_TOTAL_MAX

    # -- routes
    def do_GET(self) -> None:
        st = self.state
        path = self.path.split("?")[0]
        with st.lock:
            if path == "/fake/info":
                return self._reply(
                    HTTP_OK,
                    {"outbox_capability": st.outbox_mode, "crm_capability": st.crm_mode, "mode": st.outbox_mode},
                )
            limit = self._limit()
            if path == "/fake/outbox":
                # counts are taken over every stored message; only the LIST is cut to `limit` (the portal shows 200)
                msgs = [{"key": m["key"], "to": m["to"], "subject": m["subject"]} for m in st.outbox[:limit]]
                reminders = sum(1 for m in st.outbox if str(m["key"]).startswith(NUDGE_KEY_PREFIX))
                return self._reply(
                    HTTP_OK,
                    {"mode": st.outbox_mode, "count": len(st.outbox), "reminders": reminders, "messages": msgs},
                )
            if path == "/fake/crm":
                rows = [{"lead_id": r["lead_id"], "record": r["record"]} for r in st.crm[:limit]]
                shown = {r["lead_id"] for r in rows}
                fields = {k: v for k, v in st.crm_fields.items() if k in shown}
                return self._reply(HTTP_OK, {"count": len(st.crm), "rows": rows, "fields": fields})
        self._reply(HTTP_NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:
        path = self.path.split("?")[0]
        raw, refused = read_request_body(self)  # bounded: at most FAKE_BODY_MAX_BYTES, with a time limit
        if refused:
            return self._reply(refused, {"error": "request_body_refused"})
        obj = self._parse(raw)
        if path == "/fake/outbox":
            return self._outbox(obj)
        if path == "/fake/crm":
            return self._crm(obj)
        if path == "/fake/crm/fields":
            return self._crm_fields(obj)
        if path == "/fake/control":
            return self._control(obj)
        if path == "/fake/reset":
            self.state.reset()
            return self._reply(HTTP_OK, {"status": "reset"})
        self._reply(HTTP_NOT_FOUND, {"error": "not_found"})

    def _control(self, obj: Any) -> None:
        st = self.state
        delay = obj.get("delay_ms", 0) if isinstance(obj, dict) else None
        target = obj.get("target", "outbox") if isinstance(obj, dict) else None
        ok = (
            isinstance(obj, dict)
            and obj.get("fail_next") in FAIL_MODES
            and target in TARGETS
            and isinstance(delay, int)
            and not isinstance(delay, bool)
            and delay >= 0
        )
        if not ok:
            return self._reply(HTTP_BAD_REQUEST, {"error": "bad_control"})
        with st.lock:
            st.control[target] = [obj["fail_next"], delay]
        self._reply(HTTP_OK, {"status": "ok"})

    def _take_control(self, target: str) -> tuple[str, int]:
        """The one-shot control of `target`, cleared by taking it."""
        with self.state.lock:
            mode, delay = self.state.control[target]
            self.state.control[target] = ["none", 0]
        return mode, delay

    def _crm(self, obj: Any) -> None:
        st = self.state
        if not (isinstance(obj, dict) and isinstance(obj.get("lead_id"), str) and isinstance(obj.get("record"), dict)):
            return self._reply(HTTP_BAD_REQUEST, {"error": "bad_body"})
        mode, delay = self._take_control("crm")
        if mode == "none" and delay:
            time.sleep(delay / 1000)  # wait BEFORE storing (slow CRM step)
        if mode == "refuse":
            return self._reply(HTTP_UNPROCESSABLE, {"error": "refused", "mode": st.crm_mode})
        if mode == "drop":
            return self._hang_up()
        with st.lock:
            seen = any(r["lead_id"] == obj["lead_id"] for r in st.crm)
            already = st.crm_mode == "keyed" and seen
            if not already:
                st.crm.append({"lead_id": obj["lead_id"], "record": obj["record"]})
        if mode == "record_then_drop":
            return self._hang_up()
        if mode == "store_then_delay":
            time.sleep(delay / 1000)
        self._reply(HTTP_OK, {"status": "already_present" if already else "put", "mode": st.crm_mode})

    def _crm_fields(self, obj: Any) -> None:
        st = self.state
        keys = ("lead_id", "email_key", "owner_id", "status")
        if not (isinstance(obj, dict) and all(isinstance(obj.get(k), str) for k in keys)):
            return self._reply(HTTP_BAD_REQUEST, {"error": "bad_body"})
        mode, delay = self._take_control("crm")
        if mode == "none" and delay:
            time.sleep(delay / 1000)  # wait BEFORE storing (slow CRM step)
        if mode == "refuse":
            return self._reply(HTTP_UNPROCESSABLE, {"error": "refused", "mode": st.crm_mode})
        if mode == "drop":
            return self._hang_up()
        with st.lock:
            if not any(r["lead_id"] == obj["lead_id"] for r in st.crm):
                return self._reply(HTTP_NOT_FOUND, {"error": "no_contact"})
            st.crm_fields[obj["lead_id"]] = {"owner_id": obj["owner_id"], "status": obj["status"]}
        if mode == "record_then_drop":
            return self._hang_up()  # stored, but the adapter sees no answer
        if mode == "store_then_delay":
            time.sleep(delay / 1000)
        self._reply(HTTP_OK, {"status": "set"})

    def _outbox(self, obj: Any) -> None:
        st = self.state
        keys = ("key", "to", "subject", "body")
        if not (isinstance(obj, dict) and all(isinstance(obj.get(k), str) for k in keys)):
            return self._reply(HTTP_BAD_REQUEST, {"error": "bad_body"})
        mode, delay = self._take_control("outbox")  # the control applies to this post only
        out_mode = st.outbox_mode
        if mode == "none" and delay:
            time.sleep(delay / 1000)  # wait BEFORE storing
        if mode == "refuse":
            return self._reply(HTTP_UNPROCESSABLE, {"error": "refused", "mode": out_mode})
        if mode == "drop":
            return self._hang_up()
        with st.lock:
            seen = any(m["key"] == obj["key"] for m in st.outbox)
            already = out_mode == "keyed" and seen
            if not already:
                st.outbox.append({k: obj[k] for k in keys})
        if mode == "record_then_drop":
            return self._hang_up()
        if mode == "store_then_delay":
            time.sleep(delay / 1000)  # store, then wait, then answer
        self._reply(HTTP_OK, {"status": "already_sent" if already else "sent", "mode": out_mode})


class FakesServer(QuietServer):
    state: FakesState


def make_fakes_server(
    outbox_mode: str = "keyed", port: int = 0, crm_mode: str = "keyed", host: str | None = None
) -> FakesServer:
    """Build (not start) a fakes server; port 0 = ephemeral. Host defaults to Config.fakes_host."""
    state = FakesState(outbox_mode, crm_mode)
    handler = type("Handler", (_Handler,), {"state": state})
    # None (unset) means the configured default; an explicit empty or blank host is NOT "unset": it is refused
    where = require_loopback_host(Config().fakes_host if host is None else host)
    srv = FakesServer((where, port), handler)
    srv.state = state
    return srv


def serve_fakes_in_thread(
    outbox_mode: str = "keyed", port: int = 0, crm_mode: str = "keyed"
) -> tuple[FakesServer, str, threading.Thread]:
    """Start in a daemon thread. Returns (server, base_url, thread). Stop with stop_fakes(server, thread)."""
    srv = make_fakes_server(outbox_mode, port, crm_mode)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    host, bound = srv.server_address[0], srv.server_address[1]
    return srv, f"http://{host}:{bound}", th


def stop_fakes(srv: FakesServer, th: threading.Thread) -> None:
    srv.shutdown()
    srv.server_close()
    th.join(timeout=5)


def main(argv: list[str] | None = None) -> None:
    """Parse --outbox keyed|blind and --port (default Config().fakes_port), serve the /fake/* routes until stopped."""
    cfg = Config()
    ap = RefusingParser(prog="demo_only.fakes_server")
    ap.add_argument("--outbox", choices=MODES, required=True)
    ap.add_argument("--crm", choices=MODES, default="keyed")
    ap.add_argument("--port", type=bounded_int(0, PORT_MAX), default=cfg.fakes_port)
    args = ap.parse_args(argv)
    try:
        srv = make_fakes_server(args.outbox, args.port, args.crm)
    except ValueError:  # DESK_FAKES_HOST is not a loopback address (the setting is checked again at the factory)
        print(refusal("DESK_FAKES_HOST", "must be this computer: localhost or a loopback address"))
        raise SystemExit(EXIT_REFUSED) from None
    except OSError as e:  # the port is in use or not allowed (or the host setting cannot be listened on)
        print(listen_refusal(e, has_host_option=False))
        raise SystemExit(EXIT_REFUSED) from None
    print(f"fakes server {args.outbox} on port {srv.server_address[1]}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
