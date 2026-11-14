"""Round 7C, finding A: ONE bounded JSON loader (src/lead_desk/jsonread.py) at every read site.

Class: `json.loads` raises RecursionError (not ValueError) for text nested about 30,000 levels deep, so every reader
that caught only ValueError showed a Python trace (and on the model path left a reserved spend unsettled). Each test
below sends such text (a loopback server, a file or a stored value) to ONE read site and expects that site's usual
refusal, never a RecursionError. The last tests fail when any file outside the loader parses JSON text itself."""

from __future__ import annotations

import ast
import importlib.util
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from support import script_module, start_serving, stop_serving

from demo_only.fake_model_server import ModelState
from lead_desk import live_claude, portal_api
from lead_desk.adapters import _exchange
from lead_desk.config import LiveSettings
from lead_desk.crm_hubspot import CrmError, HubspotCrm, HubspotSettings
from lead_desk.jsonread import JsonTooDeep, loads_bounded

REPO = Path(__file__).resolve().parents[1]

DEEP = ("[" * 30000 + "]" * 30000).encode()  # 60 KB: under every reply cap


class _Deep(BaseHTTPRequestHandler):
    def _go(self) -> None:
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            self.rfile.read(n)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(DEEP)))
        self.end_headers()
        self.wfile.write(DEEP)

    do_GET = do_POST = do_PATCH = do_DELETE = _go

    def log_message(self, *_a: Any) -> None:
        pass


@pytest.fixture
def deep_url() -> Any:
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Deep)
    thread = start_serving(srv)
    yield f"http://127.0.0.1:{srv.server_port}"
    stop_serving(srv, thread)


def _live(tmp_path: Path, url: str, run: str = "r") -> LiveSettings:
    key = tmp_path / "k"
    key.write_text("made-up-key-for-tests-only\n", encoding="utf-8")
    return LiveSettings(
        model="m",
        key_file=key,
        price_in_per_mtok=Decimal(1),
        price_out_per_mtok=Decimal(1),
        price_date="2026-11-01",
        cap_run_usd=Decimal(1),
        cap_total_usd=Decimal(1),
        ledger_path=tmp_path / f"ledger-{run}",
        run_id=run,
        base_url=url,
        timeout_seconds=5.0,
    )


def test_the_loader_turns_deep_text_into_a_value_error_and_keeps_keyword_arguments() -> None:
    with pytest.raises(JsonTooDeep) as info:
        loads_bounded(DEEP)
    assert isinstance(info.value, ValueError) and not isinstance(info.value, RecursionError)
    assert "[" not in str(info.value)  # the text never holds the input
    assert loads_bounded('{"a": [1, NaN]}', parse_constant=lambda _n: None) == {"a": [1, None]}
    with pytest.raises(ValueError):
        loads_bounded(b"{not json")
    assert loads_bounded(b'{"a": [1, 2]}') == {"a": [1, 2]}


def test_site_live_claude_reply_is_a_classed_bad_reply(tmp_path: Path, deep_url: str) -> None:
    q = live_claude.LiveQualifier(_live(tmp_path, deep_url))
    with pytest.raises(live_claude.LiveBadReply):
        q.qualify("lead-1", "a@example.test")


def test_site_run_live_check_counts_the_call_as_an_error_with_no_trace(tmp_path: Path, deep_url: str) -> None:
    spec = importlib.util.spec_from_file_location("run_live_check_r7c", REPO / "scripts" / "run_live_check.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    s = _live(tmp_path, deep_url, "r2")
    out = mod.run_model(s, [("l1", "a@example.test")], 1, live_claude.SpendLedger(s.ledger_path))
    assert out["errors"] == {"model service error": 1}
    ops = [line for line in s.ledger_path.read_text(encoding="utf-8").splitlines() if line]
    # a reply that cannot be read may have cost money: the worst-case reserve stays counted (the safe side)
    assert len(ops) == 1 and '"reserve"' in ops[0], ops


def test_site_live_claude_error_body_and_torn_tail_helpers() -> None:
    assert live_claude.error_type(DEEP) is None
    whole_but_deep = b'{"a":' + b"[" * 30000 + b"]" * 30000 + b"}"
    assert live_claude._is_torn_tail(whole_but_deep) is False  # too deep to be a plain cut: kept, fails closed


def test_site_hubspot_crm_put_is_a_crm_error_not_a_trace(tmp_path: Path, deep_url: str) -> None:
    key = tmp_path / "hk"
    key.write_text("made-up-token-for-tests\n", encoding="utf-8")
    crm = HubspotCrm(HubspotSettings(key_file=key, max_calls=10, base_url=deep_url, allow_any_base_url=True))
    with pytest.raises(CrmError):
        crm.put("lead-1", {"email": "a@example.test"})


def test_site_hubspot_probe_ends_with_a_line_not_a_trace(
    deep_url: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    hp = script_module("hubspot_probe")

    monkeypatch.setenv("PROBE_TOKEN_R7C", "pat-" + "na1-" + "0000-1111-2222")
    rc = hp.main(["--yes-spend-calls", str(hp.PLANNED_CALLS), "--token-env", "PROBE_TOKEN_R7C", "--dry-run", deep_url])
    text = capsys.readouterr()
    assert rc != 0 and "Traceback" not in text.out + text.err and "RecursionError" not in text.out + text.err


def test_site_adapters_exchange_refuses_with_a_value_error(deep_url: str) -> None:
    with pytest.raises(ValueError):
        _exchange(deep_url + "/x", {"a": 1}, 5.0)


def test_site_run_real_check_desk_counts_is_an_os_error(deep_url: str) -> None:
    rrc = script_module("run_real_check")

    desk = rrc.Desk({}, Path("."), 1, "x", "rabcdef")
    desk.url = deep_url
    with pytest.raises(OSError):
        desk.counts()


def test_site_portal_api_stored_text_reads_as_empty() -> None:
    assert portal_api._object("[" * 30000) == {}
    assert portal_api._names("[" * 30000) == []


def test_site_fake_model_control_file_with_deep_json_falls_back_to_the_mode(tmp_path: Path) -> None:
    ctl = tmp_path / "control.json"
    ctl.write_bytes(b'{"mode":' + b"[" * 30000 + b"]" * 30000 + b"}")
    state = ModelState("slow", "k", None, ctl)
    assert state.current_mode() == "slow"


def test_site_load_driver_reply_parse_is_an_empty_reply(deep_url: str) -> None:
    ld = script_module("load_driver")

    code, _err, reply, _wait = ld._post(deep_url + "/x", b"{}")
    assert code == 200 and reply == {}


_SCANNED = ("src", "scripts", "demo_only", "tools", "load_tools")
_LOADER = Path("src") / "lead_desk" / "jsonread.py"


def _parses_json_itself(tree: ast.AST) -> list[int]:
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute):
                is_json_module_call = (
                    f.attr in {"loads", "load"} and isinstance(f.value, ast.Name) and f.value.id == "json"
                )
                if is_json_module_call or f.attr in {"json", "raw_decode"}:
                    lines.append(node.lineno)
            elif isinstance(f, ast.Name) and f.id in {"JSONDecoder", "loads"}:
                lines.append(node.lineno)
        if isinstance(node, ast.ImportFrom) and node.module == "json":
            lines.append(node.lineno)  # `from json import loads` hides the call
    return lines


def test_no_file_outside_the_loader_parses_json_text_itself() -> None:
    seen = 0
    for folder in _SCANNED:
        for path in sorted((REPO / folder).rglob("*.py")):
            rel = path.relative_to(REPO)
            seen += 1
            if rel == _LOADER:
                continue
            bad = _parses_json_itself(ast.parse(path.read_text(encoding="utf-8")))
            assert not bad, f"{rel} lines {bad}: parse JSON text through lead_desk.jsonread.loads_bounded"
    assert seen > 40


def test_the_scan_notices_each_way_to_parse() -> None:
    for text in ("import json\njson.loads('1')", "import json\njson.load(f)", "r.json()", "from json import loads"):
        assert _parses_json_itself(ast.parse(text)), text
    assert not _parses_json_itself(ast.parse("import json\njson.dumps({})"))
