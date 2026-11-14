"""Round 7T: tests for the findings of the EV7S evidence run (five mutants that survived, one host that was not
refused), for the independent r7s review (a missing desk counter ended the run as good; mail fakes with no host
refusal) and for the class "an empty or falsy value is silently replaced by a default". Made-up data only, loopback
only; no real service, no spend.

Result on a plain copy of r7s (counts from out/R7T/before-final.log; see R7T-RESULTS.md). FAILS = fails before the fix.
PIN = the code was already right; the test passes on both and exists so that a named mutant is killed or a wrong
later change is caught.

  t1   counting rule; a counter that is not known raises (r7s: 0 = fail open)       FAILS
  t2   counter reader: only `desk-<tag>-*<suffix>` (R19, R20); files found and
       unreadable files counted; empty glob, half-written, folder, odd values        FAILS (10 cases), PIN (glob, 1)
  t3   a result file that could not be written ends the run as failed (R27)          PIN
  t4   any non-empty DPLD_REQUIRE_SCAN value makes a missing openssl a failure (R39) PIN
  t5   quiet server silent for a client that left, reports other errors (R07)        PIN
  t6   every fake and factory refuses an explicit empty, blank or non-loopback host
       before any socket; None or unset is the configured loopback default           FAILS (15), PIN (29)
  t6b  sweeps: every def with a host parameter is in the table (a new one fails
       and is named); every bind call; every server base class                      FAILS (def sweep), PIN (2 sweeps)
  t6c  the shared refusal fails closed on a host that is not text                    FAILS (4)
  t7   the run tag is required (None and "" refused; Desk has no default)            FAILS (3)
  t8   DESK_PORT written as 0 is refused, absent is 8765; dry smtp script default
       chosen by `is None`                                                           FAILS (t8, t8b)
  t9   a missing, unreadable or half-written desk counter ends the run as failed     FAILS (3), PIN (readable counter)
  t10  the counter write is a temporary file and a replace                           PIN
  t11  no test reads DPLD_REQUIRE_SCAN with == or !=                                 PIN
  t12  hostile host spellings are refused by every entry point; loopback accepted    FAILS (21)
  t13  banner figure equals worst_case_usd of the longest request                    PIN
  t14  no test skips on openssl through skipif or importorskip                       PIN
"""

from __future__ import annotations

import ast
import json
import socket
import time
from pathlib import Path
from typing import Any

import pytest
from support import HOST, REPO, script_module

from tools.refusing_args import LOOPBACK_HOST_TEXT

rrc = script_module("run_real_check")

ALL_INTERFACES = ".".join(["0"] * 4)
OTHER_ADDRESS = ".".join(["192", "0", "2", "1"])
NOT_LOOPBACK = [ALL_INTERFACES, OTHER_ADDRESS, "", "::", "example." + "com"]
BLANK_OR_BAD = ["", " ", "\t", "\n"]


# -- t1: the counting rule (fails closed) ---------------------------------------------------------------------------


def test_t1_the_counting_rule_and_an_unknown_counter() -> None:
    assert rrc.contacts_not_accounted_for(0, 0) == 0  # a counter that says 0 and nothing shown: nothing is missing
    assert rrc.contacts_not_accounted_for(0, 3) == 0
    assert rrc.contacts_not_accounted_for(1, 0) == 1
    assert rrc.contacts_not_accounted_for(2, 1) == 1
    with pytest.raises(rrc.CounterUnreadable):  # r7s said 0 here (fail open)
        rrc.contacts_not_accounted_for(None, 0)


# -- t2: the counter reader ------------------------------------------------------------------------------------------


def test_t2_the_counter_reader_takes_exactly_the_files_of_the_run_and_the_suffix(tmp_path: Path) -> None:
    def put(name: str, n: int) -> None:
        (tmp_path / name).write_text(json.dumps({"created": n}), encoding="utf-8")

    put("desk-raaaaaa-1.hubspot.json", 2)  # counted
    put("desk-raaaaaa-2.hubspot.json", 3)  # counted
    put("desk-raaaaaaX-1.hubspot.json", 100)  # a tag that only STARTS with this tag (glob without the dash)
    put("desk-raaaaaa.hubspot.json", 200)  # no dash and no label after the tag
    put("desk-raaaaaa-1.smtp.json", 400)  # the other counter kind of the same run (suffix dropped)
    put("desk-raaaaaa-1.hubspot.json.old", 800)  # the suffix must END the name
    assert rrc.read_counter_files(tmp_path, ".hubspot.json", "raaaaaa") == {"created": 5}
    assert rrc.read_counter_files(tmp_path, ".smtp.json", "raaaaaa") == {"created": 400}


def test_t2_the_checked_reader_counts_files_and_unreadable_files(tmp_path: Path) -> None:
    read = rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "raaaaaa")
    assert (read.totals, read.files, read.unreadable) == ({}, 0, 0) and not rrc.counter_is_known(read)  # empty glob
    (tmp_path / "desk-raaaaaa-1.hubspot.json").write_text('{"created": 2, "calls": 4}', encoding="utf-8")
    read = rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "raaaaaa")
    assert (read.totals, read.files, read.unreadable) == ({"created": 2, "calls": 4}, 1, 0)
    assert rrc.counter_is_known(read)
    (tmp_path / "desk-raaaaaa-2.hubspot.json").write_text('{"created": ', encoding="utf-8")  # half written
    read = rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "raaaaaa")
    assert (read.files, read.unreadable) == (2, 1) and not rrc.counter_is_known(read)
    assert rrc.read_counter_files(tmp_path, ".hubspot.json", "raaaaaa") == {"created": 2, "calls": 4}  # numbers only


@pytest.mark.parametrize(
    "content", ['{"created": ', "[]", '{"created": [1]}', '{"created": "x"}', "", "null"], ids=repr
)
def test_t2_a_file_that_is_not_a_set_of_whole_numbers_is_unreadable_and_never_a_crash(
    tmp_path: Path, content: str
) -> None:
    (tmp_path / "desk-raaaaaa-1.hubspot.json").write_text(content, encoding="utf-8")
    read = rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "raaaaaa")
    assert read.files == 1 and read.unreadable == 1 and not rrc.counter_is_known(read)


def test_t2_a_folder_with_the_name_of_a_counter_file_is_unreadable(tmp_path: Path) -> None:
    (tmp_path / "desk-raaaaaa-1.hubspot.json").mkdir()
    read = rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "raaaaaa")
    assert (read.files, read.unreadable) == (1, 1)


def test_t2_a_counter_without_the_number_of_created_contacts_is_not_known(tmp_path: Path) -> None:
    (tmp_path / "desk-raaaaaa-1.hubspot.json").write_text('{"calls": 4}', encoding="utf-8")
    assert not rrc.counter_is_known(rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "raaaaaa"))


def test_t2_a_counter_is_known_only_when_a_file_was_found_read_whole_and_holds_the_created_number() -> None:
    """Each of the three conditions alone (kills the mutants that drop one): no file found, one unreadable, no
    number of created contacts."""
    assert rrc.counter_is_known(rrc.CounterRead({"created": 3}, 2, 0))
    assert not rrc.counter_is_known(rrc.CounterRead({"created": 3}, 0, 0))
    assert not rrc.counter_is_known(rrc.CounterRead({"created": 3}, 2, 1))
    assert not rrc.counter_is_known(rrc.CounterRead({"calls": 3}, 2, 0))
    assert not rrc.counter_is_known(rrc.CounterRead({}, 0, 0))


def test_t2_the_same_tag_other_kinds_of_file_are_not_read_into_the_hubspot_sum(tmp_path: Path) -> None:
    """R20 (suffix dropped) was a real gap: the desk log and the mail counter of the SAME run sit in the same folder.
    R19 (the dash left out of the glob) is NOT equivalent either: a tag that only starts with this tag, or a file with
    no label, would be read (the reader takes any tag text; TAG_HEX_CHARS only fixes what the run itself makes)."""
    (tmp_path / "desk-raaaaaa-1.hubspot.json").write_text('{"created": 1}', encoding="utf-8")
    (tmp_path / "desk-raaaaaa-1.smtp.json").write_text('{"created": 10, "sent": 9}', encoding="utf-8")
    (tmp_path / "desk-raaaaaa-1.log").write_text('{"created": 100}', encoding="utf-8")
    read = rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "raaaaaa")
    assert (read.totals, read.files) == ({"created": 1}, 1)


# -- t3: the result file ---------------------------------------------------------------------------------------------


def test_t3_a_result_file_that_could_not_be_written_ends_the_run_as_failed(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rrc, "write_result", lambda *_a, **_k: False)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert code == rrc.EXIT_FAILED, out[-1500:]


# -- t4: the openssl helper ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["1", "true", "yes", "TRUE", "2", "0", "on"])
def test_t4_any_non_empty_require_value_makes_a_missing_openssl_a_failure(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    from support import skip_or_fail_without_openssl

    monkeypatch.setenv("DPLD_REQUIRE_SCAN", value)
    with pytest.raises(BaseException) as info:
        skip_or_fail_without_openssl()
    assert info.type is pytest.fail.Exception, info.type


def test_t4_an_empty_require_value_is_the_same_as_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    from support import skip_or_fail_without_openssl

    monkeypatch.setenv("DPLD_REQUIRE_SCAN", "")
    with pytest.raises(BaseException) as info:
        skip_or_fail_without_openssl()
    assert info.type is pytest.skip.Exception, info.type


# -- t5: the quiet server --------------------------------------------------------------------------------------------


def _handle(srv: Any, exc: BaseException) -> None:
    try:
        raise exc
    except BaseException:
        srv.handle_error(None, ("127.0.0.1", 1))


@pytest.mark.parametrize("exc", [BrokenPipeError(), ConnectionResetError(), ConnectionAbortedError(), TimeoutError()])
def test_t5_a_client_that_left_is_silent(capsys: pytest.CaptureFixture[str], exc: BaseException) -> None:
    from demo_only.bad_request import QuietServer

    srv = QuietServer((HOST, 0), type("H", (), {}))
    try:
        _handle(srv, exc)
    finally:
        srv.server_close()
    cap = capsys.readouterr()
    assert cap.out == "" and cap.err == ""


@pytest.mark.parametrize("exc", [ValueError("a real handler fault"), KeyError("k"), OSError("disk")])
def test_t5_every_other_error_is_reported(capsys: pytest.CaptureFixture[str], exc: BaseException) -> None:
    from demo_only.bad_request import QuietServer

    srv = QuietServer((HOST, 0), type("H", (), {}))
    try:
        _handle(srv, exc)
    finally:
        srv.server_close()
    assert "Exception occurred during processing of request" in capsys.readouterr().err


# -- t6: every fake and factory refuses an explicit blank or non-loopback host ---------------------------------------


def _handler() -> type:
    return type("H", (), {})


def _quiet(host: str) -> None:
    from demo_only.bad_request import QuietServer

    QuietServer((host, 0), _handler())


def _hubspot(host: str) -> None:
    from demo_only.fake_hubspot import HubspotState, serve

    serve(HubspotState("k", "ok"), host, 0)


def _fakes_class(host: str) -> None:
    from demo_only.fakes_server import FakesServer

    FakesServer((host, 0), _handler())


def _fakes_factory(host: str) -> None:
    from demo_only.fakes_server import make_fakes_server

    make_fakes_server(host=host)


def _model(host: str) -> None:
    from demo_only.fake_model_server import make_model_server

    make_model_server(host, 0, "ok", "k")


def _imap(host: str) -> None:
    from demo_only.fake_imap import FakeImap

    FakeImap(Path("no-such.crt"), Path("no-such.key"), host, {})


def _smtp(host: str) -> None:
    from demo_only.fake_smtp_tls import FakeSmtp

    FakeSmtp(Path("no-such.crt"), Path("no-such.key"), host)


# (file, qualified name) -> the function that calls it with a host. THE table of the sweep in t6b.
ENTRY_POINTS: dict[tuple[str, str], Any] = {
    ("demo_only/bad_request.py", "QuietServer.__init__"): _quiet,
    ("demo_only/fake_hubspot.py", "serve"): _hubspot,
    ("demo_only/fakes_server.py", "make_fakes_server"): _fakes_factory,
    ("demo_only/fake_model_server.py", "make_model_server"): _model,
    ("demo_only/fake_imap.py", "FakeImap.__init__"): _imap,
    ("demo_only/fake_smtp_tls.py", "FakeSmtp.__init__"): _smtp,
}
# a def with a host parameter that binds nothing: the reason it is not an entry point
NOT_A_BIND: dict[tuple[str, str], str] = {
    ("demo_only/fake_smtp_tls.py", "make_cert"): "makes a certificate for a name; opens no socket",
    ("demo_only/bad_request.py", "require_loopback_host"): "the refusal itself (tested directly in t6c)",
    ("demo_only/portal_demo.py", "PortalDemo.set_bound_address"): "records the address the desk already bound",
    ("demo_only/portal_demo.py", "PortalDemo._url_for"): "builds text from an address; opens no socket",
}
# classes that inherit their refusal from QuietServer (named so the test can call them too)
INHERITING = {"FakesServer": _fakes_class, "FakeHubspot": None}

HOST_PARAMS = {"host", "bind", "address", "addr", "server_address", "bind_address", "hostname", "listen_host"}


class _Sockets:
    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.made = 0
        real = socket.socket.__init__
        outer = self

        def counting(self_: socket.socket, *a: Any, **k: Any) -> None:
            outer.made += 1
            real(self_, *a, **k)

        monkeypatch.setattr(socket.socket, "__init__", counting)


@pytest.mark.parametrize("host", NOT_LOOPBACK)
@pytest.mark.parametrize(
    "call",
    [*ENTRY_POINTS.values(), _fakes_class],
    ids=lambda f: f.__name__.strip("_"),
)
def test_t6_every_entry_point_refuses_the_host_before_any_socket(
    monkeypatch: pytest.MonkeyPatch, call: Any, host: str
) -> None:
    sockets = _Sockets(monkeypatch)
    with pytest.raises(ValueError, match=LOOPBACK_HOST_TEXT):
        call(host)
    assert sockets.made == 0


@pytest.mark.parametrize("host", BLANK_OR_BAD)
def test_t6_a_blank_host_is_refused_by_every_entry_point(monkeypatch: pytest.MonkeyPatch, host: str) -> None:
    sockets = _Sockets(monkeypatch)
    for call in ENTRY_POINTS.values():
        with pytest.raises(ValueError, match=LOOPBACK_HOST_TEXT):
            call(host)
    assert sockets.made == 0


@pytest.mark.parametrize("kw", [{}, {"host": None}], ids=["unset", "None"])
def test_t6_an_unset_host_still_means_the_configured_loopback_default(kw: dict[str, Any]) -> None:
    from demo_only.fakes_server import make_fakes_server
    from lead_desk.config import Config

    srv = make_fakes_server(**kw)
    try:
        assert srv.server_address[0] == Config().fakes_host and srv.server_address[1] > 0
    finally:
        srv.server_close()


@pytest.mark.parametrize("host", [HOST, "localhost", "127.0.0.1"])
def test_t6_the_mail_fakes_still_listen_on_this_computer(host: str, tmp_path: Path) -> None:
    from demo_only.fake_smtp_tls import make_cert

    made = make_cert(tmp_path, host)
    if made is None:
        from support import skip_or_fail_without_openssl

        skip_or_fail_without_openssl()
    from demo_only.fake_imap import FakeImap
    from demo_only.fake_smtp_tls import FakeSmtp

    cert, key = made
    imap, smtp = FakeImap(cert, key, host, {"INBOX": []}), FakeSmtp(cert, key, host)
    try:
        assert imap.port > 0 and smtp.port > 0
    finally:
        imap.close()
        smtp.close()


def _demo_only_defs() -> dict[tuple[str, str], list[str]]:
    """(file, qualified name) -> host-like parameter names, for every def (and method) in demo_only."""
    found: dict[tuple[str, str], list[str]] = {}
    for py in sorted((REPO / "demo_only").glob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        rel = py.relative_to(REPO).as_posix()

        def visit(node: ast.AST, prefix: str) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.ClassDef):
                    visit(child, prefix + child.name + ".")
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = child.args
                    names = [a.arg for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)]
                    hit = [n for n in names if n in HOST_PARAMS]
                    if hit:
                        found[(rel, prefix + child.name)] = hit
                    visit(child, prefix + child.name + ".")

        visit(tree, "")
    return found


def test_t6b_every_def_with_a_host_parameter_is_in_the_table() -> None:
    """How a new one is caught: a def in demo_only with a parameter named host, bind, address and the like that is in
    neither ENTRY_POINTS (called with every bad host above) nor NOT_A_BIND (with a reason) fails this test and is
    named."""
    found = set(_demo_only_defs())
    known = set(ENTRY_POINTS) | set(NOT_A_BIND)
    new = found - known
    assert new == set(), f"new def with a host parameter, add it to ENTRY_POINTS or NOT_A_BIND: {new}"
    assert known - found == set(), f"table entry that no longer exists: {known - found}"


def test_t6b_every_bind_call_in_demo_only_sits_in_a_table_entry() -> None:
    """A socket bound or a server class made anywhere else in demo_only (a new fake with its own bind) is named."""
    allowed_files = {rel for rel, _ in ENTRY_POINTS} | {"demo_only/fakes_server.py"}
    bind_calls: set[str] = set()
    for py in sorted((REPO / "demo_only").glob("*.py")):
        rel = py.relative_to(REPO).as_posix()
        for node in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func)
                if name.endswith(".bind") or name in {"socket.create_server", "ThreadingHTTPServer", "HTTPServer"}:
                    bind_calls.add(f"{rel}:{name}")
    outside = {c for c in bind_calls if c.split(":")[0] not in allowed_files}
    assert outside == set(), f"a bind in a file with no table entry: {outside}"


def test_t6b_every_class_that_extends_a_server_class_inherits_the_refusal() -> None:
    from demo_only import fake_hubspot, fakes_server
    from demo_only.bad_request import QuietServer

    assert issubclass(fakes_server.FakesServer, QuietServer) and issubclass(fake_hubspot.FakeHubspot, QuietServer)
    for py in sorted((REPO / "demo_only").glob("*.py")):
        for node in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ClassDef):
                bases = {ast.unparse(b) for b in node.bases}
                assert not bases & {"ThreadingHTTPServer", "HTTPServer", "socketserver.TCPServer", "TCPServer"} or (
                    py.name == "bad_request.py" and node.name == "QuietServer"
                ), f"{py.name}:{node.name} extends a plain server class: extend QuietServer"


@pytest.mark.parametrize("host", [None, b"127.0.0.1", 0, ("127.0.0.1",)], ids=repr)
def test_t6c_the_refusal_fails_closed_on_a_host_that_is_not_text(host: Any) -> None:
    from demo_only.bad_request import require_loopback_host

    with pytest.raises(ValueError, match=LOOPBACK_HOST_TEXT):
        require_loopback_host(host)
    assert require_loopback_host("localhost") == "localhost"


# -- t7: the run tag is required ------------------------------------------------------------------------------------


@pytest.mark.parametrize("tag", ["", None], ids=repr)
def test_t7_an_empty_or_missing_tag_is_refused_not_turned_into_untagged_files(tmp_path: Path, tag: Any) -> None:
    with pytest.raises(ValueError):
        rrc.Desk({}, tmp_path, 1, "7", tag=tag)
    with pytest.raises(ValueError):
        rrc.read_counter_files(tmp_path, ".hubspot.json", "")


def test_t7_the_desk_has_no_default_tag(tmp_path: Path) -> None:
    desk_class: Any = rrc.Desk  # called the wrong way on purpose
    with pytest.raises(TypeError):
        desk_class({}, tmp_path, 1, "7")
    assert rrc.Desk({}, tmp_path, 1, "7", "rabcdef").log_path.name == "desk-rabcdef-7.log"


# -- t8: DESK_PORT written as 0 --------------------------------------------------------------------------------------


def test_t8_a_port_of_zero_is_refused_and_an_absent_port_is_the_default() -> None:
    assert rrc.desk_port({}) == rrc.DESK_PORT_DEFAULT == 8765
    assert rrc.desk_port({"DESK_PORT": "9123"}) == 9123
    with pytest.raises(ValueError, match="DESK_PORT"):
        rrc.desk_port({"DESK_PORT": "0"})


def test_t8_the_run_uses_that_one_function(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from test_real_check_dry import _valid_config

    code = rrc.main(["--config", str(_valid_config(tmp_path, DESK_PORT="0"))])
    out = capsys.readouterr().out
    assert code == rrc.EXIT_REFUSED and "DESK_PORT" in out and "Start?" not in out, out[-400:]


def test_t8b_the_dry_smtp_script_default_is_chosen_by_none_not_by_truth() -> None:
    src = (REPO / "scripts" / "run_real_check.py").read_text(encoding="utf-8")
    assert 'a.dry_smtp_script or "ok"' not in src


# -- t9: a counter that is missing or unreadable ends the run as failed (the r7s review, Major 1) -------------------


def _hiding_crm(hidden: int) -> type:
    class Hiding(rrc.HubspotCrm):
        """A CRM whose LIST shows `hidden` contacts fewer than exist (list lag)."""

        def rows_with_prefix(self, prefix: str) -> list[tuple[str, str]]:
            rows = super().rows_with_prefix(prefix)
            return rows[: len(rows) - hidden]

    return Hiding


def _unreadable_counters() -> type:
    class Colliding(rrc.Desk):
        """Each desk's counter path is already taken by a folder: the desk's replace fails and it says nothing (it
        must never break a send), so the counter is unreadable at the end, as after a hard kill or a full disk."""

        def start(self) -> None:
            self.log_path.with_suffix(".hubspot.json").mkdir(parents=True, exist_ok=True)
            super().start()

    return Colliding


def _hide_hubspot_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Only the HubSpot counter reads as missing (no file); every other read (the mail counter) is the real one, so
    the exit code can differ from 0 only because of the missing HubSpot counter."""
    real = rrc.read_counter_files_checked

    def reader(run_dir: Path, suffix: str, tag: str) -> Any:
        if suffix == ".hubspot.json":
            return rrc.CounterRead({}, 0, 0)
        return real(run_dir, suffix, tag)

    monkeypatch.setattr(rrc, "read_counter_files_checked", reader)


def test_t9_a_missing_counter_with_a_hidden_contact_ends_as_failed(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The scenario of the review: counter missing + one created contact hidden by list lag + the lead not CRM-done
    (floor F3 silent). On r7s: nothing said, exit 0, a contact left in HubSpot."""
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(1))
    monkeypatch.setattr(rrc, "floor_checks", lambda *_a, **_k: [])
    _hide_hubspot_counter(monkeypatch)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert "counter cannot be trusted" in out and "may be left in HubSpot" in out, out[-2000:]
    assert code == rrc.EXIT_FAILED, out[-2000:]


def test_t9_a_counter_the_desk_could_not_write_ends_the_real_run_as_failed(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same, with the real desk processes and the real reader (no patch of the reader)."""
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(1))
    monkeypatch.setattr(rrc, "floor_checks", lambda *_a, **_k: [])
    monkeypatch.setattr(rrc, "Desk", _unreadable_counters())
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert "counter cannot be trusted" in out, out[-2000:]
    assert code == rrc.EXIT_FAILED, out[-2000:]


def test_t9_a_missing_counter_alone_ends_as_failed_even_when_nothing_is_hidden(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rrc, "floor_checks", lambda *_a, **_k: [])
    _hide_hubspot_counter(monkeypatch)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    assert code == rrc.EXIT_FAILED, capsys.readouterr().out[-1500:]


def test_t9_a_counter_that_can_be_read_still_ends_with_zero(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(0))
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert code == 0 and "counter cannot be trusted" not in out, out[-1500:]


# -- t10: the desk's counter write is a temporary file and a replace ------------------------------------------------


def test_t10_the_counter_file_is_never_half_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The write is a temporary file, then os.replace. A stop (a kill, a full disk) during the write leaves the
    previous whole file in place; a stop before the replace leaves only the temporary file."""
    import lead_desk.run_stats as rs

    target = tmp_path / "desk-raaaaaa-1.hubspot.json"
    rs.write_stats(target, {"created": 1})
    assert json.loads(target.read_text(encoding="utf-8")) == {"created": 1}

    real_dumps = rs.json.dumps

    def dying(data: Any, **kw: Any) -> str:
        raise OSError("the disk is full")

    monkeypatch.setattr(rs.json, "dumps", dying)
    rs.write_stats(target, {"created": 2})  # swallowed by design: a counter file must never break a send
    monkeypatch.setattr(rs.json, "dumps", real_dumps)
    assert json.loads(target.read_text(encoding="utf-8")) == {"created": 1}

    def no_replace(*_a: Any, **_k: Any) -> None:
        raise OSError("stopped before the replace")

    monkeypatch.setattr(rs.os, "replace", no_replace)
    rs.write_stats(target, {"created": 3})
    assert json.loads(target.read_text(encoding="utf-8")) == {"created": 1}  # the target was not touched


def test_t10_the_target_name_is_only_ever_changed_by_a_replace(tmp_path: Path) -> None:
    src = (REPO / "src" / "lead_desk" / "run_stats.py").read_text(encoding="utf-8")
    assert "os.replace(tmp, path)" in src
    assert src.index("open_output(tmp") < src.index("os.replace(tmp, path)")
    assert "open_output(path" not in src


# -- t11: every consumer of DPLD_REQUIRE_SCAN reads it the same way (set and not empty) -----------------------------


def test_t11_no_test_compares_the_require_flag_to_a_value() -> None:
    """R39 asked whether one consumer reads `== "1"` while the helper reads truthiness. All consumers use truthiness
    (os.environ.get(...)); a comparison anywhere would make "true" mean different things in different files."""
    flag_names = {"REQUIRE_SCAN_ENV", "DPLD_REQUIRE_SCAN"}
    bad: list[str] = []
    for py in sorted((REPO / "tests").glob("*.py")) + sorted((REPO / "tools").glob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                text = ast.unparse(node)
                if any(n in text for n in flag_names) and any(isinstance(o, (ast.Eq, ast.NotEq)) for o in node.ops):
                    bad.append(f"{py.name}:{node.lineno}: {text}")
    assert bad == [], bad


# -- t12: the hostile list for the loopback refusal (the r7s review, minors 4 and 5) --------------------------------
# What lead_desk.config.is_loopback_host does with each spelling (read and run in r7t, not guessed): fail closed on
# every one below; it is only True for localhost in any letter case, 127.x, ::1 and ::ffff:127.x (brackets allowed).
HOSTILE_HOSTS: list[Any] = [
    None,
    " ",
    "\t",
    "\n",
    "0",
    "127.1",
    "localhost.",
    "[::]",
    "::",
    "0x7f.0.0.1",
    "127.0.0.1 ",
    " localhost",
    b"127.0.0.1",
    b"localhost",
    0,
    ("127.0.0.1",),
]
LOOPBACK_SPELLINGS = ["LOCALHOST", "LocalHost", "::ffff:127.0.0.1", "[::1]", "127.0.0." + "2"]


@pytest.mark.parametrize("host", HOSTILE_HOSTS, ids=repr)
def test_t12_every_hostile_spelling_is_refused_before_any_socket(monkeypatch: pytest.MonkeyPatch, host: Any) -> None:
    sockets = _Sockets(monkeypatch)
    calls = list(ENTRY_POINTS.values())
    if host is not None:  # None means "unset" for make_fakes_server only; the others must refuse it
        calls.append(_fakes_class)
    for call in calls:
        if host is None and call is _fakes_factory:
            continue
        with pytest.raises(ValueError, match=LOOPBACK_HOST_TEXT):
            call(host)
    assert sockets.made == 0


@pytest.mark.parametrize("host", LOOPBACK_SPELLINGS)
def test_t12_a_loopback_spelling_is_accepted_by_the_shared_rule(host: str) -> None:
    from demo_only.bad_request import require_loopback_host

    assert require_loopback_host(host) == host


# -- t13: the banner's worst-case figure, recomputed from worst_case_usd and the two request builders ---------------


@pytest.mark.parametrize(
    ("model", "price_in", "price_out", "persons"),
    [("claude-sonnet-5-5", "2", "10", 8), ("m" * 40, "0.5", "2.5", 13), ("claude-opus-5-5", "4", "20", 9)],
)
def test_t13_the_banner_figure_is_worst_case_usd_of_the_longest_request_times_the_factors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    price_in: str,
    price_out: str,
    persons: int,
) -> None:
    from decimal import Decimal

    from test_r7q_findings import _live_env
    from test_real_check_dry import _valid_config

    from lead_desk.live_claude import request_body, worst_case_usd

    tag = "rabcdef"
    monkeypatch.setattr(rrc, "new_tag", lambda: tag)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    env = {
        **_live_env(tmp_path, model),
        "DESK_LIVE_PRICE_IN_PER_MTOK": price_in,
        "DESK_LIVE_PRICE_OUT_PER_MTOK": price_out,
    }
    cfg = _valid_config(tmp_path, REAL_PERSONS=str(persons), **env)
    assert rrc.main(["--config", str(cfg), "--live-model"]) == rrc.EXIT_STOPPED
    out = capsys.readouterr().out

    from lead_desk.config import Config

    live = Config.from_env({**rrc.load_env(cfg), "DESK_QUALIFIER": "live_claude", "DESK_PORT": "0"}).live
    assert live is not None
    plan = rrc.make_plan(tag, persons)
    emails = [it["envelope"]["payload"]["email"] for items in plan.values() for it in items]
    lead_id = rrc.LEAD_ID_PREFIX + "f" * rrc.LEAD_ID_HEX_CHARS
    longest = max(len(request_body(live, rrc.question_text(lead_id, rrc.normalise_email(e)))) for e in emails)
    one_call = worst_case_usd(live, longest)
    # independent arithmetic (no program function): input bytes at the input price, max_tokens at the output price
    by_hand = (Decimal(price_in) * longest + Decimal(price_out) * live.max_tokens) / 1_000_000
    assert one_call == by_hand
    figure = by_hand * rrc.MODEL_CALLS_PER_LEAD * (persons + 3) * 2
    assert f"worst case model cost: US${figure:.4f} " in out, (figure, out[-900:])
    assert rrc.MODEL_CALLS_PER_LEAD == 3  # the factor the banner text names (3 tries per lead, 2 desk processes)


# -- t14: no test skips on a missing openssl through skipif or importorskip either (the r7s review, minor 7) ---------


def _openssl_skip_sites(source: str) -> list[int]:
    """Lines of a skipif(...) or importorskip(...) call whose text names openssl (any letter case)."""
    lines = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and ast.unparse(node.func).endswith(("skipif", "importorskip")):
            if "openssl" in ast.unparse(node).lower():
                lines.append(node.lineno)
    return lines


@pytest.mark.parametrize(
    "source",
    [
        chr(10).join(
            ["import pytest", "@pytest.mark.skipif(shutil.which('openssl') is None, reason='x')", "def test_a(): pass"]
        ),
        "import pytest\npytestmark = pytest.mark.skipif(not HAVE_OPENSSL, reason='openssl')\n",
        "import pytest\nssl = pytest.importorskip('openssl_helper')\n",
    ],
)
def test_t14_the_guard_sees_each_way_of_skipping_on_openssl(source: str) -> None:
    assert _openssl_skip_sites(source) != []


def test_t14_no_test_file_skips_on_openssl_through_skipif_or_importorskip() -> None:
    bad = []
    for py in sorted((REPO / "tests").glob("*.py")):
        if py.name == Path(__file__).name:
            continue
        bad += [f"{py.name}:{n}" for n in _openssl_skip_sites(py.read_text(encoding="utf-8"))]
    assert bad == [], bad


# -- t15: a create open when a desk was stopped hard (the crash window, named by the lead) ---------------------------
#
# Cause (r7s): HubspotCrm.put counted `created` only AFTER HubSpot's 201 reply (crm_hubspot.py, put). A desk stopped
# hard between the request and that count (the crash drill stops the first desk while its second batch is in flight)
# can leave a contact in HubSpot that no counter shows; the restarted desk then gets a 409 for it and counts
# `conflicts`, not `created`. The sum `created` was one too low, so a contact hidden by list lag in the same run was
# not noticed (created 8, list showed 8 of 9: "0 missing"). r7t writes `create_open` +1 before the request leaves (same
# write as the call counter) and ends it together with the outcome in one write; a stopped desk leaves 1. The check
# then takes created + create_open as the possible number (at most the leads in the book). No sleep and no real kill:
# the stop is forced by an exception that is not an Exception (nothing after it runs, like a kill) at the exact point.


class _Killed(BaseException):
    """Stands for a hard kill: it is not an Exception, so `except Exception` does not see it and nothing after the
    raise runs."""


def _stats(path: Path) -> dict[str, int]:
    return json.loads(path.read_text(encoding="utf-8"))


def _crm_with_stats(rig: Any, tmp_path: Path) -> tuple[Any, Path]:
    stats = tmp_path / "desk-rabcdef-1.hubspot.json"
    return rig.crm(stats_file=stats), stats


def test_t15_the_counting_rule_takes_open_creates_as_possible_contacts_and_never_more_than_the_leads() -> None:
    f = rrc.contacts_not_accounted_for
    assert f(8, 8, 1, 9) == 1  # the window: 8 counted, 1 open, the list showed 8 of 9
    assert f(8, 9, 1, 9) == 0  # the open create did make a contact and the list shows it
    assert f(9, 9, 1, 9) == 0  # the open create was retried by the next desk: 10 possible, but only 9 leads
    assert f(9, 8, 1, 9) == 1  # the cap by the leads does not hide a real miss
    assert f(8, 8, 0, 9) == 0 and f(8, 8) == 0  # no open create: the old rule
    assert f(8, 4, -3, 9) == 4  # a negative number never lowers the possible number (8 - 4, not 5 - 4)
    assert f(0, 0, 1, None) == 1  # no lead count given: created + open
    with pytest.raises(rrc.CounterUnreadable):
        rrc.contacts_not_accounted_for(None, 0, 1, 9)


def test_t15_the_window_after_the_request_and_before_the_count_leaves_the_create_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import HubspotCrm

    rig = Rig(tmp_path)
    try:
        crm, stats = _crm_with_stats(rig, tmp_path)

        def stop_before_the_count(self: Any, outcome: str | None) -> None:
            raise _Killed

        monkeypatch.setattr(HubspotCrm, "_settle_create", stop_before_the_count)
        with pytest.raises(_Killed):
            crm.put("L-1", REC)
        assert len(rig.state.contacts) == 1  # HubSpot made the contact
        written = _stats(stats)
        assert written["created"] == 0 and written["create_open"] == 1, written  # no counter shows it, the window does
        read = rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "rabcdef")
        assert (
            read.totals["create_open"] == 1
            and rrc.contacts_not_accounted_for(read.totals["created"], 0, read.totals["create_open"], 1) == 1
        )
    finally:
        rig.stop()


def test_t15_the_window_before_the_reply_also_leaves_the_create_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import HubspotCrm

    rig = Rig(tmp_path)
    try:
        crm, stats = _crm_with_stats(rig, tmp_path)

        def stop_in_the_request(self: Any, *a: Any, **k: Any) -> None:
            raise _Killed

        monkeypatch.setattr(HubspotCrm, "_once", stop_in_the_request)
        with pytest.raises(_Killed):
            crm.put("L-1", REC)
        assert _stats(stats)["create_open"] == 1
    finally:
        rig.stop()


def test_t15_every_normal_end_of_a_create_closes_it(tmp_path: Path) -> None:
    """Created, conflict, refusal and a used-up call cap all end with create_open 0 (never negative); only the
    first two count a contact."""
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import CrmCapReached, CrmError

    rig = Rig(tmp_path)
    try:
        crm, stats = _crm_with_stats(rig, tmp_path)
        crm.put("L-1", REC)
        assert (_stats(stats)["created"], _stats(stats)["create_open"]) == (1, 0)
        crm.put("L-1", REC)  # the same email again: HubSpot answers 409, the adapter confirms the same contact
        after = _stats(stats)
        assert (after["created"], after["conflicts"], after["create_open"]) == (1, 1, 0), after
        rig.state.mode = "forbidden_400"
        with pytest.raises(CrmError):
            crm.put("L-2", {**REC, "email": "other@example.test"})
        assert _stats(stats)["create_open"] == 0 and _stats(stats)["created"] == 1
        assert _stats(stats)["create_unknown"] == 0  # a clear 4xx refusal proves nothing was stored
        rig.state.mode = "ok"
        small_stats = tmp_path / "desk-rabcdef-3.hubspot.json"
        small = rig.crm(stats_file=small_stats, max_calls=1)
        small.put("L-4", {**REC, "email": "fourth@example.test"})
        with pytest.raises(CrmCapReached):
            small.put("L-5", {**REC, "email": "fifth@example.test"})
        assert _stats(small_stats)["create_open"] == 0
    finally:
        rig.stop()


def _window_in_the_counter(
    monkeypatch: pytest.MonkeyPatch, created_less: int, open_more: int, unknown_instead: bool = False
) -> None:
    """Make the HubSpot counter of the real dry run read as if a desk had been stopped in the window: `created_less`
    created contacts not counted and `open_more` creates open. Only the totals change; the run itself is real."""
    real = rrc.read_counter_files_checked

    def reader(run_dir: Path, suffix: str, tag: str) -> Any:
        read = real(run_dir, suffix, tag)
        if suffix != ".hubspot.json":
            return read
        totals = dict(read.totals)
        totals["created"] -= created_less
        totals["create_open"] = totals.get("create_open", 0) + open_more * (not unknown_instead)
        totals["create_unknown"] = totals.get("create_unknown", 0) + open_more * unknown_instead
        return rrc.CounterRead(totals, read.files, read.unreadable)

    monkeypatch.setattr(rrc, "read_counter_files_checked", reader)


def test_t15_a_run_with_a_window_in_the_counter_and_a_hidden_contact_ends_as_failed(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The scenario of the failing r7s test with the window forced instead of timed: the sum of `created` is one too
    low, one create is open and one contact is hidden by list lag (floor F3 silent). Must be failed and say so."""
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(1))
    monkeypatch.setattr(rrc, "floor_checks", lambda *_a, **_k: [])
    _window_in_the_counter(monkeypatch, created_less=1, open_more=1)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert code == rrc.EXIT_FAILED and "1 contacts may be left" in out, out[-2000:]


@pytest.mark.parametrize(("created_less", "open_more"), [(1, 1), (0, 1)], ids=["made-and-listed", "retried"])
def test_t15_a_window_in_the_counter_with_nothing_hidden_is_no_false_alarm(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, created_less: int, open_more: int
) -> None:
    """The window alone, when the list shows every contact, must not fail the run (the crash drill hits it on
    purpose): the open create made the contact and it is listed, or it was retried (more possible than leads)."""
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(0))
    _window_in_the_counter(monkeypatch, created_less, open_more)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert code == 0 and "may be left" not in out, out[-2000:]


# -- t16: the same class for mail (the lead's question a): a mail counted only after the server reply ----------------
#
# smtp_provider.send writes `attempts` BEFORE the connection and `sent` AFTER the dialogue (smtp_provider.py, the two
# write_stats calls in send), so a desk stopped hard between the server's reply and the count leaves `sent` one too low.
# The control that already exists: floor F4 uses the LARGER of the desk's `sent` and the mails the mailbox reader
# counted (run_real_check.py, floor_checks: `sent_total = max(desk_sent, mails)`), and fails closed when the counter is
# missing (`sent_total is not None`). Pin: passes on r7s too.


def test_t16_a_mail_the_desk_did_not_count_is_still_counted_by_the_mailbox_and_fails_the_floor() -> None:
    from test_real_check_dry import _book, _floors

    book = _book({f"L{i}": ("sent", 1, "") for i in range(9)})
    # one lead got a second mail whose count was lost in the window: the desk says 9 sent (attempts 10), mailbox 10
    undercounted = _floors(book, 9, settled=0, mails=10, crm=9, sent=9)
    assert undercounted["F4"]["ok"] is False
    # the same book with a mailbox that agrees with the book: the floor holds
    assert _floors(book, 9, settled=0, mails=9, crm=9, sent=8)["F4"]["ok"] is True
    # no counter at all proves nothing and fails closed
    assert _floors(book, 9, settled=0, mails=9, crm=9, sent=None)["F4"]["ok"] is False


def test_t15_a_create_that_waits_on_a_429_and_then_succeeds_opens_and_closes_exactly_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One put is one open create however many request attempts the 429 waits cause (kills a count per attempt).
    The wait is replaced by a recorder (no real timing)."""
    import types

    from test_crm_hubspot import REC, Rig

    from lead_desk import crm_hubspot

    waited: list[float] = []
    monkeypatch.setattr(crm_hubspot, "time", types.SimpleNamespace(sleep=waited.append, monotonic=time.monotonic))
    rig = Rig(tmp_path)
    try:
        crm, stats = _crm_with_stats(rig, tmp_path)
        rig.state.mode, rig.state.times, rig.state.retry_after = "r429", 2, "0.01"
        crm.put("L-1", REC)
        written = _stats(stats)
        assert (written["creates"], written["created"], written["create_open"]) == (3, 1, 0), written
        assert len(waited) == 2  # two waits happened, none of them real
    finally:
        rig.stop()


# -- t17: the outcome of a create is unknown after a timeout, a transport error or a 5xx (the lead's gap 1) ----------
#
# In those cases the request HAS left and the contact may exist, so the create is counted as `create_unknown` (it
# feeds the possible number); only a reply that proves nothing was stored (a clear 4xx, 429 after the waits) or a raise
# before the request leaves counts as none. The fake HubSpot really creates the contact first; no sleep, no kill.


def _create_then(monkeypatch: pytest.MonkeyPatch, how: str) -> None:
    from lead_desk.crm_hubspot import CrmError, HubspotCrm, _Reply

    real = HubspotCrm._once

    def once(self: Any, method: str, path: str, obj: Any, deadline: float, key: str) -> Any:
        real(self, method, path, obj, deadline, key)  # HubSpot made the contact
        if how == "drop":
            raise CrmError("connection dropped")  # the reply never reached the desk
        return _Reply(int(how), {}, None)  # an answer that says nothing about the create (500, 408)

    monkeypatch.setattr(HubspotCrm, "_once", once)


@pytest.mark.parametrize("how", ["drop", "500", "408"])
def test_t17_a_create_that_may_have_made_the_contact_is_counted_as_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, how: str
) -> None:
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import CrmError

    rig = Rig(tmp_path)
    try:
        crm, stats = _crm_with_stats(rig, tmp_path)
        _create_then(monkeypatch, how)
        with pytest.raises(CrmError):
            crm.put("L-1", REC)
        assert len(rig.state.contacts) == 1
        written = _stats(stats)
        assert (written["created"], written["create_open"], written["create_unknown"]) == (0, 0, 1), written
        total = written["create_open"] + written["create_unknown"]
        assert rrc.contacts_not_accounted_for(written["created"], 0, total, 1) == 1  # the list shows nothing of it
    finally:
        rig.stop()


def test_t17_a_429_after_the_waits_proves_nothing_was_stored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import types

    from test_crm_hubspot import REC, Rig

    from lead_desk import crm_hubspot
    from lead_desk.crm_hubspot import CrmBusy

    monkeypatch.setattr(crm_hubspot, "time", types.SimpleNamespace(sleep=lambda _s: None, monotonic=time.monotonic))
    rig = Rig(tmp_path)
    try:
        crm, stats = _crm_with_stats(rig, tmp_path)
        rig.state.mode, rig.state.times, rig.state.retry_after = "r429", 99, "0.01"
        with pytest.raises(CrmBusy):
            crm.put("L-1", REC)
        written = _stats(stats)
        assert (written["create_open"], written["create_unknown"], len(rig.state.contacts)) == (0, 0, 0), written
    finally:
        rig.stop()


@pytest.mark.parametrize("window", [(1, 1), (0, 1)], ids=["made-and-listed", "retried"])
def test_t17_an_unknown_create_with_nothing_hidden_is_no_false_alarm(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, window: tuple[int, int]
) -> None:
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(0))
    _window_in_the_counter(monkeypatch, window[0], window[1], unknown_instead=True)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert code == 0 and "may be left" not in out, out[-2000:]


def test_t17_an_unknown_create_and_a_contact_the_list_does_not_show_ends_as_failed(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(1))
    monkeypatch.setattr(rrc, "floor_checks", lambda *_a, **_k: [])
    _window_in_the_counter(monkeypatch, 1, 1, unknown_instead=True)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert code == rrc.EXIT_FAILED and "1 contacts may be left" in out, out[-2000:]


# -- t18: the write of the open create must work before the request leaves (the lead's gap 2) -------------------------


def test_t18_a_counters_file_that_cannot_be_written_stops_the_create_before_it_is_sent(tmp_path: Path) -> None:
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import CrmCounterUnwritable

    rig = Rig(tmp_path)
    try:
        taken = tmp_path / "desk-rabcdef-1.hubspot.json"
        taken.mkdir()  # a folder with the file's name: the replace cannot succeed
        crm = rig.crm(stats_file=taken)
        with pytest.raises(CrmCounterUnwritable, match="create was not sent"):
            crm.put("L-1", REC)
        assert len(rig.state.contacts) == 0  # nothing left the desk
        assert crm.stats()["calls"] == 0 and crm.stats()["create_open"] == 0
        # the other counters stay best-effort: a read with the same unwritable file still works
        assert crm.rows_with_prefix("L") == []
    finally:
        rig.stop()
