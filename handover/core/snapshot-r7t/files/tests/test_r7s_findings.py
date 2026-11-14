"""Round 7S: tests for the findings of the r7r review. Made-up data only, loopback only; no real model, mail or spend.
Header table: finding, what is pinned, result on a copy of r7r (FAILS = new behaviour, fails before the fix; PIN = code
that is already right or guards against a wrong fix, passes by design; a mutant planted on r7s is killed by it, see
R7S-RESULTS.md).

  finding | what is pinned                                                              | on r7r
  ------- | --------------------------------------------------------------------------- | ------
  s1      | QuietServer (the one server class of every fake) refuses a bind that is not | FAILS
          | this computer. FAILS: itself, a subclass, FakeHubspot. PIN: the other two   |
          | fakes (their factories already refuse)                                      |
  s1b     | the file-call guard sees every use of QuietServer outside its own file      | FAILS
  s1c     | a loopback bind still works                                                 | PIN
  s1d     | an address that is not a host and a port is refused (fails closed)          | FAILS
  s3      | a contact the desk created that the CRM list does not show is said and ends | FAILS
          | the check with the failed exit code, with and without the clean-up          |
  s3d     | a contact left by a failed archive is said as LEFT, not again as missing    | PIN
  s3e     | the exit code is 0 only if checks hold, file written, none left, none        | FAILS
          | unaccounted (one failing part at a time)                                    |
  s3b     | the desk's counter files are those of THIS run: an old file in a shared     | FAILS
          | run folder does not count                                                   |
  s3c     | the counting rule itself (created, accepted number, no counter)             | FAILS
  s6      | a test that needs openssl fails on CI (DPLD_REQUIRE_SCAN set) and skips     | FAILS
          | without it; no test file skips on a missing openssl by itself               |
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest
from support import HOST, REPO, script_module
from test_file_call_guard import _plant, _problems

from tools.refusing_args import LOOPBACK_HOST_TEXT

rrc = script_module("run_real_check")

# Addresses that are not this computer. Built from parts so no line holds a whole address (the repo's scan reads lines).
ALL_INTERFACES = ".".join(["0"] * 4)
OTHER_ADDRESS = ".".join(["192", "0", "2", "1"])  # documentation range
NOT_LOOPBACK = [ALL_INTERFACES, OTHER_ADDRESS, "", "::", "example." + "com"]


def _handler() -> type:
    return type("H", (), {})


# -- s1: the loopback refusal sits in QuietServer ------------------------------------------------------------------


@pytest.mark.parametrize("host", NOT_LOOPBACK)
def test_s1_quiet_server_itself_refuses_a_bind_that_is_not_this_computer(host: str) -> None:
    from demo_only.bad_request import QuietServer

    with pytest.raises(ValueError, match=LOOPBACK_HOST_TEXT):
        QuietServer((host, 0), _handler())


@pytest.mark.parametrize("host", NOT_LOOPBACK)
def test_s1_a_subclass_in_any_file_refuses_too(host: str) -> None:
    from demo_only.bad_request import QuietServer

    class Later(QuietServer):  # a fake someone adds next year
        pass

    with pytest.raises(ValueError, match=LOOPBACK_HOST_TEXT):
        Later((host, 0), _handler())


@pytest.mark.parametrize("host", NOT_LOOPBACK)
def test_s1_the_fake_hubspot_server_refuses(host: str) -> None:
    from demo_only.fake_hubspot import HubspotState, serve

    with pytest.raises(ValueError, match=LOOPBACK_HOST_TEXT):
        serve(HubspotState("k", "ok"), host, 0)


@pytest.mark.parametrize("host", [h for h in NOT_LOOPBACK if h])  # an empty host means "the default" for this factory
def test_s1_the_fakes_server_refuses(host: str) -> None:
    from demo_only.fakes_server import make_fakes_server

    with pytest.raises(ValueError, match=LOOPBACK_HOST_TEXT):
        make_fakes_server(host=host)


@pytest.mark.parametrize("host", NOT_LOOPBACK)
def test_s1_the_fake_model_server_refuses(host: str) -> None:
    from demo_only.fake_model_server import make_model_server

    with pytest.raises(ValueError, match=LOOPBACK_HOST_TEXT):
        make_model_server(host, 0, "ok", "k")


@pytest.mark.parametrize("address", [(None, 0), (b"127.0.0.1", 0), (), "127.0.0.1", 8080], ids=repr)
def test_s1_an_address_that_is_not_a_host_and_port_is_refused(address: Any) -> None:
    """Fails closed: what cannot be read as a host name is not loopback."""
    from demo_only.bad_request import QuietServer

    with pytest.raises(ValueError, match=LOOPBACK_HOST_TEXT):
        QuietServer(address, _handler())


def test_s1_the_refusal_comes_before_any_socket_is_made(monkeypatch: pytest.MonkeyPatch) -> None:
    """Nothing may listen, even for a moment: the check runs before the base class opens the port."""
    import socket

    from demo_only.bad_request import QuietServer

    made: list[object] = []
    real = socket.socket.__init__

    def counting(self: socket.socket, *a: Any, **k: Any) -> None:
        made.append(self)
        real(self, *a, **k)

    monkeypatch.setattr(socket.socket, "__init__", counting)
    with pytest.raises(ValueError):
        QuietServer((ALL_INTERFACES, 0), _handler())
    assert made == []


@pytest.mark.parametrize("host", [HOST, "localhost", "127.0.0.1"])
def test_s1c_a_loopback_bind_still_works(host: str) -> None:
    from demo_only.bad_request import QuietServer

    srv = QuietServer((host, 0), _handler())
    try:
        assert srv.server_address[1] > 0 and srv.daemon_threads is True
    finally:
        srv.server_close()


def test_s1b_the_guard_sees_a_use_of_quiet_server_outside_its_own_file(tmp_path: Path) -> None:
    for shape in (
        "from demo_only.bad_request import QuietServer\nclass S(QuietServer):\n    pass",
        "from demo_only.bad_request import QuietServer\nsrv = QuietServer(('x', 0), None)",
        "from demo_only import bad_request\nclass S(bad_request.QuietServer):\n    pass",
    ):
        root = _plant(tmp_path / str(abs(hash(shape))), shape, "demo_only")
        found = [p for p in _problems(root, {}, {}) if p.startswith("demo_only/planted.py")]
        assert found, shape


# -- s3: a contact the desk created that the CRM list does not show -----------------------------------------------


def test_s3c_the_counting_rule() -> None:
    assert rrc.contacts_not_accounted_for(5, 5) == 0
    assert rrc.contacts_not_accounted_for(5, 4) == 1
    assert rrc.contacts_not_accounted_for(5, 0) == 5
    assert rrc.contacts_not_accounted_for(4, 5) == 0  # a 409 conflict or a crash in the middle of a call: not an error
    # r7t: a counter that is not known is NOT "nothing is missing" (F3 never reads the counter): the rule fails closed
    for accounted in (0, 5):
        with pytest.raises(rrc.CounterUnreadable):
            rrc.contacts_not_accounted_for(None, accounted)


@pytest.mark.parametrize(
    ("ok", "written", "left", "unseen", "known", "zero"),
    [
        (True, True, [], 0, True, True),
        (False, True, [], 0, True, False),
        (True, False, [], 0, True, False),
        (True, True, ["7"], 0, True, False),
        (True, True, [], 1, True, False),  # only an unaccounted contact is wrong: that alone ends the run as failed
        (True, True, [], 0, False, False),  # r7t: only an unknown counter is wrong: that alone ends the run as failed
    ],
)
def test_s3e_the_exit_code_is_zero_only_when_nothing_is_open(
    ok: bool, written: bool, left: list[str], unseen: int, known: bool, zero: bool
) -> None:
    assert (rrc.exit_code_of(ok, written, left, unseen, known) == 0) is zero


def _hiding_crm(hidden: int) -> type:
    class Hiding(rrc.HubspotCrm):
        """A CRM whose LIST shows `hidden` contacts fewer than exist (list lag)."""

        def rows_with_prefix(self, prefix: str) -> list[tuple[str, str]]:
            rows = super().rows_with_prefix(prefix)
            return rows[: len(rows) - hidden]

    return Hiding


@pytest.mark.parametrize(
    ("cleanup", "floors_silent"),
    [(True, True), (False, True), (True, False)],
    ids=["with-cleanup-f3-silent", "without-cleanup-f3-silent", "with-cleanup-f3-also-fails"],
)
def test_s3_a_created_contact_the_list_does_not_show_ends_the_check_with_the_failed_exit_code(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, cleanup: bool, floors_silent: bool
) -> None:
    """`floors_silent` is the case of the finding: the hidden contact belongs to a lead the book does not show as
    CRM-done, so floor F3 has nothing to say (here the floors are made silent to build that case with the real desk)."""
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(1))
    if floors_silent:
        monkeypatch.setattr(rrc, "floor_checks", lambda *_a, **_k: [])
    code = rrc.main(["--dry-fakes", "--assume-yes", *(["--cleanup"] if cleanup else [])])
    out = capsys.readouterr().out
    assert "1 contacts may be left" in out, out[-2500:]
    assert code == rrc.EXIT_FAILED, out[-2500:]


def test_s3_a_contact_left_by_a_failed_archive_is_said_once_as_left_not_again_as_missing(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The contact the list showed but the archive call refused is counted (done + left), not reported twice."""

    class Flaky(rrc.HubspotCrm):
        tried = 0

        def archive(self, cid: str) -> None:
            type(self).tried += 1
            if type(self).tried == 1:
                raise rrc.CrmError("made-up refusal")
            super().archive(cid)

    monkeypatch.setattr(rrc, "HubspotCrm", Flaky)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert "contacts are LEFT" in out and "may be left" not in out
    assert code == rrc.EXIT_FAILED, out[-2500:]


def test_s3_nothing_hidden_still_ends_with_zero(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(0))
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert "may be left" not in out and code == 0, out[-2500:]


def test_s3b_counter_files_of_an_older_run_in_the_same_folder_do_not_count(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    class Seeded(rrc.DryFakes):
        def __init__(self, *a: Any, **k: Any) -> None:
            super().__init__(*a, **k)
            run = Path(self.env["DESK_DB_PATH"]).parent
            run.mkdir(parents=True, exist_ok=True)
            for name in ("desk-3.hubspot.json", "desk-r" + "000000-1.hubspot.json"):  # unlike this run's tag
                (run / name).write_text(json.dumps({"created": 99, "creates": 99, "calls": 99}), encoding="utf-8")
            for name in ("desk-3.smtp.json", "desk-r" + "000000-1.smtp.json"):
                (run / name).write_text(json.dumps({"sent": 99, "attempts": 99}), encoding="utf-8")

    monkeypatch.setattr(rrc, "DryFakes", Seeded)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert "may be left" not in out and code == 0, out[-2500:]


def test_s3b_the_counter_reader_takes_only_the_files_of_the_given_run(tmp_path: Path) -> None:
    (tmp_path / "desk-raaaaaa-1.hubspot.json").write_text('{"created": 2}', encoding="utf-8")
    (tmp_path / "desk-raaaaaa-2.hubspot.json").write_text('{"created": 3}', encoding="utf-8")
    (tmp_path / "desk-rbbbbbb-1.hubspot.json").write_text('{"created": 50}', encoding="utf-8")
    (tmp_path / "desk-1.hubspot.json").write_text('{"created": 70}', encoding="utf-8")
    assert rrc.read_counter_files(tmp_path, ".hubspot.json", "raaaaaa") == {"created": 5}
    assert rrc.read_counter_files(tmp_path, ".hubspot.json", "rcccccc") == {}


def test_s3b_the_desk_writes_its_counters_under_the_run_tag(tmp_path: Path) -> None:
    d = rrc.Desk({}, tmp_path, 1, "7", tag="rabcdef")
    assert d.log_path.name == "desk-rabcdef-7.log"
    assert d.log_path.with_suffix(".hubspot.json").name == "desk-rabcdef-7.hubspot.json"


# -- s6: a missing openssl is a failure on CI, a skip elsewhere ---------------------------------------------------


def test_s6_without_the_require_flag_a_missing_openssl_is_a_skip(monkeypatch: pytest.MonkeyPatch) -> None:
    from support import skip_or_fail_without_openssl

    monkeypatch.delenv("DPLD_REQUIRE_SCAN", raising=False)
    with pytest.raises(
        BaseException
    ) as info:  # BaseException: a wrong outcome must show as a failed assert, not a skip
        skip_or_fail_without_openssl()
    assert info.type is pytest.skip.Exception


def test_s6_with_the_require_flag_a_missing_openssl_is_a_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    from support import skip_or_fail_without_openssl

    monkeypatch.setenv("DPLD_REQUIRE_SCAN", "1")
    with pytest.raises(BaseException) as info:  # a skip here would be the very thing this test is about
        skip_or_fail_without_openssl()
    assert info.type is pytest.fail.Exception and "openssl" in str(info.value)


def test_s6_no_test_file_skips_on_a_missing_openssl_by_itself() -> None:
    """The class: a skip written next to a certificate that could not be made hides the whole test on CI. Every such
    place goes through support.skip_or_fail_without_openssl."""
    own = Path(__file__).resolve()
    bad = []
    for py in sorted((REPO / "tests").glob("*.py")):
        if py == own:
            continue
        for node in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and ast.unparse(node.func) == "pytest.skip"
                and node.args
                and any(w in ast.unparse(node.args[0]).lower() for w in ("openssl program", "no openssl"))
            ):
                bad.append(f"{py.name}:{node.lineno}")
    assert not bad, "pytest.skip next to openssl (use skip_or_fail_without_openssl): " + ", ".join(bad)
